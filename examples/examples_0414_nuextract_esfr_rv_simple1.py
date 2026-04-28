from zzz_nuextract_pipeline import specs_from_json, patch_spec
from assemble import assemble_objects
from ocp_vscode import show


# ── Step 1: load the JSON extracted on the website ────────────────────────
specs = specs_from_json("examples/example_0414_esfr_rv_simple1.json")
assembly = assemble_objects(specs)
show(assembly)