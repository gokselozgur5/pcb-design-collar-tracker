#!/usr/bin/env python3
"""Apply the source-bound r05f ENABLE capacitor placement; rerun native DRC afterward."""
from pathlib import Path
import sys,json,hashlib,shutil
sys.path.insert(0,str(Path('scripts').resolve()))
import pcbnew as k
from trim_power_r05_tails import islands
r=Path('experiments/power-r05f-return-reset');p=r/'hardware/collar-tracker.kicad_pcb'
plan=json.loads((r/'evidence/c9-placement-plan.json').read_text())
assert hashlib.sha256(p.read_bytes()).hexdigest()==plan['source_sha256']
b=k.LoadBoard(str(p));f=next(f for f in b.GetFootprints() if f.GetReference()=='C9')
nets={p.GetNetname() for f in b.GetFootprints() for p in f.Pads()};before=islands(b,nets)
ids={t.m_Uuid.AsString():t for t in b.GetTracks()}
assert all(uid in ids for uid in plan['remove_ids'])
shutil.copy2(p,r/'build/before-c9.kicad_pcb')
for uid in plan['remove_ids']:b.Delete(ids[uid])
vector=lambda p:k.VECTOR2I(*(round(v*1e6) for v in p))
f.SetPosition(vector(plan['position']));f.SetOrientationDegrees(plan['native_angle'])
for pad in f.Pads():
 expected=plan['pads'][pad.GetNetname()];actual=pad.GetPosition()
 assert abs(actual.x/1e6-expected[0])<1e-5 and abs(actual.y/1e6-expected[1])<1e-5
ground=next(pad for pad in f.Pads() if pad.GetNetname()=='/GND')
t=k.PCB_TRACK(b);t.SetStart(ground.GetPosition());t.SetEnd(vector(plan['ground_target']))
t.SetLayer(k.B_Cu);t.SetWidth(200000);t.SetNet(ground.GetNet());b.Add(t)
after=islands(b,nets)
# C9 moves from the R7 local ground via to the C3 local ground via.
# All other native terminal groups must be identical; C9 must reach the selected via.
uid=ground.m_Uuid.AsString()
def unchanged(groups):
 return sorted((net,tuple(x for x in group if x!=uid)) for net,group in groups if any(x!=uid for x in group))
assert unchanged(before)==unchanged(after),'Relocation changed unrelated native terminal groups'
cn=b.GetConnectivity();todo=[ground];seen=set()
while todo:
 current=todo.pop();ident=current.m_Uuid.AsString()
 if ident in seen:continue
 seen.add(ident);todo.extend(q for q in cn.GetConnectedTracks(current) if q.GetNetname()=='/GND')
assert plan['ground_via_id'] in seen,'C9 lacks its local ground via'
k.ZONE_FILLER(b).Fill(b.Zones());assert k.SaveBoard(str(p),b)
(r/'evidence/c9-relocated.json').write_text(json.dumps({'before_sha256':plan['source_sha256'],'source_sha256':hashlib.sha256(p.read_bytes()).hexdigest(),'plan_sha256':hashlib.sha256((r/'evidence/c9-placement-plan.json').read_bytes()).hexdigest(),'unchanged_terminal_groups_preserved':len(unchanged(before)),'relocated_ground_terminal':'C9.2','new_local_ground_via':plan['ground_via_id'],'ground_track_id':t.m_Uuid.AsString(),'scope':'Placement and local ground applied. Full native DRC and ENABLE completion remain required.'},indent=2)+'\n')
print('C9 relocated; all unrelated terminal groups preserved and local ground via reached')
