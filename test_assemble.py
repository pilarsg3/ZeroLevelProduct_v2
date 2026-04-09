"""
Test the assemble_objects workflow with mixed 3D object types.
"""

from assemble import assemble_objects
from ocp_vscode import show

# Define a list of objects with different operations
object_specs = [
    # Extrude a rectangle
    {
        "operation": "extrude",
        "obj_id": "rectangular_beam",
        "profile": {"obj_type": "rectangle", "width": 10, "height": 5},
        "height": 20,
    },
    
    # Extrude a circle
    {
        "operation": "extrude",
        "obj_id": "cylindrical_shaft",
        "profile": {"obj_type": "circle", "radius": 3},
        "height": 15,
        "center_coords": (20, 0, 0),
    },
    
    # Revolve an ellipse
    {
        "operation": "revolve",
        "obj_id": "revolve_vase",
        "profile": {"obj_type": "ellipse", "r1": 5, "r2": 3},
        "angle": 360,
        "plane": "XZ",
        "axis": "Z",
        "axis_point": (-10, 0, 0),
    },
    
    # Primitive cylinder
    {
        "operation": "primitive",
        "obj_id": "tank",
        "profile": {"obj_type": "cylinder", "radius": 5, "height": 10},
        "center_coords": (0, 15, 0),
    },
    
    # Primitive box
    {
        "operation": "primitive",
        "obj_id": "base_platform",
        "profile": {"obj_type": "box", "length": 30, "width": 30, "height": 2},
        "center_coords": (0, 0, -10),
    },
]

# Build and assemble all objects
print("Building objects...")
assembly = assemble_objects(object_specs)
print("✓ Assembly complete! Objects loaded:")
for spec in object_specs:
    print(f"  - {spec['obj_id']} ({spec['operation']})")

print("\nDisplaying assembly...")
show(assembly)
