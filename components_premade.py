"""
Pre-made domain components.

Accessed through the same dict interface as build_3D_primitive(), so they
slot into assemble_objects() and build_solid() exactly like any primitive.

The distinction from components_3D_primitives.py:

  components_3D_primitives  — pure geometry, no domain knowledge
                               (cylinder, pipe, box, sphere, …)
  components_premade        — domain-specific assemblies, built from
                               primitives + boolean operations
                               (reactor_vessel, reactor_top_plate, …)

Adding a new component
----------------------
1. Write a  _build_<name>(obj: dict) -> cq.Workplane  function below.
2. Add one entry to PREMADE_BUILDERS.
Nothing else in the codebase needs to change.

Usage (identical style to all other build_solid primitives)
-----------------------------------------------------------
>>> RPV = {
...     "operation":          "primitive",
...     "obj_id":             "rpv",
...     "obj_type":           "reactor_vessel",
...     "inner_d":            4.72,
...     "wall_t":             0.04,
...     "straight_h":         5.5,
...     "bottom_head_type":   "ellipsoidal",
...     "bottom_head_params": {"head_depth": 1.0},
... }
>>> TOP_PLATE = {
...     "operation":  "primitive",
...     "obj_id":     "top_plate",
...     "obj_type":   "reactor_top_plate",
...     "outer_d":    4.72 + 2 * 0.04,
...     "thickness":  0.1,
...     "z_bottom":   5.5,
...     "hole_groups": [...],
... }
>>> assembly = assemble_objects([RPV, TOP_PLATE, ...])
"""

from __future__ import annotations
from typing import Any
import cadquery as cq

from reactor_vessel import create_reactor_vessel
from top_plate      import create_top_plate


# ---------------------------------------------------------------------------
# Individual builders — each takes the raw dict, returns cq.Workplane
# ---------------------------------------------------------------------------

def _build_reactor_vessel(obj: dict[str, Any]) -> cq.Workplane:
    vessel, _ = create_reactor_vessel(
        inner_d            = obj["inner_d"],
        wall_t             = obj["wall_t"],
        straight_h         = obj["straight_h"],
        bottom_head_type   = obj.get("bottom_head_type"),
        bottom_head_params = obj.get("bottom_head_params"),
        top_head_type      = obj.get("top_head_type"),
        top_head_params    = obj.get("top_head_params"),
        # top_plate intentionally excluded — use "reactor_top_plate" separately
    )
    return vessel


def _build_reactor_top_plate(obj: dict[str, Any]) -> cq.Workplane:
    return create_top_plate(
        plate_outer_d   = obj["outer_d"],
        plate_thickness = obj["thickness"],
        center_coords   = (0.0, 0.0, obj["z_bottom"] + obj["thickness"] / 2.0),
        hole_groups     = obj.get("hole_groups"),
    )


# ---------------------------------------------------------------------------
# Registry — the only thing that needs editing when adding a new component
# ---------------------------------------------------------------------------

PREMADE_BUILDERS: dict[str, Any] = {
    "reactor_vessel":    _build_reactor_vessel,
    "reactor_top_plate": _build_reactor_top_plate,
}


# ---------------------------------------------------------------------------
# Public entry point — mirrors build_3D_primitive() signature
# ---------------------------------------------------------------------------

def build_premade_component(obj: dict[str, Any]) -> cq.Workplane:
    obj_type = obj.get("obj_type", "")
    if obj_type not in PREMADE_BUILDERS:
        raise ValueError(
            f"Unknown premade component {obj_type!r}. "
            f"Available: {sorted(PREMADE_BUILDERS)}"
        )
    return PREMADE_BUILDERS[obj_type](obj)