#!/usr/bin/env python3
"""Smooth cable centerlines and conservative sampled clearance calculations.

The supplied antenna cable construction and tolerances still need approval.
These functions check geometry, not RF performance or flex-cycle qualification.
"""
import math

import numpy as np


def spline(control, count=1601):
    """Clamped cubic B-spline, analytic first/second derivatives, and arc lengths."""
    points = np.asarray(control, dtype=float)
    degree = 3
    assert len(points) >= 4 and points.shape[1] == 3
    knots = np.r_[np.zeros(4), np.arange(1, len(points) - 3) / (len(points) - 3), np.ones(4)]

    def evaluate(c, k, d, times):
        result = []
        for t in times:
            index = min(len(c) - 1, np.searchsorted(k, t, side='right') - 1)
            work = c[index - d:index + 1].copy()
            for level in range(1, d + 1):
                for j in range(d, level - 1, -1):
                    i = index - d + j
                    alpha = (t - k[i]) / (k[i + d + 1 - level] - k[i])
                    work[j] = (1 - alpha) * work[j - 1] + alpha * work[j]
            result.append(work[d])
        return np.asarray(result)

    t = np.linspace(0, 1, count)
    xyz = evaluate(points, knots, degree, t)
    d1 = 3 * np.diff(points, axis=0) / (knots[4:len(points)+3] - knots[1:len(points)])[:, None]
    d2 = 2 * np.diff(d1, axis=0) / (knots[4:len(points)+2] - knots[2:len(points)])[:, None]
    velocity = evaluate(d1, knots[1:-1], 2, t)
    acceleration = evaluate(d2, knots[2:-2], 1, t)
    speed = np.linalg.norm(velocity, axis=1)
    cross = np.linalg.norm(np.cross(velocity, acceleration), axis=1)
    radii = np.divide(speed**3, cross, out=np.full_like(speed, np.inf), where=cross > 1e-12)
    steps = np.linalg.norm(np.diff(xyz, axis=0), axis=1)
    arc = np.r_[0, np.cumsum(steps)]
    # A derivative B-spline lies in the convex hull of its control vectors.
    # Its largest control-vector norm bounds speed on every sampling interval;
    # this bounds arc travel, unlike the shorter sample-to-sample chord.
    travel_bound = float(np.linalg.norm(d1, axis=1).max()) / (count - 1)
    return xyz, arc, radii, max(float(steps.max()), travel_bound)


def point_box_distance(points, low, high):
    """Distance to a closed AABB, including zero for points inside it."""
    return np.linalg.norm(np.maximum(np.maximum(np.asarray(low) - points, points - np.asarray(high)), 0), axis=1)


def curve_separation(a, b, own_arc=None, neighbor_length=0):
    """Sample separation; caller subtracts half-step bounds for both curves."""
    result = math.inf
    for start in range(0, len(a), 128):
        delta = a[start:start+128, None, :] - b[None, :, :]
        distances = np.linalg.norm(delta, axis=2)
        if own_arc is not None:
            distances[np.abs(own_arc[start:start+128, None] - own_arc[None, :]) <= neighbor_length] = np.inf
        result = min(result, float(distances.min()))
    return result
