"""
Assemble multiple 3D objects into one cq.Assembly.

Takes a list of object specifications, builds each one using build_solid(),
and assembles them together.
"""

from typing import Any, Dict, List, cast
import cadquery as cq
from ocp_vscode import show
import hashlib

from utils import insert_into

def _color_from_id(obj_id: str) -> cq.Color:
    """Deterministic pleasant color from obj_id string."""
    h = int(hashlib.md5(obj_id.encode()).hexdigest(), 16)
    r = ((h >> 16) & 0xFF) / 255
    g = ((h >> 8)  & 0xFF) / 255
    b = (h         & 0xFF) / 255
    # Bias toward mid-range brightness to avoid near-black or near-white
    r = 0.3 + r * 0.6
    g = 0.3 + g * 0.6
    b = 0.3 + b * 0.6
    return cq.Color(r, g, b)


def assemble_objects(object_specs: List[Dict[str, Any]]) -> cq.Assembly:
    """
    Build a list of objects and assemble them.
    
    Args:
        object_specs: List of dicts, each with "operation" key plus all build_solid() parameters.
                     Supports two formats for primitives:
                     - With "profile": {"obj_type": "cylinder", ...}
                     - Flattened: "obj_type": "cylinder", ... (directly in spec)
    
    Returns:
        cq.Assembly with all built objects
    
    Example:
        >>> specs = [
        ...     {"operation": "extrude", "profile": {...}, "height": 20, "obj_id": "beam"},
        ...     {"operation": "primitive", "obj_type": "cylinder", "radius": 5, ...},
        ... ]
        >>> assembly = assemble_objects(specs)
    """
    from build_3D_solid import build_solid  # Import here to avoid circular dependency if build_solid also imports assemble_objects
    assembly = cq.Assembly()
    objects: Dict[str, cq.Workplane] = {}


    for spec in object_specs:
        spec_copy = spec.copy()
        operation = spec_copy.pop("operation")
        spec_copy.pop("insert_into", None)   # strip before passing to build_solid

        if "profile" in spec_copy:
            solid, obj_id = build_solid(operation, **spec_copy)
        elif "obj_type" in spec_copy:
            profile = spec_copy.copy()
            obj_id            = profile.pop("obj_id", None)
            rotation_angles   = profile.pop("rotation_angles", (0, 0, 0))
            center_coords     = profile.pop("center_coords", None)
            center_coords_pol = profile.pop("center_coords_pol", None)
            solid, obj_id = build_solid(operation, profile,
                                        obj_id=obj_id,
                                        rotation_angles=rotation_angles,
                                        center_coords=center_coords,
                                        center_coords_pol=center_coords_pol)
        else:
            solid, obj_id = build_solid(operation, **spec_copy)

        objects[obj_id] = solid

    for spec in object_specs:
        target_id = spec.get("insert_into")
        if target_id is None:
            continue
        insert_id = spec.get("obj_id")
        if insert_id is None:
            raise ValueError("insert_into: spec is missing 'obj_id'")
        if target_id not in objects:
            raise ValueError(f"insert_into: target '{target_id}' not found in assembly")
        objects[target_id] = insert_into(objects[target_id], objects[insert_id])

    # The following is so that each component has a different color based on the hash of its name
    colors = {spec["obj_id"]: spec.get("color") for spec in object_specs if "obj_id" in spec}
    for obj_id, solid in objects.items():
        color_spec = colors.get(obj_id)
        if color_spec is not None:
            if not isinstance(color_spec, (tuple, list)) or len(color_spec) not in (3, 4):
                raise ValueError(f"'{obj_id}' color must be (r, g, b) or (r, g, b, a) with values in 0.0–1.0, got: {color_spec}")
            color = cq.Color(*color_spec)
        else:
            color = _color_from_id(obj_id)
        assembly.add(solid, name=obj_id, color=color)

    return assembly






def apply_boolean_operations(assembly: cq.Assembly, operations: List[Dict[str, Any]]) -> cq.Assembly:
    """
    Apply Boolean operations between solids in an assembly.
    
    Args:
        assembly: cq.Assembly with built objects
        operations: List of dicts specifying Boolean operations:
            - "operation": "union", "cut", or "intersect"
            - "obj1": obj_id of first object (result stored here)
            - "obj2": obj_id of second object
            - "keep_obj2": if True, keep obj2 in assembly; if False, remove it (default: True)
    
    Returns:
        Modified cq.Assembly with Boolean operations applied
    
    Example:
        >>> assembly = assemble_objects([...])
        >>> operations = [
        ...     {"operation": "union", "obj1": "beam", "obj2": "core"},
        ...     {"operation": "cut", "obj1": "beam", "obj2": "hole"},
        ... ]
        >>> assembly = apply_boolean_operations(assembly, operations)
    """
    # Extract objects from assembly into a dict for easy access
    objects = {child.name: child.obj for child in assembly.children}
    
    for op_spec in operations:
        operation = op_spec["operation"].lower()
        obj1_id = op_spec["obj1"]
        obj2_id = op_spec["obj2"]
        keep_obj2 = op_spec.get("keep_obj2", True)
        
        if obj1_id not in objects or obj2_id not in objects:
            raise ValueError(f"Objects not found in assembly: obj1='{obj1_id}', obj2='{obj2_id}'")
        
        obj1 = cast(cq.Workplane, objects[obj1_id])
        obj2 = cast(cq.Workplane, objects[obj2_id])
        
        # Apply Boolean operation
        if operation == "union":
            result = obj1.union(obj2)
        elif operation == "cut":
            result = obj1.cut(obj2)
        elif operation == "intersect":
            result = obj1.intersect(obj2)
        else:
            raise ValueError(f"Unknown operation: '{operation}'. Use 'union', 'cut', or 'intersect'")
        
        # Update obj1 with result, optionally remove obj2
        objects[obj1_id] = result
        if not keep_obj2:
            del objects[obj2_id]
    
    # Rebuild assembly from modified objects -  this is for when we didn't update the colors (so for when we did nto specify that each component has a different color based on the hash)
    # new_assembly = cq.Assembly()
    # for obj_id, obj in objects.items():
    #     new_assembly.add(obj, name=obj_id)

    # Rebuild assembly from modified objects - we include the fact that each component has a different color based on the hash of its name, so that when we do boolean operations, we can still see the different components in different colors (instead of them all becoming the same color after the boolean operation)
    new_assembly = cq.Assembly()
    for obj_id, obj in objects.items():
        # Retrieve original color from old assembly if it exists
        original = next((c for c in assembly.children if c.name == obj_id), None)
        color = original.color if original is not None else _color_from_id(obj_id)
        new_assembly.add(obj, name=obj_id, color=color)
    
    return new_assembly