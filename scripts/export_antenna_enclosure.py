#!/usr/bin/env python3
"""Export the populated r08 antenna revision and independently check its CAD intersections."""
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
OUT=ROOT/'mechanical/swim-r08-antennas'
RUNTIME=ROOT/'.runtime';RUNTIME.mkdir(exist_ok=True)
exe=os.environ.get('COLLAR_OPENSCAD') or shutil.which('openscad')
assert exe,'Install OpenSCAD or set COLLAR_OPENSCAD'
subprocess.run([sys.executable,str(ROOT/'scripts/build_swim_r08_geometry.py'),
                '--parameters',str(OUT/'parameters.json'),'--output',str(OUT)],check=True)
geometry_python=os.environ.get('COLLAR_GEOMETRY_PYTHON',str(ROOT/'.venv-dfm/bin/python'))
subprocess.run([geometry_python,str(ROOT/'scripts/check_antenna_assembly.py')],check=True)
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
inputs={n:sha(OUT/n) for n in ['parameters.json','parameters.scad','enclosure.scad','populated.scad','fit-profile.json','components.native.json','antenna-fit.json','cables.scad','routing-controls.json']}
p=json.loads((OUT/'parameters.json').read_text())
parts=['body','lid','carrier','contact','contact_seal','magnet_plug','dock','boot']
for name in parts:
    with (RUNTIME/f'swim-r08-{name}.log').open('w') as log:
        subprocess.run([exe,'-o',str(OUT/f'{name}.stl'),'--export-format','binstl','-D',f'part="{name}"',str(OUT/'enclosure.scad')],check=True,stdout=log,stderr=subprocess.STDOUT)
for name in ['exploded','section','mounted','populated','routing']:
    with (RUNTIME/f'swim-r08-{name}.log').open('w') as log:
        subprocess.run([exe,'-o',str(OUT/f'{name}.png'),'--imgsize','1600,1200','--projection','o','--viewall','--autocenter','--camera','0,0,0,65,0,35,140','--colorscheme','Tomorrow','-D',f'part="{name}"',str(OUT/'enclosure.scad')],check=True,stdout=log,stderr=subprocess.STDOUT)
assert all(sha(OUT/n)==s for n,s in inputs.items()),'CAD inputs changed during export'


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

rows=[inspect(OUT/f'{n}.stl') for n in parts]
b=p['body'];expected={'body':[b['size'][0]+1.3,b['size'][1],b['size'][2]],'lid':[b['size'][0],b['size'][1],b['size'][2]-min(c['low'][2] for c in json.loads((OUT/'antenna-fit.json').read_text())['scenarios'][2]['clips'])+b['lid_thickness']],
 'carrier':[41.6,33.6,9.4],'contact':[8.5,8.5,p['contacts']['stem_length']+p['contacts']['thread_length']+p['contacts']['head_thickness']],
 'boot':[b['size'][0]+3,b['size'][1]+3,b['size'][2]+b['lid_thickness']+4.8]}
for row in rows:
    name=Path(row['file']).stem
    if name in expected:assert all(abs(a-z)<.0001 for a,z in zip(row['dimensions_mm'],expected[name])),row
# Independent CAD boolean: current envelopes with 0.20 mm clearance must be
# empty, while restoring the original carrier must produce an actual solid.
# Exit code alone is insufficient: require the explicit empty-object diagnostic.
intersection_results=[]
for legacy in (False,True):
    label='before-charge-carrier' if legacy else 'current-carrier'
    source=OUT/'enclosure.scad'
    if legacy:
        source=RUNTIME/'swim-r08-before-charge-carrier.scad'
        cad=(OUT/'enclosure.scad').read_text()
        old='for(b=carrier_reliefs)translate([b[0],b[1],-eps])cube([b[2]-b[0],b[3]-b[1],b[4]+eps]);'
        assert old in cad
        cad=cad.replace(old,'for(i=[0:len(carrier_reliefs)-2])let(b=carrier_reliefs[i])translate([b[0],b[1],-eps])cube([b[2]-b[0],b[3]-b[1],b[4]+eps]);')
        cad=cad.replace('for(p=carrier_leg_centers)', 'for(p=[[-19.8,-12],[-19.8,12],[19.8,-12],[19.8,12]])')
        source.write_text(cad)
    target=RUNTIME/('swim-r08-'+label+'-intersection.stl')
    # A unique directory prevents stale output being mistaken for this run.
    import tempfile
    with tempfile.TemporaryDirectory(prefix='fit-boolean-',dir=RUNTIME) as temp:
        target=Path(temp)/'intersection.stl'
        env=dict(os.environ,OPENSCADPATH=str(OUT))
        run=subprocess.run([exe,'-o',str(target),'--export-format','binstl','-D','part="interference"',str(source)],env=env,capture_output=True,text=True)
        empty='Current top level object is empty.' in run.stderr
        if legacy:
            assert run.returncode==0 and target.exists() and not empty,run.stderr
            result_mesh=inspect(target)
            assert result_mesh['signed_volume_mm3']>0
        else:
            assert run.returncode==1 and empty and not target.exists(),run.stderr
            result_mesh=None
        intersection_results.append(dict(case=label,source_sha256=sha(source),returncode=run.returncode,
                                         empty=empty,interference_volume_mm3=result_mesh['signed_volume_mm3'] if result_mesh else 0,
                                         diagnostic=run.stderr))
# Independent curved-cable/guide collision checks. The deliberately undersized
# channel must fail. The real channel must leave the inflated cable sweep empty.
# OpenSCAD's 12-sided spheres are enlarged by cos(15)^-2; another 0.015 mm covers
# the sampled centerline chord. The nominal dense check is recorded separately.
guide_results=[]
for part in ['guide_interference','guide_control']:
    with tempfile.TemporaryDirectory(prefix='guide-boolean-',dir=RUNTIME) as temp:
        target=Path(temp)/'intersection.stl'
        run=subprocess.run([exe,'-o',str(target),'--export-format','binstl','-D',f'part="{part}"',str(OUT/'enclosure.scad')],capture_output=True,text=True)
        empty='Current top level object is empty.' in run.stderr
        if part=='guide_interference':
            assert run.returncode==1 and empty and not target.exists(),run.stderr
            volume=0
        else:
            assert run.returncode==0 and target.exists() and not empty,run.stderr
            volume=inspect(target,allow_separate=True)['signed_volume_mm3']
            assert volume>0
        guide_results.append(dict(case=part,returncode=run.returncode,empty=empty,
                                  interference_volume_mm3=volume,diagnostic=run.stderr))
assert all(sha(OUT/n)==digest for n,digest in inputs.items()),'CAD inputs changed during boolean checks'
result=dict(cad_input_sha256=inputs,pcb_sha256=json.loads((OUT/'checks.json').read_text())['source_sha256'],meshes=rows,
            previews={n+'.png':sha(OUT/(n+'.png')) for n in ['exploded','section','mounted','populated','routing']},
            intersection_controls=intersection_results,guide_intersection_controls=guide_results,exporter_sha256=sha(Path(__file__)),
            scope='Actual exported STL bounds, oriented-edge incidence and connected surfaces. This is mesh integrity only, not physical fit, manufacturing acceptance, sealing or IP qualification.')
(OUT/'mesh-checks.json').write_text(json.dumps(result,indent=2)+'\n')
print('Verified',len(rows),'closed exported meshes, 5 previews and CAD clearance positive/negative controls')
