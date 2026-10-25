#!/usr/bin/env python3
"""Apply a complete return-via plan to its exact native source and refill."""
import hashlib
import json
import argparse
from pathlib import Path
import sys
import pcbnew as k

parser=argparse.ArgumentParser(description=__doc__)
parser.add_argument('trial',type=Path)
parser.add_argument('--allow-partial',action='store_true',help='Apply an incomplete plan as WIP and retain every unresolved return in the report')
args=parser.parse_args()
root=args.trial;pcb=root/'hardware/collar-tracker.kicad_pcb'
plan=json.loads((root/'evidence/return-via-plan.json').read_text())
assert not plan['failed'] or args.allow_partial, 'Incomplete return coverage; use an explicitly partial WIP application'
assert hashlib.sha256(pcb.read_bytes()).hexdigest()==plan['source_sha256'], 'Stale plan'
b=k.LoadBoard(str(pcb))
for x,y in plan['added']:
    v=k.PCB_VIA(b);v.SetPosition(k.VECTOR2I(round(x*1e6),round(y*1e6)))
    v.SetWidth(600000);v.SetDrill(200000);v.SetViaType(k.VIATYPE_THROUGH)
    v.SetLayerPair(k.F_Cu,k.B_Cu);v.SetNet(b.FindNet('/GND'));v.SetLocked(True)
    v.SetFrontTentingMode(k.TENTING_MODE_TENTED);v.SetBackTentingMode(k.TENTING_MODE_TENTED)
    b.Add(v)
k.ZONE_FILLER(b).Fill(b.Zones());assert k.SaveBoard(str(pcb),b)
result=dict(before_sha256=plan['source_sha256'],source_sha256=hashlib.sha256(pcb.read_bytes()).hexdigest(),
            added=len(plan['added']),unresolved=plan['failed'],partial=bool(plan['failed']),
            scope='Applied and refilled; native DRC and actual return coverage still required.')
(root/'evidence/return-vias-applied.json').write_text(json.dumps(result,indent=2)+'\n')
print(json.dumps(result))
