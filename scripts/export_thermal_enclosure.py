#!/usr/bin/env python3
"""Export the r11 thermal-fit prototype with independent CAD collision controls."""
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
OUT=ROOT/'mechanical/swim-r11-thermal-fit'
RUNTIME=ROOT/'.runtime';RUNTIME.mkdir(exist_ok=True)
exe=os.environ.get('COLLAR_OPENSCAD') or shutil.which('openscad')
assert exe,'Install OpenSCAD or set COLLAR_OPENSCAD'
geometry_python=os.environ.get('COLLAR_GEOMETRY_PYTHON',str(ROOT/'.venv-dfm/bin/python'))
report=json.loads((OUT/'retention-checks.json').read_text())
assert report['result']=='CONDITIONAL_RETENTION_GEOMETRY_PASS','Run and resolve check_thermal_assembly.py first'
assert report['checker_sha256']==hashlib.sha256((ROOT/'scripts/check_thermal_assembly.py').read_bytes()).hexdigest(),'Stale retention checker'
assert report['retention_input_sha256']==hashlib.sha256((OUT/'retention.json').read_bytes()).hexdigest(),'Stale retention dimensions'
fit=json.loads((OUT/'antenna-fit.json').read_text())
for name,digest in {**fit['inputs'],**report['base_inputs']}.items():
    assert hashlib.sha256((ROOT/name).read_bytes()).hexdigest()==digest,'Stale geometry input: '+name
for name,digest in fit['generated'].items():
    assert hashlib.sha256((OUT/name).read_bytes()).hexdigest()==digest,'Stale generated input: '+name
assert all(c['pass_'] for c in report['checks']) and report['cable_motion']['all_sampled_cases_pass']
subprocess.run([sys.executable,str(ROOT/'scripts/build_swim_r08_geometry.py'),
                '--parameters',str(OUT/'parameters.json'),'--output',str(OUT)],check=True)
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
inputs={n:sha(OUT/n) for n in ['parameters.json','parameters.scad','enclosure.scad','populated.scad','fit-profile.json','components.native.json','antenna-fit.json','cables.scad','routing-controls.json','pack.scad','retention.json','retention.scad','retention-checks.json','thermal.json']}
p=json.loads((OUT/'parameters.json').read_text())
parts=['body','lid','carrier','contact','contact_seal','magnet_plug','dock','boot','retainer']


def inspect(path, allow_separate=False):
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
                closed_oriented_manifold=bad==0 and degenerate==0 and (components==1 or allow_separate) and volume>0)
    assert result['closed_oriented_manifold'],result
    return result


from concurrent.futures import ThreadPoolExecutor
import tempfile


def export_part(name):
    with (RUNTIME/f'swim-r11-{name}.log').open('w') as log:
        subprocess.run([exe,'-o',str(OUT/f'{name}.stl'),'--export-format','binstl',
                        '-D',f'part="{name}"',str(OUT/'enclosure.scad')],check=True,stdout=log,stderr=subprocess.STDOUT)
    result=inspect(OUT/f'{name}.stl')
    print('Mesh verified:',name,flush=True)
    return result


with ThreadPoolExecutor(max_workers=2) as workers:
    rows=list(workers.map(export_part,parts))
assert all(sha(OUT/n)==s for n,s in inputs.items()),'CAD inputs changed during export'
b=p['body'];expected={'body':[b['size'][0]+1.3,b['size'][1],b['size'][2]],'lid':[b['size'][0],b['size'][1],b['size'][2]-min([c['low'][2] for c in json.loads((OUT/'antenna-fit.json').read_text())['scenarios'][2]['clips']]+[13.0])+b['lid_thickness']],
 'carrier':[41.6,33.6,9.7], 'retainer':[41.8,34.3,2.1],'contact':[8.5,8.5,p['contacts']['stem_length']+p['contacts']['thread_length']+p['contacts']['head_thickness']],
 'boot':[b['size'][0]+3,b['size'][1]+3,b['size'][2]+b['lid_thickness']+4.8]}
for row in rows:
    name=Path(row['file']).stem
    if name in expected:assert all(abs(a-z)<.0001 for a,z in zip(row['dimensions_mm'],expected[name])),row

source=RUNTIME/'swim-r11-before-charge-carrier.scad'
cad=(OUT/'enclosure.scad').read_text()
old='for(b=carrier_reliefs)translate([b[0],b[1],-eps])cube([b[2]-b[0],b[3]-b[1],b[4]+eps]);'
assert old in cad
cad=cad.replace(old,'for(i=[0:len(carrier_reliefs)-1])if(i!=4)let(b=carrier_reliefs[i])translate([b[0],b[1],-eps])cube([b[2]-b[0],b[3]-b[1],b[4]+eps]);')
cad=cad.replace('for(p=carrier_leg_centers)', 'for(p=[[-19.8,-12],[-19.8,12],[19.8,-12],[19.8,12]])')
source.write_text(cad)
cases=[('current-carrier','interference',OUT/'enclosure.scad',True),
       ('old-U12-support','interference',source,False),
       ('guide_interference','guide_interference',OUT/'enclosure.scad',True),
       ('guide_control','guide_control',OUT/'enclosure.scad',False),
       ('retention_interference','retention_interference',OUT/'enclosure.scad',True),
       ('carrier_motion_interference','carrier_motion_interference',OUT/'enclosure.scad',True),
       ('key_interference','key_interference',OUT/'enclosure.scad',True),
       ('key_wrong_orientation','key_wrong_orientation',OUT/'enclosure.scad',False)]


def collision(case):
    label,part,source,expected_empty=case
    with tempfile.TemporaryDirectory(prefix='r11-boolean-',dir=RUNTIME) as temp:
        target=Path(temp)/'intersection.stl'
        run=subprocess.run([exe,'-o',str(target),'--export-format','binstl','-D',f'part="{part}"',str(source)],
                           env=dict(os.environ,OPENSCADPATH=str(OUT)),capture_output=True,text=True)
        empty='Current top level object is empty.' in run.stderr
        if expected_empty:
            assert run.returncode==1 and empty and not target.exists(),(label,run.stderr)
            volume=0
        else:
            assert run.returncode==0 and target.exists() and not empty,(label,run.stderr)
            volume=inspect(target,allow_separate=True)['signed_volume_mm3']
            assert volume>0,label
        result=dict(case=label,source_sha256=sha(source),returncode=run.returncode,empty=empty,
                    interference_volume_mm3=volume,diagnostic=run.stderr)
        print('CAD control verified:',label,flush=True)
        return result


with ThreadPoolExecutor(max_workers=2) as workers:
    controls=list(workers.map(collision,cases))
assert all(sha(OUT/n)==s for n,s in inputs.items()),'CAD inputs changed during collision checks'
previews=['exploded','section','mounted','populated','routing']
for name in previews:
    with (RUNTIME/f'swim-r11-{name}.log').open('w') as log:
        subprocess.run([exe,'-o',str(OUT/f'{name}.png'),'--imgsize','1600,1200','--projection','o',
                        '--viewall','--autocenter','--camera','0,0,0,65,0,35,140','--colorscheme','Tomorrow',
                        '-D',f'part="{name}"',str(OUT/'enclosure.scad')],check=True,stdout=log,stderr=subprocess.STDOUT)
assert all(sha(OUT/n)==s for n,s in inputs.items()),'CAD inputs changed during previews'
result=dict(cad_input_sha256=inputs,pcb_sha256=json.loads((OUT/'checks.json').read_text())['source_sha256'],meshes=rows,
            previews={n+'.png':sha(OUT/(n+'.png')) for n in previews},cad_controls=controls,
            exporter_sha256=sha(Path(__file__)),
            scope='Actual exported mesh integrity and CAD intersections. Conditional dimensional evidence only: no physical thermal, retention, manufacturing or ingress acceptance.')
(OUT/'mesh-checks.json').write_text(json.dumps(result,indent=2)+'\n')
print('Verified 9 closed meshes, 8 CAD controls and 5 previews',flush=True)
