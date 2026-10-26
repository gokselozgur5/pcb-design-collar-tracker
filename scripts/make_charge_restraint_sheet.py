#!/usr/bin/env python3
"""Two factory-review sheets from the actual r19 geometry and measured outputs."""
import base64
import hashlib
import json
from pathlib import Path
import subprocess
from xml.sax.saxutils import escape

ROOT=Path(__file__).resolve().parents[1]
OUT=ROOT/'assembly/internal-charge-r03'
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()


def main():
    spec=json.loads((OUT/'restraint.json').read_text())
    cad=json.loads((OUT/'cad-checks.json').read_text())
    report=json.loads((OUT/'checks.json').read_text())
    headers='<svg xmlns="http://www.w3.org/2000/svg" xmlns:xlink="http://www.w3.org/1999/xlink" width="297mm" height="210mm" viewBox="0 0 297 210"><rect width="297" height="210" fill="white"/>'
    def text(x,y,s,size=3.1,weight='normal',colour='#182b39'):
        return f'<text x="{x}" y="{y}" font-family="DejaVu Sans,sans-serif" font-size="{size}" font-weight="{weight}" fill="{colour}">{escape(s)}</text>'
    def photo(name,x,y,w,h):
        data=base64.b64encode((OUT/name).read_bytes()).decode()
        return f'<image x="{x}" y="{y}" width="{w}" height="{h}" xlink:href="data:image/png;base64,{data}"/>'
    common=text(10,12,'CT-INTERNAL-CHARGE-003-A / R19',5,'bold')+text(10,19,'PROTOTYPE REVIEW - manufacturing and physical qualification HOLD',3.5,'bold','#b74418')
    one=headers+common+photo('restraint-preview.png',5,24,164,109)
    one+=text(172,30,'DISPENSING ENVELOPES / mm',3.5,'bold')
    y=38
    for p in spec['patches']:
        one+=text(172,y,p['id'],3.2,'bold');y+=6
        for axis,i in [('X',0),('Y',1),('Z',2)]:
            one+=text(174,y,f'{axis}: {p["low_mm"][i]:.3f} to {p["high_mm"][i]:.3f}');y+=5
        y+=3
    lines=['Dimensions use the assembled enclosure frame. Total placement/service allowance +/-0.05mm.',
           'The PCB owns one shared insulating block. Each metal terminal owns a separate block.',
           'PTFE adhesion is not relied on. Inspect both solder joints before covering them.',
           f'{report["passing_poses"]}/27 static poses pass; 52 added checks per pose. Minimum component gap: 0.22mm.',
           'The geometry does not establish bond strength, continuous motion or a production process.',
           'Factory trial: lid open, battery absent, 21..25C / 40..60% RH / >=168h plus passing witnesses.',
           'Handling qualification target: 0.5N for 60s, anchor movement <=0.03mm. Not yet tested.',
           'Use restraint.json and README.md for covered lengths, substrate tests and release requirements.']
    for i,line in enumerate(lines):one+=text(10,141+6*i,line)
    one+=text(10,202,'1 / 2 | Nominal CAD illustration. No order, supplier approval or physical test is recorded.',2.6)
    one+='</svg>'
    two=headers+common
    for i,tool in enumerate(cad['forming_tools']):
        x=7+145*i;col=tool['colour'];size=tool['size_mm']
        two+=photo(col+'-fixture-preview.png',x,25,138,92)
        two+=text(x+4,121,col.upper()+' FORMING NEST',3.5,'bold')
        two+=text(x+4,128,f'Overall: {size[0]:.2f} x {size[1]:.2f} x {size[2]:.2f}mm')
        two+=text(x+4,134,f'Centerline reference: {tool["wire_length_mm"]:.4f}mm')
        two+=text(x+4,140,f'Bounded tool clearance: {tool["minimum_clearance_bound_mm"]:.4f}mm')
    lines=['The tools sit on a bench and are removed before final assembly. They do not fit inside the collar.',
           'Channels are open vertically. Lift the wire straight out, then inspect released shape and springback.',
           'Maximum wire OD 0.6604mm; tool tolerance +/-0.05mm. Tool material/process must meet that tolerance.',
           'Strip 1.8 +/-0.1mm at the terminal and 2.4 +/-0.1mm at the PCB. Verify actual ends in assembly.',
           'The recorded curve lengths are not a qualified cut-length tolerance. Do not stretch wires to fit.',
           'Confirm lid installation, adhesive deformation and cyclic motion on samples before release.']
    for i,line in enumerate(lines):two+=text(10,153+6*i,line)
    two+=text(10,202,'2 / 2 | Green PCB DFM does not cover tool accuracy, factory wiring, operating function or IP68.',2.6)
    two+='</svg>'
    files=[]
    for i,svg in enumerate([one,two],1):
        src=OUT/f'restraint-sheet-{i}.svg';dest=OUT/f'restraint-sheet-{i}.pdf';src.write_text(svg)
        subprocess.run(['rsvg-convert','-f','pdf','-o',str(dest),str(src)],check=True);files.extend([src,dest])
    pdf=OUT/'restraint-sheet.pdf'
    subprocess.run(['pdfunite',str(OUT/'restraint-sheet-1.pdf'),str(OUT/'restraint-sheet-2.pdf'),str(pdf)],check=True)
    dependencies=[OUT/n for n in ['restraint.json','checks.json','cad-checks.json',*cad['previews']]]+[Path(__file__)]
    (OUT/'drawing-checks.json').write_text(json.dumps(dict(inputs={str(p.relative_to(ROOT)):sha(p) for p in dependencies},
        files={p.name:sha(p) for p in files+[pdf]},physical_qualification=False),indent=2)+'\n')
    print(pdf)


if __name__=='__main__':
    main()
