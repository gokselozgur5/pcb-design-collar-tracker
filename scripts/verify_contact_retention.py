#!/usr/bin/env python3
"""Read-only r16 source/evidence verification; standard Python, no CAD rerun."""
import argparse
import json
from pathlib import Path
import re

from check_contact_retention import OUT, ROOT, dimensions, parameters, sha
from export_contact_retention import bearing_vertices
from inspect_enclosure_mesh import inspect


def require(ok,message):
    if not ok:raise ValueError(message)


def evidence():
    s=json.loads((OUT/'contact.json').read_text());r=json.loads((OUT/'checks.json').read_text())
    dims=dimensions(s)
    require(r['checks'][:len(dims['checks'])]==dims['checks'],'Changed stack calculation')
    require(r['result']=='CONTACT_RETENTION_GEOMETRY_PASS' and all(x['pass_'] for x in r['checks']),'Failed contact geometry')
    require(len(r['component_clearances'])==85 and len(r['bearing_areas_mm2'])==2,'Missing contact geometry evidence')
    require(r['old_circular_bearing_area_mm2']==0,'Unexpected old round bearing')
    require(r['native_pinout']=={'J3.1':'/VIN_5V','J3.2':'/GND'},'Wrong native contact polarity')
    require((OUT/'parameters.scad').read_text()==parameters(s),'Changed generated contact dimensions')
    for k in ['production_release','physical_retention_qualified','physical_ingress_qualified']:
        require(not s[k] and not r[k],'Unexpected physical/release acceptance')
    m=json.loads((OUT/'mesh-checks.json').read_text())
    for report in [r,m]:
        for name,digest in report['inputs'].items():require(sha(ROOT/name)==digest,'Changed contact input: '+name)
    expected={'body.stl','contact.stl','positive_terminal.stl','negative_terminal.stl'}
    require({row['file'] for row in m['meshes']}==expected,'Incomplete contact meshes')
    for row in m['meshes']:require(inspect(OUT/row['file'])==row,'Changed contact mesh: '+row['file'])
    require(set(m['diagnostics'])=={Path(x).stem for x in expected},'Missing CAD diagnostics')
    for name,d in m['diagnostics'].items():require(not re.search(r'WARNING|ERROR',d) and re.search(r'Simple:\s+yes',d),'Invalid CAD solid: '+name)
    require({c['case'] for c in m['controls']}=={'retention_collision','body_collision','old_body_control','penetration_control'},'Missing CAD control')
    for c in m['controls']:
        if c['case']=='body_collision' and not c['empty']:
            bearing_vertices(c['contact_vertices'],s)
            allowed={'WARNING: Object may not be a valid 2-manifold and may need repair!',
                     'EXPORT-WARNING: Exported object may not be a valid 2-manifold and may need repair'}
            require(c['returncode']==0 and c['volume_mm3']==0 and all(line in allowed for line in c['diagnostic'].splitlines() if re.search(r'WARNING|ERROR',line)),'Unexpected bearing result')
        elif c['case'] in {'retention_collision','body_collision'}:
            require(c['empty'] and c['returncode']==1 and c['volume_mm3']==0 and not c['contact_vertices'] and not re.search(r'WARNING|ERROR',c['diagnostic']),'Contact penetration')
        else:
            require(not c['empty'] and c['returncode']==0 and c['volume_mm3']>0 and not re.search(r'WARNING|ERROR',c['diagnostic']),'Bad-assembly control failed')
    require(set(m['previews'])=={'review.png','section.png'},'Missing contact previews')
    for name,digest in m['previews'].items():require(sha(OUT/name)==digest,'Changed contact preview: '+name)
    require(not m['physical_qualification'],'Unexpected physical mesh acceptance')
    return r


def record():
    evidence()
    names=['README.md','sources.json','contact.json','contacts.scad','parameters.scad','checks.json','mesh-checks.json',
           'body.stl','contact.stl','positive_terminal.stl','negative_terminal.stl','review.png','section.png',
           'contact-retention-sheet.svg','contact-retention-sheet.pdf','contact-retention-sheet.png']
    files=[OUT/name for name in names]+sorted((OUT/'evidence/initial-step').iterdir())
    files += [ROOT/'scripts'/name for name in ['check_contact_retention.py','export_contact_retention.py','make_contact_retention_sheet.py','verify_contact_retention.py']]
    files += [ROOT/'tests/test_contact_retention.py']
    cp=dict(revision='r16',production_release=False,physical_qualification=False,files={str(p.relative_to(ROOT)):sha(p) for p in files})
    path=OUT/'checkpoint.json'
    if path.exists():require(json.loads(path.read_text())==cp,'Preserve prior contact checkpoint; use a successor')
    else:path.write_text(json.dumps(cp,indent=2)+'\n')


def verify(check_baseline=True):
    if check_baseline:
        from verify_dock_wire_clamp import verify as previous
        previous()
    r=evidence();cp=json.loads((OUT/'checkpoint.json').read_text())
    require(cp['revision']=='r16' and not cp['production_release'] and not cp['physical_qualification'],'Wrong checkpoint scope')
    for name,digest in cp['files'].items():require(sha(ROOT/name)==digest,'Changed contact checkpoint file: '+name)
    return dict(result='PASS',revision='r16',checks=len(r['checks']),populated_envelopes=85,closed_meshes=4,cad_controls=4,
                bearing_areas_mm2=r['bearing_areas_mm2'],physical_retention_qualified=False,physical_ingress_qualified=False)


if __name__=='__main__':
    ap=argparse.ArgumentParser(description=__doc__);ap.add_argument('--record',action='store_true');args=ap.parse_args()
    if args.record:record()
    print(json.dumps(verify(),indent=2))
