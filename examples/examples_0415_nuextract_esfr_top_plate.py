from nuextract_pipeline import specs_from_json, patch_spec
from assemble import assemble_objects
from ocp_vscode import show


# ── Step 1: load the JSON extracted on the website ────────────────────────
specs = specs_from_json("examples/example_0415_esfr_top_plate.json")

specs = patch_spec(specs, "reactor_top_plate_1", {
    "thickness": 0.5,
    "z_bottom":  0.0,
    "hole_groups": [
        {"hole_diameter": 2.224, "layout": "explicit_positions", "positions": [(0.0, 0.0)]},
        {"hole_diameter": 1.600, "layout": "symmetric", "count": 3, "placement_radius": 2.730},
        {"hole_diameter": 1.350, "layout": "symmetric", "count": 3, "placement_radius": 3.369, "start_angle_deg": 60.0},
    ],
})




assembly = assemble_objects(specs)
show(assembly)

