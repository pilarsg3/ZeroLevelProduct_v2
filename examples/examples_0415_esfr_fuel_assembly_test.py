"""
from nuextract_pipeline import specs_from_json, patch_spec
from assemble import assemble_objects
from ocp_vscode import show


# ── Step 1: load the JSON extracted on the website ────────────────────────
specs = specs_from_json("examples/example_0415_esfr_fuel_assembly_test.json")
print([s["obj_id"] for s in specs])
specs = patch_spec(specs, "hex_head", {
    "operation":      "extrude",
    "obj_type":       None,
    "profile":        {"obj_type": "regular_polygon", "radius": 0.0915, "nmb_of_sides": 6},
    "height":         0.150,
    "wall_thickness": (0.090 - 0.058) / 2,   # = 0.016m
})




assembly = assemble_objects(specs)
show(assembly)
"""











"""
import json
from nuextract_pipeline import postprocess
from assemble import assemble_objects
from ocp_vscode import show

with open("examples/example_0415_esfr_fuel_assembly_test.json") as f:
    raw = json.load(f)

# patch hex_head in raw before postprocess
for comp in raw["components"]:
    if comp["obj_id"] == "hex_head":
        comp["operation"]      = "extrude"   # ← add this line
        comp["profile_radius"] = 91.5
        comp["extrude_height"] = 150

specs = postprocess(raw)
print([s["obj_id"] for s in specs])
assembly = assemble_objects(specs)
show(assembly)
"""



"""
import json
from nuextract_pipeline import postprocess
from assemble import assemble_objects
from ocp_vscode import show

with open("examples/example_0415_esfr_fuel_assembly_test.json") as f:
    raw = json.load(f)

# drop redundant pipe components (already captured in hex_head via wall_thickness)
raw["components"] = [c for c in raw["components"]
                     if c["obj_id"] not in ("inner_pipe", "outer_pipe")]

# patch raw (in mm) before postprocess scales to metres
for comp in raw["components"]:
    if comp["obj_id"] == "hex_head":
        comp["operation"]      = "extrude"
        comp["profile_radius"] = 91.5    # across-flats 183/2
        comp["extrude_height"] = 150
        comp["wall_thickness"] = 16.0    # (90 - 58) / 2

specs    = postprocess(raw)
print([s["obj_id"] for s in specs])
assembly = assemble_objects(specs)
show(assembly)
"""


"""
import json
from nuextract_pipeline import postprocess
from assemble import assemble_objects
from ocp_vscode import show

with open("examples/example_0415_esfr_fuel_assembly_test.json") as f:
    raw = json.load(f)

# drop redundant pipe components
raw["components"] = [c for c in raw["components"]
                     if c["obj_id"] not in ("inner_pipe", "outer_pipe")]

# patch raw (in mm) before postprocess scales to metres
for comp in raw["components"]:
    if comp["obj_id"] == "main_body":
        comp["height"]   = 3914
        comp["center_z"] = 150 + 3914 / 2   # starts after hex head

    if comp["obj_id"] == "hex_head":
        comp["operation"]      = "extrude"
        comp["profile_radius"] = 91.5
        comp["extrude_height"] = 150
        comp["wall_thickness"] = 16.0
        comp["center_z"]       = 75          # z=0 to z=150, centred at 75

specs    = postprocess(raw)
assembly = assemble_objects(specs)
show(assembly)
"""




"""
import json
from nuextract_pipeline import postprocess
from assemble import assemble_objects
from ocp_vscode import show

with open("examples/example_0415_esfr_fuel_assembly_test.json") as f:
    raw = json.load(f)

# drop redundant pipe components
raw["components"] = [c for c in raw["components"]
                     if c["obj_id"] not in ("inner_pipe", "outer_pipe")]

# patch raw (in mm) before postprocess scales to metres
for comp in raw["components"]:
    if comp["obj_id"] == "main_body":
        for f in ("radius", "height", "outer_d", "inner_d", "wall_t",
                "outer_radius", "inner_radius", "length", "width"):
            comp[f] = None
        comp["operation"]        = "extrude"
        comp["obj_type"]         = None
        comp["profile_obj_type"] = "regular_polygon"
        comp["profile_radius"]   = 86.6
        comp["profile_nmb_of_sides"] = 6
        comp["extrude_height"]   = 3314
        comp["center_z"]         = 3314 / 2

    if comp["obj_id"] == "hex_head":
        comp["profile_obj_type"] = None   # ← clear so no profile is built
        comp["obj_type"]  = "cylinder"
        comp["radius"]    = 15
        comp["height"]    = 600
        comp["center_z"]  = 3314 + 300
        comp["extrude_height"] = None     # ← clear this too

specs    = postprocess(raw)
assembly = assemble_objects(specs)
show(assembly)
"""

import json
from zzz_nuextract_pipeline import postprocess
from assemble import assemble_objects
from ocp_vscode import show

with open("examples/example_0415_esfr_fuel_assembly_test.json") as f:
    raw = json.load(f)

# drop redundant pipe components
raw["components"] = [c for c in raw["components"]
                     if c["obj_id"] not in ("inner_pipe", "outer_pipe")]

# patch raw (in mm) before postprocess scales to metres
for comp in raw["components"]:
    if comp["obj_id"] == "main_body":
        for f in ("radius", "height", "outer_d", "inner_d", "wall_t",
                  "outer_radius", "inner_radius", "length", "width"):
            comp[f] = None
        comp["obj_type"]     = "pipe"
        comp["outer_radius"] = 45        # Ø90 / 2
        comp["inner_radius"] = 29        # Ø58 / 2
        comp["height"]       = 3914      # full length
        comp["center_z"]     = 3914 / 2
        comp["center_x"]     = 0
        comp["center_y"]     = 0
        comp["obj_id"]       = "inner_pipe_full"

    if comp["obj_id"] == "hex_head":
        for f in ("radius", "height", "outer_d", "inner_d", "wall_t",
                  "outer_radius", "inner_radius", "length", "width"):
            comp[f] = None
        comp["operation"]            = "extrude"
        comp["obj_type"]             = None
        comp["profile_obj_type"]     = "regular_polygon"
        comp["profile_radius"]       = 86.6
        comp["profile_nmb_of_sides"] = 6
        comp["extrude_height"]       = 3314
        comp["center_z"]             = 150 + 3314 / 2   # z=150 to z=3464
        comp["center_x"]             = 0
        comp["center_y"]             = 0
        comp["obj_id"]               = "hex_rod"

specs    = postprocess(raw)
assembly = assemble_objects(specs)
show(assembly)


