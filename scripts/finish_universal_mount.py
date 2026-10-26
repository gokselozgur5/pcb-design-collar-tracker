#!/usr/bin/env python3
"""Produce the dimension summary, length screen and portable design archive."""
import base64
import hashlib
import json
import math
from pathlib import Path
import re
import subprocess
import zipfile

ROOT=Path(__file__).resolve().parents[1]
OUT=ROOT/'mechanical/universal-mount-r01'
ARCHIVE=ROOT/'release/collar-tracker-3d-universal-mount-r01.zip'

def closure_screen():
    cases=json.loads((OUT/'fit-checks.json').read_text())['cases'];rows=[]
    for name,v in cases.items():
        if v.get('round_collar'):
            dia=v['rope_diameter'];r=dia/2+.9;zc=-6.8-dia/2*math.sqrt(2)
            points=[(-5.5,-1.5),(5.5,-1.5),(5.5,-6.5)]+[(r*math.sin(math.radians(a)),zc+r*math.cos(math.radians(a))) for a in range(35,326,10)]+[(-5.5,-6.5)]
        else:
            w=v['collar_width'];t=v['collar_thickness'];z=-7.8
            points=[(-5.5,-1.5),(5.5,-1.5),(5.5,-6.5),(max(w/2+.9,6),z+.8),(w/2+1.2,z-t-.2),(w/2-.4,z-t-1),(-w/2+.4,z-t-1),(-w/2-1.2,z-t-.2),(-max(w/2+.9,6),z+.8),(-5.5,-6.5)]
        c=sum(math.dist(a,b) for a,b in zip(points,points[1:]+points[:1]))
        loop=25+5*math.floor((c-25)/5);h1=loop+7;h2=h1+5
        length=120 if c+29<=120 else 220
        row={'case':name,'installed_centreline_mm':round(c,3),'two_holes_y_mm':[h1,h2],
             'unstrained_loop_mm':loop,'demanded_extension_percent':round((c/loop-1)*100,2),
             'strap_length_mm':length,'tail_beyond_keeper_mm':round(length-(c+24),3)}
        assert 32<=h1<h2<=length-8 and row['tail_beyond_keeper_mm']>=5
        rows.append(row)
    (OUT/'closure-screen.json').write_text(json.dumps({'scope':'Length-only screen of the parametric routing. Hole/button spacing is 5 mm; calculated strain is a demand, not material or retention evidence. Keeper ends 24 mm after the leading strap tip; leave at least 5 mm tail past it. Installed envelopes omit overlapping tail, clasp deformation and contact pressure.','cases':rows},indent=2)+'\n')

def overview():
    panels=[('render-mounted.png','01 / ON THE COLLAR','Rigid housing 57.4 × 49.4 × 21 mm · outer holder 60.8 × 52.8 × 27.3 mm'),
            ('render-exploded.png','02 / INSIDE THE ENCLOSURE','Battery cradle · 40 × 32 mm PCB · antenna envelopes · gasket · lid'),
            ('render-underside.png','03 / ADJUSTABLE ATTACHMENT','Two wrap straps · flat or V-groove pad · 120 / 220 mm strap options'),
            ('pcb-top.png','04 / CURRENT PCB','KiCad r05m render · four package bodies use dimensional substitutes')]
    svg=['<svg xmlns="http://www.w3.org/2000/svg" xmlns:xlink="http://www.w3.org/1999/xlink" width="2000" height="1590" viewBox="0 0 2000 1590">',
         '<rect width="2000" height="1590" fill="#f4f7f2"/>',
         '<g font-family="Helvetica,Arial,sans-serif" fill="#213b2e">',
         '<text x="60" y="52" font-size="17" letter-spacing="3">COLLAR TRACKER / UNIVERSAL MOUNT R01</text>',
         '<text x="60" y="107" font-size="40" font-weight="bold">PCB, enclosure and adjustable collar attachment</text>',
         '<text x="60" y="143" font-size="19" fill="#617367">Prototype CAD · actual design geometry · dimensions in millimetres</text>']
    for i,(file,title,caption) in enumerate(panels):
        x=60+(i%2)*960;y=185+(i//2)*670
        encoded=base64.b64encode((OUT/file).read_bytes()).decode()
        svg += [f'<rect x="{x}" y="{y}" width="920" height="635" rx="14" fill="#e9eeeb"/>',
                f'<image x="{x+10}" y="{y+12}" width="900" height="535" preserveAspectRatio="xMidYMid meet" xlink:href="data:image/png;base64,{encoded}"/>',
                f'<text x="{x+23}" y="{y+580}" font-size="19" font-weight="bold">{title}</text>',
                f'<text x="{x+23}" y="{y+611}" font-size="16" fill="#536c5d">{caption}</text>']
    svg += ['<text x="60" y="1560" font-size="17" fill="#617367">Checked examples: flat 8 × 1, 25 × 3, 60 × 8 mm; round Ø4, Ø8, Ø16 mm. Grip, comfort and IP68 need physical qualification.</text>','</g></svg>']
    file=OUT/'design-overview.svg';file.write_text('\n'.join(svg)+'\n')
    subprocess.run(['rsvg-convert','-o',str(OUT/'design-overview.png'),str(file)],check=True)
    subprocess.run(['rsvg-convert','-f','pdf','-o',str(OUT/'design-overview.pdf'),str(file)],check=True)

def package():
    files={p for p in OUT.rglob('*') if p.is_file() and p.name not in ['delivery.json','.DS_Store']}
    # Preserve repository-relative imports, so the delivered CAD opens offline.
    for rel in re.findall(r'import\("([^"]+)"\)',(OUT/'mount.scad').read_text()):
        p=(OUT/rel).resolve();assert p.is_relative_to(ROOT) and p.is_file();files.add(p)
    inventory={str(p.relative_to(ROOT)):hashlib.sha256(p.read_bytes()).hexdigest() for p in sorted(files)}
    with zipfile.ZipFile(ARCHIVE,'w',zipfile.ZIP_DEFLATED,compresslevel=9) as z:
        z.writestr('START-HERE.txt','Open mechanical/universal-mount-r01/viewer.html to inspect the design offline.\nRead mechanical/universal-mount-r01/README.md for dimensions, part selection and prototype limits.\nThe adjustable mount CAD is mechanical/universal-mount-r01/mount.scad. All its mesh imports are included.\nThis archive is a 3D prototype design package, not an approved PCB or product order release.\n')
        z.writestr('manifest.json',json.dumps(inventory,indent=2)+'\n')
        for p in sorted(files):z.write(p,str(p.relative_to(ROOT)))
    with zipfile.ZipFile(ARCHIVE) as z:
        assert z.testzip() is None
        for name,digest in inventory.items():assert hashlib.sha256(z.read(name)).hexdigest()==digest
    delivery={'archive':str(ARCHIVE.relative_to(ROOT)),'sha256':hashlib.sha256(ARCHIVE.read_bytes()).hexdigest(),'bytes':ARCHIVE.stat().st_size,'file_count':len(inventory),'scope':'Portable prototype CAD, STL, offline viewer, images and nominal checks; no manufacturing or physical qualification.'}
    (OUT/'delivery.json').write_text(json.dumps(delivery,indent=2)+'\n');print(json.dumps(delivery))

if __name__=='__main__':
    closure_screen();overview();package()
