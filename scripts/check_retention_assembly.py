#!/usr/bin/env python3
"""Build a captive-PCB prototype and screen bounded component/cable movement.

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
from antenna_cable_geometry import curve_separation, point_box_distance, spline
from audit_populated_fit import carrier_solids, rounded_rect, solid_distance

ROOT = Path(__file__).resolve().parents[1]
BASE = ROOT/'mechanical/swim-r09-pack-request'
OUT = ROOT/'mechanical/swim-r10-retention'
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

    low, high = 1., 10.
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
    """Nominal conservative prisms; intentional bearing contacts are separate."""
    bottom = p['pcb']['bottom_z']-1.5
    rails = []
    for b in r['guide_rails_xy_mm']:
        shape = box(*b)
        cut = box(*r['sim_bridge_relief_xy_mm'])
        slot = box(*r['orientation_key']['slot_xy_mm'])
        levels = sorted({bottom, r['sim_bridge_bottom_z_mm'],
                         r['orientation_key']['slot_bottom_z_mm'], r['guide_top_z_mm']})
        for low, high in zip(levels, levels[1:]):
            section = shape
            if low < r['sim_bridge_bottom_z_mm']:
                section = section.difference(cut)
            if low >= r['orientation_key']['slot_bottom_z_mm']:
                section = section.difference(slot)
            if not section.is_empty:
                rails.append(('carrier guide rail', section, low, high))
    ribs = [('body locator', box(*b), p['body']['floor'], p['pcb']['bottom_z'])
            for b in r['locator_ribs_xy_mm']]
    posts = [('lid hold-down', box(*b), r['lid_post_bottom_z_mm'], p['body']['size'][2])
             for b in r['lid_posts_xy_mm']]
    f, key = r['frame'], r['orientation_key']
    retainer = [('retainer frame', frame_shape(r), f['bottom_z_mm'], f['bottom_z_mm']+f['height_mm']),
                ('orientation key', box(*key['xy_mm']), key['bottom_z_mm'], f['bottom_z_mm']+.1)]
    return rails, ribs, posts, retainer


def bounds_and_screens(p, profile, r, nominal_parts):
    motion = r['motion_screen']
    gap = motion['minimum_component_gap_mm']
    rails, ribs, posts, retainer = retention_solids(p, r)
    lower = [x for x in carrier_solids(p, profile['carrier_reliefs'])
             if x[0] not in ('carrier guide', 'carrier leg')]
    lower += [('carrier leg', box(x-.5,y-1,x+.5,y+1), p['body']['floor'], p['pcb']['bottom_z']-1.5)
              for x,y in p['carrier_leg_centers_mm']]
    # The retainer may translate to the cavity walls and lift to the lid stops.
    frame_delta = r['frame']['bottom_z_mm']-motion['retainer_bottom_z_mm'][0]
    frame_lift = motion['retainer_bottom_z_mm'][1]-r['frame']['bottom_z_mm']
    frame_allow = motion['retainer_to_body_xy_mm']+.025
    retainer_sweep = [(name, shape.buffer(frame_allow, join_style='mitre'),
                       low-frame_delta, high+frame_lift+.05) for name,shape,low,high in retainer]
    checks, failures, boxes = [], [], []
    minimums = {}
    top_min, top_max = motion['pcb_top_z_mm']
    for part in nominal_parts:
        xy = box(*part['envelope_xy_bounds_mm'])
        height = part['height_max_mm']+part['applied_z_allowance_mm']
        if part['side']=='top':
            low, high = top_min, top_max+height
        else:
            # Minimum top height belongs to the thin board. Do not combine it
            # with maximum thickness to invent a board below its support datum.
            low = p['pcb']['bottom_z']-r['dimension_requirements']['axial_feature_tolerance_mm']-height
            high = top_max-.71
        global_shape = xy.buffer(motion['pcb_to_body_xy_mm'], join_style='mitre')
        relative_shape = xy.buffer(motion['pcb_to_carrier_xy_mm'], join_style='mitre')
        boxes.append([part['ref'], [*global_shape.bounds[:2],low],
                      [global_shape.bounds[2]-global_shape.bounds[0],global_shape.bounds[3]-global_shape.bounds[1],high-low]])
        distances = []
        for name,shape,z0,z1 in lower+rails:
            # Carrier/board seating datum is common; use the board-to-carrier
            # displacement, rather than adding independent shell movement twice.
            distance = solid_distance((relative_shape,low,high),
                                      (shape.buffer(.025,join_style='mitre'),z0-.025,z1+.025))
            distances.append((distance,name))
        for name,shape,z0,z1 in ribs+posts+retainer_sweep:
            distance = solid_distance((global_shape,low,high),(shape,z0,z1))
            distances.append((distance,name))
        distance, name = min(distances)
        minimums[part['ref']] = dict(gap_mm=distance,obstacle=name)
        if distance < gap-1e-8:
            failures.append(dict(ref=part['ref'],gap_mm=distance,obstacle=name))
    checks.append(dict(name='Swept component envelopes versus retention',pass_=not failures,failures=failures))
    # Explicit manufacturing stack: no rigid hold-down may prevent lid seating.
    d = r['dimension_requirements']
    axial = d['axial_feature_tolerance_mm']
    guide_max = r['guide_top_z_mm']+axial
    frame_max = r['frame']['height_mm']+axial
    stop_min = r['lid_post_bottom_z_mm']-axial
    closure_gap = stop_min-guide_max-frame_max
    top_limit = r['lid_post_bottom_z_mm']+axial-(r['frame']['height_mm']-axial)
    checks.append(dict(name='Lid closes at assigned stack limits',pass_=closure_gap>=-1e-8,minimum_gap_mm=closure_gap))
    checks.append(dict(name='Upper PCB capture plane matches motion screen',pass_=abs(top_limit-top_max)<1e-8,maximum_top_z_mm=top_limit))
    card_gap=r['sim_bridge_bottom_z_mm']-axial-(p['pcb']['bottom_z']+axial)
    checks.append(dict(name='SIM insertion clears bridge with PCB seated',
                       pass_=card_gap>=gap-1e-8,minimum_gap_mm=card_gap,
                       condition='Power off; board seated in lifted carrier; remove retainer before service.'))
    # The four inward tabs must overlap even the smallest allowed board while
    # the board and retainer move in opposite directions. A yaw screen also
    # exercises contact loss near the rectangular board's sharp corners.
    relative_xy = motion['pcb_to_body_xy_mm']+motion['retainer_to_body_xy_mm']
    board_small = box(-19.95,-15.95,19.95,15.95)
    outline = rounded_rect(*r['frame']['outer_mm'],r['frame']['outer_radius_mm'])
    tabs = [box(*b).intersection(outline).buffer(-.025,join_style='mitre')
            for b in r['capture_tabs_xy_mm']+r['north_tabs_xy_mm']]
    overlap_cases=[]
    for x,y,yaw in itertools.product([-relative_xy,0,relative_xy],
                                     [-relative_xy,0,relative_xy],[-.6,0,.6]):
        board=translate(rotate(board_small,yaw,origin=(0,0)),xoff=x,yoff=y)
        areas=[tab.intersection(board).area for tab in tabs]
        overlap_cases.append(dict(offset_mm=[x,y],yaw_deg=yaw,overlap_area_mm2=areas,
                                  pass_=len(areas)==4 and min(areas)>=.1))
    checks.append(dict(name='Four tabs retain the smallest board',
                       pass_=all(c['pass_'] for c in overlap_cases),
                       minimum_contact_area_mm2=min(min(c['overlap_area_mm2']) for c in overlap_cases)))
    dims=r['dimension_requirements']
    carrier_shift=(41.7+dims['body_locator_aperture_overall_tolerance_mm']
                   -(41.6-dims['frame_and_carrier_overall_tolerance_mm']))/2
    relative_shift=(40.2+dims['frame_and_carrier_overall_tolerance_mm']
                    -(40-dims['pcb_outline_overall_tolerance_mm']))/2
    checks.append(dict(name='Lateral envelopes cover assigned size limits',
                       pass_=relative_shift+.025<=motion['pcb_to_carrier_xy_mm']+1e-8
                       and carrier_shift+motion['pcb_to_carrier_xy_mm']<=motion['pcb_to_body_xy_mm']+1e-8,
                       carrier_center_shift_mm=carrier_shift,pcb_center_shift_mm=relative_shift,
                       corner_rotation_allowance_mm=.025))
    cavity = rounded_rect(*p['body']['cavity'],p['body']['cavity_radius'])
    checks.append(dict(name='Retainer outline inside cavity',pass_=cavity.covers(frame_shape(r))))
    for name,shape,lo,hi in posts:
        for ant in p['antenna_reservations']:
            x,y,z=ant['center'];w,h,t=ant['size']
            distance=solid_distance((shape,lo,hi),(box(x-w/2,y-h/2,x+w/2,y+h/2),z-t/2,z+t/2))
            checks.append(dict(name=name+' to '+ant['label'],pass_=distance>=gap,gap_mm=distance))
    return dict(checks=checks,minimum_component_gaps=minimums,swept_boxes=boxes,tab_overlap_cases=overlap_cases,
                minimum_gap_mm=min(v['gap_mm'] for v in minimums.values()))


def cable_motion(p, r, controls, nominal_parts):
    motion = r['motion_screen']; nominal_top=p['pcb']['bottom_z']+p['pcb']['size'][2]
    nominal_rows=antenna.cable_rows(controls,p,p['pcb']['size'][2])
    nominal_clips=antenna.make_clips(nominal_rows,p)
    cases=[]
    for dx,dy,top in itertools.product([-.3,0,.3],[-.3,0,.3],
                                      [motion['pcb_top_z_mm'][0],nominal_top,motion['pcb_top_z_mm'][1]]):
        shift=np.array([dx,dy,top-nominal_top]); rows=[]; summaries=[]
        for name,source in controls.items():
            c=np.array(source);c[:2]+=shift
            tuned,handle=tune_handle(c)
            xyz,arc,radii,step=spline(tuned,4001)
            distances=[]
            connector='J1' if name=='LTE' else 'J2'
            for part in nominal_parts:
                if part['ref']==connector:
                    continue
                a,b,c,d=part['envelope_xy_bounds_mm'];z0,z1=part['envelope_z_mm']
                low=np.array([a,b,z0])+shift;high=np.array([c,d,z1])+shift
                if part['side']=='bottom':
                    low[2]-=.91-.84088
                distance=float(point_box_distance(xyz,low,high).min())-.715-step/2
                distances.append((distance,part['ref']))
            minimum,ref=min(distances)
            rows.append(dict(name=name,xyz=xyz,arc=arc,radii=radii,step=step))
            summaries.append(dict(name=name,handle_mm=handle,length_mm=float(arc[-1]),
                minimum_radius_mm=float(radii.min()),minimum_component_gap_mm=minimum,limiting_ref=ref,
                pass_=minimum>=.2 and radii.min()>=3 and abs(arc[-1]-98.5)<.01 and step<=.08))
        clips=antenna.make_clips(rows,p)
        displacement=max(float(np.linalg.norm(np.array(a['center'])-b['center']))
                         for a,b in zip(clips,nominal_clips))
        separation=curve_separation(rows[0]['xyz'],rows[1]['xyz'])-1.43-sum(x['step']/2 for x in rows)
        cases.append(dict(pcb_pose_mm=[dx,dy,top],cables=summaries,
                          cable_gap_mm=separation,guide_center_shift_mm=displacement,
                          pass_=all(s['pass_'] for s in summaries) and separation>=.2 and displacement<1e-8))
    return dict(cases=cases,all_sampled_cases_pass=all(c['pass_'] for c in cases),
                scope='27 sampled endpoint poses with a fixed-length initial-handle adjustment. Component swept volumes are conservative; this cable pose sampling is not proof of every continuous deformation or physical flex life.')


def write_retention_scad(p, r, screen):
    rows={
        'retainer_outer':r['frame']['outer_mm'],'retainer_inner':r['frame']['inner_mm'],
        'retainer_outer_r':r['frame']['outer_radius_mm'],'retainer_inner_r':r['frame']['inner_radius_mm'],
        'retainer_z':r['frame']['bottom_z_mm'],'retainer_h':r['frame']['height_mm'],
        'retainer_tabs':r['capture_tabs_xy_mm']+r['north_tabs_xy_mm'],
        'retainer_posts':r['lid_posts_xy_mm'],'retainer_post_z':r['lid_post_bottom_z_mm'],
        'locator_ribs':r['locator_ribs_xy_mm'],'guide_rails':r['guide_rails_xy_mm'],
        'guide_top_z':r['guide_top_z_mm'],'sim_bridge_bottom_z':r['sim_bridge_bottom_z_mm'],
        'sim_bridge_cut':r['sim_bridge_relief_xy_mm'],'key_bounds':r['orientation_key']['xy_mm'],
        'key_z':r['orientation_key']['bottom_z_mm'],'key_slot':r['orientation_key']['slot_xy_mm'],
        'key_slot_z':r['orientation_key']['slot_bottom_z_mm'],'motion_boxes':screen['swept_boxes']}
    text='// Generated captive-PCB prototype; physical retention remains unqualified.\n'
    text+='\n'.join(k+' = '+json.dumps(v)+';' for k,v in rows.items())+'\n'
    text+='''
module xy_box(b,z,h){translate([b[0],b[1],z])cube([b[2]-b[0],b[3]-b[1],h]);}
module body_locators(){for(b=locator_ribs)xy_box(b,floor_t,pcb_z-floor_t);}
module retention_posts(){for(b=retainer_posts)xy_box(b,retainer_post_z,body_h-retainer_post_z+.1);}
module guide_rail_solids(offset_z=0){
    difference(){
        // Clip every rail to the SAME outer contour as the carrier. Extending
        // only its outboard edge before clipping avoids CGAL submicron slivers
        // between a rectangle and offset()'s tessellated straight edge.
        intersection(){
            translate([0,0,pcb_z-1.5+offset_z-.01])
                linear_extrude(guide_top_z-(pcb_z-1.5)+.02)rr(41.6,33.6,1.8);
            union()for(i=[0:3])let(b=guide_rails[i],
                q=[b[0]-(i==0?.01:0),b[1]-(i==2?.01:0),b[2]+(i==1?.01:0),b[3]+(i==3?.01:0)])
                xy_box(q,pcb_z-1.5+offset_z,guide_top_z-(pcb_z-1.5));
        }
        xy_box(sim_bridge_cut,pcb_z-1.5+offset_z-.01,sim_bridge_bottom_z-(pcb_z-1.5)+.01);
        xy_box(key_slot,key_slot_z+offset_z,guide_top_z-key_slot_z+.01);
    }
}
module retainer_plan(){intersection(){
    rr(retainer_outer[0],retainer_outer[1],retainer_outer_r);
    union(){difference(){rr(retainer_outer[0],retainer_outer[1],retainer_outer_r);rr(retainer_inner[0],retainer_inner[1],retainer_inner_r);}
        for(b=retainer_tabs)translate([b[0],b[1]])square([b[2]-b[0],b[3]-b[1]]);}
}}
module retainer(){
    translate([0,0,retainer_z])linear_extrude(retainer_h)retainer_plan();
    xy_box(key_bounds,key_z,retainer_z-key_z+.1);
}
module swept_components(clearance=0){for(p=motion_boxes)
    translate(p[1]-[clearance,clearance,clearance])cube(p[2]+[2*clearance,2*clearance,2*clearance]);}
'''
    (OUT/'retention.scad').write_text(text)


def build():
    r=json.loads((OUT/'retention.json').read_text())
    sources=[BASE/n for n in ['parameters.json','components.native.json','fit-profile.json','routing-controls.json','enclosure.scad','pack.scad']]
    base_hashes={str(path.relative_to(ROOT)):SHA(path) for path in sources}
    p,n,profile,controls=[json.loads(path.read_text()) for path in sources[:4]]
    p['revision']=OUT.name
    p['status']='Captive-PCB geometry prototype; supplier pack, physical retention and ingress unqualified'
    p['carrier_leg_centers_mm'][1][1]=9.7
    # New bounded motion needs clearance beyond the original seated-only model.
    for row in profile['carrier_reliefs']:
        if row['name'] in ('D1 tolerance clearance','U12 charge gate clearance'):
            a,b,c,d=row['bounds_mm'];row['bounds_mm']=[a-.25,b-.25,c+.25,d+.25]
    profile['carrier_reliefs'] += [
        dict(name='C10 bounded-motion clearance',bounds_mm=[16.99,12.58,19.81,14.72],depth_mm=1.5),
        dict(name='R29 bounded-motion clearance',bounds_mm=[-15.43,13.66,-12.57,15.84],depth_mm=1.5)]
    controls['GNSS'][6][2]+=1.0
    controls['LTE'][2][0]+=.2
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
                tab_overlap_cases=screen['tab_overlap_cases'],
                cable_motion=motion,physical_retention_qualified=False,physical_ingress_qualified=False,
                scope='Captivity and geometric clearances at assigned manufacturing limits. No supplier process, strength, shock, wear, anti-rattle or physical sealing acceptance.')
    (OUT/'retention-checks.json').write_text(json.dumps(report,indent=2)+'\n')
    write_retention_scad(p,r,screen)
    cad=(BASE/'enclosure.scad').read_text()
    cad=cad.replace('// Swim enclosure r09 pack request study.','// Swim enclosure r10 captive-PCB prototype.')
    cad=cad.replace('include <pack.scad>','include <pack.scad>\ninclude <retention.scad>')
    cad=cad.replace('module body() {','module body_shell() {',1)
    cad=cad.replace('module lid_shell() {','module body(){union(){body_shell();body_locators();}}\nmodule lid_shell() {',1)
    cad=cad.replace('union(){lid_shell();translate([0,0,-body_h])cable_guide_solids();}',
                    'union(){lid_shell();translate([0,0,-body_h]){cable_guide_solids();retention_posts();}}')
    old='for(s=[-1,1],y=[-12,12])translate([s*20.4-.3,y-1,0])cube([.6,2,2.7]);'
    assert old in cad
    cad=cad.replace(old,'guide_rail_solids(-(pcb_z-1.5));')
    # Give the leg/frame union an internal overlap; preserve the floor datum.
    cad=cad.replace('cube([1,2,pcb_z-1.5-floor_t]);','cube([1,2,pcb_z-1.5-floor_t+eps]);')
    cad=cad.replace('translate([0,0,explode/3])contents();','translate([0,0,explode/3])contents();\n    color([.65,.24,.65])translate([0,0,explode/2])retainer();')
    cad=cad.replace('else if(part=="lid")lid();','else if(part=="lid")lid();\nelse if(part=="retainer")translate([0,0,-key_z])retainer();')
    modes='''
else if(part=="retention_interference")intersection(){swept_components(.2);union(){body_locators();retention_posts();retainer();}}
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
