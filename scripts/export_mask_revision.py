#!/usr/bin/env python3
"""Export the verified 0.3.1 review candidate without touching old releases."""
from pathlib import Path
import hashlib,json,re,shutil,subprocess,zipfile
ROOT=Path(__file__).resolve().parents[1]
T=ROOT/'experiments/35x28-mask-r031';E=T/'evidence';PCB=T/'hardware/collar-tracker.kicad_pcb'
OUT=ROOT/'release/collar-tracker-0.3.1-35x28-dfm'
ZIP=OUT.parent/(OUT.name+'.zip')
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
originals={ROOT/'release/collar-tracker-0.3-35x28-dfm.zip':'e46e4cf50de7912b1931fe0f99e849249e361bfcf7c30b5a75df07b299de4ef1',
 ROOT/'experiments/35x28-in2/hardware/collar-tracker.kicad_pcb':'e43296f852e2b1f9a789794bd66c97c7418bf79f2dd2b295e2a6412c608d19d2',
 ROOT/'hardware/collar-tracker.kicad_pcb':'61d6f37123e53f4f5284e3da7178212036f7e0b26254874c8b8d93de76ec7929',
 ROOT/'release/collar-tracker-0.2.1-dfm.zip':'b64b68dbb6d619b725db6139ebe5d33d8fd0b3a35aceac32ea19d106ca830619'}
assert all(sha(p)==h for p,h in originals.items())
source_hash=sha(PCB)
g=json.loads((E/'geometry-checks.json').read_text())
assert g['local_gate_passed'] and g['pcb_sha256']==source_hash
assert g['verified_revision_profile'].startswith('0.3.1')
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
note='''COLLAR TRACKER 0.3.1 - 35 x 28 mm - DFM REVIEW CANDIDATE ONLY

4 copper layers, proposed 0.8 mm thickness. In1 is reserved GND; In2 carries
signals/power and GND fill. 53 footprints, 792 track segments, 77 tented
0.60/0.20 mm through vias. Minimum drawn trace/fill width 0.20 mm.
No native DRC errors, opens or schematic parity violations. 47 explicit
library-footprint-difference warnings remain; no severity downgrade.

Changes from 0.3:
- C1/C2/C5/C8: GRM03-family reflow land candidate, 0.30 x 0.35 mm lands,
  0.55 mm pitch, 0.25 mm copper gap (previously 0.18 mm), +0.025 mm mask.
  Separate paste apertures updated to match the new lands. This follows
  the common a/b/c window in Murata's GRM03 guidance; final assembly
  evaluation and exact-SKU BOM verification remain required.
- J3/J4/J5/J6/J7 contacts: +0.05 mm mask registration allowance.
- J1/J2 U.FL: one union polygon per existing shared mask opening;
  copper, paste and keepout unchanged. Not proof of supplier warning closure.
- Only 3 GNSS_LNA_EN control trace segments moved. U2.1 mask-to-trace gap
  increased from 0.1517 mm to 0.2100 mm. RF traces and all vias unchanged.
- GND-zone clearance increased 0.20 -> 0.25 mm; refill/connectivity checked.
- Two legends moved 0.10 mm and revision legend now reads 0.3.1 TEST.

SUPPLIER STATUS: This revision HAS NOT been run through JLCDFM.
The latest user-supplied 0.3 report (2026-10-25 00:42:22) still has
0 Danger / 67 Warning. Those counts do NOT describe this 0.3.1 file.
No promise of zero orange warnings. Fixed-pitch U5/U2 mask/pad spacings,
U2's DK-derived partly mask-defined center pad, and U1 land/mask/stencil
review remain. SMT DFM, assembled hardware, power and RF tests are absent.

Assembly goal: factory-assembled, programmed and function-tested delivery,
with no user hand soldering. This is NOT a completed PCBA order package.
Exact BOM/part sourcing, battery/NTC/ESD/UVLO/VDD_GPIO sequencing,
actual eSIM/operator, antennas/50-ohm stackup/body effects, sensor and
enclosure remain unresolved. J6 is SIM contacts, J5 is a digital expansion
interface, not installed eSIM or heart-rate hardware. U1 paste remains 1:1
input for the assembly partner to adjust; final stencil has not been approved.

Original 0.3 and earlier releases preserved. No upload/order/physical test.
Source: experiments/35x28-mask-r031/hardware.
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
