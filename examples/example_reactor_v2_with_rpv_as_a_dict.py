from assemble import assemble_objects
from ocp_vscode import show
import math

# ================================================================================================
# EXAMPLE: SMR primary loop — vessel, core, heat exchangers
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

REACTOR_HX = [
    {
        "operation": "primitive",
        "obj_id": f"hx{i + 1}",
        "obj_type": "pipe",
        "height": 5,
        "outer_radius": 0.25,
        "inner_radius": 0.22,
        "center_coords_pol": (1.7, i * math.pi / 2, 4.5)
    }
    for i in range(4)
]

RPV = {
    "operation":          "primitive",
    "obj_id":             "rpv",
    "obj_type":           "reactor_vessel",
    "inner_d":            4.72,
    "wall_t":             0.04,
    "straight_h":         5.5,
    "bottom_head_type":   "ellipsoidal",
    "bottom_head_params": {"head_depth": 1.0},
}

TOP_PLATE = {
    "operation":  "primitive",
    "obj_id":     "top_plate",
    "obj_type":   "reactor_top_plate",
    "outer_d":    4.72 + 2 * 0.04,
    "thickness":  0.1,
    "z_bottom":   5.5,
    "hole_groups": [
        dict(hole_diameter=0.52, layout="custom_angles",
             angles_deg=[0.0, 90.0, 180.0, 270.0], placement_radius=1.7),
    ],
}


assembly = assemble_objects([REACTOR_CORE, *REACTOR_HX, RPV, TOP_PLATE])
show(assembly)

