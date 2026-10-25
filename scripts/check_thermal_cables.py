#!/usr/bin/env python3
"""Check all sampled moving cable paths against the new mechanical parts.

This supplements the component/length/bend checks without regenerating CAD.
No cable deformation outside the stated pose samples is qualified.
"""
import hashlib
import json
from pathlib import Path

import numpy as np
from shapely import covers, distance, points

from antenna_cable_geometry import curve_separation, point_box_distance
from thermal_cable_geometry import spline
from audit_populated_fit import rounded_rect
from check_thermal_assembly import retention_solids

ROOT=Path(__file__).resolve().parents[1]
OUT=ROOT/'mechanical/swim-r11-thermal-fit'
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()


def prism_gap(xyz, shape, low, high, radius, step):
    planar=distance(shape,points(xyz[:,:2]))
    vertical=np.maximum(np.maximum(low-xyz[:,2],xyz[:,2]-high),0)
    return float(np.hypot(planar,vertical).min())-radius-step/2


def build():
    paths=[OUT/n for n in ['parameters.json','retention.json','routing-controls.json','retention-checks.json']]
    p,r,controls,motion=[json.loads(path.read_text()) for path in paths]
    deps=[Path(__file__),ROOT/'scripts/check_thermal_assembly.py',ROOT/'scripts/antenna_cable_geometry.py',ROOT/'scripts/thermal_cable_geometry.py']
    inputs={str(path.relative_to(ROOT)):sha(path) for path in paths+deps}
    rails,ribs,posts,retainer=retention_solids(p,r)
    q=r['motion_screen'];frame_shift=q['retainer_to_body_xy_mm']+.025+q['thermal_xy_allowance_mm']
    swept_retainer=[(name,shape.buffer(frame_shift,join_style='mitre'),
                     low+r['motion_screen']['retainer_bottom_z_mm'][0]-r['frame']['bottom_z_mm'],
                     high+r['motion_screen']['retainer_bottom_z_mm'][1]-r['frame']['bottom_z_mm']+.05)
                    for name,shape,low,high in retainer]
    rails=[(name,shape.buffer(.36+.025+q['thermal_xy_allowance_mm'],join_style='mitre'),lo-.05-q['thermal_z_allowance_mm'],hi+.05+q['thermal_z_allowance_mm']) for name,shape,lo,hi in rails]
    solids=rails+ribs+posts+swept_retainer
    cavity=rounded_rect(*p['body']['cavity'],p['body']['cavity_radius'])
    nominal_top=p['pcb']['bottom_z']+p['pcb']['size'][2]
    radius=p['cable_model']['diameter_mm']/2+p['cable_model']['centerline_position_allowance_mm']
    cases=[]
    for case in motion['cable_motion']['cases']:
        dx,dy,top=case['pcb_pose_mm'];shift=np.array([dx,dy,top-nominal_top]);rows=[]
        for saved in case['cables']:
            name=saved['name'];control=np.array(saved['control_points_mm'])
            xyz,arc,radii,step=spline(control,4001)
            checks=[]
            xy_points=points(xyz[:,:2])
            wall=float(distance(cavity.boundary,xy_points).min())-radius-step/2
            checks.append(dict(name='cavity wall',pass_=bool(covers(cavity,xy_points).all() and wall>=.2),gap_mm=wall))
            lid=p['body']['size'][2]-float(xyz[:,2].max())-radius-step/2
            checks.append(dict(name='lid',pass_=lid>=0,gap_mm=lid))
            self_gap=curve_separation(xyz,xyz,arc,3.)-2*radius-step
            checks.append(dict(name='nonlocal self clearance',pass_=self_gap>=.2,gap_mm=self_gap))
            mechanical=[(prism_gap(xyz,s,lo,hi,radius,step),label) for label,s,lo,hi in solids]
            clearance,obstacle=min(mechanical)
            checks.append(dict(name='new retention solids',pass_=clearance>=.2,gap_mm=clearance,obstacle=obstacle))
            for i,ant in enumerate(p['antenna_reservations']):
                center,size=np.array(ant['center']),np.array(ant['size']);lo,hi=center-size/2,center+size/2
                own=(i==0)==(name=='LTE');samples=xyz
                if own:
                    joint=((arc[-1]-arc<=20)&(xyz[:,0]>=lo[0]-radius-.2)&(xyz[:,0]<=hi[0]+radius+.2)
                           &(xyz[:,1]>=lo[1]-radius-.2)&(xyz[:,1]<=hi[1]+radius+.2))
                    samples=xyz[~joint]
                gap=float(point_box_distance(samples,lo,hi).min())-radius-step/2
                checks.append(dict(name=ant['label'],pass_=gap>=.2,gap_mm=gap,intentional_feed_joint_excluded=own))
            # A cubic B-spline remains inside its control-point convex hull.
            # Every possible bottom-side body is below maximum board underside
            # Z=11.26, so this also covers the thickness extremes independently.
            bottom_gap=float(control[:,2].min())-(q['pcb_top_z_mm'][1]-.71)-radius-step/2
            checks.append(dict(name='all bottom-side bodies',pass_=bottom_gap>=.2,gap_mm=bottom_gap))
            rows.append(dict(name=name,checks=checks,pass_=all(c['pass_'] for c in checks)))
        cases.append(dict(pcb_pose_mm=case['pcb_pose_mm'],cables=rows,pass_=all(x['pass_'] for x in rows)))
    report=dict(result='SAMPLED_CABLE_CLEARANCE_PASS' if all(c['pass_'] for c in cases) else 'FAIL',
                inputs=inputs,cases=cases,physical_flex_qualified=False,
                scope='27 sampled endpoint poses: new retention solids, walls/lid, antennas, nonlocal self clearance and bottom-side thickness bound. Own feed-joint exclusion matches the preserved antenna model. No full continuous-motion or physical qualification.')
    (OUT/'moving-cable-checks.json').write_text(json.dumps(report,indent=2)+'\n')
    failures=[dict(pose=c['pcb_pose_mm'],cable=x['name'],check=v) for c in cases for x in c['cables'] for v in x['checks'] if not v['pass_']]
    print(json.dumps(dict(result=report['result'],cases=len(cases),failures=failures),indent=2))
    return report


if __name__=='__main__':
    raise SystemExit(build()['result']=='FAIL')
