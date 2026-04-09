import cadquery as cq
import math
from ocp_vscode import show


def build_utube(
    leg_height: float,
    bend_radius: float,
    tube_outer_r: float,
    tube_inner_r: float,
    pitch: float = 0.0,
) -> cq.Workplane:
    """
    Single U-tube built from explicit geometry (no sweep of hollow profile).

    Geometry (centreline, XZ plane):
      - Leg 1: straight cylinder along -Z, centred at x=0
      - U-bend: half-torus at z = -(leg_height + bend_radius), bend in XZ plane
      - Leg 2: straight cylinder along +Z, centred at x = 2*bend_radius (or pitch)

    Top of both legs sits at z = 0.
    """
    p = pitch if pitch > 0 else 2 * bend_radius

    def _solid_utube(r: float) -> cq.Workplane:
        """Build a solid (filled) U-tube with tube radius r."""

        # ---- Leg 1: along -Z at x=0 -----------------------------------
        leg1 = (
            cq.Workplane("XY")
            .circle(r)
            .extrude(leg_height)                        # extrudes +Z
            .translate((0, 0, -leg_height))             # shift so top is at z=0
        )

        # ---- Leg 2: along +Z at x=p -----------------------------------
        leg2 = (
            cq.Workplane("XY")
            .circle(r)
            .extrude(leg_height)
            .translate((p, 0, -leg_height))
        )

        # ---- U-bend: half-torus in XZ plane ----------------------------
        # Full torus: major radius = bend_radius (distance from torus centre to tube CL)
        #             minor radius = r (tube cross-section radius)
        # We only want the lower half (x >= 0 side that connects the two legs).
        #
        # The torus centre sits at (bend_radius, 0, -leg_height) in XZ.
        # We revolve a circle in the XZ plane 180° around Z at that centre.
        bend_centre_x = p / 2           # midpoint between the two leg centrelines
        torus_major   = p / 2           # = bend_radius when pitch = 2*bend_radius

        half_torus = (
            cq.Workplane("XZ")
            .workplane()
            .transformed(offset=(bend_centre_x, 0, -leg_height))
            .moveTo(torus_major, 0)     # start on tube centreline
            .circle(r)                  # minor cross-section
            .revolve(
                angleDegrees=180,
                axisStart=(0, 0, 0),
                axisEnd=(0, 1, 0),      # revolve around Y axis (local)
            )
        )

        return leg1.union(leg2).union(half_torus)

    outer = _solid_utube(tube_outer_r)
    inner = _solid_utube(tube_inner_r)

    return outer.cut(inner).clean()


def build_utube_bundle(
    bundle_layout: list[tuple[float, float]],
    leg_height: float,
    bend_radius: float,
    tube_outer_r: float,
    tube_inner_r: float,
) -> cq.Assembly:
    """
    Place U-tubes according to bundle_layout (x, y) positions of leg-1 centreline.
    """
    assembly = cq.Assembly()
    single   = build_utube(leg_height, bend_radius, tube_outer_r, tube_inner_r)

    for i, (x, y) in enumerate(bundle_layout):
        assembly.add(
            single.translate((x, y, 0)),
            name=f"utube_{i}"
        )
    return assembly


# -----------------------------------------------------------------------
# Quick test: single U-tube scaled to drawing (mm)
# -----------------------------------------------------------------------
UTUBE_BUNDLE = build_utube_bundle(
    bundle_layout = [(0, 0)],
    leg_height    = 4413,
    bend_radius   = 100,
    tube_outer_r  = 11,
    tube_inner_r  = 9,
)

show(UTUBE_BUNDLE)