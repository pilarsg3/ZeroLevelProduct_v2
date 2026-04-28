"""
from nuextract_pipeline import specs_from_json, patch_spec
from assemble import assemble_objects
from ocp_vscode import show


# ── Step 1: load the JSON extracted on the website ────────────────────────
specs = specs_from_json("examples/example_0415_esfr_core_test.json")
specs = patch_spec(specs, "core", {
    "radius": 2.142,   # 4284mm / 2
    "height": 1.3,     # not on drawing
})

assembly = assemble_objects(specs)
show(assembly)
"""
import json
from zzz_nuextract_pipeline import postprocess, patch_spec
from assemble import assemble_objects
from ocp_vscode import show

# load raw JSON
with open("examples/example_0415_esfr_core_test.json") as f:
    raw = json.load(f)

# patch the raw component BEFORE postprocess filters it out
for comp in raw["components"]:
    if comp.get("obj_id") == "core":
        comp["radius"] = 2142.0   # in mm — postprocess will scale to metres
        comp["height"] = 1300.0   # in mm

specs    = postprocess(raw)
assembly = assemble_objects(specs)
show(assembly)
