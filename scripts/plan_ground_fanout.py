#!/usr/bin/env python3
"""Plan local GND pad-to-via stubs from exported physical geometry.

Run with the Shapely environment, then apply with KiCad. This is a planner;
native DRC and filled-plane connectivity remain mandatory acceptance gates.
"""
import argparse
import hashlib
import json
import math
from pathlib import Path

from shapely.geometry import LineString, Point, Polygon, box
from shapely.ops import unary_union
from shapely.strtree import STRtree

parser = argparse.ArgumentParser()
parser.add_argument('trial', type=Path)
args = parser.parse_args()
root = args.trial
geometry = json.loads((root / 'evidence/placement-geometry.json').read_text())
extra = json.loads((root / 'evidence/placement-extra.json').read_text())
clearance, via_radius, max_length = .2, .3, 2.2
pads = geometry['pads']
pad_shapes = [unary_union([Polygon(p) for p in pad['poly']]) for pad in pads]
pad_tree = STRtree(pad_shapes)
keepouts = [(Polygon(p), z) for z in extra['keepouts'] for p in z['poly']]
tracks = [(LineString([t['start'], t['end']]).buffer(t['width'] / 2), t) for t in geometry['tracks']]
board = box(*extra['bounds'])
vias, stubs, failures = [], [], []


def via_clear(pos):
    point = Point(pos)
    if not board.buffer(-(.4 + via_radius)).covers(point):
        return False
    for i in pad_tree.query(point.buffer(via_radius + clearance)):
        if point.distance(pad_shapes[i]) < via_radius + clearance - 1e-6:
            return False
    for shape, z in keepouts:
        if z['vias'] and point.distance(shape) < via_radius + clearance - 1e-6:
            return False
    for shape, t in tracks:
        if t['net'] != '/GND' and point.distance(shape) < via_radius + clearance - 1e-6:
            return False
    return all(math.dist(pos, v) >= 2 * via_radius + clearance - 1e-6 for v in vias)


def simple_paths(start, end):
    dx, dy = end[0] - start[0], end[1] - start[1]
    length = min(abs(dx), abs(dy))
    sx, sy = (1 if dx >= 0 else -1), (1 if dy >= 0 else -1)
    for mid in [(start[0] + sx * length, start[1] + sy * length),
                (end[0] - sx * length, end[1] - sy * length)]:
        out = [tuple(start)]
        for p in [mid, tuple(end)]:
            p = tuple(round(v, 6) for v in p)
            if math.dist(out[-1], p) > 1e-6:
                out.append(p)
        if len(out) > 1:
            yield out


def paths(start, end):
    yield from simple_paths(start, end)
    # Escape a fine-pitch row before turning toward a clear via position.
    for neck in [.2, .4, .6, .8, 1.0]:
        for dx, dy in [(1, 0), (-1, 0), (0, 1), (0, -1)]:
            mid = (round(start[0] + dx * neck, 6), round(start[1] + dy * neck, 6))
            for tail in simple_paths(mid, end):
                points = [tuple(start), *tail]
                if LineString(points).length <= max_length:
                    yield points


def width_for(pad):
    if pad['ref'] == 'U1':
        # 0.25 leaves margin beside the 0.5-mm-pitch perimeter contacts.
        # The larger internal ground lands can take a wider 0.3-mm neck.
        return .3 if int(pad['pin']) >= 105 else .25
    if pad['ref'].startswith('J') or (pad['ref'] in ['U2', 'U3'] and pad['pin'] == '11'):
        return .3
    others = [p for p in pads if p['ref'] == pad['ref'] and p['net'] != '/GND']
    if len(others) == 1:
        width = .4 if others[0]['net'] in ['/VIN_5V', '/VBAT', '/VSYS', '/VDD_NRF'] else .3 if others[0]['net'] == '/VIO_1V8' else .2
        shape = pad_shapes[pads.index(pad)]
        x1, y1, x2, y2 = shape.bounds
        return round(max(.2, min(width, x2 - x1, y2 - y1)), 6)
    return .2


def path_clear(points, pad, index, width):
    line = LineString(points)
    if line.length > max_length or not board.buffer(-(.4 + width / 2)).covers(line):
        return False
    for i in pad_tree.query(line.buffer(width / 2 + clearance)):
        if i != index and set(pad['layers']).intersection(pads[i]['layers']):
            # Adjacent IC ground terminals may share a short local connection.
            # Do not run a ground bus through separate passive components.
            if pads[i]['net'] == '/GND' and pads[i]['ref'] == pad['ref'] and pad['ref'].startswith('U'):
                continue
            if line.distance(pad_shapes[i]) < width / 2 + clearance - 1e-6:
                return False
    for shape, z in keepouts:
        if z['tracks'] and z['layer'] in pad['layers'] and line.distance(shape) < width / 2 + clearance - 1e-6:
            return False
    for shape, t in tracks:
        if t['net'] != '/GND' and t['layer'] in pad['layers'] and line.distance(shape) < width / 2 + clearance - 1e-6:
            return False
    return True


ground = [(i, pad) for i, pad in enumerate(pads) if pad['net'] == '/GND']
priority = {'U3': 0, 'U2': 1, 'U5': 2, 'D1': 3, 'U1': 4}
ground.sort(key=lambda x: (priority.get(x[1]['ref'], 5), x[1]['ref'], int(x[1]['pin']), x[0]))
for index, pad in ground:
    width = width_for(pad)
    px, py = pad['pos']
    candidates = [(tuple(v), True) for v in vias if math.dist((px, py), v) <= max_length]
    for radius in [i / 10 for i in range(6, 23)]:
        for dx, dy in [(1, 0), (-1, 0), (0, 1), (0, -1), (1, 1), (-1, 1), (1, -1), (-1, -1)]:
            candidates.append(((round((px + dx * radius) * 20) / 20,
                                round((py + dy * radius) * 20) / 20), False))
    candidates.sort(key=lambda c: math.dist((px, py), c[0]) - (.12 if c[1] else 0))
    selected = None
    for pos, shared in candidates:
        if not shared and not via_clear(pos):
            continue
        for points in paths((px, py), pos):
            if path_clear(points, pad, index, width):
                selected = (pos, shared, points)
                break
        if selected:
            break
    if selected is None:
        # Fine-pitch packages may need an off-axis via; keep the route itself
        # orthogonal/45 degrees. Search a local grid, still with the same limits.
        grid = [(round(px * 20 + ix) / 20, round(py * 20 + iy) / 20)
                for ix in range(-44, 45) for iy in range(-44, 45)]
        grid = sorted(set(grid), key=lambda v: math.dist((px, py), v))
        for pos in grid:
            if math.dist((px, py), pos) > max_length or not via_clear(pos):
                continue
            for points in paths((px, py), pos):
                if path_clear(points, pad, index, width):
                    selected = (pos, False, points)
                    break
            if selected:
                break
    if selected is None:
        failures.append({'ref': pad['ref'], 'pin': pad['pin'], 'id': pad['id'], 'pos': pad['pos']})
        continue
    pos, shared, points = selected
    if not shared:
        vias.append(pos)
    stubs.append({'ref': pad['ref'], 'pin': pad['pin'], 'pad_id': pad['id'],
                  'layer': pad['layers'][0], 'points': points, 'width': width,
                  'length': LineString(points).length, 'shared_via': shared, 'via': pos})

source = root / 'hardware/collar-tracker.kicad_pcb'
plan = {'source_sha256': hashlib.sha256(source.read_bytes()).hexdigest(),
        'target': {'via_diameter': .6, 'via_drill': .2, 'clearance': clearance, 'max_stub_length': max_length},
        'ground_pads': len(ground), 'vias': vias, 'stubs': stubs, 'failures': failures,
        'scope': 'Planned geometry only; native DRC and filled-plane connectivity not yet checked.'}
(root / 'evidence/ground-plan.json').write_text(json.dumps(plan, indent=2) + '\n')
print(json.dumps({'ground_pads': len(ground), 'connected_in_plan': len(stubs), 'vias': len(vias),
                  'max_stub_mm': max(s['length'] for s in stubs), 'failures': failures}, indent=2))
