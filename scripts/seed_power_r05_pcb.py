#!/usr/bin/env python3
"""Seed an r05 placement experiment from the immutable r04i PCB.

Run with KiCad Python. Remove affected power routing explicitly; do not retain
old copper on a renamed pad. New parts initially sit outside the outline for
the copper-aware placement planner. This is not a routed or released board.
"""
import csv
import hashlib
import json
import math
import os
from pathlib import Path
import pcbnew as k
import build_power_r05 as schematic
import build_draft as symbols

ROOT = Path(__file__).resolve().parents[1]
TRIAL = ROOT / 'experiments/power-r05-supervised'
HW = TRIAL / 'hardware'
SOURCE = ROOT / 'experiments/paul-nanosim-r04i-sim-access-40x32/hardware/collar-tracker.kicad_pcb'
BASE_SHA = 'f4be0288708733aaa6092a703ffa1bfebb3dc059fd21112a8cfed94028acc3b0'
OUTPUT = HW / 'collar-tracker.kicad_pcb'


def xy(v):
    return [v.x / 1e6, v.y / 1e6]


def vec(p):
    return k.VECTOR2I(*(round(v * 1e6) for v in p))


def polys(poly):
    return [[xy(poly.COutline(n).CPoint(i)) for i in range(poly.COutline(n).PointCount())]
            for n in range(poly.OutlineCount())]


def export_placement(board, changed, output=OUTPUT, trial=TRIAL):
    out = {'bounds_mm': [98, 98, 138, 130], 'footprints': {}, 'tracks': [], 'vias': []}
    for f in board.GetFootprints():
        f.BuildCourtyardCaches()
        outlines = polys(f.GetCourtyard(f.GetLayer()))
        pads = []
        for pad in f.Pads():
            if not pad.IsOnCopperLayer():
                continue
            pads.append({'pin': pad.GetNumber(), 'net': pad.GetNetname(),
                         'poly': polys(pad.GetEffectivePolygon(f.GetLayer()))})
        out['footprints'][f.GetReference()] = {
            'pos': xy(f.GetPosition()), 'angle': f.GetOrientationDegrees(),
            'side': 'B' if f.IsFlipped() else 'F', 'courtyards': outlines,
            'pads': pads, 'movable': f.GetReference() in changed}
    for track in board.GetTracks():
        if track.GetClass() == 'PCB_VIA':
            out['vias'].append({'pos': xy(track.GetPosition()),
                                'diameter': track.GetWidth(k.F_Cu) / 1e6, 'net': track.GetNetname()})
        else:
            out['tracks'].append({'start': xy(track.GetStart()), 'end': xy(track.GetEnd()),
                                  'width': track.GetWidth() / 1e6,
                                  'side': 'F' if track.GetLayer() == k.F_Cu else 'B',
                                  'net': track.GetNetname()})
    out['source_sha256'] = hashlib.sha256(output.read_bytes()).hexdigest()
    (trial / 'evidence/placement-input.json').write_text(json.dumps(out, indent=2) + '\n')


def main():
    assert hashlib.sha256(SOURCE.read_bytes()).hexdigest() == BASE_SHA
    assert not OUTPUT.exists(), 'Preserve existing work; this seed runs once'
    design = json.loads((HW / 'design.json').read_text())
    parts = {p['ref']: p for p in design['parts'] if not p['ref'].startswith('#')}
    inv = json.loads((TRIAL / 'evidence/native-netlist.json').read_text())
    nets = {pin: name for name, pins in inv['nets'].items() for pin in pins}
    board = k.LoadBoard(str(SOURCE))
    fps = {f.GetReference(): f for f in board.GetFootprints()}
    changed = (set(parts) - set(fps)) | {'C9'}
    removed_tracks = []
    reroute_nets = {'/VBAT', '/VSYS', '/VDD_NRF', '/NRF_ENABLE', '/BAT_ADC'}
    removed_ground_pads = [pad for ref in ['R11', 'C22', 'C9'] for pad in fps[ref].Pads()
                           if pad.GetNetname() == '/GND']
    for track in list(board.GetTracks()):
        remove = track.GetNetname() in reroute_nets
        if track.GetClass() == 'PCB_TRACK' and track.GetNetname() == '/GND':
            # Remove only the old local attachment segments; planes/vias and
            # every other ground connection are preserved for native review.
            remove = any(pad.HitTest(track.GetStart()) or pad.HitTest(track.GetEnd())
                         for pad in removed_ground_pads)
        if remove:
            removed_tracks.append({'uuid': track.m_Uuid.AsString(), 'net': track.GetNetname()})
            board.Delete(track)
    for ref in (set(fps) - set(parts)) | {'C9'}:
        board.Delete(fps.pop(ref))
    io = k.PCB_IO_KICAD_SEXPR()
    fp_changes = {}
    for index, ref in enumerate(sorted(changed)):
        part = parts[ref]
        lib, name = part['footprint'].split(':', 1)
        folder = HW / (lib + '.pretty') if lib.startswith('Collar') else (
            Path(os.environ['KICAD10_FOOTPRINT_DIR']) / (lib + '.pretty'))
        f = io.FootprintLoad(str(folder), name)
        assert f is not None, part['footprint']
        local_name = ref + '_' + name
        local_id = 'Collar05:' + local_name
        f.SetFPIDAsString(local_id)
        for g in list(f.GraphicalItems()):
            if g.GetLayer() == k.F_SilkS:
                g.SetLayer(k.F_Fab)
        f.Reference().SetVisible(False)
        f.Value().SetVisible(False)
        f.SetReference('REF**')
        io.FootprintSave(str(HW / 'Collar05.pretty'), f)
        f.SetReference(ref)
        f.SetValue(part['value'])
        f.SetPath(k.KIID_PATH('/' + design['root_uuid'] + '/' + symbols.uid(ref)))
        f.SetPosition(vec([150 + 5 * (index % 5), 100 + 5 * (index // 5)]))
        board.Add(f)
        fps[ref] = f
        fp_changes[ref] = {'before': part['footprint'], 'after': local_id}
        part['footprint'] = local_id
    for ref, f in fps.items():
        part = parts[ref]
        f.SetValue(part['value'])
        f.SetField('MPN', part['mpn'])
        f.GetField('MPN').SetVisible(False)
        f.SetField('Design status', part['status'])
        f.GetField('Design status').SetVisible(False)
        for pad in f.Pads():
            if not pad.IsOnCopperLayer() or not pad.GetNumber():
                continue
            net_name = nets.get(ref + '.' + pad.GetNumber())
            assert net_name, (ref, pad.GetNumber())
            net = board.FindNet(net_name)
            if net is None or net.GetNetCode() < 0:
                net = k.NETINFO_ITEM(board, net_name)
                board.Add(net)
            pad.SetNet(net)
    native = schematic.parse((HW / 'collar-tracker.kicad_sch').read_text())
    for inst in native:
        if not isinstance(inst, list) or inst[0] != 'symbol' or not schematic.child(inst, 'lib_id'):
            continue
        props = {str(x[1]): x for x in inst if isinstance(x, list) and x[0] == 'property'}
        ref = str(props['Reference'][2])
        if ref in fp_changes:
            props['Footprint'][2] = schematic.Quoted(fp_changes[ref]['after'])
    (HW / 'collar-tracker.kicad_sch').write_text(schematic.emit(native) + '\n')
    (HW / 'design.json').write_text(json.dumps(design, indent=2) + '\n')
    # Keep the assembly inventory aligned with the local footprint identifiers.
    with (HW / 'bom.csv').open('w', newline='') as handle:
        fields = ['ref', 'value', 'mpn', 'footprint', 'dnp', 'onboard', 'status']
        writer = csv.DictWriter(handle, fieldnames=fields, lineterminator='\n')
        writer.writeheader()
        writer.writerows({key: part[key] for key in fields} for part in parts.values())
    for item in board.GetDrawings():
        if item.GetClass() == 'PCB_TEXT':
            item.SetText(item.GetText().replace('r04i', 'r05'))
    board.GetTitleBlock().SetRevision('0.5-power-WIP')
    board.BuildConnectivity()
    assert k.SaveBoard(str(OUTPUT), board)
    (TRIAL / 'build').mkdir(exist_ok=True)
    (TRIAL / 'evidence/pcb-seed.json').write_text(json.dumps({
        'baseline_pcb_sha256': BASE_SHA, 'source_sha256': hashlib.sha256(OUTPUT.read_bytes()).hexdigest(),
        'footprint_changes': fp_changes, 'removed_tracks': removed_tracks,
        'changed_parts': sorted(changed), 'scope': 'Unplaced, unrouted candidate. No PCB DRC/DFM acceptance.'
    }, indent=2) + '\n')
    export_placement(board, changed)
    print(json.dumps({'parts': len(fps), 'changed_parts': len(changed),
                      'removed_track_items': len(removed_tracks), 'placement': 'PENDING'}))


if __name__ == '__main__':
    main()
