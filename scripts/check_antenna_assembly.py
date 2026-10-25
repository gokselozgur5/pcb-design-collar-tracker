#!/usr/bin/env python3
"""Check the r08 antenna assembly at native PCB positions without changing PCB.

This is a conditional geometry screen. Cable end datums, the CAPH length tolerance,
the supplied coax bend limit, clip material capability and physical RF are open.
"""
import argparse
import copy
import hashlib
import json
import math
from pathlib import Path

import numpy as np
from shapely.geometry import Point, box

from antenna_cable_geometry import curve_separation, point_box_distance, spline
from audit_populated_fit import rounded_rect, write_scad
from check_charge_fit import evaluate as component_fit


ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / 'mechanical/swim-r08-antennas'
SHA = lambda p: hashlib.sha256(p.read_bytes()).hexdigest()


def cable_rows(controls, parameters, thickness, count=4001):
    rows = []
    delta = thickness - parameters['cable_model']['authored_pcb_thickness_mm']
    for name, points in controls.items():
        control = copy.deepcopy(points)
        for i in [0, 1]:
            control[i][2] += delta
        xyz, arc, radii, step = spline(control, count)
        rows.append(dict(name=name, connector='J1' if name == 'LTE' else 'J2',
                         xyz=xyz, arc=arc, radii=radii, step=step))
    return rows


def make_clips(rows, parameters):
    """Lid-mounted clips are confined to the clear strip between the two FPCs."""
    clips = []
    for row in rows:
        xyz, arc = row['xyz'], row['arc']
        intersections = []
        for i in range(len(xyz) - 1):
            if (xyz[i, 1] - 2.6) * (xyz[i+1, 1] - 2.6) < 0:
                fraction = (2.6 - xyz[i, 1]) / (xyz[i+1, 1] - xyz[i, 1])
                center = xyz[i] + fraction * (xyz[i+1] - xyz[i])
                tangent = xyz[i+1] - xyz[i]
                tangent /= np.linalg.norm(tangent)
                if arc[i] > 10:  # Never clamp directly at the MHF1 plug exit.
                    intersections.append((center, tangent))
        assert len(intersections) == 2, (row['name'], intersections)
        for index, (center, tangent) in enumerate(intersections):
            curved_exit = row['name'] == 'GNSS' and index == 1
            half_width = 2.4 if curved_exit else 1.45
            clips.append(dict(name=f"{row['name']}-{index+1}", cable=row['name'],
                              center=center.tolist(), tangent=tangent.tolist(),
                              low=[float(center[0]-half_width), 1.9, float(center[2]-1.15)],
                              high=[float(center[0]+half_width), 3.3, parameters['body']['size'][2]],
                              bore_diameter_mm=2.0 if curved_exit else 1.8,
                              entry_slit_width_mm=1.0))
    return clips


def evaluate(native, profile, parameters, controls, count=4001):
    model = parameters['cable_model']
    radius = model['diameter_mm']/2 + model['centerline_position_allowance_mm']
    gap = model['minimum_gap_mm']
    thickness = native['board_size_mm'][2]
    parts = component_fit(native, profile, parameters)
    rows = cable_rows(controls, parameters, thickness, count)
    clips = make_clips(rows, parameters)
    cavity = rounded_rect(*parameters['body']['cavity'], parameters['body']['cavity_radius'])
    checks = []

    def check(name, ok, **details):
        checks.append(dict(name=name, pass_=bool(ok), **details))

    check('All populated component envelopes', parts['checked_geometry_pass'],
          count=parts['checked'], violations=parts['violations'])
    nominal_z = parameters['pcb']['bottom_z'] + thickness + model['plug_centerline_above_pcb_mm']
    actual = {p['ref']: p for p in native['parts']}
    summaries = []
    for row in rows:
        xyz, arc, radii, step = (row[k] for k in ['xyz', 'arc', 'radii', 'step'])
        name = row['name']
        check(name+' sample resolution', step <= model['sample_max_step_mm'], maximum_step_mm=step)
        endpoint = [*actual[row['connector']]['position_mm'], nominal_z]
        check(name+' starts at native connector', np.linalg.norm(xyz[0]-endpoint) < 1e-8,
              connector=row['connector'], endpoint_mm=xyz[0].tolist())
        check(name+' nominal length', abs(arc[-1]-98.5) < .15, centerline_length_mm=float(arc[-1]),
              basis='100 mm nominal less provisional 1.5 mm connector datum offset; supplier tolerance and end datums remain open')
        check(name+' provisional bend screen', radii.min() >= model['minimum_bend_radius_mm'],
              minimum_radius_mm=float(radii.min()), required_mm=model['minimum_bend_radius_mm'])
        wall = min(Point(*p[:2]).distance(cavity.boundary) if cavity.covers(Point(*p[:2])) else -1 for p in xyz)
        check(name+' cavity wall', wall-radius-step/2 >= gap,
              conservative_gap_mm=wall-radius-step/2)
        lid_gap = parameters['body']['size'][2]-float(xyz[:, 2].max())-radius-step/2
        # At the adhesive-mounted feed joint, contact with its own antenna is
        # intentional. The complete cable envelope must still stay below the lid.
        check(name+' below lid', lid_gap >= 0, conservative_gap_mm=lid_gap)
        self_gap = curve_separation(xyz, xyz, arc, 3.0)-2*radius-step
        check(name+' nonlocal self clearance', self_gap >= gap, conservative_gap_mm=self_gap,
              excluded_contiguous_arc_length_mm=3.0)
        distances = []
        for p in parts['parts']:
            if p['ref'] == row['connector']:
                continue  # This is the intentional mating joint only.
            a,b,c,d = p['envelope_xy_bounds_mm']
            low,high = p['envelope_z_mm']
            distance = float(point_box_distance(xyz,[a,b,low],[c,d,high]).min())-radius-step/2
            distances.append((distance,p['ref']))
        minimum, ref = min(distances)
        check(name+' populated bodies', minimum >= gap, conservative_gap_mm=minimum, limiting_ref=ref)
        antenna_checks = []
        for index, ant in enumerate(parameters['antenna_reservations']):
            center, size = np.array(ant['center']), np.array(ant['size'])
            low,high = center-size/2,center+size/2
            own = (index == 0) == (name == 'LTE')
            points = xyz
            if own:
                # FPC and its factory-attached feed cable form one assembly.
                # Their overlapping tolerance boxes are not a free-air joint.
                # Detailed feed-bond geometry is explicitly UNQUALIFIED: exclude
                # only the last 20 mm within this FPC's XY envelope. Lid, other
                # antenna, components and every other cable remain checked.
                in_joint = ((arc[-1]-arc <= 20) &
                            (xyz[:,0] >= low[0]-radius-gap) & (xyz[:,0] <= high[0]+radius+gap) &
                            (xyz[:,1] >= low[1]-radius-gap) & (xyz[:,1] <= high[1]+radius+gap))
                points = xyz[~in_joint]
            distance = float(point_box_distance(points,low,high).min())-radius-step/2
            antenna_checks.append(dict(antenna=ant['label'], conservative_gap_mm=distance,
                                       intentional_feed_joint_excluded=own))
        check(name+' antenna bodies', all(r['conservative_gap_mm'] >= gap for r in antenna_checks),
              rows=antenna_checks)
        summaries.append(dict(name=name, connector=row['connector'], length_mm=float(arc[-1]),
                              minimum_radius_mm=float(radii.min()), sample_count=len(xyz),
                              maximum_step_mm=step, centerline_bounds_mm=[xyz.min(0).tolist(),xyz.max(0).tolist()],
                              minimum_component_gap_mm=minimum, limiting_ref=ref))
    separation = curve_separation(rows[0]['xyz'],rows[1]['xyz'])-2*radius-sum(r['step']/2 for r in rows)
    check('Cable-to-cable clearance', separation >= gap, conservative_gap_mm=separation)
    for clip in clips:
        # Bores/slits are checked on actual CAD below. These whole-box checks
        # independently establish that clip bodies miss the FPCs and components.
        low,high = np.array(clip['low']),np.array(clip['high'])
        for a in parameters['antenna_reservations']:
            c,s = np.array(a['center']),np.array(a['size'])
            distance = float(np.linalg.norm(np.maximum(np.maximum(c-s/2-high,low-(c+s/2)),0)))
            check(clip['name']+' clip to '+a['label'],distance>=gap,clearance_mm=distance)
        for p in parts['parts']:
            a,b,c,d=p['envelope_xy_bounds_mm'];l,h=p['envelope_z_mm']
            distance=float(np.linalg.norm(np.maximum(np.maximum(np.array([a,b,l])-high,low-np.array([c,d,h])),0)))
            if distance < gap:
                check(clip['name']+' clip populated body',False,ref=p['ref'],clearance_mm=distance)
    return dict(result='CONDITIONAL_GEOMETRY_PASS' if all(c['pass_'] for c in checks) else 'GEOMETRY_FAIL',
                checks=checks, cables=summaries, clips=clips, parts=parts['parts']),rows,parts


def build():
    paths=[OUT/n for n in ['components.native.json','fit-profile.json','parameters.json','routing-controls.json']]
    native,profile,p,controls=[json.loads(path.read_text()) for path in paths]
    assert SHA(ROOT/native['source'])==native['source_sha256']
    scenarios=[]
    for thickness in [.71,.81,.84088,.91]:
        n,q=copy.deepcopy(native),copy.deepcopy(p)
        n['board_size_mm'][2]=q['pcb']['size'][2]=thickness
        result,rows,parts=evaluate(n,profile,q,controls)
        assert result['result']=='CONDITIONAL_GEOMETRY_PASS', [c for c in result['checks'] if not c['pass_']]
        scenarios.append(dict(thickness_mm=thickness,**result))
    current,rows,parts=evaluate(native,profile,p,controls)
    write_scad(OUT,parts,profile)
    with (OUT/'populated.scad').open('a') as f:
        f.write('carrier_leg_centers = '+json.dumps(p['carrier_leg_centers_mm'])+';\n')
    scad='// Generated by check_antenna_assembly.py; nominal conditional cable geometry.\n'
    scad+='cable_radius = '+str(p['cable_model']['diameter_mm']/2)+';\n'
    for i,row in enumerate(rows):
        # CAD uses 401 samples, independently checked against the dense path.
        xyz=row['xyz'][::10]
        scad+=f'cable_{i} = '+json.dumps(np.round(xyz,6).tolist())+';\n'
    scad+='cable_paths = [cable_0,cable_1];\n'
    scad+='cable_clips = '+json.dumps([[c['center'],c['tangent'],c['low'],c['high'],c['bore_diameter_mm'],c['entry_slit_width_mm']] for c in current['clips']])+';\n'
    (OUT/'cables.scad').write_text(scad)
    inputs=paths+[ROOT/'scripts/antenna_cable_geometry.py',ROOT/'scripts/check_antenna_assembly.py',ROOT/'scripts/audit_populated_fit.py',ROOT/'scripts/check_charge_fit.py']
    receipt=dict(pcb_sha256=native['source_sha256'],result='CONDITIONAL_GEOMETRY_PASS',
                 scenarios=scenarios, inputs={str(f.relative_to(ROOT)):SHA(f) for f in inputs},
                 generated={n:SHA(OUT/n) for n in ['populated.scad','cables.scad']},
                 antenna_parts=['Synzen SZK-C-3L30','Synzen SZK-C-0G04'],
                 physical_rf_qualified=False,physical_ingress_qualified=False,production_assembly_complete=False,
                 limits=['Nominal 100 mm cables; 1.5 mm end datum allowance and plug exit height require supplier confirmation.',
                         'CAPH drawing omits dimensional tolerances; assigned envelope allowances are engineering constraints.',
                         '3 mm bend radius and 0.15 mm path allowance are provisional; cable construction and cyclic flex not qualified.',
                         'Factory feed-bond geometry is not qualified; the final 20 mm inside its own FPC footprint is treated as an intentional assembly joint.',
                         'Clips require process/material/retention testing. Antenna-to-metal clearance is geometry, not RF acceptance.',
                         'Battery remains an unselected reservation. No physical device or IP68 test has been performed.'])
    (OUT/'antenna-fit.json').write_text(json.dumps(receipt,indent=2)+'\n')
    print(json.dumps(dict(result=receipt['result'],pcb_unchanged=True,scenarios=len(scenarios),cables=current['cables'],clips=len(current['clips'])),indent=2))
    return receipt


if __name__=='__main__':
    build()
