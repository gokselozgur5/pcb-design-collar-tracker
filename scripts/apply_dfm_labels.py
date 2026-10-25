#!/usr/bin/env python3
"""Apply the measured silkscreen positions to the current PCB."""
from pathlib import Path
import json
import pcbnew as k
ROOT=Path(__file__).resolve().parents[1];P=ROOT/'hardware/collar-tracker.kicad_pcb'
b=k.LoadBoard(str(P));by_id={g.m_Uuid.AsString():g for g in b.GetDrawings()}
positions=json.loads((ROOT/'evidence/jlc-dfm-20261024/silk-placement.json').read_text())
for item in positions:
    g=by_id[item['id']];assert g.GetText()==item['text']
    g.SetPosition(k.VECTOR2I_MM(*item['to']))
assert k.SaveBoard(str(P),b)
print('Applied',len(positions),'measured legend positions.')
