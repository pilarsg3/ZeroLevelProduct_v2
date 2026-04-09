# examples.py
import math
import cadquery as cq
from ocp_vscode import show

from profile_built_in_2D_sketch import build_2D_sketch
from components_3D_primitives import set_components
from utils import extrude_profile, revolve_profile


# ------------------------------------------------------------------------------
# ── 2D → extrude examples ─────────────────────────────────────────────────────
# ------------------------------------------------------------------------------
ex_rect            = {"obj_type": "rectangle",       "width": 20,  "height": 10}
ex_circle          = {"obj_type": "circle",           "radius": 8}
ex_ellipse         = {"obj_type": "ellipse",          "r1": 12,     "r2": 6}
ex_trapezoid       = {"obj_type": "trapezoid",        "width": 20,  "height": 10, "a1": 75}
ex_slot            = {"obj_type": "slot",             "width": 25,  "height": 8}
ex_regular_polygon = {"obj_type": "regular_polygon",  "radius": 10, "nmb_of_sides": 6}
ex_polygon         = {"obj_type": "polygon",          "pts": [(0, 0), (20, 0), (10, 15)]}

rect            = extrude_profile(build_2D_sketch(ex_rect, sketch_plane="XZ"),            height=10)
circle          = extrude_profile(build_2D_sketch(ex_circle),          height=10)
ellipse         = extrude_profile(build_2D_sketch(ex_ellipse),         height=10)
trapezoid       = extrude_profile(build_2D_sketch(ex_trapezoid),       height=10)
slot            = extrude_profile(build_2D_sketch(ex_slot),            height=10)
regular_polygon = extrude_profile(build_2D_sketch(ex_regular_polygon), height=10)
polygon         = extrude_profile(build_2D_sketch(ex_polygon),         height=10)

ellipse_sym     = extrude_profile(build_2D_sketch(ex_ellipse),                    height=10, both=True)
circle_xz       = extrude_profile(build_2D_sketch(ex_circle, sketch_plane="XZ"), height=15)

# show(rect)
# show(rect, circle, ellipse, trapezoid, slot, regular_polygon, polygon)



# ------------------------------------------------------------------------------
# ── 2D → revolve examples ─────────────────────────────────────────────────────
# ------------------------------------------------------------------------------
# ── Full 360° revolves around Z ───────────────────────────────────────────────

# Rectangle off-axis → hollow cylinder (tube)
rect_tube = revolve_profile(
    build_2D_sketch({"obj_type": "rectangle", "width": 10, "height": 20}, sketch_plane="XZ"),
    angle=30.0,
    axis="Z",
    axis_point=(0, 0, 0),      # x-offset >= width/2=5 to clear the axis
)
# wp = build_2D_sketch({"obj_type": "rectangle", "width": 10, "height": 20}, sketch_plane="XZ")
# val = wp.val()
# print(type(val))
# faces = val._faces.Faces()
# print(f"num faces: {len(faces)}")
# bb = faces[0].BoundingBox()
# print(f"x: [{bb.xmin:.2f}, {bb.xmax:.2f}]")
# print(f"y: [{bb.ymin:.2f}, {bb.ymax:.2f}]")
# print(f"z: [{bb.zmin:.2f}, {bb.zmax:.2f}]")

# Circle off-axis → torus
torus = revolve_profile(
    build_2D_sketch({"obj_type": "circle", "radius": 3}, sketch_plane="XZ"),
    angle=360.0,
    axis="Z",
    axis_point=(10, 0, 0),      # major radius = 10, minor radius = 3
)

# Ellipse off-axis → elliptic torus
elliptic_torus = revolve_profile(
    build_2D_sketch({"obj_type": "ellipse", "r1": 4, "r2": 2}, sketch_plane="XZ"),
    angle=360.0,
    axis="Z",
    axis_point=(12, 0, 0),
)

# Regular polygon off-axis → faceted torus (hexagonal cross-section)
hex_torus = revolve_profile(
    build_2D_sketch({"obj_type": "regular_polygon", "radius": 3, "nmb_of_sides": 6}, sketch_plane="XZ"),
    angle=360.0,
    axis="Z",
    axis_point=(10, 0, 0),
)


# ── Partial revolves ──────────────────────────────────────────────────────────

# Rectangle → 90° pipe elbow cross-section
elbow_90 = revolve_profile(
    build_2D_sketch({"obj_type": "rectangle", "width": 4, "height": 6}, sketch_plane="XZ"),
    angle=90.0,
    axis="Z",
    axis_point=(12, 0, 0),
)

# Trapezoid → 180° dome-like solid
dome = revolve_profile(
    build_2D_sketch({"obj_type": "trapezoid", "width": 8, "height": 6, "a1": 75}, sketch_plane="XZ"),
    angle=180.0,
    axis="Z",
    axis_point=(8, 0, 0),
)


# ── Revolve around X and Y axes ───────────────────────────────────────────────

# Circle revolved around X → torus lying on its side
torus_x = revolve_profile(
    build_2D_sketch({"obj_type": "circle", "radius": 3}, sketch_plane="YZ"),
    angle=360.0,
    axis="X",
    axis_point=(0, 10, 0),      # offset in Y (perpendicular to X-axis)
)

# Rectangle revolved around Y → disc / flange
flange = revolve_profile(
    build_2D_sketch({"obj_type": "rectangle", "width": 6, "height": 2}, sketch_plane="XZ"),
    angle=360.0,
    axis="Y",
    axis_point=(8, 0, 0),       # offset in X (perpendicular to Y-axis)
)


# ── Reactor-relevant: coolant plenum cross-section ────────────────────────────

plenum = revolve_profile(
    build_2D_sketch({"obj_type": "slot", "width": 6, "height": 3}, sketch_plane="XZ"),
    angle=360.0,
    axis="Z",
    axis_point=(15, 0, 0),
)


# ── Visualise (uncomment one at a time) ──────────────────────────────────────

#show(rect_tube)
# show(torus)
# show(elliptic_torus)
# show(hex_torus)
# show(elbow_90)
# show(dome)
# show(torus_x)
# show(flange)
# show(plenum)













# ------------------------------------------------------------------------------
# ── 3D primitives examples ────────────────────────────────────────────────────
# ------------------------------------------------------------------------------
BOX_1 = {
    "obj_id": "box1", "obj_type": "box",
    "length": 4, "width": 6, "height": 4
}
CYLINDER_1 = {
    "obj_id": "cylinder1", "obj_type": "cylinder",
    "height": 3, "radius": 2, "center_coords": (5, 5, 5)
}
CYLINDER_2 = {
    "obj_id": "cylinder2", "obj_type": "cylinder",
    "height": 5, "radius": 2,
    "center_coords": (10, -5, 7), "rotation_angles": (10, 45, 30)
}
SPHERE_1 = {
    "obj_id": "sphere1", "obj_type": "sphere",
    "radius": 2, "center_coords": (-3, -5, -3)
}
WEDGE_1 = {
    "obj_id": "wedge1", "obj_type": "wedge",
    "dx": 10, "dy": 6, "dz": 4,
    "xmin": 0, "zmin": 0, "xmax": 10, "zmax": 2,
    "center_coords": (10, 10, 0)
}
CYLINDER_CLOSED_BOTTOM_1 = {
    "obj_id": "cylinder_closed_bottom1", "obj_type": "cylinder_closed_bottom",
    "height": 6, "outer_radius": 2.5, "wall_thickness": 0.4, "bottom_thickness": 1.0,
    "center_coords": (20, 0, 0)
}

OVERLAPPING_A = {
    "obj_id": "cyl_a", "obj_type": "cylinder",
    "height": 5, "radius": 2, "rotation_angles": (10, 45, 30)
}
OVERLAPPING_B = {
    "obj_id": "cyl_b", "obj_type": "cylinder",
    "height": 5, "radius": 2, "center_coords": (0, 0, 5)
}

REACTOR_CORE = {
    "obj_id": "core", "obj_type": "cylinder",
    "height": 1.3, "radius": 1.0, "center_coords": (0, 0, 1.5)
}
REACTOR_VESSEL = {
    "obj_id": "rpv", "obj_type": "cylinder_closed_bottom",
    "height": 5.5, "outer_radius": 2.4, "wall_thickness": 0.04,
    "bottom_thickness": 1.2, "center_coords_pol": (0, 0, 0)
}
HX_RADIUS = 1.7
REACTOR_HX = [
    {
        "obj_id": f"hx{i+1}", "obj_type": "cylinder",
        "height": 2, "radius": 0.25,
        "center_coords_pol": (HX_RADIUS, i * math.pi / 2, 3.5)
    }
    for i in range(4)
]


# ── Run ───────────────────────────────────────────────────────────────────────

# 2D extrusions
# show(rect, circle, ellipse, trapezoid, slot, regular_polygon, polygon)

# Symmetric / non-default plane
# show(ellipse_sym, circle_xz)

# 3D primitives
# set_components([BOX_1, CYLINDER_1, SPHERE_1, CYLINDER_2, WEDGE_1, CYLINDER_CLOSED_BOTTOM_1])
# set_components([OVERLAPPING_A, OVERLAPPING_B])
# set_components([REACTOR_CORE, REACTOR_VESSEL] + REACTOR_HX)



