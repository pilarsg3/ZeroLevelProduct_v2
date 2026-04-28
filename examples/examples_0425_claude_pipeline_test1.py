from claude_pipeline import extract_specs_from_drawing, patch_spec
from assemble import assemble_objects

specs = extract_specs_from_drawing(
    "examples/esfr_smr_vessel_drawing.png",
    save_raw_to="examples/example_claude_pipeline_test1.json",
)

# inspect example_claude_pipeline_test1.json, then patch whatever Claude missed
specs = patch_spec(specs, "reactor_vessel_main", {"wall_t": 0.04})

assembly = assemble_objects(specs)