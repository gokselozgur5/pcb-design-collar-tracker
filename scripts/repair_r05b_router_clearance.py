#!/usr/bin/env python3
"""Move one imported CT detour away from a fixed rail via; rules stay unchanged."""
from pathlib import Path
import hashlib
import json
import shutil
import pcbnew as k

ROOT = Path(__file__).resolve().parents[1]
TRIAL = ROOT / 'experiments/power-r05b-pin-exits'
PCB = TRIAL / 'hardware/collar-tracker.kicad_pcb'
before = hashlib.sha256(PCB.read_bytes()).hexdigest()
assert before == '70ef470237e845686e4c45fc96def3b5cabb7e5d46d8611722d58122131aae53'
shutil.copy2(PCB, TRIAL / 'build/route1-before-clearance.kicad_pcb')
protected = set(json.loads((TRIAL / 'evidence/protected-pin-exits.json').read_text()))
project = json.loads(PCB.with_suffix('.kicad_pro').read_text())
board = k.LoadBoard(str(PCB))
changes = []
for t in board.GetTracks():
    if t.GetClass() != 'PCB_TRACK' or t.GetNetname() != '/UV_DELAY':
        continue
    for getter, setter, name in ((t.GetStart, t.SetStart, 'start'), (t.GetEnd, t.SetEnd, 'end')):
        pos = getter()
        if pos.y != 128540600:
            continue
        assert t.m_Uuid.AsString() not in protected and t.GetLayer() == k.B_Cu
        changes.append({'id': t.m_Uuid.AsString(), 'endpoint': name,
                        'before_mm': [pos.x / 1e6, pos.y / 1e6],
                        'after_mm': [pos.x / 1e6, 128.5706]})
        setter(k.VECTOR2I(pos.x, 128570600))
assert len(changes) == 6, changes
board.BuildConnectivity()
k.ZONE_FILLER(board).Fill(board.Zones())
assert k.SaveBoard(str(PCB), board)
after_project = json.loads(PCB.with_suffix('.kicad_pro').read_text())
assert project['board']['design_settings'] == after_project['board']['design_settings']
assert project['net_settings'] == after_project['net_settings']
result = {'before_sha256': before, 'source_sha256': hashlib.sha256(PCB.read_bytes()).hexdigest(),
          'changes': changes, 'reason': 'Imported 0.2 mm CT branch had 0.1906 mm clearance to a fixed via. Move the horizontal chain by 0.03 mm.',
          'acceptance': 'Pending native DRC and unchanged open-count verification'}
(TRIAL / 'evidence/router-clearance-repair.json').write_text(json.dumps(result, indent=2) + '\n')
print(json.dumps(result))
