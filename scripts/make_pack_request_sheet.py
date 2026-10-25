#!/usr/bin/env python3
"""Render a one-page supplier request from its controlled JSON dimensions."""
import html
import json
from pathlib import Path
import subprocess

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT/'assembly/pack-r03'
p = json.loads((OUT/'request.json').read_text())
m = p['mechanical']; n = m['ntc']
w, d, h = m['maximum_complete_pack_body_mm']
svg = ['<svg xmlns="http://www.w3.org/2000/svg" width="1123" height="794" viewBox="0 0 1123 794">',
       '<defs><marker id="arrow" markerWidth="8" markerHeight="8" refX="4" refY="4" orient="auto-start-reverse"><path d="M8 0L0 4L8 8" fill="none" stroke="#34485c"/></marker></defs>',
       '<rect width="1123" height="794" fill="white"/>',
       '<style>text{font-family:Arial,sans-serif;fill:#172b3c}.small{font-size:14px}.body{font-size:17px}.dim{stroke:#34485c;stroke-width:1.2;fill:none;marker-start:url(#arrow);marker-end:url(#arrow)}</style>']


def text(x, y, message, size=17, color='#172b3c', bold=False):
    svg.append(f'<text x="{x}" y="{y}" font-size="{size}" style="fill:{color};font-weight:{700 if bold else 400}">{html.escape(str(message))}</text>')


def rect(x,y,width,height,fill,stroke='#405769',radius=0):
    svg.append(f'<rect x="{x}" y="{y}" width="{width}" height="{height}" fill="{fill}" stroke="{stroke}" rx="{radius}"/>')


text(36,45,'CT-BAT-001-A | Protected pack + temperature sensor',27,bold=True)
rect(36,62,1051,42,'#fff1d4','#e3b252',5)
text(51,90,'SUPPLIER REQUEST — dimensions and ratings need written confirmation',19,bold=True)
text(36,135,'Requested pack body',20,bold=True)
scale=8.5; x,y=82,181
rect(x,y,w*scale,d*scale,'#e6edf2','#405769',8)
ntcw,ntcd,ntch=n['body_maximum_mm']
rect(x+(w-ntcw)/2*scale,y+(d-ntcd)/2*scale,ntcw*scale,ntcd*scale,'#eeba66','#a06b28',2)
text(100,225,'Complete protected 1S pack',16)
text(114,351,'Flat NTC attachment',16)
text(108,376,'Active sensing area: confirm',13)
svg.append(f'<path d="M{x} {y-23}H{x+w*scale}" class="dim"/>')
text(x+83,y-33,f'{w:g} mm MAX',16)
svg.append(f'<path d="M{x+w*scale+25} {y}V{y+d*scale}" class="dim"/>')
text(x+w*scale+36,y+d*scale/2,f'{d:g}',16)
text(x+w*scale+36,y+d*scale/2+20,'mm',14)
text(36,481,'Side section — budgets, not a supplier-approved stack',17,bold=True)
sx,sy=82,505
rect(sx,sy,w*scale,h*scale,'#e6edf2')
bond = n['bond_thickness_budget_mm']
cover = n['cover_thickness_budget_mm']
rect(sx+(w-ntcw)/2*scale,sy-bond*scale,ntcw*scale,bond*scale,'#d6cba8')
rect(sx+(w-ntcw)/2*scale,sy-(bond+ntch)*scale,ntcw*scale,ntch*scale,'#eeba66')
svg.append(f'<path d="M{sx+w*scale+22} {sy}V{sy+h*scale}" class="dim"/>')
text(389,532,f'{h:g} mm',16)
text(36,580,'Body limit must include PCM, insulation and service swelling.',14)
text(36,603,f'NTC: {ntcw:g} x {ntcd:g} x {ntch:g} mm; bond ≤{bond:g} mm; cover ≤{cover:.2f} mm.',14)
envelope = ' x '.join(f'{value:g}' for value in m['assembly_envelope_mm'])
text(36,626,f'Available complete assembly envelope: {envelope} mm.',14)

text(505,135,'Electrical requirements',20,bold=True)
rows=[('Capacity',f'≥{p["capacity_mAh"]["minimum_requested"]:g} mAh; about {p["capacity_mAh"]["preferred_nominal"]:g} mAh preferred'),
      ('Pack voltage',f'1S, {p["voltage"]["nominal_V"]:g} V nominal'),
      ('Charge voltage',f'{p["voltage"]["charge_nominal_V"]:g} V ±{100*p["voltage"]["charger_accuracy_fraction"]:g}%; confirm compatible limits'),
      ('Charge current',f'{1000*p["charge"]["nominal_A"]:g} mA nominal; check {1000*p["charge"]["design_upper_A"]:g} mA screen'),
      ('Cell charging',f'{p["charge"]["cell_temperature_C"][0]:g}–{p["charge"]["cell_temperature_C"][1]:g}°C; hardware temperature interlock'),
      ('Pack discharge',f'{1000*p["discharge"]["continuous_requested_A"]:g} mA continuous design allowance'),
      ('Charge finish',f'About {100*p["charge"]["nominal_A"]:g} mA termination; {p["charge"]["safety_timer_nominal_h"]:g} h nominal safety timer'),
      ('Pulse rating','Return duration, duty and temperature limits'),
      ('Sensor',f'{n["r25_ohm"]/1000:g}k ±{100*n["r25_tolerance_fraction"]:g}%; B{n["beta_25_85_K"]:g} ±{100*n["beta_tolerance_fraction"]:g}%; attached to cell'),
      ('Protection','Return thresholds, delays and recovery'),
      ('Termination','Three insulated, factory-assembled outputs')]
for i,(label,value) in enumerate(rows):
    yy=168+i*31
    if i%2==0:rect(500,yy-20,587,30,'#f3f6f8','none')
    text(510,yy,label,14,bold=True);text(655,yy,value,14)
text(505,545,'Native board interface',20,bold=True)
for i,line in enumerate(['J4.1  RED      protected positive / VBAT',
                         'J4.2  BLACK  protected negative + NTC return',
                         'J4.3  WHITE  NTC signal / BAT_NTC']):
    text(510,575+i*25,line,16)
rect(36,655,1051,101,'#f3f6f8','none',5)
for i,line in enumerate([
    'Please return a controlled part/drawing, complete-pack limits, NTC construction, safety documents, MOQ and lead time.',
    'The reference EEMB LP503030-PCM-LD sheet limits its PCM to 350 mA continuous. It is NOT approved for this request.',
    'If these limits cannot be met, propose a supported alternative. This enquiry is not an order or a manufacturing release.',
    'No end-user soldering. Lead length, routing, strain relief, sensor lag and physical qualification are still open.'
]):text(49,678+i*22,line,14)
text(36,780,'2026-10-26  |  Engineering request  |  Units: mm  |  Not to scale  |  1 / 1',13)
svg.append('</svg>')
(OUT/'request-sheet.svg').write_text('\n'.join(svg)+'\n')
for kind in ['pdf','png']:
    subprocess.run(['rsvg-convert','--format',kind,'--output',str(OUT/f'request-sheet.{kind}'),str(OUT/'request-sheet.svg')],check=True)
print('Created supplier request sheet; no supplier contact or part approval.')
