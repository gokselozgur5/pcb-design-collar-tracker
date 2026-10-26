#!/usr/bin/env python3
"""Read native pad positions for assembly/pogo review; load once, never save."""
import csv
import hashlib
import json
from pathlib import Path
import pcbnew as k

ROOT = Path(__file__).resolve().parents[1]
SOURCE = ROOT/'experiments/power-r05l-charge-interlock'
OUT = ROOT/'assembly/pcba-r01'


def export():
    pcb = SOURCE/'hardware/collar-tracker.kicad_pcb'
    original = hashlib.sha256(pcb.read_bytes()).hexdigest()
    saved = json.loads((SOURCE/'assembly/assembly-check.json').read_text())
    assert original == saved['source_sha256']
    board = k.LoadBoard(str(pcb))
    origin = board.GetDesignSettings().GetAuxOrigin()
    assert (origin.x, origin.y) == (100000000, 128000000)
    fitted = {p['ref'] for p in csv.DictReader((SOURCE/'hardware/bom.csv').open())
              if p['mpn'] and p['dnp'] == 'False'}
    contacts, pin_one, fitted_pads = [], [], []
    for footprint in sorted(board.GetFootprints(), key=lambda f: f.GetReference()):
        ref = footprint.GetReference()
        for pad in footprint.Pads():
            if ref not in ['J3', 'J4', 'J5', 'J7'] and ref not in fitted:
                continue
            p = pad.GetPosition()
            row = dict(reference=ref, pin=pad.GetNumber(), net=pad.GetNetname(),
                       side='Top' if footprint.GetLayer() == k.F_Cu else 'Bottom',
                       x_mm=round((p.x-origin.x)/1e6, 6), y_mm=round((origin.y-p.y)/1e6, 6),
                       size_x_mm=pad.GetSize().x/1e6, size_y_mm=pad.GetSize().y/1e6,
                       pad_rotation_degrees=pad.GetOrientationDegrees())
            if ref in ['J3', 'J4', 'J5', 'J7']:
                contacts.append(row)
            else:
                fitted_pads.append(row)
                if ref.startswith(('U', 'D', 'Q', 'J')) and pad.GetNumber() == '1':
                    pin_one.append(row)
    assert len(contacts) == 23 and hashlib.sha256(pcb.read_bytes()).hexdigest() == original
    for name, rows in [('interface-pads.csv', contacts), ('pin-one.csv', pin_one),
                       ('fitted-pads.csv', fitted_pads)]:
        with (OUT/name).open('w', newline='') as stream:
            writer = csv.DictWriter(stream, fieldnames=list(rows[0]))
            writer.writeheader(); writer.writerows(rows)
    data = dict(result='PASS', source_sha256=original, kicad_version=k.Version(),
                exporter_sha256=hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
                origin_native_mm=[100,128], interface_pad_count=len(contacts),
                pin_one_land_count=len(pin_one), fitted_pad_count=len(fitted_pads),
                coordinates='Gerber top-view X right/Y up on both sides; bottom is not mirrored',
                scope='Native pad geometry only; fixture contact, polarity/process and component rotation acceptance remain open',
                outputs={name:hashlib.sha256((OUT/name).read_bytes()).hexdigest() for name in ['interface-pads.csv', 'pin-one.csv', 'fitted-pads.csv']})
    (OUT/'contact-export.json').write_text(json.dumps(data, indent=2)+'\n')
    print(json.dumps(data, indent=2))


if __name__ == '__main__':
    export()
