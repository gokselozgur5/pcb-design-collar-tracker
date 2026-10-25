#!/usr/bin/env python3
"""Create a dimensioned r12 review from the same checked cap and cradle shapes."""
import html
import json
from pathlib import Path
import subprocess

from check_pack_retention import cap_shape, centered

ROOT=Path(__file__).resolve().parents[1]
OUT=ROOT/'mechanical/swim-r12-pack-retention'
s=json.loads((OUT/'pack-retention.json').read_text())
r=json.loads((OUT/'pack-retention-checks.json').read_text())
assert r['result']=='CONDITIONAL_PACK_RETENTION_GEOMETRY_PASS'
svg=['<svg xmlns="http://www.w3.org/2000/svg" width="1123" height="794" viewBox="0 0 1123 794">',
     '<rect width="1123" height="794" fill="white"/>',
     '<style>text{font-family:Arial,sans-serif;fill:#192d3b}</style>']


def text(x,y,value,size=15,bold=False):
    svg.append(f'<text x="{x}" y="{y}" font-size="{size}" font-weight="{700 if bold else 400}">{html.escape(str(value))}</text>')


def rect(x,y,w,h,fill,stroke='none'):
    svg.append(f'<rect x="{x}" y="{y}" width="{w}" height="{h}" fill="{fill}" stroke="{stroke}"/>')


def plan(shape,fill,stroke):
    def ring(coords):
        points=[(252+8.9*x,335-8.9*y) for x,y in coords]
        return 'M'+' L'.join(f'{x:.4f},{y:.4f}' for x,y in points)+' Z'
    shapes=list(shape.geoms) if hasattr(shape,'geoms') else [shape]
    for p in shapes:
        d=ring(p.exterior.coords)+' '.join(ring(i.coords) for i in p.interiors)
        svg.append(f'<path d="{d}" fill-rule="evenodd" fill="{fill}" stroke="{stroke}" stroke-width="1"/>')


text(36,42,'CT-BAT-RET-001-A | Battery capture / r12',27,True)
rect(36,60,1051,42,'#fff0d4','#d9af65')
text(48,87,'CONDITIONAL PROTOTYPE — pack, contact regions, strength and ingress are not supplier-qualified',16,True)
text(36,137,'Plan: cap and cradle',20,True)
c=s['cradle'];f=s['cap']
plan(centered(c['outer_mm'],c['corner_radius_mm']).difference(centered(c['inner_mm'],c['corner_radius_mm'])),'#b9d4e5','#537a95')
plan(centered(s['pack_body_maximum_mm'][:2]),'#e7f1e9','#528666')
plan(cap_shape(s),'#e0b159','#a77622')
for b in f['bridges_xy_mm']:
    rect(252+b[0]*8.9,335-b[3]*8.9,(b[2]-b[0])*8.9,(b[3]-b[1])*8.9,'#e0b159','#a77622')
plan(centered([28,6.1]),'#dfab85','#a66c43')
text(142,172,'Cap body: 34.4mm',16,True)
text(442,307,'Cap',13);text(442,325,'33.0',16,True);text(442,345,'mm',14)
text(162,339,'NTC cover',14,True)
text(36,510,'Gold: carrier-integral cap and bridges.',15)
text(36,536,'Blue: shell-integral cradle. Green: requested pack.',14)
text(36,562,'Clearance cuts follow actual bottom-side parts.',14)
text(510,137,'Vertical stack and limits',20,True)
ntc=min(x['ntc_gap_mm'] for x in r['moving_pack_clearances'])
rows=[('Pack support','Z=1.80mm; original shell floor'),
      ('Maximum body top','Z=7.10mm seated'),
      ('Cradle wall top','Z=7.10mm'),
      ('Cap bearing / top','Z=7.56 / 8.31mm; 0.75mm thick'),
      ('PCB support','Z=10.40mm; unchanged'),
      ('Body max / min','32 x 30.5 x 5.3 / 30.5 x 29 x 4.8mm'),
      ('Component sweep',f'85 parts; new-solid gap ≥{r["minimum_component_gap_mm"]:.3f}mm'),
      ('Raised NTC cover',f'Gap to populated PCB ≥{ntc:.3f}mm'),
      ('Capture regions',f'Four; minimum guaranteed area {min(r["guaranteed_capture_areas_mm2"]):.3f}mm²'),
      ('Rigid outside','57.4 x 49.4 x 21.0mm + docking key'),
      ('Material / process','PC candidate; physical capability unapproved')]
for i,(k,v) in enumerate(rows):
    y=173+i*32
    if i%2==0:rect(504,y-21,583,31,'#f0f4f7')
    text(512,y,k,13,True);text(665,y,v,13)
text(510,554,'No rigid pouch preload or user soldering is intended.',14,True)
text(510,578,'Do not force the pack, carrier or lid into place.',14)
rect(36,610,1051,143,'#f0f4f7')
notes=[
 'Minimum pack dimensions and allowed bearing regions are added engineering requirements, not an approved supplier drawing.',
 'The raised-sensor check uses the shared carrier datum, independent component temperature and 0.10mm total feature error.',
 'Assigned CTE/tolerances are unchanged from r11. Pack/board tilt, loads, abrasion, cap strength and creep need physical checks.',
 'Factory lead exit, harness routing, contact termination, dock and programming/test remain unfinished. No order is authorized.',
 'The all-green PCB Gerber is unchanged. No physical water/dust test or IP68 approval is implied.'
]
for i,line in enumerate(notes):text(49,637+i*23,line,13)
text(36,779,'2026-10-26 | Units: mm | Actual plan geometry; dimensions govern | Review only | 1 / 1',13)
svg.append('</svg>')
(OUT/'pack-retention-sheet.svg').write_text('\n'.join(svg)+'\n')
for kind in ['pdf','png']:
    subprocess.run(['rsvg-convert','--format',kind,'--output',str(OUT/f'pack-retention-sheet.{kind}'),str(OUT/'pack-retention-sheet.svg')],check=True)
print('Created r12 battery-retention review drawing.')
