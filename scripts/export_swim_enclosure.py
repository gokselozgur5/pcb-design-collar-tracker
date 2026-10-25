#!/usr/bin/env python3
"""Rebuild prototype solids/previews and inspect the actual exported triangles."""
import collections
import hashlib
import json
import math
import os
from pathlib import Path
import shutil
import struct
import subprocess
import sys

ROOT=Path(__file__).resolve().parents[1]
OUT=ROOT/'mechanical/swim-r01'
RUNTIME=ROOT/'.runtime';RUNTIME.mkdir(exist_ok=True)
exe=os.environ.get('COLLAR_OPENSCAD') or shutil.which('openscad')
assert exe,'Install OpenSCAD or set COLLAR_OPENSCAD'
subprocess.run([sys.executable,str(ROOT/'scripts/build_swim_enclosure.py')],check=True)
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
inputs={n:sha(OUT/n) for n in ['parameters.json','parameters.scad','enclosure.scad']}
p=json.loads((OUT/'parameters.json').read_text())
parts=['body','lid','carrier','contact','contact_seal','magnet_plug','dock','boot']
for name in parts:
    with (RUNTIME/f'swim-{name}.log').open('w') as log:
        subprocess.run([exe,'-o',str(OUT/f'{name}.stl'),'--export-format','binstl','-D',f'part="{name}"',str(OUT/'enclosure.scad')],check=True,stdout=log,stderr=subprocess.STDOUT)
for name in ['exploded','section','mounted']:
    with (RUNTIME/f'swim-{name}.log').open('w') as log:
        subprocess.run([exe,'-o',str(OUT/f'{name}.png'),'--imgsize','1600,1200','--projection','o','--viewall','--autocenter','--camera','0,0,0,65,0,35,140','--colorscheme','Tomorrow','-D',f'part="{name}"',str(OUT/'enclosure.scad')],check=True,stdout=log,stderr=subprocess.STDOUT)
assert all(sha(OUT/n)==s for n,s in inputs.items()),'CAD inputs changed during export'


def inspect(path):
    data=path.read_bytes();n=struct.unpack_from('<I',data,80)[0]
    assert len(data)==84+50*n,'Expected binary STL'
    points={};faces=[];bounds=[[math.inf]*3,[-math.inf]*3];volume=0.;degenerate=0
    for i in range(n):
        record=struct.unpack_from('<12fH',data,84+50*i)
        xyz=[record[3+j*3:6+j*3] for j in range(3)];face=[]
        for v in xyz:
            assert all(math.isfinite(x) for x in v)
            q=tuple(round(x,5) for x in v)
            if q not in points:points[q]=len(points)
            face.append(points[q])
            for axis in range(3):bounds[0][axis]=min(bounds[0][axis],v[axis]);bounds[1][axis]=max(bounds[1][axis],v[axis])
        if len(set(face))<3:degenerate+=1
        faces.append(face)
        a,b,c=xyz
        volume+=(a[0]*(b[1]*c[2]-b[2]*c[1])+a[1]*(b[2]*c[0]-b[0]*c[2])+a[2]*(b[0]*c[1]-b[1]*c[0]))/6
    edges=collections.defaultdict(list);parent=list(range(n))
    def find(i):
        while parent[i]!=i:parent[i]=parent[parent[i]];i=parent[i]
        return i
    for i,f in enumerate(faces):
        for a,b in zip(f,f[1:]+f[:1]):edges[tuple(sorted([a,b]))].append((i,1 if a<b else -1))
    for items in edges.values():
        for i,_ in items[1:]:parent[find(i)]=find(items[0][0])
    bad=sum(len(x)!=2 or sum(v for _,v in x)!=0 for x in edges.values())
    components=len({find(i) for i in range(n)})
    result=dict(file=path.name,sha256=sha(path),triangles=n,vertices=len(points),bounds_mm=bounds,
                dimensions_mm=[bounds[1][i]-bounds[0][i] for i in range(3)],signed_volume_mm3=volume,
                bad_edge_count=bad,collapsed_faces_at_1e_5mm=degenerate,connected_surfaces=components,
                closed_oriented_manifold=bad==0 and degenerate==0 and components==1 and volume>0)
    assert result['closed_oriented_manifold'],result
    return result

rows=[inspect(OUT/f'{n}.stl') for n in parts]
b=p['body'];expected={'body':[b['size'][0]+1.3,b['size'][1],b['size'][2]],'lid':[b['size'][0],b['size'][1],b['lid_thickness']],
 'carrier':[41.6,33.6,9.4],'contact':[8.5,8.5,p['contacts']['stem_length']+p['contacts']['thread_length']+p['contacts']['head_thickness']],
 'boot':[b['size'][0]+3,b['size'][1]+3,b['size'][2]+b['lid_thickness']+4.8]}
for row in rows:
    name=Path(row['file']).stem
    if name in expected:assert all(abs(a-z)<.0001 for a,z in zip(row['dimensions_mm'],expected[name])),row
result=dict(cad_input_sha256=inputs,pcb_sha256=json.loads((OUT/'checks.json').read_text())['source_sha256'],meshes=rows,
            previews={n+'.png':sha(OUT/(n+'.png')) for n in ['exploded','section','mounted']},
            scope='Actual exported STL bounds, oriented-edge incidence and connected surfaces. This is mesh integrity only, not physical fit, manufacturing acceptance, sealing or IP qualification.')
(OUT/'mesh-checks.json').write_text(json.dumps(result,indent=2)+'\n')
print('Verified',len(rows),'closed exported meshes and 3 previews')
