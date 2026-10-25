#!/usr/bin/env python3
"""Add two signal layers to an isolated r05f copy without changing outer copper."""
from pathlib import Path
import hashlib
import json
import pcbnew as k
from trim_power_r05_tails import islands

ROOT = Path(__file__).resolve().parents[1]
TRIAL = ROOT / 'experiments/power-r05h-six-layer'
PCB = TRIAL / 'hardware/collar-tracker.kicad_pcb'
before = hashlib.sha256(PCB.read_bytes()).hexdigest()
assert before == '1b2b4bd7b90c3931bd8cbb151637408902332a94260d4a2a820ae6df04838a09'
receipt = TRIAL / 'evidence/six-layer-seed.json'
assert not receipt.exists()
board = k.LoadBoard(str(PCB))
assert board.GetCopperLayerCount() == 4
nets = {p.GetNetname() for f in board.GetFootprints() for p in f.Pads()}
groups = islands(board, nets)
assert all(t.GetClass() == 'PCB_VIA' or t.GetLayer() in [k.F_Cu, k.B_Cu]
           for t in board.GetTracks())
zones = list(board.Zones())
assert len(zones) == 2 and {z.GetLayer() for z in zones} == {k.In1_Cu, k.In2_Cu}
assert all(z.GetNetname() == '/GND' and not z.GetIsRuleArea() for z in zones)
board.SetCopperLayerCount(6)
for z in zones:
    if z.GetLayer() == k.In2_Cu:
        z.SetLayer(k.In4_Cu)
assert board.GetCopperLayerCount() == 6
assert islands(board, nets) == groups
board.GetTitleBlock().SetRevision('0.5h-six-layer-WIP')
k.ZONE_FILLER(board).Fill(board.Zones())
assert k.SaveBoard(str(PCB), board)
receipt.write_text(json.dumps(dict(
    before_sha256=before, source_sha256=hashlib.sha256(PCB.read_bytes()).hexdigest(),
    copper_layers=6, ground_layers=['In1.Cu', 'In4.Cu'],
    signal_layers=['F.Cu', 'In2.Cu', 'In3.Cu', 'B.Cu'],
    terminal_groups_preserved=len(groups),
    scope='Nominal 0.8 mm feasibility layout. Actual supplier dielectric stack, RF impedance and manufacturing acceptance remain open.'
), indent=2) + '\n')
print('Six layers, two dedicated GND planes; all native terminal groups retained')
