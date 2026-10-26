#!/usr/bin/env python3
"""Draw the r15 clamp and distinguish geometric evidence from qualification."""
import base64
import html
import json
from pathlib import Path
import subprocess

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT/'mechanical/swim-r15-wire-clamp'


def main():
    r = json.loads((OUT/'checks.json').read_text())
    assert r['result'] == 'CLAMP_GEOMETRY_PASS'
    svg = ['<svg xmlns="http://www.w3.org/2000/svg" width="1123" height="794" viewBox="0 0 1123 794">',
           '<rect width="1123" height="794" fill="white"/>',
           '<style>text{font-family:Arial,sans-serif;fill:#203645}</style>']

    def text(x, y, value, size=14, bold=False):
        svg.append(f'<text x="{x}" y="{y}" font-size="{size}" font-weight="{700 if bold else 400}">{html.escape(str(value))}</text>')

    def rect(x, y, w, h, fill):
        svg.append(f'<rect x="{x}" y="{y}" width="{w}" height="{h}" fill="{fill}"/>')

    def png(name, x, y, w, h, crop=None):
        data = base64.b64encode((OUT/name).read_bytes()).decode()
        if crop:
            box = ' '.join(str(v) for v in crop)
            svg.append(f'<svg x="{x}" y="{y}" width="{w}" height="{h}" viewBox="{box}">')
            svg.append(f'<image width="1600" height="1100" href="data:image/png;base64,{data}"/></svg>')
        else:
            svg.append(f'<image x="{x}" y="{y}" width="{w}" height="{h}" href="data:image/png;base64,{data}"/>')

    text(34, 40, 'CT-DOCK-001-C | Wire clamp and assembly fixture / r15', 25, True)
    rect(34, 57, 1054, 42, '#fff0d4')
    text(47, 84, 'PROTOTYPE — geometry checked; clamp retention, dock holding and electrical release remain open', 14, True)
    text(34, 130, 'External dry dock: 101.5 x 36 x 16mm', 19, True)
    png('review.png', 20, 140, 520, 315)
    text(34, 476, 'Wearable, PCB, key, seals and spring-contact seats unchanged.', 12, True)
    text(34, 505, 'Clamp assembly (cap lifted for visibility)', 16, True)
    png('clamp_detail.png', 30, 514, 350, 195, (630, 385, 360, 350))
    text(376, 550, '2 x M2 x 10', 13, True)
    text(376, 575, '4 silicone pads', 13)
    text(376, 600, 'Hard-stop columns', 13)
    text(376, 625, '1.93mm face gap', 13)
    text(376, 650, '6 x 3mm pad outline', 13)
    text(570, 130, 'Separate factory forming fixture', 19, True)
    png('fixture_review.png', 556, 141, 531, 230)
    rows = [('Free span / wire', '40.95 +/- 0.10mm at 23C'),
            ('Fixed-end plane', 'X=49.00 +/- 0.10mm total'),
            ('Sheet thickness', '0.7874 +/- 0.1016mm'),
            ('Local pad displacement', '5.50..43.52% / assigned bounds'),
            ('Housing / cap / fixture', 'Four closed CAD meshes'),
            ('CAD collision checks', '5 clear / 3 contacts / 5 controls'),
            ('PCB DFM', 'Unchanged: two runs at 0/0/455')]
    for i, (label, value) in enumerate(rows):
        y = 394+i*31
        if i % 2 == 0: rect(564, y-22, 524, 31, '#eff4f7')
        text(574, y, label, 12, True)
        text(770, y, value, 12)
    notes = ['The fixture controls assembly shape only. Free wires still require cycle tests.',
             'Squeeze is not a friction, insulation-strain or lifetime calculation.',
             'Factory pull target: 5N / 60s per wire; no physical result exists.',
             'Position error and later slip share the same +/- 0.10mm budget.']
    for i, line in enumerate(notes): text(570, 639+i*20, line, 11)
    rect(34, 718, 1054, 39, '#eff4f7')
    text(47, 742, 'Open: latch, internal J3 route, pack approval, firmware and physical power/RF/water/dust testing. No order release.', 12, True)
    text(34, 779, '2026-10-26 | Units: mm | See dock.json, sources.json, checks.json, mesh-checks.json and README | Review only', 11)
    svg.append('</svg>')
    path = OUT/'wire-clamp-sheet.svg'
    path.write_text('\n'.join(svg)+'\n')
    for fmt in ['pdf', 'png']:
        subprocess.run(['rsvg-convert', '--format', fmt, '--output', str(OUT/f'wire-clamp-sheet.{fmt}'), str(path)], check=True)


if __name__ == '__main__':
    main()
