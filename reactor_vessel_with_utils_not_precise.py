from __future__ import annotations

import math
from typing import Any

import cadquery as cq

from utils import extrude_profile, revolve_profile
from top_plate import create_top_plate


# ---------------------------------------------------------------------------
# Bottom head builders
# Each returns a solid with its rim in the XY plane at z=0,
# extending downward (z < 0).
# ---------------------------------------------------------------------------

def _head_flat(od: float, plate_t: float, **_) -> cq.Workplane:
    wp = cq.Workplane("XY").placeSketch(
        cq.Sketch().circle(od / 2)
    )
    return extrude_profile(wp, -plate_t)


def _head_hemispherical(od: float, **_) -> cq.Workplane:
    r = od / 2
    sphere = cq.Workplane("XY").sphere(r)
    cutter = (
        cq.Workplane("XY")
        .box(10 * od, 10 * od, 10 * od)
        .translate((0, 0, -5 * od))
    )
    return sphere.intersect(cutter)


def _head_ellipsoidal(od: float, head_depth: float, n: int = 40, **_) -> cq.Workplane:
    r = od / 2
    pts = [
        (r * math.cos(t), -head_depth * math.sin(t))
        for t in [i * (math.pi / 2) / n for i in range(n + 1)]
    ]
    # Build the 2D profile on XZ plane as a workplane with a sketch
    s = cq.Sketch()
    for i in range(len(pts) - 1):
        s = s.segment(pts[i], pts[i + 1])
    s = s.segment(pts[-1], (0, 0)).segment((0, 0), pts[0]).assemble()
    wp = cq.Workplane("XZ").placeSketch(s)
    wp._plane_name = "XZ"  # type: ignore[attr-defined]
    return revolve_profile(wp, angle=360, axis="Z")


def _head_torispherical(
    od: float,
    Rc: float | None = None,
    rk: float | None = None,
    n_crown: int = 80,
    n_knuckle: int = 40,
    **_,
) -> cq.Workplane:
    r = od / 2
    Rc = od if Rc is None else Rc
    rk = 0.06 * od if rk is None else rk

    if rk <= 0:   raise ValueError("rk must be > 0")
    if Rc <= r:   raise ValueError("Rc must be > od/2")
    if Rc <= rk:  raise ValueError("Rc must be > rk")

    xk, zk = r - rk, 0.0
    d   = Rc - rk
    rad = d * d - xk * xk
    if rad <= 0:
        raise ValueError("Infeasible Rc/rk for this od")
    zc = math.sqrt(rad)

    dx, dz = xk, zk - zc
    L   = math.hypot(dx, dz)
    ux, uz = dx / L, dz / L
    xt  = Rc * ux
    zt  = zc + Rc * uz

    a0 = math.atan2(0.0 - zk, r - xk)
    a1 = math.atan2(zt - zk, xt - xk)
    if a1 > a0:
        a1 -= 2 * math.pi
    knuckle_pts = [
        (xk + rk * math.cos(a), zk + rk * math.sin(a))
        for a in [a0 + i * (a1 - a0) / n_knuckle for i in range(n_knuckle + 1)]
    ]

    b0 = math.atan2(zt - zc, xt)
    b1 = -math.pi / 2
    crown_pts = [
        (Rc * math.cos(b), zc + Rc * math.sin(b))
        for b in [b0 + i * (b1 - b0) / n_crown for i in range(1, n_crown + 1)]
    ]

    pts = knuckle_pts + crown_pts
    s = cq.Sketch()
    for i in range(len(pts) - 1):
        s = s.segment(pts[i], pts[i + 1])
    s = s.segment(pts[-1], (0, 0)).segment((0, 0), pts[0]).assemble()
    wp = cq.Workplane("XZ").placeSketch(s)
    wp._plane_name = "XZ"  # type: ignore[attr-defined]
    return revolve_profile(wp, angle=360, axis="Z")


_HEAD_BUILDERS = {
    "flat":          _head_flat,
    "hemispherical": _head_hemispherical,
    "ellipsoidal":   _head_ellipsoidal,
    "torispherical": _head_torispherical,
}


def _build_outer_head(od: float, head_type: str, params: dict) -> cq.Workplane:
    if head_type not in _HEAD_BUILDERS:
        raise ValueError(
            f"Unknown head type '{head_type}'. "
            f"Choose from: {list(_HEAD_BUILDERS)}"
        )
    return _HEAD_BUILDERS[head_type](od, **params)


def _build_top_head(od: float, head_type: str, params: dict, z0: float) -> cq.Workplane:
    h = _build_outer_head(od, head_type, params)
    return h.mirror("XY").translate((0, 0, z0))


# ---------------------------------------------------------------------------
# Public API — unchanged signature, now uses utils internally
# ---------------------------------------------------------------------------

def create_reactor_vessel(
    inner_d: float,
    wall_t: float,
    straight_h: float,
    *,
    bottom_head_type:      str | None = None,
    bottom_head_params:    dict | None = None,
    top_head_type:         str | None = None,
    top_head_params:       dict | None = None,
    top_plate_thickness:   float | None = None,
    top_plate_hole_groups: list[dict[str, Any]] | None = None,
) -> tuple[cq.Workplane, cq.Workplane | None]:

    if inner_d    <= 0: raise ValueError("inner_d must be > 0")
    if wall_t     <= 0: raise ValueError("wall_t must be > 0")
    if straight_h <= 0: raise ValueError("straight_h must be > 0")

    bottom_head_params = dict(bottom_head_params or {})
    top_head_params    = dict(top_head_params    or {})

    if bottom_head_type == "flat":
        bottom_head_params.setdefault("plate_t", wall_t)
    if top_head_type == "flat":
        top_head_params.setdefault("plate_t", wall_t)

    if bottom_head_type == "ellipsoidal" and "head_depth" not in bottom_head_params:
        raise ValueError("bottom_head_type='ellipsoidal' requires head_depth")
    if top_head_type == "ellipsoidal" and "head_depth" not in top_head_params:
        raise ValueError("top_head_type='ellipsoidal' requires head_depth")

    od = inner_d + 2 * wall_t

    # ── 1. Outer shell — now via extrude_profile ─────────────────────────
    outer_wp = cq.Workplane("XY").placeSketch(cq.Sketch().circle(od / 2))
    outer    = extrude_profile(outer_wp, straight_h)

    if bottom_head_type == "flat":
        t     = float(bottom_head_params["plate_t"])
        bh_wp = cq.Workplane("XY").placeSketch(cq.Sketch().circle(od / 2))
        outer = outer.union(extrude_profile(bh_wp, -t))
    elif bottom_head_type is not None:
        outer = outer.union(_build_outer_head(od, bottom_head_type, bottom_head_params))

    if top_head_type == "flat":
        t     = float(top_head_params["plate_t"])
        th_wp = cq.Workplane("XY").workplane(offset=straight_h).placeSketch(
            cq.Sketch().circle(od / 2)
        )
        outer = outer.union(extrude_profile(th_wp, t))
    elif top_head_type is not None:
        outer = outer.union(_build_top_head(od, top_head_type, top_head_params, straight_h))

    # ── 2. Inner bore ─────────────────────────────────────────────────────
    inner_wp = cq.Workplane("XY").placeSketch(cq.Sketch().circle(inner_d / 2))
    inner    = extrude_profile(inner_wp, straight_h)

    if bottom_head_type == "ellipsoidal":
        hd = float(bottom_head_params["head_depth"])
        p  = {**bottom_head_params, "head_depth": max(hd - wall_t, 1e-3)}
        inner = inner.union(_build_outer_head(inner_d, "ellipsoidal", p))
    elif bottom_head_type not in (None, "flat"):
        inner = inner.union(_build_outer_head(inner_d, bottom_head_type, bottom_head_params))

    if top_head_type == "ellipsoidal":
        hd = float(top_head_params["head_depth"])
        p  = {**top_head_params, "head_depth": max(hd - wall_t, 1e-3)}
        inner = inner.union(_build_top_head(inner_d, "ellipsoidal", p, straight_h))
    elif top_head_type not in (None, "flat"):
        inner = inner.union(_build_top_head(inner_d, top_head_type, top_head_params, straight_h))

    vessel = outer.cut(inner).clean()

    # ── 3. Top plate ──────────────────────────────────────────────────────
    top_plate = None
    if top_plate_thickness is not None:
        top_plate = create_top_plate(
            plate_outer_d   = od,
            plate_thickness = top_plate_thickness,
            center_coords   = (0.0, 0.0, straight_h + top_plate_thickness / 2.0),
            hole_groups     = top_plate_hole_groups,
        )

    return vessel, top_plate