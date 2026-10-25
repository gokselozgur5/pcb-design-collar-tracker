#!/usr/bin/env python3
"""Verify the actual 0.3 -> 0.3.1 Gerber aperture changes independently."""
from pathlib import Path
import json
from itertools import combinations
from shapely.ops import unary_union
from shapely.geometry import Polygon,LineString
from audit_release_mask import read_gerber

ROOT=Path(__file__).resolve().parents[1]
BASE=ROOT/'release/collar-tracker-0.3-35x28-dfm'
NEW=ROOT/'release/collar-tracker-0.3.1-35x28-dfm'
E=ROOT/'experiments/35x28-mask-r031/evidence'
caps={'C1','C2','C5','C8'};contacts={'J3','J4','J5','J6','J7'}
report={'scope':'Before/after actual exported copper pad, mask and paste apertures; not supplier DFM or powered testing.',
        'arc_model_quadrant_segments':96,
        'capacitors':{},'contact_minimum_expansion_mm':{},'ufl':{},'mask_components_under_010':[],
        'all_unlisted_pad_copper_unchanged':True}
for side,ce,me,pe in [('top','gtl','gts','gtp'),('bottom','gbl','gbs','gbp')]:
    _,oldpads=read_gerber(next(BASE.glob('*.'+ce)),copper=True)
    _,newpads=read_gerber(next(NEW.glob('*.'+ce)),copper=True)
    oldm,_=read_gerber(next(BASE.glob('*.'+me)))
    newm,_=read_gerber(next(NEW.glob('*.'+me)))
    paste,_=read_gerber(next(NEW.glob('*.'+pe)))
    assert len(oldpads)==len(newpads)
    for a,b in zip(oldpads,newpads):
        assert (a['ref'],a['pin'])==(b['ref'],b['pin'])
        if b['ref'] not in caps:
            assert a['xy']==b['xy'] and a['geometry'].equals(b['geometry'])
    for ref in sorted({p['ref'] for p in newpads}&caps):
        old=[p for p in oldpads if p['ref']==ref];new=[p for p in newpads if p['ref']==ref]
        assert len(new)==len(old)==2
        gap=new[0]['geometry'].distance(new[1]['geometry'])
        assert abs(gap-.25)<1e-6
        mu=unary_union([g for r,g in newm if r==ref]);pu=unary_union([g for r,g in paste if r==ref])
        parts=list(mu.geoms);assert len(parts)==2
        maskgap=parts[0].distance(parts[1]);assert abs(maskgap-.20)<1e-6
        paste_ratios=[p['geometry'].intersection(pu).area/p['geometry'].area for p in new]
        assert all(abs(x-1)<1e-8 for x in paste_ratios)
        report['capacitors'][ref]={'old_copper_gap_mm':old[0]['geometry'].distance(old[1]['geometry']),
          'new_copper_gap_mm':gap,'new_mask_bridge_mm':maskgap,'paste_copper_overlap_ratio':paste_ratios}
    for ref in sorted({p['ref'] for p in newpads}&contacts):
        mu=unary_union([g for r,g in newm if r==ref])
        ps=[p for p in newpads if p['ref']==ref]
        assert all(mu.buffer(1e-7).covers(p['geometry']) for p in ps)
        minimum=min(p['geometry'].boundary.distance(mu.boundary) for p in ps)
        assert minimum>.04998
        report['contact_minimum_expansion_mm'][ref]=minimum
    if side=='top':
        for ref in ['J1','J2']:
            old=[g for r,g in oldm if r==ref];new=[g for r,g in newm if r==ref]
            assert len(old)==4 and len(new)==1
            a=unary_union(old);b=new[0]
            diff=a.hausdorff_distance(b)
            assert diff<.000002
            report['ufl'][ref]={'old_shapes':len(old),'new_shapes':len(new),'polygon_model_boundary_change_mm':diff,
                               'maximum_arc_polygonization_error_mm':.000011}
    mu=unary_union([g for r,g in newm]);parts=list(mu.geoms)
    for a,b in combinations(parts,2):
        gap=a.distance(b)
        if 1e-7<gap<.1-1e-6:report['mask_components_under_010'].append({'side':side,'gap_mm':gap})
assert not report['mask_components_under_010']
d=json.loads((E/'geometry.json').read_text())
pad=next(p for p in d['pads'] if p['ref']=='U2' and p['pin']=='1')
g=unary_union([Polygon(p) for p in pad['poly']]).buffer(pad['mask']['F.Mask'],quad_segs=96)
tr=next(t for t in d['tracks'] if t['id']=='623202d5-9d9d-4aab-8057-7aa98301ea52')
tg=LineString([tr['start'],tr['end']]).buffer(tr['width']/2,quad_segs=96)
report['u2_1_to_control_track_mask_gap_mm']=g.distance(tg)
assert report['u2_1_to_control_track_mask_gap_mm']>=.21-1e-6
report['passed']=True
(E/'gerber-revision-checks.json').write_text(json.dumps(report,indent=2)+'\n')
print(json.dumps(report,indent=2))
