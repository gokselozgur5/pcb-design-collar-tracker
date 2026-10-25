#!/usr/bin/env python3
"""Apply a source-bound r05b full-pin placement; native DRC is the next gate."""
import hashlib
import json
from pathlib import Path
import pcbnew as k

ROOT = Path(__file__).resolve().parents[1]
TRIAL = ROOT / 'experiments/power-r05b-pin-exits'
PCB = TRIAL / 'hardware/collar-tracker.kicad_pcb'


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def main():
    plan_path = TRIAL / 'evidence/placement-plan.json'
    plan = json.loads(plan_path.read_text())
    assert plan['complete'] and len(plan['placements']) == 20
    assert sha(PCB) == plan['source_sha256'], 'Preserve existing placement/routing'
    project = PCB.with_suffix('.kicad_pro')
    before_project = json.loads(project.read_text())
    board = k.LoadBoard(str(PCB))
    fps = {f.GetReference(): f for f in board.GetFootprints()}
    vector = lambda xy: k.VECTOR2I(*(round(v * 1e6) for v in xy))
    for ref, (x, y, angle, side) in plan['placements'].items():
        f = fps[ref]
        if f.IsFlipped() != (side == 'B'):
            f.SetLayerAndFlip(k.B_Cu if side == 'B' else k.F_Cu)
        f.SetOrientationDegrees(angle)
        f.SetPosition(vector([x, y]))
    for stub in plan['stubs']:
        net = board.FindNet(stub['net'])
        assert net is not None and net.GetNetCode() > 0
        for start, end in zip(stub['points'], stub['points'][1:]):
            if start == end:
                continue
            track = k.PCB_TRACK(board)
            track.SetStart(vector(start))
            track.SetEnd(vector(end))
            track.SetWidth(round(stub['width'] * 1e6))
            track.SetLayer(board.GetLayerID(stub['layer']))
            track.SetNet(net)
            track.SetLocked(True)
            board.Add(track)
    existing = {(v.GetPosition().x, v.GetPosition().y) for v in board.GetTracks() if v.GetClass() == 'PCB_VIA'}
    for via in plan['vias']:
        pos = vector(via['pos'])
        assert (pos.x, pos.y) not in existing, 'Duplicate via proposal'
        existing.add((pos.x, pos.y))
        track = k.PCB_VIA(board)
        track.SetPosition(pos)
        track.SetWidth(600000)
        track.SetDrill(200000)
        track.SetViaType(k.VIATYPE_THROUGH)
        track.SetLayerPair(k.F_Cu, k.B_Cu)
        track.SetFrontTentingMode(k.TENTING_MODE_TENTED)
        track.SetBackTentingMode(k.TENTING_MODE_TENTED)
        track.SetNet(board.FindNet(via['net']))
        track.SetLocked(True)
        board.Add(track)
    board.BuildConnectivity()
    k.ZONE_FILLER(board).Fill(board.Zones())
    assert k.SaveBoard(str(PCB), board)
    after_project = json.loads(project.read_text())
    assert before_project['board']['design_settings'] == after_project['board']['design_settings']
    assert before_project['net_settings'] == after_project['net_settings']
    placement = {f.GetReference(): [f.GetPosition().x / 1e6, f.GetPosition().y / 1e6,
                                  f.GetOrientationDegrees(), 'B' if f.IsFlipped() else 'F']
                 for f in board.GetFootprints()}
    (TRIAL / 'build/placement.json').write_text(json.dumps(placement, indent=2) + '\n')
    (TRIAL / 'evidence/protected-pin-exits.json').write_text(json.dumps(
        sorted(t.m_Uuid.AsString() for t in board.GetTracks()), indent=2) + '\n')
    (TRIAL / 'evidence/placement-apply.json').write_text(json.dumps({
        'before_sha256': plan['source_sha256'], 'source_sha256': sha(PCB),
        'plan_sha256': sha(plan_path), 'changed_footprints': len(plan['placements']),
        'reserved_pin_exits': len(plan['stubs']), 'added_vias': len(plan['vias']),
        'scope': 'Applied placement and pin exits. Native DRC, routing and physical acceptance pending.'}, indent=2) + '\n')
    print(json.dumps({'source_sha256': sha(PCB), 'pin_exits': len(plan['stubs']), 'added_vias': len(plan['vias'])}))


if __name__ == '__main__':
    main()
