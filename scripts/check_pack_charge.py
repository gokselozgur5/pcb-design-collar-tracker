#!/usr/bin/env python3
"""Reproduce a source-bound battery/charger incompatibility; never qualify a pack."""
import argparse
import hashlib
import itertools
import json
import math
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
FOLDER = ROOT / 'assembly/pack-charge-r01'


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def temperature_at_resistance(resistance, r25, beta):
    """Constant-beta approximation, not a guaranteed full R/T curve."""
    return 1 / (1 / 298.15 + math.log(resistance / r25) / beta) - 273.15


def temperature_permits(vts, hot, cold):
    return hot <= vts <= cold


def current_screen(pack, required):
    # A bare cell rating cannot substitute for the assembled PCM limit.
    continuous = min(pack['bare_cell_discharge_max_A'], pack['pcm_continuous_max_A'])
    return dict(required_A=required, continuous_A=continuous,
                continuous_pass=continuous >= required,
                peak_A=pack['pcm_peak_max_A'], peak_duration_s=pack['pcm_peak_duration_s'],
                pulse_duty_cycle_qualified=False)


def calculate(spec):
    c, n, p = spec['charger'], spec['ntc_candidate'], spec['pack_candidate']
    ranges = {}
    for kind in ('hot', 'cold'):
        values = [temperature_at_resistance(v / (i * 1e-6), r, b)
                  for v, i, r, b in itertools.product(
                      c[kind + '_entry_V'][::2], c['bias_uA'][::2],
                      [n['R25_ohm'] * (1 - n['R25_tolerance']), n['R25_ohm'] * (1 + n['R25_tolerance'])],
                      [n['B25_85_K'] * (1 - n['B_tolerance']), n['B25_85_K'] * (1 + n['B_tolerance'])])]
        ranges[kind] = dict(nominal_beta_C=temperature_at_resistance(
            c[kind + '_entry_V'][1] / (c['bias_uA'][1] * 1e-6), n['R25_ohm'], n['B25_85_K']),
            beta_sensitivity_range_C=[min(values), max(values)])
    # A tabulated 50 C point directly exposes the mismatch without assuming
    # constant beta across the full curve. The sensitivity below is approximate.
    r50 = dict(n['rt_table_ohm'])[50]
    delta = n['B25_85_K'] * n['B_tolerance'] * abs(1 / 323.15 - 1 / 298.15)
    v50 = [r50 * (1 - n['R25_tolerance']) * math.exp(-delta) * c['bias_uA'][0] * 1e-6,
           r50 * (1 + n['R25_tolerance']) * math.exp(delta) * c['bias_uA'][2] * 1e-6]
    permits_50 = all(temperature_permits(v, h, cold) for v, h, cold in itertools.product(
        v50, c['hot_entry_V'][::2], c['cold_entry_V'][::2]))
    return dict(result='HOLD', electrical_release=False, charge_window_implemented=False,
                pack_selected=False, ntc_selected=False,
                thresholds=ranges,
                tabulated_50C=dict(resistance_ohm=r50, nominal_ts_V=r50 * c['bias_uA'][1] * 1e-6,
                                  sensitivity_ts_V=v50, charging_permitted_at_all_reviewed_corners=permits_50,
                                  exceeds_candidate_charge_max_C=50 > p['charge_temperature_C'][1]),
                pack_current=current_screen(p, spec['engineering_supply_screen_A']),
                source_conclusion='Direct 103JT-025 cannot enforce the reviewed pack 0–45 C charging window. U3 CE is grounded. No firmware-only fix exists in this saved topology.',
                scope='Datasheet/topology analysis and constant-beta sensitivity, not a powered result, guaranteed NTC curve or safety certification.')


def compute():
    spec = json.loads((FOLDER / 'inputs.json').read_text())
    pcb = ROOT / spec['pcb']
    if sha(pcb) != spec['pcb_sha256'] or sha(pcb.with_suffix('.kicad_sch')) != spec['schematic_sha256']:
        raise ValueError('Reviewed native source changed')
    nets = json.loads((ROOT / spec['native_netlist']).read_text())['nets']
    if nets['/BAT_NTC'] != ['J4.3', 'U3.6'] or 'U3.4' not in nets['/GND']:
        raise ValueError('Charger topology differs from this review')
    result = calculate(spec)
    result.update(pcb_sha256=spec['pcb_sha256'], inputs_sha256=sha(FOLDER / 'inputs.json'),
                  checker_sha256=sha(Path(__file__)), native_netlist_sha256=sha(ROOT / spec['native_netlist']))
    return result


def verify():
    result = compute()
    if result != json.loads((FOLDER / 'check.json').read_text()):
        raise ValueError('Battery/charge report is stale')
    if not result['tabulated_50C']['charging_permitted_at_all_reviewed_corners']:
        raise ValueError('Original mismatch no longer reproduced; review new inputs')
    return dict(result='EVIDENCE_PASS', electrical_release=False,
                charge_window_implemented=False, pack_selected=False,
                finding='Direct 10k/B3435 NTC permits charging above the candidate pack 45 C limit')


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--write', action='store_true', help='Save this analysis; does not modify CAD')
    args = parser.parse_args()
    report = compute()
    if args.write:
        (FOLDER / 'check.json').write_text(json.dumps(report, indent=2) + '\n')
    verify()
    print(json.dumps(report, indent=2))
    raise SystemExit(2)  # Expected: actual electrical release remains HOLD.
