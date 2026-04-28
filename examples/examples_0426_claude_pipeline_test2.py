from claude_pipeline import extract_specs_from_drawing, patch_spec
from assemble import assemble_objects
from ocp_vscode import show

specs = extract_specs_from_drawing(
    "examples/esfr_smr_vessel_drawing.png",
    save_raw_to="examples/claude_pipeline_test2.json",
)

specs = patch_spec(specs, "reactor_main_vessel", {"wall_t": 0.04})
assembly = assemble_objects(specs)
show(assembly)