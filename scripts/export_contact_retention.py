#!/usr/bin/env python3
"""Export r16 source parts and check the actual CAD intersections."""
from concurrent.futures import ThreadPoolExecutor
import json
import os
from pathlib import Path
import re
import shutil
import struct
import subprocess
import tempfile

from check_contact_retention import OUT, ROOT, sha
from inspect_enclosure_mesh import inspect


def bearing_vertices(vertices, spec):
    """Only the dimensioned rear bearing plane may contact the shell."""
    if not vertices:raise ValueError('Missing bearing faces')
    for x,y,z in vertices:
        if abs(x-spec['pocket']['bearing_x_mm'])>3e-5:
            raise ValueError('Terminal penetrates the shell')
        if not (1.8<z<15.4 and -11<y<11):
            raise ValueError('Unexpected contact outside the terminal pockets')


def main():
    exe=os.environ.get('COLLAR_OPENSCAD') or shutil.which('openscad');assert exe
    rt=ROOT/'.runtime/contact-retention-r16';rt.mkdir(parents=True,exist_ok=True)
    checks=json.loads((OUT/'checks.json').read_text());assert checks['result']=='CONTACT_RETENTION_GEOMETRY_PASS'
    inputs=dict(checks['inputs'])
    for p in [Path(__file__),OUT/'contacts.scad',OUT/'parameters.scad',ROOT/'scripts/inspect_enclosure_mesh.py',
              ROOT/'mechanical/swim-r13-charge-dock/body.stl',ROOT/'mechanical/swim-r12-pack-retention/carrier.stl',
              ROOT/'mechanical/swim-r11-thermal-fit/retainer.stl']:
        inputs[str(p.relative_to(ROOT))]=sha(p)
    diagnostics={}
    def export(name):
        path=OUT/(name+'.stl')
        r=subprocess.run([exe,'-o',str(path),'--export-format','binstl','-D',f'part="{name}"',str(OUT/'contacts.scad')],capture_output=True,text=True)
        (rt/(name+'.log')).write_text(r.stderr)
        assert r.returncode==0 and not re.search(r'WARNING|ERROR',r.stderr),(name,r.stderr)
        assert re.search(r'Simple:\s+yes',r.stderr),(name,r.stderr)
        diagnostics[name]=r.stderr
        result=inspect(path);print('Closed mesh:',name,flush=True);return result
    with ThreadPoolExecutor(max_workers=2) as pool:
        meshes=list(pool.map(export,['body','contact','positive_terminal','negative_terminal']))
    def control(name):
        with tempfile.TemporaryDirectory(dir=rt,prefix=name) as temp:
            path=Path(temp)/'intersection.stl'
            r=subprocess.run([exe,'-o',str(path),'--export-format','binstl','-D',f'part="{name}"',str(OUT/'contacts.scad')],capture_output=True,text=True)
            (rt/(name+'.log')).write_text(r.stderr)
            empty='Current top level object is empty.' in r.stderr
            vertices=[];volume=0
            if name=='retention_collision':
                assert r.returncode==1 and empty and not path.exists(),r.stderr
                assert not re.search(r'WARNING|ERROR',r.stderr),r.stderr
            elif name=='body_collision':
                # CGAL may discard coplanar boundaries or emit only their
                # zero-thickness faces. Both are zero solid penetration; a
                # separate +0.1mm control must still produce positive volume.
                if empty:
                    assert r.returncode==1 and not path.exists() and not re.search(r'WARNING|ERROR',r.stderr),r.stderr
                else:
                    assert r.returncode==0 and path.exists(),r.stderr
                    data=path.read_bytes();n=struct.unpack_from('<I',data,80)[0]
                    assert len(data)==84+50*n
                    vertices=[list(struct.unpack_from('<3f',data,84+50*i+12+12*j)) for i in range(n) for j in range(3)]
                    bearing_vertices(vertices,json.loads((OUT/'contact.json').read_text()))
                    allowed={'WARNING: Object may not be a valid 2-manifold and may need repair!',
                             'EXPORT-WARNING: Exported object may not be a valid 2-manifold and may need repair'}
                    assert all(line in allowed for line in r.stderr.splitlines() if re.search(r'WARNING|ERROR',line)),r.stderr
            else:
                assert r.returncode==0 and not empty and path.exists(),r.stderr
                assert not re.search(r'WARNING|ERROR',r.stderr),r.stderr
                volume=inspect(path,allow_separate=True)['signed_volume_mm3'];assert volume>0
            print('CAD control:',name,'empty' if empty else ('bearing plane' if vertices else volume),flush=True)
            return dict(case=name,empty=empty,returncode=r.returncode,volume_mm3=volume,contact_vertices=vertices,diagnostic=r.stderr)
    with ThreadPoolExecutor(max_workers=2) as pool:
        controls=list(pool.map(control,['retention_collision','body_collision','old_body_control','penetration_control']))
    previews={}
    for name in ['review','section']:
        path=OUT/(name+'.png')
        r=subprocess.run([exe,'-o',str(path),'--imgsize','1600,1100','--projection','o','--viewall','--autocenter',
                          '--camera','0,0,0,55,0,40,150','--colorscheme','Tomorrow','-D',f'part="{name}"',str(OUT/'contacts.scad')],capture_output=True,text=True)
        (rt/(name+'.log')).write_text(r.stderr);assert r.returncode==0 and not re.search(r'WARNING|ERROR',r.stderr),r.stderr
        previews[path.name]=sha(path);print('Rendered:',name,flush=True)
    assert all(sha(ROOT/n)==v for n,v in inputs.items()),'Source changed during CAD export'
    (OUT/'mesh-checks.json').write_text(json.dumps(dict(inputs=inputs,meshes=meshes,diagnostics=diagnostics,controls=controls,previews=previews,physical_qualification=False),indent=2)+'\n')


if __name__=='__main__':main()
