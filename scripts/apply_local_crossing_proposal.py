#!/usr/bin/env python3
"""Apply a source-bound WIP crossing proposal, retaining all unrelated terminals."""
import argparse
import hashlib
import json
from pathlib import Path

import pcbnew as k
from trim_power_r05_tails import islands


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('trial', type=Path)
    args = parser.parse_args()
    trial = args.trial.resolve()
    assert trial.name == 'power-r05g-local-crossings'
    pcb = trial / 'hardware/collar-tracker.kicad_pcb'
    plan_path = trial / 'evidence/local-crossing-plan.json'
    receipt = trial / 'evidence/local-crossing-applied.json'
    assert not receipt.exists(), 'Do not apply a crossing plan twice'
    plan = json.loads(plan_path.read_text())
    before = hashlib.sha256(pcb.read_bytes()).hexdigest()
    assert plan['before_sha256'] == before
    assert plan['net'] == '/VIO_ENABLE'
    allowed = {'/HEALTH_EN', '/CHG_STAT', '/CHG_FAULT', '/VIO_ENABLE'}
    assert set(plan['allowed_changed_nets']) == allowed
    board = k.LoadBoard(str(pcb))
    nets = {p.GetNetname() for f in board.GetFootprints() for p in f.Pads()}
    protected_before = islands(board, nets - allowed)
    affected_before = islands(board, allowed)
    layers = {'F.Cu': k.F_Cu, 'B.Cu': k.B_Cu}
    by_id = {t.m_Uuid.AsString(): t for t in board.GetTracks()}
    created = []

    def vec(p):
        return k.VECTOR2I(round(p[0] * 1e6), round(p[1] * 1e6))

    def track(a, z, layer, net):
        assert a != z
        t = k.PCB_TRACK(board)
        t.SetStart(vec(a)); t.SetEnd(vec(z)); t.SetLayer(layer)
        t.SetWidth(k.FromMM(.2)); t.SetNet(board.FindNet(net))
        t.SetLocked(True); board.Add(t)
        created.append(t.m_Uuid.AsString())

    for cut in plan['cuts']:
        old = by_id[cut['id']]
        assert old.GetClass() == 'PCB_TRACK'
        assert old.GetNetname() == cut['net'] in allowed - {plan['net']}
        assert old.GetWidth() == k.FromMM(.2)
        assert old.GetLayer() == layers[cut['layer']]
        assert old.GetStart() == vec(cut['start']) and old.GetEnd() == vec(cut['end'])
        board.Delete(old)
        for piece in cut['pieces']:
            assert len(piece) == 2
            track(piece[0], piece[1], layers[cut['layer']], cut['net'])
    added_vias = []
    for a, z in zip(plan['points'], plan['points'][1:]):
        assert a[2] in (0, 1) and z[2] in (0, 1)
        if a[2] == z[2]:
            track(a[:2], z[:2], [k.F_Cu, k.B_Cu][a[2]], plan['net'])
        else:
            assert a[:2] == z[:2]
            v = k.PCB_VIA(board)
            v.SetPosition(vec(a)); v.SetWidth(k.FromMM(.6)); v.SetDrill(k.FromMM(.2))
            v.SetViaType(k.VIATYPE_THROUGH); v.SetLayerPair(k.F_Cu, k.B_Cu)
            v.SetNet(board.FindNet(plan['net']))
            v.SetFrontTentingMode(k.TENTING_MODE_TENTED)
            v.SetBackTentingMode(k.TENTING_MODE_TENTED)
            board.Add(v); added_vias.append(v.m_Uuid.AsString())
    assert islands(board, nets - allowed) == protected_before
    affected_after = islands(board, allowed)
    k.ZONE_FILLER(board).Fill(board.Zones())
    backup = trial / 'build/before-local-crossing.kicad_pcb'
    assert not backup.exists()
    backup.write_bytes(pcb.read_bytes())
    assert k.SaveBoard(str(pcb), board)
    receipt.write_text(json.dumps(dict(
        before_sha256=before, source_sha256=hashlib.sha256(pcb.read_bytes()).hexdigest(),
        plan_sha256=hashlib.sha256(plan_path.read_bytes()).hexdigest(),
        protected_terminal_groups=len(protected_before),
        affected_groups_before=affected_before, affected_groups_after=affected_after,
        new_tracks=created, new_vias=added_vias,
        scope='WIP only. Full native checks and repair of intentionally opened nets are required.'
    ), indent=2) + '\n')
    print('Applied source-bound crossing; protected terminal groups unchanged')


if __name__ == '__main__':
    main()
