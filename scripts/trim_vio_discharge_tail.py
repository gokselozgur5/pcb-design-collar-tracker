#!/usr/bin/env python3
"""Trim only the unused end beyond the live Q1 drain branch in r05f."""
from pathlib import Path
import hashlib,json
import pcbnew as k
from trim_power_r05_tails import islands

r=Path(__file__).resolve().parents[1]/'experiments/power-r05f-return-reset'
p=r/'hardware/collar-tracker.kicad_pcb';receipt=r/'evidence/discharge-tail.json'
assert not receipt.exists()
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
before_sha=sha(p);assert json.loads((r/'evidence/tails1.json').read_text())['source_sha256']==before_sha
b=k.LoadBoard(str(p));nets={p.GetNetname() for f in b.GetFootprints() for p in f.Pads()};before=islands(b,nets)
t=next(t for t in b.GetTracks() if t.m_Uuid.AsString()=='00881e28-f3bd-46ed-a7e8-348a586f3ec6')
assert t.GetClass()=='PCB_TRACK' and t.GetNetname()=='/VIO_DISCHARGE' and t.GetLayer()==k.F_Cu and t.GetWidth()==200000
assert (t.GetStart().x,t.GetStart().y,t.GetEnd().x,t.GetEnd().y)==(133350000,120412500,133350000,118000000)
t.SetEnd(k.VECTOR2I(133350000,118650000))
assert islands(b,nets)==before,'Trimming the loose end changed a live terminal group'
k.ZONE_FILLER(b).Fill(b.Zones());assert k.SaveBoard(str(p),b)
receipt.write_text(json.dumps({'before_sha256':before_sha,'source_sha256':sha(p),'track_id':t.m_Uuid.AsString(),
 'old_end_mm':[133.35,118],'new_end_mm':[133.35,118.65],'removed_length_mm':.65,
 'native_terminal_groups_preserved':len(before),
 'scope':'Only the straight unused tail was shortened; new copper is a subset of the original. Fresh native DRC required.'},indent=2)+'\n')
print('Trimmed 0.65 mm beyond the live branch; terminal groups preserved')
