#!/usr/bin/env python3
"""Package real KiCad Gerber/Excellon outputs, with DRC status and hashes."""
from pathlib import Path
import argparse,hashlib,json,shutil,subprocess,zipfile,sys
ROOT=Path(__file__).resolve().parents[1]
parser=argparse.ArgumentParser()
parser.add_argument('--revision',default='0.2.1',choices=['0.2','0.2.1'])
args=parser.parse_args()
PCB=ROOT/'hardware/collar-tracker.kicad_pcb'
OUT=ROOT/('release/collar-tracker-'+args.revision+'-dfm')
OUT.mkdir(parents=True,exist_ok=True)
CLI=ROOT/'scripts/kicad-cli'
DRC=ROOT/'evidence/pcb-final-drc.json'
with (ROOT/'evidence/dfm-export.log').open('w') as log:
    def run(*args):
        subprocess.run([str(CLI),*map(str,args)],cwd=ROOT,stdout=log,stderr=subprocess.STDOUT,check=True)
    if args.revision=='0.2':
        original=json.loads((OUT/'DRC-summary.json').read_text())['pcb_sha256']
        if hashlib.sha256(PCB.read_bytes()).hexdigest()!=original:
            raise SystemExit('Refusing to overwrite the original 0.2 package with a different PCB. Use the current revision.')
    if args.revision=='0.2.1':
        subprocess.run([str(ROOT/'scripts/kicad-python'),str(ROOT/'scripts/dfm_geometry.py'),str(PCB),str(ROOT/'evidence/jlc-dfm-20261024/geometry-after.json')],cwd=ROOT,stdout=log,stderr=subprocess.STDOUT,check=True)
        subprocess.run([str(ROOT/'.venv-dfm/bin/python'),str(ROOT/'scripts/check_dfm_geometry.py')],cwd=ROOT,stdout=log,stderr=subprocess.STDOUT,check=True)
    run('pcb','drc','--format','json','--severity-all','--schematic-parity','--all-track-errors','-o',DRC,PCB)
    drc=json.loads(DRC.read_text())
    errors=[v for v in drc['violations'] if v['severity']=='error']
    opens=drc['unconnected_items'];parity=drc.get('schematic_parity',[])
    if errors or opens or any(v['severity']=='error' for v in parity):
        raise SystemExit(f'Export blocked: {len(errors)} DRC errors, {len(opens)} opens, {len(parity)} parity findings. Inspect {DRC}.')
    run('pcb','export','gerbers','-l','F.Cu,In1.Cu,In2.Cu,B.Cu,F.Mask,B.Mask,F.SilkS,B.SilkS,F.Paste,B.Paste,Edge.Cuts','--use-drill-file-origin','--subtract-soldermask','-o',OUT,PCB)
    run('pcb','export','drill','--format','excellon','--drill-origin','plot','--excellon-separate-th','--generate-report','--report-path',OUT/'drill-report.txt','-o',OUT,PCB)
note='''COLLAR TRACKER REVISION — DFM REVIEW ONLY — NOT RELEASED FOR ORDER

Board outline: 30 x 22 mm. Copper layers: 4. Proposed total thickness: 0.8 mm.
Layer order: F.Cu, In1.Cu, In2.Cu, B.Cu. All contain signal routes and GND fill.
Inner layers are NOT uninterrupted ground reference planes in this draft.
Nominal signal width: 0.15 mm; permitted local neckdown minimum: 0.10 mm.
Clearance: 0.10 mm. These are provisional geometric rules, not power-integrity validation.
Through vias: 0.45 mm copper diameter / 0.20 mm drill, tented.
Finish candidate: ENIG. No controlled-impedance stackup has been approved.
Gerber and drill coordinates use the same lower-left auxiliary origin.

This package is for the fabricator's geometry/manufacturability analyzer.
Its checks cannot validate the circuit, radio or battery system.

OPEN DESIGN ITEMS BEFORE FABRICATION:
- Hardware undervoltage cutoff and nRF9151 VDD_GPIO sequencing.
- Operator/eUICC profile and actual eSIM package. J6 is an external SIM
  contact interface, NOT an onboard eSIM IC.
- Health sensor/contact method. J5 is a digital expansion interface only.
- Battery/NTC/charging-input protection and pulse-current suitability.
- LTE/GNSS antennas, RF stackup, matching, ground-return review and body effects.
- The community nRF land pattern has a pin-1 copper difference versus
  the examined Nordic DK revision; reconcile against the current package drawing.
- Assembly/stencil review, enclosure fit and physical bring-up.

No purchase, supplier upload, assembly qualification or physical test was performed.
See DRC-summary.json for the exact local findings accompanying this export.
'''
note=note.replace('REVISION',args.revision,1)
if args.revision=='0.2.1':
    note+='''
JLC REPORT FOLLOW-UP (original report 2026-10-24 20:24:49, revision 0.2):
- J4 battery contact row moved 0.20 mm; closest battery via/pad gap is 0.225 mm.
- J1/J2 U.FL apertures expanded 0.05 mm to join the existing central opening.
  The original copper-free connector keepout remains. Each connector explicitly
  permits this intended shared solder-mask aperture in KiCad; no global DRC
  exclusions or severity reductions were added.
- Dense component outlines/orientation graphics moved from silk to Fab.
  Board/interface labels remain, with 1.0 mm text and 0.15 mm strokes.
- U2 center pad now uses only copper; its existing separate mask/paste graphics
  remain, replacing the invalid negative-margin representation.
- Library-footprint mismatch warnings record these intentional local changes.
  The new package has NOT been run through JLCDFM. Local checks do not prove
  that every warning or the two pad-spacing danger examples in the PDF is gone;
  the PDF contains no per-occurrence coordinates. Re-upload and inspect results.
'''
(OUT/'READ-ME-DFM-ONLY.txt').write_text(note)
summary={'errors':len(errors),'unconnected':len(opens),'schematic_parity':parity,
         'warnings':[v for v in drc['violations'] if v['severity']=='warning'],
         'pcb_sha256':hashlib.sha256(PCB.read_bytes()).hexdigest()}
(OUT/'DRC-summary.json').write_text(json.dumps(summary,indent=2)+'\n')
if args.revision=='0.2.1':
    shutil.copy2(ROOT/'evidence/jlc-dfm-20261024/geometry-verification.json',OUT/'LOCAL-GEOMETRY-CHECKS.json')
files=[p for p in OUT.iterdir() if p.is_file() and p.name!='SHA256SUMS.txt']
assert all(any(p.suffix.lower()==ext for p in files) for ext in ['.gtl','.gbl','.g1','.g2','.gts','.gbs','.drl']), [p.name for p in files]
assert any(p.suffix.lower() in ['.gm1','.gko'] for p in files), 'Missing board outline'
(OUT/'SHA256SUMS.txt').write_text(''.join(hashlib.sha256(p.read_bytes()).hexdigest()+'  '+p.name+'\n' for p in sorted(files)))
target=OUT.parent/(OUT.name+'.zip')
with zipfile.ZipFile(target,'w',zipfile.ZIP_DEFLATED) as z:
    for p in sorted(OUT.iterdir()):
        if p.is_file(): z.write(p,p.name)
with zipfile.ZipFile(target) as z:assert z.testzip() is None
print(json.dumps({'zip':str(target),'bytes':target.stat().st_size,'sha256':hashlib.sha256(target.read_bytes()).hexdigest(),'drc_errors':len(errors),'opens':len(opens),'warnings':len(summary['warnings'])}))
