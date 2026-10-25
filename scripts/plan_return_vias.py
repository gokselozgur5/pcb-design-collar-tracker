#!/usr/bin/env python3
"""Plan ground returns within the inherited 2 mm screen, using actual copper.

This is a geometry screen, not RF/EMC qualification. Apply only to the exact
hashed source, refill, and verify native connectivity afterward.
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
parser.add_argument('--reroute-inner-signals', action='store_true',
                    help='Six-layer WIP proposal only: reserve ground returns before rerouting the new inner signals')
parser.add_argument('--grid-mm', type=float, default=.1,
                    help='Placement search resolution; clearance and 2 mm screen are unchanged')
parser.add_argument('--historical-geometry', type=Path,
                    help='Also test exact historical GND via positions against current copper')
args = parser.parse_args()
assert args.grid_mm in (.1, .05, .025)
root = args.trial
pcb = root / 'hardware/collar-tracker.kicad_pcb'
g = json.loads((root / 'evidence/route-geometry.json').read_text())
source_sha = hashlib.sha256(pcb.read_bytes()).hexdigest()
assert g.get('source_sha256') == source_sha, 'Regenerate geometry from the current board'
extra = json.loads((root / 'evidence/placement-extra.json').read_text())
assert extra['source_sha256'] == source_sha, 'Regenerate placement metadata from the current board'
objects = []
deferred = []
if args.reroute_inner_signals:
    assert root.resolve().name == 'power-r05h-six-layer'
    assert g['copper_layers'] == ['F.Cu','In1.Cu','In2.Cu','In3.Cu','In4.Cu','B.Cu']
for p in g['pads']:
    objects.append(unary_union([Polygon(poly) for poly in p['poly']]))
for v in g['vias']:
    objects.append(Point(v['pos']).buffer(v['diameter']/2, quad_segs=32))
for t in g['tracks']:
    if args.reroute_inner_signals and t['layer'] in ['In2.Cu','In3.Cu']:
        deferred.append(t['id'])
        continue
    if t['net'] != '/GND':
        objects.append(LineString([t['start'], t['end']]).buffer(t['width']/2, quad_segs=16))
for z in extra['keepouts']:
    if z['vias']:
        objects.extend(Polygon(p) for p in z['poly'])
tree = STRtree(objects)
board = box(*g['board_bounds_mm']).buffer(-.701)
ground = [v['pos'] for v in g['vias'] if v['net']=='/GND']
signals = [v for v in g['vias'] if v['net']!='/GND']
assert ground
before = {v['id']: min(math.dist(v['pos'], p) for p in ground) for v in signals}
added = []
failed = []
historical = []
if args.historical_geometry:
    historical = [v['pos'] for v in json.loads(args.historical_geometry.read_text())['vias']
                  if v['net'] == '/GND']


def clear(p):
    point = Point(p)
    if not board.covers(point):
        return False
    for i in tree.query(point.buffer(.501)):
        if point.distance(objects[i]) < .501:
            return False
    return all(math.dist(p, other) >= .801 for other in added)


for via in sorted(signals, key=lambda v: before[v['id']], reverse=True):
    if min(math.dist(via['pos'], p) for p in ground+added) <= 2:
        continue
    x, y = via['pos']
    step=args.grid_mm; span=math.ceil(2/step)
    candidates = [(round((round(x/step)+dx)*step,6), round((round(y/step)+dy)*step,6))
                  for dx in range(-span, span+1) for dy in range(-span, span+1)] + historical
    candidates = [p for p in candidates if math.dist(p, via['pos']) < 2 and clear(p)]
    if not candidates:
        failed.append(via['id'])
        continue
    # Prefer a local return; among comparable distances cover nearby transitions too.
    candidates.sort(key=lambda p: math.dist(p,via['pos'])-.05*sum(
        min(math.dist(v['pos'],q) for q in ground+added)>2 and math.dist(v['pos'],p)<2
        for v in signals))
    added.append(candidates[0])
rows = [dict(via_id=v['id'], net=v['net'], pos=v['pos'], before_mm=before[v['id']],
             after_mm=min(math.dist(v['pos'],p) for p in ground+added)) for v in signals]
failed = [r['via_id'] for r in rows if r['after_mm']>2]
report = dict(source_sha256=source_sha,
              deferred_inner_tracks=deferred,
              grid_mm=args.grid_mm,
              historical_geometry_sha256=hashlib.sha256(args.historical_geometry.read_bytes()).hexdigest() if args.historical_geometry else None,
              ground_vias_before=len(ground), added=added, diameter_mm=.6, drill_mm=.2,
              target_mm=2, items=rows, failed=failed,
              scope='Planned Euclidean return-via spacing; native clearance/fill checks pending.')
(root/'evidence/return-via-plan.json').write_text(json.dumps(report,indent=2)+'\n')
print(json.dumps(dict(non_ground_vias=len(signals), outside_before=sum(x>2 for x in before.values()),
                     added=len(added), outside_after=len(failed), maximum_after_mm=max(r['after_mm'] for r in rows))))
