from build_3D_solid import build_solid
from utils import insert_into
from ocp_vscode import show
import cadquery as cq
import time
import math




# 1. Hollow extruded circle (pipe cross-section)
solid1, _ = build_solid("extrude", {"obj_type": "circle", "radius": 5}, height=20, wall_thickness=1.0)

# 2. Hollow extruded rectangle (box with open top/bottom)
solid2, _ = build_solid("extrude", {"obj_type": "rectangle", "width": 10, "height": 6}, height=15, wall_thickness=1.2)

# 3. Hollow torus (revolve a circle around Z)
solid3, _ = build_solid("revolve", {"obj_type": "circle", "radius": 2}, plane="XZ", axis="Z", axis_point=(8, 0, 0), angle=60, wall_thickness=0.5)

# 4. Hollow swept pipe along an L-path
PATH_L = cq.Wire.assembleEdges([
    cq.Edge.makeLine(cq.Vector(0, 0, 0),  cq.Vector(0, 0, 20)),
    cq.Edge.makeLine(cq.Vector(0, 0, 20), cq.Vector(20, 0, 20)),
])
solid4, _ = build_solid("sweep", {"obj_type": "circle", "radius": 3}, path=PATH_L, wall_thickness=0.2)
#show(solid4)
#print("Showing: hollow swept pipe along L-path")
#time.sleep(3)
#print("Continuing with more examples of hollow solids built with extrude, revolve, and sweep...")

# 5. Hollow extruded freeform T-profile
T_PTS = [(-5,0),(5,0),(5,1),(1,1),(1,6),(-1,6),(-1,1),(-5,1)]
solid5, _ = build_solid("extrude", T_PTS, height=40, wall_thickness=0.3)


# 1. Helix path (e.g. spring / coil)
PATH_HELIX = cq.Wire.makeHelix(pitch=10, height=40, radius=8)
solid6, _ = build_solid("sweep", {"obj_type": "circle", "radius": 1.5}, path=PATH_HELIX, wall_thickness=0.4)
#show(solid6)
#time.sleep(3)

# 2. Spline path (smooth curve through arbitrary points)
PATH_SPLINE = cq.Wire.assembleEdges([
    cq.Edge.makeSpline([
        cq.Vector(0, 0, 0),
        cq.Vector(5, 5, 10),
        cq.Vector(10, 0, 20),
        cq.Vector(15, -5, 30),
    ])
])
solid7, _ = build_solid("sweep", {"obj_type": "rectangle", "width": 4, "height": 2}, path=PATH_SPLINE, isFrenet=False, wall_thickness=0.5)
#show(solid7)
#time.sleep(3)

# Another example of L-path but with Frenet frame (twisting along the path)
PATH_L_a = cq.Wire.assembleEdges([
    cq.Edge.makeLine(cq.Vector(0, 0, 0),  cq.Vector(0, 0, 20)),
    cq.Edge.makeLine(cq.Vector(0, 0, 20), cq.Vector(20, 0, 20)),
])

solid_a, _ = build_solid(
    "sweep",
    {"obj_type": "rectangle", "width": 4, "height": 2},
    path=PATH_L,
    isFrenet=False,
    wall_thickness=0.5,
)
#show(solid_a)
#time.sleep(3)

PATH_L_b = cq.Wire.assembleEdges([
    cq.Edge.makeLine(cq.Vector(0, 0, 0), cq.Vector(0, 0, 10)),  # goes up
    cq.Edge.makeLine(cq.Vector(0, 0, 10), cq.Vector(10, 0, 10)), # turns right
])

solid_b, _ = build_solid(
    "sweep",
    {"obj_type": "circle", "radius": 3},  # large radius relative to the bend
    path=PATH_L,
    isFrenet=False,
)
#show(solid_b)
#time.sleep(3)

PATH_L_c = cq.Wire.assembleEdges([
    cq.Edge.makeLine(cq.Vector(0, 0, 0),  cq.Vector(0, 0, 10)),
    cq.Edge.makeLine(cq.Vector(0, 0, 10), cq.Vector(10, 0, 10)),
])

solid_rect, _ = build_solid(
    "sweep",
    {"obj_type": "rectangle", "width": 6, "height": 4},
    path=PATH_L_c,
    isFrenet=False,
)
#show(solid_rect)
#time.sleep(3)

def make_polyline(points: list) -> cq.Wire:
    return cq.Wire.assembleEdges([
        cq.Edge.makeLine(points[i], points[i + 1])
        for i in range(len(points) - 1)
    ])

PATH_test_c = make_polyline([
    cq.Vector(2, 0, 0),
    cq.Vector(2, 0, 4),
    cq.Vector(2.2, 0, 4.2),
    cq.Vector(2.5, 0, 4.5),
    cq.Vector(2.75, 0, 4.75),
    cq.Vector(3, 0, 5),
    cq.Vector(5, 0, 5),
])

solid_C, _ = build_solid(
    "sweep",
    {"obj_type": "circle", "radius": 0.1},
    path=PATH_test_c,
    isFrenet=False,
    wall_thickness=0.02,
)
#show(solid_C)
#time.sleep(3)

solid_d, _ = build_solid(
    "sweep",
    {"obj_type": "circle", "radius": 0.1},
    path=(
        (0, 0, 0),
        (0, 0, 4),
        (0.2, 0, 4.2),
        (0.5, 0, 4.5),
        (0.75, 0, 4.75),
        (1, 0, 5),
        (3, 0, 5),
    ),
    isFrenet=False,
    wall_thickness=0.02,
)
#show(solid_d)
#time.sleep(3)







# Another example to see how to make a tube with a smooth shape when at the perpendicular part
# PATH_testx = cq.Wire.makePolygon(([
#         cq.Vector(2, 0, 0),
#         cq.Vector(2, 0, 4),
#         cq.Vector(2.2, 0, 4.2),
#         cq.Vector(2.5, 0, 4.5),
#         cq.Vector(2.75, 0, 4.75),
#         cq.Vector(3, 0, 5),
#         cq.Vector(5, 0, 5),
#     ])
# )
pts = [
    cq.Vector(2, 0, 0),
    cq.Vector(2, 0, 4),
    cq.Vector(2.2, 0, 4.2),
    cq.Vector(2.5, 0, 4.5),
    cq.Vector(2.75, 0, 4.75),
    cq.Vector(3, 0, 5),
    cq.Vector(5, 0, 5),
]

PATH_testx = cq.Wire.assembleEdges([
    cq.Edge.makeLine(pts[i], pts[i+1])
    for i in range(len(pts) - 1)
])
solidx, _ = build_solid("sweep", {"obj_type": "circle", "radius": 0.1}, path=PATH_testx, isFrenet=False, wall_thickness=0.02)
#show(solidx)


r = 5  # bend radius — must be > pipe radius

PATH_90 = cq.Wire.assembleEdges([
    cq.Edge.makeLine(
        cq.Vector(0, 0, 0),
        cq.Vector(0, 0, 10)          # straight segment going up
    ),
    cq.Edge.makeThreePointArc(
        cq.Vector(0, 0, 10),         # end of first segment
        cq.Vector(r * 0.293, 0, 10 + r * 0.707),  # midpoint of arc
        cq.Vector(r, 0, 10 + r)      # start of second segment
    ),
    cq.Edge.makeLine(
        cq.Vector(r, 0, 10 + r),
        cq.Vector(10 + r, 0, 10 + r) # straight segment going right
    ),
])

solid_90, _ = build_solid(
    "sweep",
    {"obj_type": "circle", "radius": 1},
    path=PATH_90,
    isFrenet=False,
    wall_thickness=0.2,
)
show(solid_90)




# 3. Arc path (quarter circle bend)
PATH_ARC = cq.Wire.assembleEdges([
    cq.Edge.makeThreePointArc(
        cq.Vector(0, 0, 0),
        cq.Vector(10, 0, 10),
        cq.Vector(20, 0, 0),
    )
])
solid8, _ = build_solid("sweep", {"obj_type": "ellipse", "r1": 3, "r2": 1.5}, path=PATH_ARC, wall_thickness=0.5)
#show(solid8)

# 4. Analytical callable — sinusoidal wave path
def wave_path(t):
    return (t * 30, 5 * math.sin(t * 2 * math.pi), 0)  # must start at (0,0,0) when t=0

solid9, _ = build_solid("sweep", {"obj_type": "circle", "radius": 1}, path=wave_path, wall_thickness=0.3)

# 5. S-curve: two arcs joined
PATH_S = cq.Wire.assembleEdges([
    cq.Edge.makeThreePointArc(cq.Vector(0, 0, 0),  cq.Vector(5,  5, 10), cq.Vector(10, 0, 20)),
    cq.Edge.makeThreePointArc(cq.Vector(10, 0, 20), cq.Vector(15, -5, 30), cq.Vector(20, 0, 40)),
])
solid10, _ = build_solid("sweep", {"obj_type": "regular_polygon", "radius": 2, "nmb_of_sides": 6}, path=PATH_S, wall_thickness=0.4)



#show(solid7)





# -----------------------------------------------------------------------------------------------
# These (complex) example demonstrates boolean operations between various 3D primitives.
# It also shows how to use the `insert_into` utility function to position one object inside another.
# -----------------------------------------------------------------------------------------------


PIPE_1_DEF   = {"obj_type": "pipe", "height": 20, "outer_radius": 3, "inner_radius": 2}
PIPE_6_DEF   = {"obj_type": "pipe", "height": 20, "outer_radius": 1, "inner_radius": 0.7}
PIPE_7_DEF   = {"obj_type": "pipe", "height": 20, "outer_radius": 1, "inner_radius": 0.7}
PIPE_9_DEF   = {"obj_type": "pipe", "height": 20, "outer_radius": 0.8, "inner_radius": 0.6}
PIPE_10_DEF  = {"obj_type": "pipe", "height": 30, "outer_radius": 2, "inner_radius": 1.5}
VESSEL_9_DEF = {"obj_type": "cylinder_closed_bottom", "height": 10, "outer_radius": 5, "wall_thickness": 0.5, "bottom_thickness": 1.0}

CYL_2_DEF   = {"obj_type": "cylinder", "height": 20, "radius": 2}
SPH_3_DEF   = {"obj_type": "sphere", "radius": 9}
INNER_4_DEF = {"obj_type": "box", "length": 4, "width": 4, "height": 4}
CYL_5_DEF   = {"obj_type": "cylinder", "height": 8, "radius": 1}
SPH_8_DEF   = {"obj_type": "sphere", "radius": 2}
SPH_10_DEF  = {"obj_type": "sphere", "radius": 5}
CYL_10_DEF  = {"obj_type": "cylinder", "height": 30, "radius": 1}

# ── 1. Pipe through a box wall ──────────────────────────────────────────────
pipe1, _ = build_solid("primitive", PIPE_1_DEF)
wall1, _ = build_solid("primitive", {"obj_type": "box", "length": 10, "width": 10, "height": 2})
print(f"Combining: box  <--  {PIPE_1_DEF['obj_type']}")
show(insert_into(wall1, pipe1))
time.sleep(3)

# ── 2. Cylinder through a box ───────────────────────────────────────────────
cyl2, _  = build_solid("primitive", CYL_2_DEF)
wall2, _ = build_solid("primitive", {"obj_type": "box", "length": 10, "width": 10, "height": 2})
print(f"Combining: box  <--  {CYL_2_DEF['obj_type']}")
show(insert_into(wall2, cyl2))
time.sleep(3)

# ── 3. Sphere embedded in a box ─────────────────────────────────────────────
sph3, _  = build_solid("primitive", SPH_3_DEF)
wall3, _ = build_solid("primitive", {"obj_type": "box", "length": 12, "width": 12, "height": 12})
print(f"Combining: box  <--  {SPH_3_DEF['obj_type']}")
show(insert_into(wall3, sph3))
time.sleep(3)

# ── 4. Box cut into a larger box ────────────────────────────────────────────
inner4, _ = build_solid("primitive", INNER_4_DEF)
outer4, _ = build_solid("primitive", {"obj_type": "box", "length": 10, "width": 10, "height": 10})
print(f"Combining: box  <--  {INNER_4_DEF['obj_type']}")
show(insert_into(outer4, inner4))
time.sleep(3)

# ── 5. Cylinder embedded in a sphere ────────────────────────────────────────
cyl5, _ = build_solid("primitive", CYL_5_DEF)
sph5, _ = build_solid("primitive", {"obj_type": "sphere", "radius": 5})
print(f"Combining: sphere  <--  {CYL_5_DEF['obj_type']}")
show(insert_into(sph5, cyl5))
time.sleep(3)

# ── 6. Pipe through a cylinder ──────────────────────────────────────────────
pipe6, _ = build_solid("primitive", PIPE_6_DEF)
cyl6, _  = build_solid("primitive", {"obj_type": "cylinder", "height": 4, "radius": 6})
print(f"Combining: cylinder  <--  {PIPE_6_DEF['obj_type']}")
show(insert_into(cyl6, pipe6))
time.sleep(3)

# ── 7. Pipe through a wedge ─────────────────────────────────────────────────
pipe7, _  = build_solid("primitive", PIPE_7_DEF)
wedge7, _ = build_solid("primitive", {"obj_type": "wedge", "dx": 10, "dy": 8, "dz": 10,
                                       "xmin": 2, "zmin": 2, "xmax": 8, "zmax": 8})
print(f"Combining: wedge  <--  {PIPE_7_DEF['obj_type']}")
show(insert_into(wedge7, pipe7))
time.sleep(3)

# ── 8. Sphere into a cylinder ───────────────────────────────────────────────
sph8, _ = build_solid("primitive", SPH_8_DEF)
cyl8, _ = build_solid("primitive", {"obj_type": "cylinder", "height": 10, "radius": 5})
print(f"Combining: cylinder  <--  {SPH_8_DEF['obj_type']}")
show(insert_into(cyl8, sph8))
time.sleep(3)

# ── 9. Pipe through a cylinder_closed_bottom (rotated) ──────────────────────
vessel9, _ = build_solid("primitive", VESSEL_9_DEF)
pipe9, _   = build_solid("primitive", PIPE_9_DEF, rotation_angles=(0, 90, 0), center_coords=(0, 0, 3))
print(f"Combining: cylinder_closed_bottom  <--  {PIPE_9_DEF['obj_type']}")
show(insert_into(vessel9, pipe9))
time.sleep(3)

# ── 10. Box with sphere + pipe + cylinder all combined ───────────────────────
block10, _ = build_solid("primitive", {"obj_type": "box", "length": 20, "width": 20, "height": 20})
sph10, _   = build_solid("primitive", SPH_10_DEF)
pipe10, _  = build_solid("primitive", PIPE_10_DEF)
cyl10, _   = build_solid("primitive", CYL_10_DEF, center_coords=(5, 5, 0))
print(f"Combining: box  <--  {PIPE_10_DEF['obj_type']}")
result10 = insert_into(block10, pipe10)
print(f"Combining: result  <--  {SPH_10_DEF['obj_type']}")
result10 = insert_into(result10, sph10)
print(f"Combining: result  <--  {CYL_10_DEF['obj_type']}")
result10 = insert_into(result10, cyl10)
show(result10)
time.sleep(3)