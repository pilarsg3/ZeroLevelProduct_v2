# import cad_to_dagmc

# def convert_to_dagmc(step_files: list[str], tags: list[str], output_path: str):
#     geometry = cad_to_dagmc.CadToDagmc()
#     for step_file, tag in zip(step_files, tags):
#         geometry.add_stp_file(filename=step_file, material_tags=[tag])
#     geometry.export_dagmc_h5m_file(filename=output_path, meshing_backend="gmsh")
#     print(f"DAGMC file written: {output_path}")



import cad_to_dagmc
import cadquery as cq

def convert_to_dagmc(step_files: list[str], tags: list[str], output_path: str):
    geometry = cad_to_dagmc.CadToDagmc()

    for step_file, tag in zip(step_files, tags):
        compound = cq.importers.importStep(step_file)
        solids = compound.Solids()          # type: ignore

        if len(solids) > 1:
            fused = solids[0]
            for s in solids[1:]:
                fused = fused.fuse(s)
            geometry.add_cadquery_object(cadquery_object=fused, material_tags=[tag])
        else:
            geometry.add_cadquery_object(cadquery_object=solids[0], material_tags=[tag])

        print(f"{step_file} -> {len(solids)} solids")

    geometry.export_dagmc_h5m_file(filename=output_path, meshing_backend="gmsh")
    print(f"DAGMC file written: {output_path}")






if __name__ == "__main__":
    convert_to_dagmc(
        step_files=["output/reactor_vessel.step", "output/ihx.step"],
        tags=["steel316", "steel316"],
        output_path="output/reactor.h5m"
    )