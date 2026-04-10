from assemble import assemble_objects
from build_3D_solid import build_solid
from assemble import assemble_objects
from ocp_vscode import show, show_object
import math
import cadquery as cq
from typing import cast

# ================================================================================================
# EXAMPLE: SMR primary loop - vessel, core, steam generators (polar coordinates)
# Dimensions in meters
# ================================================================================================

REACTOR_CORE = {
    "operation": "primitive",
    "obj_id": "core",
    "obj_type": "cylinder",
    "height": 1.3,
    "radius": 2 / 2,
    "center_coords": (0, 0, 1.5),
    "rotation_angles": (0, 0, 0)
}

REACTOR_VESSEL = {
    "operation": "primitive",
    "obj_id": "rpv",
    "obj_type": "cylinder_closed_bottom",
    "height": 5.5,
    "outer_radius": 4.8 / 2,
    "wall_thickness": 0.04,
    "bottom_thickness": 5.5 - 4.3,
    "center_coords_pol": (0, 0, 0)
}

REACTOR_HX = [
    {"operation": "primitive",
        "obj_id": f"hx{i + 1}",
        "obj_type": "cylinder",
        "height": 2,
        "radius": 0.25,
        "center_coords_pol": (1.7, i * math.pi / 2, 3.5)
    }
    for i in range(4)
]

TOP_COMPONENT = {
    "obj_id": "top",
    "operation": "revolve",
    "profile": [(0,0), (1,0), (1,1), (2,2), (2,3), (0,3)],
    "plane": "XZ",
    "angle": 360,
    "axis": "Z",
    "axis_point": (0, 0, 0),
    "center_coords": (0, 0, 5.5),
    "rotation_angles": (0, 0, 0)
}

#show(assemble_objects([TOP_COMPONENT]))
#show(assemble_objects([REACTOR_CORE, REACTOR_VESSEL, *REACTOR_HX, TOP_COMPONENT]))

# ================================================================================================
# SIMPLE EXAMPLE - Two intersecting boxes
# ================================================================================================

BOX1 = {
    "operation": "primitive",
    "obj_id": "box1",
    "obj_type": "box",
    "length": 5,
    "width": 5,
    "height": 5,
    "center_coords": (0, 0, 0)
}

CYLINDER = {
    "operation": "primitive",
    "obj_id": "cylinder",
    "obj_type": "cylinder",
    "radius": 1,
    "height": 10,
    "center_coords": (0, 0, 0)
}

# Build assembly with box and cylinder through it
print("Assembling box with cylinder through the middle...")
assembly = assemble_objects([BOX1, CYLINDER])
# Debug: Print assembly contents
print("\nAssembly contents:")
for i, child in enumerate(assembly.children):
    print(f"  [{i}] {child.name}: {type(child.obj).__name__}")
    if hasattr(child, 'children') and child.children:
        for j, subchild in enumerate(child.children):
            print(f"      [{j}] {subchild.name}: {type(subchild.obj).__name__}")
show(assembly)

# ================================================================================================
# APPLY BOOLEAN OPERATIONS
# ================================================================================================

from assemble import apply_boolean_operations
import time
# 1. UNION - Fuse box1 + cylinder into one solid
print("\n=== OPERATION 1: UNION ===")
assembly_union = assemble_objects([BOX1, CYLINDER])
assembly_union = apply_boolean_operations(assembly_union, [
    {"operation": "union", "obj1": "box1", "obj2": "cylinder"}
])
show(assembly_union)
time.sleep(1)

# 2. CUT - Remove cylinder from box1 (carve it out)
print("\n=== OPERATION 2: CUT ===")
assembly_cut = assemble_objects([BOX1, CYLINDER])
assembly_cut = apply_boolean_operations(assembly_cut, [
    {"operation": "cut", "obj1": "box1", "obj2": "cylinder"}
])
show(assembly_cut)
time.sleep(1)

# 3. INTERSECT - Keep only the overlapping volume
print("\n=== OPERATION 3: INTERSECT ===")
assembly_intersect = assemble_objects([BOX1, CYLINDER])
assembly_intersect = apply_boolean_operations(assembly_intersect, [
    {"operation": "intersect", "obj1": "box1", "obj2": "cylinder"}
])
show(assembly_intersect)
time.sleep(1)


# Show box + cylinder
#show(assemble_objects([BOX1, CYLINDER]))
#time.sleep(1)
# Later, show just box
#show(assemble_objects([BOX1]))
#time.sleep(1)
# Or just cylinder
#show(assemble_objects([CYLINDER]))


# 1. Box (the wall)
BOX = {
    "operation": "primitive",
    "obj_id": "wall",
    "obj_type": "box",
    "length": 10,
    "width": 10,
    "height": 2,
    "center_coords": (0, 0, 0)
}

# 2. Outer cylinder (pipe exterior)
PIPE_OUTER = {
    "operation": "primitive",
    "obj_id": "pipe_outer",
    "obj_type": "cylinder",
    "radius": 1.0,
    "height": 5,
    "center_coords": (0, 0, 0)
}

# 3. Inner cylinder (to hollow it out)
PIPE_INNER = {
    "operation": "primitive",
    "obj_id": "pipe_inner",
    "obj_type": "cylinder",
    "radius": 0.8,
    "height": 5,
    "center_coords": (0, 0, 0)
}

# 4. Create hollow pipe, then cut through wall
# Step 1: Create hollow pipe (cut inner from outer)
pipe_assembly = assemble_objects([PIPE_OUTER, PIPE_INNER])
pipe_assembly = apply_boolean_operations(pipe_assembly, [
    {"operation": "cut", "obj1": "pipe_outer", "obj2": "pipe_inner", "keep_obj2": False}
])

# Step 2: Now cut the hollow pipe through the wall
# Need to rebuild assembly with wall + the result
final_assembly = assemble_objects([BOX, PIPE_OUTER])  # Use pipe_outer from the hollow operation
final_assembly = apply_boolean_operations(final_assembly, [
    {"operation": "cut", "obj1": "wall", "obj2": "pipe_outer", "keep_obj2": True}
])
show(final_assembly)
time.sleep(1)

# 1. Box (the wall)
BOX = {
    "operation": "primitive",
    "obj_id": "wall",
    "obj_type": "box",
    "length": 10,
    "width": 10,
    "height": 2,
    "center_coords": (0, 0, 0)
}

# 2. Create hollow cylinder directly
wall_solid, _ = build_solid("primitive", BOX)
wall_solid = cast(cq.Workplane, wall_solid)  # ← Add this
hollow_pipe = cq.Workplane("XY").cylinder(5, 1).shell(0.2)  # Shell removes interior, 0.2 is wall thickness

# 3. Cut hole through wall with the hollow pipe
wall_with_hole = wall_solid.cut(hollow_pipe)

# 4. Show both
assembly = cq.Assembly()
assembly.add(wall_with_hole, name="wall_with_hole")
assembly.add(hollow_pipe, name="hollow_pipe")
show(assembly)
time.sleep(1)


import cadquery as cq
import cadquery as cq

box = cq.Workplane("XY").box(10, 10, 2)
outer = cq.Workplane("XY").cylinder(20, 3)
inner = cq.Workplane("XY").cylinder(20, 2)

# Cut the inner bore from the box+outer together, then subtract nothing
wall = box.union(outer).cut(inner)

show(wall)



