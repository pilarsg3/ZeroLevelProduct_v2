"""
Examples illustrating the material property system.

Organised from simplest to most complex:
  Ex 1 — one component, string lookup
  Ex 2 — one component, inline dict
  Ex 3 — one component, MaterialSpec instance
  Ex 4 — one porous component
  Ex 5 — multiple components, mixed material forms
  Ex 6 — BOM: totals, JSON serialisation
  Ex 7 — full SMR primary loop with OpenMC export
  Ex 8 — browsing the material library
"""

from assemble import assemble_objects
from materials import (
    compute_bom,
    print_bom,
    bom_to_dict,
    bom_totals,
    export_openmc_materials,
    print_openmc_cards,
    MATERIAL_LIBRARY,
    MaterialSpec,
)
from ocp_vscode import show
import math
import json


# ============================================================================
# EXAMPLE 1 — One component, string lookup
# ============================================================================
# The simplest possible case. "material" is a string key into MATERIAL_LIBRARY.
# Everything else — density, composition, cost — is looked up automatically.

specs_ex1 = [
    {
        "operation": "primitive",
        "obj_id":    "vessel",
        "obj_type":  "cylinder",
        "height":    5.0,
        "radius":    2.5,
        "material":  "SS316L",      # ← just a string
    },
]

print("\n" + "="*60)
print("EXAMPLE 1 — One component, string lookup")
print("="*60)
assembly_ex1 = assemble_objects(specs_ex1)
bom_ex1      = compute_bom(assembly_ex1)
print_bom(bom_ex1)
show(assembly_ex1)


# ============================================================================
# EXAMPLE 2 — One component, inline dict
# ============================================================================
# Use a dict when the material is not in the library, or when you want to
# override specific values (e.g. density at a different operating temperature).

specs_ex2 = [
    {
        "operation": "primitive",
        "obj_id":    "coolant",
        "obj_type":  "cylinder",
        "height":    5.0,
        "radius":    2.0,
        "material": {                       # ← inline dict
            "name":            "sodium_hot",
            "density_gcc":     0.820,       # at 650°C; library value is 550°C
            "cost_usd_per_kg": 3.5,
            "fraction_type":   "ao",
            "elements":        {"Na": 1.0},
            "notes":           "Sodium at 650°C operating point",
        },
    },
]

print("\n" + "="*60)
print("EXAMPLE 2 — One component, inline dict")
print("="*60)
assembly_ex2 = assemble_objects(specs_ex2)
bom_ex2      = compute_bom(assembly_ex2)
print_bom(bom_ex2)
show(assembly_ex2)


# ============================================================================
# EXAMPLE 3 — One component, MaterialSpec instance
# ============================================================================
# Define a MaterialSpec object once and reuse it across many specs.
# Useful when the same custom material appears on multiple components.

my_cladding = MaterialSpec(
    name                 = "FeCrAl_cladding",
    density_gcc          = 7.25,
    cost_usd_per_kg      = 18.0,
    thermal_conductivity = 13.5,
    fraction_type        = "wo",
    elements             = {"Fe": 0.790, "Cr": 0.130, "Al": 0.050, "Y": 0.003},
    grade                = "APMT",
    notes                = "Accident-tolerant fuel cladding candidate",
)

specs_ex3 = [
    {
        "operation":  "primitive",
        "obj_id":     "clad_tube",
        "obj_type":   "pipe",
        "height":     3.66,
        "outer_radius": 0.0047,
        "inner_radius": 0.0041,
        "material":   my_cladding,          # ← MaterialSpec instance
    },
]

print("\n" + "="*60)
print("EXAMPLE 3 — One component, MaterialSpec instance")
print("="*60)
assembly_ex3 = assemble_objects(specs_ex3)
bom_ex3      = compute_bom(assembly_ex3)
print_bom(bom_ex3)
show(assembly_ex3)


# ============================================================================
# EXAMPLE 4 — Porous component
# ============================================================================
# Add a "porosity" field and the effective density is computed automatically.
# density_gcc is the fully-dense reference value (from the datasheet).
# effective_density_gcc = density_gcc * (1 - porosity) is what gets used
# for mass and OpenMC density card.

specs_ex4 = [
    {
        "operation": "primitive",
        "obj_id":    "fuel_pellet",
        "obj_type":  "cylinder",
        "height":    0.013,
        "radius":    0.004,
        "material": {
            "name":            "UO2_sintered",
            "density_gcc":     10.96,       # theoretical full density
            "porosity":        0.05,        # 5% porosity → effective = 10.41 g/cm³
            "cost_usd_per_kg": 2200.0,
            "fraction_type":   "wo",
            "nuclides":        {"U235": 0.0397, "U238": 0.8270, "O16": 0.1333},
            "notes":           "Sintered at 95% TD",
        },
    },
]

print("\n" + "="*60)
print("EXAMPLE 4 — Porous component")
print("="*60)
assembly_ex4 = assemble_objects(specs_ex4)
bom_ex4      = compute_bom(assembly_ex4)
print_bom(bom_ex4)   # porosity column shows "5%"; density shown is effective
show(assembly_ex4)


# ============================================================================
# EXAMPLE 5 — Multiple components, mixed material forms
# ============================================================================
# All three forms can coexist in the same spec list.
# Components without a "material" key are silently skipped in the BOM —
# useful for placeholder geometry you haven't assigned a material to yet.

specs_ex5 = [
    {
        "operation": "primitive",
        "obj_id":    "rpv_wall",
        "obj_type":  "pipe",
        "height":    5.5,
        "outer_radius": 2.40,
        "inner_radius": 2.36,
        "material":  "SS316L",              # form 1: string
    },
    {
        "operation":     "primitive",
        "obj_id":        "reflector",
        "obj_type":      "cylinder",
        "height":        5.5,
        "radius":        2.0,
        "center_coords": (0, 0, 0),
        "material":      "graphite",        # form 1: string
    },
    {
        "operation":     "primitive",
        "obj_id":        "shield_ring",
        "obj_type":      "pipe",
        "height":        5.5,
        "outer_radius":  3.0,
        "inner_radius":  2.4,
        "center_coords": (0, 0, 0),
        "material": {                       # form 2: inline dict
            "name":            "borated_steel",
            "density_gcc":     7.80,
            "cost_usd_per_kg": 3.8,
            "fraction_type":   "wo",
            "elements":        {"Fe": 0.985, "B": 0.010, "Mn": 0.005},
        },
    },
    {
        "operation":     "primitive",
        "obj_id":        "placeholder_pump",
        "obj_type":      "cylinder",
        "height":        1.0,
        "radius":        0.3,
        "center_coords": (3.0, 0, 2.0),
        # no "material" key → skipped in BOM silently
    },
]

print("\n" + "="*60)
print("EXAMPLE 5 — Multiple components, mixed forms")
print("="*60)
assembly_ex5 = assemble_objects(specs_ex5)
bom_ex5      = compute_bom(assembly_ex5)
print_bom(bom_ex5)   # placeholder_pump does not appear
show(assembly_ex5)


# ============================================================================
# EXAMPLE 6 — BOM totals and JSON serialisation
# ============================================================================
# bom_totals() aggregates mass and cost across all entries.
# bom_to_dict() produces a JSON-serialisable list, useful for saving results
# to a file or feeding into a cost model / spreadsheet.

print("\n" + "="*60)
print("EXAMPLE 6 — BOM totals and JSON serialisation")
print("="*60)
# reuse bom_ex5 from above
totals = bom_totals(bom_ex5)
print(f"Total mass : {totals['total_mass_kg']:,.1f} kg")
print(f"Total cost : ${totals['total_cost_usd']:,.0f}")

bom_json = bom_to_dict(bom_ex5)
print("\nBOM as JSON:")
print(json.dumps(bom_json, indent=2))

# save to file:
# with open("bom_output.json", "w") as f:
#     json.dump(bom_json, f, indent=2)


# ============================================================================
# EXAMPLE 7 — Full SMR primary loop + OpenMC export
# ============================================================================
# All components annotated with materials. After assembly, the same spec list
# feeds compute_bom() for cost and export_openmc_materials() for neutronics —
# no duplication of material data anywhere.

specs_ex7 = [
    {
        "operation":          "primitive",
        "obj_id":             "rpv",
        "obj_type":           "reactor_vessel",
        "inner_d":            4.72,
        "wall_t":             0.04,
        "straight_h":         5.5,
        "bottom_head_type":   "ellipsoidal",
        "bottom_head_params": {"head_depth": 1.0},
        "material":           "SS316L",
    },
    {
        "operation":     "primitive",
        "obj_id":        "core",
        "obj_type":      "cylinder",
        "height":        1.3,
        "radius":        1.0,
        "center_coords": (0, 0, 1.5),
        "material":      "UO2_45",
    },
    *[
        {
            "operation":         "primitive",
            "obj_id":            f"hx{i+1}",
            "obj_type":          "pipe",
            "height":            5.0,
            "outer_radius":      0.25,
            "inner_radius":      0.22,
            "center_coords_pol": (1.7, i * math.pi / 2, 4.5),
            "material":          "Inconel625",
        }
        for i in range(4)
    ],
]

print("\n" + "="*60)
print("EXAMPLE 7 — Full SMR primary loop")
print("="*60)
assembly_ex7 = assemble_objects(specs_ex7)

# cost accounting
bom_ex7 = compute_bom(assembly_ex7)
print_bom(bom_ex7)
totals_ex7 = bom_totals(bom_ex7)
print(f"\nTotal mass : {totals_ex7['total_mass_kg']:,.1f} kg")
print(f"Total cost : ${totals_ex7['total_cost_usd']:,.0f}")

# OpenMC material cards — uncomment when openmc is installed:
# omc_mats = export_openmc_materials(assembly_ex7)
# for obj_id, mat in omc_mats.items():
#     print(f"{obj_id}: {mat}")
# openmc.Materials(list(omc_mats.values())).export_to_xml()

show(assembly_ex7)
print_openmc_cards(assembly_ex7)

# OpenMC material cards — requires openmc installed
# omc_mats = export_openmc_materials(assembly_ex7)
# for obj_id, mat in omc_mats.items():
#     print(f"\n--- {obj_id} ---")
#     print(f"  name:    {mat.name}")
#     print(f"  density: {mat.density} g/cm³")
#     for nuclide, fraction in mat.nuclides:
#         print(f"  {nuclide:<12} {fraction:.4f}")




# ============================================================================
# EXAMPLE 8 — Browsing the material library
# ============================================================================
# Quick reference: print all materials with density and cost.

print("\n" + "="*60)
print("EXAMPLE 8 — Available materials in MATERIAL_LIBRARY")
print("="*60)
for name, mat in MATERIAL_LIBRARY.items():
    cost_str = f"${mat.cost_usd_per_kg}/kg" if mat.cost_usd_per_kg else "no cost data"
    print(f"  {name:<22}  rho={mat.density_gcc} g/cm³   {cost_str}")



