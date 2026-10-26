#!/usr/bin/env python3
"""r16 dry-side terminal and rear-bearing geometry; no force or IP acceptance."""
import hashlib
import json
import math
from pathlib import Path
import re

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / 'mechanical/swim-r16-contact-retention'
BASE = ROOT / 'mechanical/swim-r11-thermal-fit'
sha = lambda p: hashlib.sha256(p.read_bytes()).hexdigest()


def dimensions(s):
    """Standard-library interface checks, also used by read-only verification."""
    c, p, t, w, n = (s[k] for k in ['contact', 'pocket', 'terminal', 'washer', 'nut'])
    checks = []
    def check(name, value, minimum):
        checks.append(dict(name=name, value=round(value, 9), minimum=minimum, pass_=value >= minimum-1e-8))
    ft = p['feature_tolerance_mm']
    ct = c['axial_dimension_tolerance_mm']
    tt = t['dimension_tolerance_mm']
    shoulder = c['side_x_mm']-c['stem_length_mm']
    tip = shoulder-c['thread_length_mm']
    nut_inner = p['bearing_x_mm']-ft-t['base_thickness_mm']-tt-w['thickness_mm'][1]-n['thickness_mm'][1]
    check('shoulder cannot bottom before the terminal bears on the body', shoulder-ct-p['bearing_x_mm']-ft, .08)
    check('thread projects beyond complete maximum nut stack', nut_inner-(tip+2*ct), .5)
    check('radial seal retains a full dry-side shaft land', c['stem_length_mm']-ct-(3.85+2.8/2+.05), .5)
    check('dry pocket remains behind the radial sealing groove', 28.7-(3.85+2.8/2+.05)-p['bearing_x_mm']-ft, .5)
    check('pocket to inner lid-gland wall', 49/2-(2.5+.05)/2-.05-p['bearing_x_mm']-ft, .5)
    check('pocket roof below lid-gland floor', 18.5-1.34-.03-p['tail_top_z_mm']-ft, 1)
    check('pocket preserves the existing floor', p['base_z_mm'][0], 1.8)
    check('terminal hole clears maximum M3 thread', t['thread_hole_diameter_mm']-tt-3.05, .08)
    check('washer hole clears maximum M3 thread', w['inner_diameter_mm'][0]-3.05, .1)
    check('minimum terminal main thickness', t['base_thickness_mm']-tt, .9)
    check('minimum terminal tail thickness', t['tail_thickness_mm']-tt, .4)
    check('nut retains at least three pitches of nominal axial length', n['thickness_mm'][0], 1.5)
    pos=t['assembly_position_tolerance_mm']+t['thermal_position_allowance_mm']+tt
    check('terminal base clears pocket floor',t['base_z_mm'][0]-pos-p['base_z_mm'][0]-ft,.2)
    check('terminal base clears pocket side wall',(p['base_width_mm']-t['base_width_mm'])/2-pos-ft,.15)
    check('terminal tail clears pocket',p['tail_radius_mm']-t['tail_radius_mm']-pos-ft,.2)
    check('terminal tail clears maximum existing frame X envelope',p['bearing_x_mm']-ft-t['tail_thickness_mm']-tt-(20.9+.61+.15),.2)
    check('old circular backing reservation has no rear bearing',7.34-6.4,.9)
    expected=[(-6,'red','J3.1','/VIN_5V'),(6,'black','J3.2','/GND')]
    checks.append(dict(name='polarity follows r13 and native J3 pinout',pass_=[(x['contact_y_mm'],x['wire'],x['pad'],x['net']) for x in s['polarity']]==expected))
    return dict(checks=checks, shoulder_x_mm=shoulder, thread_tip_x_mm=tip,
                maximum_stack_inner_x_mm=nut_inner, physical_retention_qualified=False,
                physical_ingress_qualified=False, production_release=False)


def terminal_shapes(s, i):
    from shapely.geometry import Point, box
    from shapely.ops import unary_union
    p,t=s['pocket'],s['terminal'];y=s['contact']['centers_y_mm'][i]
    r=t['corner_radius_mm'];z0,z1=t['base_z_mm'];w=t['base_width_mm']
    base=box(y-w/2+r,z0+r,y+w/2-r,z1-r).buffer(r,quad_segs=32)
    tail=unary_union([Point(y,t['tail_root_z_mm']).buffer(t['tail_radius_mm'],quad_segs=32),
                      Point(*t['tail_centers_yz_mm'][i]).buffer(t['tail_radius_mm'],quad_segs=32)]).convex_hull
    shape=base.union(tail)
    holes=Point(y,s['contact']['center_z_mm']).buffer(t['thread_hole_diameter_mm']/2,quad_segs=48).union(
        Point(*t['tail_centers_yz_mm'][i]).buffer(t['wire_hole_diameter_mm']/2,quad_segs=32))
    return [(shape.intersection(box(-30,0,30,t['thickness_transition_z_mm'])).difference(holes),p['bearing_x_mm']-t['base_thickness_mm'],p['bearing_x_mm']),
            (shape.intersection(box(-30,t['thickness_transition_z_mm'],30,25)).difference(holes),p['bearing_x_mm']-t['tail_thickness_mm'],p['bearing_x_mm'])]


def evaluate(s):
    from shapely.geometry import Point, box
    from audit_populated_fit import solid_distance
    result=dimensions(s);checks=result['checks'];t=s['terminal'];p=s['pocket'];c=s['contact']
    def check(name,value,minimum=.2):
        checks.append(dict(name=name,value=round(value,9),minimum=minimum,pass_=value>=minimum-1e-8))
    # Subtract an oversized, circumscribed bore plus the assigned placement
    # range from an undersized terminal. Bearing is on both lateral ears.
    allowance=t['assembly_position_tolerance_mm']+t['thermal_position_allowance_mm']+t['dimension_tolerance_mm']
    bearings=[]
    for i,y in enumerate(c['centers_y_mm']):
        shape=terminal_shapes(s,i)[0][0].buffer(-t['dimension_tolerance_mm'])
        bore=Point(y,c['center_z_mm']).buffer(7.36/2/math.cos(math.pi/96)+allowance,quad_segs=48)
        bearing=shape.difference(bore)
        areas=[bearing.intersection(box(y-10,0,y-3.68,20)).area,
               bearing.intersection(box(y+3.68,0,y+10,20)).area]
        bearings.append(areas)
        for side,a in zip(['negative-Y','positive-Y'],areas):check(f'terminal {i+1} {side} bearing area',a,1.5)
    old_bearing=math.pi*max(0,(6.4/2)**2-(7.34/2)**2)
    netlist_path=ROOT/'experiments/power-r05l-charge-interlock/evidence/native-netlist.json'
    nets=json.loads(netlist_path.read_text())['nets']
    actual={pin:net for net,pins in nets.items() for pin in pins if pin in {'J3.1','J3.2'}}
    checks.append(dict(name='polarity matches the preserved native netlist',pass_=actual=={x['pad']:x['net'] for x in s['polarity']}))
    text=(BASE/'retention.scad').read_text()
    parts=json.loads(re.search(r'^motion_boxes = (.+);$',text,re.M).group(1))
    assert len(parts)==85
    metals=[]
    for i,y in enumerate(c['centers_y_mm']):
        for j,(shape,x0,x1) in enumerate(terminal_shapes(s,i)):
            metals.append((f'terminal {i+1} section {j+1}',shape.buffer(allowance),x0-.05,x1+.05))
        for label,dia,x0,x1 in [
            ('thread',3.05,result['thread_tip_x_mm']-.1,result['shoulder_x_mm']+.05),
            ('nut',s['nut']['rotation_envelope_diameter_mm'],result['maximum_stack_inner_x_mm'],p['bearing_x_mm']-.95-.45),
            ('washer',s['washer']['outer_diameter_incoming_max_mm'],p['bearing_x_mm']-1.05-.55,p['bearing_x_mm']-.95)]:
            metals.append((f'{label} {i+1}',Point(y,c['center_z_mm']).buffer(dia/2+.05,quad_segs=48),x0,x1))
    distances=[]
    for ref,low,size in parts:
        high=[a+b for a,b in zip(low,size)]
        obstacle=(box(low[1],low[2],high[1],high[2]),low[0],high[0])
        gap,name=min((solid_distance((shape,x0,x1),obstacle),name) for name,shape,x0,x1 in metals)
        distances.append(dict(ref=ref,gap_mm=gap,obstacle=name))
    check('all 85 swept populated envelopes clear new metal',min(x['gap_mm'] for x in distances))
    # r12 maximum cradle including its existing .05/.15mm feature/thermal bounds.
    pack=(box(-16.7,1.8,16.7,7.23),-17.4,17.4)
    check('new metal clears maximum pack/cradle envelope',min(solid_distance((shape,x0,x1),pack) for _,shape,x0,x1 in metals))
    check('opposite terminal base metal separation',12-t['base_width_mm']-2*allowance,2)
    result.update(result='CONTACT_RETENTION_GEOMETRY_PASS' if all(x['pass_'] for x in checks) else 'CONTACT_RETENTION_GEOMETRY_HOLD',
                  bearing_areas_mm2=bearings,old_circular_bearing_area_mm2=old_bearing,native_pinout=actual,component_clearances=distances,
                  scope='Source-bound geometric retention and clearance prototype. Load, torque, contact resistance, harness route/insertion, thermal cycles and ingress require separate acceptance.')
    return result


def parameters(s):
    c,p,t=s['contact'],s['pocket'],s['terminal']
    vals=dict(contact_ys=c['centers_y_mm'],contact_z=c['center_z_mm'],stem_l=c['stem_length_mm'],thread_l=c['thread_length_mm'],
              bearing_x=p['bearing_x_mm'],pocket_w=p['base_width_mm'],pocket_z=p['base_z_mm'],pocket_r=p['tail_radius_mm'],pocket_top=p['tail_top_z_mm'],
              terminal_w=t['base_width_mm'],terminal_z=t['base_z_mm'],terminal_t=t['base_thickness_mm'],tail_t=t['tail_thickness_mm'],terminal_r=t['tail_radius_mm'],
              tail_root_z=t['tail_root_z_mm'],tail_yz=t['tail_centers_yz_mm'],transition_z=t['thickness_transition_z_mm'],terminal_hole=t['thread_hole_diameter_mm'],wire_hole=t['wire_hole_diameter_mm'])
    return '// Generated from contact.json. Prototype dimensions, not physical acceptance.\n'+'\n'.join(k+' = '+json.dumps(v)+';' for k,v in vals.items())+'\n'


def main():
    s=json.loads((OUT/'contact.json').read_text());r=evaluate(s)
    files=[OUT/'contact.json',Path(__file__),ROOT/'scripts/audit_populated_fit.py',BASE/'retention.scad',BASE/'checkpoint.json',
           ROOT/s['pcb_source'],ROOT/'experiments/power-r05l-charge-interlock/evidence/native-netlist.json',ROOT/'mechanical/swim-r12-pack-retention/checkpoint.json',ROOT/'mechanical/swim-r13-charge-dock/checkpoint.json']
    r['inputs']={str(p.relative_to(ROOT)):sha(p) for p in files}
    (OUT/'checks.json').write_text(json.dumps(r,indent=2)+'\n')
    (OUT/'parameters.scad').write_text(parameters(s))
    print(r['result']);print(json.dumps([x for x in r['checks'] if not x['pass_']],indent=2))
    return 0 if r['result'].endswith('_PASS') else 2


if __name__=='__main__':raise SystemExit(main())
