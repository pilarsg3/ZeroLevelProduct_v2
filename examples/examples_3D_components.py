from components_3D_primitives import set_components
import math
from ocp_vscode import show






# ================================================================================================
# EXAMPLE 1: Basic 3D primitives without overlaps
# ================================================================================================

BOX_1 = {
    "obj_id": "box1",
    "obj_type": "box",
    "length": 4,
    "width": 6,
    "height": 4
}

CYLINDER_1 = {
    "obj_id": "cylinder1",
    "obj_type": "cylinder",
    "height": 3,
    "radius": 2,
    "center_coords": (5, 5, 5)
}

CYLINDER_2 = {
    "obj_id": "cylinder2",
    "obj_type": "cylinder",
    "height": 5,
    "radius": 2,
    "center_coords": (10, -5, 7),
    "rotation_angles": (10, 45, 30)
}

SPHERE_1 = {
    "obj_id": "sphere1",
    "obj_type": "sphere",
    "radius": 2,
    "center_coords": (-3, -5, -3)
}

WEDGE_1 = {
    "obj_id": "wedge1",
    "obj_type": "wedge",
    "dx": 10, "dy": 6, "dz": 4,
    "xmin": 0, "zmin": 0,
    "xmax": 10, "zmax": 2,
    "center_coords": (10, 10, 0)
}

CYLINDER_CLOSED_BOTTOM_1 = {
    "obj_id": "cylinder_closed_bottom1",
    "obj_type": "cylinder_closed_bottom",
    "height": 6,
    "outer_radius": 2.5,
    "wall_thickness": 0.4,
    "bottom_thickness": 1.0,
    "center_coords": (20, 0, 0),
    "rotation_angles": (0, 0, 0)
}

EXAMPLE_1 = [BOX_1, CYLINDER_1, SPHERE_1, CYLINDER_2, WEDGE_1, CYLINDER_CLOSED_BOTTOM_1]

# ================================================================================================
# EXAMPLE 2: Overlapping cylinders
# ================================================================================================

CYLINDER_3 = {
    "obj_id": "cylinder3",
    "obj_type": "cylinder",
    "height": 5,
    "radius": 2,
    "rotation_angles": (10, 45, 30)
}

CYLINDER_4 = {
    "obj_id": "cylinder4",
    "obj_type": "cylinder",
    "height": 5,
    "radius": 2,
    "center_coords": (0, 0, 5)
}

EXAMPLE_2 = [CYLINDER_3, CYLINDER_4]


# ================================================================================================
# EXAMPLE 3: Reactor vessel model with core and heat exchangers (polar coordinates)
# Dimensions in meters
# ================================================================================================

REACTOR_CORE = {
    "obj_id": "core",
    "obj_type": "cylinder",
    "height": 1.3,  # active height
    "radius": 2 / 2,  # core diameter = 2 m
    "center_coords": (0, 0, 1.5),
    "rotation_angles": (0, 0, 0)
}

REACTOR_VESSEL = {
    "obj_id": "rpv",
    "obj_type": "cylinder_closed_bottom",
    "height": 5.5,
    "outer_radius": 4.8 / 2,
    "wall_thickness": 0.04,
    "bottom_thickness": 5.5 - 4.3,  # vessel height - cylindrical section height
    "center_coords_pol": (0, 0, 0)
}

# Heat exchangers at 90-degree intervals around the vessel
# Use r=1.7 for non-overlapping, r=1.0 for overlapping configurations
REACTOR_HX_RADIUS = 1.7
EXAMPLE_3 = [REACTOR_CORE, REACTOR_VESSEL] + [
    {
        "obj_id": f"hx{i + 1}",
        "obj_type": "cylinder",
        "height": 2,
        "radius": 0.25,
        "center_coords_pol": (REACTOR_HX_RADIUS, i * math.pi / 2, 3.5)
    }
    for i in range(4)
]



# ================================================================================================
# EXAMPLE 4: Examples of the cylinder with closed bottom with different head types
# ================================================================================================


# Flat (legacy style — still works)
CYLINDER_CLOSED_BOTTOM_FLAT = {
    "obj_id": "ccb_flat",
    "obj_type": "cylinder_closed_bottom",
    "height": 6, "outer_radius": 2.5, "wall_thickness": 0.4,
    "bottom_thickness": 1.0,          # ← old key, still accepted
    "center_coords": (20, 0, 0),
}

# Hemispherical — no extra params needed
CYLINDER_CLOSED_BOTTOM_HEMI = {
    "obj_id": "ccb_hemi",
    "obj_type": "cylinder_closed_bottom",
    "height": 6, "outer_radius": 2.5, "wall_thickness": 0.4,
    "bottom_head_type": "hemispherical",
    "center_coords": (30, 0, 0),
}

# Ellipsoidal — head_depth required
CYLINDER_CLOSED_BOTTOM_ELLIP = {
    "obj_id": "ccb_ellip",
    "obj_type": "cylinder_closed_bottom",
    "height": 6, "outer_radius": 2.5, "wall_thickness": 0.4,
    "bottom_head_type":   "ellipsoidal",
    "bottom_head_params": {"head_depth": 0.8},
    "center_coords": (40, 0, 0),
}

# Torispherical — Rc / rk optional (have sensible defaults)
CYLINDER_CLOSED_BOTTOM_TORI = {
    "obj_id": "ccb_tori",
    "obj_type": "cylinder_closed_bottom",
    "height": 6, "outer_radius": 2.5, "wall_thickness": 0.4,
    "bottom_head_type":   "torispherical",
    "bottom_head_params": {"Rc": 5.0, "rk": 0.3},
    "center_coords": (50, 0, 0),
}




#set_components([CYLINDER_CLOSED_BOTTOM_ELLIP, CYLINDER_CLOSED_BOTTOM_FLAT, CYLINDER_CLOSED_BOTTOM_HEMI, CYLINDER_CLOSED_BOTTOM_TORI])















# ================================================================================================
# Main execution (uncomment to run)
# ================================================================================================

# Uncomment one of the following to test:
#set_components(EXAMPLE_1)
set_components(EXAMPLE_2)
#set_components(EXAMPLE_3)













