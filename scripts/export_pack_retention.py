#!/usr/bin/env python3
"""Export only the changed r12 body/carrier, then test actual CAD intersections."""
from concurrent.futures import ThreadPoolExecutor
import hashlib
import json
import os
from pathlib import Path
import shutil
import subprocess
import tempfile

from inspect_enclosure_mesh import inspect

ROOT=Path(__file__).resolve().parents[1]
BASE=ROOT/'mechanical/swim-r11-thermal-fit'
OUT=ROOT/'mechanical/swim-r12-pack-retention'
RUNTIME=ROOT/'.runtime/pack-r12'
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()


def main():
    exe=os.environ.get('COLLAR_OPENSCAD') or shutil.which('openscad')
    assert exe, 'Install OpenSCAD or set COLLAR_OPENSCAD'
    RUNTIME.mkdir(parents=True,exist_ok=True)
    report=json.loads((OUT/'pack-retention-checks.json').read_text())
    assert report['result']=='CONDITIONAL_PACK_RETENTION_GEOMETRY_PASS'
    files=[OUT/n for n in ['pack-retention.json','pack-retention-checks.json','enclosure.scad','pack.scad','pack-retention.scad','pack-retention-parameters.scad']]
    files += [BASE/n for n in ['parameters.scad','populated.scad','cables.scad','pack.scad','retention.scad','checkpoint.json']]
    files += [Path(__file__),ROOT/'scripts/inspect_enclosure_mesh.py']
    inputs={str(p.relative_to(ROOT)):sha(p) for p in files}
    for name,digest in report['inputs'].items():
        assert sha(ROOT/name)==digest, 'Stale input: '+name
    def mesh(name):
        target=OUT/(name+'.stl')
        with (RUNTIME/(name+'.log')).open('w') as log:
            subprocess.run([exe,'-o',str(target),'--export-format','binstl','-D',f'part="{name}"',str(OUT/'enclosure.scad')],
                           stdout=log,stderr=subprocess.STDOUT,check=True)
        result=inspect(target)
        expected={'body':[58.7,49.4,18.5],'carrier':[41.6,33.6,9.7]}[name]
        assert all(abs(a-b)<.0001 for a,b in zip(result['dimensions_mm'],expected)),result
        print('Actual mesh verified:',name,flush=True)
        return result
    with ThreadPoolExecutor(max_workers=2) as pool:
        meshes=list(pool.map(mesh,['body','carrier']))
    cases=[('pack_components',True),('pack_components_control',False),('pack_hardware',True),
           ('pack_ntc',True),('pack_ntc_control',False),('pack_cradle',True),('pack_cradle_control',False)]
    def collision(case):
        name,expected_empty=case
        with tempfile.TemporaryDirectory(prefix=name+'-',dir=RUNTIME) as temp:
            target=Path(temp)/'intersection.stl'
            result=subprocess.run([exe,'-o',str(target),'--export-format','binstl','-D',f'part="{name}"',str(OUT/'enclosure.scad')],capture_output=True,text=True)
            (RUNTIME/(name+'.log')).write_text(result.stderr)
            empty='Current top level object is empty.' in result.stderr
            if expected_empty:
                assert result.returncode==1 and empty and not target.exists(),(name,result.stderr)
                volume=0
            else:
                assert result.returncode==0 and target.exists() and not empty,(name,result.stderr)
                volume=inspect(target,allow_separate=True)['signed_volume_mm3']
                assert volume>0
            print('CAD control verified:',name,flush=True)
            return dict(case=name,empty=empty,returncode=result.returncode,interference_volume_mm3=volume,diagnostic=result.stderr)
    with ThreadPoolExecutor(max_workers=2) as pool:
        controls=list(pool.map(collision,cases))
    previews={}
    for name in ['pack_exploded','pack_review','pack_section','mounted']:
        target=OUT/(name+'.png')
        with (RUNTIME/(name+'.log')).open('w') as log:
            subprocess.run([exe,'-o',str(target),'--imgsize','1600,1200','--projection','o','--viewall','--autocenter',
                            '--camera','0,0,0,65,0,35,140','--colorscheme','Tomorrow','-D',f'part="{name}"',str(OUT/'enclosure.scad')],
                           stdout=log,stderr=subprocess.STDOUT,check=True)
        previews[target.name]=sha(target)
        print('Rendered:',name,flush=True)
    assert all(sha(ROOT/n)==s for n,s in inputs.items()),'Source changed during export'
    report=dict(inputs=inputs,meshes=meshes,cad_controls=controls,previews=previews,
                unchanged_parts={n:sha(BASE/n) for n in ['lid.stl','retainer.stl','contact.stl','contact_seal.stl','magnet_plug.stl','dock.stl','boot.stl']},
                scope='Two changed meshes and new CAD controls. Seven r11 parts reused by hash; no new physical qualification.')
    (OUT/'mesh-checks.json').write_text(json.dumps(report,indent=2)+'\n')


if __name__=='__main__':
    main()
