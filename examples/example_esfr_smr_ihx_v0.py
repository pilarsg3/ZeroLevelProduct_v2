"""
Basic Intermediate Heat Exchanger (IHX) model - accurate structure.

Creates:
- Main vertical hollow cylinder (central shell)
- Two outlet tubes from the top (with curved transitions using ThreePointArc)
- Two outlet tubes perpendicular/horizontal from middle (with curved transitions)

Uses build_solid() and sweep operations with curved paths.
"""

import math
from typing import Callable, Tuple
import cadquery as cq
from assemble import assemble_objects
from ocp_vscode import show


def create_ihx_sweep_path_top() -> Callable[[float], Tuple[float, float, float]]:
    """
    Create a 3D curved path for top outlet nozzle.
    Returns parametric function for sweep: t goes from 0 to 1
    Path must start at (0, 0, 0) and curves outward/upward.
    """
    def path_func(t):
        # Arc from (0, 0, 0) curving outward and upward
        x = 0.30 * t
        y = 0.0
        z = 0.20 * (1 - (1 - t)**2)  # Quadratic easing for vertical rise
        return (x, y, z)
    return path_func


def create_ihx_sweep_path_side() -> Callable[[float], Tuple[float, float, float]]:
    """
    Create a 3D curved path for side outlet nozzle.
    Returns parametric function for sweep: t goes from 0 to 1
    Path must start at (0, 0, 0) and curves outward horizontally.
    """
    def path_func(t):
        # Arc from (0, 0, 0) curving outward horizontally
        x = 0.13 * t + 0.05 * (1 - (1 - t)**2)  # Horizontal extension
        y = 0.0
        z = 0.03 * math.sin(math.pi * t)  # Small vertical curve
        return (x, y, z)
    return path_func


def create_basic_ihx_specs(
    shell_id: float = 0.50,        # Inner diameter of main shell (m)
    shell_wall_t: float = 0.02,    # Wall thickness (m)
    shell_height: float = 2.5,     # Main shell height (m)
    outlet_nozzle_od: float = 0.08, # Outlet nozzle outer diameter (m)
) -> list:
    """
    Create object specifications for heat exchanger with curved nozzles.
    
    Args:
        shell_id: Inner diameter of main cylindrical shell
        shell_wall_t: Wall thickness
        shell_height: Height of main shell body
        outlet_nozzle_od: Outlet nozzle outer diameter
    
    Returns:
        List of object specification dicts
    """
    
    shell_od = shell_id + 2 * shell_wall_t
    shell_ri = shell_id / 2
    shell_ro = shell_od / 2
    nozzle_r = outlet_nozzle_od / 2
    
    specs = []
    
    # ===== MAIN SHELL - Large central hollow cylinder =====
    specs.append({
        "operation": "primitive",
        "obj_id": "shell_main",
        "obj_type": "pipe",
        "height": shell_height,
        "outer_radius": shell_ro,
        "inner_radius": shell_ri,
        "center_coords": (0, 0, shell_height / 2),
    })
    
    # ===== TOP OUTLET NOZZLES - Two tubes from top with curved transitions =====
    # Top-left outlet
    specs.append({
        "operation": "sweep",
        "obj_id": "nozzle_top_left",
        "profile": {"obj_type": "circle", "radius": nozzle_r},
        "path": create_ihx_sweep_path_top(),
        "center_coords": (0, 0, shell_height),  # Position at top of shell
    })
    
    # Top-right outlet (mirror)
    specs.append({
        "operation": "sweep",
        "obj_id": "nozzle_top_right",
        "profile": {"obj_type": "circle", "radius": nozzle_r},
        "path": create_ihx_sweep_path_top(),
        "center_coords": (0, 0, shell_height),  # Position at top of shell
        "rotation_angles": (0, 0, 180),  # Mirror to other side
    })
    
    # ===== SIDE OUTLET NOZZLES - Two horizontal tubes with curved transitions =====
    # Side outlet +X direction
    specs.append({
        "operation": "sweep",
        "obj_id": "nozzle_side_x",
        "profile": {"obj_type": "circle", "radius": nozzle_r},
        "path": create_ihx_sweep_path_side(),
        "center_coords": (shell_ro, 0, shell_height / 2),  # Position at shell edge, middle height
    })
    
    # Side outlet -X direction
    specs.append({
        "operation": "sweep",
        "obj_id": "nozzle_side_neg_x",
        "profile": {"obj_type": "circle", "radius": nozzle_r},
        "path": create_ihx_sweep_path_side(),
        "center_coords": (shell_ro, 0, shell_height / 2),  # Position at shell edge, middle height
        "rotation_angles": (0, 0, 180),  # Mirror to opposite side
    })
    
    return specs


# ===== EXAMPLE USAGE =====
if __name__ == "__main__":
    # Create the object specifications
    ihx_specs = create_basic_ihx_specs(
        shell_id=0.50,
        shell_wall_t=0.02,
        shell_height=2.5,
        outlet_nozzle_od=0.08,
    )
    
    # Assemble all components
    assembly = assemble_objects(ihx_specs)
    
    # Display the complete assembly
    show(assembly)
