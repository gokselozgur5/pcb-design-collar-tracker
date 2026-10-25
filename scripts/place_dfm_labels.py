#!/usr/bin/env python3
"""Find positions for existing legends, using KiCad-exported glyph polygons.

Run with .venv-dfm/bin/python. Checks real pad/mask and drill geometry,
including tented holes. It is a local geometric check, not JLCDFM itself.
"""
from pathlib import Path
import itertools,json,math
from shapely.geometry import Polygon,Point,box
from shapely.ops import unary_union
from shapely.affinity import translate

ROOT=Path(__file__).resolve().parents[1];E=ROOT/'evidence/jlc-dfm-20261024'
data=json.loads((E/'geometry-stage1.json').read_text())
texts=json.loads((E/'silk-candidates.json').read_text())
def geom(p):return unary_union([Polygon(a) for a in p])
obstacles={l:[] for l in ['F.Silkscreen','B.Silkscreen']}
for p in data['pads']:
    for silk,mask,cu in [('F.Silkscreen','F.Mask','F.Cu'),('B.Silkscreen','B.Mask','B.Cu')]:
        if cu in p['layers']:
            obstacles[silk].append(geom(p['poly']).buffer(max(0,p['mask'].get(mask,0))+.16))
for v in data['vias']:
    for l in obstacles:obstacles[l].append(Point(v['pos']).buffer(v['drill']/2+.30))
for g in data['mask_graphics']:
    l='F.Silkscreen' if g['layer']=='F.Mask' else 'B.Silkscreen'
    obstacles[l].append(geom(g['poly']).buffer(.16))
allowed=box(100.3,100.3,129.7,121.7);result=[]
for t in sorted(texts,key=lambda t:0 if t['text']=='1V8 SWD' else 1):
    original=geom(t['poly']);obs=unary_union(obstacles[t['layer']]);chosen=None
    # Search near the connector first, and record exact displacement.
    deltas=sorted(itertools.product(range(-30,31),repeat=2),key=lambda d:(d[0]*d[0]+d[1]*d[1],abs(d[0])))
    for dx,dy in deltas:
        moved=translate(original,dx*.1,dy*.1)
        if allowed.covers(moved) and not moved.intersects(obs):chosen=(dx*.1,dy*.1,moved);break
    if chosen is None:raise RuntimeError('No legible local position for '+t['text'])
    dx,dy,moved=chosen;new=[round(t['pos'][0]+dx,4),round(t['pos'][1]+dy,4)]
    obstacles[t['layer']].append(moved.buffer(.2))
    result.append({'id':t['id'],'text':t['text'],'from':t['pos'],'to':new,'distance_mm':math.hypot(dx,dy),'poly':t['poly']})
(E/'silk-placement.json').write_text(json.dumps(result,indent=2)+'\n')
print(json.dumps([{k:v for k,v in a.items() if k!='poly'} for a in result],indent=2))
