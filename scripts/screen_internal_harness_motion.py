#!/usr/bin/env python3
"""Reject or characterize a simple endpoint-motion proposal; not a flex model.

PCB-attached parts and the wire's PCB end share the same translation. Expanding
parts over all poses against a stationary attached wire would invent collisions.
The input wire is one fixed length: a different fitted length at each pose is
not accepted as slack or as manufacturing tolerance.
"""
import json
from pathlib import Path

import numpy as np
from scipy.spatial import cKDTree

from check_internal_harness import BASE, OUT, ROOT, sha, point_box_distance
from internal_harness_geometry import evaluate, physical_radii
from thermal_cable_geometry import spline


def build():
    s=json.loads((OUT/'harness.json').read_text())
    motion=json.loads((BASE/'retention-checks.json').read_text())['cable_motion']['cases']
    parts=[p for p in json.loads((BASE/'antenna-fit.json').read_text())['scenarios'][2]['parts'] if p['ref']!='J3']
    nominal=[evaluate(w['controls_mm']) for w in s['wires']]
    target=[(c['arc_upper'][-1]+c['arc_lower'][-1])/2 for c in nominal]
    weights=np.array([0,0,.5,.8,1,1,1,1])[:,None]
    rows=[]
    for i,case in enumerate(motion):
        dx,dy,top=case['pcb_pose_mm'];shift=np.array([dx,dy,top-s['pcb_nominal_top_mm']])
        rf=[spline(c['control_points_mm'],4001) for c in case['cables']]
        trees=[cKDTree(c[0]) for c in rf]
        curves=[];wires=[]
        for wi,w in enumerate(s['wires']):
            control=np.array(w['controls_mm'])+weights*shift
            c=evaluate(control);curves.append(c);xyz=c['xyz'];step=c['travel_bound']
            radius=physical_radii(c,s['wire'])[0]+s['wire']['free_route_position_allowance_mm']+step/2
            gaps=[]
            for p in parts:
                a,b,d,e=p['envelope_xy_bounds_mm'];lo,hi=p['envelope_z_mm']
                ds=point_box_distance(xyz,np.array([a,b,lo])+shift,np.array([d,e,hi])+shift)-radius
                gaps.append((float(ds.min()),p['ref']))
            rf_gap=min(float((tree.query(xyz)[0]-radius-.715-data[3]/2).min()) for tree,data in zip(trees,rf))
            length=(c['arc_lower'][-1]+c['arc_upper'][-1])/2
            error=float(length-target[wi]);gap,ref=min(gaps)
            wires.append(dict(colour=w['colour'],length_mm=float(length),fixed_length_error_mm=error,
                              component_gap_mm=gap,component=ref,RF_gap_mm=rf_gap,
                              radius_lower_mm=c['radius_lower'],controls_mm=control.tolist(),
                              fixed_length_pass=abs(error)<=.001,
                              geometry_screen_pass=gap>=.2 and rf_gap>=.2 and c['radius_lower']>=s['wire']['minimum_bend_radius_mm']))
        pair=float(cKDTree(curves[0]['xyz']).query(curves[1]['xyz'])[0].min())
        pair-=s['wire']['outside_diameter_max_mm']+2*s['wire']['free_route_position_allowance_mm']+sum(c['travel_bound']/2 for c in curves)
        rows.append(dict(pcb_pose_mm=case['pcb_pose_mm'],wires=wires,pair_gap_mm=pair,
                         pass_=pair>=.2 and all(w['fixed_length_pass'] and w['geometry_screen_pass'] for w in wires)))
        if (i+1)%9==0:print('Screened',i+1,'of',len(motion),'poses',flush=True)
    paths=[OUT/'harness.json',BASE/'retention-checks.json',BASE/'antenna-fit.json',Path(__file__),
           ROOT/'scripts/internal_harness_geometry.py',ROOT/'scripts/thermal_cable_geometry.py',ROOT/'scripts/check_internal_harness.py']
    result=dict(result='LINEAR_POSE_FAMILY_REJECTED' if not all(c['pass_'] for c in rows) else 'SAMPLED_LINEAR_POSE_FAMILY_PASS',
                inputs={str(p.relative_to(ROOT)):sha(p) for p in paths},control_translation_weights=weights.ravel().tolist(),
                nominal_lengths_mm=[float(x) for x in target],fixed_length_numerical_tolerance_mm=.001,cases=rows,
                summary=dict(passing_poses=sum(c['pass_'] for c in rows),total_poses=len(rows),
                             largest_fixed_length_error_mm=max(abs(w['fixed_length_error_mm']) for c in rows for w in c['wires']),
                             minimum_pair_gap_mm=min(c['pair_gap_mm'] for c in rows)),
                scope='Diagnostic proposal only. Correlated PCB translations; existing RF pose paths. No continuous flex, restraint, service or thermal-material acceptance. Negative conservative gaps need geometry inspection before being called physical collisions.',
                physical_qualification=False,manufacturing_release=False)
    (OUT/'motion-screen.json').write_text(json.dumps(result,indent=2)+'\n')
    print(json.dumps(dict(result=result['result'],summary=result['summary']),indent=2))


if __name__=='__main__':build()
