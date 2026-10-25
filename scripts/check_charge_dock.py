#!/usr/bin/env python3
"""Bound the charging dock's geometry, with manufacturing assumptions explicit."""
import hashlib
import itertools
import json
import math
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / 'mechanical/swim-r13-charge-dock'
PCB = ROOT / 'experiments/power-r05l-charge-interlock/evidence'
sha = lambda p: hashlib.sha256(p.read_bytes()).hexdigest()


def evaluate(s):
    c, d, k, t, h = (s[n] for n in ['contact', 'dock', 'key', 'limits', 'harness'])
    checks = []

    def check(name, value, minimum):
        checks.append(dict(name=name, value=value, minimum=minimum,
                           pass_=value >= minimum - 1e-9))

    ft = t['molded_feature_tolerance']
    lt = c['length_tolerance']
    dt = c['diameter_tolerance']
    thermal = t['differential_thermal_axial']
    # Spring force seats the flange against the BACK stop while operating.
    # The compression calculation is not valid for an unheld, separating dock.
    strokes, bottom = [], []
    for a, travel, back, head, gap, therm in itertools.product(
        [c['full_stroke_to_flange_back'] - lt, c['full_stroke_to_flange_back'] + lt],
        [c['stroke'] - c['stroke_tolerance'], c['stroke'] + c['stroke_tolerance']],
        [d['flange_back_x'] - ft, d['flange_back_x'] + ft],
        [t['case_head_height'] - t['case_head_tolerance'], t['case_head_height'] + t['case_head_tolerance']],
        [0, t['mate_gap_max']], [-thermal, thermal]):
        compression = head - gap - (back + therm - a - travel)
        strokes.append(compression)
        # Travel cancels here: do not combine an impossible long/short spring.
        bottom.append(travel - compression)
    check('minimum operating compression', min(strokes), t['min_operating_stroke'])
    check('minimum remaining spring travel', min(bottom), t['min_bottoming_margin'])
    # Conservative forward movement: ignore the barb's earlier stop and use only
    # the flange and front shoulder. This also bounds unseated pins during mating.
    forward_play = d['flange_back_x'] + ft - (c['flange_t'] - lt) - (d['front_stop_x'] - ft)
    earliest_contact = (t['case_head_height'] + t['case_head_tolerance']
                        - (d['flange_back_x'] - ft - thermal
                           - c['full_stroke_to_flange_back'] - lt
                           - c['stroke'] - c['stroke_tolerance'] - forward_play))
    key_reach = k['length'] - ft - t['key_position_error']
    check('reversed key stops before earliest conductive touch', key_reach - earliest_contact,
          t['min_key_early_margin'])
    # After a 180 degree turn about the contact axis, the taller r13 key hits the
    # solid front nose below the right-way key slot. The old high key misses it.
    reverse_lo, reverse_hi = 2 * d['pin_z'] - k['z_max'], 2 * d['pin_z'] - k['z_min']
    reverse_overlap = min(reverse_hi, d['nose_top']) - max(reverse_lo, d['nose_bottom'])
    check('reversed key overlaps solid nose in Z', reverse_overlap - 2 * t['key_position_error'], .5)
    check('key depth clearance', k['slot_depth'] - ft - k['length'] - ft - thermal, .1)
    check('key lateral clearance', (k['slot_y_max'] - k['y_max']) - 2 * ft, .1)
    check('key lower clearance', k['z_min'] - k['slot_z_min'] - 2 * ft, .1)
    for name, hole, solid in [('upper barrel', d['upper_bore_d'], c['barrel_d']),
                              ('flange', d['flange_pocket_d'], c['flange_d']),
                              ('crimp barrel', d['tail_bore_d'], c['crimp_d'])]:
        check(name + ' radial running gap', (hole - ft - solid - dt) / 2,
              t['min_radial_clearance'])
    check('front flange bearing width', (c['flange_d'] - dt - d['upper_bore_d'] - ft) / 2, .025)
    check('rear flange bearing width', (c['flange_d'] - dt - d['tail_bore_d'] - ft) / 2, .05)
    # The stepped chamber starts ahead of the larger step even with two independent
    # length tolerances. It does not rely on a claimed press fit of a wire-mount pin.
    step_min = d['flange_back_x'] - ft - c['upper_step_to_flange_back'] - 2 * lt - thermal
    check('front stop clears larger pin step', step_min - d['front_stop_x'] - ft, .1)
    check('rear pin barrel fits before wire pocket', d['wire_pocket_x'][0] -
          (d['flange_back_x'] + ft + c['crimp_length'] + lt + thermal), .25)
    check('dock covers pin and cable termination', d['depth'] - d['wire_exit_x'], 4)
    check('head pocket depth', d['head_pocket_depth'] - ft -
          t['case_head_height'] - t['case_head_tolerance'], .2)
    check('head pocket radial allowance', (d['head_pocket_d'] - ft - 8.5 - ft) / 2, .15)
    check('contact lands fully on head', (8.5 - .1 - c['tip_d'] - dt) / 2 - t['pin_position_error'], .5)
    check('nose clears boot in Y', (36 - d['nose_width']) / 2 - ft - t['boot_position_allowance'], .05)
    check('nose clears boot lower edge', d['nose_bottom'] - .8 - ft - .10, .025)
    check('nose clears boot upper edge', 13.4 - d['nose_top'] - ft - .10, .025)
    check('rear housing clears boot face', d['rear_start'] - 1.5 - ft - t['boot_position_allowance'], .2)
    check('wire fits contact crimp hole', (c['wire_hole_d'] - dt - h['wire_conductor_d']) / 2, .1)
    # y(x) = y0 + (y1-y0)(3t²-2t³). Since |y''| <= 6dy/L²,
    # curvature <= 6dy/L² everywhere. This is a continuous lower radius bound.
    length = h['route_x'][1] - h['route_x'][0]
    dy = math.hypot(h['route_y'][1] - h['route_y'][0], h['jacket_center_z_allowance'])
    radius = length * length / (6 * dy)
    check('continuous tail bend lower bound', radius, h['usb_tail_bend_requirement'])
    check('opposite wire insulation gap', 2 * h['route_y'][1] - h['usb_tail_d_requirement'], .2)
    check('USB jacket fits exit', (d['wire_exit_d'] - ft -
          h['usb_cable_d_nom'] - h['usb_cable_d_tolerance']) / 2 - h['jacket_center_z_allowance'], .05)
    check('insulated fuse fits cavity height', (d['wire_pocket_z'][1] - d['wire_pocket_z'][0]
          - h['fuse_insulated_d_requirement']) / 2, .5)
    check('fuse and return wire separation', 12 - h['fuse_insulated_d_requirement'] / 2 -
          h['wire_od_max'] / 2, 2)
    netlist = json.loads((PCB / 'native-netlist.json').read_text())
    required = {'J3.1': '/VIN_5V', 'J3.2': '/GND', 'J4.1': '/VBAT', 'J4.2': '/GND', 'J4.3': '/BAT_NTC'}
    actual = {pin: net for net, pins in netlist['nets'].items() for pin in pins if pin in required}
    check('native J3/J4 pinout agrees', int(actual == required), 1)
    passed = all(row['pass_'] for row in checks)
    return dict(result='CONDITIONAL_DOCK_GEOMETRY_PASS' if passed else 'DOCK_GEOMETRY_HOLD',
                checks=checks, operating_compression_mm=[min(strokes), max(strokes)],
                minimum_bottoming_margin_mm=min(bottom), unloaded_forward_play_bound_mm=forward_play,
                earliest_contact_gap_bound_mm=earliest_contact, continuous_tail_radius_bound_mm=radius,
                maximum_pair_force_at_midstroke_N=2 * c['midstroke_force_g'][1] * .00980665,
                force_note='Midstroke only; force over the complete tolerance stroke is not bounded by this number.',
                native_pinout=actual, qualification=s['qualification'])


def write_parameters(s, r):
    lines = ['// Generated by scripts/check_charge_dock.py. Edit dock.json.']
    for group in ['contact', 'dock', 'key', 'harness']:
        for key, value in s[group].items():
            if isinstance(value, (int, float, list)):
                lines.append(group + '_' + key + ' = ' + json.dumps(value) + ';')
    lines.append('earliest_contact_gap = ' + str(r['earliest_contact_gap_bound_mm']) + ';')
    (OUT / 'parameters.scad').write_text('\n'.join(lines) + '\n')


def main():
    s = json.loads((OUT / 'dock.json').read_text())
    r = evaluate(s)
    r['inputs'] = {str(p.relative_to(ROOT)): sha(p) for p in
                  [OUT / 'dock.json', Path(__file__), PCB / 'native-netlist.json',
                   ROOT / 'mechanical/swim-r12-pack-retention/body.stl',
                   ROOT / 'mechanical/swim-r11-thermal-fit/parameters.scad']}
    (OUT / 'checks.json').write_text(json.dumps(r, indent=2) + '\n')
    write_parameters(s, r)
    print(r['result'], len(r['checks']), 'checks')
    for row in r['checks']:
        if not row['pass_']:
            print('FAIL', row)
    if r['result'] != 'CONDITIONAL_DOCK_GEOMETRY_PASS':
        raise SystemExit(1)


if __name__ == '__main__':
    main()
