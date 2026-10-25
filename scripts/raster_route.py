#!/usr/bin/env python3
"""Read-only 0.2 mm route proposal using precomputed conservative grid geometry.

Input/output are JSON on standard streams. Shapely/NumPy do the repeated geometry
queries; the caller owns native application, length limits and full KiCad DRC.
"""
import heapq
import itertools
import json
import math
import sys
import time
import numpy as np
from shapely import intersects_xy
from shapely.geometry import LineString, Point, box
from shapely.ops import unary_union


def search(data):
    started = time.monotonic()
    step = .05
    assert data['width'] == .2
    xmin, ymin, xmax, ymax = data['bounds']
    x0, y0 = round(xmin / step), round(ymin / step)
    nx, ny = round((xmax - xmin) / step) + 1, round((ymax - ymin) / step) + 1
    count = nx * ny
    xx, yy = np.meshgrid((np.arange(nx) + x0) * step, (np.arange(ny) + y0) * step)
    line_shapes, via_shapes = [[], []], [[], []]
    for kind, layer, net, raw, bounds in data['objects']:
        if kind in {'pad', 'keepout', 'via_keepout'}:
            shape = box(*bounds)
        elif kind == 'via':
            shape = Point(raw[:2]).buffer(raw[2], quad_segs=32)
        else:
            shape = LineString([raw[:2], raw[2:4]]).buffer(raw[4], quad_segs=32)
        if net != data['net'] and kind != 'via_keepout':
            line_shapes[layer].append(shape)
        if net != data['net'] or kind in {'pad', 'via'}:
            via_shapes[layer].append(shape)
    obstacles = [unary_union(shapes).buffer(.301, quad_segs=32) for shapes in line_shapes]
    via_obstacle = unary_union(via_shapes[0] + via_shapes[1]).buffer(.501, quad_segs=32)
    inside = (xx >= xmin + .501) & (xx <= xmax - .501) & (yy >= ymin + .501) & (yy <= ymax - .501)
    free = np.stack([inside & ~intersects_xy(shape, xx, yy) for shape in obstacles])
    via_inside = (xx >= xmin + .701) & (xx <= xmax - .701) & (yy >= ymin + .701) & (yy <= ymax - .701)
    via_free = (via_inside & ~intersects_xy(via_obstacle, xx, yy)).ravel()
    directions = [(1, 0), (-1, 0), (0, 1), (0, -1), (1, 1), (-1, 1), (1, -1), (-1, -1)]
    mid_free = []
    for dx, dy in directions:
        mx, my = xx + dx * step / 2, yy + dy * step / 2
        # An edge can only be used when both endpoint nodes are free. Query
        # expensive polygon midpoints only for those candidates; this retains
        # the exact same grid predicate, including diagonal corner checks.
        other_free = np.roll(free, shift=(-dy, -dx), axis=(1, 2))
        possible = free & other_free
        if dx > 0:
            possible[:, :, -dx:] = False
        elif dx < 0:
            possible[:, :, :-dx] = False
        if dy > 0:
            possible[:, -dy:, :] = False
        elif dy < 0:
            possible[:, :-dy, :] = False
        edges = np.zeros_like(free)
        for layer, shape in enumerate(obstacles):
            selected = possible[layer]
            edges[layer][selected] = ~intersects_xy(shape, mx[selected], my[selected])
        mid_free.append(edges.ravel())
    free = free.ravel()

    def nearby(points):
        result = {}
        for point in points:
            px, py, layer = point
            ix, iy = round(px / step) - x0, round(py / step) - y0
            for dx, dy in itertools.product(range(-1, 2), repeat=2):
                jx, jy = ix + dx, iy + dy
                if not (0 <= jx < nx and 0 <= jy < ny):
                    continue
                node = layer * count + jy * nx + jx
                if not free[node]:
                    continue
                qx, qy = (jx + x0) * step, (jy + y0) * step
                samples = np.linspace(0, 1, 5)
                sx, sy = px + (qx - px) * samples, py + (qy - py) * samples
                if np.any(intersects_xy(obstacles[layer], sx, sy)):
                    continue
                result[node] = point
        return result

    starts, targets = nearby(data['starts']), nearby(data['ends'])
    if not starts or not targets:
        return dict(status='no access', visited=0, starts=len(starts), targets=len(targets))
    # Bounding-box distance is an admissible lower bound to every target.
    tx, ty = [p[0] for p in data['ends']], [p[1] for p in data['ends']]
    hx = np.maximum(np.maximum(min(tx) - xx, xx - max(tx)), 0)
    hy = np.maximum(np.maximum(min(ty) - yy, yy - max(ty)), 0)
    heuristic = np.hypot(hx, hy).ravel().tolist() * 2
    distance = [math.inf] * (count * 2)
    parent = [-1] * (count * 2)
    origins = {}
    queue, serial = [], itertools.count()
    for node, point in starts.items():
        local = node % count
        x, y = (local % nx + x0) * step, (local // nx + y0) * step
        distance[node] = math.hypot(point[0] - x, point[1] - y)
        origins[node] = point
        heapq.heappush(queue, (distance[node] + heuristic[node], next(serial), node))
    found, visited = None, 0
    while queue and visited < data.get('state_limit', 600000):
        cost, _, node = heapq.heappop(queue)
        if cost > distance[node] + heuristic[node] + 1e-8:
            continue
        visited += 1
        if node in targets:
            found = node
            break
        local, layer = node % count, node // count
        ix, iy = local % nx, local // nx
        neighbors = []
        for direction, (dx, dy) in enumerate(directions):
            if not (0 <= ix + dx < nx and 0 <= iy + dy < ny):
                continue
            other = node + dx + dy * nx
            if free[other] and mid_free[direction][node]:
                neighbors.append((other, step * math.hypot(dx, dy)))
        if via_free[local]:
            neighbors.append((local + (1 - layer) * count, 2.))
        for other, added in neighbors:
            candidate = distance[node] + added
            if candidate + 1e-9 < distance[other]:
                distance[other] = candidate
                parent[other] = node
                heapq.heappush(queue, (candidate + heuristic[other], next(serial), other))
    result = dict(status='found' if found is not None else 'no route', visited=visited,
                  elapsed_seconds=time.monotonic() - started, grid_step_mm=step,
                  pending_native_acceptance=True)
    if found is None:
        return result
    path, node = [], found
    while parent[node] != -1:
        local = node % count
        path.append([(local % nx + x0) * step, (local // nx + y0) * step, node // count])
        node = parent[node]
    local = node % count
    path.append([(local % nx + x0) * step, (local // nx + y0) * step, node // count])
    result['points'] = [origins[node]] + list(reversed(path)) + [targets[found]]
    return result


if __name__ == '__main__':
    print(json.dumps(search(json.load(sys.stdin))))
