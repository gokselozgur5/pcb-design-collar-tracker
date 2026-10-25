#!/usr/bin/env python3
"""Seed legible interface labels; place against actual mask/drill geometry next."""
import hashlib
import json
from pathlib import Path
import sys
import pcbnew as k

trial=Path(sys.argv[1]);pcb=trial/'hardware/collar-tracker.kicad_pcb'
assert 'paul-nanosim' in str(pcb)
b=k.LoadBoard(str(pcb));before=hashlib.sha256(pcb.read_bytes()).hexdigest()
assert not any(d.GetClass()=='PCB_TEXT' and d.GetLayer() in [k.F_SilkS,k.B_SilkS] for d in b.GetDrawings()), 'Labels already exist'
labels=[('5V',101.25,124.4,k.F_SilkS,0),('GND',103.75,124.4,k.F_SilkS,0),
        ('BAT+',103.5,124.4,k.B_SilkS,0),('GND',106,124.4,k.B_SilkS,0),
        ('NTC',108.5,124.4,k.B_SilkS,0),('SWD',104,103.7,k.B_SilkS,0),
        ('SIM',133.4,103.8,k.B_SilkS,90),('EXT',125,122.9,k.B_SilkS,0),
        ('CT 0.4',116,117,k.B_SilkS,0)]
rows=[]
for text,x,y,layer,angle in labels:
    t=k.PCB_TEXT(b);t.SetText(text);t.SetLayer(layer)
    t.SetPosition(k.VECTOR2I(round(x*1e6),round(y*1e6)))
    t.SetTextSize(k.VECTOR2I(950000,950000));t.SetTextThickness(160000)
    t.SetTextAngle(k.EDA_ANGLE(angle,k.DEGREES_T));t.SetMirrored(layer==k.B_SilkS);b.Add(t)
    rows.append(dict(id=t.m_Uuid.AsString(),text=text,position_mm=[x,y],layer=b.GetLayerName(layer)))
assert k.SaveBoard(str(pcb),b)
(trial/'evidence/label-seed.json').write_text(json.dumps(dict(before_sha256=before,
    source_sha256=hashlib.sha256(pcb.read_bytes()).hexdigest(),labels=rows,
    scope='Initial positions only. Run actual glyph/mask/drill placement and review proximity to each connector before export.'),indent=2)+'\n')
print('Seeded',len(rows),'English interface labels')
