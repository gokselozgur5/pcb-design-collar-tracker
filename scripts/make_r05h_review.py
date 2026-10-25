#!/usr/bin/env python3
"""Produce a compact source-bound PCB/fit review without claiming production approval."""
import base64
import hashlib
import html
import json
from pathlib import Path
import subprocess

root = Path(__file__).resolve().parents[1]
trial = root / 'experiments/power-r05h-six-layer'
out = trial / 'evidence'
fitdir = root / 'mechanical/swim-r06-six-layer-fit'
read = lambda p: json.loads(p.read_text())
sha = lambda p: hashlib.sha256(p.read_bytes()).hexdigest()
source = sha(trial / 'hardware/collar-tracker.kicad_pcb')
inv = read(out / 'layout-inventory.json')
fit = read(fitdir / 'populated-fit.json')
records = [read(out / f'jlc-final-check{i}/summary.json') for i in (1, 2)]
export = read(out / 'collar-tracker-05h-final2-40x32-dfm/manifest.json')
assert source == inv['source_sha256'] == fit['pcb_sha256'] == export['source_sha256']
assert all(r['zip_sha256'] == export['zip_sha256'] and r['counts'] == dict(danger=0,warning=0,good=449)
           and r['analyzed_rows'] == 29 for r in records)
assert records[0]['record_id'] != records[1]['record_id'] and inv['returns_outside_2mm'] == 0
lines = ['<svg xmlns="http://www.w3.org/2000/svg" width="1600" height="1200" viewBox="0 0 1600 1200" font-family="Arial, sans-serif">']
def rect(x,y,w,h,fill):
    lines.append(f'<rect x="{x}" y="{y}" width="{w}" height="{h}" fill="{fill}"/>')
def text(x,y,value,size=23,color='#253442',bold=False):
    lines.append(f'<text x="{x}" y="{y}" font-size="{size}" fill="{color}" font-weight="{"bold" if bold else "normal"}">{html.escape(str(value))}</text>')
def picture(path,x,y,w,h):
    b64 = base64.b64encode(path.read_bytes()).decode()
    lines.append(f'<image x="{x}" y="{y}" width="{w}" height="{h}" preserveAspectRatio="xMidYMid meet" href="data:image/png;base64,{b64}"/>')
rect(0,0,1600,1200,'#f4f6f8');rect(0,0,1600,120,'#183145')
text(40,55,'COLLAR TRACKER / r05h DESIGN REVIEW',36,'white',True)
text(40,95,'PCB DFM complete. Electrical release on hold. IP68 unqualified.',24,'#e3ebf0')
for x,name,title in [(40,'top','TOP / 40 × 32 mm'),(820,'bottom','BOTTOM / mirrored component view')]:
    rect(x,145,740,585,'white');text(x+20,185,title,25,bold=True)
    picture(out/(name+'.png'),x+20,205,700,510)
rect(40,750,740,360,'#e4f0e8');text(60,793,'VERIFIED PCB CHECKS',25,'#18603c',True)
for i,s in enumerate([
    'Six layers; nominal thickness 0.8 mm; 71 footprints',
    'Native DRC / ERC / connectivity / parity: zero findings',
    'Two real JLC runs: 0 Danger / 0 Warning / 449 Good',
    'Same ZIP and rules; all 29 rows analyzed; SMT off',
    '94 unique GND terminals local; 110 GND vias',
    'In1/In4: continuous GND; 128/128 return screens pass',
    'RF geometry retained; actual stack / impedance open']):text(60,835+i*36,s,21)
rect(820,750,740,360,'white');picture(fitdir/'populated.png',825,750,340,255)
text(1150,790,'NOMINAL FIT',24,bold=True)
for i,s in enumerate(['69 populated envelopes','30 shell checks pass','Rigid: 57.4 × 49.4 × 17.6','Boot: 60.4 × 52.4 × 22.4','2 m / 60 min: provisional']):text(1150,830+i*34,s,20)
text(840,1040,'Pack, antennas, retention, seals and physical tests remain open.',19)
text(840,1073,'Component boxes and orange antenna reservations are provisional.',18)
text(40,1142,'PCB: '+source,17)
text(40,1176,'2026-10-25 | Bare-board DFM evidence only; BOM/CPL, factory programming and powered tests remain required.',18)
lines.append('</svg>');(out/'review.svg').write_text('\n'.join(lines)+'\n')
for suffix in ['pdf','png']:
    subprocess.run(['rsvg-convert','-f',suffix,'-o',str(out/('review.'+suffix)),str(out/'review.svg')],check=True)
print('Created current PCB and preliminary fit review PDF/PNG')
