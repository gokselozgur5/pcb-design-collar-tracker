#!/usr/bin/env python3
"""Screen all four cable routes at correlated static PCB poses; no physical release."""
import copy,hashlib,json,sys
from pathlib import Path
import numpy as np
from scipy.spatial import cKDTree
from shapely import points,distance,covers

from internal_harness_geometry import evaluate
from antenna_cable_geometry import curve_separation,point_box_distance
from check_thermal_assembly import retention_solids
from check_thermal_cables import prism_gap
from audit_populated_fit import rounded_rect
from check_internal_harness import check as check_charge
ROOT=Path(__file__).resolve().parents[1]
OUT=ROOT/'mechanical/swim-r17-cable-integration'
base=ROOT/'mechanical/swim-r11-thermal-fit'
p=json.loads((base/'parameters.json').read_text());r=json.loads((base/'retention.json').read_text());q=r['motion_screen']
parts=json.loads((base/'antenna-fit.json').read_text())['scenarios'][2]['parts']
old=json.loads((base/'retention-checks.json').read_text())['cable_motion']['cases']
rails,ribs,posts,frame=retention_solids(p,r);frame_shift=q['retainer_to_body_xy_mm']+.025+q['thermal_xy_allowance_mm']
frame=[(name,s.buffer(frame_shift,join_style='mitre'),lo+q['retainer_bottom_z_mm'][0]-r['frame']['bottom_z_mm'],hi+q['retainer_bottom_z_mm'][1]-r['frame']['bottom_z_mm']+.05) for name,s,lo,hi in frame]
rails=[(name,s.buffer(.36+.025+q['thermal_xy_allowance_mm'],join_style='mitre'),lo-.05-q['thermal_z_allowance_mm'],hi+.05+q['thermal_z_allowance_mm']) for name,s,lo,hi in rails]
solids=rails+ribs+posts+frame
cavity=rounded_rect(*p['body']['cavity'],p['body']['cavity_radius']);radius=.715

def check_rf(model,indices=None):
    # The curved bore is cut along the frozen SCAD polyline, not a newly
    # proposed cable curve. Use that actual polyline for the aperture check.
    line=next(line for line in (base/'cables.scad').read_text().splitlines() if line.startswith('cable_1 = '))
    guide_path=np.array(json.loads(line.split('=',1)[1].strip().rstrip(';')))
    local=(np.minimum(guide_path[:-1,1],guide_path[1:,1])<6)&(np.maximum(guide_path[:-1,1],guide_path[1:,1])>-.4)
    starts=guide_path[:-1][local];vectors=np.diff(guide_path,axis=0)[local]
    lengths_squared=np.einsum('ij,ij->i',vectors,vectors)
    results=[]
    for row in model['poses']:
        if indices is not None and row['pose_index'] not in indices:continue
        curves=[evaluate(c['control_points_mm']) for c in row['cables']];shift=np.array(row['pcb_pose_mm'])-[0,0,11.24088];checks=[]
        def add(name,value,minimum=0):checks.append(dict(name=name,value=float(value),minimum=minimum,pass_=bool(value>=minimum-1e-8)))
        for cable,curve,previous in zip(row['cables'],curves,old[row['pose_index']]['cables']):
            name=cable['name'];xyz=curve['xyz'];step=curve['travel_bound'];er=radius+step/2
            add(name+' connector endpoint',1e-8-np.linalg.norm(xyz[0]-np.array(previous['control_points_mm'][0])))
            add(name+' FPC endpoint',1e-8-np.linalg.norm(xyz[-1]-np.array(previous['control_points_mm'][-1])))
            add(name+' fixed-length lower tolerance',curve['arc_lower'][-1]-(98.5-.001))
            add(name+' fixed-length upper tolerance',98.5+.001-curve['arc_upper'][-1])
            add(name+' continuous bend bound',curve['radius_lower'],3)
            allowance=np.array([q['thermal_xy_allowance_mm']]*2+[q['thermal_z_allowance_mm']]);gaps=[]
            for part in parts:
                if part['ref']==('J1' if name=='LTE' else 'J2'):continue
                a,b,c,d=part['envelope_xy_bounds_mm'];lo,hi=part['envelope_z_mm']
                gaps.append(float(point_box_distance(xyz,np.array([a,b,lo])+shift-allowance,np.array([c,d,hi])+shift+allowance).min())-er)
            add(name+' populated components',min(gaps),.2)
            add(name+' swept retention',min(prism_gap(xyz,s,lo,hi,radius,step) for _,s,lo,hi in solids),.2)
            xy=points(xyz[:,:2]);wall=float(distance(cavity.boundary,xy).min())-er if covers(cavity,xy).all() else -1
            add(name+' cavity walls',wall,.2);add(name+' lid roof',p['body']['size'][2]-xyz[:,2].max()-er,0)
            add(name+' nonlocal self clearance',curve_separation(xyz,xyz,curve['arc_lower'],3)-2*radius-step,.2)
            for i,ant in enumerate(p['antenna_reservations']):
                center,size=np.array(ant['center']),np.array(ant['size']);lo,hi=center-size/2,center+size/2
                own=(i==0)==(name=='LTE');joint=np.zeros(len(xyz),bool)
                if own:joint=((curve['arc_upper'][-1]-curve['arc_lower']<=20)&np.all(xyz[:,:2]>=lo[:2]-radius-.2,axis=1)&np.all(xyz[:,:2]<=hi[:2]+radius+.2,axis=1))
                add(name+' '+ant['label'],float(point_box_distance(xyz[~joint],lo,hi).min())-er,.2)
            add(name+' bottom bodies',np.array(cable['control_points_mm'])[:,2].min()-(q['pcb_top_z_mm'][1]-.71)-er,.2)
            intersects=np.zeros(len(xyz),bool)
            for clip in model['clips']:
                intersects|=point_box_distance(xyz,np.array(clip['low']),np.array(clip['high'])+[0,0,.1])<=er
            bore_margins=[]
            for clip in model['clips']:
                if clip['cable']!=name:continue
                v=xyz[intersects]-np.array(clip['center']);axis=np.array(clip['tangent']);axis/=np.linalg.norm(axis)
                if clip['name']=='GNSS-2':
                    offsets=xyz[intersects,None,:]-starts[None,:,:]
                    fraction=np.clip(np.einsum('ijk,jk->ij',offsets,vectors)/lengths_squared,0,1)
                    ds=np.linalg.norm(offsets-fraction[:,:,None]*vectors,axis=2).min(axis=1)
                    margin=clip['bore_diameter_mm']/2-ds-er
                else:
                    along=v@axis;ds=np.linalg.norm(v-along[:,None]*axis,axis=1)
                    margin=np.minimum(clip['bore_diameter_mm']/2-ds-er,6-np.abs(along)-er)
                bore_margins.append(margin)
            add(name+' inside own guide bores',np.max(np.array(bore_margins),axis=0).min(),0)
        add('RF pair separation',cKDTree(curves[0]['xyz']).query(curves[1]['xyz'])[0].min()-2*radius-sum(c['travel_bound']/2 for c in curves),.2)
        failures=[c for c in checks if not c['pass_']];results.append(dict(pose_index=row['pose_index'],checks=checks,pass_=not failures))
    return results


def validate_model(model):
    if [c['pose_index'] for c in model['poses']] != list(range(27)):
        raise ValueError('Missing, duplicated or reordered PCB pose')
    if any(c['pcb_pose_mm'] != old[i]['pcb_pose_mm'] for i,c in enumerate(model['poses'])):
        raise ValueError('Correlated PCB pose changed')
    for pose in model['poses']:
        if [c['name'] for c in pose['cables']] != ['LTE','GNSS']:
            raise ValueError('RF cable identity or order changed')
        for control in [c['control_points_mm'] for c in pose['cables']]+pose['charge_controls']:
            c=np.asarray(control,dtype=float)
            if c.ndim!=2 or c.shape[1]!=3 or len(c)<4 or not np.isfinite(c).all():
                raise ValueError('Invalid spline control points')
    expected_clips=json.loads((base/'antenna-fit.json').read_text())['scenarios'][2]['clips']
    if model['clips'] != expected_clips:
        raise ValueError('This candidate must use the existing physical lid guides')
    if model['rf_target_length_mm'] != 98.5:
        raise ValueError('RF cable target length changed')
    if any(model[k] for k in ['physical_qualification','manufacturing_release','continuous_motion_accepted']):
        raise ValueError('Static curves cannot establish physical or motion acceptance')


def check_charge_pose(model,index):
    spec=json.loads((ROOT/'assembly/internal-charge-r02/harness.json').read_text())
    nominal=[evaluate(w['controls_mm']) for w in spec['wires']]
    targets=[float((c['arc_lower'][-1]+c['arc_upper'][-1])/2) for c in nominal]
    if len(model['wire_target_lengths_mm']) != 2 or any(abs(a-b)>1e-6 for a,b in zip(targets,model['wire_target_lengths_mm'])):
        raise ValueError('Charge-wire target lengths changed')
    row=model['poses'][index]
    for wire,control in zip(spec['wires'],row['charge_controls'],strict=True):
        wire['controls_mm']=control
    result=check_charge(spec,pose_index=index,rf_cables=row['cables'],rf_clips=model['clips'])
    if result['result']=='HOLD':
        # A smaller travel bound can resolve an overly conservative interval
        # screen. Every original check and physical limit is retained.
        result=check_charge(spec,pose_index=index,rf_cables=row['cables'],rf_clips=model['clips'],curve_count=16001)
    lengths=[w['length_interval_mm'] for w in result['wires']]
    length_pass=all(lo>=target-.001 and hi<=target+.001 for (lo,hi),target in zip(lengths,targets))
    return dict(pose_index=index,checks=result['checks'],wires=result['wires'],
                fixed_length_intervals_mm=lengths,fixed_length_pass=length_pass,
                pass_=length_pass and all(c['pass_'] for c in result['checks']))


def build():
    names=['scripts/check_cable_integration.py','scripts/check_internal_harness.py',
           'scripts/internal_harness_geometry.py','scripts/thermal_cable_geometry.py',
           'scripts/antenna_cable_geometry.py','scripts/check_thermal_assembly.py',
           'scripts/check_thermal_cables.py','scripts/audit_populated_fit.py',
           'assembly/internal-charge-r02/harness.json','assembly/internal-charge-r02/sources.json',
           'mechanical/swim-r16-contact-retention/contact.json',
           'experiments/power-r05l-charge-interlock/evidence/native-netlist.json',
           'experiments/power-r05l-charge-interlock/evidence/route-geometry.json']
    paths=[ROOT/n for n in names]+[OUT/'routing.json']+[base/n for n in ['parameters.json','retention.json','retention-checks.json','antenna-fit.json','cables.scad','enclosure.scad']]
    native=json.loads((ROOT/names[-1]).read_text());paths.append(ROOT/native['source'])
    inputs={str(path.relative_to(ROOT)):hashlib.sha256(path.read_bytes()).hexdigest() for path in paths}
    model=json.loads((OUT/'routing.json').read_text());validate_model(model)
    rf=check_rf(model);rows=[]
    for i,rf_row in enumerate(rf):
        charge=check_charge_pose(model,i)
        rows.append(dict(pose_index=i,pcb_pose_mm=model['poses'][i]['pcb_pose_mm'],
                         rf=rf_row,charge=charge,pass_=rf_row['pass_'] and charge['pass_']))
        failures=[c['name'] for part in [rf_row,charge] for c in part['checks'] if not c['pass_']]
        print('Pose',i,'PASS' if rows[-1]['pass_'] else 'HOLD',failures,flush=True)
    if any(hashlib.sha256((ROOT/name).read_bytes()).hexdigest()!=digest for name,digest in inputs.items()):
        raise ValueError('A source changed during the integrated geometry check')
    result=dict(result='SAMPLED_FOUR_CABLE_GEOMETRY_PASS' if all(r['pass_'] for r in rows) else 'HOLD',
                inputs=inputs,
                poses=rows,passing_poses=sum(r['pass_'] for r in rows),total_poses=27,
                fixed_length_numerical_tolerance_mm=.001,
                physical_qualification=False,manufacturing_release=False,continuous_motion_accepted=False,
                scope='Continuous geometric bounds on individual static curves at 27 correlated PCB poses. Existing lid guide bores are checked. No continuous deformation, cable cut/thermal tolerance, force, restraint, service motion or physical qualification.')
    (OUT/'checks.json').write_text(json.dumps(result,indent=2)+'\n')
    print(result['result'],result['passing_poses'],'/ 27',flush=True)
    return result


if __name__=='__main__':
    raise SystemExit(build()['result']=='HOLD')
