from zzz_nuextract_pipeline import extract_specs_from_drawing, patch_spec
from assemble import assemble_objects
from ocp_vscode import show



"""
# 1. drawing → specs


specs = extract_specs_from_drawing(
    "examples/esfr_smr_vessel_drawing.png",
    api_key    = "78aa77aef0bc493489cc81f504f68f03",
    project_id = "745256fc-e8d7-4369-b62f-c4d9bda7ceaf",
    save_raw_to = "debug_raw.json",
)



# 2. patch anything NuExtract couldn't read (e.g. wall_t not on drawing)
# specs = patch_spec(specs, "rpv", {"wall_t": 0.05})

# 3. assemble & show
assembly = assemble_objects(specs)
show(assembly)


#def extract_specs_from_drawing(
#    drawing_path: str | Path,
#    api_key:     str | None = None,   # ← real parameter
#    api_base:    str | None = None,   # ← real parameter
#    model:       str | None = None,
#    save_raw_to: str | Path | None = None,
#)

"""


"""
examples_0414_nuextract.py
==========================
Recommended workflow:
  1. Go to nuextract.ai → Tests Reactor Vessel project → Workspace tab
  2. Drag your drawing into the Playground and click Extract
  3. Copy the output JSON, save as debug_raw.json in the project root
  4. Run this script
"""

from zzz_nuextract_pipeline import specs_from_json, patch_spec
from assemble import assemble_objects
from ocp_vscode import show

# ── Step 1: load the JSON extracted on the website ────────────────────────
specs = specs_from_json("debug_raw.json")


"""
# ── Step 2: patch values NuExtract couldn't read from the drawing ─────────
# reactor_vessel: inner_d and wall_t are not annotated on the drawing
specs = patch_spec(specs, "reactor_vessel_1", {
    "operation":  "primitive",          # NuExtract misread as "extrude"
    "inner_d":    8.91,                 # outer_d(9.01) - 2 * wall_t(0.05)
    "wall_t":     0.05,
    "straight_h": 9.0,                  # NuExtract put this in "height"
    "bottom_head_params": {
        "Rc": 5.245,
        "rk": 0.379,
    },
})

# reactor_top_plate: z_bottom not on drawing — sits flush on top of vessel
specs = patch_spec(specs, "reactor_top_plate_1", {
    "z_bottom": 9.0,
})

specs = patch_spec(specs, "reactor_top_plate_1", {
    "z_bottom": 9.0,
    "hole_groups": [
        # centre hole — Ø2224
        {"hole_diameter": 2.224, "layout": "explicit_positions", "positions": [(0.0, 0.0)]},
        # inner ring — 3x Ø1600 at r=2730
        {"hole_diameter": 1.600, "layout": "symmetric", "count": 3, "placement_radius": 2.730},
        # outer ring — 3x Ø1350 at r=3369, offset 60°
        {"hole_diameter": 1.350, "layout": "symmetric", "count": 3, "placement_radius": 3.369, "start_angle_deg": 60.0},
    ],
})
"""

# ── Step 3: assemble and show ─────────────────────────────────────────────
assembly = assemble_objects(specs)
show(assembly)