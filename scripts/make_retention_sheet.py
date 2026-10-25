#!/usr/bin/env python3
"""Render the r10 retainer drawing from the controlled dimensional study."""
import hashlib
import html
import json
from pathlib import Path
import subprocess

ROOT=Path(__file__).resolve().parents[1]
OUT=ROOT/'mechanical/swim-r10-retention'
r=json.loads((OUT/'retention.json').read_text())
result=json.loads((OUT/'retention-checks.json').read_text())
assert result['result']=='CONDITIONAL_RETENTION_GEOMETRY_PASS'
assert result['checker_sha256']==hashlib.sha256((ROOT/'scripts/check_retention_assembly.py').read_bytes()).hexdigest()
f=r['frame'];outer=f['outer_mm'];inner=f['inner_mm']
svg=['<svg xmlns="http://www.w3.org/2000/svg" width="1123" height="794" viewBox="0 0 1123 794">',
     '<rect width="1123" height="794" fill="white"/>',
     '<style>text{font-family:Arial,sans-serif;fill:#172b3c}</style>']


def text(x,y,label,size=16,bold=False):
    svg.append(f'<text x="{x}" y="{y}" font-size="{size}" font-weight="{700 if bold else 400}">{html.escape(str(label))}</text>')


def rect(x,y,w,h,fill,stroke='none',radius=0):
    svg.append(f'<rect x="{x}" y="{y}" width="{w}" height="{h}" fill="{fill}" stroke="{stroke}" rx="{radius}"/>')


text(36,43,'CT-RET-001 | Captive PCB frame / r10',27,True)
rect(36,60,1051,42,'#fff1d4','#e3b252',5)
text(50,88,'PROTOTYPE — manufacturing, thermal fit, retention strength and ingress remain unqualified',17,True)
text(36,132,'Retainer plan',20,True)
scale=8.4;cx=252;cy=324
def plan_rect(b,color):
    a,bb,c,d=b
    rect(cx+a*scale,cy-d*scale,(c-a)*scale,(d-bb)*scale,color)
rx=cx-outer[0]/2*scale;ry=cy-outer[1]/2*scale
svg.append(f'<defs><clipPath id="outline"><rect x="{rx}" y="{ry}" width="{outer[0]*scale}" height="{outer[1]*scale}" rx="{f["outer_radius_mm"]*scale}"/></clipPath></defs>')
rect(rx,ry,outer[0]*scale,outer[1]*scale,'#a66dae','#63366b',f['outer_radius_mm']*scale)
rect(cx-inner[0]/2*scale,cy-inner[1]/2*scale,inner[0]*scale,inner[1]*scale,'white','none',f['inner_radius_mm']*scale)
svg.append('<g clip-path="url(#outline)">')
for b in r['capture_tabs_xy_mm']+r['north_tabs_xy_mm']:plan_rect(b,'#a66dae')
svg.append('</g>')
svg.append(f'<rect x="{cx-20*scale}" y="{cy-16*scale}" width="{40*scale}" height="{32*scale}" fill="none" stroke="#1d906d" stroke-width="1.4" stroke-dasharray="7 4"/>')
plan_rect(r['orientation_key']['xy_mm'],'#e7a748')
text(168,169,f'{outer[0]:g} mm overall',16,True)
text(439,317,f'{outer[1]:g}',16,True);text(439,338,'mm',14)
text(116,307,'40 x 32mm PCB outline',17)
text(115,333,'Four inward capture tabs',17)
text(112,359,'Key shown in orange',16)
text(36,500,f'Frame thickness: {f["height_mm"]:g}mm; aperture: {inner[0]:g} x {inner[1]:g}mm.',16)
text(36,526,'Board and its all-green Gerber remain unchanged.',15)
text(36,551,'Rigid enclosure: 57.4 x 49.4 x 21.0mm, plus docking key.',15)

text(510,132,'Assembly datums and checks',20,True)
tab=next(c for c in result['checks'] if c['name']=='Four tabs retain the smallest board')
card=next(c for c in result['checks'] if c['name']=='SIM insertion clears bridge with PCB seated')
minimum=min(c['gap_mm'] for c in result['minimum_component_gaps'].values())
cable=min(c['minimum_component_gap_mm'] for case in result['cable_motion']['cases'] for c in case['cables'])
rows=[('PCB support','Z=10.40mm; thickness 0.71–0.91mm'),
      ('Guide / frame bottom',f'Z={r["guide_top_z_mm"]:.2f}mm nominal'),
      ('Lid stop plane',f'Z={r["lid_post_bottom_z_mm"]:.2f}mm nominal'),
      ('Maximum PCB top',f'Z={r["motion_screen"]["pcb_top_z_mm"][1]:.2f}mm in this model'),
      ('SIM bridge',f'Z={r["sim_bridge_bottom_z_mm"]:.2f}mm; seated gap ≥{card["minimum_gap_mm"]:.2f}mm'),
      ('Component sweep',f'85 envelopes; minimum gap {minimum:.3f}mm'),
      ('Cable endpoint poses',f'27 cases; minimum body gap {cable:.3f}mm'),
      ('Tab overlap',f'27 offset/yaw cases; ≥{tab["minimum_contact_area_mm2"]:.3f}mm² per tab'),
      ('Manufacturing limits','Assigned requirements; inspect actual parts'),
      ('Free play','Captive frame; zero movement is not claimed'),
      ('Material','Insulating POM-C candidate; not approved')]
for i,(label,value) in enumerate(rows):
    yy=165+i*31
    if i%2==0:rect(504,yy-20,583,30,'#f3f6f8')
    text(512,yy,label,13,True);text(672,yy,value,13)
text(510,543,'Factory closure and service',18,True)
text(510,568,'Insert SIM with power off and the board seated in the lifted carrier.',13)
text(510,590,'Fit the key, inspect all tabs and cables, then close without force.',13)
rect(36,620,1051,136,'#f3f6f8','none',5)
notes=[
 'Dimensions describe the ambient prototype. Verify manufacturing limits and thermal expansion before ordering.',
 'The PCB remains captive within assigned bounds; shock, vibration, stiffness, wear and anti-rattle behavior need testing.',
 'Cable checks sample endpoint movement. They do not prove every continuous deformation or physical flex life.',
 'The pack is still an unapproved supplier request. Pack retention, harness/dock and firmware remain unfinished.',
 'No supplier message, order or physical water/dust qualification is implied by this drawing.'
]
for i,line in enumerate(notes):text(49,645+i*23,line,14)
text(36,780,'2026-10-26 | Units: mm | Plan schematic / dimensions govern | Prototype review | 1 / 1',13)
svg.append('</svg>')
(OUT/'retention-sheet.svg').write_text('\n'.join(svg)+'\n')
for kind in ['pdf','png']:
    subprocess.run(['rsvg-convert','--format',kind,'--output',str(OUT/f'retention-sheet.{kind}'),str(OUT/'retention-sheet.svg')],check=True)
print('Created r10 prototype retention drawing.')
