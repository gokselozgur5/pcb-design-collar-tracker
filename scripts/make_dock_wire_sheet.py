#!/usr/bin/env python3
"""Render a concise r14 drawing with the unclosed manufacturing conditions."""
import base64
import html
import json
from pathlib import Path
import subprocess

ROOT=Path(__file__).resolve().parents[1]
OUT=ROOT/'mechanical/swim-r14-wire-motion'


def main():
    r=json.loads((OUT/'checks.json').read_text())
    assert r['result']=='CONDITIONAL_WIRE_GEOMETRY_PASS'
    svg=['<svg xmlns="http://www.w3.org/2000/svg" width="1123" height="794" viewBox="0 0 1123 794">',
         '<rect width="1123" height="794" fill="white"/>',
         '<style>text{font-family:Arial,sans-serif;fill:#203645}</style>']
    def text(x,y,value,size=15,bold=False):
        svg.append(f'<text x="{x}" y="{y}" font-size="{size}" font-weight="{700 if bold else 400}">{html.escape(str(value))}</text>')
    def rect(x,y,w,h,fill):
        svg.append(f'<rect x="{x}" y="{y}" width="{w}" height="{h}" fill="{fill}"/>')
    def png(name,x,y,w,h):
        data=base64.b64encode((OUT/name).read_bytes()).decode()
        svg.append(f'<image x="{x}" y="{y}" width="{w}" height="{h}" href="data:image/png;base64,{data}"/>')
    text(34,40,'CT-DOCK-001-B | Charging-wire movement / r14',26,True)
    rect(34,57,1054,42,'#fff0d4')
    text(47,84,'GEOMETRY STUDY — fixed-end restraint, contact holding and physical qualification remain open',15,True)
    text(34,130,'External dock: 94 x 36 x 16mm',20,True)
    png('review.png',20,142,535,330)
    text(34,493,'Wearable, PCB, seals, key and contact seats are unchanged.',13,True)
    text(34,519,'USB red → fuse → Y=-6 → J3.1 /VIN_5V',14)
    text(34,544,'USB black → Y=+6 → J3.2 /GND',14)
    text(570,130,'Constant-length wire family',20,True)
    png('motion.png',557,140,530,218)
    rows=[('Free span at 23C','40.95 +/- 0.10mm per wire'),
          ('In-service span bound','40.775 to 41.125mm'),
          ('Conservative contact travel','2.1421mm'),
          ('Minimum remaining slack','0.3858mm'),
          ('Continuous radius bound',f'{r["continuous_radius_lower_bound"]:.4f}mm (required 8.382mm)'),
          ('Full sweep / housing','Empty CAD intersection'),
          ('Old housing control','Interference detected')]
    for i,(label,value) in enumerate(rows):
        y=378+i*30
        if i%2==0:rect(564,y-22,524,30,'#eff4f7')
        text(574,y,label,13,True);text(786,y,value,13)
    rect(34,580,1054,170,'#eff4f7')
    notes=[
        'The complete calculated family fits. Three colored poses illustrate it; interval bounds establish the continuous envelope.',
        'This does not constrain a free wire to that shape. A fixed-end clamp, forming process and cyclic-flex tests are still required.',
        '40.95mm excludes stripped conductor, crimp insertion and splice overlap. Do not use it as a production cut length.',
        'The r05l PCB retains both recorded 0 Danger / 0 Warning / 455 Good JLC runs. No unchanged-byte DFM was repeated.',
        'Dock retention, internal J3 wiring, pack approval, firmware and physical powered/RF/ingress tests remain open.',
        'This dry indoor charging prototype is not an order release. IP68 is a target, not a measured or certified result.'
    ]
    for i,line in enumerate(notes):text(47,605+i*25,line,12)
    text(34,778,'2026-10-26 | Units: mm | See dock.json, checks.json, mesh-checks.json and README | Review only',12)
    svg.append('</svg>')
    path=OUT/'wire-motion-sheet.svg';path.write_text('\n'.join(svg)+'\n')
    for fmt in ['pdf','png']:
        subprocess.run(['rsvg-convert','--format',fmt,'--output',str(OUT/f'wire-motion-sheet.{fmt}'),str(path)],check=True)


if __name__=='__main__':main()
