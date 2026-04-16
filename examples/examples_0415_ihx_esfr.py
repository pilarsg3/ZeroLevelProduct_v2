"""
example_ihx_esfr_smart.py
=========================
ESFR-SMART IHX — illustrates create_ihx() with explicit dimensions.

All dimensions from drawing 48e465b2 and hand-drawn flow diagram.
Units: metres.

Geometry layout (Z axis = IHX axis, z=0 = bottom of straight shell section)
-----------------------------------------------------------------------------
z = -hemi    hemispherical bottom
z = 0        bottom of straight shell section
z = 0        bottom of lower tube bundle
z = 5.0      top of lower tube bundle / bottom of funnel
z = 3.0      bottom of inner cylinder
z = 9.963    top of main shell / bottom of neck
z = 11.794   top of neck  (9.963 + 1.831)
z = 11.794   primary elbow connects here (top of neck)
"""

import cadquery as cq
from ocp_vscode import show
from ihx import create_ihx

# Inner funnel profile (r, z) — tapered from narrow at top to wide at bottom
# Based on drawing: upper inner_d≈400mm, widens to ≈800mm, then bundle section
ESFR_FUNNEL_PROFILE = [
    (0.400, 3.000),   # bottom outer
    (0.400, 4.413),   # straight outer
    (0.660, 6.075),   # taper outer
    (0.660, 8.500),   # top outer
    (0.650, 8.500),   # top inner (10mm wall)
    (0.650, 6.075),   # taper inner
    (0.390, 4.413),   # straight inner
    (0.390, 3.000),   # bottom inner
]

parts = create_ihx(
    # ── outer main shell ─────────────────────────────────
    shell_outer_radius     = 0.663,    # Ø1326 ≈ Ø1320
    shell_height           = 9.963,
    shell_wall_t           = 0.020,
    shell_bottom_t         = 0.020,

    # ── upper neck ───────────────────────────────────────
    neck_outer_radius      = 0.218,    # Ø436 / 2
    neck_wall_t            = 0.020,
    neck_height            = 1.831,    # from drawing: 1831mm above shell top

    # ── inner cylinder (through neck + upper shell) ──────
    inner_cyl_outer_radius = 0.200,    # Ø400 / 2
    inner_cyl_wall_t       = 0.010,
    inner_cyl_height       = 8.500,    # runs from z=3.0 to z=11.5
    inner_cyl_z_bottom     = 3.000,

    # ── funnel (tapered inner structure, green region) ───
    funnel_profile         = ESFR_FUNNEL_PROFILE,
    funnel_wall_t          = 0.010,

    # ── lower tube bundle (red, two concentric cylinders) ─
    bundle_outer_od        = 0.800,    # Ø800
    bundle_outer_wall_t    = 0.010,
    bundle_inner_od        = 0.200,    # central downcomer tube
    bundle_inner_wall_t    = 0.010,
    bundle_height          = 5.000,    # from drawing: 5000mm
    bundle_z_bottom        = 0.000,

    # ── primary sodium elbow pipe ────────────────────────
    primary_pipe_od        = 0.436,    # Ø436
    primary_pipe_wall_t    = 0.020,
    primary_R_bend         = 1.050,   # from drawing: R1050
    primary_L_vert         = 3.000,   # longer vertical leg
    primary_L_horiz        = 3.000,    # horizontal leg exiting to the right

    # ── side nozzle (primary outlet / secondary inlet) ───
    side_nozzle_od         = 0.760,    # Ø760
    side_nozzle_wall_t     = 0.030,
    side_nozzle_length     = 0.800,
    side_nozzle_z          = 6.075,    # mid-height of main shell
)

assembly = cq.Assembly()
for name, solid in parts.items():
    assembly.add(solid, name=name)

show(assembly)

