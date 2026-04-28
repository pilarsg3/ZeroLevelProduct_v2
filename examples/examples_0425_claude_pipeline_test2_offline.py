from claude_pipeline import specs_from_json, patch_spec
from assemble import assemble_objects
from ocp_vscode import show

specs = specs_from_json("examples/claude_pipeline_test2.json")
specs = [s for s in specs if s.get("obj_id") != "bottom_drain_nozzle"]
specs = patch_spec(specs, "reactor_main_vessel", {"wall_t": 0.04})
specs = patch_spec(specs, "reactor_top_plate", {
    "hole_groups": [
        {"hole_diameter": 2.224, "layout": "explicit_positions", "positions": [(0.0, 0.0)]},
        {"hole_diameter": 1.35,  "layout": "symmetric", "count": 6, "placement_radius": 2.73},
    ]
})


assembly = assemble_objects(specs)
show(assembly)