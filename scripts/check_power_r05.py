#!/usr/bin/env python3
"""Check the r05 native netlist and conditional timing bounds, not powered behavior.

The model deliberately has no electrical PASS state. It distinguishes topology,
calculations with explicit component assumptions, and unverified physical limits.
"""
import argparse
import hashlib
import itertools
import json
import math
from pathlib import Path
import subprocess
import tempfile
import xml.etree.ElementTree as ET

ROOT = Path(__file__).resolve().parents[1]
TRIAL = ROOT / 'experiments/power-r05-supervised'
EXPECTED_CHANGES = {'R1.1': '/POWER_GOOD', 'U4.3': '/VIO_ENABLE', 'U1.73': '/FG_ALERT'}
REMOVED = {'R10', 'R11', 'C22'}


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def require(condition, message):
    if not condition:
        raise ValueError(message)


def read(path):
    return json.loads(path.read_text())


def write(path, data):
    path.write_text(json.dumps(data, indent=2, sort_keys=True) + '\n')


def refresh():
    sch = TRIAL / 'hardware/collar-tracker.kicad_sch'
    before = sha(sch)
    runtime = ROOT / '.runtime/power-r05'
    runtime.mkdir(parents=True, exist_ok=True)
    with tempfile.TemporaryDirectory(dir=runtime) as tmp:
        target = Path(tmp) / 'netlist.xml'
        result = subprocess.run([str(ROOT / 'scripts/kicad-cli'), 'sch', 'export', 'netlist',
                                 '--format', 'kicadxml', '-o', str(target), str(sch)],
                                capture_output=True, text=True)
        (runtime / 'netlist-export.log').write_text(result.stdout + result.stderr)
        require(result.returncode == 0, 'Native export failed; see runtime log')
        require(sha(sch) == before, 'Schematic changed during export')
        root = ET.parse(target).getroot()
        write(TRIAL / 'evidence/native-netlist.json', {
            'schematic_sha256': before, 'exporter': root.findtext('./design/tool'),
            'parts': {c.attrib['ref']: c.findtext('value') for c in root.findall('./components/comp')},
            'nets': {n.attrib['name']: sorted(p.attrib['ref'] + '.' + p.attrib['pin']
                                            for p in n.findall('node'))
                     for n in root.findall('./nets/net')}})


def connected(inventory):
    result = {}
    for net, pins in inventory['nets'].items():
        if net.startswith('unconnected-'):
            continue
        for pin in pins:
            require(pin not in result, 'Duplicate pin: ' + pin)
            result[pin] = net
    return result


def check_topology(baseline, candidate):
    old, new = connected(baseline), connected(candidate)
    require(set(baseline['parts']) - set(candidate['parts']) == REMOVED,
            'Unexpected removed components')
    expected_added = {'U6', 'U7', 'U8', 'U9', 'Q1'} | {
        'R' + str(n) for n in range(16, 24)} | {'C' + str(n) for n in range(25, 31)}
    require(set(candidate['parts']) - set(baseline['parts']) == expected_added,
            'Unexpected added components')
    changes = {}
    for pin, net in old.items():
        if pin.split('.')[0] in REMOVED:
            require(pin not in new, 'Removed divider component still connected')
            continue
        expected = EXPECTED_CHANGES.get(pin, net)
        require(new.get(pin) == expected, 'Unexpected existing connection: ' + pin)
        if new[pin] != net:
            changes[pin] = {'before': net, 'after': new[pin]}
    require(set(changes) == set(EXPECTED_CHANGES), 'Missing intended connection changes')
    expected_nets = {
        '/POWER_GOOD': {'U6.1', 'R16.2', 'R19.1', 'R1.1', 'U7.3', 'U8.2'},
        '/POWER_FAULT': {'U8.4', 'Q1.2', 'Q1.5', 'R22.1'},
        '/VIO_ENABLE': {'U7.1', 'R20.2', 'U4.3', 'Q1.3'},
        '/UV_SENSE': {'U6.5', 'R17.2', 'R18.1', 'R19.2'},
        '/UV_DELAY': {'U6.4', 'C25.1'},
        '/VIO_DELAY': {'U7.4', 'C26.1'},
        '/VIO_DISCHARGE': {'Q1.6', 'R21.2'},
        '/NRF_ENABLE': {'U1.10', 'R1.2', 'C9.1', 'U7.5'},
        '/FG_ALERT': {'U9.5', 'U1.73', 'R23.2'},
    }
    for net, pins in expected_nets.items():
        require(set(candidate['nets'].get(net, [])) == pins, 'Unexpected topology: ' + net)
    required_pins = {
        'U6.6': '/VDD_NRF', 'U6.3': '/VDD_NRF', 'U7.6': '/VDD_NRF',
        'U8.5': '/VDD_NRF', 'R16.1': '/VDD_NRF', 'R17.1': '/VDD_NRF',
        'R20.1': '/VDD_NRF', 'Q1.1': '/GND', 'Q1.4': '/GND',
        'R18.2': '/GND', 'R21.1': '/VIO_1V8', 'R22.2': '/GND',
        'R23.1': '/VIO_1V8', 'U9.3': '/VBAT', 'U9.2': '/VBAT',
        'U9.7': '/I2C_SCL', 'U9.8': '/I2C_SDA', 'U9.6': '/GND',
        'U9.1': '/GND', 'U9.4': '/GND', 'U9.9': '/GND',
    }
    for ref in ['U6.2', 'U7.2', 'U8.3'] + ['C%d.2' % n for n in range(25, 31)]:
        required_pins[ref] = '/GND'
    for n in [27, 28, 29]:
        required_pins['C%d.1' % n] = '/VDD_NRF'
    required_pins['C30.1'] = '/VBAT'
    for pin, net in required_pins.items():
        require(new.get(pin) == net, 'Incorrect power/interface pin: ' + pin)
    require('/BAT_ADC' not in candidate['nets'], 'Always-on ADC feed remains')
    for ref, value in {'U6': 'TPS3808G01DBVR', 'U7': 'TPS3808G30DBVR',
                       'U8': 'SN74LVC1G14DCKR', 'Q1': 'DMN62D2UDW-7',
                       'U9': 'MAX17048G+T10', 'R1': '22k /1%',
                       'R16': '10k /1%', 'R17': '1M /0.1%', 'R18': '130k /0.1%',
                       'R19': '16.9M /1%', 'R20': '10k /1%', 'R21': '22R /1%',
                       'C9': '1uF /16V X7R', 'C25': '680nF /25V X7R',
                       'C26': '47nF /16V X7R'}.items():
        require(candidate['parts'][ref] == value, 'Unreviewed power component: ' + ref)
    return {'component_count': len(candidate['parts']), 'existing_changes': changes,
            'unchanged_connected_existing_pins': len(old) - 6 - len(changes),
            'battery_adc_feed_removed': True, 'pin_membership': 'PASS'}


def timing(inputs):
    """Independent endpoint bounds, deliberately wider than coupled physical corners."""
    falling, rising = [], []
    for rt, rb, rh, vit, leakage in itertools.product(
            [1e6 * .999, 1e6 * 1.001], [130e3 * .999, 130e3 * 1.001],
            [16.9e6 * .99, 16.9e6 * 1.01], [.405 * .98, .405 * 1.02], [-25e-9, 25e-9]):
        # VDD and the released RESET are not assumed exactly equal: include the
        # declared pull-up drop. SENSE current is positive when entering the IC.
        conductance = 1 / rt + 1 / rb + 1 / rh
        for pg_drop in [0, inputs['power_good_high_drop_V']]:
            falling.append((vit * conductance + leakage + pg_drop / rh) / (1 / rt + 1 / rh))
        for hysteresis, vol in itertools.product([0, .03], [0, .4]):
            rising.append(rt * (vit * (1 + hysteresis) * conductance + leakage - vol / rh))
    c_min, c_max = inputs['enable_cap_effective_uF']
    off_delay_min = .6 * (inputs['restart_cap_effective_nF'][0] / 175 + .0005)
    gpio_delay_min = .6 * (inputs['gpio_delay_cap_effective_nF'][0] / 175 + .0005)
    gpio_delay_max = 1.4 * (inputs['gpio_delay_cap_effective_nF'][1] / 175 + .0005)
    r_enable_min, r_enable_max = 22000 * .99, 22000 * 1.01
    r_pullup_max = 10000 * 1.01
    tau_max = (r_enable_max + r_pullup_max) * c_max * 1e-6
    # Subtract separately bounded PG drop and enable/SENSE input load.
    input_load = inputs['enable_and_sense_load_max_uA'] * 1e-6
    gaps, latest_gpio = [], []
    for rail in [min(falling), max(rising), inputs['maximum_valid_rail_V']]:
        final = rail - inputs['power_good_high_drop_V'] - (r_enable_max + r_pullup_max) * input_load
        require(final > .89 * rail, 'ENABLE cannot reach guaranteed high under declared input load')
        t_enable_high = -tau_max * math.log(1 - .89 * rail / final)
        # Earliest fixed supervisor threshold (zero unspecified minimum hysteresis).
        t_sense_early = -tau_max * math.log(1 - (2.79 * .985) / final)
        gaps.append(gpio_delay_min - max(0, t_enable_high - t_sense_early))
        t_sense_late = -tau_max * math.log(1 - (2.79 * 1.015 * 1.025) / final)
        latest_gpio.append(t_sense_late + gpio_delay_max)
    # Upper bound on time to guaranteed low: start at the maximum valid rail,
    # but use the lowest held-up rail's LOW threshold and worst RESET VOL.
    final_low = .4 + r_enable_max * inputs['enable_source_leak_max_uA'] * 1e-6
    low_threshold = .18 * min(falling)
    require(final_low < low_threshold, 'ENABLE cannot reach guaranteed low')
    low_after = r_enable_max * c_max * 1e-6 * math.log(
        (inputs['maximum_valid_rail_V'] - final_low) / (low_threshold - final_low))
    # Earliest departure from guaranteed HIGH, initially fully enabled, assuming
    # an instantly clamped PG=0. This is not a cold-start or partial-start case.
    earliest_high_departure = -r_enable_min * c_min * 1e-6 * math.log(.89)
    discharge = ((22 * 1.01 + inputs['fet_hot_rds_bound_ohm']) *
                 inputs['vio_cap_max_uF'] * 1e-6 * math.log(1.8 / .1))
    results = {
        'falling_threshold_V': [min(falling), max(falling)],
        'restart_threshold_V': [min(rising), max(rising)],
        'recognized_fault_restart_delay_min_s': off_delay_min,
        'enable_low_hold_min_s': off_delay_min - low_after,
        'gpio_after_enable_high_min_s': min(gaps),
        'gpio_enable_latest_after_power_good_s': max(latest_gpio),
        'vio_to_0p1V_estimate_max_s': discharge,
        'fully_on_enable_high_departure_min_s': earliest_high_departure,
        'turnoff_latency_budget_s': earliest_high_departure - discharge,
        'rail_must_remain_valid_until_enable_low_s': low_after,
    }
    checks = {
        'static_cutoff_above_modem_minimum': min(falling) > 3.0,
        'restart_threshold_below_nominal_full_cell': max(rising) < 4.2,
        'recognized_fault_holds_enable_low_1s': off_delay_min - low_after >= 1.0,
        'gpio_start_more_than_6ms_after_enable_high': min(gaps) > .006,
        'fully_on_shutdown_has_positive_latency_budget': earliest_high_departure > discharge,
    }
    require(all(checks.values()), 'Conditional design bound failed: ' + str(checks))
    return {'bounds': results, 'conditional_checks': checks,
            'scope': 'Analytical bounds with explicit unqualified inputs; not SPICE, silicon characterization or a bench result.'}


def verify(write_report=False):
    native = TRIAL / 'evidence/native-netlist.json'
    candidate = read(native)
    sch = TRIAL / 'hardware/collar-tracker.kicad_sch'
    require(candidate['schematic_sha256'] == sha(sch), 'Stale native inventory')
    erc_path = TRIAL / 'evidence/erc.json'
    erc = read(erc_path)
    violations = [v for sheet in erc['sheets'] for v in sheet['violations']]
    require(not violations, 'Native ERC is not clean')
    baseline = ROOT / 'evidence/power-review-r04i/native-power.json'
    inputs = TRIAL / 'evidence/timing-inputs.json'
    report = {'electrical_acceptance': 'HOLD', 'physical_test': False,
              'pcb_or_dfm_result': False,
              'topology': check_topology(read(baseline), candidate),
              'analysis': timing(read(inputs)),
              'unqualified': read(inputs)['qualification_required'],
              'inputs': {str(p.relative_to(ROOT)): sha(p) for p in [
                  native, sch, baseline, inputs, erc_path, Path(__file__)]}}
    path = TRIAL / 'evidence/power-check.json'
    if write_report:
        write(path, report)
    else:
        require(read(path) == report, 'Saved r05 power check is stale')
    return report


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--refresh', action='store_true')
    parser.add_argument('--write', action='store_true')
    args = parser.parse_args()
    if args.refresh:
        refresh()
    result = verify(args.write)
    print(json.dumps(result, indent=2))
    raise SystemExit(2)  # HOLD remains explicit even when all model checks pass.
