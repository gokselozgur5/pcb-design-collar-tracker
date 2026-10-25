#!/usr/bin/env python3
"""Apply inspected manufacturer land drawings to the isolated r05b candidate."""
import hashlib
import json
from pathlib import Path
import shutil
import pcbnew as k

ROOT = Path(__file__).resolve().parents[1]
TRIAL = ROOT / 'experiments/power-r05b-pin-exits'
PCB = TRIAL / 'hardware/collar-tracker.kicad_pcb'
EXPECTED = 'e631887fb896243b69523c90e0ed8fb224a3ac989362a5d56dc10bf93620f94f'
SPECS = {
    'U6': {'row': 1.3, 'pitch': 0.95, 'size': [1.1, 0.6], 'radius': 0.05,
           'courtyard_x': 2.1, 'source': 'TI DBV0006A, 4214840/G 08/2024',
           'pdf': 'tps3808.pdf', 'page': 37,
           'url': 'https://www.ti.com/lit/ds/symlink/tps3808.pdf'},
    'U8': {'row': 1.1, 'pitch': 0.65, 'size': [0.95, 0.4], 'radius': 0.05,
           'courtyard_x': 1.825, 'source': 'TI DCK0005A, 4214834/G 11/2024',
           'pdf': 'sn74lvc1g14.pdf', 'page': 34,
           'url': 'https://www.ti.com/lit/ds/symlink/sn74lvc1g14.pdf'},
    'Q1': {'row': 0.95, 'pitch': 0.65, 'size': [0.6, 0.42], 'radius': 0,
           'courtyard_x': None, 'source': 'Diodes DS44897 Rev. 1-2, September 2023',
           'pdf': 'dmn62d2udw-direct.pdf', 'page': 7,
           'url': 'https://www.diodes.com/datasheet/download/DMN62D2UDW.pdf'},
}
SPECS['U7'] = dict(SPECS['U6'])


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def vector(xy):
    return k.VECTOR2I(*(round(v * 1e6) for v in xy))


def refine(f, spec):
    """Edit an owned, front-side, zero-rotation footprint at the origin."""
    assert f.GetParent() is not None and not f.IsFlipped()
    before = []
    for p in f.Pads():
        pin = int(p.GetNumber())
        old = p.GetPosition()
        before.append({'pin': pin, 'xy': [old.x / 1e6, old.y / 1e6],
                       'size': [p.GetSize().x / 1e6, p.GetSize().y / 1e6]})
        y_index = {1: -1, 2: 0, 3: 1, 4: 1, 5: 0, 6: -1}
        # Five-pin SC70 omits the right-hand middle lead.
        y_index[5] = -1 if f.GetReference() == 'U8' else 0
        p.SetPosition(vector([(-1 if pin <= 3 else 1) * spec['row'], y_index[pin] * spec['pitch']]))
        p.SetSize(vector(spec['size']))
        p.SetShape(k.PAD_SHAPE_ROUNDRECT if spec['radius'] else k.PAD_SHAPE_RECT)
        if spec['radius']:
            p.SetRoundRectRadiusRatio(spec['radius'] / min(spec['size']))
        # Preserve the existing mask/paste policy; these edits follow source
        # drawings, not a DFM result or a relaxed design rule.
    if spec['courtyard_x']:
        for g in f.GraphicalItems():
            if g.GetLayer() != k.F_CrtYd:
                continue
            for getter, setter in [(g.GetStart, g.SetStart), (g.GetEnd, g.SetEnd)]:
                v = getter()
                if abs(v.x) > 1_000_000:
                    setter(vector([spec['courtyard_x'] * (1 if v.x > 0 else -1), v.y / 1e6]))
    return before


def main():
    assert sha(PCB) == EXPECTED, 'Source changed; do not overwrite later work'
    shutil.copy2(PCB, TRIAL / 'build/before-source-lands.kicad_pcb')
    project = json.loads(PCB.with_suffix('.kicad_pro').read_text())
    board = k.LoadBoard(str(PCB))
    fps = {f.GetReference(): f for f in board.GetFootprints()}
    io = k.PCB_IO_KICAD_SEXPR()
    rows = []
    for ref, spec in SPECS.items():
        f = fps[ref]
        pos = k.VECTOR2I(f.GetPosition().x, f.GetPosition().y)
        angle, flipped = f.GetOrientationDegrees(), f.IsFlipped()
        if flipped:
            f.SetLayerAndFlip(k.F_Cu)
        f.SetOrientationDegrees(0)
        f.SetPosition(vector([0, 0]))
        before = refine(f, spec)
        # Saving the same owned footprint avoids an unowned clone's flip path.
        io.FootprintSave(str(TRIAL / 'hardware/Collar05.pretty'), f)
        if flipped:
            f.SetLayerAndFlip(k.B_Cu)
        f.SetOrientationDegrees(angle)
        f.SetPosition(pos)
        pdf = ROOT / '.runtime/power-r05' / spec['pdf']
        rows.append({'ref': ref, 'before': before, 'drawing': spec,
                     'source_pdf_sha256': sha(pdf),
                     'land_note': 'Drawing inspected visually; stencil and assembly process remain unqualified.'})
    board.BuildConnectivity()
    k.ZONE_FILLER(board).Fill(board.Zones())
    assert k.SaveBoard(str(PCB), board)
    after_project = json.loads(PCB.with_suffix('.kicad_pro').read_text())
    assert project['board']['design_settings'] == after_project['board']['design_settings']
    assert project['net_settings'] == after_project['net_settings']
    result = {'before_sha256': EXPECTED, 'source_sha256': sha(PCB),
              'refined': rows, 'native_drc_pending': True}
    (TRIAL / 'evidence/source-land-refinement.json').write_text(json.dumps(result, indent=2) + '\n')
    print(json.dumps({'source_sha256': sha(PCB), 'refined': list(SPECS)}))


if __name__ == '__main__':
    main()
