#!/usr/bin/env python3
"""Read-only verification of the adjustable mount and portable 3D package."""
import hashlib
import json
from pathlib import Path
import re
import zipfile
from inspect_enclosure_mesh import inspect

ROOT=Path(__file__).resolve().parents[1]
OUT=ROOT/'mechanical/universal-mount-r01'
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()

def verify():
    native=json.loads((OUT/'visual-provenance.json').read_text())
    assert sha(ROOT/native['native_pcb'])==native['native_sha256']
    rows=json.loads((OUT/'mesh-checks.json').read_text())['meshes']
    assert len(rows)==33
    single={'boot.stl','flat_pad.stl','round_pad.stl','strap_short.stl','strap_long.stl'}
    for row in rows:
        mesh=OUT/row['file'];assert sha(mesh)==row['sha256']
        actual=inspect(mesh,allow_separate=mesh.name not in single)
        assert actual==row,(mesh.name,'Saved mesh inspection differs')
    fit=json.loads((OUT/'fit-checks.json').read_text())
    assert len(fit['checks'])==25 and fit['all_nominal_intersections_empty']
    assert all(r['no_intersection'] and r['volume_mm3']==0 for r in fit['checks'])
    old=OUT/'evidence/initial-flat-pad'
    bad=json.loads((old/'fit-checks.json').read_text())
    failed=[r for r in bad['checks'] if r['volume_mm3']>0]
    assert len(failed)==3
    for row in failed:
        actual=inspect(old/(row['name']+'.stl'),allow_separate=True)
        assert abs(actual['signed_volume_mm3']-row['volume_mm3'])<1e-7
    closure=json.loads((OUT/'closure-screen.json').read_text())['cases']
    assert len(closure)==6 and all(r['tail_beyond_keeper_mm']>=5 for r in closure)
    browser=json.loads((OUT/'viewer-checks.json').read_text())
    assert browser['file_protocol'] and not browser['uncaught_errors'] and not browser['network_requests']
    assert len(browser['collar_cases'])==6
    library=json.loads((OUT/'viewer-assets/provenance.json').read_text())
    assert sha(OUT/'viewer-assets/three.bundle.mjs')==library['sha256']
    delivered=json.loads((OUT/'delivery.json').read_text());archive=ROOT/delivered['archive']
    assert sha(archive)==delivered['sha256']
    with zipfile.ZipFile(archive) as z:
        assert z.testzip() is None
        manifest=json.loads(z.read('manifest.json'));assert len(manifest)==delivered['file_count']
        for name,digest in manifest.items():
            assert sha(ROOT/name)==digest,name
            assert hashlib.sha256(z.read(name)).hexdigest()==digest,name
        base=OUT.relative_to(ROOT)
        for rel in re.findall(r'import\("([^"]+)"\)',(OUT/'mount.scad').read_text()):
            resolved=(OUT/rel).resolve().relative_to(ROOT)
            assert str(resolved) in manifest,resolved
        assert str(base/'viewer.html') in manifest
    return {'native_pcb_unchanged':True,'closed_meshes':len(rows),'single_surface_new_parts':len(single),
            'no_positive_volume_intersections':len(fit['checks']),'retained_failing_pad_cases':len(failed),
            'collar_examples':6,'portable_files':delivered['file_count'],'archive_sha256':delivered['sha256'],
            'scope':'Prototype CAD and saved visual/example-fit evidence; not physical closure, IP68 or order acceptance.'}

if __name__=='__main__':print(json.dumps(verify(),indent=2))
