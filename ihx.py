"""
ihx.py
======
General parametric Intermediate Heat Exchanger (IHX) builder.

Geometry (from hand-drawn flow diagram)
----------------------------------------
                    ┌──────────┐  ← primary elbow pipe exits here (horizontal)
                    │  neck    │  ← upper_neck (narrower cylinder above main shell)
               ─────┤          ├─────
               │    │ inner_cyl│    │
               │    │          │    │  ← main shell annulus
               │    │  funnel  │    │  ← inner structure tapers wider here (green)
               │  ──┤          ├──  │
               │  │ └──────────┘ │  │  ← lower_bundle (red, two concentric cylinders)
               └──┴──────────────┴──┘  ← hemispherical bottom

Primary sodium (yellow, orange arrows)
  → enters TOP via elbow pipe (horizontal → 90° bend → vertical DOWN into neck)
  → flows DOWN in annular region (between inner_cylinder and outer shell)
  → at bottom: flows UP through lower_bundle outer tube
  → exits via SECONDARY SIDE NOZZLE at mid-height  ← NOTE: exits here

Secondary sodium (blue)
  → enters via central channel at top
  → flows DOWN through inner_cylinder central bore
  → U-turn at bottom hemispherical plenum
  → flows UP through lower_bundle inner tube
  → exits via another nozzle

All dimensions must be provided explicitly.
See example_ihx_esfr_smart.py for ESFR-SMART worked example.

Example
-------
>>> from ihx import create_ihx
>>> parts = create_ihx(
...     shell_outer_radius = 0.663,
...     shell_height       = 9.963,
...     ...
... )
>>> assembly = cq.Assembly()
>>> for name, solid in parts.items():
...     assembly.add(solid, name=name)
>>> show(assembly)
"""

from __future__ import annotations

from typing import Sequence
import cadquery as cq


# ---------------------------------------------------------------------------
# Internal helpers
# ---------------------------------------------------------------------------

def _hollow_cyl(od: float, wall_t: float, h: float, z0: float = 0.0) -> cq.Workplane:
    """Hollow cylinder, bottom face at z=z0, top at z=z0+h."""
    r_out = od / 2
    r_in  = od / 2 - wall_t
    solid = (
        cq.Workplane("XY").workplane(offset=z0)
        .circle(r_out).extrude(h)
        .cut(
            cq.Workplane("XY").workplane(offset=z0)
            .circle(r_in).extrude(h)
        )
        .clean()
    )
    return solid


def _hemi_shell(od: float, wall_t: float) -> cq.Workplane:
    """Hemispherical shell cap, rim at z=0, extending downward."""
    r_out = od / 2
    r_in  = od / 2 - wall_t
    box   = cq.Workplane("XY").box(10*od, 10*od, 10*od).translate((0,0,-5*od))
    return (
        cq.Workplane("XY").sphere(r_out).intersect(box)
        .cut(cq.Workplane("XY").sphere(r_in).intersect(box))
        .clean()
    )


def _primary_elbow(
    pipe_od:   float,
    wall_t:    float,
    R_bend:    float,
    L_vert:    float,
    L_horiz:   float,
    z_top:     float,
) -> cq.Workplane:
    """
    Swept hollow elbow pipe.
    Vertical leg descends from z_top downward (length L_vert).
    90° bend, then horizontal leg of length L_horiz in +X direction.
    The elbow is built in the XZ plane.
    """
    from build_3D_solid import build_solid  # local import — avoids circular dependency

    # path: start at top, go DOWN (negative z), bend to +X
    # path_wire = (
    #     cq.Workplane("XZ")
    #     .moveTo(0, z_top)
    #     .lineTo(0, z_top - L_vert)
    #     .radiusArc((R_bend, z_top - L_vert - R_bend), -R_bend)
    #     .lineTo(R_bend + L_horiz, z_top - L_vert - R_bend)
    #     .wire()
    #     .val()
    # )
    path_wire = (
    cq.Workplane("XZ")
    .moveTo(R_bend + L_horiz, z_top)
    .lineTo(R_bend, z_top)
    .radiusArc((0, z_top - R_bend), -R_bend)   # ← negative sign
    .lineTo(0, z_top - R_bend - L_vert)
    .wire()
    .val()
    )

    outer, _ = build_solid("sweep",
        {"obj_type": "circle", "radius": pipe_od / 2},
        path=path_wire, isFrenet=True, plane="XY", obj_id="_ihx_el_out")  # type: ignore
    inner, _ = build_solid("sweep",
        {"obj_type": "circle", "radius": pipe_od / 2 - wall_t},
        path=path_wire, isFrenet=True, plane="XY", obj_id="_ihx_el_in")   # type: ignore
    return outer.cut(inner).clean()


def _side_nozzle(
    od:       float,
    wall_t:   float,
    length:   float,
    shell_od: float,
    z_centre: float,
) -> cq.Workplane:
    """Hollow horizontal nozzle in +X direction, root at shell outer surface."""
    r_out   = od / 2
    r_in    = od / 2 - wall_t
    x_start = shell_od / 2
    return (
        cq.Workplane("YZ")
        .circle(r_out).extrude(length)
        .cut(cq.Workplane("YZ").circle(r_in).extrude(length))
        .clean()
        .translate((x_start, 0, z_centre))
    )


def _revolved_profile(
    pts: Sequence[tuple[float, float]],
) -> cq.Workplane:
    """Body of revolution from a CLOSED (r, z) point list defining the full wall cross-section."""
    from build_3D_solid import build_solid
    solid, _ = build_solid(
        "revolve", list(pts),
        angle=360, plane="XZ", axis="Z",
        obj_id="_ihx_rev",
        # no wall_thickness — profile already defines the hollow shell
    )
    return solid


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------

def create_ihx(
    # ── Outer main shell ────────────────────────────────────────────────
    shell_outer_radius:    float,   # outer radius of main cylindrical shell
    shell_height:          float,   # height of main straight section
    shell_wall_t:          float,   # shell wall thickness
    shell_bottom_t:        float,   # hemispherical bottom thickness

    # ── Upper neck (narrower cylinder above main shell) ──────────────────
    neck_outer_radius:     float,   # outer radius of neck
    neck_wall_t:           float,   # neck wall thickness
    neck_height:           float,   # height of neck above main shell top

    # ── Inner cylinder (runs through neck + upper main shell) ─────────────
    inner_cyl_outer_radius: float,  # outer radius of inner cylinder
    inner_cyl_wall_t:       float,
    inner_cyl_height:       float,  # total height of inner cylinder
    inner_cyl_z_bottom:     float,  # z of bottom face of inner cylinder

    # ── Inner funnel / taper (revolved profile, green region) ─────────────
    funnel_profile:        Sequence[tuple[float, float]],
    funnel_wall_t:         float,

    # ── Lower tube bundle (two concentric cylinders, red region) ──────────
    bundle_outer_od:       float,   # outer diameter of outer tube
    bundle_outer_wall_t:   float,
    bundle_inner_od:       float,   # outer diameter of inner tube
    bundle_inner_wall_t:   float,
    bundle_height:         float,   # height of tube bundle section
    bundle_z_bottom:       float,   # z of bottom face of tube bundle

    # ── Primary sodium elbow pipe (top of neck) ───────────────────────────
    primary_pipe_od:       float,
    primary_pipe_wall_t:   float,
    primary_R_bend:        float,
    primary_L_vert:        float,   # vertical leg going DOWN from neck top
    primary_L_horiz:       float,   # horizontal leg in +X direction

    # ── Side nozzle (primary outlet / secondary inlet, mid-height) ────────
    side_nozzle_od:        float,
    side_nozzle_wall_t:    float,
    side_nozzle_length:    float,
    side_nozzle_z:         float,   # z centre of nozzle

) -> dict[str, cq.Workplane]:
    """
    Build a parametric IHX with the geometry visible in the ESFR-SMART
    hand-drawn flow diagram:

      outer_shell      — main pressure boundary + hemispherical bottom
      upper_neck       — narrower cylinder above main shell
      inner_cylinder   — central flow separator (through neck + upper shell)
      funnel           — tapered inner structure (widens toward lower section)
      lower_bundle_outer — outer concentric tube in lower section
      lower_bundle_inner — inner concentric tube in lower section
      primary_elbow    — swept elbow pipe at top of neck
      side_nozzle      — horizontal nozzle at mid-height of main shell

    All dimensions in metres. No defaults — must supply all parameters.
    See example_ihx_esfr_smart.py for ESFR-SMART dimensions.
    """

    # ── validation ──────────────────────────────────────────────────────
    if shell_outer_radius  <= 0: raise ValueError("shell_outer_radius must be > 0")
    if neck_outer_radius   <= 0: raise ValueError("neck_outer_radius must be > 0")
    if neck_outer_radius   >= shell_outer_radius:
        raise ValueError("neck_outer_radius must be < shell_outer_radius")
    if inner_cyl_outer_radius >= neck_outer_radius:
        raise ValueError("inner_cyl_outer_radius must be < neck_outer_radius")

    parts: dict[str, cq.Workplane] = {}

    # ── 1. Outer main shell (straight section) ───────────────────────────
    shell_cyl = _hollow_cyl(
        od     = 2 * shell_outer_radius,
        wall_t = shell_wall_t,
        h      = shell_height,
        z0     = 0.0,
    )
    shell_hemi = _hemi_shell(
        od     = 2 * shell_outer_radius,
        wall_t = shell_bottom_t,
    )
    parts["outer_shell"] = shell_cyl.union(shell_hemi).clean()

    # ── 2. Upper neck ────────────────────────────────────────────────────
    parts["upper_neck"] = _hollow_cyl(
        od     = 2 * neck_outer_radius,
        wall_t = neck_wall_t,
        h      = neck_height,
        z0     = shell_height,
    )

    # ── 3. Inner cylinder ────────────────────────────────────────────────
    parts["inner_cylinder"] = _hollow_cyl(
        od     = 2 * inner_cyl_outer_radius,
        wall_t = inner_cyl_wall_t,
        h      = inner_cyl_height,
        z0     = inner_cyl_z_bottom,
    )

    # ── 4. Funnel / inner tapered structure ──────────────────────────────
    parts["funnel"] = _revolved_profile(
        pts = funnel_profile,
    )

    # ── 5. Lower tube bundle — outer tube ────────────────────────────────
    parts["lower_bundle_outer"] = _hollow_cyl(
        od     = bundle_outer_od,
        wall_t = bundle_outer_wall_t,
        h      = bundle_height,
        z0     = bundle_z_bottom,
    )

    # ── 6. Lower tube bundle — inner tube ────────────────────────────────
    parts["lower_bundle_inner"] = _hollow_cyl(
        od     = bundle_inner_od,
        wall_t = bundle_inner_wall_t,
        h      = bundle_height,
        z0     = bundle_z_bottom,
    )

    # ── 7. Primary sodium elbow pipe (enters neck from top) ─────────────
    neck_top_z = shell_height + neck_height
    parts["primary_elbow"] = _primary_elbow(
        pipe_od  = primary_pipe_od,
        wall_t   = primary_pipe_wall_t,
        R_bend   = primary_R_bend,
        L_vert   = primary_L_vert,
        L_horiz  = primary_L_horiz,
        z_top    = neck_top_z,
    )

    # ── 8. Side nozzle ───────────────────────────────────────────────────
    parts["side_nozzle"] = _side_nozzle(
        od       = side_nozzle_od,
        wall_t   = side_nozzle_wall_t,
        length   = side_nozzle_length,
        shell_od = 2 * shell_outer_radius,
        z_centre = side_nozzle_z,
    )

    return parts