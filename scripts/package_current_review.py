#!/usr/bin/env python3
"""Package the unchanged all-green PCB and the current conditional assembly study."""
import argparse
import hashlib
import io
import json
from pathlib import Path
import subprocess
import zipfile

import package_charge_review as drawing
from verify_charge_candidate import verify as verify_pcb
from verify_dock_wire_motion import verify as verify_wire

ROOT=Path(__file__).resolve().parents[1]
OUT=ROOT/'release/r14-current-review'
PACKAGE=ROOT/'release/collar-tracker-r05l-r14-review.zip'
RECEIPT=PACKAGE.with_suffix('.json')
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()


def verify_bundle():
    receipt=json.loads(RECEIPT.read_text())
    assert sha(PACKAGE)==receipt['zip_sha256']
    assert not receipt['production_release'] and not receipt['physical_ingress_test']
    with zipfile.ZipFile(PACKAGE) as archive:
        assert archive.testzip() is None
        assert len(archive.namelist())==len(set(archive.namelist()))
        assert set(archive.namelist())=={x['archive_path'] for x in receipt['files']}|{'manifest.json'}
        assert json.loads(archive.read('manifest.json'))=={k:v for k,v in receipt.items() if k!='zip_sha256'}
        for entry in receipt['files']:
            data=archive.read(entry['archive_path'])
            assert len(data)==entry['bytes'] and hashlib.sha256(data).hexdigest()==entry['sha256']
            assert sha(ROOT/entry['repo_path'])==entry['sha256'],entry['repo_path']
    return dict(result='PASS',package=str(PACKAGE),files=len(receipt['files']),sha256=receipt['zip_sha256'])


def build():
    pcb,wire=verify_pcb(),verify_wire(check_baseline=False)
    OUT.mkdir(parents=True,exist_ok=True)
    previous=drawing.OUT;drawing.OUT=OUT
    try:
        drawing.page('pcb-review','COLLAR TRACKER / VERIFIED PCB',
            'r05l PCB DFM is complete. A fully assembled, working tracker is not released.',
            [(ROOT/'release/r05l-review/top.png','TOP / 40 x 32mm'),
             (ROOT/'release/r05l-review/bottom.png','BOTTOM / mirrored view')],
            ['VERIFIED / UNCHANGED',
             'Six copper layers; physical nano-SIM.',
             'Native DRC / ERC / opens / parity: zero findings.',
             'Both JLC PCB runs: 0 Danger / 0 Warning / 455 Good.',
             'Same ZIP and rules; all 29 rows analyzed; SMT off.',
             '81 fitted references / 44 candidate MPNs.',
             '109 physical GND pads have local via paths.',
             'Independent hardware hot/cold charge interlock.'],
            ['REMAINING BEFORE A WORKING-DEVICE ORDER',
             'Protected pack and lead-exit approval.',
             'Dock holding and wire-end restraint.',
             'Internal contact lugs / J3 wiring and joining process.',
             'Factory sourcing, CPL rotation and SMT review.',
             'Firmware, programming and functional tests.',
             'Powered / RF / physical water and dust tests.',
             'No purchase, supplier message or physical test made.'],
            ['Gerber SHA256: '+pcb['zip_sha256'],
             'JLC records: '+' / '.join(pcb['supplier_records'])])
        drawing.page('assembly-review','COLLAR TRACKER / CURRENT ASSEMBLY STUDY',
            'Conditional geometry. Pack supplier response, factory assembly and physical validation remain open.',
            [(ROOT/'mechanical/swim-r12-pack-retention/pack_review.png','r12 / requested pack and retaining cap'),
             (ROOT/'mechanical/swim-r14-wire-motion/mounted.png','r13 shell / r14 dock; lid and internals omitted')],
            ['CURRENT MODEL',
             'Rigid shell + lid: 57.4 x 49.4 x 21.0mm.',
             'Body including external key: 61.4mm in X.',
             'Boot: 60.4 x 52.4 x 25.8mm.',
             'r12 carrier/cap; r11 lid, frame, boot and seals.',
             'r13 shell/key; r14 dock: 94 x 36 x 16mm.',
             'Constant-length pigtails; continuous radius >=8.696mm.',
             'Full wire-family / housing CAD intersection empty.'],
            ['LIMITS / DO NOT ORDER AS A FINISHED DEVICE',
             'Requested pack: 32 x 30.5 x 5.3mm maximum.',
             'That pack envelope is not supplier approved.',
             'Free-wire geometry does not constrain real buckling.',
             'Contact holding / clamp / cycle-life tests remain open.',
             'Charging is a dry indoor prototype only.',
             'IP68 is a target, not a certified or measured result.',
             '2m fresh water / 60min is an engineering assumption.'],
            ['Parts in this review are explicitly revision-mapped; previous releases remain preserved.',
             'Open the repository STATUS / RESUME for the exact source, commands and remaining work.'])
    finally:drawing.OUT=previous
    subprocess.run(['pdfunite',str(OUT/'pcb-review.pdf'),str(OUT/'assembly-review.pdf'),
                    str(ROOT/'mechanical/swim-r14-wire-motion/wire-motion-sheet.pdf'),str(OUT/'review.pdf')],check=True)
    (OUT/'START-HERE.txt').write_text(
        'COLLAR TRACKER — r05l PCB / r14 CURRENT REVIEW\n\n'
        'Open review.pdf first. Upload only gerber.zip to PCB DFM, not this outer ZIP.\n'
        'The unchanged Gerber passed two actual JLC PCB DFM runs at 0 Danger /\n'
        '0 Warning / 455 Good each. SMT analysis was off.\n\n'
        'This is a review package, NOT an order release or a complete working device.\n'
        'PCB DFM, mechanical fit, SMT assembly, functional operation and IP68 are\n'
        'separate acceptance steps. No powered / RF / physical ingress test exists.\n\n'
        'Current wearable part sources:\n'
        '  body: r13 (r12 cradle plus r13 external key)\n'
        '  carrier/cap: r12\n'
        '  lid, retainer, boot, contacts, contact seals and magnet plugs: r11\n'
        '  external dry-dock halves: r14\n'
        'STLs use their documented export frames; they are not pre-positioned\n'
        'assembly files. Use the repository SCAD sources for assembly coordinates.\n\n'
        'Remaining: pack supplier approval and lead exit; dock holding and wire-end\n'
        'restraint; internal lugs/J3 wiring; factory terminations and source/fault\n'
        'behavior; sourcing/SMT; firmware; assembled powered/RF/water/dust tests.\n'
        'The battery enquiry remains unsent. No order/payment is authorized.\n\n'
        'Editable source and reproducible verification:\n'
        'https://github.com/gokselozgur5/pcb-design-collar-tracker\n'
        'Read docs/STATUS.md and docs/RESUME.md. This ZIP is a review selection,\n'
        'not a replacement for a complete repository checkout.\n')
    entries=[];payload={}
    def add(archive_name,path):
        assert archive_name not in payload
        payload[archive_name]=path.read_bytes()
        entries.append(dict(archive_path=archive_name,repo_path=str(path.relative_to(ROOT)),
                            bytes=len(payload[archive_name]),sha256=sha(path)))
    for name in ['review.pdf','START-HERE.txt','pcb-review.png','assembly-review.png']:
        add(name,OUT/name)
    trial=ROOT/'experiments/power-r05l-charge-interlock'
    add('gerber.zip',trial/'evidence/collar-tracker-05l-charge-final4-40x32-dfm.zip')
    for p in sorted((trial/'hardware').iterdir()):
        if p.suffix in {'.kicad_pcb','.kicad_sch','.kicad_pro','.kicad_dru'}:add('pcb-source/'+p.name,p)
    for name in ['candidate-bom.csv','candidate-cpl.csv','native-positions.csv']:
        add('pcb-assembly/'+name,trial/'assembly'/name)
    for i in [1,2]:
        folder=trial/f'evidence/jlc-check{i}'
        for name in ['report.pdf','receipt.json','rules.json','summary.json','rows.txt']:
            add(f'pcb-dfm/check{i}/'+name,folder/name)
    dock=ROOT/'mechanical/swim-r14-wire-motion'
    checkpoint=json.loads((dock/'checkpoint.json').read_text())
    for name in checkpoint['files']:
        p=ROOT/name
        if p.parent==dock:add('dock-r14/'+p.name,p)
    add('dock-r14/checkpoint.json',dock/'checkpoint.json')
    mapping={'body.stl':'swim-r13-charge-dock','carrier.stl':'swim-r12-pack-retention',
             **{name:'swim-r11-thermal-fit' for name in ['lid.stl','retainer.stl','boot.stl','contact.stl','contact_seal.stl','magnet_plug.stl']}}
    for name,revision in mapping.items():add('wearable-meshes/'+name,ROOT/'mechanical'/revision/name)
    for name in ['request-sheet.pdf','supplier-request.txt','README.md']:
        add('battery-request/'+name,ROOT/'assembly/pack-r03'/name)
    for name in ['STATUS.md','RESUME.md']:
        add('handoff/'+name,ROOT/'docs'/name)
    manifest=dict(production_release=False,physical_ingress_test=False,
                  pcb_sha256=pcb['source_sha256'],gerber_zip_sha256=pcb['zip_sha256'],
                  supplier_records=pcb['supplier_records'],dock_revision=wire['revision'],
                  wearable_mesh_revisions=mapping,files=sorted(entries,key=lambda x:x['archive_path']))
    payload['manifest.json']=(json.dumps(manifest,indent=2)+'\n').encode()
    buffer=io.BytesIO()
    with zipfile.ZipFile(buffer,'w',compression=zipfile.ZIP_DEFLATED) as archive:
        for name,data in sorted(payload.items()):
            info=zipfile.ZipInfo(name,date_time=(2026,10,26,0,0,0));info.compress_type=zipfile.ZIP_DEFLATED
            info.external_attr=0o100644<<16;archive.writestr(info,data)
    data=buffer.getvalue()
    assert not PACKAGE.exists() or PACKAGE.read_bytes()==data,'Preserve earlier delivery; use a successor filename'
    PACKAGE.write_bytes(data)
    RECEIPT.write_text(json.dumps({**manifest,'zip_sha256':sha(PACKAGE)},indent=2)+'\n')
    return verify_bundle()


if __name__=='__main__':
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--verify',action='store_true');args=parser.parse_args()
    print(json.dumps(verify_bundle() if args.verify else build(),indent=2))
