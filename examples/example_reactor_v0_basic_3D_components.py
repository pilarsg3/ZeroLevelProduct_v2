from assemble import assemble_objects
from ocp_vscode import show
import math
import cadquery as cq

from top_plate import create_top_plate

# ================================================================================================
# EXAMPLE: SMR primary loop - vessel, core, steam generators (polar coordinates)
# Dimensions in meters
# ================================================================================================

REACTOR_CORE = {
    "operation": "primitive",
    "obj_id": "core",
    "obj_type": "cylinder",
    "height": 1.3,
    "radius": 2 / 2,
    "center_coords": (0, 0, 1.5),
}

REACTOR_VESSEL = {
    "operation": "primitive",
    "obj_id": "rpv",
    "obj_type": "cylinder_closed_bottom",
    "height": 5.5,
    "outer_radius": 4.8 / 2,
    "wall_thickness": 0.04,
    "bottom_thickness": 5.5 - 4.3,
    "center_coords_pol": (0, 0, 0),
}

REACTOR_HX = [
    {
        "operation": "primitive",
        "obj_id": f"hx{i + 1}",
        "obj_type": "pipe",
        "height": 5,
        "outer_radius": 0.25,
        "inner_radius": 0.22,
        "center_coords_pol": (1.7, i * math.pi / 2, 4.5),
        "insert_into": "top1",        # ← inserts each HX into the top component
    }
    for i in range(4)
]

TOP_COMPONENT1 = {
    "obj_id": "top1",
    "operation": "revolve",
    "profile": [(0,0), (1,0), (1,1), (2.2,1.5), (2.2,2.6), (0,2.6)],
    "plane": "XZ",
    "angle": 360,
    "axis": "Z",
    "axis_point": (0, 0, 0),
    "center_coords": (0, 0, 5),
}

TOP_COMPONENT2 = {
    "obj_id": "top2",
    "operation": "revolve",
    "profile": [(0,0), (2,0), (2,0.5), (1.5,3), (1.5,4), (0,4)],
    "plane": "XZ",
    "angle": 360,
    "axis": "Z",
    "axis_point": (0, 0, 0),
    "center_coords": (0, 0, 5),
}

# ── Example 1: no top plate ───────────────────────────────────────────────────
assembly = assemble_objects([REACTOR_CORE, REACTOR_VESSEL, *REACTOR_HX, TOP_COMPONENT1])
show(assembly)


# ── Example 2: with top plate ─────────────────────────────────────────────────
# PLATE_THICKNESS  = 0.1
# PLATE_CENTROID_Z = 5.5 / 2 + PLATE_THICKNESS / 2

# top_plate = create_top_plate(
#     plate_outer_d   = 4.8,
#     plate_thickness = PLATE_THICKNESS,
#     center_coords   = (0.0, 0.0, PLATE_CENTROID_Z),
#     hole_groups=[
#         dict(
#             hole_diameter    = 0.52,
#             layout           = "custom_angles",
#             angles_deg       = [0.0, 90.0, 180.0, 270.0],
#             placement_radius = 1.7,
#         ),
#     ],
# )

# assembly = assemble_objects([REACTOR_CORE, REACTOR_VESSEL, *REACTOR_HX, TOP_COMPONENT1])
# assembly.add(top_plate, name="top_plate")
#show(assembly)