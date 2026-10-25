#!/usr/bin/env python3
"""Compare continuous outer-layer routing regions using exact exported copper.

This is a planning model, not native DRC or a completed route. Existing same-net
vias and feasible new via-center regions connect the two layer-region graphs.
"""
import argparse
import hashlib
import json
from pathlib import Path
from shapely.geometry import LineString, Point, Polygon, box
from shapely.ops import unary_union
from shapely.strtree import STRtree

parser = argparse.ArgumentParser(description=__doc__)
parser.add_argument('trial', type=Path)
parser.add_argument('net')
parser.add_argument('--pad-boxes', action='store_true')
parser.add_argument('--output', type=Path, required=True)
args = parser.parse_args()
g = json.loads((args.trial / 'evidence/route-geometry.json').read_text())
pcb = args.trial / 'hardware/collar-tracker.kicad_pcb'
assert g['source_sha256'] == hashlib.sha256(pcb.read_bytes()).hexdigest()
extra = json.loads((args.trial / 'evidence/placement-extra.json').read_text())
layers = ['F.Cu', 'B.Cu']
cu = {layer: [] for layer in layers}
for pad in g['pads']:
    shape = unary_union([Polygon(p) for p in pad['poly']])
    if args.pad_boxes:
        shape = box(*shape.bounds)
    for layer in layers:
        if layer in pad['layers']:
            cu[layer].append((shape, pad['net'], 'pad'))
for via in g['vias']:
    for layer in layers:
        cu[layer].append((Point(via['pos']).buffer(via['diameter'] / 2, quad_segs=32), via['net'], 'via'))
for track in g['tracks']:
    cu[track['layer']].append((LineString([track['start'], track['end']]).buffer(track['width'] / 2, quad_segs=32), track['net'], 'track'))
keepouts = {layer: {'tracks': [], 'vias': []} for layer in layers}
for zone in extra['keepouts']:
    shape = unary_union([Polygon(p) for p in zone['poly']])
    if args.pad_boxes:
        shape = box(*shape.bounds)
    for kind in ['tracks', 'vias']:
        if zone[kind]:
            keepouts[zone['layer']][kind].append(shape)

def polygons(shape):
    if shape.is_empty:
        return []
    if shape.geom_type == 'Polygon':
        return [shape]
    return [p for p in shape.geoms if p.geom_type == 'Polygon' and p.area > 1e-8]

free, via_blockers = {}, []
for layer in layers:
    obstacles = [s for s, n, _ in cu[layer] if n != args.net] + keepouts[layer]['tracks']
    free[layer] = polygons(box(*g['board_bounds_mm']).buffer(-.501).difference(
        unary_union(obstacles).buffer(.301, quad_segs=32)))
    via_blockers.extend(s for s, n, kind in cu[layer] if n != args.net or kind in {'pad', 'via'})
    via_blockers.extend(keepouts[layer]['tracks'] + keepouts[layer]['vias'])
via_free = polygons(box(*g['board_bounds_mm']).buffer(-.701).difference(
    unary_union(via_blockers).buffer(.501, quad_segs=32)))
trees = {layer: STRtree(free[layer]) for layer in layers}
parents = {(layer, i): (layer, i) for layer in layers for i in range(len(free[layer]))}

def region(layer, point):
    found = trees[layer].query(point, predicate='covered_by')
    return (layer, int(found[0])) if len(found) else None

def root(item):
    if item is None:
        return None
    while parents[item] != item:
        parents[item] = parents[parents[item]]
        item = parents[item]
    return item

def join(a, b):
    if a is not None and b is not None:
        parents[root(b)] = root(a)

for patch in via_free:
    point = patch.representative_point()
    join(region(layers[0], point), region(layers[1], point))
for via in g['vias']:
    if via['net'] == args.net:
        point = Point(via['pos'])
        join(region(layers[0], point), region(layers[1], point))
terminals = []
for pad in g['pads']:
    if pad['net'] != args.net:
        continue
    rows = {layer: root(region(layer, Point(pad['pos']))) for layer in layers if layer in pad['layers']}
    terminals.append(dict(pad=pad['ref'] + '.' + pad['pin'], pos=pad['pos'], region_groups=rows))
groups = {}
for layer, shapes in free.items():
    for i, shape in enumerate(shapes):
        key = str(root((layer, i)))
        groups.setdefault(key, []).append(dict(layer=layer, bounds=list(shape.bounds), area_mm2=shape.area))
report = dict(source_sha256=g['source_sha256'], net=args.net, pad_boxes=args.pad_boxes,
              track_width_mm=.2, added_clearance_mm=.201, via_diameter_mm=.6,
              layer_regions={layer: len(shapes) for layer, shapes in free.items()},
              available_new_via_regions=len(via_free), terminals=terminals, groups=groups,
              scope='Continuous geometric reachability only; an exact routed candidate and fresh native checks are required.')
args.output.write_text(json.dumps(report, indent=2) + '\n')
print(json.dumps({key: report[key] for key in ['net', 'pad_boxes', 'layer_regions', 'available_new_via_regions', 'terminals']}, indent=2))
