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


def assemble_objects(object_specs: List[Dict[str, Any]], export_path: str | None = None) -> cq.Assembly:
    """
    Build a list of objects and assemble them.
    
    Args:
        object_specs: List of dicts, each with "operation" key plus all build_solid() parameters.
                     Supports two formats for primitives:
                     - With "profile": {"obj_type": "cylinder", ...}
                     - Flattened: "obj_type": "cylinder", ... (directly in spec)
        export_path: Optional file path to export the assembly as a STEP file.
                     STEP (.step / .stp) is the standard neutral CAD exchange format,
                     readable by Fusion 360, SolidWorks, FreeCAD, and all major CAD tools.
                     If None (default), no file is written.
                     Example: export_path="output/reactor.step"
    
    Returns:
        cq.Assembly with all built objects
    
    Example:
        >>> assembly = assemble_objects(specs)
        >>> assembly = assemble_objects(specs, export_path="output/reactor.step")
    """
    from build_3D_solid import build_solid  # Import here to avoid circular dependency if build_solid also imports assemble_objects
    assembly = cq.Assembly()
    objects: Dict[str, cq.Workplane] = {}


    for spec in object_specs:
        spec_copy = spec.copy()
        operation = spec_copy.pop("operation")
        spec_copy.pop("insert_into", None)   # strip before passing to build_solid
        spec_copy.pop("material", None)      # strip — not a build_solid parameter; original spec retains it for compute_bom(), export_openmc_materials(), etc.

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
        # normalise to list so both str and list are supported
        target_ids = [target_id] if isinstance(target_id, str) else target_id
        for tid in target_ids:
            if tid not in objects:
                raise ValueError(f"insert_into: target '{tid}' not found in assembly")
            objects[tid] = insert_into(objects[tid], objects[insert_id])

    # --- Overlap detection (runs after insert_into so cuts are already applied) ---
    # First, record every (child, parent) pair that was explicitly resolved via
    # insert_into so we don't fire false warnings for intentional penetrations.
    # Build a set of (child_id, parent_id) pairs that were explicitly resolved
    # via insert_into, so we don't warn about intentional penetrations.
    intentional_pairs = set()
    for spec in object_specs:
        target = spec.get("insert_into")
        if target is None:
            continue
        # Normalise to list, same as the insert_into loop above
        targets = [target] if isinstance(target, str) else target
        for tid in targets:
            intentional_pairs.add((spec["obj_id"], tid))
            intentional_pairs.add((tid, spec["obj_id"]))  # add both orderings

    # Then check all remaining pairs for unresolved overlaps.
    # Note: this is O(n²) — for large assemblies a bounding-box pre-filter
    # can be added later to skip pairs that clearly don't touch.
    import warnings
    solid_list = list(objects.items())
    for i in range(len(solid_list)):
        id_i, wp_i = solid_list[i]
        for j in range(i + 1, len(solid_list)):
            id_j, wp_j = solid_list[j]
            # Skip pairs that were intentionally connected via insert_into
            if (id_i, id_j) in intentional_pairs:
                continue
            try:
                inter = wp_i.val().intersect(wp_j.val())          # type: ignore
                if not inter.isNull() and inter.Volume() > 1e-6:
                    warnings.warn(
                        f"Unintentional overlap detected between '{id_i}' and '{id_j}' "
                        f"(volume ≈ {inter.Volume():.2f} mm³). "
                        f"Use insert_into or apply_boolean_operations to resolve.",
                        stacklevel=2,
                    )
            except Exception:
                # OCCT can throw on degenerate geometry pairs; skip silently
                pass


    # The following is so that each component has a different color based on the hash of its name
    # Assign a deterministic color per component based on obj_id hash,
    # unless the spec explicitly provides a color.
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

    assembly._specs = object_specs   # type: ignore  -> attach specs to the assembly

    if export_path is not None:
        import os
        parent = os.path.dirname(export_path)
        if parent:
            os.makedirs(parent, exist_ok=True)
        cq.exporters.export(assembly.toCompound(), export_path)
        print(f"Assembly exported to: {export_path}")

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
    
    new_assembly._specs = getattr(assembly, "_specs", [])  # type: ignore

    return new_assembly