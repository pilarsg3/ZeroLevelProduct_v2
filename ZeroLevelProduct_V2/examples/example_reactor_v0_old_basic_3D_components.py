from assemble import assemble_objects
from ocp_vscode import show
import math
import cadquery as cq
from typing import cast

from top_plate import create_top_plate
from utils import insert_into

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
    "rotation_angles": (0, 0, 0)
}

REACTOR_VESSEL = {
    "operation": "primitive",
    "obj_id": "rpv",
    "obj_type": "cylinder_closed_bottom",
    "height": 5.5,
    "outer_radius": 4.8 / 2,
    "wall_thickness": 0.04,
    "bottom_thickness": 5.5 - 4.3,
    "center_coords_pol": (0, 0, 0)
}

# REACTOR_HX = [
#     {"operation": "primitive",
#         "obj_id": f"hx{i + 1}",
#         "obj_type": "cylinder",
#         "height": 4,
#         "radius": 0.25,
#         "center_coords_pol": (1.7, i * math.pi / 2, 4.5)
#     }
#     for i in range(4)
# ]

REACTOR_HX = [
    {"operation": "primitive",
        "obj_id": f"hx{i + 1}",
        "obj_type": "pipe",
        "height": 5,
        "outer_radius": 0.25,
        "inner_radius": 0.22,
        "center_coords_pol": (1.7, i * math.pi / 2, 4.5)
    }
    for i in range(4)
]

# ── Top plate ─────────────────────────────────────────────────────────────────
# Vessel centroid at z=0, height=5.5 → top face at z=2.75
# Plate thickness=0.1 → centroid at z=2.75 + 0.05 = 2.8
# Holes match HX layout: r=1.7, angles 0/90/180/270 deg, diameter = HX OD + small clearance

PLATE_THICKNESS  = 0.1
VESSEL_TOP_FACE  = 5.5 / 2           # = 2.75
PLATE_CENTROID_Z = VESSEL_TOP_FACE + PLATE_THICKNESS / 2   # = 2.8

top_plate = create_top_plate(
    plate_outer_d   = 4.8,           # matches vessel outer diameter
    plate_thickness = PLATE_THICKNESS,
    center_coords   = (0.0, 0.0, PLATE_CENTROID_Z),
    hole_groups=[
        dict(
            hole_diameter    = 0.52,          # HX OD=0.5 + 0.02 clearance
            layout           = "custom_angles",
            angles_deg       = [0.0, 90.0, 180.0, 270.0],
            placement_radius = 1.7,
        ),
    ],
)

TOP_COMPONENT1 = {
    "obj_id": "top",
    "operation": "revolve",
    "profile": [(0,0), (1,0), (1,1), (2.2,1.5), (2.2,2.6), (0,2.6)],
    "plane": "XZ",
    "angle": 360,
    "axis": "Z",
    "axis_point": (0, 0, 0),
    "center_coords": (0, 0, 5),
    "rotation_angles": (0, 0, 0)
}

TOP_COMPONENT2 = {
    "obj_id": "top",
    "operation": "revolve",
    "profile": [(0,0), (2,0), (2,0.5), (1.5,3), (1.5,4), (0,4)],
    "plane": "XZ",
    "angle": 360,
    "axis": "Z",
    "axis_point": (0, 0, 0),
    "center_coords": (0, 0, 5),
    "rotation_angles": (0, 0, 0)
}

hxtest = {
    "obj_id": "hxtest",
    "operation": "sweep",
    "profile": {"obj_type": "circle", "radius": 0.25},
    "path": cq.Wire.assembleEdges([
        cq.Edge.makeLine(cq.Vector(4, 0, 0), cq.Vector(4, 0, 3.5)),
        cq.Edge.makeLine(cq.Vector(4, 0, 3.5), cq.Vector(2, 0, 3.5)),
    ]),
    "center_coords_pol": (1.5, 0, 4.5)
}


#show(assemble_objects([TOP_COMPONENT]))
#show(assemble_objects([REACTOR_CORE, REACTOR_VESSEL, *REACTOR_HX, TOP_COMPONENT]))
assembly = assemble_objects([REACTOR_CORE, REACTOR_VESSEL, *REACTOR_HX, TOP_COMPONENT1])
#assembly = assemble_objects([REACTOR_CORE, REACTOR_VESSEL, hxtest, TOP_COMPONENT1])


# ---------------------------- Post-process: insert HXs into top component (no top plate) ----------------------------
objects = {child.name: cast(cq.Workplane, child.obj) for child in assembly.children}

top = objects["top"]
for i in range(4):
    top = insert_into(top, objects[f"hx{i+1}"])
objects["top"] = top

# Rebuild assembly
final_assembly = cq.Assembly()
for obj_id, obj in objects.items():
    final_assembly.add(obj, name=obj_id)

show(final_assembly)




# ---------------------------- Post-process: insert HXs into top component (with top plate) ----------------------------
# ── Assemble ──────────────────────────────────────────────────────────────────
assembly = assemble_objects([REACTOR_CORE, REACTOR_VESSEL, *REACTOR_HX, TOP_COMPONENT1])
objects = {child.name: cast(cq.Workplane, child.obj) for child in assembly.children}

final_assembly = cq.Assembly()
for obj_id, obj in objects.items():
    final_assembly.add(obj, name=obj_id)
final_assembly.add(top_plate, name="top_plate")

#show(final_assembly)