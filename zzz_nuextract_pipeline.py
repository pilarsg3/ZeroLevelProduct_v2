"""
nuextract_pipeline.py
=====================
Pipeline: technical drawing  →  assemble_objects() specs.

Two workflows
-------------
A) RECOMMENDED — extract on nuextract.ai website (better model), save JSON,
   load here:

    from nuextract_pipeline import specs_from_json, patch_spec
    specs = specs_from_json("debug_raw.json")
    specs = patch_spec(specs, "reactor_vessel_1", {"inner_d": 8.91, ...})

B) FULLY AUTOMATED — extract via API (requires numind SDK + project setup):

    from nuextract_pipeline import extract_specs_from_drawing, patch_spec
    specs = extract_specs_from_drawing("drawing.png", api_key=..., project_id=...)

Environment variables for option B
-----------------------------------
    NUEXTRACT_API_KEY    — your API key
    NUEXTRACT_PROJECT_ID — your project ID
"""

from __future__ import annotations

import asyncio
import json
import os
import warnings
from pathlib import Path
from typing import Any


# ---------------------------------------------------------------------------
# 1.  SCHEMA  (reference copy — paste into nuextract.ai project Template field)
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
                "reactor_vessel", "reactor_top_plate",
            ],

            "radius": "number",
            "height": "number",
            "outer_radius": "number",
            "inner_radius": "number",
            "length": "number",
            "width":  "number",

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

            "revolve_angle": "number",
            "revolve_axis":  ["X", "Y", "Z"],

            "plane": ["XY", "XZ", "YZ"],
        }
    ],
}


# ---------------------------------------------------------------------------
# 2.  POST-PROCESSING
#     Flat NuExtract output  →  nested assemble_objects() spec list.
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
}


def _sc(value: Any, s: float) -> Any:
    if isinstance(value, (int, float)):
        return value * s
    if isinstance(value, list):
        return [_sc(v, s) for v in value]
    return value


def _rebuild_component(c: dict[str, Any], s: float) -> dict[str, Any]:
    """Rebuild one flat NuExtract component into a nested assemble_objects spec."""
    spec: dict[str, Any] = {}

    #for f in ("obj_id", "operation", "obj_type", "insert_into", "plane"):
    #    if c.get(f):
    #        spec[f] = c[f]


    for f in ("obj_id", "operation", "insert_into", "plane"):
        if c.get(f):
            spec[f] = c[f]
    # only add obj_type if there's no profile (profile-based ops don't use obj_type)
    if c.get("obj_type") and not c.get("profile_obj_type"):
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

    return spec


def postprocess(raw: dict[str, Any]) -> list[dict[str, Any]]:
    """
    Convert raw NuExtract JSON into clean assemble_objects() spec list.

    Parameters
    ----------
    raw : dict
        Parsed NuExtract output — from API or loaded from a JSON file.

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
        # skip ghost components — obj_type present but no useful dimensions extracted
        _REQUIRED_BY_TYPE = {
            "reactor_vessel":    ("outer_d", "inner_d", "straight_h", "height"),
            "reactor_top_plate": ("outer_d",),
        }
        obj_type = rebuilt.get("obj_type")
        if obj_type in _REQUIRED_BY_TYPE:
            if not any(rebuilt.get(f) for f in _REQUIRED_BY_TYPE[obj_type]):
                continue
        elif obj_type and not any(rebuilt.get(f) for f in (
            "radius", "height", "length", "outer_radius", "extrude_height",
        )) and not rebuilt.get("profile"):
            continue
        specs.append(rebuilt)

    return specs


# ---------------------------------------------------------------------------
# 3.  WORKFLOW A — load JSON saved from nuextract.ai website  (RECOMMENDED)
# ---------------------------------------------------------------------------

def specs_from_json(json_path: str | Path) -> list[dict[str, Any]]:
    """
    Load a NuExtract JSON file saved from the website and postprocess it.

    This is the recommended approach — the nuextract.ai website uses a higher
    quality model than the default API tier.

    Steps
    -----
    1. Go to nuextract.ai → your project → Workspace tab
    2. Drag your drawing into the Playground and click Extract
    3. Copy the output JSON and save it as a .json file
    4. Pass that file path here

    Parameters
    ----------
    json_path : str | Path
        Path to the JSON file saved from nuextract.ai.

    Returns
    -------
    list[dict]
        Clean spec list, ready for assemble_objects().

    Example
    -------
    >>> specs = specs_from_json("debug_raw.json")
    >>> specs = patch_spec(specs, "reactor_vessel_1", {"inner_d": 8.91})
    >>> assembly = assemble_objects(specs)
    """
    json_path = Path(json_path)
    if not json_path.exists():
        raise FileNotFoundError(f"JSON file not found: {json_path}")
    with open(json_path) as f:
        raw = json.load(f)
    return postprocess(raw)


# ---------------------------------------------------------------------------
# 4.  WORKFLOW B — fully automated API extraction
# ---------------------------------------------------------------------------

async def _extract_async(
    drawing_path: Path,
    api_key:      str,
    project_id:   str,
) -> dict[str, Any]:
    from numind import NuMindAsync
    client = NuMindAsync(api_key=api_key)
    response = await client.extract_structured_data(
        project_id = project_id,
        input_file = drawing_path,
    )
    raw = response.result
    if isinstance(raw, str):
        raw = json.loads(raw)
    return raw


def extract_from_drawing(
    drawing_path: str | Path,
    api_key:      str | None = None,
    project_id:   str | None = None,
) -> dict[str, Any]:
    """Send a drawing to the NuExtract API and return the raw extracted dict."""
    key = api_key    or os.environ.get("NUEXTRACT_API_KEY")
    pid = project_id or os.environ.get("NUEXTRACT_PROJECT_ID")

    if not key:
        raise ValueError("No API key. Pass api_key= or set NUEXTRACT_API_KEY env var.")
    if not pid:
        raise ValueError("No project ID. Pass project_id= or set NUEXTRACT_PROJECT_ID env var.")

    drawing_path = Path(drawing_path)
    if not drawing_path.exists():
        raise FileNotFoundError(f"Drawing not found: {drawing_path}")

    return asyncio.run(_extract_async(drawing_path, key, pid))


def extract_specs_from_drawing(
    drawing_path: str | Path,
    api_key:      str | None = None,
    project_id:   str | None = None,
    save_raw_to:  str | Path | None = None,
) -> list[dict[str, Any]]:
    """Fully automated pipeline: drawing image → assemble_objects() spec list."""
    raw = extract_from_drawing(drawing_path, api_key=api_key, project_id=project_id)

    if save_raw_to is not None:
        save_raw_to = Path(save_raw_to)
        save_raw_to.parent.mkdir(parents=True, exist_ok=True)
        with open(save_raw_to, "w") as f:
            json.dump(raw, f, indent=2)
        print(f"Raw extraction saved → {save_raw_to}")

    return postprocess(raw)


# ---------------------------------------------------------------------------
# 5.  MANUAL OVERRIDE HELPER
# ---------------------------------------------------------------------------

def patch_spec(
    specs:   list[dict[str, Any]],
    obj_id:  str,
    updates: dict[str, Any],
) -> list[dict[str, Any]]:
    """
    Apply manual overrides to one component after extraction.

    Useful for values not on the drawing (e.g. wall_t, inner_d).

    Example
    -------
    >>> specs = patch_spec(specs, "reactor_vessel_1", {"inner_d": 8.91, "wall_t": 0.05})
    """
    for spec in specs:
        if spec.get("obj_id") == obj_id:
            spec.update(updates)
            return specs
    raise KeyError(f"No component with obj_id='{obj_id}' found in specs.")