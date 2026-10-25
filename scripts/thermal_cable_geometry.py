#!/usr/bin/env python3
"""Vectorized evaluation of the same clamped cubic used by the antenna model.

Only the r11 pose search uses this implementation. Independent regressions compare
positions, derivatives-derived radii, length and travel bounds with the preserved
scalar evaluator. This changes computation, not the cable acceptance thresholds.
"""
import numpy as np


def spline(control, count=1601):
    points = np.asarray(control, dtype=float)
    assert len(points) >= 4 and points.shape[1] == 3 and count >= 2
    knots = np.r_[np.zeros(4), np.arange(1, len(points)-3)/(len(points)-3), np.ones(4)]
    times = np.linspace(0, 1, count)

    def evaluate(c, k, degree):
        indices = np.minimum(len(c)-1, np.searchsorted(k, times, side='right')-1)
        work = c[indices[:, None]-degree+np.arange(degree+1)].copy()
        for level in range(1, degree+1):
            for j in range(degree, level-1, -1):
                i = indices-degree+j
                alpha = ((times-k[i])/(k[i+degree+1-level]-k[i]))[:, None]
                work[:, j] = (1-alpha)*work[:, j-1]+alpha*work[:, j]
        return work[:, degree]

    d1 = 3*np.diff(points, axis=0)/(knots[4:len(points)+3]-knots[1:len(points)])[:, None]
    d2 = 2*np.diff(d1, axis=0)/(knots[4:len(points)+2]-knots[2:len(points)])[:, None]
    xyz = evaluate(points, knots, 3)
    velocity = evaluate(d1, knots[1:-1], 2)
    acceleration = evaluate(d2, knots[2:-2], 1)
    speed = np.linalg.norm(velocity, axis=1)
    cross = np.linalg.norm(np.cross(velocity, acceleration), axis=1)
    radii = np.divide(speed**3, cross, out=np.full_like(speed, np.inf), where=cross > 1e-12)
    steps = np.linalg.norm(np.diff(xyz, axis=0), axis=1)
    arc = np.r_[0, np.cumsum(steps)]
    travel_bound = float(np.linalg.norm(d1, axis=1).max())/(count-1)
    return xyz, arc, radii, max(float(steps.max()), travel_bound)
