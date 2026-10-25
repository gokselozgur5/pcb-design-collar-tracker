#!/usr/bin/env python3
"""Verify the one-route repair using the actual supplier warning segment.
Run with .venv-dfm/bin/python. A before/after failure distinguishes the fix.
"""
from pathlib import Path
import hashlib,json,re,zipfile
from shapely.geometry import LineString
R=Path(__file__).resolve().parents[1]
A=R/'experiments/35x28-clearance-r033';B=R/'experiments/35x28-clearance-r034';E=B/'evidence'
old=json.loads((A/'evidence/geometry.json').read_text());new=json.loads((E/'geometry.json').read_text())
for key in ['pads','vias','mask_graphics','zones']:assert old[key]==new[key],key
ot={t['id']:t for t in old['tracks']};nt={t['id']:t for t in new['tracks']}
assert set(ot)==set(nt)
changed=[i for i in ot if ot[i]!=nt[i]]
assert changed==['518a7bbe-4d4f-476f-95b5-f3a983aa1dff']
uid=changed[0];before=ot[uid];after=nt[uid]
assert before['net']==after['net']=='/GND' and before['width']==.2 and after['width']==.3
assert {k:v for k,v in before.items() if k!='width'}=={k:v for k,v in after.items() if k!='width'}
finding=json.loads((R/'evidence/zero-warning-r033/repro033-finalname/remaining.json').read_text())
assert len(finding)==1 and finding[0]['category']=='coverage'
span=LineString(finding[0]['native_xy'])
def metal(t):return LineString([t['start'],t['end']]).buffer(t['width']/2,quad_segs=96)
old_gap=span.difference(metal(before)).length
new_gap=span.difference(metal(after)).length
assert old_gap>.08 and new_gap<.000001,(old_gap,new_gap)
# Existing mask/stencil/holes and three other copper layers must be identical.
g0=A/'evidence/iteration1-gerbers';g1=E/'gerbers'
def normalized(p):
 return '\n'.join(l for l in p.read_text().splitlines() if not l.startswith(('%TF.CreationDate,','%TF.ProjectId,','G04 Created by KiCad','; DRILL file','; #@! TF.CreationDate,')))
unchanged=[]
for ext in ['g1','g2','gbl','gts','gbs','gtp','gbp','gm1','gto']:
 a=next(g0.glob('*.'+ext));b=next(g1.glob('*.'+ext))
 assert normalized(a)==normalized(b),ext
 unchanged.append(b.name)
for name in ['collar-tracker-PTH.drl','collar-tracker-NPTH.drl']:
 assert normalized(g0/name)==normalized(g1/name);unchanged.append(name)
for name in ['collar-tracker.kicad_pro','collar-tracker.kicad_dru','collar-tracker.kicad_sch']:
 assert (A/'hardware'/name).read_bytes()==(B/'hardware'/name).read_bytes(),name
ds=json.loads((E/'drc.json').read_text())
assert not any(ds[k] for k in ['violations','unconnected_items','schematic_parity'])
source=json.loads((E/'export-source.json').read_text());sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
assert sha(B/'hardware/collar-tracker.kicad_pcb')==source['pcb_sha256']
assert sha(Path(source['zip']))==source['zip_sha256']
with zipfile.ZipFile(source['zip']) as z:
 assert z.testzip() is None
 for name in z.namelist():assert z.read(name)==(g1/name).read_bytes()
result={'verified':True,'source_sha256':source['pcb_sha256'],'zip_sha256':source['zip_sha256'],
 'changed_track':uid,'supplier_warning_segment_mm':finding[0]['native_xy'],
 'segment_outside_ground_trace_before_mm':old_gap,'segment_outside_ground_trace_after_mm':new_gap,
 'pads_masks_stencil_components_vias_nets_rules_unchanged':True,'native_errors':0,'native_warnings':0,'opens':0,'parity':0,
 'unchanged_output_files_except_timestamps_revision':unchanged,
 'copper_layers_changed':['F.Cu'],'limitation':'Local geometry plus native DRC; supplier repeat checks are separate.'}
(E/'local-checks.json').write_text(json.dumps(result,indent=2)+'\n');print(json.dumps(result,indent=2))
