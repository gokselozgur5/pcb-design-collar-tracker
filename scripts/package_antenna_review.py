#!/usr/bin/env python3
"""Deliver unchanged r05l PCB evidence with the conditional r08 assembly review."""
import argparse
import hashlib
import io
import json
from pathlib import Path
import subprocess
import zipfile

import package_charge_review as previous
from verify_antenna_candidate import verify as verify_assembly
from verify_charge_candidate import verify as verify_pcb

ROOT=Path(__file__).resolve().parents[1]
MECH=ROOT/'mechanical/swim-r08-antennas'
TRIAL=ROOT/'experiments/power-r05l-charge-interlock'
OUT=ROOT/'release/r08-assembly-review'
PACKAGE=ROOT/'release/collar-tracker-r05l-r08-review.zip'
RECEIPT=PACKAGE.with_suffix('.json')
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()


def verify_bundle():
    receipt=json.loads(RECEIPT.read_text())
    assert sha(PACKAGE)==receipt['zip_sha256']
    with zipfile.ZipFile(PACKAGE) as archive:
        assert archive.testzip() is None
        assert len(archive.namelist())==len(set(archive.namelist()))
        assert set(archive.namelist())=={e['archive_path'] for e in receipt['files']}|{'manifest.json'}
        assert json.loads(archive.read('manifest.json'))=={k:v for k,v in receipt.items() if k!='zip_sha256'}
        for entry in receipt['files']:
            data=archive.read(entry['archive_path'])
            assert len(data)==entry['bytes'] and hashlib.sha256(data).hexdigest()==entry['sha256']
            assert sha(ROOT/entry['repo_path'])==entry['sha256'],entry['repo_path']
    assert not receipt['production_release'] and not receipt['physical_ingress_test']
    return dict(result='PASS',package=str(PACKAGE),files=len(receipt['files']),sha256=receipt['zip_sha256'])


def build():
    assembly,pcb=verify_assembly(),verify_pcb()
    OUT.mkdir(parents=True,exist_ok=True)
    old_output=previous.OUT
    previous.OUT=OUT
    try:
        previous.page('pcb-review','COLLAR TRACKER / r05l PCB REVIEW',
            'Two actual all-green PCB DFM reports. Working-device release remains on hold.',
            [(ROOT/'release/r05l-review/top.png','TOP / copper and silkscreen'),
             (ROOT/'release/r05l-review/bottom.png','BOTTOM / mirrored component view')],
            ['VERIFIED PCB / UNCHANGED',
             '40 x 32 mm / six Cu layers / 87 footprints.',
             'Native DRC, ERC, connectivity and parity: zero findings.',
             'JLC: 0 Danger / 0 Warning / 455 Good in both runs.',
             'Same ZIP, unchanged rules, all 29 rows; SMT off.',
             '81 fitted references / 44 exact candidate MPNs.',
             '109 physical GND pads have local via paths.',
             'Two GND planes; 154/154 signal-via return screens.'],
            ['REQUIRED BEFORE WORKING DELIVERY',
             'Hardware charge-temperature interlock is implemented.',
             'Its thermal/startup model still needs powered tests.',
             'Protected pack and NTC attachment are unselected.',
             'r08 prototype antenna/cable model: see next page.',
             'Firmware, factory programming and functional tests: open.',
             'Procurement, CPL rotations and SMT acceptance: open.',
             'This package is for review, not an order release.'],
            ['PCB SHA256: '+pcb['source_sha256'],
             'JLC records: '+' / '.join(pcb['supplier_records'])])
        previous.page('assembly-review','COLLAR TRACKER / r08 ASSEMBLY REVIEW',
            'Prototype antennas and routed cables. The all-green r05l PCB is unchanged.',
            [(MECH/'routing.png','LTE + GNSS / actual connector positions'),
             (MECH/'section.png','SECTION / seal, carrier and cable guides')],
            ['CHECKED MODEL / CONDITIONAL',
             'CAPH LTE + ZETA GNSS; standard 100 mm cable candidates.',
             '85 populated envelopes; four PCB thickness cases.',
             'Separate cable paths and four internal lid guides.',
             'CAD guide interference empty; undersized control fails.',
             'Eight closed meshes; five inspected assembly views.',
             'Rigid shell + lid: 57.4 x 49.4 x 20.6 mm.',
             'Boot: 60.4 x 52.4 x 25.4 mm. Key adds 1.3 mm.'],
            ['WORKING-DEVICE RELEASE STILL ON HOLD',
             'Protected pack / NTC attachment: not selected.',
             'Cable end datums and length tolerance fit: open.',
             'Exact coax bend limit and feed bond: open.',
             'Clip strength and opening/service motion: untested.',
             'PCB retention, dock/harness and factory firmware: open.',
             'No powered, RF or physical water/dust test exists.',
             'IP68 is a design target, not an achieved rating.'],
            ['PCB SHA256: '+pcb['source_sha256'],
             'Two preserved JLC runs: 0 Danger / 0 Warning / 455 Good each. SMT was not analyzed.'])
    finally:
        previous.OUT=old_output
    subprocess.run(['pdfunite',str(OUT/'pcb-review.pdf'),str(OUT/'assembly-review.pdf'),str(OUT/'review.pdf')],check=True)
    (OUT/'START-HERE.txt').write_text(
        'COLLAR TRACKER r05l PCB / r08 ANTENNA ASSEMBLY\n\n'
        'Open review.pdf for the current two-page review.\n'
        'Upload only gerber.zip to PCB DFM, not this outer review archive.\n'
        'The Gerber is unchanged: two actual 0 Danger / 0 Warning / 455 Good JLC runs.\n'
        'There was no new JLC upload for this mechanical-only revision.\n\n'
        'r08 replaces antenna placeholders and adds conditional cable routes/lid guides.\n'
        'The battery is still a reservation. Cable tolerances, feed construction,\n'
        'clip strength, materials, RF, firmware and physical ingress need qualification.\n'
        'This is not an order release or a completed working device.\n\n'
        'Native sources, reproducible checks and continuation:\n'
        'https://github.com/gokselozgur5/pcb-design-collar-tracker\n'
        'Read docs/STATUS.md and docs/RESUME.md in the repository.\n')
    checkpoint=json.loads((TRIAL/'evidence/charge-checkpoint.json').read_text())
    payload={};entries=[]
    def add(name,path):
        assert name not in payload
        data=path.read_bytes();payload[name]=data
        entries.append(dict(archive_path=name,repo_path=str(path.relative_to(ROOT)),bytes=len(data),sha256=sha(path)))
    for name in ['review.pdf','assembly-review.png','START-HERE.txt']:
        add(name,OUT/name)
    add('gerber.zip',ROOT/checkpoint['package'])
    for row in checkpoint['files']:
        p=TRIAL/row['path'];add(str(p.relative_to(ROOT)),p)
    for p in [TRIAL/'README.md',TRIAL/'evidence/charge-checkpoint.json']:
        add(str(p.relative_to(ROOT)),p)
    for folder in [MECH,ROOT/'assembly/pack-antenna-r02']:
        for p in sorted(folder.rglob('*')):
            if p.is_file():add(str(p.relative_to(ROOT)),p)
    manifest=dict(pcb_sha256=pcb['source_sha256'],gerber_zip_sha256=pcb['zip_sha256'],
                  supplier_records=pcb['supplier_records'],mechanical_revision=assembly['revision'],
                  production_release=False,physical_ingress_test=False,
                  files=sorted(entries,key=lambda e:e['archive_path']))
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
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--verify',action='store_true');args=p.parse_args()
    print(json.dumps(verify_bundle() if args.verify else build(),indent=2))
