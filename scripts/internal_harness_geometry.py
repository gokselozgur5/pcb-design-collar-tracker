#!/usr/bin/env python3
"""Continuous cubic bounds for the internal charge-harness prototype."""
import numpy as np


def evaluate(control, count=4001):
    p = np.asarray(control, dtype=float)
    if p.ndim != 2 or p.shape[1] != 3 or len(p) < 4:
        raise ValueError('Expected at least four 3D control points')
    # Include every knot: the following Bezier conversion must not span a knot.
    spans = len(p) - 3
    panels = max(1, (count - 1 + spans - 1) // spans)
    t = np.linspace(0, 1, spans * panels + 1)
    k = np.r_[np.zeros(4), np.arange(1, spans) / spans, np.ones(4)]

    def at(c, knots, degree):
        ix = np.minimum(len(c)-1, np.searchsorted(knots, t, side='right')-1)
        work = c[ix[:, None]-degree+np.arange(degree+1)].copy()
        for level in range(1, degree+1):
            for j in range(degree, level-1, -1):
                i = ix-degree+j
                a = ((t-knots[i])/(knots[i+degree+1-level]-knots[i]))[:, None]
                work[:, j] = (1-a)*work[:, j-1]+a*work[:, j]
        return work[:, degree]

    d1 = 3*np.diff(p, axis=0)/(k[4:len(p)+3]-k[1:len(p)])[:, None]
    xyz = at(p, k, 3)
    velocity = at(d1, k[1:-1], 2)
    dt = 1/(len(t)-1)
    q = np.stack([xyz[:-1], xyz[:-1]+velocity[:-1]*dt/3,
                  xyz[1:]-velocity[1:]*dt/3, xyz[1:]], axis=1)
    v = 3*np.diff(q, axis=1)
    a = 2*np.diff(v, axis=1)
    direction = xyz[1:]-xyz[:-1]
    chord = np.linalg.norm(direction, axis=1)
    if np.any(chord <= 1e-12):
        raise ValueError('Stationary or degenerate curve interval')
    direction /= chord[:, None]
    speed_lower = np.min(np.sum(v*direction[:, None, :], axis=2), axis=1)
    cross_upper = np.linalg.norm(np.cross(v[:, :, None, :], a[:, None, :, :]), axis=3).max(axis=(1, 2))
    radius = np.divide(np.maximum(speed_lower, 0)**3, cross_upper,
                       out=np.full_like(chord, np.inf), where=cross_upper > 0)
    radius[speed_lower <= 0] = 0
    # Arc length lies between the endpoint chord and Bezier control polygon.
    upper = np.linalg.norm(np.diff(q, axis=1), axis=2).sum(axis=1)
    return dict(xyz=xyz, cells=q, arc_lower=np.r_[0, np.cumsum(chord)],
                arc_upper=np.r_[0, np.cumsum(upper)],
                radius_lower=float(radius.min()),
                travel_bound=float(np.linalg.norm(d1, axis=1).max())*dt,
                derivative=velocity)


def physical_radii(curve, spec):
    """Only fully stripped intervals get the smaller conductor envelope."""
    upper = curve['arc_upper']
    remainder = upper[-1]-upper
    reserve = (curve['travel_bound']/2 + spec['strip_length_tolerance_mm']
               + spec['free_route_position_allowance_mm'])
    bare = ((upper + reserve <= spec['terminal_strip_mm']) |
            (remainder + reserve <= spec['pcb_strip_mm']))
    return np.where(bare, spec['conductor_diameter_incoming_max_mm']/2,
                    spec['outside_diameter_max_mm']/2), bare
