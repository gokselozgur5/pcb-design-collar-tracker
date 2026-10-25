#!/usr/bin/env python3
"""Conditional pack/cradle fit bounds. Supplier contact/load approval stays open."""
import hashlib
import itertools
import json
from pathlib import Path

from shapely.geometry import box
from shapely.ops import unary_union

from audit_populated_fit import rounded_rect, solid_distance

ROOT = Path(__file__).resolve().parents[1]
BASE = ROOT / 'mechanical/swim-r11-thermal-fit'
OUT = ROOT / 'mechanical/swim-r12-pack-retention'
sha = lambda p: hashlib.sha256(p.read_bytes()).hexdigest()


def centered(size, radius=0):
    return rounded_rect(*size, radius) if radius else box(-size[0]/2, -size[1]/2, size[0]/2, size[1]/2)


def cap_shape(spec):
    c = spec['cap']
    return centered(c['outer_mm'], c['corner_radius_mm']).difference(
        centered(c['inner_mm']).union(centered(c['ntc_opening_mm'])))


def solids(spec, parameters):
    c, f = spec['cradle'], spec['cap']
    outer = centered(c['outer_mm'], c['corner_radius_mm'])
    walls = outer.difference(centered(c['inner_mm'], c['corner_radius_mm']))
    cradle = [('cradle platform', outer, parameters['body']['floor'], c['platform_top_z_mm']),
              ('cradle wall', walls, c['platform_top_z_mm'], c['wall_top_z_mm'])]
    cap = [('pack cap', cap_shape(spec), f['bottom_z_mm'], f['top_z_mm'])]
    cap += [('cap bridge '+str(i+1), box(*bounds), f['bottom_z_mm'], f['bridge_top_z_mm'])
            for i, bounds in enumerate(f['bridges_xy_mm'])]
    return cradle, cap


def evaluate(spec, parameters, retention, parts, thermal):
    motion, c, f = spec['motion'], spec['cradle'], spec['cap']
    tol = motion['feature_tolerance_mm']
    xy, za = motion['thermal_xy_allowance_mm'], motion['thermal_z_allowance_mm']
    gap = motion['minimum_component_gap_mm']
    carrier_motion = motion['carrier_to_body_xy_mm']
    checks = []
    def check(name, value, minimum=gap):
        checks.append(dict(name=name, value=value, minimum=minimum, pass_=value >= minimum-1e-8))
    # A service maximum must already include pack expansion/swelling. No lithium
    # pouch CTE or compressed-pouch assumption is invented here.
    minimum, maximum = spec['pack_body_minimum_for_capture_mm'], spec['pack_body_maximum_mm']
    check('positive complete-pack dimensions', min(minimum), 0.01)
    check('minimum pack does not exceed maximum', min(b-a for a,b in zip(minimum,maximum)), 0)
    check('pack bottom agrees with platform', -abs(spec['pack_body_bottom_z_mm']-c['platform_top_z_mm']), 0)
    check('nonzero cap thickness', f['top_z_mm']-f['bottom_z_mm'], .5)
    check('bridge overlaps original carrier ledge', f['bridge_top_z_mm']-(parameters['pcb']['bottom_z']-1.5), .05)
    for axis in range(2):
        check('cradle wall thickness '+str(axis), (c['outer_mm'][axis]-c['inner_mm'][axis])/2-2*tol, .5)
        check('maximum pack to cradle '+str(axis), (c['inner_mm'][axis]-maximum[axis])/2-tol-xy)
    # Independent body/carrier tolerances and thermal Z bounds; this is an
    # assigned assembled-chain allocation, not a separate allowance per feature.
    check('maximum pack to cap underside', f['bottom_z_mm']-(c['platform_top_z_mm']+maximum[2])-2*tol-2*za)
    check('cradle wall to cap underside', f['bottom_z_mm']-c['wall_top_z_mm']-2*tol-2*za)
    # The rectangular pack must remain vertically engaged with the wall when it
    # lifts into the cap. Board/carrier tilt and force are explicitly not modeled.
    check('minimum pack remains below wall at full lift',
          c['wall_top_z_mm']-tol-za-(f['bottom_z_mm']+tol+za-minimum[2]), 1)
    play = [(c['inner_mm'][i]+2*tol+2*xy-minimum[i])/2 for i in range(2)]
    relative = [v+carrier_motion+xy+tol for v in play]
    kernel = box(-minimum[0]/2+relative[0], -minimum[1]/2+relative[1],
                 minimum[0]/2-relative[0], minimum[1]/2-relative[1])
    capture = cap_shape(spec).buffer(-tol, join_style='mitre').intersection(kernel)
    quadrants = [box(x0,y0,x1,y1) for x0,x1 in [(-50,0),(0,50)] for y0,y1 in [(-50,0),(0,50)]]
    contact = [capture.intersection(q).area for q in quadrants]
    for i, area in enumerate(contact):
        check('guaranteed pack overlap quadrant '+str(i+1), area, 1)
    # Cover28x6.1 includes NTC26x4.1; use full minimum-pack travel, cap float,
    # placement/thermal allocations. NTC must never become a cap bearing.
    sensor_shape = box(-14-relative[0], -3.05-relative[1], 14+relative[0], 3.05+relative[1])
    sensor_gap = sensor_shape.distance(cap_shape(spec).buffer(tol, join_style='mitre'))
    check('NTC cover lateral clearance at all bounded translations', sensor_gap)
    cradle, cap = solids(spec, parameters)
    # Added solids only. Original shell/ledge/key/guide/cables retain their r11
    # evidence. Cap bridges may contact the existing body locators as carrier
    # bearing surfaces, so they must not exceed the original outer carrier rim.
    carrier_outline = rounded_rect(41.6,33.6,1.8)
    for name, shape, low, high in cap[1:]:
        check(name+' stays inside original carrier outline', -shape.difference(carrier_outline).area, 0)
    part_results = {}
    top_min, top_max = retention['motion_screen']['pcb_top_z_mm']
    for part in parts:
        height = part['height_max_mm']+part['applied_z_allowance_mm']
        if part['side']=='top':
            low, high = top_min, top_max+height+za
        else:
            low = parameters['pcb']['bottom_z']-retention['dimension_requirements']['axial_feature_tolerance_mm']-za-height
            high = top_max-.71*thermal['states']['board_z'][0]['scale']
        distances=[]
        for obstacles, travel in [(cradle,retention['motion_screen']['pcb_to_body_xy_mm']),
                                 (cap,retention['motion_screen']['pcb_to_carrier_xy_mm'])]:
            envelope = box(*part['envelope_xy_bounds_mm']).buffer(travel+xy,join_style='mitre')
            for name,shape,z0,z1 in obstacles:
                distance = solid_distance((envelope,low,high),
                    (shape.buffer(tol,join_style='mitre'),z0-tol-za,z1+tol+za))
                distances.append((distance,name))
        distance,name=min(distances)
        part_results[part['ref']]=dict(gap_mm=distance,obstacle=name)
    check('all 85 populated envelopes clear new solids',min(v['gap_mm'] for v in part_results.values()))
    # Metal contact thread and full-rotation nut/washer/lug reservation. Keep
    # their unresolved termination construction distinct from bounding boxes.
    ct = parameters['contacts']; inner_x = ct['side_x']-ct['stem_length']
    hardware=[]
    for y in ct['centers_y']:
        hardware += [('M3 thread',box(inner_x-ct['thread_length'],y-1.5,inner_x,y+1.5),ct['center_z']-1.5,ct['center_z']+1.5),
                     ('contact backing',box(inner_x-2.8,y-3.2,inner_x,y+3.2),ct['center_z']-3.2,ct['center_z']+3.2)]
    for obstacles, travel in [(cradle,0),(cap,carrier_motion)]:
        for name,shape,z0,z1 in obstacles:
            for hn, hs, hl, hh in hardware:
                distance=solid_distance((shape.buffer(tol+travel+xy,join_style='mitre'),z0-tol-za,z1+tol+za),
                                        (hs.buffer(tol,join_style='mitre'),hl-tol,hh+tol))
                check(name+' to '+hn+' '+str(round(hs.centroid.y)),distance)
    cavity = centered(parameters['body']['cavity'],parameters['body']['cavity_radius']).buffer(-tol)
    for name,shape,z0,z1 in cradle+cap[:1]:
        outer = shape.buffer(tol+xy+(carrier_motion if name=='pack cap' else 0),join_style='mitre')
        distance = outer.distance(cavity.boundary) if cavity.covers(outer) else -outer.difference(cavity).area
        check(name+' to cavity wall',distance)
    return dict(result='CONDITIONAL_PACK_RETENTION_GEOMETRY_PASS' if all(c['pass_'] for c in checks) else 'PACK_RETENTION_GEOMETRY_HOLD',
                checks=checks,component_clearances=part_results,minimum_component_gap_mm=min(v['gap_mm'] for v in part_results.values()),
                guaranteed_capture_areas_mm2=contact,pack_xy_play_mm=play,pack_to_cap_relative_xy_mm=relative,
                physical_pack_retention_qualified=False,physical_ingress_qualified=False,
                scope='Conditional static, parallel pack/PCB translation and assigned dimensional/thermal bounds. Minimum pack size, contact regions, lead exit, tilt/impact/abrasion, strength and physical ingress remain unapproved.')


def scad(spec):
    c,f=spec['cradle'],spec['cap']
    rows={'pack_cradle_inner':c['inner_mm'],'pack_cradle_outer':c['outer_mm'],
          'pack_cradle_r':c['corner_radius_mm'],'pack_platform_z':c['platform_top_z_mm'],
          'pack_wall_z':c['wall_top_z_mm'],'pack_cap_outer':f['outer_mm'],
          'pack_cap_inner':f['inner_mm'],'pack_cap_ntc':f['ntc_opening_mm'],
          'pack_cap_r':f['corner_radius_mm'],'pack_cap_z':f['bottom_z_mm'],
          'pack_cap_top':f['top_z_mm'],'pack_bridges':f['bridges_xy_mm'],
          'pack_bridge_top':f['bridge_top_z_mm']}
    return '// Generated from pack-retention.json; conditional dimensional requirements.\n'+'\n'.join(k+' = '+json.dumps(v)+';' for k,v in rows.items())+'\n'


def main():
    spec=json.loads((OUT/'pack-retention.json').read_text())
    p,r,fit,report=[json.loads((BASE/name).read_text()) for name in ['parameters.json','retention.json','antenna-fit.json','retention-checks.json']]
    result=evaluate(spec,p,r,fit['scenarios'][2]['parts'],report['thermal'])
    files=[OUT/'pack-retention.json',ROOT/'scripts/check_pack_retention.py',ROOT/'scripts/audit_populated_fit.py',
           ROOT/'assembly/pack-r03/request.json']+[BASE/n for n in ['parameters.json','retention.json','antenna-fit.json','retention-checks.json','checkpoint.json']]
    result['inputs']={str(f.relative_to(ROOT)):sha(f) for f in files}
    result['pcb_sha256']=fit['pcb_sha256']
    (OUT/'pack-retention-checks.json').write_text(json.dumps(result,indent=2)+'\n')
    (OUT/'pack-retention-parameters.scad').write_text(scad(spec))
    print(result['result'], 'minimum component gap',result['minimum_component_gap_mm'])
    print(json.dumps([c for c in result['checks'] if not c['pass_']],indent=2))
    return 0 if all(c['pass_'] for c in result['checks']) else 2


if __name__=='__main__':
    raise SystemExit(main())
