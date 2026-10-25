#!/usr/bin/env python3
"""Render the checked dock drawing and pinout as a standalone review sheet."""
import base64
import html
import json
from pathlib import Path
import subprocess

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / 'mechanical/swim-r13-charge-dock'


def main():
    r = json.loads((OUT / 'checks.json').read_text())
    assert r['result'] == 'CONDITIONAL_DOCK_GEOMETRY_PASS'
    svg = ['<svg xmlns="http://www.w3.org/2000/svg" width="1123" height="794" viewBox="0 0 1123 794">',
           '<rect width="1123" height="794" fill="white"/>',
           '<style>text{font-family:Arial,sans-serif;fill:#203645}</style>']

    def text(x, y, value, size=15, bold=False):
        svg.append(f'<text x="{x}" y="{y}" font-size="{size}" font-weight="{700 if bold else 400}">{html.escape(str(value))}</text>')

    def rect(x, y, w, h, fill):
        svg.append(f'<rect x="{x}" y="{y}" width="{w}" height="{h}" fill="{fill}"/>')

    text(34,40,'CT-DOCK-001-A | External charging dock / r13',26,True)
    rect(34,57,1054,42,'#fff0d4')
    text(47,84,'GEOMETRY PROTOTYPE — holding force, assembly process, powered behavior and IP68 remain open',15,True)
    text(34,132,'Split housing and sourced component envelopes',18,True)
    data = base64.b64encode((OUT / 'review.png').read_bytes()).decode()
    svg.append(f'<image x="22" y="142" width="535" height="358" href="data:image/png;base64,{data}"/>')
    text(34,518,'Dock: 60 x 36 x 16mm, excluding cable / screw heads.',14,True)
    text(34,542,'Two Mill-Max 0962 contacts; 26 AWG pigtails; 0.75A fuse.',14)
    text(34,566,'Jacket tie bay is separate from the electrical terminations.',14)
    text(570,132,'Mating and polarity checks',20,True)
    rows=[('Contact travel',f'{r["operating_compression_mm"][0]:.3f}–{r["operating_compression_mm"][1]:.3f}mm compressed'),
          ('Bottoming margin',f'{r["minimum_bottoming_margin_mm"]:.3f}mm minimum'),
          ('Operating condition','Faces held within 0.05mm gap'),
          ('Early touch bound',f'{r["earliest_contact_gap_bound_mm"]:.3f}mm face separation'),
          ('Revised collar key','4.0mm projection; Z=7.7–13.2'),
          ('Reverse block margin','0.55mm in aligned 180° screen'),
          ('Wire splay radius',f'≥{r["continuous_tail_radius_bound_mm"]:.3f}mm continuous bound'),
          ('Wearable main shell','57.4 x 49.4 x 21.0mm, unchanged'),
          ('Shell including key','61.4 x 49.4 x 21.0mm'),
          ('Unchanged boot','60.4 x 52.4 x 25.8mm')]
    for i,(a,b) in enumerate(rows):
        y=171+i*31
        if i%2==0:rect(564,y-22,524,30,'#eff4f7')
        text(574,y,a,13,True);text(741,y,b,13)
    text(570,505,'USB red → F1 → Y=-6 → J3.1 /VIN_5V',15,True)
    text(570,533,'USB black → Y=+6 → J3.2 /GND',15,True)
    text(570,562,'White/green/drain individually insulated; no USB data.',13)
    rect(34,599,1054,151,'#eff4f7')
    notes=[
        'PCB r05l and both actual 0 Danger / 0 Warning JLC reports are unchanged. This drawing is not a PCB or device release.',
        'The old short/high key fails the reverse-contact checks. Skew, damage and physical misuse are not qualified by this aligned model.',
        'The two springs can require 1.569N at midstroke. Existing magnets have no demonstrated holding force across the plastic walls.',
        'Dry indoor charging only. Crimp tooling, sleeve/joins, cable pull, source/fault behavior and the internal J3 route remain unfinished.',
        'Battery supplier approval, firmware and assembled powered/RF/water/dust tests are still required. No order or physical test was made.'
    ]
    for i,line in enumerate(notes):text(47,625+i*25,line,12)
    text(34,778,'2026-10-26 | Units: mm | Dimensions govern | See dock.json, checks.json and source manifest | Review only',12)
    svg.append('</svg>')
    path=OUT/'dock-sheet.svg'
    path.write_text('\n'.join(svg)+'\n')
    for fmt in ['pdf','png']:
        subprocess.run(['rsvg-convert','--format',fmt,'--output',str(OUT/f'dock-sheet.{fmt}'),str(path)],check=True)


if __name__=='__main__':
    main()
