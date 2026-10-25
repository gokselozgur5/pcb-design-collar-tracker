#!/usr/bin/env python3
"""Independent geometry audit of the size experiment, including pad bounding boxes.

Run after dfm_geometry.py with .venv-dfm/bin/python. This does not reproduce
the proprietary JLCDFM algorithm or qualify RF, battery or circuit operation.
"""
from pathlib import Path
import itertools,json,hashlib,sys
from shapely.geometry import Polygon,Point,LineString,box
from shapely.ops import unary_union
from shapely.affinity import translate

ROOT=Path(__file__).resolve().parents[1];OUT=Path(sys.argv[1]).resolve() if len(sys.argv)>1 else ROOT/'experiments/35x28';E=OUT/'evidence'
mask_revision=len(sys.argv)>2 and sys.argv[2]=='--mask-revision-031'
mask_revision032=len(sys.argv)>2 and sys.argv[2]=='--mask-revision-032'
assert len(sys.argv)<=2 or mask_revision or mask_revision032, 'Unknown verification profile'
inner2=json.loads((E/'source.json').read_text()).get('inner2_signal',False)
data=json.loads((E/'geometry.json').read_text())
base_path=('experiments/35x28-mask-r031/evidence/geometry.json' if mask_revision032 else
           'experiments/35x28-in2/evidence/geometry.json' if mask_revision else
           'evidence/jlc-dfm-20261024/geometry-after.json')
base=json.loads((ROOT/base_path).read_text())
def geom(a):return unary_union([Polygon(p) for p in a])
def label(p):return p['ref']+'.'+p['pin']
pads=[(p,geom(p['poly'])) for p in data['pads']]
vias=[(v,Point(v['pos']).buffer(v['diameter']/2,quad_segs=96)) for v in data['vias']]
tracks=[(t,LineString([t['start'],t['end']]).buffer(t['width']/2,quad_segs=32)) for t in data['tracks']]
report={'scope':'Local native copper/legend geometry only. Not supplier DFM acceptance.',
    'pcb_sha256':hashlib.sha256(Path(data['source']).read_bytes()).hexdigest(),
    'size_mm':[35,28,.8],'footprints':len(set(p['ref'] for p in data['pads'])),
    'tracks':len(tracks),'vias':len(vias),
    'minimum_track_width_mm':min(t['width'] for t,g in tracks),
    'inner_signal_segments':sum(t['layer'] in ['In1.Cu','In2.Cu'] for t,g in tracks),
    'reserved_ground_plane_signal_segments':sum(t['layer']=='In1.Cu' or (t['layer']=='In2.Cu' and not inner2) for t,g in tracks),
    'via_sizes_mm':sorted(set((v['diameter'],v['drill']) for v,g in vias)),
    'minimum_via_annulus_mm':min(((v['diameter']-v['drill'])/2 for v,g in vias),default=None)}
failures=[]
old={(p['ref'],p['pin']):p for p in base['pads']}
for p,g in pads:
    before=old[(p['ref'],p['pin'])];shift=translate(geom(before['poly']),p['pos'][0]-before['pos'][0],p['pos'][1]-before['pos'][1])
    expected_mask=before['mask']
    shape_ok=g.symmetric_difference(shift).area<=1e-5
    if mask_revision:
        if p['ref'] in ['C1','C2','C5','C8']:
            expected_mask={l:.025 for l in before['mask']}
            x0,y0,x1,y1=g.bounds
            original=geom(before['poly']);ox0,oy0,ox1,oy1=original.bounds
            # C2 is rotated 90 degrees; preserve the land's long-axis orientation.
            w,h=(.30,.35) if ox1-ox0>oy1-oy0 else (.35,.30)
            shape_ok=abs(x1-x0-w)<1e-5 and abs(y1-y0-h)<1e-5 and g.within(original)
        elif p['ref'] in ['J1','J2']:expected_mask={}
        elif p['ref'] in ['J3','J4','J5','J6','J7']:expected_mask={l:.05 for l in before['mask']}
    if mask_revision032 and p['ref']=='U2' and p['pin'] in ['1','5','6','10']:
        expected_mask={}
    if (p['net'],p['layers'],p['mask'])!=(before['net'],before['layers'],expected_mask) or not shape_ok:
        failures.append({'category':'changed_pad','pad':label(p)})
if mask_revision:
    # Audit the bounded source delta, not just an allowlist of references.
    assert {p['id'] for p in data['pads']}=={p['id'] for p in base['pads']}
    assert data['vias']==base['vias'],'Unexpected via change'
    old_tracks={t['id']:t for t in base['tracks']};new_tracks={t['id']:t for t in data['tracks']}
    assert set(old_tracks)==set(new_tracks)
    expected={
      '623202d5-9d9d-4aab-8057-7aa98301ea52':([124.76,117.0],[124.76,119.2195]),
      '6b5d4c50-3553-4d4a-8fca-8e81a61c3808':([124.1875,117.0],[124.76,117.0]),
      '86fe62c8-bf2a-4fcf-b3bd-cbbd80495d56':([124.76,119.2195],[124.3583,119.6212])}
    for uid,t in new_tracks.items():
        want=dict(old_tracks[uid])
        if uid in expected:
            assert want['net']=='/GNSS_LNA_EN' and want['layer']=='F.Cu'
            want.update(start=expected[uid][0],end=expected[uid][1])
        assert t==want,('Unexpected track delta',uid)
    for ref in ['C1','C2','C5','C8']:
        pair=[(p,g) for p,g in pads if p['ref']==ref]
        assert len(pair)==2
        assert abs(pair[0][1].distance(pair[1][1])-.25)<1e-5
        for p,g in pair:
            oldpad=old[(p['ref'],p['pin'])]
            assert abs(Point(p['pos']).distance(Point(oldpad['pos']))-.045)<1e-5
    for ref in ['J1','J2']:
        # The old native effective-pad polygons are coarse approximations
        # (about 7.4 um at these rounded corners). Compare against the actual
        # released Gerber union used by the plan, not those approximations.
        prior=Polygon(json.loads((E/'ufl-mask-plan.json').read_text())[ref]['points_mm'])
        newparts=[geom(m['poly']) for m in data['mask_graphics'] if m['ref']==ref]
        assert len(newparts)==1
        assert prior.hausdorff_distance(newparts[0])<.000002
    assert all(z['clearance_mm']==.25 for z in data['zones'])
    report['verified_revision_profile']='0.3.1 bounded pad/mask/control-route delta; original RF tracks and all vias unchanged'
if mask_revision032:
    assert {p['id'] for p in data['pads']}=={p['id'] for p in base['pads']}
    old_by_id={p['id']:p for p in base['pads']}
    for p,g in pads:
        before=old_by_id[p['id']]
        assert p['pos']==before['pos'] and p['poly']==before['poly'], ('Copper pad changed',label(p))
    assert data['tracks']==base['tracks'] and data['vias']==base['vias'], 'Routing changed'
    assert data['zones']==base['zones'], 'Zone settings changed'
    assert [m for m in data['mask_graphics'] if m['ref']!='U2']==[m for m in base['mask_graphics'] if m['ref']!='U2']
    parts=[geom(m['poly']) for m in data['mask_graphics'] if m['ref']=='U2']
    assert len(parts)==5
    expected=[box(123-.775,116.5-1.45,123+.775,116.5+1.45)]
    for p,g in pads:
        if p['ref']=='U2' and p['pin'] in ['1','5','6','10']:
            x,y=p['pos'];expected.append(box(x-.2625,y-.2575,x+.2625,y+.2575))
    assert unary_union(parts).symmetric_difference(unary_union(expected)).area<1e-7
    report['verified_revision_profile']='0.3.2 manufacturer U2 mask dimensions; all copper pads, routing, vias and zone settings unchanged'
near_pad_via=[];near_pad_track=[];near_via_via=[];pad_gaps=[]
minimum={'pad_via_actual':100.,'pad_via_bbox':100.,'different_net_pad_track_bbox':100.,'via_via_all_nets':100.}
for p,g in pads:
    bounds=box(*g.bounds)
    for v,vg in vias:
        # All nets, including same-net vias that would crowd an exposed aperture.
        actual=g.distance(vg);conservative=bounds.distance(vg)
        minimum['pad_via_actual']=min(minimum['pad_via_actual'],actual)
        minimum['pad_via_bbox']=min(minimum['pad_via_bbox'],conservative)
        if conservative<.2-1e-4:
            near_pad_via.append({'pad':label(p),'pad_net':p['net'],'via_net':v['net'],'via_id':v['id'],
                'via_pos':v['pos'],'actual_mm':actual,'bbox_mm':conservative})
    for t,tg in tracks:
        if t['net']==p['net'] or t['layer'] not in p['layers']:continue
        d=bounds.distance(tg);minimum['different_net_pad_track_bbox']=min(minimum['different_net_pad_track_bbox'],d)
        if d<.2-1e-4:near_pad_track.append({'pad':label(p),'track_id':t['id'],'net':t['net'],'bbox_mm':d})
for (a,ag),(b,bg) in itertools.combinations(vias,2):
    d=ag.distance(bg);minimum['via_via_all_nets']=min(minimum['via_via_all_nets'],d)
    if d<.2-1e-4:near_via_via.append({'a':a['id'],'b':b['id'],'nets':[a['net'],b['net']],'mm':d})
for (a,ag),(b,bg) in itertools.combinations(pads,2):
    if a['net']==b['net'] or not set(a['layers'])&set(b['layers']):continue
    d=ag.distance(bg)
    if d<.2-1e-4:pad_gaps.append({'a':label(a),'b':label(b),'same_package':a['ref']==b['ref'],'mm':d})
mask={'F.Mask':[],'B.Mask':[]}
for p,g in pads:
    for l,e in p['mask'].items():mask[l].append(g.buffer(e,quad_segs=32))
for m in data['mask_graphics']:mask[m['layer']].append(geom(m['poly']))
mask_gaps=[]
for layer,polys in mask.items():
    u=unary_union(polys);parts=list(u.geoms) if hasattr(u,'geoms') else [u]
    for a,b in itertools.combinations(parts,2):
        d=a.distance(b)
        if 1e-5<d<.1-1e-4:mask_gaps.append({'layer':layer,'mm':d})
silks=[]
for t in data['silks']:
    g=geom(t['poly']);layer='F.Cu' if t['layer']=='F.Silkscreen' else 'B.Cu';ml='F.Mask' if layer=='F.Cu' else 'B.Mask'
    obstacles=[pg.buffer(max(0,p['mask'].get(ml,0)),quad_segs=32) for p,pg in pads if layer in p['layers']]+mask[ml]
    pd=min(g.distance(o) for o in obstacles)
    hd=min((g.distance(Point(v['pos']).buffer(v['drill']/2,quad_segs=64)) for v,vg in vias),default=100)
    silks.append({'text':t['text'],'pad_mask_clearance_mm':pd,'hole_clearance_mm':hd,'inside_edge_margin_03':box(100.3,100.3,134.7,127.7).covers(g)})
report.update(minimum_clearance_mm=minimum,pad_via_under_020=near_pad_via,pad_track_bbox_under_020=near_pad_track,
    via_via_under_020=near_via_via,fixed_pad_spacing_under_020=pad_gaps,mask_bridge_under_010=mask_gaps,silks=silks,
    pad_invariant_failures=failures)
report['zones']=data.get('zones',[])
package_ok=all(p['same_package'] and p['mm']>=.15-1e-4 for p in pad_gaps)
zone_ok=len(report['zones'])==4 and all(z['net']=='/GND' and z['minimum_width_mm']>=.2 for z in report['zones'])
report['local_gate_passed']=not (near_pad_via or near_pad_track or near_via_via or mask_gaps or failures or report['reserved_ground_plane_signal_segments']) and package_ok and zone_ok and report['minimum_track_width_mm']>=.2-1e-6 and all(s['pad_mask_clearance_mm']>=.2-1e-4 and s['hole_clearance_mm']>=.3-1e-4 and s['inside_edge_margin_03'] for s in silks)
(E/'geometry-checks.json').write_text(json.dumps(report,indent=2)+'\n')
print(json.dumps({k:(len(v) if isinstance(v,list) and k not in ['size_mm','via_sizes_mm','zones'] else v) for k,v in report.items() if k!='scope'},indent=2))
