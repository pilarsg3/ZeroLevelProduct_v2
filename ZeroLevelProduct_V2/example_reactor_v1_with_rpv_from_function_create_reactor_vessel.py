from assemble import assemble_objects
from reactor_vessel import create_reactor_vessel
from ocp_vscode import show
import math
import cadquery as cq

# ================================================================================================
# EXAMPLE 1: SMR primary loop — vessel, core, heat exchangers
# ================================================================================================

REACTOR_CORE = {
    "operation": "primitive",
    "obj_id": "core",
    "obj_type": "cylinder",
    "height": 1.3,
    "radius": 2 / 2,
    "center_coords": (0, 0, 1.5),
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
    }
    for i in range(4)
]

rpv, top_plate = create_reactor_vessel(
    inner_d    = 4.72,
    wall_t     = 0.04,
    straight_h = 5.5,
    bottom_head_type   = "ellipsoidal",
    bottom_head_params = {"head_depth": 1.0},
    top_plate_thickness = 0.1,
    top_plate_hole_groups=[
        dict(hole_diameter=1.0,  layout="explicit_positions", positions=[(0.0, 0.0)]),
        dict(hole_diameter=0.52, layout="custom_angles", angles_deg=[0.0, 90.0, 180.0, 270.0], placement_radius=1.7),
    ],
)

# assemble_objects handles insert_into automatically
assembly = assemble_objects([REACTOR_CORE, *REACTOR_HX])

# rpv and top_plate are pre-built — add them directly
assembly.add(rpv,       name="rpv")
assembly.add(top_plate, name="top_plate")

show(assembly)


# ================================================================================================
# EXAMPLE 2: Alternative RPV — torispherical bottom
# ================================================================================================

rpv_v2, top_plate_v2 = create_reactor_vessel(
    inner_d    = 3.5,
    wall_t     = 0.05,
    straight_h = 4.2,
    bottom_head_type   = "torispherical",
    bottom_head_params = {"Rc": 3.8, "rk": 0.15},
    top_plate_thickness = 0.08,
    top_plate_hole_groups=[
        dict(hole_diameter=0.35, layout="explicit_positions", positions=[(0.0, 0.0), (0.5, 0.5), (-0.5, -0.5)]),
        dict(hole_diameter=0.6,  layout="custom_angles", angles_deg=[45.0, 135.0, 225.0, 315.0], placement_radius=1.2),
    ],
)

show(rpv_v2, top_plate_v2)