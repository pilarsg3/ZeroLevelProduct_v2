import cadquery as cq
from ocp_vscode import show
from assemble import assemble_objects

# inlet_pipe_secondary = {"operation": "sweep",
#                          "obj_id": "inlet_pipe_secondary",
#                          "profile": {"type": "circle", "radius": 0.436},


path = cq.Wire.assembleEdges([
    cq.Edge.makeLine(cq.Vector(0, 0, 0), cq.Vector(5, 0, 0)),
    cq.Edge.makeThreePointArc(cq.Vector(5, 0, 0), cq.Vector(7, 2, 0), cq.Vector(5, 4, 0)),
    cq.Edge.makeLine(cq.Vector(5, 4, 0), cq.Vector(0, 4, 0))
])

spec = {
    "operation": "sweep",
    "profile": {"obj_type": "circle", "radius": 0.5},
    "path": path,
}

assembly = assemble_objects([spec])
show(assembly)

