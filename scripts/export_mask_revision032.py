#!/usr/bin/env python3
"""Export the verified 0.3.2 review candidate without touching old releases."""
from pathlib import Path
import hashlib,json,re,shutil,subprocess,zipfile
ROOT=Path(__file__).resolve().parents[1]
T=ROOT/'experiments/35x28-mask-r032';E=T/'evidence';PCB=T/'hardware/collar-tracker.kicad_pcb'
OUT=ROOT/'release/collar-tracker-0.3.2-35x28-dfm'
ZIP=OUT.parent/(OUT.name+'.zip')
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
originals={ROOT/'release/collar-tracker-0.3.1-35x28-dfm.zip':'616a26fcc55a17004994cd455970d1841c65877e6102e5f5bbb29f50c6a83ffc',
 ROOT/'experiments/35x28-mask-r031/hardware/collar-tracker.kicad_pcb':'a7e596b58e7e32e75886a4b711d0680cc23c1b5abfe2d4a14a947072b90c495c',
 ROOT/'release/collar-tracker-0.3-35x28-dfm.zip':'e46e4cf50de7912b1931fe0f99e849249e361bfcf7c30b5a75df07b299de4ef1',
 ROOT/'experiments/35x28-in2/hardware/collar-tracker.kicad_pcb':'e43296f852e2b1f9a789794bd66c97c7418bf79f2dd2b295e2a6412c608d19d2',
 ROOT/'hardware/collar-tracker.kicad_pcb':'61d6f37123e53f4f5284e3da7178212036f7e0b26254874c8b8d93de76ec7929',
 ROOT/'release/collar-tracker-0.2.1-dfm.zip':'b64b68dbb6d619b725db6139ebe5d33d8fd0b3a35aceac32ea19d106ca830619'}
assert all(sha(p)==h for p,h in originals.items())
source_hash=sha(PCB)
g=json.loads((E/'geometry-checks.json').read_text())
assert g['local_gate_passed'] and g['pcb_sha256']==source_hash
assert g['verified_revision_profile'].startswith('0.3.2')
assert not ZIP.exists(), 'Refuse to overwrite an already exported revision'
OUT.mkdir(exist_ok=True)
with (E/'export.log').open('w') as log:
 def run(*args):subprocess.run([str(ROOT/'scripts/kicad-cli'),*map(str,args)],cwd=ROOT,stdout=log,stderr=subprocess.STDOUT,check=True)
 run('pcb','drc','--format','json','--severity-all','--schematic-parity','--all-track-errors','-o',E/'final-drc.json',PCB)
 d=json.loads((E/'final-drc.json').read_text())
 errors=[v for v in d['violations'] if v['severity']=='error']
 assert not errors and not d['unconnected_items'] and not d['schematic_parity']
 run('pcb','export','gerbers','-l','F.Cu,In1.Cu,In2.Cu,B.Cu,F.Mask,B.Mask,F.SilkS,B.SilkS,F.Paste,B.Paste,Edge.Cuts',
     '--use-drill-file-origin','--subtract-soldermask','-o',OUT,PCB)
 run('pcb','export','drill','--format','excellon','--drill-origin','plot','--excellon-separate-th','--generate-report',
     '--report-path',OUT/'drill-report.txt','-o',OUT,PCB)
assert sha(PCB)==source_hash
note='''COLLAR TRACKER 0.3.2 - 35 x 28 mm - DFM REVIEW CANDIDATE ONLY

4 copper layers, proposed 0.8 mm thickness, 1 oz outer copper / green mask
candidate. 53 footprints, 792 track segments, 77 tented 0.60/0.20 mm vias.
In1 remains reserved GND. This revision changes only U2 mask apertures,
the revision label and title metadata. Copper/routing/paste unchanged.

SKY65943-11 primary source: Skyworks 204404H, 2025-09-04, Figure 7/page 9:
https://www.skyworksinc.com/-/media/C1965FC4C165469FAEED1BA276874AF1.pdf
- Center mask: 1.55 x 2.487 -> 1.55 x 2.90 mm. Select the full opening
  within the manufacturer's 60-100% center-opening range. No paste increase.
- Four large terminal masks: 0.525 x 0.615 -> 0.525 x 0.515 mm to match
  Figure 7. Their 0.425 x 0.515 mm copper pads are not reduced.
- All six small terminal masks remain 0.525 x 0.375 mm.
- All other components, copper pads, traces, vias, paste and rules preserved.

Native checks: 0 errors, 0 opens, 0 schematic-parity violations. 47 explicit
library-footprint-difference warnings remain, without exclusions/downgrades.

SUPPLIER STATUS: 0.3.2 HAS NOT been run through JLCDFM.
The user-supplied 0.3.1 report dated 2026-10-25 01:28:03 has 0 Danger and
45 Warning: 10 pad spacing, 30 mask bridge, 3 mask-to-trace, 2 negative mask.
Those are NOT results for this new file. PCB analysis only; SMT unchecked.
0.3.1's 22->2 negative and 2->0 compound mask reductions are verified by
that report. Its remaining two negatives have not been individually mapped.
The 0.08 mm trace example is localized at the U1.71 ground-pad/pour neck;
it is not a demonstrated foreign-net clearance error, nor closed as harmless.
Fixed-pitch U2/U5 mask/land dimensions require assembly/fab disposition.
No promise that orange warnings will all disappear. Do not shrink
manufacturer lands merely to satisfy the generic checker.

This is NOT an order-ready PCBA package. Factory-assembled, programmed and
function-tested delivery with no user hand soldering remains the goal.
BOM/part sourcing, battery/NTC/ESD/UVLO/VDD_GPIO sequencing, actual eSIM and
operator, antennas/50-ohm stackup/body effects, firmware, fixture, sensor
and enclosure are unresolved. J6 is SIM contacts; J5 a digital interface.
U1 1:1 paste is partner input, not an approved production stencil.

Source: experiments/35x28-mask-r032/hardware.
Old releases preserved. No supplier upload/order or powered/physical test.
'''
(OUT/'READ-ME-DFM-ONLY.txt').write_text(note)
(OUT/'DRC-summary.json').write_text(json.dumps({'source':str(PCB),'pcb_sha256':source_hash,'errors':0,'opens':0,
 'schematic_parity':[],'warnings':d['violations'],'supplier_dfm':'NOT RUN'},indent=2)+'\n')
shutil.copy2(E/'geometry-checks.json',OUT/'LOCAL-GEOMETRY-CHECKS.json')
shutil.copy2(E/'changes.json',OUT/'REVISION-CHANGES.json')
drill=(OUT/'collar-tracker-PTH.drl').read_text()
holes=re.findall(r'^X[-+\d.]+Y[-+\d.]+$',drill,re.M)
assert len(holes)==77 and re.search(r'^T\d+C0\.200$',drill,re.M)
edge=(OUT/'collar-tracker-Edge_Cuts.gm1').read_text()
assert '%MOMM*%' in edge and '%FSLAX46Y46*%' in edge
coords=[(int(x)/1e6,int(y)/1e6) for x,y in re.findall(r'X(-?\d+)Y(-?\d+)D0[12]\*',edge)]
assert (min(x for x,y in coords),max(x for x,y in coords),min(y for x,y in coords),max(y for x,y in coords))==(0,35,0,28)
assert all(any(p.suffix==ext for p in OUT.iterdir()) for ext in ['.gtl','.gbl','.g1','.g2','.gts','.gbs','.gto','.gbo','.gtp','.gbp','.gm1'])
files=sorted(p for p in OUT.iterdir() if p.is_file() and p.name!='SHA256SUMS.txt')
(OUT/'SHA256SUMS.txt').write_text(''.join(sha(p)+'  '+p.name+'\n' for p in files))
with zipfile.ZipFile(ZIP,'w',zipfile.ZIP_DEFLATED) as z:
 for p in sorted(OUT.iterdir()):
  if p.is_file():z.write(p,p.name)
with zipfile.ZipFile(ZIP) as z:
 assert z.testzip() is None
 for line in z.read('SHA256SUMS.txt').decode().splitlines():
  h,n=line.split('  ',1);assert hashlib.sha256(z.read(n)).hexdigest()==h
 count=len(z.namelist())
assert all(sha(p)==h for p,h in originals.items()) and sha(PCB)==source_hash
delivery={'zip':str(ZIP),'bytes':ZIP.stat().st_size,'files':count,'sha256':sha(ZIP),'pcb_sha256':source_hash,
 'native_errors':0,'opens':0,'parity':0,'native_warnings':len(d['violations']),'local_geometry_passed':True,
 'supplier_dfm':'NOT RUN','board_mm':[35,28,.8],'drilled_holes':77,'old_releases_unchanged':True}
(E/'delivery.json').write_text(json.dumps(delivery,indent=2)+'\n')
print(json.dumps(delivery,indent=2))
