#!/usr/bin/env python3
"""Continuous, constant-length wire family for the r14 dry charging dock.

The manufacturer bend radius is a static design limit, not a flex-life rating.
Endpoint restraint and wire cycling require factory/physical qualification.
"""
import hashlib
import json
import math
from pathlib import Path

from check_charge_dock import evaluate as evaluate_dock

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / 'mechanical/swim-r14-wire-motion'
sha = lambda p: hashlib.sha256(p.read_bytes()).hexdigest()


def arc_length(span, amplitude, panels=4096):
    # Composite midpoint quadrature for integral hypot(L, pi*A*sin(2*pi*t)).
    return sum(math.hypot(span, math.pi * amplitude * math.sin(2 * math.pi * (i + .5) / panels))
               for i in range(panels)) / panels


def arc_error(span, amplitude, panels):
    # |f''| <= (2*pi)^2 * (B^2/L + B^4/(4*L^3)), B=pi*A.
    # Composite midpoint absolute error <= max|f''|/(24*n^2).
    b = math.pi * amplitude
    return (2 * math.pi)**2 * (b*b/span + b**4/(4*span**3)) / (24*panels**2)


def amplitude_for(span, length, panels=4096):
    if span <= 0 or length < span:
        raise ValueError('Wire cannot span endpoints without stretching')
    lo, hi = 0., length
    for _ in range(45):
        mid = (lo + hi) / 2
        if arc_length(span, mid, panels) < length:
            lo = mid
        else:
            hi = mid
    return hi


def bump_max(t0, t1):
    t0, t1 = max(0., t0), min(1., t1)
    if t0 > t1:
        return 0.
    if t0 <= .5 <= t1:
        return 1.
    return max((1-math.cos(2*math.pi*t0))/2, (1-math.cos(2*math.pi*t1))/2)


def swept_cells(start, end, amplitude, radius, step, y=6., z=5.5):
    """Enclose every shape, not just sampled poses.

    For x in a cell, t=(x-start)/(end-start) increases with x and decreases
    with either endpoint (for 0<=t<=1). Use all independent endpoint bounds,
    the global amplitude upper bound, and expand each cell by the swept radius.
    The rectangular Minkowski expansion contains the full circular insulation.
    """
    cells=[]
    n=math.ceil((end[1]-start[0])/step)
    for i in range(n):
        a=start[0]+i*step
        b=min(a+step,end[1])
        t0=(a-start[1])/(end[1]-start[1])
        t1=(b-start[0])/(end[0]-start[0])
        height=amplitude*bump_max(t0,t1)
        cells.append([a-radius,y-radius,z-radius,b+radius,y+height+radius,z+radius])
    return cells


def evaluate(spec):
    inherited=evaluate_dock(spec)
    m,h,d,c=spec['motion'],spec['harness'],spec['dock'],spec['contact']
    checks=list(inherited['checks'])

    def check(name,value,minimum):
        checks.append(dict(name=name,value=value,minimum=minimum,pass_=value>=minimum-1e-9))

    nominal_start=d['flange_back_x']+c['crimp_length']
    travel=inherited['unloaded_forward_play_bound_mm']
    starts=[nominal_start-travel-m['start_axial_tolerance'],nominal_start+m['start_axial_tolerance']]
    end_allowance=m['fixed_end_tolerance']+m['fixed_end_thermal_allowance']
    ends=[m['fixed_end_x']-end_allowance,m['fixed_end_x']+end_allowance]
    span_min,span_max=ends[0]-starts[1],ends[1]-starts[0]
    length_allowance=m['free_wire_length_tolerance']+m['wire_service_length_allowance']
    lengths=[m['free_wire_length']-length_allowance,m['free_wire_length']+length_allowance]
    delta_t=max(abs(t-m['reference_temperature_C']) for t in m['temperature_range_C'])
    check('fixed-end thermal allowance covers housing CTE bound',m['fixed_end_thermal_allowance']-
          m['fixed_end_x']*m['housing_CTE_max_per_K']*delta_t,0)
    check('start allowance covers contact feature and thermal limits',m['start_axial_tolerance']-
          c['length_tolerance']-spec['limits']['molded_feature_tolerance']-
          nominal_start*m['housing_CTE_max_per_K']*delta_t,0)
    check('wire service allowance covers effective CTE bound',m['wire_service_length_allowance']-
          m['free_wire_length']*m['wire_CTE_requirement_per_K']*delta_t,0)
    check('positive slack at longest endpoint span',lengths[0]-span_max,m['minimum_slack_at_max_span'])
    # The integral grows with both L and A. Largest required amplitude therefore
    # occurs at the shortest span and longest wire. Inflate the target by a
    # rigorously checked quadrature bound, never by a fitted sampled residual.
    amp=amplitude_for(span_min,max(lengths[1],span_min)+m['arc_error_bound_mm'],m['arc_quadrature_panels'])
    err=arc_error(span_min,amp,m['arc_quadrature_panels'])
    check('quadrature allowance covers rigorous error',m['arc_error_bound_mm']-err,0)
    # kappa=|y''|/(1+y'^2)^(3/2) <= 2*pi^2*A/L^2 everywhere.
    radius=span_min**2/(2*math.pi**2*amp)
    check('all-position continuous wire bend bound',radius,h['wire_min_bend'])
    # Nearby shell boundaries are at most 15mm from their corresponding datum
    # (side walls, cavity roof/floor and rear-relief shoulder). Account for their
    # own feature/CTE motion as well as wire and endpoint movement.
    boundary_extent=max(abs(d['wire_pocket_y'][0]),abs(d['wire_pocket_y'][1]),
                        abs(d['wire_pocket_z'][0]),abs(d['wire_pocket_z'][1]),m['rear_relief_end_x'])
    check('shell margin covers nearby feature and CTE motion',m['shell_clearance_allowance']-
          spec['limits']['molded_feature_tolerance']-boundary_extent*m['housing_CTE_max_per_K']*delta_t,0)
    inflate=h['wire_od_max']/2+m['route_position_allowance']+m['insulation_radius_allowance']+m['shell_clearance_allowance']
    outer=6+amp+inflate
    check('wire family clears cavity side',d['wire_pocket_y'][1]-outer,m['required_housing_clearance'])
    check('opposite loop envelopes remain separated',12-2*inflate,2)
    check('wire family clears cavity floor',d['pin_z']-inflate-d['wire_pocket_z'][0],m['required_housing_clearance'])
    check('wire family clears cavity roof',d['wire_pocket_z'][1]-d['pin_z']-inflate,m['required_housing_clearance'])
    shoulder=m['rear_relief_start_x']-d['flange_back_x']
    check('rear flange shoulder retains axial material',shoulder*(1-m['housing_CTE_max_per_K']*delta_t)-
          2*spec['limits']['molded_feature_tolerance'],.65)
    check('fixed-end region lies before fuse',h['fuse_center'][0]-h['fuse_body_length_requirement']/2-ends[1],3)
    cells=swept_cells(starts,ends,amp,inflate,m['slice_step'])
    poses=[]
    for i in range(m['sampled_forward_positions']):
        q=travel*i/(m['sampled_forward_positions']-1)
        start=nominal_start-q
        a=amplitude_for(m['fixed_end_x']-start,m['free_wire_length'],m['arc_quadrature_panels'])
        poses.append(dict(forward=q,start_x=start,end_x=m['fixed_end_x'],amplitude=a,
                          arc_length=arc_length(m['fixed_end_x']-start,a,m['arc_quadrature_panels'])))
    return dict(result='CONDITIONAL_WIRE_GEOMETRY_PASS' if all(x['pass_'] for x in checks) else 'WIRE_GEOMETRY_HOLD',
                checks=checks, inherited_dock=inherited, start_x_bounds=starts,end_x_bounds=ends,
                endpoint_span_bounds=[span_min,span_max],free_length_bounds=lengths,
                amplitude_upper_bound=amp,arc_error_upper_bound=err,
                continuous_radius_lower_bound=radius,wire_envelope_radius=inflate,
                swept_cells=cells,illustrative_poses=poses,physical_qualification=False,
                interpretation='Continuous geometry bound. Assumes controlled fixed ends and curve family; not a cyclic-flex, crimp, holding, electrical or ingress qualification.')


def main():
    spec=json.loads((OUT/'dock.json').read_text())
    result=evaluate(spec)
    result['inputs']={str(p.relative_to(ROOT)):sha(p) for p in [OUT/'dock.json',Path(__file__),ROOT/'scripts/check_charge_dock.py',
        ROOT/'experiments/power-r05l-charge-interlock/evidence/native-netlist.json']}
    (OUT/'checks.json').write_text(json.dumps(result,indent=2)+'\n')
    lines=['// Generated by check_dock_wire_motion.py; units mm.']
    for group in ['contact','dock','key','harness','motion']:
        for key,value in spec[group].items():
            if isinstance(value,(int,float,list)):
                lines.append(f'{group}_{key} = {json.dumps(value)};')
    lines += ['wire_swept_cells = '+json.dumps(result['swept_cells'])+';',
              'wire_envelope_radius = '+str(result['wire_envelope_radius'])+';',
              'wire_poses = '+json.dumps([[p['start_x'],p['end_x'],p['amplitude']] for p in result['illustrative_poses']])+';',
              'earliest_contact_gap = '+str(result['inherited_dock']['earliest_contact_gap_bound_mm'])+';']
    (OUT/'parameters.scad').write_text('\n'.join(lines)+'\n')
    print(result['result'],len(result['checks']),'checks; continuous radius',result['continuous_radius_lower_bound'])
    for row in result['checks']:
        if not row['pass_']:print('FAIL',row)
    if result['result']!='CONDITIONAL_WIRE_GEOMETRY_PASS':raise SystemExit(1)


if __name__=='__main__':
    main()
