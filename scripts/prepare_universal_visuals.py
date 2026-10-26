#!/usr/bin/env python3
"""Prepare visual-only missing bodies; preserve every native fabrication byte."""
import hashlib
import json
from pathlib import Path
import re

ROOT=Path(__file__).resolve().parents[1]
OUT=ROOT/'mechanical/universal-mount-r01'
RUN=ROOT/'.runtime/universal-mount-r01'
SOURCE=ROOT/'experiments/pcba-r05m-rohm-q1/hardware/collar-tracker.kicad_pcb'
def main():
    raw=SOURCE.read_text(); rendered=raw; models=RUN/'models';models.mkdir(exist_ok=True)
    bodies={'U1':(12.1,11.1,1.3,[.65,.67,.70]),'U2':(2.5,2.5,.7,[.10,.11,.13]),
            'U9':(2,2,.8,[.1,.11,.13]),'J6':(9.04,12.3,1.35,[.65,.67,.70])}
    inserts=[]
    for match in list(re.finditer(r'^\t\(footprint ',raw,re.M)):
        end=re.search(r'^\t\)',raw[match.start():],re.M).end()+match.start()
        block=raw[match.start():end];ref=re.search(r'\(property "Reference" "([^"]+)"',block)[1]
        if ref in bodies:
            w,d,h,col=bodies[ref]; model=models/(ref+'.wrl')
            model.write_text('#VRML V2.0 utf8\nTransform { translation 0 0 '+str((h/2+.03)/2.54)+' children [ Shape { appearance Appearance { material Material { diffuseColor '+' '.join(map(str,col))+' } } geometry Box { size '+' '.join(str(x/2.54) for x in (w,d,h))+' } } ] }\n')
            path=str(model)
        elif ref in ['U10','U11','U12']:
            path='${KICAD10_3DMODEL_DIR}/Package_TO_SOT_SMD.3dshapes/SOT-353_SC-70-5.step'
        else:continue
        insertion='\n\t\t(model "'+path+'"\n\t\t\t(offset (xyz 0 0 0))\n\t\t\t(scale (xyz 1 1 1))\n\t\t\t(rotate (xyz 0 0 0))\n\t\t)\n'
        inserts.append((end-2,insertion))
    for at,s in reversed(inserts):rendered=rendered[:at]+s+rendered[at:]
    restored=rendered
    for _,s in inserts:restored=restored.replace(s,'',1)
    assert restored==raw
    (RUN/'visual-only.kicad_pcb').write_text(rendered)
    records=json.loads((ROOT/'mechanical/swim-r09-pack-request/components.native.json').read_text())['parts']
    profile={p['ref']:p for p in json.loads((ROOT/'mechanical/swim-r09-pack-request/fit-profile.json').read_text())['parts']}
    lines=['// Simplified component envelopes at native positions; not supplier 3D models.']
    for p in records:
        if p['dnp'] or p['ref'] not in profile:continue
        b=p['body_and_land_bounds_mm'];h=profile[p['ref']]['height_max_mm'];z=11.24088 if p['side']=='top' else 10.4-h
        c=[.57,.60,.64] if p['ref'] in ['U1','J6'] else [.12,.13,.16]
        lines.append(f'color({c})translate([{b[0]},{b[1]},{z}])cube([{b[2]-b[0]},{b[3]-b[1]},{h}]); // {p["ref"]}')
    (OUT/'components.scad').write_text('\n'.join(lines)+'\n')
    harness=(ROOT/'mechanical/swim-r18-charge-clearance/harness.scad').read_text()
    start=harness.index('rf_paths =')+len('rf_paths =')
    paths=json.JSONDecoder().raw_decode(harness[start:].lstrip())[0]
    (OUT/'rf-paths.scad').write_text('// Existing r18 nominal RF paths; visual representation only.\nrf_paths='+json.dumps(paths)+';\nfor(j=[0:1])color(j==0?[.85,.58,.17]:[.14,.32,.53])for(i=[0:len(rf_paths[j])-2])hull(){translate(rf_paths[j][i])sphere(r=.565,$fn=8);translate(rf_paths[j][i+1])sphere(r=.565,$fn=8);}\n')
    (OUT/'visual-provenance.json').write_text(json.dumps({'native_pcb':str(SOURCE.relative_to(ROOT)),
       'native_sha256':hashlib.sha256(SOURCE.read_bytes()).hexdigest(),
       'visual_only_additions':list(bodies)+['U10','U11','U12'],
       'simplified_bodies_mm':bodies,'fabrication_geometry_changed':False,
       'limits':'Four bodies are dimensioned visual approximations. Assembly scene uses existing conservative envelopes. Neither is a new mechanical qualification.'},indent=2)+'\n')
    print('Prepared seven visual-only model additions; native source untouched.')
if __name__=='__main__':main()
