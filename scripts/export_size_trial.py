#!/usr/bin/env python3
"""Package the accepted 35x28 geometry trial; leaves 0.2/0.2.1 unchanged."""
from pathlib import Path
import hashlib,json,re,shutil,subprocess,zipfile
ROOT=Path(__file__).resolve().parents[1];TRIAL=ROOT/'experiments/35x28-in2'
PCB=TRIAL/'hardware/collar-tracker.kicad_pcb';E=TRIAL/'evidence'
OUT=ROOT/'release/collar-tracker-0.3-35x28-dfm';OUT.mkdir(parents=True,exist_ok=True)
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
source_hash=sha(PCB)
with (E/'final-drc.log').open('w') as log:
    subprocess.run([str(ROOT/'scripts/kicad-cli'),'pcb','drc','--format','json','--severity-all',
        '--schematic-parity','--all-track-errors','-o',str(E/'final-drc.json'),str(PCB)],
        cwd=ROOT,stdout=log,stderr=subprocess.STDOUT,check=True)
assert sha(PCB)==source_hash,'Source changed during native DRC'
drc=json.loads((E/'final-drc.json').read_text());g=json.loads((E/'geometry-checks.json').read_text())
errors=[x for x in drc['violations'] if x['severity']=='error'];warnings=[x for x in drc['violations'] if x['severity']=='warning']
assert not errors and not drc['unconnected_items'] and not drc['schematic_parity']
assert g['local_gate_passed'] and g['pcb_sha256']==sha(PCB)
assert g['footprints']==53 and g['via_sizes_mm']==[[.6,.2]] and g['reserved_ground_plane_signal_segments']==0
with (E/'export.log').open('w') as log:
    def run(*args):subprocess.run([str(ROOT/'scripts/kicad-cli'),*map(str,args)],stdout=log,stderr=subprocess.STDOUT,check=True,cwd=ROOT)
    run('pcb','export','gerbers','-l','F.Cu,In1.Cu,In2.Cu,B.Cu,F.Mask,B.Mask,F.SilkS,B.SilkS,F.Paste,B.Paste,Edge.Cuts','--use-drill-file-origin','--subtract-soldermask','-o',OUT,PCB)
    run('pcb','export','drill','--format','excellon','--drill-origin','plot','--excellon-separate-th','--generate-report','--report-path',OUT/'drill-report.txt','-o',OUT,PCB)
note='''COLLAR TRACKER 0.3 — 35 x 28 mm GEOMETRY TRIAL — DFM REVIEW ONLY

Four copper layers; proposed thickness 0.8 mm. 53 footprints.
F.Cu / In1.Cu / In2.Cu / B.Cu. In1.Cu is reserved for GND, with no signal
tracks. In2.Cu contains signal/power tracks and GND fill, not a solid plane.
Minimum track width 0.20 mm; power tracks range 0.20–0.25 mm.
Ground fill minimum width is also set to 0.20 mm.
Through vias: 0.60 mm copper / 0.20 mm drill, tented; 0.20 mm nominal annulus.
Different-net copper clearance: 0.20 mm, except fixed same-package pad
spacing at 0.15 mm. Component pad shapes/nets/mask apertures match 0.2.1.
The explicit package-pad exception applies to pads only, never tracks/vias.
No global DRC exclusions or severity downgrades. 43 library-difference
warnings remain for the inherited local mask/silk footprint modifications.
Independent local pad-box-to-via, pad-box-to-foreign-track, via-to-via,
mask-bridge and legend/drill geometry checks accompany the native DRC.

This package HAS NOT been run through JLCDFM. The 0.2.1 report's 2 Danger /
306 Warning counts belong to the previous 30 x 22 board. Local checks do not
establish that all proprietary supplier warnings are resolved.

OPEN BEFORE FABRICATION:
- Battery/NTC, peak currents, charging-input/ESD protection, hardware UVLO,
  nRF9151 VDD_GPIO sequencing and power integrity.
- J6 is an external SIM interface. No eSIM IC/profile or Turkish operator
  provisioning has been selected/verified.
- J5 is a digital expansion interface, not an installed heart-rate sensor.
- LTE/GNSS antenna geometry, RF reference/return, 50-ohm stackup, matching
  and operation near the animal's body; no RF performance test.
- nRF land-pattern pin-1 difference vs the examined Nordic DK, stencil,
  intentional shared U.FL mask apertures and assembly review.
- Enclosure/battery/antenna integration. The old 38 x 30 mm mockup used a
  30 x 22 mm PCB and has not been updated for this board.

No supplier upload, order, assembly, or physical/powered test was performed.
Native source is in experiments/35x28-in2/hardware. Old packages preserved.
'''
(OUT/'READ-ME-DFM-ONLY.txt').write_text(note)
summary={'board_mm':[35,28,.8],'errors':0,'unconnected':0,'schematic_parity':[],
         'warnings':warnings,'pcb_sha256':sha(PCB),'source':str(PCB),'supplier_dfm':'NOT RUN'}
(OUT/'DRC-summary.json').write_text(json.dumps(summary,indent=2)+'\n')
shutil.copy2(E/'geometry-checks.json',OUT/'LOCAL-GEOMETRY-CHECKS.json')
# Verify actual exported drill commands and outline centerlines.
pth=next(p for p in OUT.glob('*-PTH.drl'))
drill=pth.read_text();holes=re.findall(r'^X[-+\d.]+Y[-+\d.]+$',drill,re.M)
assert len(holes)==g['vias'],(len(holes),g['vias'])
assert re.search(r'^T\d+C0\.200$',drill,re.M), 'Unexpected drill tool'
edge=next(p for p in OUT.iterdir() if p.suffix.lower() in ['.gm1','.gko'])
text=edge.read_text();assert '%MOMM*%' in text and '%FSLAX46Y46*%' in text
coords=[(int(x)/1e6,int(y)/1e6) for x,y in re.findall(r'X(-?\d+)Y(-?\d+)D0[12]\*',text)]
assert coords and min(x for x,y in coords)==0 and max(x for x,y in coords)==35 and min(y for x,y in coords)==0 and max(y for x,y in coords)==28,coords
files=[p for p in OUT.iterdir() if p.is_file() and p.name!='SHA256SUMS.txt']
exts=['.gtl','.gbl','.g1','.g2','.gts','.gbs','.gto','.gbo','.gtp','.gbp','.gm1']
assert all(any(p.suffix.lower()==ext for p in files) for ext in exts)
(OUT/'SHA256SUMS.txt').write_text(''.join(sha(p)+'  '+p.name+'\n' for p in sorted(files)))
target=OUT.parent/(OUT.name+'.zip')
with zipfile.ZipFile(target,'w',zipfile.ZIP_DEFLATED) as z:
    for p in sorted(OUT.iterdir()):
        if p.is_file():z.write(p,p.name)
with zipfile.ZipFile(target) as z:
    assert z.testzip() is None
    for line in z.read('SHA256SUMS.txt').decode().splitlines():
        digest,name=line.split('  ',1);assert hashlib.sha256(z.read(name)).hexdigest()==digest
    names=z.namelist()
assert sha(ROOT/'hardware/collar-tracker.kicad_pcb')=='61d6f37123e53f4f5284e3da7178212036f7e0b26254874c8b8d93de76ec7929'
assert sha(PCB)==source_hash,'Source changed during export'
assert sha(ROOT/'release/collar-tracker-0.2.1-dfm.zip')=='b64b68dbb6d619b725db6139ebe5d33d8fd0b3a35aceac32ea19d106ca830619'
delivery={'zip':str(target),'bytes':target.stat().st_size,'files':len(names),'sha256':sha(target),'pcb_sha256':sha(PCB),'outline_mm':[35,28],'drilled_holes':len(holes),'native_errors':0,'opens':0,'parity':0,'native_warnings':len(warnings),'local_geometry_passed':True,'supplier_dfm':'NOT RUN'}
(E/'delivery.json').write_text(json.dumps(delivery,indent=2)+'\n');print(json.dumps(delivery,indent=2))
