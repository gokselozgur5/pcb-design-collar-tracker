#!/usr/bin/env python3
"""Release only U7's PG entry that encloses its adjacent VIO_ENABLE pad.

This intentionally opens one PG connection for local rerouting. All other native
terminal groups must survive. The published r05f source is never modified.
"""
from pathlib import Path
import hashlib,json
import pcbnew as k
from trim_power_r05_tails import islands

root=Path(__file__).resolve().parents[1];r=root/'experiments/power-r05g-local-crossings'
pcb=r/'hardware/collar-tracker.kicad_pcb';out=r/'evidence/u7-pg-open.json'
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
before_sha=sha(pcb);assert before_sha=='1b2b4bd7b90c3931bd8cbb151637408902332a94260d4a2a820ae6df04838a09'
assert not out.exists()
b=k.LoadBoard(str(pcb));nets={p.GetNetname() for f in b.GetFootprints() for p in f.Pads()}
before=islands(b,nets);items={t.m_Uuid.AsString():t for t in b.GetTracks()}
pad=next(p for f in b.GetFootprints() if f.GetReference()=='U7' for p in f.Pads() if p.GetNumber()=='3')
assert pad.GetNetname()=='/POWER_GOOD';uid=pad.m_Uuid.AsString()
prefixes=['129529ab','2750c920','2a2ef1e5','2ae90b47','2d52436a','6a6cd7f4','8437564e','8f8abdb1','987575a4','a9f58fcd','cfae2d94']
removed=[]
for prefix in prefixes:
 matches=[u for u in items if u.startswith(prefix)];assert len(matches)==1
 t=items[matches[0]];assert t.GetClass()=='PCB_TRACK' and t.GetNetname()=='/POWER_GOOD' and t.GetLayer()==k.B_Cu
 removed.append({'id':matches[0],'start':[t.GetStart().x/1e6,t.GetStart().y/1e6],'end':[t.GetEnd().x/1e6,t.GetEnd().y/1e6],'width_mm':t.GetWidth()/1e6});b.Delete(t)
t=items['c690a142-a55a-4a29-974a-70ac2c76f886']
assert t.GetNetname()=='/POWER_GOOD' and (t.GetStart().x,t.GetStart().y,t.GetEnd().x,t.GetEnd().y)==(117550000,126400000,117550000,123850000)
t.SetEnd(k.VECTOR2I(117550000,125700000))
after=islands(b,nets)
def unaffected(groups):return sorted((n,tuple(x for x in pins if x!=uid)) for n,pins in groups if any(x!=uid for x in pins))
assert unaffected(before)==unaffected(after),'Unrelated native terminal groups changed'
assert ('/POWER_GOOD',(uid,)) in after,'U7 PG entry was not isolated as intended'
assert sum(n=='/POWER_GOOD' for n,_ in before)==1 and sum(n=='/POWER_GOOD' for n,_ in after)==2
k.ZONE_FILLER(b).Fill(b.Zones());assert k.SaveBoard(str(pcb),b)
out.write_text(json.dumps({'before_sha256':before_sha,'source_sha256':sha(pcb),'removed':removed,
 'shortened_track':{'id':t.m_Uuid.AsString(),'old_end_mm':[117.55,123.85],'new_end_mm':[117.55,125.7]},
 'intentionally_isolated_pad':'U7.3','unaffected_terminal_groups_preserved':len(unaffected(before)),
 'scope':'One PG connection deliberately opened for a local crossing repair. Full native DRC and both PG/VIO routing required.'},indent=2)+'\n')
print('Opened only U7.3 PG entry; all other terminal groups preserved')
