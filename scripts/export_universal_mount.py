#!/usr/bin/env python3
"""Export the collar attachment and check actual solids and installed paths."""
import argparse
from concurrent.futures import ThreadPoolExecutor
import hashlib
import json
from pathlib import Path
import subprocess
import struct
from inspect_enclosure_mesh import inspect

ROOT=Path(__file__).resolve().parents[1]
OUT=ROOT/'mechanical/universal-mount-r01'
RUN=ROOT/'.runtime/universal-mount-r01'
SCAD=OUT/'mount.scad'
CONFIGS={
 'narrow':{'collar_width':8,'collar_thickness':1},
 'standard':{'collar_width':25,'collar_thickness':3},
 'wide':{'collar_width':60,'collar_thickness':8},
 'rope_small':{'round_collar':True,'rope_diameter':4},
 'rope':{'round_collar':True,'rope_diameter':8},
 'rope_large':{'round_collar':True,'rope_diameter':16},
}

def run(name,part,defines=None,png=False,camera='0,0,0,65,0,35,180',size='1800,1400'):
    ext='png' if png else 'stl';dest=(RUN if 'collision' in name else OUT)/(name+'.'+ext)
    args=['openscad','-o',str(dest)]
    if png:args+=['--imgsize',size,'--projection','o','--viewall','--autocenter','--camera',camera,'--colorscheme','Tomorrow']
    else:args+=['--export-format','binstl']
    for key,value in {'part':part,**(defines or {})}.items():args+=['-D',key+'='+json.dumps(value)]
    result=subprocess.run(args+[str(SCAD)],capture_output=True,text=True)
    log=result.stdout+result.stderr;(RUN/(name+'.log')).write_text(log)
    if result.returncode and 'Current top level object is empty.' not in log:
        raise RuntimeError(name+': '+log[-1200:])
    # Exact tangency can leave CGAL edges but no surface or volume. Accept only
    # an empty binary STL in a collision query, never a defective delivered part.
    boundary_only=('collision' in name and result.returncode==0 and dest.exists()
                   and len(dest.read_bytes())==84 and struct.unpack_from('<I',dest.read_bytes(),80)[0]==0
                   and 'Facets:          0' in log and 'ERROR:' not in log)
    if boundary_only:
        print(name,'ZERO-VOLUME CONTACT',flush=True)
        return None
    if 'WARNING:' in log or 'ERROR:' in log:raise RuntimeError(name+': '+log[-1800:])
    print(name, 'EMPTY' if result.returncode else 'OK',flush=True)
    return dest if result.returncode==0 else None

def solids():
    specs=[('boot','boot',{}),('flat_pad','flat_pad',{}),('round_pad','round_pad',{}),
           ('strap_short','strap',{'strap_length':120}),('strap_long','strap',{'strap_length':220})]
    specs += [(name,name,{}) for name in ['body','lid','carrier','retainer','battery','pcb','pcb_substrate','pcb_components','contacts','gasket','antennas','terminals','charge_wires','fasteners','rf','staking']]
    specs += [(name+'_'+kind,kind,values) for name,values in CONFIGS.items() for kind in ['collar','installed_straps']]
    with ThreadPoolExecutor(max_workers=3) as pool:
        paths=list(pool.map(lambda item:run(*item),specs))
    evidence=[]
    for path in paths:
        row=inspect(path,allow_separate=path.stem not in ['boot','flat_pad','round_pad','strap_short','strap_long'])
        evidence.append(row)
    (OUT/'mesh-checks.json').write_text(json.dumps({'scope':'Exported STL topology and nominal bounds; not strength or waterproof qualification','meshes':evidence},indent=2)+'\n')

def checks():
    jobs=[('boot_shell_collision','boot_shell_collision',{})]
    for name,values in CONFIGS.items():
        for check in ['strap_boot_collision','strap_collar_collision','pad_strap_collision','pad_collar_collision']:
            jobs.append((name+'_'+check,check,values))
    with ThreadPoolExecutor(max_workers=3) as pool:
        paths=list(pool.map(lambda item:run(*item),jobs))
    rows=[]
    for (name,part,values),path in zip(jobs,paths):
        rows.append({'name':name,'parameters':values,'no_intersection':path is None,
                     'zero_volume_boundary_contact': 'Facets:          0' in (RUN/(name+'.log')).read_text(),
                     'volume_mm3':0 if path is None else inspect(path,allow_separate=True)['signed_volume_mm3']})
    (OUT/'fit-checks.json').write_text(json.dumps({'scope':'Nominal CAD intersections of strap envelopes. Does not prove fitted closure, elasticity, strength, grip or every collar.','cases':CONFIGS,'checks':rows,'all_nominal_intersections_empty':all(r['no_intersection'] for r in rows)},indent=2)+'\n')
    assert all(r['no_intersection'] for r in rows),[r for r in rows if not r['no_intersection']]

def previews():
    jobs=[('mounted','mounted',{}),('exploded','exploded',{}),
          ('underside','mounted',{},False),('section','mount_section',{})]
    for name,part,params,*extra in jobs:
        run(name,part,params,png=True,camera='0,0,0,125,0,35,180' if name=='underside' else '0,0,0,65,0,35,180',size='1600,1800' if name=='exploded' else '1800,1400')
    run('narrow','mounted',CONFIGS['narrow'],png=True)
    run('wide','mounted',CONFIGS['wide'],png=True)
    run('rope','mounted',CONFIGS['rope'],png=True,camera='0,0,0,100,0,35,180')

if __name__=='__main__':
    ap=argparse.ArgumentParser();ap.add_argument('stage',choices=['solids','checks','previews']);args=ap.parse_args()
    RUN.mkdir(exist_ok=True)
    {'solids':solids,'checks':checks,'previews':previews}[args.stage]()
