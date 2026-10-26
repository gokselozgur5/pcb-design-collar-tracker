#!/usr/bin/env python3
"""Check r15 clamp geometry; do not infer friction or physical retention."""
import hashlib
import itertools
import json
import math
from pathlib import Path

from check_dock_wire_motion import evaluate as evaluate_wire

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / 'mechanical/swim-r15-wire-clamp'
sha = lambda p: hashlib.sha256(p.read_bytes()).hexdigest()


def validate_contact_faces(name, points, spec):
    """Accept only the actual planar bearing faces, never a penetration volume."""
    c, d = spec['clamp'], spec['dock']
    lo, hi = d['pin_z']-c['gap']/2, d['pin_z']+c['gap']/2
    pad = name == 'pad_interference'
    planes = [lo, hi] if pad else [hi+(c['cap_thickness'] if name == 'screw_interference' else 0)]
    if not points or len(points) % 3:
        raise ValueError('Missing contact triangles')
    # A triangle must lie in one plane, not bridge two permitted planes.
    for i in range(0, len(points), 3):
        if not any(all(abs(p[2]-z)<1e-6 for p in points[i:i+3]) for z in planes):
            raise ValueError('Nonplanar contact overlap')
    if pad:
        width = c['pad_width']+c['pad_dimension_tolerance']
        good = all(c['pad_x'][0]-1e-5 <= p[0] <= c['pad_x'][1]+c['pad_dimension_tolerance']+1e-5
                   and min(abs(p[1]-y) for y in d['pin_y'])<=width/2+1e-5 for p in points)
    else:
        radius = c['screw_head_d']/2 if name == 'screw_interference' else 2.6
        distances = [min(math.hypot(p[0]-c['screw_x'], p[1]-y) for y in c['screw_y']) for p in points]
        good = min(distances)>=c['screw_hole_d']/2-1e-5 and max(distances)<=radius+1e-5
    if not good:
        raise ValueError('Unexpected contact footprint')


def evaluate(spec):
    wire = evaluate_wire(spec)
    c, d, h, m = (spec[k] for k in ['clamp', 'dock', 'harness', 'motion'])
    checks = []

    def check(name, value, minimum):
        checks.append(dict(name=name, value=value, minimum=minimum,
                           pass_=value >= minimum - 1e-9))

    check('inherited continuous wire screen passes',
          int(wire['result'] == 'CONDITIONAL_WIRE_GEOMETRY_PASS'), 1)
    pad = [c['pad_thickness'] + sign * (c['pad_thickness_tolerance'] +
           c['pad_service_thickness_allowance']) for sign in [-1, 1]]
    gap = [c['gap'] + sign * (c['gap_feature_tolerance'] +
           c['gap_service_allowance']) for sign in [-1, 1]]
    diameter = [c['wire_od_min'] - c['wire_service_diameter_allowance'],
                h['wire_od_max'] + c['wire_service_diameter_allowance']]
    check('positive pad thickness', pad[0], .5)
    # Flat-pad displacement at the wire center; not a pressure/friction model.
    # Independent upper/lower sheet limits, wire OD and hard-stop gap.
    squeeze = [(a+b+od-g)/(a+b)
               for a, b, od, g in itertools.product(pad, pad, diameter, gap)]
    check('minimum local pad displacement', min(squeeze), c['squeeze_fraction_limits'][0])
    check('maximum local pad displacement', c['squeeze_fraction_limits'][1], max(squeeze))
    check('hard faces do not pinch bare wire envelope', gap[0]-diameter[1], .8)
    check('pad front defines the inherited end plane',
          m['fixed_end_tolerance']-abs(c['pad_x'][0]-m['fixed_end_x']), .1)
    check('assigned end-plane slip stays within feature allowance',
          m['fixed_end_tolerance']-c['endpoint_slip_limit'], 0)
    check('pad has useful contact length', c['pad_x'][1]-c['pad_x'][0]-2*c['pad_dimension_tolerance'], 5.5)
    check('maximum incoming pad fits its pocket', c['pad_pocket_extra']-
          c['pad_dimension_tolerance']-spec['limits']['molded_feature_tolerance'], .05)
    check('splice stays beyond clamp cap', c['first_splice_x']-c['cap_x'][1], .4)
    check('splice and fuse datums agree',
          1-abs(c['first_splice_x']+h['splice_envelope'][0] -
                (h['fuse_center'][0]-h['fuse_body_length_requirement']/2)), 1)
    check('screw column clears pad pocket',
          min(abs(y) for y in c['screw_y'])-2.6-6-c['pad_width']/2-c['pad_dimension_tolerance'], 1)
    check('clamp cap clears side wall',
          d['wire_pocket_y'][1]-c['cap_half_width']-c['cap_fit_allowance'], .5)
    upper = d['pin_z'] + c['gap']/2
    cap_top = upper+c['cap_thickness']
    check('cap and screw head fit below dock roof',
          d['top']-cap_top-c['screw_head_h']-c['cap_fit_allowance'], 2)
    # Assigned stack error includes feature, flatness and service movement.
    stack_error = .12
    tip = [cap_top-stack_error-c['screw_length']-c['screw_length_tolerance'],
           cap_top+stack_error-c['screw_length']+c['screw_length_tolerance']]
    check('clamp screws stay above dock bottom', tip[0]-d['bottom'], .1)
    check('minimum axial nut overlap',
          min(c['nut_h'][0], c['nut_ceiling_z']-.05-tip[1]), 1.2)
    check('pad service budget is nonzero', c['pad_service_thickness_allowance'], .02)
    check('gap service budget is nonzero', c['gap_service_allowance'], .015)
    check('wire service budget is nonzero', c['wire_service_diameter_allowance'], .01)
    return dict(result='CLAMP_GEOMETRY_PASS' if all(x['pass_'] for x in checks) else 'CLAMP_GEOMETRY_HOLD',
                checks=checks, wire=wire, pad_thickness_bounds=pad, hard_gap_bounds=gap,
                local_pad_displacement_fraction=[min(squeeze), max(squeeze)],
                screw_tip_z_bounds=tip, cap_top_z=cap_top,
                physical_retention_qualified=False,
                interpretation='Geometry with assigned material/service bounds. Endpoint slip, pressure, friction, creep and flex life require physical tests.')


def main():
    spec = json.loads((OUT/'dock.json').read_text())
    result = evaluate(spec)
    result['inputs'] = {str(p.relative_to(ROOT)): sha(p) for p in [
        OUT/'dock.json', Path(__file__), ROOT/'scripts/check_dock_wire_motion.py',
        ROOT/'scripts/check_charge_dock.py',
        ROOT/'experiments/power-r05l-charge-interlock/evidence/native-netlist.json']}
    (OUT/'checks.json').write_text(json.dumps(result, indent=2)+'\n')
    lines = ['// Generated by check_dock_wire_clamp.py; units mm.']
    for group in ['contact', 'dock', 'key', 'harness', 'motion', 'clamp']:
        for key, value in spec[group].items():
            if isinstance(value, (int, float, list)):
                lines.append(f'{group}_{key} = {json.dumps(value)};')
    wire = result['wire']
    lines += ['wire_swept_cells = '+json.dumps(wire['swept_cells'])+';',
              'wire_envelope_radius = '+str(wire['wire_envelope_radius'])+';',
              'wire_poses = '+json.dumps([[p['start_x'], p['end_x'], p['amplitude']]
                                        for p in wire['illustrative_poses']])+';',
              'earliest_contact_gap = '+str(wire['inherited_dock']['earliest_contact_gap_bound_mm'])+';']
    (OUT/'parameters.scad').write_text('\n'.join(lines)+'\n')
    print(result['result'], len(result['checks']), 'clamp checks;', len(wire['checks']), 'inherited checks')
    print('Local pad displacement fraction:', result['local_pad_displacement_fraction'])
    for check in result['checks']:
        if not check['pass_']: print('FAIL', check)
    if result['result'] != 'CLAMP_GEOMETRY_PASS': raise SystemExit(1)


if __name__ == '__main__':
    main()
