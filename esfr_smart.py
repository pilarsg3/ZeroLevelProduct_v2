import os
from reactor_vessel import create_reactor_vessel
from ihx import create_ihx
from utils import export_step
from dagmc_convert import convert_to_dagmc
from openmc_export import write_xmls

OUTPUT_DIR = "output/esfr_smart"
os.makedirs(OUTPUT_DIR, exist_ok=True)

# ---------------------------------------------------------------------------
# Geometry params
# ---------------------------------------------------------------------------

rpv_geometry = dict(
    inner_d             = 4.72,
    wall_t              = 0.04,
    straight_h          = 5.5,
    bottom_head_type    = "ellipsoidal",
    bottom_head_params  = {"head_depth": 1.0},
    top_plate_thickness = 0.1,
)

ESFR_FUNNEL_PROFILE = [
    (0.400, 3.000),
    (0.400, 4.413),
    (0.660, 6.075),
    (0.660, 8.500),
    (0.650, 8.500),
    (0.650, 6.075),
    (0.390, 4.413),
    (0.390, 3.000),
]

ihx_geometry = dict(
    shell_outer_radius      = 0.663,
    shell_height            = 9.963,
    shell_wall_t            = 0.020,
    shell_bottom_t          = 0.020,

    neck_outer_radius       = 0.218,
    neck_wall_t             = 0.020,
    neck_height             = 1.831,

    inner_cyl_outer_radius  = 0.200,
    inner_cyl_wall_t        = 0.010,
    inner_cyl_height        = 8.500,
    inner_cyl_z_bottom      = 3.000,

    funnel_profile          = ESFR_FUNNEL_PROFILE,
    funnel_wall_t           = 0.010,

    bundle_outer_od         = 0.800,
    bundle_outer_wall_t     = 0.010,
    bundle_inner_od         = 0.200,
    bundle_inner_wall_t     = 0.010,
    bundle_height           = 5.000,
    bundle_z_bottom         = 0.000,

    primary_pipe_od         = 0.436,
    primary_pipe_wall_t     = 0.020,
    primary_R_bend          = 1.050,
    primary_L_vert          = 3.000,
    primary_L_horiz         = 3.000,

    side_nozzle_od          = 0.760,
    side_nozzle_wall_t      = 0.030,
    side_nozzle_length      = 0.800,
    side_nozzle_z           = 6.075,
)

# ---------------------------------------------------------------------------
# Material params (OpenMC only)
# ---------------------------------------------------------------------------

rpv_material = dict(
    material_tag = "steel316",
    elements     = {"Fe": 0.65, "Cr": 0.17, "Ni": 0.12, "Mo": 0.025},
    density      = 7.99,
)

ihx_material = dict(
    material_tag = "steel316_ihx",
    elements     = {"Fe": 0.65, "Cr": 0.17, "Ni": 0.12, "Mo": 0.025},
    density      = 7.99,
)

# ---------------------------------------------------------------------------
# Build geometry
# ---------------------------------------------------------------------------

vessel, top_plate = create_reactor_vessel(**rpv_geometry) #type: ignore
ihx_parts = create_ihx(**ihx_geometry)                    #type: ignore

# ---------------------------------------------------------------------------
# Export to STEP
# ---------------------------------------------------------------------------

rpv_step = f"{OUTPUT_DIR}/reactor_vessel.step"
export_step(vessel, rpv_step)                             #type: ignore

if top_plate is not None:
    export_step(top_plate, f"{OUTPUT_DIR}/top_plate.step")  #type: ignore

ihx_steps = []
for part_name, solid in ihx_parts.items():
    path = f"{OUTPUT_DIR}/ihx_{part_name}.step"
    export_step(solid, path)                              #type: ignore   
    ihx_steps.append(path)

# ---------------------------------------------------------------------------
# Convert to DAGMC
# ---------------------------------------------------------------------------

h5m_path = f"{OUTPUT_DIR}/reactor.h5m"
all_steps = [rpv_step] + ihx_steps
all_tags  = ["steel316"] + ["steel316_ihx"] * len(ihx_steps)

convert_to_dagmc(
    step_files  = all_steps,
    tags        = all_tags,
    output_path = h5m_path,
)

# ---------------------------------------------------------------------------
# Write OpenMC XMLs
# ---------------------------------------------------------------------------

bounding_radius = rpv_geometry["inner_d"] / 2 + rpv_geometry["wall_t"] + 10     #type: ignore
bounding_height = rpv_geometry["straight_h"] + 10                               #type: ignore   

write_xmls(
    h5m_path        = h5m_path,
    spec_dicts      = [rpv_material, ihx_material],
    bounding_radius = bounding_radius,
    bounding_height = bounding_height,
    output_dir      = OUTPUT_DIR,
)

print("Done. Run: openmc --path", OUTPUT_DIR)