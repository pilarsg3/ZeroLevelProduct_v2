from nuextract_pipeline import specs_from_json, patch_spec
from assemble import assemble_objects
from ocp_vscode import show


# ── Step 1: load the JSON extracted on the website ────────────────────────
specs = specs_from_json("examples/example_0415_esfr_rv_simple2.json")
specs = patch_spec(specs, "reactor_vessel_1", {
    "wall_t":  0.05,
    "inner_d": 8.91,   # override the wrong value NuExtract computed
})
specs = patch_spec(specs, "reactor_vessel_1", {
    "wall_t":           0.05,
    "inner_d":          8.91,
    "bottom_head_type": "torispherical",
    "bottom_head_params": {"Rc": 5.245, "rk": 0.379},
})

assembly = assemble_objects(specs)
show(assembly)

