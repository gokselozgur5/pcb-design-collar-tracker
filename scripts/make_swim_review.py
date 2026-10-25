#!/usr/bin/env python3
"""Create portable English review/drawing sheets from the checked prototype."""
import base64
import html
import json
import math
from pathlib import Path
import shutil
import subprocess
from verify_handoff import verify

ROOT=Path(__file__).resolve().parents[1];OUT=ROOT/'mechanical/swim-r01'
p=json.loads((OUT/'parameters.json').read_text());checks=json.loads((OUT/'checks.json').read_text())
mesh=json.loads((OUT/'mesh-checks.json').read_text());verification=verify(include_review_bundle=False)
assert checks['source_sha256']==mesh['pcb_sha256']==verification['current']['source_sha256']
assert checks['all_declared_geometry_checks_pass']
b,g,c=p['body'],p['gland'],p['contacts'];W,H=1600,1160
parts=[]
def raw(x):parts.append(x)
def text(x,y,s,size=21,color='#203040',weight='normal'):
    raw(f'<text x="{x}" y="{y}" font-size="{size}" fill="{color}" font-weight="{weight}">{html.escape(str(s))}</text>')
def rect(x,y,w,h,fill,stroke='none',r=0):raw(f'<rect x="{x}" y="{y}" width="{w}" height="{h}" rx="{r}" fill="{fill}" stroke="{stroke}"/>')
def line(x1,y1,x2,y2,stroke='#647586',width=1.5):raw(f'<path d="M{x1},{y1} L{x2},{y2}" fill="none" stroke="{stroke}" stroke-width="{width}"/>')
def picture(path,x,y,w,h):
    data=base64.b64encode(path.read_bytes()).decode();raw(f'<image x="{x}" y="{y}" width="{w}" height="{h}" preserveAspectRatio="xMidYMid meet" href="data:image/png;base64,{data}"/>')
def start(title,subtitle):
    parts.clear();raw(f'<svg xmlns="http://www.w3.org/2000/svg" width="{W}" height="{H}" viewBox="0 0 {W} {H}" font-family="Arial, sans-serif">');rect(0,0,W,H,'#f3f6fa');rect(0,0,W,140,'#142638');text(48,65,title,37,'white','bold');text(48,108,subtitle,22,'#bdd0df')
def finish(name):
    text(48,1128,'2026-10-25  |  Dimensions in mm. Diagrams are not print-scale. STL files are 1:1.  |  Prototype / no IP qualification',18,'#5a6b7a')
    raw('</svg>');(OUT/(name+'.svg')).write_text('\n'.join(parts)+'\n');subprocess.run(['rsvg-convert','-f','pdf','-o',str(OUT/(name+'.pdf')),str(OUT/(name+'.svg'))],check=True)
    subprocess.run(['rsvg-convert','-o',str(OUT/(name+'.png')),str(OUT/(name+'.svg'))],check=True)

start('COLLAR TRACKER  /  DESIGN REVIEW','r04i PCB verified  •  swim-r01 enclosure prototype  •  final part selections and physical tests remain open')
rect(40,164,660,545,'white','#d8e0e8',12);rect(722,164,838,545,'white','#d8e0e8',12)
text(64,205,'40 × 32 mm  /  FOUR-LAYER PCB',25,weight='bold')
picture(ROOT/p['pcb']['trial']/'evidence/back.png',64,225,610,450)
text(746,205,'SEALED HOUSING  /  EXPLODED MODEL',25,weight='bold')
picture(OUT/'exploded.png',742,215,796,470)
rect(40,730,660,338,'#e7f2ec','#b8d8c5',12);text(65,773,'PCB CHECKS COMPLETE',25,'#176b43','bold')
for i,s in enumerate(['Native DRC / ERC / connectivity / parity: zero findings','Two real JLC records: 0 Danger / 0 Warning each','Identical ZIP, unchanged rules, 29 analyzed rows each','82 local GND pads; two continuous inner GND layers','93 / 93 signal-via return screens; SIM lane clear','SMT assembly, power and RF qualification remain open']):text(65,815+i*39,s,20)
rect(722,730,838,338,'#fff3df','#e5c891',12);text(746,773,'MECHANICAL PROTOTYPE',25,'#865416','bold')
for i,s in enumerate([f'Rigid body: {b["size"][0]:g} × {b["size"][1]:g} × {b["size"][2]+b["lid_thickness"]:g}; {b["size"][0]+1.3:g} including the key',f'With collar boot: {b["size"][0]+3:g} × {b["size"][1]+3:g} × {b["size"][2]+b["lid_thickness"]+4.8:g}','Continuous lid O-ring; two independent contact seals',f'Target: {p["target"]["depth_m"]:g} m fresh water / {p["target"]["duration_min"]:g} min — provisional conditions','Eight exported solids checked; no physical ingress test','Battery, antenna and dock reservations are not approved parts']):text(746,815+i*39,s,20)
finish('overview')

start('SWIM-r01  /  DIMENSIONED PROTOTYPE','Nominal CAD plus controlled seal dimensions  •  CNC/process and material approval required before manufacture')
# Top view; Y flipped to match the PCB/model axes.
text(48,190,'TOP VIEW / LID REMOVED',25,weight='bold');raw('<g transform="translate(330,445) scale(7,-7)" stroke-width=".15">')
rect(-b['size'][0]/2,-b['size'][1]/2,*b['size'][:2],'#d7e1e9','#304a60',b['corner_radius'])
rect(b['size'][0]/2,-1.5,1.3,3,'#d7e1e9','#304a60')
raw(f'<rect x="{-g["centerline_size"][0]/2}" y="{-g["centerline_size"][1]/2}" width="{g["centerline_size"][0]}" height="{g["centerline_size"][1]}" rx="{g["corner_radius"]}" fill="none" stroke="#5c7990" stroke-width="{g["width"]}"/>')
rect(-b['cavity'][0]/2,-b['cavity'][1]/2,*b['cavity'],'#fff','#9baab6',b['cavity_radius'])
raw('<rect x="-20" y="-16" width="40" height="32" fill="#b9ddc6" fill-opacity=".65" stroke="#23714a" stroke-width=".2"/>')
raw('<rect x="4.4" y="12.1" width="9.2" height="3.9" fill="#eab56c" fill-opacity=".8"/>')
for x,y in p['fasteners']['centers']:raw(f'<circle cx="{x}" cy="{y}" r="{p["fasteners"]["hole"]/2}" fill="white" stroke="#304a60" stroke-width=".15"/>')
raw('</g>');text(175,661,f'{b["size"][0]:g} body width; {b["size"][0]+1.3:g} with key',20);text(94,700,f'{b["size"][1]:g} body depth  •  R{b["corner_radius"]:g} outer corners',20);text(94,734,f'{b["cavity"][0]:g} × {b["cavity"][1]:g} cavity, R{b["cavity_radius"]:g}  •  PCB 40 × 32',20);text(94,768,'4 × Ø2.2 at (±25.1, ±21.1)',20);text(94,802,'Orange: SIM lane; lift tray for card service',20)
# Cross-section of the main face gland, dimensions at enlarged scale.
text(730,190,'MAIN LID SEAL / SECTION',25,weight='bold')
rect(750,240,650,80,'#aabac7','#304a60');rect(750,320,650,200,'#d7e1e9','#304a60')
rect(925,320,250,134,'white','#304a60');raw('<ellipse cx="1050" cy="387" rx="113" ry="67" fill="#7f4d9a" fill-opacity=".8" stroke="#503565"/>')
text(760,290,'LID',20);text(760,495,'BODY',20);text(1220,395,'1.34',22);text(950,555,'2.50 ±0.05',22)
text(730,592,'Depth 1.34 ±0.02; local flatness budget 0.01',21)
text(730,628,'Centerline 49 × 41, R6; bottom corner R0.2',21)
text(730,664,'O-ring 50.52 ID × 1.78 section, EPDM 70A',21)
mr=next(x for x in checks['checks'] if x['name']=='Main seal declared tolerance screen')
text(730,700,f'Declared squeeze: {100*mr["squeeze"][0]:.1f}–{100*mr["squeeze"][1]:.1f}%; fill: {100*mr["fill"][0]:.1f}–{100*mr["fill"][1]:.1f}%',21)
text(730,736,'Seal face Ra ≤0.8 µm; no burrs or crossing tool marks',21)
# Bottom panel: compact contact dimensional definition.
rect(40,840,1520,245,'white','#d8e0e8',12);text(64,882,'SEALED CHARGING TARGET / CUSTOM TURNED PART',24,weight='bold')
for i,s in enumerate(['Head Ø8.5 × 0.8  |  Shaft Ø7.28 × 7.70  |  Rear M4 × 3.50 thread','Radial gland root Ø4.64 ±0.01; width 2.80 ±0.05; center 3.85 behind head','Housing bore Ø7.34 ±0.02; seal ID 4.50 ±0.10 × section 1.80 ±0.08','Centers at Y=±6, Z=5.8 on +X wall. +Y is +5 V; −Y is GND.']):text(65,922+i*36,s,21)
text(64,1070,'Contact coating, edge finishing, retention, dock parts and electrical/immersion durability require prototype qualification.',18,'#865416')
finish('drawing')
exe=shutil.which('pdfunite');assert exe,'pdfunite is needed to join the two review sheets'
subprocess.run([exe,str(OUT/'overview.pdf'),str(OUT/'drawing.pdf'),str(OUT/'review.pdf')],check=True)
print('Created review.pdf: measured PCB evidence + prototype drawing')
