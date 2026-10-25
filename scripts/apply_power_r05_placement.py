#!/usr/bin/env python3
"""Apply the source-bound r05 placement plan; native routing checks follow."""
import hashlib
import json
from pathlib import Path
import shutil
import sys
import pcbnew as k

ROOT = Path(__file__).resolve().parents[1]
TRIAL = ROOT / 'experiments/power-r05-supervised'
PCB = TRIAL / 'hardware/collar-tracker.kicad_pcb'


def main():
    plan = json.loads((TRIAL / 'evidence/placement-plan.json').read_text())
    project = TRIAL / 'hardware/collar-tracker.kicad_pro'
    project_before = json.loads(project.read_text())
    backup = TRIAL / 'build/seed-before-placement.kicad_pcb'
    previous = hashlib.sha256(PCB.read_bytes()).hexdigest()
    if '--replan' in sys.argv:
        old = json.loads((TRIAL / 'evidence/placement-applied.json').read_text())
        assert previous == old['source_sha256'], 'Board advanced since placement; do not overwrite routing'
        before = hashlib.sha256(backup.read_bytes()).hexdigest()
        rejected = TRIAL / 'build/placement-first.kicad_pcb'
        assert not rejected.exists(), 'Preserve previous replan evidence'
        shutil.copy2(PCB, rejected)
        assert before == plan['source_sha256'], 'Stale placement plan'
        # Load at the project path. Loading a bare build/ snapshot substitutes
        # KiCad defaults and can write them back to the real project on SaveBoard.
        shutil.copy2(backup, PCB)
        board = k.LoadBoard(str(PCB))
    else:
        before = previous
        assert not backup.exists(), 'Already applied; preserve work'
        shutil.copy2(PCB, backup)
        board = k.LoadBoard(str(PCB))
    assert before == plan['source_sha256'], 'Stale placement plan'
    fps = {f.GetReference(): f for f in board.GetFootprints()}
    for ref, (x, y, angle, side) in plan['placements'].items():
        f = fps[ref]
        assert f.GetParent() is not None, 'KiCad Flip requires a parent BOARD'
        if f.IsFlipped() != (side == 'B'):
            f.SetLayerAndFlip(k.B_Cu if side == 'B' else k.F_Cu)
        f.SetOrientationDegrees(angle)
        f.SetPosition(k.VECTOR2I(round(x * 1e6), round(y * 1e6)))
    title = board.GetTitleBlock()
    title.SetRevision('0.5-power-WIP')
    board.SetTitleBlock(title)
    board.BuildConnectivity()
    k.ZONE_FILLER(board).Fill(board.Zones())
    assert k.SaveBoard(str(PCB), board)
    project_after = json.loads(project.read_text())
    assert project_before['board']['design_settings'] == project_after['board']['design_settings']
    assert project_before['net_settings'] == project_after['net_settings']
    placement = {f.GetReference(): [f.GetPosition().x / 1e6, f.GetPosition().y / 1e6,
                                    f.GetOrientationDegrees(), 'B' if f.IsFlipped() else 'F']
                 for f in board.GetFootprints()}
    (TRIAL / 'build/placement.json').write_text(json.dumps(placement, indent=2) + '\n')
    extra = {'bounds': [98, 98, 138, 130], 'footprints': {}, 'keepouts': []}
    for f in board.GetFootprints():
        extra['footprints'][f.GetReference()] = {'pos': placement[f.GetReference()][:2],
                                                'side': board.GetLayerName(f.GetLayer())}
        for z in f.Zones():
            if z.GetIsRuleArea():
                p = z.Outline()
                extra['keepouts'].append({'ref': f.GetReference(), 'layer': board.GetLayerName(z.GetLayer()),
                    'tracks': z.GetDoNotAllowTracks(), 'vias': z.GetDoNotAllowVias(),
                    'poly': [[[p.COutline(n).CPoint(i).x / 1e6, p.COutline(n).CPoint(i).y / 1e6]
                              for i in range(p.COutline(n).PointCount())] for n in range(p.OutlineCount())]})
    (TRIAL / 'evidence/placement-extra.json').write_text(json.dumps(extra, indent=2) + '\n')
    (TRIAL / 'evidence/placement-applied.json').write_text(json.dumps({
        'before_sha256': before, 'source_sha256': hashlib.sha256(PCB.read_bytes()).hexdigest(),
        'changed_parts': sorted(plan['placements']), 'native_checks': 'PENDING',
        'scope': 'Component placement only; ground fanout and routing still incomplete.'
    }, indent=2) + '\n')
    if 'ground_stubs' in plan:
        ground_plan = {
            'source_sha256': hashlib.sha256(PCB.read_bytes()).hexdigest(),
            'incremental': True, 'existing_ground_vias': sum(
                t.GetClass() == 'PCB_VIA' and t.GetNetname() == '/GND' for t in board.GetTracks()),
            'ground_pads': len(plan['ground_stubs']), 'stubs': plan['ground_stubs'],
            'vias': plan['ground_vias'], 'failures': [],
            'scope': 'Ground reservations from placement; native DRC and actual pad-to-plane connectivity pending.'}
        (TRIAL / 'evidence/ground-plan.json').write_text(json.dumps(ground_plan, indent=2) + '\n')
    print('Applied', len(plan['placements']), 'placements to 40 x 32 mm candidate')


if __name__ == '__main__':
    main()
