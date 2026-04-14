"""
Material metadata, Bill-of-Materials (BOM), and OpenMC export.

Design
------
Each object spec passed to ``assemble_objects()`` may carry a ``"material"``
key.  Two forms are accepted:

  1. String  — looked up in MATERIAL_LIBRARY (preferred for library materials)
  2. Dict    — inline spec for one-offs or parameter sweeps

String form (most common):
    ``"material": "SS316L"``

Dict form (override / custom):
    ``"material": {
        "name":                 "SS316L",       # required
        "density_gcc":          7.98,           # required  [g/cm³]
        "cost_usd_per_kg":      4.5,            # optional  (BOM)
        "thermal_conductivity": 15.0,           # optional  [W/m·K]
        "fraction_type":        "wo",           # "wo"=weight, "ao"=atom  (OpenMC)
        "elements": {"Fe": 0.65, "Cr": 0.17},  # OR "nuclides": {...}
    }``

Downstream uses
---------------
* ``compute_bom(assembly)``             → list[BOMEntry]             (cost accounting)
* ``export_openmc_materials(assembly)`` → dict[obj_id, openmc.Material]
* ``print_bom(entries)``                → formatted table to stdout
* ``bom_to_dict(entries)``              → JSON-serialisable list of dicts

Unit convention
---------------
CadQuery solids are dimensioned in **metres** in this codebase (inner_d=4.72 m,
wall_t=0.04 m, etc.), so ``val().Volume()`` returns m³.
OpenMC uses **g/cm³** for density.
Conversion:  mass_kg = volume_m3 x density_gcc x 1000
             (because 1 g/cm³ = 1000 kg/m³)
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Optional, cast
import cadquery as cq
from cadquery import Shape as CQShape


# ============================================================================
# MaterialSpec
# ============================================================================

@dataclass
class MaterialSpec:
    """All properties of a material, shared across cost and neutronics tools.

    Parameters
    ----------
    name : str
        Identifier used in library lookups and export labels.
    density_gcc : float
        Density in g/cm³ (OpenMC native unit; 1 g/cm³ = 1000 kg/m³).
    cost_usd_per_kg : float, optional
        Unit material cost [USD/kg].  Required for BOM; ignored by OpenMC export.
    thermal_conductivity : float, optional
        Thermal conductivity [W/m·K].  Informational; useful for
        thermal-hydraulics coupling later.
    fraction_type : str, optional
        ``"wo"`` (weight fractions) or ``"ao"`` (atom fractions).
        Required when ``elements`` or ``nuclides`` is provided.
        Structural materials are almost always ``"wo"``;
        fuel is typically ``"wo"`` or ``"ao"`` depending on enrichment spec.
    elements : dict[str, float], optional
        Elemental composition, e.g. ``{"Fe": 0.65, "Cr": 0.17}``.
        Fractions must sum to ~1.0.  Use for structural / coolant materials.
    nuclides : dict[str, float], optional
        Isotopic composition, e.g. ``{"U235": 0.045, "U238": 0.955, ...}``.
        Use for fuel where isotopic detail matters for neutronics.
    grade : str, optional
        More specific designation (e.g. ``"ASTM A240 Type 316L"``).
    notes : str, optional
        Free-text remarks (data source, assumptions, caveats).
    porosity : float, optional
        Volume fraction of voids, in [0, 1).  Default 0.0 (fully dense).
        effective_density_gcc = density_gcc * (1 - porosity).
    """
    name:                 str
    density_gcc:          float
    cost_usd_per_kg:      Optional[float]             = None
    thermal_conductivity: Optional[float]             = None
    fraction_type:        Optional[str]               = None   # "wo" | "ao"
    elements:             Optional[dict[str, float]]  = None
    nuclides:             Optional[dict[str, float]]  = None
    grade:                Optional[str]               = None
    notes:                Optional[str]               = None
    porosity:             float                        = 0.0

    def __post_init__(self) -> None:
        if self.density_gcc <= 0:
            raise ValueError(f"density_gcc must be > 0, got {self.density_gcc}")
        if self.cost_usd_per_kg is not None and self.cost_usd_per_kg < 0:
            raise ValueError(f"cost_usd_per_kg must be >= 0, got {self.cost_usd_per_kg}")
        if self.fraction_type is not None and self.fraction_type not in ("wo", "ao"):
            raise ValueError(f"fraction_type must be 'wo' or 'ao', got {self.fraction_type!r}")
        if self.elements is not None and self.nuclides is not None:
            raise ValueError("Provide either 'elements' or 'nuclides', not both.")
        if not 0.0 <= self.porosity < 1.0:
            raise ValueError(f"porosity must be in [0, 1), got {self.porosity}")

    @property
    def effective_density_gcc(self) -> float:
        """Density accounting for porosity [g/cm³].
        
        This is what is used for all mass and neutronics calculations.
        density_gcc is the fully dense reference value (from datasheet);
        effective_density_gcc = density_gcc * (1 - porosity).
        """
        return self.density_gcc * (1.0 - self.porosity)

    @property
    def density_kg_m3(self) -> float:
        """Effective density in kg/m³, accounting for porosity."""
        return self.effective_density_gcc * 1000.0


# ============================================================================
# MATERIAL_LIBRARY
# ============================================================================
#
# Elemental compositions are weight fractions (fraction_type="wo") unless noted.
# Fractions are normalised to sum to 1.0.
#
# Cost figures are indicative 2024 rough market prices for plate/bar stock.
# Compositions from: ASM Handbook, ASTM standards, IAEA-TECDOC, Special Metals.
#
MATERIAL_LIBRARY: dict[str, MaterialSpec] = {

    # ── Stainless steels ─────────────────────────────────────────────────────
    "SS316L": MaterialSpec(
        name="SS316L", density_gcc=7.98,
        cost_usd_per_kg=4.5, thermal_conductivity=15.0,
        fraction_type="wo",
        elements={"Fe": 0.6482, "Cr": 0.1700, "Ni": 0.1200,
                  "Mo": 0.0250, "Mn": 0.0200, "Si": 0.0100,
                  "C":  0.0003, "N":  0.0010, "P":  0.0005},
        grade="ASTM A240 Type 316L",
        notes="Low-carbon austenitic; common for RPV internals and piping",
    ),
    "SS304": MaterialSpec(
        name="SS304", density_gcc=8.00,
        cost_usd_per_kg=3.2, thermal_conductivity=16.2,
        fraction_type="wo",
        elements={"Fe": 0.6992, "Cr": 0.1900, "Ni": 0.0900,
                  "Mn": 0.0200, "Si": 0.0100, "C":  0.0008},
        grade="ASTM A240 Type 304",
    ),
    "SS347": MaterialSpec(
        name="SS347", density_gcc=7.98,
        cost_usd_per_kg=5.0, thermal_conductivity=14.0,
        fraction_type="wo",
        elements={"Fe": 0.6340, "Cr": 0.1800, "Ni": 0.1100,
                  "Nb": 0.0080, "Mn": 0.0200, "Si": 0.0100,
                  "C":  0.0008, "P":  0.0002},
        grade="ASTM A240 Type 347",
        notes="Nb-stabilised austenitic; high-temperature nuclear applications",
    ),

    # ── Ferritic / low-alloy pressure vessel steels ──────────────────────────
    "carbon_steel": MaterialSpec(
        name="carbon_steel", density_gcc=7.85,
        cost_usd_per_kg=1.1, thermal_conductivity=50.0,
        fraction_type="wo",
        elements={"Fe": 0.9850, "Mn": 0.0090, "C":  0.0030,
                  "Si": 0.0020, "P":  0.0003, "S":  0.0003},
        grade="SA-516 Gr. 70",
    ),
    "P91": MaterialSpec(
        name="P91", density_gcc=7.75,
        cost_usd_per_kg=6.5, thermal_conductivity=28.0,
        fraction_type="wo",
        elements={"Fe": 0.8750, "Cr": 0.0900, "Mo": 0.0100,
                  "V":  0.0020, "Nb": 0.0008, "C":  0.0010,
                  "Mn": 0.0040, "Si": 0.0030, "N":  0.0005},
        grade="9Cr-1Mo-V, ASTM A335 P91",
        notes="High-temperature creep-resistant ferritic; fast-reactor steam lines",
    ),
    "P22": MaterialSpec(
        name="P22", density_gcc=7.83,
        cost_usd_per_kg=4.0, thermal_conductivity=36.0,
        fraction_type="wo",
        elements={"Fe": 0.9640, "Cr": 0.0220, "Mo": 0.0100,
                  "Mn": 0.0030, "Si": 0.0010},
        grade="2.25Cr-1Mo, ASTM A335 P22",
    ),

    # ── Nickel-base alloys ───────────────────────────────────────────────────
    "Inconel625": MaterialSpec(
        name="Inconel625", density_gcc=8.44,
        cost_usd_per_kg=45.0, thermal_conductivity=9.8,
        fraction_type="wo",
        elements={"Ni": 0.6100, "Cr": 0.2150, "Mo": 0.0900,
                  "Nb": 0.0365, "Fe": 0.0250, "Co": 0.0100,
                  "Al": 0.0020, "Ti": 0.0020},
        grade="UNS N06625",
        notes="IHX / heat-exchanger tubing in corrosive environments",
    ),
    "Inconel718": MaterialSpec(
        name="Inconel718", density_gcc=8.19,
        cost_usd_per_kg=50.0, thermal_conductivity=11.4,
        fraction_type="wo",
        elements={"Ni": 0.5300, "Cr": 0.1900, "Fe": 0.1700,
                  "Nb": 0.0520, "Mo": 0.0300, "Ti": 0.0090,
                  "Al": 0.0050, "Co": 0.0100},
        grade="UNS N07718",
        notes="Age-hardenable; control rod drives, fasteners",
    ),
    "Hastelloy_C276": MaterialSpec(
        name="Hastelloy_C276", density_gcc=8.89,
        cost_usd_per_kg=60.0, thermal_conductivity=10.2,
        fraction_type="wo",
        elements={"Ni": 0.5700, "Mo": 0.1600, "Cr": 0.1550,
                  "Fe": 0.0600, "W":  0.0400, "Co": 0.0250,
                  "Mn": 0.0100, "V":  0.0030},
        grade="UNS N10276",
    ),

    # ── Zirconium alloys ─────────────────────────────────────────────────────
    "zircaloy4": MaterialSpec(
        name="zircaloy4", density_gcc=6.56,
        cost_usd_per_kg=28.0, thermal_conductivity=12.6,
        fraction_type="wo",
        elements={"Zr": 0.9824, "Sn": 0.0145, "Fe": 0.0021, "Cr": 0.0010},
        grade="ASTM B353 Zry-4",
        notes="Fuel cladding in LWRs; low neutron absorption cross-section",
    ),
    "Zr702": MaterialSpec(
        name="Zr702", density_gcc=6.51,
        cost_usd_per_kg=25.0, thermal_conductivity=22.0,
        fraction_type="wo",
        elements={"Zr": 0.9950, "Hf": 0.0045, "Fe": 0.0003, "O": 0.0002},
        grade="ASTM B493 UNS R60702",
        notes="Unalloyed zirconium; structural components",
    ),

    # ── Fuel ─────────────────────────────────────────────────────────────────
    "UO2_45": MaterialSpec(
        name="UO2_45", density_gcc=10.40,
        cost_usd_per_kg=2200.0,
        fraction_type="wo",
        nuclides={"U235": 0.0397, "U238": 0.8270, "O16": 0.1333},
        notes=(
            "Sintered UO2 at ~95% TD, 4.5 wt% U235 enrichment (typical LWR). "
            "Cost is highly enrichment- and market-dependent; treat as indicative."
        ),
    ),
    "MOX": MaterialSpec(
        name="MOX", density_gcc=10.60,
        cost_usd_per_kg=3500.0,
        fraction_type="wo",
        nuclides={"Pu239": 0.0530, "Pu240": 0.0160, "Pu241": 0.0050,
                  "U238":  0.7930, "O16":   0.1330},
        notes="Mixed-oxide fuel; ~7% Pu content; cost highly variable",
    ),

    # ── Coolants / moderators ─────────────────────────────────────────────────
    "sodium_coolant": MaterialSpec(
        name="sodium_coolant", density_gcc=0.850,
        cost_usd_per_kg=3.5, thermal_conductivity=62.0,
        fraction_type="ao",
        elements={"Na": 1.0},
        notes="Liquid sodium at ~550°C; density approximate",
    ),
    "lead_bismuth": MaterialSpec(
        name="lead_bismuth", density_gcc=10.45,
        cost_usd_per_kg=8.0, thermal_conductivity=13.0,
        fraction_type="wo",
        elements={"Pb": 0.4450, "Bi": 0.5550},
        notes="LBE eutectic coolant at ~400°C; density approximate",
    ),
    "heavy_water": MaterialSpec(
        name="heavy_water", density_gcc=1.105,
        cost_usd_per_kg=300.0, thermal_conductivity=0.60,
        fraction_type="ao",
        nuclides={"H2": 0.6667, "O16": 0.3333},
        notes="D2O moderator/coolant; indicative bulk price",
    ),
    "light_water": MaterialSpec(
        name="light_water", density_gcc=1.000,
        cost_usd_per_kg=0.001, thermal_conductivity=0.60,
        fraction_type="ao",
        nuclides={"H1": 0.6667, "O16": 0.3333},
    ),
    "graphite": MaterialSpec(
        name="graphite", density_gcc=1.75,
        cost_usd_per_kg=12.0, thermal_conductivity=130.0,
        fraction_type="ao",
        elements={"C": 1.0},
        grade="Nuclear grade (IG-110 equivalent)",
    ),

    # ── Shielding ─────────────────────────────────────────────────────────────
    "concrete_heavy": MaterialSpec(
        name="concrete_heavy", density_gcc=3.50,
        cost_usd_per_kg=0.3,
        fraction_type="wo",
        elements={"O": 0.3110, "Si": 0.0170, "Ca": 0.2290,
                  "Fe": 0.3680, "Ba": 0.0750},
        notes="Heavyweight concrete with barite aggregate; radiation shielding",
    ),
    "lead": MaterialSpec(
        name="lead", density_gcc=11.34,
        cost_usd_per_kg=2.5, thermal_conductivity=35.0,
        fraction_type="ao",
        elements={"Pb": 1.0},
        notes="Gamma shielding",
    ),
}


# ============================================================================
# Internal helpers
# ============================================================================

def _resolve_material(raw: Any) -> MaterialSpec:
    """Convert a user-supplied material value to a MaterialSpec.

    Accepts: str (library key), dict (inline spec), MaterialSpec instance.
    """
    if isinstance(raw, MaterialSpec):
        return raw
    if isinstance(raw, str):
        if raw not in MATERIAL_LIBRARY:
            available = sorted(MATERIAL_LIBRARY)
            raise ValueError(
                f"Unknown material {raw!r}.\n"
                f"Available library keys: {available}\n"
                f"Or pass a dict: name, density_gcc, "
                f"[cost_usd_per_kg, fraction_type, elements/nuclides, ...]"
            )
        return MATERIAL_LIBRARY[raw]
    if isinstance(raw, dict):
        return MaterialSpec(**raw)
    raise TypeError(
        f"'material' must be a str (library key), dict, or MaterialSpec "
        f"— got {type(raw)!r}"
    )


def _volume_m3(shape: Any) -> float:
    """Extract volume in m³ from a cq.Workplane or cq.Shape.
    
    Accepts both types so that volume extraction works whether the object
    came through assemble_objects() or was built and added manually.
    """
    if isinstance(shape, cq.Workplane):
        solid = cast(CQShape, shape.val())
        return float(solid.Volume())
    if hasattr(shape, "Volume"):
        solid = cast(CQShape, shape)
        return float(solid.Volume())
    raise TypeError(f"Cannot extract volume from {type(shape)!r}")


# ============================================================================
# BOMEntry
# ============================================================================

@dataclass
class BOMEntry:
    """One component's contribution to the bill of materials."""
    obj_id:                str
    material_name:         str
    grade:                 Optional[str]
    density_gcc:           float          # fully dense reference value
    porosity:              float          # 0.0 = fully dense
    effective_density_gcc: float          # density_gcc * (1 - porosity)
    volume_m3:             float
    mass_kg:               float          # computed from effective_density_gcc
    cost_usd_per_kg:       Optional[float]
    total_cost_usd:        Optional[float]   # None if cost_usd_per_kg not provided
    notes:                 Optional[str]


# ============================================================================
# BOM functions
# ============================================================================

def compute_bom(
    assembly: cq.Assembly,
) -> list[BOMEntry]:
    """
    Compute a Bill of Materials from the built assembly.

    Only specs with a ``"material"`` key are included; others are skipped.

    Volume is extracted from the CadQuery solid (m³, model in metres).
    Mass = volume_m3 x density_gcc x 1000  (1 g/cm³ = 1000 kg/m³).

    Parameters
    ----------
    assembly : cq.Assembly
        The assembled model returned by ``assemble_objects()``.
        Specs are read from ``assembly._specs``.

    Returns
    -------
    list[BOMEntry]
    """
    object_specs = assembly._specs  # type: ignore
    shape_map: dict[str, Any] = {c.name: c.obj for c in assembly.children}
    entries: list[BOMEntry] = []

    for spec in object_specs:
        obj_id  = spec.get("obj_id")        # type: ignore
        mat_raw = spec.get("material")      # type: ignore
        if obj_id is None or mat_raw is None:
            continue

        mat   = _resolve_material(mat_raw)
        shape = shape_map.get(obj_id)
        if shape is None:
            import warnings
            warnings.warn(
                f"compute_bom: obj_id={obj_id!r} not found in assembly — skipped.",
                stacklevel=2,
            )
            continue

        vol_m3  = _volume_m3(shape)
        mass_kg = vol_m3 * mat.effective_density_gcc * 1000.0
        total   = (mass_kg * mat.cost_usd_per_kg
                   if mat.cost_usd_per_kg is not None else None)

        entries.append(BOMEntry(
            obj_id                = obj_id,
            material_name         = mat.name,
            grade                 = mat.grade,
            density_gcc           = mat.density_gcc,
            porosity              = mat.porosity,
            effective_density_gcc = mat.effective_density_gcc,
            volume_m3             = vol_m3,
            mass_kg               = mass_kg,
            cost_usd_per_kg       = mat.cost_usd_per_kg,
            total_cost_usd        = total,
            notes                 = mat.notes,
        ))

    return entries


def bom_totals(entries: list[BOMEntry]) -> dict[str, float]:
    """Aggregate totals. Returns ``total_mass_kg`` and ``total_cost_usd``."""
    return {
        "total_mass_kg":  sum(e.mass_kg for e in entries),
        "total_cost_usd": sum(e.total_cost_usd for e in entries
                              if e.total_cost_usd is not None),
    }


def print_bom(entries: list[BOMEntry], currency: str = "USD") -> None:
    """Print a formatted BOM table to stdout."""
    if not entries:
        print("BOM is empty — no specs with a 'material' key found.")
        return

    col_w   = [18, 14, 10, 8, 10, 12, 16, 16]
    headers = ["Component", "Material", "rho (g/cc)", "Por.",
               "Vol (m3)", "Mass (kg)", f"Unit ({currency}/kg)", f"Total ({currency})"]

    def _row(cells: list) -> str:
        return "  ".join(str(c).ljust(w) for c, w in zip(cells, col_w))

    sep = "-" * (sum(col_w) + 2 * (len(col_w) - 1))
    print(sep)
    print(_row(headers))
    print(sep)
    for e in entries:
        print(_row([
            e.obj_id,
            e.material_name,
            f"{e.effective_density_gcc:.2f}",
            f"{e.porosity:.0%}" if e.porosity > 0 else "-",
            f"{e.volume_m3:.4f}",
            f"{e.mass_kg:.1f}",
            f"{e.cost_usd_per_kg:.2f}" if e.cost_usd_per_kg is not None else "-",
            f"{e.total_cost_usd:,.0f}" if e.total_cost_usd  is not None else "-",
        ]))
    print(sep)
    t = bom_totals(entries)
    print(_row(["TOTAL", "", "", "", "",
                f"{t['total_mass_kg']:.1f}", "",
                f"{t['total_cost_usd']:,.0f}"]))
    print(sep)


def bom_to_dict(entries: list[BOMEntry]) -> list[dict[str, Any]]:
    """Serialise BOM to a JSON-compatible list of dicts."""
    return [
        {
            "obj_id":                e.obj_id,
            "material":              e.material_name,
            "grade":                 e.grade,
            "density_gcc":           e.density_gcc,
            "porosity":              e.porosity,
            "effective_density_gcc": e.effective_density_gcc,
            "volume_m3":             e.volume_m3,
            "mass_kg":               e.mass_kg,
            "cost_usd_per_kg":       e.cost_usd_per_kg,
            "total_cost_usd":        e.total_cost_usd,
            "notes":                 e.notes,
        }
        for e in entries
    ]


# ============================================================================
# OpenMC export
# ============================================================================

def export_openmc_materials(assembly: cq.Assembly) -> dict[str, Any]:
    """
    Build an ``openmc.Material`` for each spec that has a ``"material"`` key
    with compositional data (``elements`` or ``nuclides``).

    Specs without composition data are skipped with a warning.
    Each component gets its own Material object (even if two share the same
    material name), so cell-level material assignment stays unambiguous.

    Parameters
    ----------
    assembly : cq.Assembly
        The assembled model returned by ``assemble_objects()``.
        Specs are read from ``assembly._specs``.

    Returns
    -------
    dict[str, openmc.Material]
        Keyed by ``obj_id``.

    Raises
    ------
    ImportError
        If ``openmc`` is not installed.

    Example
    -------
    >>> mats = export_openmc_materials(assembly)
    >>> openmc.Materials(list(mats.values())).export_to_xml()
    """
    try:
        import openmc  # type: ignore
    except ImportError:
        raise ImportError(
            "openmc is not installed.  Install it with:\\n"
            "  conda install -c conda-forge openmc\\n"
            "See https://docs.openmc.org/en/stable/usersguide/install.html"
        )

    object_specs = assembly._specs  # type: ignore
    result: dict[str, Any] = {}

    for spec in object_specs:
        obj_id  = spec.get("obj_id")        # type: ignore
        mat_raw = spec.get("material")      # type: ignore
        if obj_id is None or mat_raw is None:
            continue

        mat = _resolve_material(mat_raw)

        if mat.elements is None and mat.nuclides is None:
            import warnings
            warnings.warn(
                f"export_openmc_materials: {obj_id!r} ({mat.name}) has no "
                f"elements/nuclides — skipped.  Add composition to the MaterialSpec.",
                stacklevel=2,
            )
            continue

        if mat.fraction_type is None:
            raise ValueError(
                f"Material {mat.name!r} (obj_id={obj_id!r}) has no 'fraction_type'. "
                f"Set fraction_type='wo' (weight) or 'ao' (atom)."
            )

        omc_mat = openmc.Material(name=f"{obj_id}_{mat.name}")
        omc_mat.set_density("g/cm3", mat.effective_density_gcc)

        if mat.elements is not None:
            for symbol, fraction in mat.elements.items():
                omc_mat.add_element(symbol, fraction, percent_type=mat.fraction_type)
        else:
            for nuclide, fraction in (mat.nuclides or {}).items():
                omc_mat.add_nuclide(nuclide, fraction, percent_type=mat.fraction_type)

        result[obj_id] = omc_mat

    return result


def print_openmc_cards(assembly):
    """Print what the OpenMC material cards would look like, without needing openmc installed."""
    from materials import _resolve_material
    
    for spec in assembly._specs:
        obj_id  = spec.get("obj_id")
        mat_raw = spec.get("material")
        if obj_id is None or mat_raw is None:
            continue

        mat = _resolve_material(mat_raw)
        if mat.elements is None and mat.nuclides is None:
            continue

        composition = mat.nuclides or mat.elements
        fraction_type = mat.fraction_type or "wo"

        print(f"\n--- {obj_id} ---")
        print(f"  material name : {obj_id}_{mat.name}")
        print(f"  density       : {mat.effective_density_gcc:.4f} g/cm³")
        print(f"  fraction type : {'weight' if fraction_type == 'wo' else 'atom'}")
        print(f"  composition   :")
        for symbol, fraction in composition.items():        #type: ignore
            print(f"    {symbol:<12} {fraction:.4f}")