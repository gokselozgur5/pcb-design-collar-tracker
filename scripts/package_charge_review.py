#!/usr/bin/env python3
"""Deliver the source-bound r05l PCB and r07 enclosure review, not an order release."""
import argparse
import base64
import hashlib
import html
import io
import json
from pathlib import Path
import subprocess
import zipfile

from verify_charge_candidate import verify

ROOT=Path(__file__).resolve().parents[1]
TRIAL=ROOT/'experiments/power-r05l-charge-interlock'
MECH=ROOT/'mechanical/swim-r07-charge-interlock'
OUT=ROOT/'release/r05l-review'
PACKAGE=ROOT/'release/collar-tracker-r05l-review.zip'
RECEIPT=PACKAGE.with_suffix('.json')
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()


def verify_bundle():
    receipt=json.loads(RECEIPT.read_text())
    assert sha(PACKAGE)==receipt['zip_sha256']
    with zipfile.ZipFile(PACKAGE) as archive:
        assert archive.testzip() is None
        assert len(archive.namelist())==len(set(archive.namelist()))
        assert set(archive.namelist())=={x['archive_path'] for x in receipt['files']}|{'manifest.json'}
        assert json.loads(archive.read('manifest.json'))=={k:v for k,v in receipt.items() if k!='zip_sha256'}
        for entry in receipt['files']:
            data=archive.read(entry['archive_path'])
            assert len(data)==entry['bytes'] and hashlib.sha256(data).hexdigest()==entry['sha256']
            assert sha(ROOT/entry['repo_path'])==entry['sha256'],entry['repo_path']
    assert not receipt['production_release'] and not receipt['physical_ingress_test']
    return dict(result='PASS',package=str(PACKAGE),files=len(receipt['files']),sha256=receipt['zip_sha256'])


def page(name,title,subtitle,images,left,right,footer):
    svg=['<svg xmlns="http://www.w3.org/2000/svg" width="1600" height="1200" viewBox="0 0 1600 1200" font-family="Arial, sans-serif">']
    def rect(x,y,w,h,fill):svg.append(f'<rect x="{x}" y="{y}" width="{w}" height="{h}" fill="{fill}"/>')
    def text(x,y,value,size=23,color='#253442',bold=False):
        svg.append(f'<text x="{x}" y="{y}" font-size="{size}" fill="{color}" font-weight="{"bold" if bold else "normal"}">{html.escape(str(value))}</text>')
    rect(0,0,1600,1200,'#f4f6f8');rect(0,0,1600,120,'#183145')
    text(40,55,title,36,'white',True);text(40,95,subtitle,23,'#e3ebf0')
    for x,(path,label) in zip([40,820],images):
        rect(x,145,740,575,'white');text(x+20,185,label,24,bold=True)
        data=base64.b64encode(path.read_bytes()).decode()
        svg.append(f'<image x="{x+20}" y="205" width="700" height="500" preserveAspectRatio="xMidYMid meet" href="data:image/png;base64,{data}"/>')
    for x,lines,fill,color in [(40,left,'#e4f0e8','#18603c'),(820,right,'#fff1e8','#8d351f')]:
        rect(x,740,740,370,fill);text(x+20,782,lines[0],25,color,True)
        for i,line in enumerate(lines[1:]):text(x+20,824+36*i,line,20)
    for i,line in enumerate(footer):text(40,1144+34*i,line,17)
    svg.append('</svg>');path=OUT/(name+'.svg');path.write_text('\n'.join(svg)+'\n')
    for suffix in ['png','pdf']:
        subprocess.run(['rsvg-convert','-f',suffix,'-o',str(OUT/(name+'.'+suffix)),str(path)],check=True)


def build():
    result=verify();checkpoint=json.loads((TRIAL/'evidence/charge-checkpoint.json').read_text())
    plot=json.loads((OUT/'plot-receipt.json').read_text())
    assert plot['pcb_sha256']==result['source_sha256'] and plot['native_exit_codes']==[0,0]
    assert all(sha(OUT/p)==v for p,v in plot['files'].items())
    page('pcb-review','COLLAR TRACKER / r05l PCB REVIEW',
         'Charge interlock implemented. Two clean PCB DFM reports; assembled release remains on hold.',
         [(OUT/'top.png','TOP / native copper and silkscreen'),(OUT/'bottom.png','BOTTOM / mirrored component view')],
         ['VERIFIED PCB','40 × 32 mm / six Cu layers / 87 footprints',
          'Native DRC, ERC, connectivity and parity: zero findings',
          'Two JLC runs: 0 Danger / 0 Warning / 455 Good each',
          'Same ZIP, same rules, all 29 rows analyzed; SMT off',
          '81 fitted references / 44 exact candidate MPNs',
          '109 physical GND pads have local paths to vias',
          'Two GND planes; 154/154 signal-via return screens pass'],
         ['REQUIRED BEFORE WORKING DELIVERY',
          'Charge window is implemented; corner model is conditional.',
          'Thermal coupling, startup and fault transients need tests.',
          'Protected pack, NTC attachment and antennas: open.',
          'Firmware and factory programming/functional test: open.',
          'Procurement, CPL rotations and SMT acceptance: open.',
          'No physical powered, RF or water/dust result exists.',
          'This package is for review; it is not an order release.'],
         ['PCB SHA256: '+result['source_sha256'],'JLC records: '+' / '.join(result['supplier_records'])])
    page('enclosure-review','COLLAR TRACKER / r07 ENCLOSURE REVIEW',
         'Actual PCB placements and carrier clearance. Pack and antenna boxes remain reserved volumes.',
         [(MECH/'exploded.png','EXPLODED / shell, seal and populated envelopes'),(MECH/'section.png','SECTION / internal clearance model')],
         ['VERIFIED CAD GEOMETRY',
          '85 populated envelopes; four PCB thickness cases pass.',
          'New U12 relief and one moved support leg; 1 mm bridge.',
          'Actual CAD clearance intersection is empty.',
          'Previous carrier control has 1.234 mm³ interference.',
          'Eight exported parts: closed, oriented and connected.',
          'Rigid body + lid: 57.4 × 49.4 × 17.6 mm (key excluded).',
          'Boot envelope: 60.4 × 52.4 × 22.4 mm.'],
         ['WATER / DUST TARGET — UNQUALIFIED',
          'IP68 swimming/dust target; no physical test yet.',
          'Provisional immersion: 2 m fresh water / 60 minutes.',
          'Pack and antenna dimensions still need real selections.',
          'Material/seal grades and fastener torque remain open.',
          'Harness, dock wiring and positive PCB retention: open.',
          'Carrier strength and thermal coupling require tests.',
          'Grey/orange blocks are fit bounds, not qualified parts.'],
         ['Model: mechanical/swim-r07-charge-interlock; exact input hashes in mesh-checks.json.',
          'PCB and enclosure evidence are separate from assembled electrical and ingress acceptance.'])
    subprocess.run(['pdfunite',str(OUT/'pcb-review.pdf'),str(OUT/'enclosure-review.pdf'),str(OUT/'review.pdf')],check=True)
    (OUT/'START-HERE.txt').write_text(
        'COLLAR TRACKER r05l / r07 — PCB AND ENCLOSURE REVIEW\n\n'
        'Open review.pdf. Upload only gerber.zip to PCB DFM, not this outer archive.\n'
        'Two actual JLC runs: 0 Danger / 0 Warning / 455 Good, same bytes and rules.\n'
        'Native connectivity/DRC/ERC/parity: zero findings.\n'
        'The hardware charge-temperature interlock is now implemented.\n'
        'Model results are conditional; powered startup/thermal tests remain open.\n\n'
        'Native PCB and candidate BOM/CPL: experiments/power-r05l-charge-interlock/\n'
        'Enclosure CAD/STL/previews: mechanical/swim-r07-charge-interlock/\n'
        'Manufacturer sources and limits: assembly/charge-interlock-r01/\n'
        'Pack/NTC attachment, antennas, harness/dock/retention, firmware and factory tests remain open.\n'
        'No assembled, RF or physical IP68/water/dust qualification is claimed.\n'
        'This is not a working-PCBA order release.\n\n'
        'Continue from the repository STATUS and RESUME instructions:\n'
        'https://github.com/gokselozgur5/pcb-design-collar-tracker\n')
    payload={};entries=[]
    def add(name,path):
        assert name not in payload
        data=path.read_bytes();payload[name]=data
        entries.append(dict(archive_path=name,repo_path=str(path.relative_to(ROOT)),bytes=len(data),sha256=sha(path)))
    for name in ['review.pdf','pcb-review.png','enclosure-review.png','START-HERE.txt']:
        add(name,OUT/name)
    add('gerber.zip',ROOT/checkpoint['package'])
    for row in checkpoint['files']:
        p=TRIAL/row['path'];add(str(p.relative_to(ROOT)),p)
    for p in [TRIAL/'README.md',TRIAL/'evidence/charge-checkpoint.json']:
        add(str(p.relative_to(ROOT)),p)
    for folder in [MECH,ROOT/'assembly/charge-interlock-r01',ROOT/'assembly/pack-charge-r01']:
        for p in sorted(folder.rglob('*')):
            if p.is_file() and p.suffix!='.log':add(str(p.relative_to(ROOT)),p)
    manifest=dict(pcb_sha256=result['source_sha256'],gerber_zip_sha256=result['zip_sha256'],
                  supplier_records=result['supplier_records'],production_release=False,
                  physical_ingress_test=False,files=sorted(entries,key=lambda e:e['archive_path']))
    payload['manifest.json']=(json.dumps(manifest,indent=2)+'\n').encode()
    buffer=io.BytesIO()
    with zipfile.ZipFile(buffer,'w',compression=zipfile.ZIP_DEFLATED) as archive:
        for name,data in sorted(payload.items()):
            info=zipfile.ZipInfo(name,date_time=(2026,10,25,0,0,0));info.compress_type=zipfile.ZIP_DEFLATED
            info.external_attr=0o100644<<16;archive.writestr(info,data)
    data=buffer.getvalue()
    assert not PACKAGE.exists() or PACKAGE.read_bytes()==data,'Preserve earlier package; use a new revision'
    PACKAGE.write_bytes(data)
    RECEIPT.write_text(json.dumps({**manifest,'zip_sha256':sha(PACKAGE)},indent=2)+'\n')
    return verify_bundle()


if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--verify',action='store_true');a=p.parse_args()
    print(json.dumps(verify_bundle() if a.verify else build(),indent=2))
