#!/usr/bin/env python3
"""Verify actual 0.3.2 Gerber deltas against 0.3.1; run in .venv-dfm.

Checks geometry and file integrity, not the proprietary supplier DFM rules.
"""
from pathlib import Path
from collections import defaultdict
import hashlib
import itertools
import json
import math
import re
from shapely.geometry import Polygon, LineString, Point, box
from shapely.ops import unary_union
from shapely.affinity import affine_transform
from audit_release_mask import read_gerber

ROOT = Path(__file__).resolve().parents[1]
OLD = ROOT/'release/collar-tracker-0.3.1-35x28-dfm'
NEW = ROOT/'release/collar-tracker-0.3.2-35x28-dfm'
E = ROOT/'experiments/35x28-mask-r032/evidence'

def normalized(path):
    return '\n'.join(line for line in path.read_text().splitlines()
                     if not line.startswith(('%TF.CreationDate,','%TF.ProjectId,','G04 Created by KiCad')))

unchanged=[]
for ext in ['gtl','g1','g2','gbl','gtp','gbp','gbs','gm1']:
    a=next(OLD.glob('*.'+ext)); b=next(NEW.glob('*.'+ext))
    assert normalized(a)==normalized(b), ('Unexpected output change',ext)
    unchanged.append(b.name)

# --subtract-soldermask adds clear apertures even to the empty front silk.
# Those clear commands change with U2's mask, but must not create any ink.
for directory in [OLD,NEW]:
    positive=True
    for line in (directory/'collar-tracker-F_Silkscreen.gto').read_text().splitlines():
        if line=='%LPC*%':positive=False
        if line=='%LPD*%':positive=True
        if positive:assert not re.match(r'[XY].*D0[13]\*',line), 'Unexpected front silk ink'

old_shapes,_=read_gerber(OLD/'collar-tracker-F_Mask.gts')
new_shapes,_=read_gerber(NEW/'collar-tracker-F_Mask.gts')
def owners(shapes):
    d=defaultdict(list)
    for ref,g in shapes:d[ref].append(g)
    return {ref:unary_union(gs) for ref,gs in d.items()}
old,new=owners(old_shapes),owners(new_shapes)
assert set(old)==set(new)
for ref in old:
    if ref!='U2':assert old[ref].symmetric_difference(new[ref]).area<1e-9, ref

data=json.loads((E/'geometry.json').read_text())
base_geometry=json.loads((ROOT/'experiments/35x28-mask-r031/evidence/geometry.json').read_text())
assert len(data['silks'])==len(base_geometry['silks'])==4
base_silk={s['id']:s for s in base_geometry['silks']}
for s in data['silks']:
    before=base_silk[s['id']]
    if s['text']=='COLLAR 0.3.2 TEST':
        assert before['text']=='COLLAR 0.3.1 TEST' and s['layer']==before['layer']=='B.Silkscreen'
    else:assert s==before
padnets={(p['ref'],p['pin']):p['net'] for p in data['pads']}
_,cu=read_gerber(NEW/'collar-tracker-F_Cu.gtl',copper=True)
u2pads=[p for p in cu if p['ref']=='U2']
assert len(u2pads)==11
expected=[]
changes=[]
for p in u2pads:
    x,y=p['xy']
    if p['pin']=='11':w,h=1.55,2.9
    elif p['pin'] in ['1','5','6','10']:w,h=.525,.515
    else:w,h=.525,.375
    g=box(x-w/2,y-h/2,x+w/2,y+h/2)
    if p['pin'] not in ['11','1','5','6','10']:
        # Unchanged KiCad expansion has a 0.05 mm corner radius.
        g=p['geometry'].buffer(.05,quad_segs=96)
    expected.append(g)
    assert p['geometry'].difference(g.buffer(.000001)).area<1e-8, p['pin']
    if p['pin']=='11' or p['pin'] in ['1','5','6','10']:
        changes.append((p,g))
assert new['U2'].symmetric_difference(unary_union(expected)).area<1e-7

gaps=[]
for side,filename in [('F.Mask','collar-tracker-F_Mask.gts'),('B.Mask','collar-tracker-B_Mask.gbs')]:
    shapes,_=read_gerber(NEW/filename)
    union=unary_union([g for _,g in shapes])
    parts=list(union.geoms) if hasattr(union,'geoms') else [union]
    for a,b in itertools.combinations(parts,2):
        d=a.distance(b)
        if d<.1999:gaps.append({'layer':side,'mm':d})
assert all(g['mm']>=.1-.00002 for g in gaps)

# Changed mask apertures must not uncover a foreign-net pad, trace or via.
# Ground pours are not parsed here; copper and zone settings did not change.
foreign=[]
for p,g in changes:
    net=padnets[(p['ref'],p['pin'])]
    native=affine_transform(g,[1,0,0,-1,100,128])
    distances=[]
    for t in data['tracks']:
        if t['layer']=='F.Cu' and t['net']!=net:
            distances.append(native.distance(LineString([t['start'],t['end']]).buffer(t['width']/2,quad_segs=96)))
    for v in data['vias']:
        if 'F.Cu' in v['layers'] and v['net']!=net:
            distances.append(native.distance(Point(v['pos']).buffer(v['diameter']/2,quad_segs=96)))
    for other in cu:
        if padnets[(other['ref'],other['pin'])]!=net:
            distances.append(g.distance(other['geometry']))
    minimum=min(distances)
    assert minimum>=.1499, (p['pin'],minimum)
    foreign.append({'pad':'U2.'+p['pin'],'minimum_to_foreign_pad_track_via_mm':minimum})

audit=json.loads((E/'gerber-mask-audit.json').read_text())
assert sum(s['pad_flashes'] for s in audit['sides'].values())==268
assert all(not s['partially_mask_covered'] for s in audit['sides'].values())
before=json.loads((ROOT/'experiments/35x28-mask-r031/evidence/gerber-mask-audit.json').read_text())
assert [(p['ref'],p['pin']) for s in before['sides'].values() for p in s['partially_mask_covered']]==[('U2','11')]
# Old large openings had rounded r=0.05 corners; new ones are rectangles.
expected_removed=.21-4*(4-math.pi)*.05**2
assert abs(old['U2'].difference(new['U2']).area-expected_removed)<.000005
assert abs(new['U2'].difference(old['U2']).area-.64015)<1e-7
result={
 'source':'Actual Gerber comparison of 0.3.1 and 0.3.2; metadata dates/revision only ignored.',
 'unchanged_copper_paste_bottom_mask_outline_files':unchanged,
 'front_silkscreen_remains_empty':True,
 'bottom_silkscreen_only_revision_label_changed':True,
 'other_component_top_masks_unchanged':True,
 'U2_mask_matches_204404H_figure7_dimensions':True,
 'copper_pads_fully_mask_exposed_before_after':[267,268],
 'total_copper_pads':268,
 'mask_added_mm2':new['U2'].difference(old['U2']).area,
 'mask_removed_mm2':old['U2'].difference(new['U2']).area,
 'changed_aperture_clearance_to_foreign_copper':foreign,
 'mask_bridge_min_mm':min(g['mm'] for g in gaps),
 'mask_bridges_below_010':[],
 'limitations':'Supplier has not analyzed this revision. Report negatives not individually mapped; same-net neck and pour topology are not certified by the foreign-net check. No SMT/physical/RF qualification.',
 'verified':True}
(E/'gerber-revision-checks.json').write_text(json.dumps(result,indent=2)+'\n')
print(json.dumps(result,indent=2))
