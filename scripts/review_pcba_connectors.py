#!/usr/bin/env python3
"""Build the r02 connector review from native pads and the dated public library.

This writes review artifacts. Normal resume uses verify_pcba_connectors.py.
It does not edit the PCB, approve substitutions or submit an assembly order.
"""
import csv
import hashlib
import html
import json
import math
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
BASE = ROOT / 'assembly/pcba-r01'
OUT = ROOT / 'assembly/pcba-r02'
LIB = ROOT / '.runtime/manufacturing-r01'


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def native_lands():
    cpl = {r['Designator']: r for r in csv.DictReader((BASE / 'cpl.csv').open())}
    lands = {}
    for p in csv.DictReader((BASE / 'fitted-pads.csv').open()):
        ref = p['reference']
        if ref not in ('J1', 'J2', 'J6', 'Q1'):
            continue
        a = math.radians(float(p['pad_rotation_degrees']))
        w, h = float(p['size_x_mm']), float(p['size_y_mm'])
        lands.setdefault(ref, []).append({
            'pin': p['pin'], 'net': p['net'],
            'x_mm': round(float(p['x_mm']) - float(cpl[ref]['Mid X']), 6),
            'y_mm': round(float(p['y_mm']) - float(cpl[ref]['Mid Y']), 6),
            'width_mm': round(abs(w * math.cos(a)) + abs(h * math.sin(a)), 6),
            'height_mm': round(abs(w * math.sin(a)) + abs(h * math.cos(a)), 6),
        })
    return cpl, lands


def build():
    OUT.mkdir(parents=True, exist_ok=True)
    cpl, lands = native_lands()
    numbers = json.loads((LIB / 'library-numbers.json').read_text())['result']
    n = next(p for p in numbers if p['number'] == 'C88373')
    packages = json.loads((LIB / 'library-packages.json').read_text())['result']
    p = next(p for p in packages if p['uuid'] == n['puuid'])['dataStr']
    origin = [float(p['head'][v]) for v in ('x', 'y')]
    assert origin == [float(v) for v in p['canvas'].split('~')[16:18]]
    svg = json.loads(next(s[8:] for s in p['shape'] if s.startswith('SVGNODE~')))
    model = [float(v) for v in svg['attrs']['c_origin'].split(',')]
    model_offset = [(model[0] - origin[0]) * .254, -(model[1] - origin[1]) * .254]
    xy = []
    for child in svg['childNodes']:
        values = [float(v) for v in child['attrs']['points'].split()]
        xy.extend(zip(values[::2], values[1::2]))
    bbox_centre = [(min(v[i] for v in xy) + max(v[i] for v in xy)) / 2 for i in (0, 1)]
    assert max(abs(a - b) for a, b in zip(model, bbox_centre)) < 1e-8
    library_lands = []
    for s in p['shape']:
        if not s.startswith('PAD~'):
            continue
        v = s.split('~')
        a = math.radians(float(v[11]))
        w, h = float(v[4]) * .254, float(v[5]) * .254
        library_lands.append({
            'pin': v[8], 'function': 'SIG' if v[8] == '2' else 'GND',
            'x_mm': (float(v[2]) - origin[0]) * .254,
            'y_mm': -(float(v[3]) - origin[1]) * .254,
            'width_mm': abs(w * math.cos(a)) + abs(h * math.sin(a)),
            'height_mm': abs(w * math.sin(a)) + abs(h * math.cos(a)),
        })
    inputs = [BASE / 'cpl.csv', BASE / 'cpl-jlc-review.csv', BASE / 'fitted-pads.csv', BASE / 'bom.csv']
    report = {
        'revision': 'pcba-r02', 'production_release': False,
        'input_sha256': {str(p.relative_to(ROOT)): sha(p) for p in inputs},
        'coordinate_convention': 'Gerber top view, X right/Y up; bottom coordinates are not mirrored',
        'native_lands': lands,
        'ufl': {
            'references': ['J1', 'J2'], 'mpn': 'U.FL-R-SMT-1(10)', 'code': 'C88373',
            'package_uuid': n['puuid'], 'source': 'JLCEDA / EasyEDA Official Library',
            'source_urls': ['https://easyeda.com/', 'https://docs.easyeda.com/en/API/2-Coordinate-System-and-Unit/'],
            'library_response_sha256': {p.name: sha(p) for p in [LIB / 'library-numbers.json', LIB / 'library-packages.json']},
            'library_origin_raw': origin, 'model_centre_raw': model,
            'model_outline_bbox_centre_raw': bbox_centre,
            'model_offset_mm': model_offset, 'library_lands': library_lands,
            'manufacturer_drawing_rotation_degrees': 270,
            'manufacturer_dimensions_mm': {'ground_outer_span': 4, 'ground_inner_gap': 1.9,
                'ground_length': 2.2, 'signal_width': 1, 'signal_length': 1.05, 'signal_inner_edge': 1},
            'native_pattern_matches_nominal_manufacturer_drawing': True,
            'pin_mapping': {'native_1': 'library_2: SIG', 'native_2_both': 'library_1_and_3: GND'},
            'supplier_cpl_translation_mm': [-model_offset[0], -model_offset[1]],
            'scope': 'Candidate for this dated JLC model only. Native physical connector centres and PCB remain unchanged. Factory must confirm the placement datum before machine programming.',
        },
        'sim': {
            'reference': 'J6', 'mpn': 'SIM8051-6-0-14-00-A', 'code': 'C7363812',
            'manufacturer_drawing': 'GCT SIM8051 D6, 14 July 2022, component-side land view',
            'drawing_to_gerber': 'Rotate the component-side drawing 180 degrees, then reflect X for the bottom side',
            'native_pattern_matches_nominal_manufacturer_drawing': True,
            'native_centre_mm': [float(cpl['J6'][k]) for k in ('Mid X', 'Mid Y')],
            'card_opening_side_gerber': '+Y, toward board edge Y=30mm',
            'card_insertion_direction_gerber': '-Y, from the opening into the socket',
            'peg_holes': False, 'card_detect': False, 'unused_contact': 'C6/VPP remains electrically unconnected',
            'library_model_returned': False, 'supplier_placement_accepted': False,
        },
        'q1': {'mpn': 'DMN62D2UDW-7', 'bom_unchanged': True, 'substitution_approved': False},
        'smt_accepted': False,
    }
    (OUT / 'connector-review.json').write_text(json.dumps(report, indent=2) + '\n')
    rows = list(csv.DictReader((BASE / 'cpl-jlc-review.csv').open()))
    for row in rows:
        if row['Designator'] in ('J1', 'J2'):
            row['Mid X'] = f"{float(row['Mid X']) - model_offset[0]:.6f}"
            row['Mid Y'] = f"{float(row['Mid Y']) - model_offset[1]:.6f}"
    with (OUT / 'cpl-jlc-review.csv').open('w', newline='') as f:
        w = csv.DictWriter(f, fieldnames=list(rows[0]))
        w.writeheader()
        w.writerows(rows)
    draw(cpl, lands)
    print(json.dumps({'references': list(lands), 'ufl_model_offset_mm': model_offset,
                      'bom_unchanged': True, 'production_release': False}, indent=2))


def draw(cpl, lands):
    """Original drawing of measured native pads; no supplier artwork is copied."""
    s = ['<svg xmlns="http://www.w3.org/2000/svg" width="1200" height="1080" viewBox="0 0 1200 1080">',
         '<rect width="1200" height="1080" fill="white"/>',
         '<style>text{font-family:Arial,sans-serif;fill:#172d3d}.title{font-size:26px;font-weight:bold}.note{font-size:17px}.label{font-size:15px}</style>']

    def text(x, y, value, cls='note', anchor='start'):
        s.append(f'<text x="{x}" y="{y}" class="{cls}" text-anchor="{anchor}">{html.escape(value)}</text>')

    text(35, 43, 'r05l / PCBA r02 — native connector and Q1 placement reference', 'title')
    text(35, 75, 'Review only. Dimensions in mm; not a stencil, machine program or assembly approval.')
    text(35, 104, 'Gerber origin unchanged. J6 is shown from the bottom component side (X mirrored).')
    layouts = [('J1', 300, 305, 65), ('J2', 880, 305, 65),
               ('J6', 300, 780, 24), ('Q1', 880, 780, 95)]
    for ref, cx, cy, scale in layouts:
        y0 = 145 if ref in ('J1', 'J2') else 550
        cp = cpl[ref]
        text(cx - 240, y0, f"{ref} — {cp['Layer']} | physical centre ({float(cp['Mid X']):g}, {float(cp['Mid Y']):g})", 'note')
        s.append(f'<path d="M {cx-15} {cy} H {cx+15} M {cx} {cy-15} V {cy+15}" stroke="#667788" fill="none"/>')
        if ref in ('J1', 'J2'):
            s.append(f'<circle cx="{cx}" cy="{cy}" r="{scale}" fill="none" stroke="#667788" stroke-dasharray="4 4"/>')
        for pad in lands[ref]:
            x = -pad['x_mm'] if ref == 'J6' else pad['x_mm']
            y = pad['y_mm']
            w, h = pad['width_mm'] * scale, pad['height_mm'] * scale
            px, py = cx + x * scale, cy - y * scale
            ground = pad['net'] == '/GND'
            s.append(f'<rect x="{px-w/2}" y="{py-h/2}" width="{w}" height="{h}" fill="{"#bce4c7" if ground else "#f8d59e"}" stroke="#273b4a"/>')
            text(px, py + 5, pad['pin'], 'label', 'middle')
        if ref in ('J1', 'J2'):
            text(cx - 240, 475, 'Pin 1 = RF; both pin-2 lands = GND. Coax centre = crosshair.')
            text(cx - 240, 501, 'Only the dated JLC model origin moves -0.632003 mm in X.')
        elif ref == 'J6':
            text(cx - 240, 958, '1 VCC / 2 RST / 3 CLK / 5 GND / 6 NC / 7 IO / 8 shield')
            s.append(f'<path d="M {cx} {cy-190} v 32 m -8 -10 l 8 10 l 8 -10" stroke="#156789" stroke-width="3" fill="none"/>')
            text(cx, cy - 202, 'Opening at Gerber +Y edge; insert toward -Y', 'label', 'middle')
            text(cx - 240, 987, 'No-peg variant. Do not drill locating holes or fit a 180-degree reversal.')
        else:
            text(cx - 240, 593, 'Original DMN62D2UDW-7 remains mandatory; candidate not selected.')
            text(cx - 240, 949, '1 S1 / 2 G1 / 3 D1 / 4 S2 / 5 G2 / 6 D2')
            text(cx - 240, 976, 'S1/S2: GND; G1/G2: POWER_FAULT')
            text(cx - 240, 1003, 'D1: VIO_ENABLE; D2: VIO_DISCHARGE')
    text(35, 1052, 'Reference geometry: native r05l pad export; Hirose U.FL mounting pattern; GCT SIM8051 D6; Diodes SOT363.', 'label')
    s.append('</svg>')
    (OUT / 'placement-reference.svg').write_text('\n'.join(s) + '\n')


if __name__ == '__main__':
    build()
