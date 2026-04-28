"""
claude_vision_pipeline.py
=========================
Pipeline: technical drawing (image/PDF)  →  assemble_objects() specs.

Uses Claude's vision API to extract structured geometry from reactor drawings.
Output is a clean spec list ready for assemble_objects(). Fully self-contained
— no dependency on nuextract_pipeline.py or any other ZLP module.

Workflows
---------
A) SINGLE IMAGE:

    from claude_vision_pipeline import extract_specs_from_drawing, patch_spec
    specs = extract_specs_from_drawing("drawing.png")
    specs = patch_spec(specs, "reactor_vessel_1", {"inner_d": 8.91, "wall_t": 0.05})
    assembly = assemble_objects(specs)

B) SAVE RAW + RELOAD (inspect JSON before building):

    specs = extract_specs_from_drawing("drawing.png", save_raw_to="raw.json")
    # later:
    from claude_vision_pipeline import specs_from_json
    specs = specs_from_json("raw.json")

C) MULTIPLE VIEWS (plan + elevation in one call):

    from claude_vision_pipeline import extract_specs_from_drawings
    specs = extract_specs_from_drawings(["top_view.png", "side_view.png"])

Environment variables
---------------------
    ANTHROPIC_API_KEY   — your Anthropic API key (alternative to passing api_key=)

Requirements
------------
    pip install anthropic
"""







from __future__ import annotations

import base64
import json
import os
import warnings
from pathlib import Path
from typing import Any


from dotenv import load_dotenv
load_dotenv()




# ---------------------------------------------------------------------------
# Schema
# ---------------------------------------------------------------------------

DRAWING_EXTRACTION_SCHEMA: dict[str, Any] = {
    "units":       ["mm", "cm", "m"],
    "drawing_id":  "verbatim-string",
    "description": "string",
    "components": [
        {
            "obj_id":    "string",
            "operation": ["primitive", "extrude", "revolve", "sweep"],

            "center_x":       "number",
            "center_y":       "number",
            "center_z":       "number",
            "rotation_roll":  "number",
            "rotation_pitch": "number",
            "rotation_yaw":   "number",

            "insert_into": "string",

            "obj_type": [
                "cylinder", "pipe", "box", "sphere",
                "reactor_vessel", "reactor_top_plate", "ihx",
            ],

            # generic geometry
            "radius":       "number",
            "height":       "number",
            "outer_radius": "number",
            "inner_radius": "number",
            "length":       "number",
            "width":        "number",

            # reactor_vessel
            "inner_d":    "number",
            "wall_t":     "number",
            "straight_h": "number",

            "bottom_head_type":    ["flat", "hemispherical", "ellipsoidal", "torispherical"],
            "bottom_head_plate_t": "number",
            "bottom_head_depth":   "number",
            "bottom_head_Rc":      "number",
            "bottom_head_rk":      "number",

            "top_head_type":    ["flat", "hemispherical", "ellipsoidal", "torispherical"],
            "top_head_plate_t": "number",
            "top_head_depth":   "number",
            "top_head_Rc":      "number",
            "top_head_rk":      "number",

            # reactor_top_plate
            "outer_d":   "number",
            "thickness": "number",
            "z_bottom":  "number",
            "hole_groups": [
                {
                    "hole_diameter":    "number",
                    "layout":           ["symmetric", "custom_angles", "explicit_positions"],
                    "count":            "integer",
                    "placement_radius": "number",
                    "start_angle_deg":  "number",
                    "angles_deg":       ["number"],
                    "positions_x":      ["number"],
                    "positions_y":      ["number"],
                }
            ],

            # ihx
            "shell_od":                "number",
            "shell_wall_t":            "number",
            "shell_straight_h":        "number",
            "inner_od":                "number",
            "inner_wall_t":            "number",
            "inner_h":                 "number",
            "bundle_od":               "number",
            "bundle_id":               "number",
            "bundle_h":                "number",
            "secondary_inlet_od":      "number",
            "secondary_inlet_wall_t":  "number",
            "secondary_inlet_length":  "number",
            "secondary_inlet_z":       "number",
            "secondary_outlet_od":     "number",
            "secondary_outlet_wall_t": "number",
            "secondary_outlet_length": "number",
            "secondary_outlet_z":      "number",

            # profile-based operations (extrude / revolve / sweep)
            "profile_obj_type":     ["rectangle", "circle", "ellipse",
                                     "trapezoid", "slot", "regular_polygon"],
            "profile_width":        "number",
            "profile_height":       "number",
            "profile_radius":       "number",
            "profile_r1":           "number",
            "profile_r2":           "number",
            "profile_a1":           "number",
            "profile_nmb_of_sides": "integer",
            "profile_angle":        "number",

            "extrude_height": "number",
            "wall_thickness": "number",
            "revolve_angle":  "number",
            "revolve_axis":   ["X", "Y", "Z"],
            "plane":          ["XY", "XZ", "YZ"],
        }
    ],
}


# ---------------------------------------------------------------------------
# Prompts
# ---------------------------------------------------------------------------

_SYSTEM_PROMPT = """\
You are a nuclear engineering CAD assistant.
Your task is to extract 3D component geometry from a reactor technical drawing
and return it as a single JSON object that conforms exactly to the schema below.

RULES
-----
1. Output ONLY valid JSON — no prose, no markdown fences, no comments.
2. Use null for values not visible or not labelled in the drawing.
3. Use the drawing's own unit system and record it in the "units" field
   ("mm", "cm", or "m"). Do NOT convert units.
4. obj_type must be one of:
     cylinder | pipe | box | sphere |
     reactor_vessel | reactor_top_plate | ihx
5. For reactor_vessel: populate inner_d, wall_t, straight_h, bottom_head_type.
   Use outer_d only if inner_d is not labelled.
6. For hole_groups in reactor_top_plate: populate as many fields as visible.
7. If a dimension label is ambiguous, use your best engineering judgement and
   note the ambiguity in the top-level "description" field.
8. Generate a short snake_case obj_id for each component.

JSON SCHEMA (all fields except obj_id and operation are nullable)
-----------------------------------------------------------------
{schema}
""".format(schema=json.dumps(DRAWING_EXTRACTION_SCHEMA, indent=2))

# _USER_PROMPT = "Extract all reactor components from this drawing. Return only the JSON object."

_USER_PROMPT = """\
Before outputting JSON, carefully count all visible holes in the top plate, \
identify their diameters and bolt circle radii from the drawing labels, \
and verify head geometry type from the elevation view. \
Then output the JSON object — nothing else after it.\
"""

_MULTI_USER_PROMPT = (
    "These are multiple views of the same reactor. "
    "Reconcile dimensions across all views — e.g. diameters from the plan view, "
    "heights from the elevation — and return one combined JSON object. "
    + _USER_PROMPT
)


# ---------------------------------------------------------------------------
# Unit scaling and postprocessing
# ---------------------------------------------------------------------------

_UNIT_SCALE: dict[str, float] = {"mm": 1e-3, "cm": 1e-2, "m": 1.0}

_LINEAR_FIELDS = {
    "radius", "height", "length", "width", "outer_radius", "inner_radius",
    "inner_d", "wall_t", "straight_h",
    "bottom_head_plate_t", "bottom_head_depth", "bottom_head_Rc", "bottom_head_rk",
    "top_head_plate_t",    "top_head_depth",    "top_head_Rc",    "top_head_rk",
    "outer_d", "thickness", "z_bottom",
    "hole_diameter", "placement_radius",
    "profile_width", "profile_height", "profile_radius", "profile_r1", "profile_r2",
    "extrude_height", "wall_thickness",
    "shell_od", "shell_wall_t", "shell_straight_h",
    "inner_od", "inner_wall_t", "inner_h",
    "bundle_od", "bundle_id", "bundle_h",
    "secondary_inlet_od", "secondary_inlet_wall_t", "secondary_inlet_length", "secondary_inlet_z",
    "secondary_outlet_od", "secondary_outlet_wall_t", "secondary_outlet_length", "secondary_outlet_z",
}


def _sc(value: Any, s: float) -> Any:
    if isinstance(value, (int, float)):
        return value * s
    if isinstance(value, list):
        return [_sc(v, s) for v in value]
    return value


def _rebuild_component(c: dict[str, Any], s: float) -> dict[str, Any]:
    """Convert one flat extracted component into a nested assemble_objects() spec."""
    spec: dict[str, Any] = {}

    for f in ("obj_id", "operation", "insert_into", "plane"):
        if c.get(f):
            spec[f] = c[f]

    #if c.get("obj_type") and not c.get("profile_obj_type"):
    #    spec["obj_type"] = c["obj_type"]

    if c.get("obj_type"):
        spec["obj_type"] = c["obj_type"]

    cx, cy, cz = c.get("center_x"), c.get("center_y"), c.get("center_z")
    if any(v is not None for v in (cx, cy, cz)):
        spec["center_coords"] = (_sc(cx or 0.0, s), _sc(cy or 0.0, s), _sc(cz or 0.0, s))

    rr, rp, ry = c.get("rotation_roll"), c.get("rotation_pitch"), c.get("rotation_yaw")
    if any(v is not None for v in (rr, rp, ry)):
        spec["rotation_angles"] = (rr or 0.0, rp or 0.0, ry or 0.0)

    for f in ("radius", "height", "length", "width", "outer_radius", "inner_radius",
              "inner_d", "wall_t", "straight_h",
              "outer_d", "thickness", "z_bottom", "wall_thickness"):
        if c.get(f) is not None:
            spec[f] = _sc(c[f], s)

    if c.get("bottom_head_type"):
        spec["bottom_head_type"] = c["bottom_head_type"]
        bhp: dict[str, Any] = {}
        for src, dst in [("bottom_head_plate_t", "plate_t"), ("bottom_head_depth", "head_depth"),
                         ("bottom_head_Rc", "Rc"), ("bottom_head_rk", "rk")]:
            if c.get(src) is not None:
                bhp[dst] = _sc(c[src], s)
        if bhp:
            spec["bottom_head_params"] = bhp

    if c.get("top_head_type"):
        spec["top_head_type"] = c["top_head_type"]
        thp: dict[str, Any] = {}
        for src, dst in [("top_head_plate_t", "plate_t"), ("top_head_depth", "head_depth"),
                         ("top_head_Rc", "Rc"), ("top_head_rk", "rk")]:
            if c.get(src) is not None:
                thp[dst] = _sc(c[src], s)
        if thp:
            spec["top_head_params"] = thp

    for h in (c.get("hole_groups") or []):
        hg: dict[str, Any] = {}
        if h.get("hole_diameter") is not None:
            hg["hole_diameter"] = _sc(h["hole_diameter"], s)
        if h.get("layout"):
            hg["layout"] = h["layout"]
        if h.get("count") is not None:
            hg["count"] = h["count"]
        if h.get("placement_radius") is not None:
            hg["placement_radius"] = _sc(h["placement_radius"], s)
        if h.get("start_angle_deg") is not None:
            hg["start_angle_deg"] = h["start_angle_deg"]
        if h.get("angles_deg"):
            hg["angles_deg"] = h["angles_deg"]
        xs = h.get("positions_x") or []
        ys = h.get("positions_y") or []
        if xs and ys:
            hg["positions"] = [(_sc(x, s), _sc(y, s)) for x, y in zip(xs, ys)]
        if hg:
            spec.setdefault("hole_groups", []).append(hg)

    ihx_fields = (
        "shell_od", "shell_wall_t", "shell_straight_h",
        "inner_od", "inner_wall_t", "inner_h",
        "bundle_od", "bundle_id", "bundle_h",
        "secondary_inlet_od", "secondary_inlet_wall_t",
        "secondary_inlet_length", "secondary_inlet_z",
        "secondary_outlet_od", "secondary_outlet_wall_t",
        "secondary_outlet_length", "secondary_outlet_z",
    )
    for f in ihx_fields:
        if c.get(f) is not None:
            spec[f] = _sc(c[f], s)

    if c.get("profile_obj_type"):
        profile: dict[str, Any] = {"obj_type": c["profile_obj_type"]}
        for src, dst in [("profile_width", "width"), ("profile_height", "height"),
                         ("profile_radius", "radius"), ("profile_r1", "r1"),
                         ("profile_r2", "r2"), ("profile_a1", "a1"),
                         ("profile_nmb_of_sides", "nmb_of_sides"), ("profile_angle", "angle")]:
            if c.get(src) is not None:
                profile[dst] = _sc(c[src], s) if src in _LINEAR_FIELDS else c[src]
        spec["profile"] = profile

    op = spec.get("operation", "")
    if op == "extrude" and c.get("extrude_height") is not None:
        spec["height"] = _sc(c["extrude_height"], s)
    if op == "revolve":
        if c.get("revolve_angle") is not None:
            spec["angle"] = c["revolve_angle"]
        if c.get("revolve_axis"):
            spec["axis"] = c["revolve_axis"]

    _FIELDS_BY_TYPE: dict[str, set] = {
        "reactor_vessel": {
            "inner_d", "wall_t", "straight_h", "height",
            "bottom_head_type", "bottom_head_params",
            "top_head_type", "top_head_params",
        },
        "reactor_top_plate": {
            "outer_d", "thickness", "z_bottom", "hole_groups",
        },
        "ihx": {
            "shell_od", "shell_wall_t", "shell_straight_h",
            "inner_od", "inner_wall_t", "inner_h",
            "bundle_od", "bundle_id", "bundle_h",
            "secondary_inlet_od", "secondary_inlet_wall_t",
            "secondary_inlet_length", "secondary_inlet_z",
            "secondary_outlet_od", "secondary_outlet_wall_t",
            "secondary_outlet_length", "secondary_outlet_z",
        },
        "cylinder": {"radius", "height", "profile"},
        "pipe":     {"outer_radius", "inner_radius", "height", "profile"},
        "box":      {"length", "width", "height", "profile"},
        "sphere":   {"radius", "profile"},
    }
    _COMMON = {"obj_id", "operation", "obj_type", "insert_into",
           "center_coords", "rotation_angles",
           "plane", "angle", "axis", "wall_thickness"}

    obj_type = spec.get("obj_type")
    allowed = _COMMON | _FIELDS_BY_TYPE.get(obj_type, set()) #type: ignore

    return {k: v for k, v in spec.items() if k in allowed}


def postprocess(raw: dict[str, Any]) -> list[dict[str, Any]]:
    """
    Convert raw Claude extraction JSON into a clean assemble_objects() spec list.

    Parameters
    ----------
    raw : dict
        Parsed JSON as returned by extract_raw_from_drawing().

    Returns
    -------
    list[dict]
        One dict per component, ready for assemble_objects(specs).
    """
    units = (raw.get("units") or "mm").lower().strip()
    if units not in _UNIT_SCALE:
        warnings.warn(f"Unknown unit '{units}' — defaulting to mm.", stacklevel=2)
        units = "mm"
    s = _UNIT_SCALE[units]

    specs = []
    for comp in raw.get("components") or []:
        rebuilt = _rebuild_component(comp, s)
        if not rebuilt.get("operation"):
            continue
        if not rebuilt.get("obj_id"):
            rebuilt["obj_id"] = f"component_{len(specs)}"

        _REQUIRED_BY_TYPE = {
            "reactor_vessel":    ("outer_d", "inner_d", "straight_h", "height"),
            "reactor_top_plate": ("outer_d",),
            "ihx":               ("shell_od", "shell_straight_h"),
        }
        obj_type = rebuilt.get("obj_type")
        if obj_type in _REQUIRED_BY_TYPE:
            if not any(rebuilt.get(f) for f in _REQUIRED_BY_TYPE[obj_type]):
                continue
        elif obj_type and not any(rebuilt.get(f) for f in (
            "radius", "height", "length", "outer_radius", "extrude_height",
        )) and not rebuilt.get("profile"):
            continue

        # force correct operation for premade and primitive types
        if rebuilt.get("obj_type") in ("reactor_vessel", "reactor_top_plate", "ihx"):
            rebuilt["operation"] = "primitive"

        specs.append(rebuilt)

    return specs


# ---------------------------------------------------------------------------
# File I/O helpers
# ---------------------------------------------------------------------------

def specs_from_json(json_path: str | Path) -> list[dict[str, Any]]:
    """
    Load a previously saved raw extraction JSON and postprocess it.

    Useful for re-running postprocess() after manually editing the raw file.
    """
    json_path = Path(json_path)
    if not json_path.exists():
        raise FileNotFoundError(f"JSON file not found: {json_path}")
    with open(json_path) as f:
        raw = json.load(f)
    return postprocess(raw)


def patch_spec(
    specs:   list[dict[str, Any]],
    obj_id:  str,
    updates: dict[str, Any],
) -> list[dict[str, Any]]:
    """
    Apply manual overrides to one component after extraction.

    Useful for values not readable from the drawing (wall_t, inner_d, etc.).

    Example
    -------
    >>> specs = patch_spec(specs, "reactor_vessel_1", {"wall_t": 0.04, "inner_d": 8.91})
    """
    for spec in specs:
        if spec.get("obj_id") == obj_id:
            spec.update(updates)
            return specs
    raise KeyError(f"No component with obj_id='{obj_id}' found in specs.")


# ---------------------------------------------------------------------------
# Internal helpers
# ---------------------------------------------------------------------------

def _encode_image(image_path: Path) -> tuple[str, str]:
    suffix = image_path.suffix.lower()
    media_type_map = {
        ".png":  "image/png",
        ".jpg":  "image/jpeg",
        ".jpeg": "image/jpeg",
        ".gif":  "image/gif",
        ".webp": "image/webp",
        ".pdf":  "application/pdf",
    }
    media_type = media_type_map.get(suffix)
    if media_type is None:
        raise ValueError(
            f"Unsupported file type '{suffix}'. "
            "Supported: .png .jpg .jpeg .gif .webp .pdf"
        )
    with open(image_path, "rb") as f:
        data = base64.standard_b64encode(f.read()).decode("utf-8")
    return data, media_type


def _image_content_block(image_path: Path) -> dict[str, Any]:
    b64_data, media_type = _encode_image(image_path)
    if media_type == "application/pdf":
        return {
            "type": "document",
            "source": {"type": "base64", "media_type": media_type, "data": b64_data},
        }
    return {
        "type": "image",
        "source": {"type": "base64", "media_type": media_type, "data": b64_data},
    }


def _parse_response(raw_text: str) -> dict[str, Any]:
    raw_text = raw_text.strip()
    if raw_text.startswith("```"):
        raw_text = raw_text.split("\n", 1)[-1]
        raw_text = raw_text.rsplit("```", 1)[0]
    raw_text = raw_text.strip()
    try:
        return json.loads(raw_text)
    except json.JSONDecodeError as e:
        raise ValueError(
            f"Claude did not return valid JSON.\n"
            f"Parse error: {e}\n"
            f"Raw response (first 500 chars):\n{raw_text[:500]}"
        ) from e


def _save_raw(raw: dict[str, Any], path: str | Path) -> None:
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    with open(path, "w") as f:
        json.dump(raw, f, indent=2)
    print(f"Raw extraction saved → {path}")


def _get_client(api_key: str | None) -> Any:
    try:
        import anthropic    # type: ignore
    except ImportError as e:
        raise ImportError("anthropic package required: pip install anthropic") from e
    key = api_key or os.environ.get("ANTHROPIC_API_KEY")
    if not key:
        raise ValueError("No API key — pass api_key= or set ANTHROPIC_API_KEY env var.")
    import anthropic as _anthropic  #type: ignore
    return _anthropic.Anthropic(api_key=key)


# ---------------------------------------------------------------------------
# Core API calls
# ---------------------------------------------------------------------------

def extract_raw_from_drawing(
    drawing_path: str | Path,
    *,
    api_key:     str | None = None,
    model:       str = "claude-sonnet-4-6",
    max_tokens:  int = 4096,
    save_raw_to: str | Path | None = None,
) -> dict[str, Any]:
    """
    Send a single drawing to Claude and return the raw extracted dict.

    Save via save_raw_to= to inspect the extraction or reload later with
    specs_from_json() without making another API call.

    Parameters
    ----------
    drawing_path : str | Path
        Path to a .png / .jpg / .gif / .webp / .pdf file.
    api_key : str, optional
        Anthropic API key. Falls back to ANTHROPIC_API_KEY env var.
    model : str
        Default: "claude-sonnet-4-6". Use "claude-opus-4-5" for maximum
        extraction quality on complex or low-resolution drawings.
    max_tokens : int
        Increase to 8192 for drawings with many components.
    save_raw_to : str | Path, optional
        If given, saves the raw JSON for inspection / later reuse.
    """
    drawing_path = Path(drawing_path)
    if not drawing_path.exists():
        raise FileNotFoundError(f"Drawing not found: {drawing_path}")

    client = _get_client(api_key)
    # response = client.messages.create(
    #     model      = model,
    #     max_tokens = max_tokens,
    #     system     = _SYSTEM_PROMPT,
    #     messages   = [{
    #         "role": "user",
    #         "content": [
    #             _image_content_block(drawing_path),
    #             {"type": "text", "text": _USER_PROMPT},
    #         ],
    #     }],
    # )

    response = client.messages.create(
        model      = model,
        max_tokens = 16000,
        thinking   = {"type": "enabled", "budget_tokens": 8000},
        system     = _SYSTEM_PROMPT,
        messages   = [{
            "role": "user",
            "content": [
                _image_content_block(drawing_path),
                {"type": "text", "text": _USER_PROMPT},
            ],
        }],
    )



    raw_text = "".join(b.text for b in response.content if b.type == "text")
    raw = _parse_response(raw_text)

    if save_raw_to is not None:
        _save_raw(raw, save_raw_to)

    return raw


def extract_specs_from_drawing(
    drawing_path: str | Path,
    *,
    api_key:     str | None = None,
    model:       str = "claude-sonnet-4-6",
    max_tokens:  int = 4096,
    save_raw_to: str | Path | None = None,
) -> list[dict[str, Any]]:
    """
    Single drawing → assemble_objects() spec list.

    Example
    -------
    >>> from claude_vision_pipeline import extract_specs_from_drawing, patch_spec
    >>> from assemble import assemble_objects
    >>>
    >>> specs = extract_specs_from_drawing("esfr.png", save_raw_to="esfr_raw.json")
    >>> specs = patch_spec(specs, "reactor_vessel_1", {"wall_t": 0.04})
    >>> assembly = assemble_objects(specs)
    """
    raw = extract_raw_from_drawing(
        drawing_path,
        api_key=api_key,
        model=model,
        max_tokens=max_tokens,
        save_raw_to=save_raw_to,
    )
    return postprocess(raw)


def extract_specs_from_drawings(
    drawing_paths: list[str | Path],
    *,
    api_key:     str | None = None,
    model:       str = "claude-sonnet-4-6",
    max_tokens:  int = 8192,
    save_raw_to: str | Path | None = None,
) -> list[dict[str, Any]]:
    """
    Multiple views of the same reactor → single merged spec list.

    All images are sent in one Claude call so it can reconcile dimensions
    across views (e.g. diameters from plan, heights from elevation).

    Parameters
    ----------
    drawing_paths : list[str | Path]
        Two or more drawing images. Recommended order: plan view first.
    """
    client = _get_client(api_key)

    content: list[dict[str, Any]] = []
    for i, dp in enumerate(drawing_paths):
        dp = Path(dp)
        if not dp.exists():
            raise FileNotFoundError(f"Drawing not found: {dp}")
        content.append({"type": "text", "text": f"Drawing {i + 1} ({dp.name}):"})
        content.append(_image_content_block(dp))
    content.append({"type": "text", "text": _MULTI_USER_PROMPT})

    response = client.messages.create(
        model      = model,
        max_tokens = max_tokens,
        system     = _SYSTEM_PROMPT,
        messages   = [{"role": "user", "content": content}],
    )

    raw_text = "".join(b.text for b in response.content if b.type == "text")
    raw = _parse_response(raw_text)

    if save_raw_to is not None:
        _save_raw(raw, save_raw_to)

    return postprocess(raw)


# ---------------------------------------------------------------------------
# CLI — python claude_vision_pipeline.py drawing.png [raw_output.json]
# ---------------------------------------------------------------------------

if __name__ == "__main__":
    import sys

    if len(sys.argv) < 2:
        print("Usage: python claude_vision_pipeline.py <drawing.[png|jpg|pdf]> [raw_output.json]")
        sys.exit(1)

    drawing = sys.argv[1]
    save_to = sys.argv[2] if len(sys.argv) > 2 else None

    print(f"Extracting from: {drawing}")
    specs = extract_specs_from_drawing(drawing, save_raw_to=save_to)

    print(f"\nExtracted {len(specs)} component(s):")
    for s in specs:
        print(f"  {s.get('obj_id', '?'):30s}  obj_type={s.get('obj_type')}  operation={s.get('operation')}")

    if save_to:
        print(f"\nTo reload:  from claude_vision_pipeline import specs_from_json")
        print(f"            specs = specs_from_json('{save_to}')")