#!/usr/bin/env python3
"""Reproduce the r04i power-domain review; HOLD is not a powered test result.

--refresh exports the actual native schematic through KiCad and saves a portable
pin/net inventory. All other modes are read-only except --write, which updates
the derived report. This review is deliberately specific to the frozen r04i
circuit: an unexpected topology must be reviewed, not silently accepted.
"""
import argparse
import hashlib
import json
import math
from pathlib import Path
import re
import subprocess
import tempfile
import xml.etree.ElementTree as ET

ROOT = Path(__file__).resolve().parents[1]
TRIAL = ROOT / 'experiments/paul-nanosim-r04i-sim-access-40x32'
OUT = ROOT / 'evidence/power-review-r04i'
BOARD = TRIAL / 'hardware/collar-tracker.kicad_pcb'
SCH = TRIAL / 'hardware/collar-tracker.kicad_sch'


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def require(condition, message):
    if not condition:
        raise ValueError(message)


def save(path, value):
    path.write_text(json.dumps(value, indent=2, sort_keys=True) + '\n')


def read(path):
    return json.loads(path.read_text())


def refresh():
    """Export, check source identity twice, and omit absolute/private paths."""
    before = sha(SCH)
    runtime = ROOT / '.runtime/power-review'
    runtime.mkdir(parents=True, exist_ok=True)
    with tempfile.TemporaryDirectory(dir=runtime) as tmp:
        target = Path(tmp) / 'netlist.xml'
        proc = subprocess.run(
            [str(ROOT / 'scripts/kicad-cli'), 'sch', 'export', 'netlist',
             '--format', 'kicadxml', '-o', str(target), str(SCH)],
            capture_output=True, text=True, check=False)
        (runtime / 'netlist-export.log').write_text(proc.stdout + proc.stderr)
        require(proc.returncode == 0, 'KiCad netlist export failed; see runtime log')
        require(sha(SCH) == before, 'Schematic changed during export')
        xml = ET.parse(target).getroot()
        parts = {c.attrib['ref']: c.findtext('value')
                 for c in xml.findall('./components/comp')}
        nets = {n.attrib['name']: sorted(
                    node.attrib['ref'] + '.' + node.attrib['pin']
                    for node in n.findall('node'))
                for n in xml.findall('./nets/net')}
        OUT.mkdir(parents=True, exist_ok=True)
        save(OUT / 'native-power.json', {
            'schematic_sha256': before,
            'exporter': xml.findtext('./design/tool'),
            'parts': parts, 'nets': nets})


def engineering_value(value):
    match = re.fullmatch(r'(\d+(?:\.\d+)?)([Mkunp]?)(?:F)?', value.split()[0])
    require(match is not None, 'Unsupported component value: ' + value)
    return float(match[1]) * {'': 1, 'M': 1e6, 'k': 1e3,
                             'u': 1e-6, 'n': 1e-9, 'p': 1e-12}[match[2]]


def review():
    inventory = read(OUT / 'native-power.json')
    geometry = read(TRIAL / 'evidence/route-geometry.json')
    paths = read(TRIAL / 'evidence/power-path-review.json')
    spec = read(OUT / 'review-inputs.json')
    require(inventory['schematic_sha256'] == sha(SCH), 'Stale schematic inventory')
    require(geometry['source_sha256'] == sha(BOARD), 'Stale board geometry')
    require(paths['source_sha256'] == sha(BOARD), 'Stale copper-path estimate')
    pin_net = {}
    for name, pins in inventory['nets'].items():
        for pin in pins:
            require(pin not in pin_net, 'Duplicate schematic pin: ' + pin)
            pin_net[pin] = name
    observed = {}
    refs = {'U1', 'U3', 'U4', 'R1', 'C9', 'R6', 'R7', 'R10', 'R11', 'FB1', 'J3', 'J4'}
    for pad in geometry['pads']:
        if pad['ref'] not in refs or not pad['pin']:
            continue
        pin = pad['ref'] + '.' + pad['pin']
        require(pin_net.get(pin) == pad['net'], 'Schematic/PCB power pin mismatch: ' + pin)
        observed[pin] = pad['net']
    expected = {
        '/NRF_ENABLE': {'R1.2', 'C9.1', 'U1.10'},
        '/VDD_NRF': {'C3.1', 'C4.1', 'FB1.2', 'R1.1', 'U1.14'},
        '/VBAT': {'C19.1', 'J4.1', 'R10.1', 'U3.2'},
        '/BAT_ADC': {'C22.1', 'R10.2', 'R11.1', 'U1.73'},
    }
    for net, pins in expected.items():
        require(set(inventory['nets'][net]) == pins,
                'Power topology changed; re-review required: ' + net)
    require(pin_net['U4.1'] == pin_net['U4.3'] == pin_net['U3.1'] == '/VSYS',
            'LDO enable topology changed; re-review required')
    require(pin_net['U4.5'] == pin_net['U1.65'] == '/VIO_1V8',
            'GPIO supply topology changed; re-review required')
    require(pin_net['R11.2'] == '/GND', 'ADC divider topology changed')
    parts = inventory['parts']
    for ref, value in {'U1': 'nRF9151-LACA', 'U3': 'BQ25185DLHR',
                       'U4': 'TPS7A0218PDBVR', 'R6': '18k /1%'}.items():
        require(parts[ref] == value, 'Power part changed: ' + ref)
    val = lambda ref: engineering_value(parts[ref])
    rc_seconds = val('R1') * val('C9')
    enable_seconds = -math.log(1 - spec['nrf_enable_high_fraction']) * rc_seconds
    path_pairs = [('J4.1', 'U3.2'), ('U3.1', 'FB1.1'), ('FB1.2', 'U1.14')]
    selected_paths = []
    for start, end in path_pairs:
        matches = [p for p in paths['paths'] if p['start'] == start and p['end'] == end]
        require(len(matches) == 1 and matches[0]['connected'], 'Missing supply path')
        selected_paths.append(matches[0]['estimated_ohms_20C'])
    copper_ohms = sum(selected_paths)
    case = spec['illustrative_battery_case']
    example_vdd = case['loaded_connector_V'] - case['load_A'] * copper_ohms
    cap_refs = [ref for ref in parts if ref.startswith('C') and
                pin_net.get(ref + '.1') == '/VIO_1V8' and
                pin_net.get(ref + '.2') == '/GND']
    sources = [BOARD, SCH, TRIAL / 'evidence/route-geometry.json',
               TRIAL / 'evidence/power-path-review.json',
               OUT / 'native-power.json', OUT / 'review-inputs.json', Path(__file__)]
    return {
        'status': 'HOLD', 'powered_or_transient_test': False,
        'scope': 'Frozen r04i topology, source checks and illustrative calculations; no circuit repair.',
        'inputs': {str(p.relative_to(ROOT)): sha(p) for p in sources},
        'power_pins_compared_to_board': len(observed),
        'findings': [
            {'id': 'PWR-01', 'status': 'OPEN',
             'finding': 'No independent modem undervoltage control or guaranteed 3.0 V margin.',
             'battery_cutoff_typical_V': spec['bq_battery_uvlo_typ_V'],
             'estimated_supply_copper_ohms_20C': copper_ohms,
             'illustrative_J4_V': case['loaded_connector_V'],
             'illustrative_U3_BAT_V': case['loaded_connector_V'] - case['load_A'] * selected_paths[0],
             'illustrative_load_A': case['load_A'],
             'illustrative_nrf_V_without_component_losses': example_vdd,
             'limit': 'Not a measured failure. Nominal BUVLO and assumed copper are not guaranteed limits; IC, ferrite, contacts, cell and transients are excluded.'},
            {'id': 'PWR-02', 'status': 'OPEN',
             'finding': 'VIO LDO enable is tied to VSYS; there is no controlled GPIO supply sequence.',
             'nrf_enable_rc_nominal_ms': rc_seconds * 1000,
             'ideal_step_to_guaranteed_enable_high_ms': enable_seconds * 1000,
             'ldo_90_percent_typical_ms_at_datasheet_test_load': spec['ldo_startup_typical_ms'],
             'ldo_90_percent_maximum_ms_at_datasheet_test_load': spec['ldo_startup_maximum_ms'],
             'gpio_delay_recommendation_ms': spec['gpio_delay_recommendation_ms'],
             'vio_nominal_capacitors': cap_refs,
             'vio_nominal_capacitance_uF': sum(val(r) for r in cap_refs) * 1e6,
             'limit': 'Ideal RC and separate datasheet load conditions do not simulate this board. Nordic permits undefined GPIO states only when the application tolerates them; that review is not complete.'},
            {'id': 'PWR-03', 'status': 'OPEN',
             'finding': 'The battery ADC divider remains connected when the GPIO supply is absent.',
             'nominal_cell_V': spec['nominal_full_cell_V'],
             'unclamped_adc_V': spec['nominal_full_cell_V'] * val('R11') / (val('R10') + val('R11')),
             'upper_bound_from_top_resistor_uA': spec['nominal_full_cell_V'] / val('R10') * 1e6,
             'limit': 'A backfeed path requiring review, not a demonstrated damage or measured leakage claim. Actual clamp voltage and rail state are unknown.'},
        ],
        'charger_nominal_setting': {
            'battery_regulation_V': 4.2, 'input_limit_setting_mA': 500,
            'charge_current_mA': spec['bq_iset_factor_A_ohm'] / val('R7') * 1000,
            'limit': 'Nominal resistor settings only; not pack, NTC, thermal or input-protection acceptance.'},
    }


def verify_saved():
    actual = review()
    require(actual == read(OUT / 'power-review.json'), 'Saved power review is stale')
    return {'evidence': 'PASS', 'electrical_acceptance': actual['status'],
            'open_findings': len(actual['findings'])}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--refresh', action='store_true')
    parser.add_argument('--write', action='store_true')
    args = parser.parse_args()
    if args.refresh:
        refresh()
    if args.write:
        save(OUT / 'power-review.json', review())
    result = verify_saved()
    print(json.dumps(result, indent=2))
    return 2 if result['electrical_acceptance'] == 'HOLD' else 0


if __name__ == '__main__':
    raise SystemExit(main())
