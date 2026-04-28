import os
import cadquery as cq
from ocp_vscode import show
from reactor_vessel import create_reactor_vessel
from ihx import create_ihx
from utils import export_step, fuse_to_single_solid

OUTPUT_DIR = "output/esfr_smart"
os.makedirs(OUTPUT_DIR, exist_ok=True)

rpv_geometry = dict(
    inner_d             = 4.72,
    wall_t              = 0.04,
    straight_h          = 5.5,
    bottom_head_type    = "ellipsoidal",
    bottom_head_params  = {"head_depth": 1.0},
    top_plate_thickness = 0.1,
)

ESFR_FUNNEL_PROFILE = [
    (0.400, 3.000), (0.400, 4.413), (0.660, 6.075), (0.660, 8.500),
    (0.650, 8.500), (0.650, 6.075), (0.390, 4.413), (0.390, 3.000),
]

ihx_geometry = dict(
    shell_outer_radius=0.663, shell_height=9.963, shell_wall_t=0.020,
    shell_bottom_t=0.020, neck_outer_radius=0.218, neck_wall_t=0.020,
    neck_height=1.831, inner_cyl_outer_radius=0.200, inner_cyl_wall_t=0.010,
    inner_cyl_height=8.500, inner_cyl_z_bottom=3.000,
    funnel_profile=ESFR_FUNNEL_PROFILE, funnel_wall_t=0.010,
    bundle_outer_od=0.800, bundle_outer_wall_t=0.010, bundle_inner_od=0.200,
    bundle_inner_wall_t=0.010, bundle_height=5.000, bundle_z_bottom=0.000,
    primary_pipe_od=0.436, primary_pipe_wall_t=0.020, primary_R_bend=1.050,
    primary_L_vert=3.000, primary_L_horiz=3.000, side_nozzle_od=0.760,
    side_nozzle_wall_t=0.030, side_nozzle_length=0.800, side_nozzle_z=6.075,
)

# --- Build ---
vessel, top_plate = create_reactor_vessel(**rpv_geometry)
ihx_parts = create_ihx(**ihx_geometry)

# --- Visualize ---
assembly = cq.Assembly()
assembly.add(vessel, name="rpv")
if top_plate:
    assembly.add(top_plate, name="top_plate")
for name, solid in ihx_parts.items():
    assembly.add(solid, name=f"ihx_{name}")
show(assembly)

# --- Fuse and export STEP ---
vessel = fuse_to_single_solid(vessel)
export_step(vessel, f"{OUTPUT_DIR}/reactor_vessel.step")

if top_plate:
    top_plate = fuse_to_single_solid(top_plate)
    export_step(top_plate, f"{OUTPUT_DIR}/top_plate.step")

for name, solid in ihx_parts.items():
    solid = fuse_to_single_solid(solid)
    export_step(solid, f"{OUTPUT_DIR}/ihx_{name}.step")

print("STEP files written to", OUTPUT_DIR)