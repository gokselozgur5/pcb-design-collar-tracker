#!/usr/bin/env python3
"""Plan small signal-via moves toward ground, preserving old routes with local stubs."""
import argparse
import hashlib
import json
import math
from pathlib import Path
import numpy as np
from shapely import intersects_xy
from shapely.geometry import Point, LineString, Polygon, box
from shapely.ops import unary_union

parser = argparse.ArgumentParser(description=__doc__)
parser.add_argument('trial', type=Path)
args = parser.parse_args()
t = args.trial
pcb = t/'hardware/collar-tracker.kicad_pcb'
g = json.loads((t/'evidence/route-geometry.json').read_text())
assert g['source_sha256'] == hashlib.sha256(pcb.read_bytes()).hexdigest()
assert t.resolve().name == 'power-r05h-six-layer'
extra = json.loads((t/'evidence/placement-extra.json').read_text())
# Footprint placement/keepouts are unchanged since the routing-only edits.
layers = g['copper_layers']
ground = [v['pos'] for v in g['vias'] if v['net']=='/GND']
signals = [v for v in g['vias'] if v['net']!='/GND']
allowed = {'/VDD_NRF','/VIO_ENABLE','/UV_DELAY','/COEX0','/HEALTH_INT','/HEALTH_CS'}
result, failed = [], []
for via in signals:
    before = min(math.dist(via['pos'], p) for p in ground)
    if before <= 2:
        continue
    assert via['net'] in allowed, via
    center = Point(via['pos'])
    attachments = [x for x in g['tracks'] if x['net']==via['net'] and
                   LineString([x['start'],x['end']]).distance(center) <= (via['diameter']+x['width'])/2+1e-6]
    bridges=[]
    for x in attachments:
        line=LineString([x['start'],x['end']])
        contact=list(line.interpolate(line.project(center)).coords)[0]
        if math.dist(contact,via['pos'])>1e-6:
            bridges.append(dict(layer=x['layer'],width=x['width'],start=list(contact),end=via['pos'][:]))
    widths = {layer:max(x['width'] for x in attachments if x['layer']==layer)
              for layer in {x['layer'] for x in attachments}}
    assert widths and not set(widths)&{'In1.Cu','In4.Cu'}
    shapes = {layer:[] for layer in layers}
    hole_blockers = []
    for pad in g['pads']:
        shape=unary_union([Polygon(p) for p in pad['poly']])
        hole_blockers.append(shape)
        if pad['net'] != via['net']:
            for layer in pad['layers']:shapes[layer].append(shape)
    for v in g['vias']:
        if v['id']==via['id']:continue
        shape=Point(v['pos']).buffer(v['diameter']/2,quad_segs=32)
        hole_blockers.append(shape)
        if v['net']!=via['net']:
            for layer in v['layers']:shapes[layer].append(shape)
    for x in g['tracks']:
        if x['net']!=via['net']:
            shape=LineString([x['start'],x['end']]).buffer(x['width']/2,quad_segs=32)
            shapes[x['layer']].append(shape);hole_blockers.append(shape)
    for z in extra['keepouts']:
        shape=unary_union([Polygon(p) for p in z['poly']])
        if z['vias']:hole_blockers.append(shape)
        if z['tracks']:shapes[z['layer']].append(shape)
    blocked=unary_union(hole_blockers).buffer(.501,quad_segs=32)
    forbidden={layer:unary_union(shapes[layer]).buffer(width/2+.201,quad_segs=32)
               for layer,width in widths.items()}
    if any(LineString([b['start'],b['end']]).intersects(forbidden[b['layer']]) for b in bridges):
        failed.append(dict(id=via['id'],reason='Preserving an off-center attachment needs copper review'))
        continue
    x,y=via['pos'];candidates=[]
    for dx in range(-30,31):
        for dy in range(-30,31):
            pos=[round(x+dx*.05,6),round(y+dy*.05,6)]
            if .001<math.dist(pos,via['pos'])<=1.5 and min(math.dist(pos,p) for p in ground)<1.99:
                candidates.append(pos)
    if candidates:
        array=np.array(candidates);mask=~intersects_xy(blocked,array[:,0],array[:,1])
        candidates=[p for p,ok in zip(candidates,mask) if ok]
    bounds=box(*g['board_bounds_mm']).buffer(-.701)
    candidates.sort(key=lambda p:math.dist(p,via['pos']))
    chosen=None
    for p in candidates:
        line=LineString([via['pos'],p])
        if bounds.covers(Point(p)) and all(not line.intersects(forbidden[l]) for l in widths):
            chosen=p;break
    if chosen is None:
        failed.append(dict(id=via['id'],net=via['net'],pos=via['pos'],before_mm=before,reason='No checked local move'))
        continue
    result.append(dict(id=via['id'],net=via['net'],old=via['pos'][:],new=chosen,
                       before_mm=before,after_mm=min(math.dist(chosen,p) for p in ground),
                       stubs=widths,attached_tracks=[x['id'] for x in attachments]))
    result[-1]['bridges']=bridges
    old_pos=via['pos'][:];via['pos']=chosen
    for layer,width in widths.items():
        g['tracks'].append(dict(id='proposed-'+via['id']+'-'+layer,net=via['net'],
                               layer=layer,width=width,start=old_pos,end=chosen))
    for i,b in enumerate(bridges):
        g['tracks'].append(dict(id='proposed-bridge-'+via['id']+'-'+str(i),net=via['net'],**b))
report=dict(before_sha256=g['source_sha256'],moves=result,failed=failed,
            scope='Source-bound geometry proposal only. Native connectivity, complete DRC and returns must be checked after application.')
(t/'evidence/return-via-moves-plan.json').write_text(json.dumps(report,indent=2)+'\n')
print(json.dumps(report,indent=2))
