#!/usr/bin/env python3
"""Independent local checks for the corrected JLC findings, using native geometry.

This is not an implementation of the proprietary JLCDFM analyzer. The PDF
does not include coordinates for every occurrence; its counts are not treated
as a list of uniquely reproduced faults. Use the new supplier run for closure.
"""
from pathlib import Path
import itertools,json
from shapely.geometry import Polygon,Point,box
from shapely.ops import unary_union

ROOT=Path(__file__).resolve().parents[1];E=ROOT/'evidence/jlc-dfm-20261024'
def geom(polys):return unary_union([Polygon(p) for p in polys])
def check(p):
    copper=[];mask={'F.Mask':[],'B.Mask':[]};gaps=[];bridges=[];silk=[]
    for a in p['pads']:
        g=geom(a['poly']);label=a['ref']+'.'+a['pin']
        copper.append((label,g,a['layers']))
        for l,e in a['mask'].items():
            opening=g.buffer(e,quad_segs=32)
            if not opening.is_empty:mask[l].append(opening)
    for a in p['vias']:copper.append(('via@'+str(a['pos']),Point(a['pos']).buffer(a['diameter']/2,quad_segs=64),a['layers']))
    for a in p['mask_graphics']:mask[a['layer']].append(geom(a['poly']))
    for a,b in itertools.combinations(copper,2):
        if not set(a[2])&set(b[2]):continue
        d=a[1].distance(b[1])
        if 1e-5<d<.1-1e-6:gaps.append({'a':a[0],'b':b[0],'gap_mm':d})
    for layer,shapes in mask.items():
        union=unary_union(shapes);parts=list(union.geoms) if hasattr(union,'geoms') else [union]
        for a,b in itertools.combinations(parts,2):
            d=a.distance(b)
            if 1e-5<d<.1-1e-6:bridges.append({'layer':layer,'gap_mm':d})
    for t in p.get('silks',[]):
        g=geom(t['poly']);layer='F.Cu' if t['layer']=='F.Silkscreen' else 'B.Cu';ml='F.Mask' if layer=='F.Cu' else 'B.Mask'
        pads=[geom(a['poly']).buffer(max(0,a['mask'].get(ml,0)),quad_segs=32) for a in p['pads'] if layer in a['layers']]
        pad_gap=min(g.distance(a) for a in pads)
        hole_gap=min(g.distance(Point(v['pos']).buffer(v['drill']/2,quad_segs=64)) for v in p['vias'])
        silk.append({'text':t['text'],'pad_or_mask_clearance_mm':pad_gap,'hole_clearance_mm':hole_gap,'inside_edge_margin_03':box(100.3,100.3,129.7,121.7).covers(g)})
    return {'pad_via_gaps_under_010_mm':gaps,'mask_bridges_under_010_mm':bridges,'silks':silk}

before=json.loads((E/'geometry-before.json').read_text());after=json.loads((E/'geometry-after.json').read_text())
r={'before':check(before),'after':check(after),'scope':'Local pad/via, mask bridge, legend geometry and topology checks; not JLCDFM acceptance.'}
# Ensure the cosmetic repair has not silently changed routing or pad copper.
assert before['tracks']==after['tracks'],'Track geometry changed'
assert before['vias']==after['vias'],'Via geometry changed'
pa={p['id']:p for p in before['pads']};pb={p['id']:p for p in after['pads']};assert pa.keys()==pb.keys()
for ident,a in pa.items():
    b=pb[ident];assert (a['net'],a['pin'],a['layers'])==(b['net'],b['pin'],b['layers'])
    delta=[b['pos'][i]-a['pos'][i] for i in range(2)]
    expected=[0,.2] if a['ref']=='J4' else [0,0]
    assert all(abs(x-y)<1e-6 for x,y in zip(delta,expected)),a['ref']
    assert abs(geom(a['poly']).area-geom(b['poly']).area)<1e-6
assert len(r['before']['mask_bridges_under_010_mm'])==6,'Baseline must reproduce six thin U.FL mask bridges'
assert r['before']['pad_via_gaps_under_010_mm'],'Baseline must reject the close battery via'
assert not r['after']['mask_bridges_under_010_mm']
assert not r['after']['pad_via_gaps_under_010_mm']
assert all(t['pad_or_mask_clearance_mm']>=.15 and t['hole_clearance_mm']>=.3 and t['inside_edge_margin_03'] for t in r['after']['silks'])
r['invariants']={'track_geometry_unchanged':True,'via_geometry_unchanged':True,'pad_nets_and_shapes_unchanged':True,'only_J4_moved_02_mm':True}
(E/'geometry-verification.json').write_text(json.dumps(r,indent=2)+'\n')
print(json.dumps(r,indent=2))
