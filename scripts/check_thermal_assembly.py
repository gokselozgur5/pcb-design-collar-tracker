#!/usr/bin/env python3
"""Build the r11 thermal-fit candidate with radial frame/carrier keys.

This is geometric evidence, not a retention-force, vibration or ingress result.
The original PCB, supplier request and r09 study remain byte-preserved.
"""
import copy
import hashlib
import itertools
import json
from pathlib import Path

import numpy as np
from shapely.affinity import rotate, translate
from shapely.geometry import box
from shapely.ops import unary_union

import check_antenna_assembly as antenna
from thermal_fit_bounds import evaluate as thermal_bounds
from antenna_cable_geometry import curve_separation, point_box_distance
from thermal_cable_geometry import spline
from audit_populated_fit import carrier_solids, rounded_rect, solid_distance

ROOT = Path(__file__).resolve().parents[1]
BASE = ROOT/'mechanical/swim-r09-pack-request'
OUT = ROOT/'mechanical/swim-r11-thermal-fit'
SHA = lambda p: hashlib.sha256(p.read_bytes()).hexdigest()


def tune_handle(control, target=98.5, count=801):
    """Find a fixed-length candidate by adjusting only the initial tangent handle."""
    points = np.array(control, dtype=float)
    direction = points[1]-points[0]
    direction /= np.linalg.norm(direction)

    def evaluate(length):
        p = points.copy()
        p[1] = p[0]+direction*length
        return p, spline(p, count)[1][-1]

    low, high = .1, 15.
    assert evaluate(low)[1] < target < evaluate(high)[1], 'No fixed-length handle bracket'
    for _ in range(17):
        middle = (low+high)/2
        if evaluate(middle)[1] < target:
            low = middle
        else:
            high = middle
    p, _ = evaluate((low+high)/2)
    return p, (low+high)/2


def frame_shape(r):
    f = r['frame']
    outer = rounded_rect(*f['outer_mm'], f['outer_radius_mm'])
    inner = rounded_rect(*f['inner_mm'], f['inner_radius_mm'])
    tabs = unary_union([box(*b) for b in r['capture_tabs_xy_mm']+r['north_tabs_xy_mm']])
    return outer.intersection(outer.difference(inner).union(tabs))


def retention_solids(p, r):
    bottom = p['pcb']['bottom_z']-1.5
    rails = []
    for bounds in r['guide_rails_xy_mm']:
        shape = box(*bounds)
        levels = sorted({bottom, r['key_slot_bottom_z_mm'], r['guide_top_z_mm']})
        for low, high in zip(levels, levels[1:]):
            section = shape.difference(box(*r['sim_bridge_relief_xy_mm']))
            for cut in r.get('guide_reliefs_xy_mm', []):
                section = section.difference(box(*cut))
            if low >= r['key_slot_bottom_z_mm']:
                for key in r['radial_keys']:
                    section = section.difference(box(*key['slot_xy_mm']))
            if not section.is_empty:
                rails.append(('carrier guide rail', section, low, high))
    ribs = [('body locator',box(*b),p['body']['floor'],p['pcb']['bottom_z']) for b in r['locator_ribs_xy_mm']]
    posts = [('lid hold-down',box(*b),r['lid_post_bottom_z_mm'],p['body']['size'][2]) for b in r['lid_posts_xy_mm']]
    f=r['frame']
    retainer=[('retainer frame',frame_shape(r),f['bottom_z_mm'],f['bottom_z_mm']+f['height_mm'])]
    retainer += [(key['name']+' radial key',box(*key['xy_mm']),r['key_bottom_z_mm'],f['bottom_z_mm']+.1) for key in r['radial_keys']]
    return rails,ribs,posts,retainer


def bounds_and_screens(p, profile, r, nominal_parts):
    spec=json.loads((OUT/'thermal.json').read_text())
    thermal=thermal_bounds(p,r,spec)
    motion=r['motion_screen'];gap=motion['minimum_component_gap_mm'];xy_allow=motion['thermal_xy_allowance_mm'];z_allow=motion['thermal_z_allowance_mm']
    rails,ribs,posts,retainer=retention_solids(p,r)
    lower=[x for x in carrier_solids(p,profile['carrier_reliefs']) if x[0] not in ('carrier guide','carrier leg')]
    lower += [('carrier leg',box(x-.5,y-1,x+.5,y+1),p['body']['floor'],p['pcb']['bottom_z']-1.5) for x,y in p['carrier_leg_centers_mm']]
    checks=[dict(name='Declared thermal interface bounds',pass_=all(c['pass_'] for c in thermal['checks']),failures=[c for c in thermal['checks'] if not c['pass_']])]
    checks.append(dict(name='Motion screens cover thermal stack',pass_=
        motion['pcb_to_carrier_xy_mm']>=thermal['pcb_to_carrier_pointwise_mm']
        and motion['pcb_to_body_xy_mm']>=thermal['pcb_to_body_pointwise_mm']
        and motion['retainer_to_carrier_pointwise_mm']>=thermal['radial_key_pointwise_bound_mm']
        and motion['pcb_top_z_mm'][0]<=thermal['pcb_top_z_mm'][0]
        and motion['pcb_top_z_mm'][1]>=thermal['pcb_top_z_mm'][1]
        and motion['retainer_bottom_z_mm'][0]<=thermal['retainer_bottom_z_mm'][0]
        and motion['retainer_bottom_z_mm'][1]>=thermal['retainer_bottom_z_mm'][1]))
    minimums={};failures=[];body_boxes=[];frame_boxes=[];carrier_boxes=[]
    top_min,top_max=motion['pcb_top_z_mm'];frame_gap_max=motion['retainer_bottom_z_mm'][1]-top_min
    frame_relative=motion['pcb_to_carrier_xy_mm']+motion['retainer_to_carrier_pointwise_mm']+xy_allow
    for part in nominal_parts:
        xy=box(*part['envelope_xy_bounds_mm']);height=part['height_max_mm']+part['applied_z_allowance_mm']
        if part['side']=='top':
            low,high=top_min,top_max+height+z_allow
            frame_low,frame_high=-frame_gap_max,height+z_allow
        else:
            low=p['pcb']['bottom_z']-r['dimension_requirements']['axial_feature_tolerance_mm']-z_allow-height
            high=top_max-.71*thermal['states']['board_z'][0]['scale']
            frame_low,frame_high=-frame_gap_max-.91-height-z_allow,-.71*thermal['states']['board_z'][0]['scale']
        global_shape=xy.buffer(motion['pcb_to_body_xy_mm']+xy_allow,join_style='mitre')
        relative_shape=xy.buffer(motion['pcb_to_carrier_xy_mm']+xy_allow,join_style='mitre')
        to_frame=xy.buffer(frame_relative,join_style='mitre')
        def envelope(shape,z0,z1):
            a,b,c,d=shape.bounds
            return [part['ref'],[a,b,z0],[c-a,d-b,z1-z0]]
        body_boxes.append(envelope(global_shape,low,high));carrier_boxes.append(envelope(relative_shape,low,high))
        frame_boxes.append(envelope(to_frame,r['frame']['bottom_z_mm']+frame_low,r['frame']['bottom_z_mm']+frame_high))
        distances=[]
        for name,shape,z0,z1 in lower+rails:
            distances.append((solid_distance((relative_shape,low,high),(shape.buffer(.025,join_style='mitre'),z0-.025-z_allow,z1+.025+z_allow)),name))
        for name,shape,z0,z1 in ribs+posts:
            distances.append((solid_distance((global_shape,low,high),(shape.buffer(.025,join_style='mitre'),z0-.05-z_allow,z1+.05+z_allow)),name))
        # Frame capture couples its Z position to the PCB top. Never combine a
        # high PCB with a low frame that it would already have lifted. This is a
        # parallel-board static fit model; out-of-plane tilt/load remains open.
        for name,shape,z0,z1 in retainer:
            lo=0 if name=='retainer frame' else (z0-r['frame']['bottom_z_mm'])*thermal['states']['frame'][1]['scale']-.05
            hi=(z1-r['frame']['bottom_z_mm'])*thermal['states']['frame'][1]['scale']+.05
            distances.append((solid_distance((to_frame,frame_low,frame_high),(shape.buffer(.025,join_style='mitre'),lo,hi)),name))
        distance,name=min(distances);minimums[part['ref']]=dict(gap_mm=distance,obstacle=name)
        if distance<gap-1e-8:failures.append(dict(ref=part['ref'],gap_mm=distance,obstacle=name))
    checks.append(dict(name='Thermal/motion component envelopes versus retention',pass_=not failures,failures=failures))
    board_small=box(-19.95,-15.95,19.95,15.95)
    kernel=board_small.buffer(-frame_relative,join_style='mitre')
    outline=rounded_rect(*r['frame']['outer_mm'],r['frame']['outer_radius_mm'])
    contacts=[box(*b).intersection(outline).buffer(-.025,join_style='mitre').intersection(kernel).area for b in r['capture_tabs_xy_mm']+r['north_tabs_xy_mm']]
    checks.append(dict(name='Four tabs overlap the guaranteed board interior',pass_=len(contacts)==4 and min(contacts)>=.1,contact_areas_mm2=contacts,pointwise_relative_bound_mm=frame_relative))
    cavity=rounded_rect(*p['body']['cavity'],p['body']['cavity_radius'])
    checks.append(dict(name='Nominal frame outline inside cavity',pass_=cavity.covers(frame_shape(r))))
    for name,shape,lo,hi in posts:
        for ant in p['antenna_reservations']:
            x,y,z=ant['center'];w,h,t=ant['size'];distance=solid_distance((shape,lo,hi),(box(x-w/2,y-h/2,x+w/2,y+h/2),z-t/2,z+t/2))
            checks.append(dict(name=name+' to '+ant['label'],pass_=distance>=gap,gap_mm=distance))
    return dict(checks=checks,minimum_component_gaps=minimums,swept_boxes=body_boxes,frame_boxes=frame_boxes,carrier_boxes=carrier_boxes,
                guaranteed_tab_contacts=contacts,thermal=thermal,minimum_gap_mm=min(x['gap_mm'] for x in minimums.values()))


def cable_motion(p, r, controls, nominal_parts):
    motion = r['motion_screen']; nominal_top=p['pcb']['bottom_z']+p['pcb']['size'][2]
    nominal_rows=antenna.cable_rows(controls,p,p['pcb']['size'][2])
    nominal_clips=antenna.make_clips(nominal_rows,p)
    cases=[]
    # A sampled admissible shape is not proof that a real coax assumes it.
    # Plug azimuth and force/strain capability require physical approval.
    angles=[0,-15,15,-30,30,-45,45,-60,60,-75,75]
    for dx,dy,top in itertools.product([-motion['pcb_to_body_xy_mm'],0,motion['pcb_to_body_xy_mm']],
                                      [-motion['pcb_to_body_xy_mm'],0,motion['pcb_to_body_xy_mm']],
                                      [motion['pcb_top_z_mm'][0],nominal_top,motion['pcb_top_z_mm'][1]]):
        shift=np.array([dx,dy,top-nominal_top]); rows=[]; summaries=[]
        for name,source in controls.items():
            base=np.array(source);base[:2]+=shift;candidates=[]
            for angle in angles:
                control=base.copy();direction=control[1]-control[0];theta=np.deg2rad(angle)
                direction[:2]=np.array([[np.cos(theta),-np.sin(theta)],[np.sin(theta),np.cos(theta)]])@direction[:2]
                control[1]=control[0]+direction
                try:
                    tuned,handle=tune_handle(control)
                except AssertionError:
                    continue
                xyz,arc,radii,step=spline(tuned,4001)
                distances=[];connector='J1' if name=='LTE' else 'J2'
                for part in nominal_parts:
                    if part['ref']==connector:continue
                    a,b,c,d=part['envelope_xy_bounds_mm'];z0,z1=part['envelope_z_mm']
                    allowance=np.array([motion['thermal_xy_allowance_mm']]*2+[motion['thermal_z_allowance_mm']])
                    low=np.array([a,b,z0])+shift-allowance;high=np.array([c,d,z1])+shift+allowance
                    if part['side']=='bottom':low[2]-=.91-.84088
                    distance=float(point_box_distance(xyz,low,high).min())-.715-step/2
                    distances.append((distance,part['ref']))
                minimum,ref=min(distances)
                summary=dict(name=name,handle_mm=handle,plug_azimuth_change_degrees=angle,
                    control_points_mm=tuned.tolist(),length_mm=float(arc[-1]),minimum_radius_mm=float(radii.min()),
                    minimum_component_gap_mm=minimum,limiting_ref=ref,
                    pass_=minimum>=.2 and radii.min()>=3 and abs(arc[-1]-98.5)<.01 and step<=.08)
                score=min(minimum/.2,float(radii.min())/3)
                candidates.append((score,summary,dict(name=name,xyz=xyz,arc=arc,radii=radii,step=step)))
            assert candidates,'No fixed-length cable candidate: '+name
            _,summary,row=max(candidates,key=lambda v:v[0]);rows.append(row);summaries.append(summary)
        clips=antenna.make_clips(rows,p)
        displacement=max(float(np.linalg.norm(np.array(a['center'])-b['center'])) for a,b in zip(clips,nominal_clips))
        separation=curve_separation(rows[0]['xyz'],rows[1]['xyz'])-1.43-sum(x['step']/2 for x in rows)
        cases.append(dict(pcb_pose_mm=[dx,dy,top],cables=summaries,cable_gap_mm=separation,
                          guide_center_shift_mm=displacement,
                          pass_=all(s['pass_'] for s in summaries) and separation>=.2 and displacement<1e-8))
    return dict(cases=cases,all_sampled_cases_pass=all(c['pass_'] for c in cases),
                scope='27 sampled endpoint poses. Fixed-length shape search adjusts the first tangent length and in-plane azimuth; guide centers stay fixed. Plug orientation, reaction force, continuous deformation and physical flex life are unqualified.')


def write_retention_scad(p,r,screen):
    rows={
        'retainer_outer':r['frame']['outer_mm'],'retainer_inner':r['frame']['inner_mm'],
        'retainer_outer_r':r['frame']['outer_radius_mm'],'retainer_inner_r':r['frame']['inner_radius_mm'],
        'retainer_z':r['frame']['bottom_z_mm'],'retainer_h':r['frame']['height_mm'],
        'retainer_tabs':r['capture_tabs_xy_mm']+r['north_tabs_xy_mm'],
        'retainer_posts':r['lid_posts_xy_mm'],'retainer_post_z':r['lid_post_bottom_z_mm'],
        'locator_ribs':r['locator_ribs_xy_mm'],'guide_rails':r['guide_rails_xy_mm'],
        'guide_top_z':r['guide_top_z_mm'],'sim_bridge_cut':r['sim_bridge_relief_xy_mm'],
        'guide_reliefs':r['guide_reliefs_xy_mm'],
        'radial_keys':[key['xy_mm'] for key in r['radial_keys']],
        'radial_slots':[key['slot_xy_mm'] for key in r['radial_keys']],
        'key_z':r['key_bottom_z_mm'],'key_slot_z':r['key_slot_bottom_z_mm'],
        'motion_boxes':screen['swept_boxes'],'frame_motion_boxes':screen['frame_boxes'],
        'carrier_motion_boxes':screen['carrier_boxes']}
    text='// Generated r11 thermal-fit prototype; physical qualification remains open.\n'
    text+='\n'.join(k+' = '+json.dumps(v)+';' for k,v in rows.items())+'\n'
    text+='''
module xy_box(b,z,h){translate([b[0],b[1],z])cube([b[2]-b[0],b[3]-b[1],h]);}
module body_locators(){for(b=locator_ribs)xy_box(b,floor_t,pcb_z-floor_t);}
module retention_posts(){for(b=retainer_posts)xy_box(b,retainer_post_z,body_h-retainer_post_z+.1);}
module guide_rail_solids(offset_z=0){difference(){
    intersection(){
        translate([0,0,pcb_z-1.5+offset_z-.01])linear_extrude(guide_top_z-(pcb_z-1.5)+.02)rr(41.6,33.6,1.8);
        union()for(i=[0:3])let(b=guide_rails[i],q=[b[0]-(i==0?.01:0),b[1]-(i==2?.01:0),b[2]+(i==1?.01:0),b[3]+(i==3?.01:0)])
            xy_box(q,pcb_z-1.5+offset_z,guide_top_z-(pcb_z-1.5));
    }
    // Open SIM lane: a bridge would intersect D1 at the admitted board lift.
    xy_box(sim_bridge_cut,pcb_z-1.5+offset_z-.01,guide_top_z-(pcb_z-1.5)+.02);
    for(b=guide_reliefs)xy_box(b,pcb_z-1.5+offset_z-.01,guide_top_z-(pcb_z-1.5)+.02);
    for(b=radial_slots)xy_box(b,key_slot_z+offset_z,guide_top_z-key_slot_z+.01);
}}
module retainer_plan(){intersection(){
    rr(retainer_outer[0],retainer_outer[1],retainer_outer_r);
    union(){difference(){rr(retainer_outer[0],retainer_outer[1],retainer_outer_r);rr(retainer_inner[0],retainer_inner[1],retainer_inner_r);}
        for(b=retainer_tabs)translate([b[0],b[1]])square([b[2]-b[0],b[3]-b[1]]);}
}}
module retainer(){
    translate([0,0,retainer_z])linear_extrude(retainer_h)retainer_plan();
    intersection(){
        translate([0,0,key_z-.01])linear_extrude(retainer_z-key_z+.12)rr(retainer_outer[0],retainer_outer[1],retainer_outer_r);
        union()for(i=[0:3])let(b=radial_keys[i],q=[b[0]-(i==0?.01:0),b[1]-(i==2?.01:0),b[2]+(i==1?.01:0),b[3]+(i==3?.01:0)])
            xy_box(q,key_z,retainer_z-key_z+.1);
    }
}
module moving_components(rows,clearance=0){for(p=rows)
    translate(p[1]-[clearance,clearance,clearance])cube(p[2]+[2*clearance,2*clearance,2*clearance]);}
module retention_interference(){
    intersection(){moving_components(motion_boxes,.2);union(){body_locators();retention_posts();}}
    intersection(){moving_components(frame_motion_boxes,.2);retainer();}
}
'''
    (OUT/'retention.scad').write_text(text)


def build():
    r=json.loads((OUT/'retention.json').read_text())
    sources=[BASE/n for n in ['parameters.json','components.native.json','fit-profile.json','routing-controls.json','enclosure.scad','pack.scad']]
    base_hashes={str(path.relative_to(ROOT)):SHA(path) for path in sources}
    p,n,profile,controls=[json.loads(path.read_text()) for path in sources[:4]]
    p['revision']=OUT.name
    p['status']='Thermal dimensional prototype with radial retention keys; physical thermal, retention and ingress acceptance open'
    p['carrier_leg_centers_mm'][1][1]=9.4
    p['body']['cavity']=[42.4,34.7]
    p['contacts']['stem_length']=(p['body']['size'][0]-p['body']['cavity'][0])/2
    # New bounded motion needs clearance beyond the original seated-only model.
    for row in profile['carrier_reliefs']:
        if row['name'] in ('D1 tolerance clearance','U12 charge gate clearance'):
            a,b,c,d=row['bounds_mm'];row['bounds_mm']=[a-.60,b-.60,c+.60,d+.60]
    profile['carrier_reliefs'] += [
        dict(name='C10 bounded-motion clearance',bounds_mm=[16.64,12.23,20.16,15.07],depth_mm=1.5),
        dict(name='C33 bounded-motion clearance',bounds_mm=[-17.42,12.24,-14.58,15.76],depth_mm=1.5),
        dict(name='R29 bounded-motion clearance',bounds_mm=[-15.78,13.31,-12.22,16.19],depth_mm=1.5)]
    controls['GNSS'][6][2]+=1.5
    controls['LTE'][2][0]+=1.7
    controls['LTE'][8][2]+=.8
    for name,points in controls.items():
        controls[name]=tune_handle(points)[0].tolist()
    for name,value in [('parameters.json',p),('components.native.json',n),('fit-profile.json',profile),('routing-controls.json',controls)]:
        (OUT/name).write_text(json.dumps(value,indent=2)+'\n')
    (OUT/'pack.scad').write_bytes((BASE/'pack.scad').read_bytes())
    original=antenna.OUT
    try:
        antenna.OUT=OUT
        receipt=antenna.build()
    finally:
        antenna.OUT=original
    parts=receipt['scenarios'][2]['parts']
    screen=bounds_and_screens(p,profile,r,parts)
    motion=cable_motion(p,r,controls,parts)
    report=dict(result='CONDITIONAL_RETENTION_GEOMETRY_PASS' if all(c['pass_'] for c in screen['checks']) and motion['all_sampled_cases_pass'] else 'FAIL',
                pcb_sha256=n['source_sha256'],base_inputs=base_hashes,
                retention_input_sha256=SHA(OUT/'retention.json'),checker_sha256=SHA(Path(__file__)),
                checks=screen['checks'],minimum_component_gaps=screen['minimum_component_gaps'],
                guaranteed_tab_contacts=screen['guaranteed_tab_contacts'],thermal=screen['thermal'],
                thermal_input_sha256=SHA(OUT/'thermal.json'),thermal_checker_sha256=SHA(ROOT/'scripts/thermal_fit_bounds.py'),
                cable_evaluator_sha256=SHA(ROOT/'scripts/thermal_cable_geometry.py'),
                cable_motion=motion,physical_retention_qualified=False,physical_ingress_qualified=False,
                scope='Captivity and geometric clearances at assigned manufacturing limits. No supplier process, strength, shock, wear, anti-rattle or physical sealing acceptance.')
    (OUT/'retention-checks.json').write_text(json.dumps(report,indent=2)+'\n')
    write_retention_scad(p,r,screen)
    cad=(BASE/'enclosure.scad').read_text()
    cad=cad.replace('// Swim enclosure r09 pack request study.','// Swim enclosure r11 thermal-fit prototype.')
    cad=cad.replace('include <pack.scad>','include <pack.scad>\ninclude <retention.scad>')
    cad=cad.replace('module body() {','module body_shell() {',1)
    cad=cad.replace('module lid_shell() {','module body(){union(){body_shell();body_locators();}}\nmodule lid_shell() {',1)
    cad=cad.replace('union(){lid_shell();translate([0,0,-body_h])cable_guide_solids();}',
                    'union(){lid_shell();translate([0,0,-body_h]){cable_guide_solids();retention_posts();}}')
    old='for(s=[-1,1],y=[-12,12])translate([s*20.4-.3,y-1,0])cube([.6,2,2.7]);'
    assert old in cad
    cad=cad.replace(old,'guide_rail_solids(-(pcb_z-1.5));')
    cad=cad.replace('// Board edge clearance is 0.4 mm; no board drill holes are added.', '// The 0.4 mm lower support strip is separate from the guide aperture; no PCB holes are added.')
    # Give the leg/frame union an internal overlap; preserve the floor datum.
    cad=cad.replace('cube([1,2,pcb_z-1.5-floor_t]);','cube([1,2,pcb_z-1.5-floor_t+eps]);')
    cad=cad.replace('translate([0,0,explode/3])contents();','translate([0,0,explode/3])contents();\n    color([.65,.24,.65])translate([0,0,explode/2])retainer();')
    cad=cad.replace('else if(part=="lid")lid();','else if(part=="lid")lid();\nelse if(part=="retainer")translate([0,0,-key_z])retainer();')
    modes='''
else if(part=="retention_interference")retention_interference();
else if(part=="carrier_motion_interference")intersection(){moving_components(carrier_motion_boxes,.2);translate([0,0,pcb_z-1.5])carrier();}
else if(part=="key_interference")intersection(){retainer();translate([0,0,pcb_z-1.5])carrier();}
else if(part=="key_wrong_orientation")intersection(){rotate([0,0,180])retainer();translate([0,0,pcb_z-1.5])carrier();}
'''
    assert 'else assembly();' in cad
    cad=cad.replace('else assembly();',modes+'else assembly();')
    cad=cad.replace('hardware();rf_cables();rf_antennas();}',
                    'hardware();rf_cables();rf_antennas();color([.65,.24,.65,.8])retainer();}')
    (OUT/'enclosure.scad').write_text(cad)
    assert all(SHA(ROOT/name)==digest for name,digest in base_hashes.items())
    print(json.dumps(dict(result=report['result'],minimum_component_gap_mm=screen['minimum_gap_mm'],
                         failures=[x for x in report['checks'] if not x['pass_']],
                         failed_cable_cases=[x for x in motion['cases'] if not x['pass_']]),indent=2))
    return report


if __name__=='__main__':
    raise SystemExit(build()['result']=='FAIL')
