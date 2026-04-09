import cadquery as cq
from ocp_vscode import show

from top_plate import create_top_plate

# ── 1. Plain disk ──────────────────────────────────────────────────────────────
plate_1 = create_top_plate(
    plate_outer_d   = 92.0,
    plate_thickness = 3.0,
)

# ── 2. Central bore ────────────────────────────────────────────────────────────
plate_2 = create_top_plate(
    plate_outer_d   = 92.0,
    plate_thickness = 3.0,
    hole_groups=[
        dict(hole_diameter=20.0, layout="explicit_positions", positions=[(0.0, 0.0)]),
    ],
)

# ── 3. 6 IHX nozzles, symmetric ───────────────────────────────────────────────
plate_3 = create_top_plate(
    plate_outer_d   = 92.0,
    plate_thickness = 3.0,
    hole_groups=[
        dict(hole_diameter=6.0, layout="symmetric", count=6, placement_radius=31.0),
    ],
)

# ── 4. Three groups: IHX nozzles + instrument tubes + central bore ─────────────
plate_4 = create_top_plate(
    plate_outer_d   = 92.0,
    plate_thickness = 3.0,
    hole_groups=[
        dict(hole_diameter=6.0,  layout="symmetric",  count=6, placement_radius=31.0),
        dict(hole_diameter=2.0,  layout="symmetric",  count=3, placement_radius=20.0, start_angle_deg=30.0),
        dict(hole_diameter=10.0, layout="explicit_positions", positions=[(0.0, 0.0)]),
    ],
)

# ── 5. Custom angles ───────────────────────────────────────────────────────────
plate_5 = create_top_plate(
    plate_outer_d   = 92.0,
    plate_thickness = 3.0,
    hole_groups=[
        dict(hole_diameter=6.0, layout="custom_angles", angles_deg=[10.0, 140.0, 250.0], placement_radius=31.0),
    ],
)

# ── 6. Explicit XY positions, different sizes per hole ────────────────────────
plate_6 = create_top_plate(
    plate_outer_d   = 92.0,
    plate_thickness = 3.0,
    hole_groups=[
        dict(hole_diameter=10.0, layout="explicit_positions", positions=[(30.0,  10.0)]),
        dict(hole_diameter=14.0, layout="explicit_positions", positions=[(-18.0, 22.0)]),
        dict(hole_diameter=6.0,  layout="explicit_positions", positions=[(14.0, -28.0)]),
    ],
)

# ── Uncomment whichever plate you want to inspect ─────────────────────────────
show(plate_1)
# show(plate_2)
# show(plate_3)
# show(plate_4)
# show(plate_5)
# show(plate_6)