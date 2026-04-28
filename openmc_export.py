import openmc


def material_from_spec(spec: dict) -> openmc.Material:
    """Build an openmc.Material from a component spec dict."""
    mat = openmc.Material(name=spec["material_tag"])
    for element, fraction in spec["elements"].items():
        mat.add_element(element, fraction)
    mat.set_density("g/cm3", spec["density"])
    return mat


def build_materials(spec_dicts: list[dict]) -> openmc.Materials:
    mats = openmc.Materials()
    for spec in spec_dicts:
        mats.append(material_from_spec(spec))
    return mats


def build_geometry(h5m_path: str, bounding_radius: float, bounding_height: float) -> openmc.Geometry:
    dagmc_universe = openmc.DAGMCUniverse(filename=h5m_path)

    outer_cyl = openmc.ZCylinder(r=bounding_radius, boundary_type="vacuum")
    top = openmc.ZPlane(z0=bounding_height / 2, boundary_type="vacuum")
    bot = openmc.ZPlane(z0=-bounding_height / 2, boundary_type="vacuum")
    bounding_cell = openmc.Cell(region=-outer_cyl & -top & +bot, fill=dagmc_universe)

    return openmc.Geometry([bounding_cell])


def build_settings(particles: int = 1000, batches: int = 50, inactive: int = 10) -> openmc.Settings:
    settings = openmc.Settings()
    settings.particles = particles
    settings.batches = batches
    settings.inactive = inactive
    settings.source = openmc.IndependentSource(
        space=openmc.stats.Point((0, 0, 0))
    )
    return settings


def build_tallies(r_grid: list, z_grid: list) -> openmc.Tallies:
    mesh = openmc.CylindricalMesh(r_grid=r_grid, z_grid=z_grid)
    mesh_filter = openmc.MeshFilter(mesh)
    tally = openmc.Tally(name="flux")
    tally.filters = [mesh_filter]
    tally.scores = ["flux"]
    return openmc.Tallies([tally])


def write_xmls(
    h5m_path: str,
    spec_dicts: list[dict],
    bounding_radius: float,
    bounding_height: float,
    output_dir: str = ".",
    r_grid: list = None,        #type: ignore
    z_grid: list = None,        #type: ignore
):
    import os
    os.makedirs(output_dir, exist_ok=True)

    r_grid = r_grid or [0, bounding_radius]
    z_grid = z_grid or [-bounding_height / 2, bounding_height / 2]

    mats = build_materials(spec_dicts)
    geom = build_geometry(h5m_path, bounding_radius, bounding_height)
    sett = build_settings()
    tallies = build_tallies(r_grid, z_grid)

    mats.export_to_xml(f"{output_dir}/materials.xml")
    geom.export_to_xml(f"{output_dir}/geometry.xml")
    sett.export_to_xml(f"{output_dir}/settings.xml")
    tallies.export_to_xml(f"{output_dir}/tallies.xml")

    print(f"XMLs written to {output_dir}/")