# All units in metres (divide drawing mm by 1000)
# ⚠ wall_t not explicit in drawing — 0.05 m assumed

from assemble import assemble_objects
from ocp_vscode import show

RPV = {
    "operation":          "primitive",
    "obj_id":             "rpv",
    "obj_type":           "reactor_vessel",
    "inner_d":            8.91,       # OD 9.01 − 2 × 0.05
    "wall_t":             0.05,
    "straight_h":         9.0,
    "bottom_head_type":   "torispherical",
    "bottom_head_params": {"Rc": 5.245, "rk": 0.379},
}

TOP_PLATE = {
    "operation": "primitive",
    "obj_id":    "top_plate",
    "obj_type":  "reactor_top_plate",
    "outer_d":   10.0,
    "thickness": 0.5,
    "z_bottom":  9.0,          # sits flush on top of straight section
    "hole_groups": [
        {   # central penetration
            "hole_diameter": 2.224,
            "layout":        "explicit_positions",
            "positions":     [(0.0, 0.0)],
        },
        {   # inner ring — 3 × Ø1600 at r = 2730 mm
            "hole_diameter":    1.600,
            "layout":           "symmetric",
            "count":            3,
            "placement_radius": 2.730,
            "start_angle_deg":  0.0,
        },
        {   # outer ring — 3 × Ø1350 at r = 3369 mm, offset 60°
            "hole_diameter":    1.350,
            "layout":           "symmetric",
            "count":            3,
            "placement_radius": 3.369,
            "start_angle_deg":  60.0,
        },
    ],
}

show(assemble_objects([RPV, TOP_PLATE]))






