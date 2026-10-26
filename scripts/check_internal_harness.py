#!/usr/bin/env python3
"""Check the internal two-wire candidate; never promote fit to physical release."""
import hashlib
import json
from pathlib import Path

import numpy as np
from scipy.spatial import cKDTree
from shapely import covers, distance, points
from shapely.geometry import LineString, Polygon

from check_thermal_assembly import retention_solids
from internal_harness_geometry import evaluate, physical_radii
from thermal_cable_geometry import spline
from antenna_cable_geometry import curve_separation

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT/'assembly/internal-charge-r02'
BASE = ROOT/'mechanical/swim-r11-thermal-fit'
sha = lambda p: hashlib.sha256(p.read_bytes()).hexdigest()


def point_box_distance(xyz, lo, hi):
    return np.linalg.norm(np.maximum(0, np.maximum(lo-xyz, xyz-hi)), axis=-1)


def check(spec):
    fit = json.loads((BASE/'antenna-fit.json').read_text())['scenarios'][2]
    motion = json.loads((BASE/'retention-checks.json').read_text())
    pose = motion['cable_motion']['cases'][spec['nominal_pose_index']]
    p = json.loads((BASE/'parameters.json').read_text())
    r = json.loads((BASE/'retention.json').read_text())
    contacts = json.loads((ROOT/'mechanical/swim-r16-contact-retention/contact.json').read_text())
    nets = json.loads((ROOT/'experiments/power-r05l-charge-interlock/evidence/native-netlist.json').read_text())['nets']
    actual = {pin:net for net,pins in nets.items() for pin in pins if pin.startswith('J3.')}
    geom_path=ROOT/'experiments/power-r05l-charge-interlock/evidence/route-geometry.json'
    geom=json.loads(geom_path.read_text())
    if sha(ROOT/geom['source']) != geom['source_sha256']:
        raise ValueError('Native pad geometry belongs to a different PCB')
    pads={p['pin']:p for p in geom['pads'] if p['ref']=='J3'}
    rf = [spline(x['control_points_mm'], 4001) for x in pose['cables']]
    trees = [cKDTree(x[0]) for x in rf]
    rf_radius = p['cable_model']['diameter_mm']/2 + p['cable_model']['centerline_position_allowance_mm']
    solids = sum((list(x) for x in retention_solids(p,r)), [])
    rows = []
    checks = []
    def add(name, value, minimum):
        checks.append(dict(name=name, value=float(value), minimum=minimum, pass_=bool(value >= minimum-1e-8)))
    expected = [('red','J3.1','/VIN_5V',-6), ('black','J3.2','/GND',6)]
    mapping = [(w['colour'], w['pad'], w['net'], w['contact_y_mm']) for w in spec['wires']]
    checks.append(dict(name='native J3 and contact polarity', pass_=mapping==expected and actual==dict((w['pad'],w['net']) for w in spec['wires'])))
    add('PCB strip covers the complete bonded length',spec['wire']['pcb_strip_mm']-spec['wire']['strip_length_tolerance_mm']-spec['wire']['free_route_position_allowance_mm'],spec['joints']['pcb_bonded_length_min_mm'])
    curves = []
    for wi, w in enumerate(spec['wires']):
        c = evaluate(w['controls_mm'])
        curves.append(c)
        xyz = c['xyz']; step = c['travel_bound']; nominal, bare = physical_radii(c,spec['wire'])
        radius = nominal + spec['wire']['free_route_position_allowance_mm'] + step/2
        label = w['colour']
        self_gap=curve_separation(xyz,xyz,c['arc_lower'],3.)-spec['wire']['outside_diameter_max_mm']-2*spec['wire']['free_route_position_allowance_mm']-step
        add(label+' nonlocal self clearance',self_gap,spec['minimum_gap_mm'])
        add(label+' continuous bend radius lower bound', c['radius_lower'], spec['wire']['minimum_bend_radius_mm'])
        gaps=[]
        for part in fit['parts']:
            if part['ref']=='J3':
                continue  # J3 is the pair of owned solder pads, not a component body.
            a,b,d,e=part['envelope_xy_bounds_mm'];z0,z1=part['envelope_z_mm']
            ds=point_box_distance(xyz,np.array([a,b,z0]),np.array([d,e,z1]))-radius
            idx=int(ds.argmin());gaps.append(dict(ref=part['ref'],gap_mm=float(ds[idx]),xyz_mm=xyz[idx].tolist()))
        limiting=min(gaps,key=lambda x:x['gap_mm'])
        add(label+' other populated bodies',limiting['gap_mm'],spec['minimum_gap_mm'])
        rfgaps=[]
        for name,tree,data in zip(['LTE','GNSS'],trees,rf):
            ds=tree.query(xyz)[0]-radius-rf_radius-data[3]/2
            rfgaps.append(dict(name=name,gap_mm=float(ds.min())))
            add(label+' to '+name+' cable',float(ds.min()),spec['minimum_gap_mm'])
        mechanical=[]
        for name,shape,lo,hi in solids:
            horizontal=distance(shape,points(xyz[:,:2]))
            vertical=np.maximum(0,np.maximum(lo-xyz[:,2],xyz[:,2]-hi))
            gap=float((np.hypot(horizontal,vertical)-radius).min())
            mechanical.append(dict(name=name,gap_mm=gap))
        m=min(mechanical,key=lambda x:x['gap_mm'])
        add(label+' carrier, frame and lid posts',m['gap_mm'],spec['minimum_gap_mm'])
        for antenna in p['antenna_reservations']:
            center=np.array(antenna['center']);size=np.array(antenna['size'])
            gap=float((point_box_distance(xyz,center-size/2,center+size/2)-radius).min())
            add(label+' to '+antenna['label'],gap,spec['minimum_gap_mm'])
        add(label+' lid roof',float((p['body']['size'][2]-xyz[:,2]-radius).min()),spec['minimum_gap_mm'])
        # Screen the ordinary cavity after the dedicated contact pocket. The
        # short terminal transition is checked separately in the CAD stage.
        inner=xyz[:,0] <= 20.5
        side=p['body']['cavity'][1]/2-np.abs(xyz[inner,1])-radius[inner]
        add(label+' cavity Y walls',float(side.min()),spec['minimum_gap_mm'])
        end=np.array(w['controls_mm'][-1]);start=np.array(w['controls_mm'][0])
        target=np.array([[-16.75,-12.2,11.48],[-14.25,-12.2,11.48]][wi])
        target[:2]+=w['pcb_tip_offset_mm']
        add(label+' endpoint at native pad datum',1e-8-float(np.linalg.norm(end-target)),0)
        hole=np.array([contacts['pocket']['bearing_x_mm']-spec['joints']['terminal_tip_setback_from_pocket_face_mm'],*contacts['terminal']['tail_centers_yz_mm'][wi]])
        add(label+' endpoint at terminal-hole datum',1e-8-float(np.linalg.norm(start-hole)),0)
        tangent=np.array(w['controls_mm'][1])-start
        tangent/=np.linalg.norm(tangent)
        core=spec['wire']['conductor_diameter_incoming_max_mm']/2
        tip_error=spec['wire']['joint_tip_position_allowance_mm']
        tip_x_extent=core*np.sqrt(1-tangent[0]**2)
        tip_gap=contacts['pocket']['bearing_x_mm']-contacts['pocket']['feature_tolerance_mm']-start[0]-tip_x_extent-tip_error
        add(label+' flat wire tip clears pocket back',float(tip_gap),spec['joints']['terminal_wire_tip_to_body_min_mm'])
        front=contacts['pocket']['bearing_x_mm']-contacts['terminal']['tail_thickness_mm']
        insertion=start[0]-front-tip_error-contacts['terminal']['dimension_tolerance_mm']
        add(label+' wire insertion into terminal',insertion,spec['joints']['terminal_insertion_min_mm'])
        front_point=start+tangent*((front-start[0])/tangent[0])
        eccentric=float(np.linalg.norm(front_point[1:]-hole[1:]))
        hole_radius=(contacts['terminal']['wire_hole_diameter_mm']-contacts['terminal']['dimension_tolerance_mm'])/2
        radial_gap=hole_radius-core/abs(tangent[0])-eccentric-tip_error-contacts['terminal']['dimension_tolerance_mm']
        add(label+' conductor passes terminal hole',radial_gap,spec['joints']['terminal_hole_radial_clearance_min_mm'])
        native=pads[str(wi+1)]
        # Existing PCB-to-case frame: centre X=118, Y=114; board Y is inverted.
        pad_shape=Polygon([(x-118,114-y) for x,y in native['poly'][0]])
        planar=points(xyz[:,:2])
        owned=covers(pad_shape,planar)&(distance(pad_shape.boundary,planar)>=radius)
        board_gap=point_box_distance(xyz,np.array([-20,-16,10.4]),np.array([20,16,spec['pcb_nominal_top_mm']]))-radius
        add(label+' unowned PCB copper clearance',float(board_gap[~owned].min()),spec['minimum_gap_mm'])
        add(label+' tip offset follows native pad centre',1e-8-float(np.linalg.norm(end[:2]-np.array(w['pcb_tip_offset_mm'])-np.array([native['pos'][0]-118,114-native['pos'][1]]))),0)
        remaining=c['arc_upper'][-1]-c['arc_upper']
        bonded=xyz[remaining<=spec['joints']['pcb_bonded_length_min_mm']+step]
        # Include one full travel interval past the stated bond length, so a
        # discrete sample cannot exaggerate the copper margin.
        joint_radius=core+spec['joints']['pcb_joint_tip_position_allowance_mm']
        projection=LineString(bonded[:,:2]).buffer(joint_radius,quad_segs=48)
        edge=float(pad_shape.boundary.distance(projection)) if pad_shape.covers(projection) else -1.
        add(label+' bonded conductor remains on native copper',edge,spec['joints']['pcb_pad_edge_margin_mm'])
        add(label+' bonded conductor within solder-height envelope',
            spec['joints']['pcb_fillet_height_max_mm']-(float(bonded[:,2].max())+joint_radius-spec['pcb_nominal_top_mm']),0)
        rows.append(dict(colour=label,length_interval_mm=[float(c['arc_lower'][-1]),float(c['arc_upper'][-1])],
                         continuous_radius_lower_mm=c['radius_lower'],travel_bound_mm=step,
                         component_limiting=limiting,rf_gaps=rfgaps,mechanical_limiting=m,
                         strip_lengths_mm=[spec['wire']['terminal_strip_mm'],spec['wire']['pcb_strip_mm']]))
    pair=cKDTree(curves[0]['xyz']).query(curves[1]['xyz'])[0].min()
    pair-=spec['wire']['outside_diameter_max_mm']+2*spec['wire']['free_route_position_allowance_mm']
    pair-=sum(c['travel_bound']/2 for c in curves)
    add('opposite wire envelopes',float(pair),spec['minimum_gap_mm'])
    total_length=sum(row['length_interval_mm'][1] for row in rows)
    resistance=spec['wire']['nominal_DCR_ohm_per_1000ft_at_20C']*total_length/(304.8*1000)
    paths=[OUT/'harness.json',OUT/'sources.json',Path(__file__),ROOT/'scripts/internal_harness_geometry.py',
           BASE/'antenna-fit.json',BASE/'retention-checks.json',BASE/'parameters.json',BASE/'retention.json',
           ROOT/'mechanical/swim-r16-contact-retention/contact.json',
           ROOT/'experiments/power-r05l-charge-interlock/evidence/native-netlist.json',
           ROOT/'scripts/check_thermal_assembly.py',ROOT/'scripts/thermal_cable_geometry.py',ROOT/'scripts/antenna_cable_geometry.py',geom_path,ROOT/geom['source']]
    return dict(result='NOMINAL_ROUTE_SCREEN_PASS' if all(x['pass_'] for x in checks) else 'HOLD',
                inputs={str(path.relative_to(ROOT)):sha(path) for path in paths},checks=checks,wires=rows,
                nominal_wire_only_resistance_ohm_at_20C=resistance,
                wire_only_sensitivity=[dict(current_A=i,drop_V=i*resistance,dissipation_W=i*i*resistance) for i in [.1,.35,.5]],
                physical_qualification=False,manufacturing_release=False,
                open=['Exact body/contact-pocket and solder-joint CAD checks',
                      'Constant cut length across movement and temperature; no free-wire shape guarantee',
                      'Implemented restraint, factory forming/joining and service sequence',
                      'Fault-current/fuse coordination, powered resistance, pull and fatigue tests'])


if __name__=='__main__':
    result=check(json.loads((OUT/'harness.json').read_text()))
    (OUT/'route-checks.json').write_text(json.dumps(result,indent=2)+'\n')
    print(json.dumps(dict(result=result['result'],wires=result['wires'],failures=[x for x in result['checks'] if not x['pass_']]),indent=2))
    raise SystemExit(result['result']=='HOLD')
