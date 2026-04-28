import os
import glob
from dagmc_convert import convert_to_dagmc
from openmc_export import write_xmls

STEP_DIR   = "output/esfr_smart"
OUTPUT_DIR = "output/esfr_smart"

# --- Collect STEP files ---
rpv_step      = f"{STEP_DIR}/reactor_vessel.step"
top_plate_step = f"{STEP_DIR}/top_plate.step"
ihx_steps     = sorted(glob.glob(f"{STEP_DIR}/ihx_*.step"))

all_steps = [rpv_step, top_plate_step] + ihx_steps
all_tags  = ["steel316", "steel316"] + ["steel316_ihx"] * len(ihx_steps)

print(f"Total STEP files: {len(all_steps)}, Total tags: {len(all_tags)}")

# --- Convert to DAGMC ---
h5m_path = f"{OUTPUT_DIR}/reactor.h5m"
convert_to_dagmc(step_files=all_steps, tags=all_tags, output_path=h5m_path)

# --- Write OpenMC XMLs ---
rpv_material = dict(material_tag="steel316",     elements={"Fe": 0.65, "Cr": 0.17, "Ni": 0.12, "Mo": 0.025}, density=7.99)
ihx_material = dict(material_tag="steel316_ihx", elements={"Fe": 0.65, "Cr": 0.17, "Ni": 0.12, "Mo": 0.025}, density=7.99)

write_xmls(
    h5m_path        = h5m_path,
    spec_dicts      = [rpv_material, ihx_material],
    bounding_radius = 2.40 + 10,
    bounding_height = 5.5  + 10,
    output_dir      = OUTPUT_DIR,
)

print("Done.")