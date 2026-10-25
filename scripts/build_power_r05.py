#!/usr/bin/env python3
"""Build a separate r05 power schematic from the frozen, exported r04i circuit.

No PCB or Gerber is created or relabelled. Existing symbol pin geometry and all
unrelated nets are retained. New land patterns remain subject to drawing review.
"""
import argparse
import copy
import csv
import hashlib
import json
from pathlib import Path
import re
import shutil

import build_draft as sch

ROOT = Path(__file__).resolve().parents[1]
BASE = ROOT / 'experiments/paul-nanosim-r04i-sim-access-40x32/hardware'


class Quoted(str):
    pass


def parse(text):
    tokens = re.findall(r'"(?:\\.|[^"\\])*"|[()]|[^\s()]+', text)
    stack, root = [], None
    for token in tokens:
        if token == '(':
            node = []
            if stack:
                stack[-1].append(node)
            else:
                if root is not None:
                    raise ValueError('Multiple roots')
                root = node
            stack.append(node)
        elif token == ')':
            if not stack:
                raise ValueError('Unmatched closing parenthesis')
            stack.pop()
        else:
            if not stack:
                raise ValueError('Token outside root')
            stack[-1].append(Quoted(json.loads(token)) if token.startswith('"') else token)
    if stack or root is None:
        raise ValueError('Incomplete expression')
    return root


def emit(node):
    if isinstance(node, list):
        return '(' + ' '.join(emit(v) for v in node) + ')'
    return json.dumps(str(node), ensure_ascii=False) if isinstance(node, Quoted) else str(node)


def child(node, name):
    return next((v for v in node if isinstance(v, list) and v and v[0] == name), None)


def descend(node, name):
    for value in node:
        if isinstance(value, list):
            if value and value[0] == name:
                yield value
            yield from descend(value, name)


def gauge_footprint():
    """ADI 90-0065 Rev E: 0.70 x 0.30 lands, 1.98 row spacing, 0.50 pitch.

    MAX17048 Rev 7 explicitly refers to this land pattern for T822+3.
    Outline 21-0168 Rev M confirms its exposed-pad dimensions match T822+3C.
    Paste and mask are process proposals; copper follows the drawing unchanged.
    """
    name = 'MAX17048_T822_3_90_0065E'
    rows = [f'(footprint "{name}" (version 20240108) (generator "collar_power_r05")',
            '(layer "F.Cu") (attr smd)',
            '(descr "MAX17048 T822+3; ADI 90-0065 Rev E copper; see power review")',
            '(property "Reference" "REF**" (at 0 -1.9) (layer "F.SilkS") (effects (font (size 0.8 0.8) (thickness 0.15))))',
            '(property "Value" "MAX17048" (at 0 1.9) (layer "F.Fab") (effects (font (size 0.8 0.8) (thickness 0.1))))',
            '(fp_rect (start -1 -1) (end 1 1) (stroke (width 0.1) (type default)) (fill none) (layer "F.Fab"))',
            '(fp_rect (start -1.6 -1.3) (end 1.6 1.3) (stroke (width 0.05) (type default)) (fill none) (layer "F.CrtYd"))',
            '(fp_line (start -1 -1) (end -0.65 -0.65) (stroke (width 0.1) (type default)) (layer "F.Fab"))',
            '(fp_circle (center -1.6 -1.1) (end -1.5 -1.1) (stroke (width 0.15) (type default)) (fill none) (layer "F.SilkS"))']
    for pin in range(1, 9):
        x = -0.99 if pin <= 4 else 0.99
        y = (pin - 1) * 0.5 - 0.75 if pin <= 4 else (8 - pin) * 0.5 - 0.75
        rows.append(f'(pad "{pin}" smd rect (at {x} {y}) (size 0.70 0.30) '
                    '(layers "F.Cu" "F.Paste" "F.Mask") (solder_mask_margin 0.02))')
    rows.append('(pad "9" smd rect (at 0 0) (size 0.80 1.38) '
                '(layers "F.Cu" "F.Mask") (solder_mask_margin 0.02))')
    # Two paste apertures, 70.7% of the EP copper area; assembler must qualify stencil.
    for y in [-0.345, 0.345]:
        rows.append(f'(pad "" smd rect (at 0 {y}) (size 0.65 0.60) (layers "F.Paste"))')
    return name, '\n'.join(rows) + '\n)\n'


def load_original():
    source = BASE / 'collar-tracker.kicad_sch'
    inventory = json.loads((ROOT / 'evidence/power-review-r04i/native-power.json').read_text())
    assert hashlib.sha256(source.read_bytes()).hexdigest() == inventory['schematic_sha256']
    native = parse(source.read_text())
    original_parts = {p['ref']: p for p in json.loads((BASE / 'design.json').read_text())['parts']}
    pin_net = {pin: name.removeprefix('/') for name, pins in inventory['nets'].items()
               if not name.startswith('unconnected-') for pin in pins}
    symbols = {}
    for symbol in child(native, 'lib_symbols')[1:]:
        name = str(symbol[1]).removeprefix('Collar:')
        rect = next(descend(symbol, 'rectangle'), None)
        if rect:
            a, b = child(rect, 'start'), child(rect, 'end')
            width, height = abs(float(a[1]) - float(b[1])), abs(float(a[2]) - float(b[2]))
        else:
            width = height = 2.54
        pins = []
        for pin in descend(symbol, 'pin'):
            at = child(pin, 'at')
            number = str(child(pin, 'number')[1])
            x, y, angle = float(at[1]), float(at[2]), int(at[3])
            side = 'none' if pin[1] == 'no_connect' and x == y == 0 else {
                0: 'left', 180: 'right', 90: 'bottom'}[angle]
            pins.append({'number': number, 'name': str(child(pin, 'name')[1]),
                         'type': str(pin[1]), 'x': x, 'y': y, 'angle': angle,
                         'side': side, 'hidden': child(pin, 'hide') is not None})
        symbols[name] = {'text': emit(symbol), 'width': width, 'height': height, 'pins': pins}
    parts = []
    for inst in native[1:]:
        if not isinstance(inst, list) or inst[0] != 'symbol' or child(inst, 'lib_id') is None:
            continue
        properties = {str(p[1]): str(p[2]) for p in inst if isinstance(p, list) and p[0] == 'property'}
        ref = properties['Reference']
        old = original_parts[ref]
        name = str(child(inst, 'lib_id')[1]).removeprefix('Collar:')
        at = child(inst, 'at')
        assert float(at[3]) == 0, 'Rotated schematic instance requires explicit support'
        nets = old['nets'] if ref.startswith('#') else {
            p['number']: pin_net[ref + '.' + p['number']]
            for p in symbols[name]['pins'] if ref + '.' + p['number'] in pin_net}
        parts.append({'ref': ref, 'symbol': name, 'value': properties['Value'],
                      'x': float(at[1]), 'y': float(at[2]), 'nets': nets,
                      'footprint': properties.get('Footprint', ''), 'mpn': properties.get('MPN', ''),
                      'status': properties.get('Design status', old['status']),
                      'dnp': child(inst, 'dnp')[1] == 'yes',
                      'onboard': child(inst, 'on_board')[1] == 'yes'})
    assert len([p for p in parts if not p['ref'].startswith('#')]) == 55
    return parts, symbols, inventory['schematic_sha256'], str(child(native, 'uuid')[1])


def build(name):
    assert re.fullmatch(r'[a-zA-Z0-9_-]+', name), 'Use a plain trial name'
    out = ROOT / 'experiments' / name
    assert not out.exists(), 'Preserve existing work; use a new trial name'
    parts, symbols, original_sha, root_uuid = load_original()
    sch.parts, sch.symbols, sch.graphics = copy.deepcopy(parts), copy.deepcopy(symbols), []
    sch.ROOT_UUID = root_uuid
    sch.counter = 0
    sch.parts = [p for p in sch.parts if p['ref'] not in {'R10', 'R11', 'C22'}]
    by_ref = {p['ref']: p for p in sch.parts}
    by_ref['R1'].update(value='22k /1%', mpn='', status='Power sequencing resistor; exact AVL pending')
    by_ref['R1']['nets']['1'] = 'POWER_GOOD'
    by_ref['C9'].update(value='1uF /16V X7R', mpn='GRM21BR71C105KA01L',
                       footprint='Capacitor_SMD:C_0805_2012Metric',
                       status='Candidate; effective C 0.60 to 1.265 uF must be qualified')
    by_ref['U4']['nets']['3'] = 'VIO_ENABLE'
    by_ref['U4']['status'] = 'GPIO supply enabled by U7; Q1 forces enable low on a power fault'
    by_ref['U1']['nets']['73'] = 'FG_ALERT'
    sch.chip('TPS3808-DBV', [(6, 'VDD', 'power_in'), (5, 'SENSE', 'input'), (3, 'MR_N', 'input')],
             [(1, 'RESET_N', 'open_collector'), (4, 'CT', 'passive')], 24, [2],
             source='https://www.ti.com/lit/ds/symlink/tps3808.pdf')
    sch.chip('SN74LVC1G14-DCK', [(5, 'VCC', 'power_in'), (2, 'A', 'input')],
             [(4, 'Y', 'output'), (1, 'NC', 'no_connect')], 24, [3],
             source='https://www.ti.com/lit/ds/symlink/sn74lvc1g14.pdf')
    # The top-view circuit gives each source/gate pair the opposite drain.
    # Both sources and both gates share nets; transistor suffixes are arbitrary.
    sch.chip('DMN62D2UDW', [(1, 'S1', 'passive'), (2, 'G1', 'input'), (4, 'S2', 'passive'),
                          (5, 'G2', 'input')], [(6, 'D1', 'passive'), (3, 'D2', 'passive')], 24,
             source='https://www.diodes.com/datasheet/download/DMN62D2UDW.pdf')
    sch.chip('MAX17048-TDFN', [(3, 'VDD', 'power_in'), (2, 'CELL_NC_CONNECT_BAT', 'passive'),
                             (7, 'SCL', 'input'), (6, 'QSTRT', 'input')],
             [(8, 'SDA', 'bidirectional'), (5, 'ALRT_N', 'open_collector')], 24, [1, 4, 9],
             source='https://www.analog.com/media/en/technical-documentation/data-sheets/MAX17048-MAX17049.pdf')
    status = 'Power schematic candidate; footprint drawing and physical validation pending'
    sch.add('U6', 'TPS3808-DBV', 'TPS3808G01DBVR', 105, 444,
            {6: 'VDD_NRF', 5: 'UV_SENSE', 3: 'VDD_NRF', 1: 'POWER_GOOD', 4: 'UV_DELAY', 2: 'GND'},
            'Package_TO_SOT_SMD:SOT-23-6', mpn='TPS3808G01DBVR', status=status)
    sch.add('U7', 'TPS3808-DBV', 'TPS3808G30DBVR', 300, 444,
            {6: 'VDD_NRF', 5: 'NRF_ENABLE', 3: 'POWER_GOOD', 1: 'VIO_ENABLE', 4: 'VIO_DELAY', 2: 'GND'},
            'Package_TO_SOT_SMD:SOT-23-6', mpn='TPS3808G30DBVR', status=status)
    sch.add('U8', 'SN74LVC1G14-DCK', 'SN74LVC1G14DCKR', 495, 444,
            {5: 'VDD_NRF', 2: 'POWER_GOOD', 4: 'POWER_FAULT', 3: 'GND'},
            'Package_TO_SOT_SMD:SOT-353_SC-70-5', mpn='SN74LVC1G14DCKR', status=status)
    sch.add('Q1', 'DMN62D2UDW', 'DMN62D2UDW-7', 495, 510,
            {1: 'GND', 2: 'POWER_FAULT', 6: 'VIO_DISCHARGE',
             4: 'GND', 5: 'POWER_FAULT', 3: 'VIO_ENABLE'},
            'Package_TO_SOT_SMD:SOT-363_SC-70-6', mpn='DMN62D2UDW-7', status=status)
    # Land and package drawings were inspected; assembly stencil is still unqualified.
    sch.add('U9', 'MAX17048-TDFN', 'MAX17048G+T10', 690, 444,
            {3: 'VBAT', 2: 'VBAT', 7: 'I2C_SCL', 8: 'I2C_SDA', 6: 'GND',
             1: 'GND', 4: 'GND', 9: 'GND', 5: 'FG_ALERT'},
            'Collar05:MAX17048_T822_3_90_0065E', mpn='MAX17048G+T10', status=status)
    resistor_specs = [
        ('R16', '10k /1%', 45, 480, 'VDD_NRF', 'POWER_GOOD'),
        ('R17', '1M /0.1%', 45, 500, 'VDD_NRF', 'UV_SENSE'),
        ('R18', '130k /0.1%', 145, 500, 'UV_SENSE', 'GND'),
        ('R19', '16.9M /1%', 145, 480, 'POWER_GOOD', 'UV_SENSE'),
        ('R20', '10k /1%', 300, 480, 'VDD_NRF', 'VIO_ENABLE'),
        ('R21', '22R /1%', 495, 552, 'VIO_1V8', 'VIO_DISCHARGE'),
        ('R22', '1M /1%', 590, 510, 'POWER_FAULT', 'GND'),
        ('R23', '100k /1%', 690, 500, 'VIO_1V8', 'FG_ALERT'),
    ]
    for ref, value, x, y, a, b in resistor_specs:
        sch.r(ref, value, x, y, a, b, status='Candidate; specified tolerance and exact AVL required')
    capacitors = [
        ('C25', '680nF /25V X7R', 95, 533, 'UV_DELAY', 'GRM219R71E684KA88D', 'Capacitor_SMD:C_0805_2012Metric'),
        ('C26', '47nF /16V X7R', 300, 500, 'VIO_DELAY', '', 'Capacitor_SMD:C_0402_1005Metric'),
        ('C27', '100nF /16V X7R', 195, 444, 'VDD_NRF', '', 'Capacitor_SMD:C_0402_1005Metric'),
        ('C28', '100nF /16V X7R', 395, 444, 'VDD_NRF', '', 'Capacitor_SMD:C_0402_1005Metric'),
        ('C29', '100nF /16V X7R', 590, 444, 'VDD_NRF', '', 'Capacitor_SMD:C_0402_1005Metric'),
        ('C30', '100nF /16V X7R', 780, 444, 'VBAT', '', 'Capacitor_SMD:C_0402_1005Metric'),
    ]
    for ref, value, x, y, rail, mpn, footprint in capacitors:
        sch.add(ref, 'C', value, x, y, {1: rail, 2: 'GND'}, footprint, mpn=mpn,
                status='Candidate; effective capacitance and exact AVL require review')
    sch.add('#FLG04', 'PWR_FLAG', 'PWR_FLAG', 780, 480, {1: 'VBAT'}, onboard=False)
    sch.text('r05 POWER SCHEMATIC CANDIDATE — NO SUCCESSOR PCB OR DFM RESULT', 25, 15, 2.0)
    sch.text('Existing RF, SIM and digital circuits retain r04i net membership.\n'
             'R10/R11/C22 removed; U1.73 is now FG_ALERT.\n'
             'C9 grows to 0805. New parts need placement and drawing review.', 610, 60, 1.35)
    sch.text('Power control: U6 supervises the modem rail; R19 adds hysteresis.\n'
             'U7 delays the 1.8 V rail after NRF_ENABLE rises.\n'
             'U8/Q1 disable U4 and discharge VIO on POWER_GOOD low.\n'
             'U9 reads the protected cell over the switched-domain I2C bus.', 610, 110, 1.35)
    sch.text('HOLD: validate threshold/timing corners, effective capacitance,\n'
             'brief faults, supply collapse, low-cell charging recovery and\n'
             'off-state interfaces. No powered validation or order approval.', 610, 165, 1.35)
    sch.text('Protected pack/NTC and actual LTE/GNSS antennas remain unselected.\n'
             'Firmware must wait for VIO, recover I2C and configure the fuel gauge.\n'
             'Do not quick-start the gauge on every processor reset.', 610, 220, 1.35)
    hw = out / 'hardware'
    hw.mkdir(parents=True)
    for name in ['evidence', 'previews']:
        (out / name).mkdir()
    for path in BASE.iterdir():
        if path.is_dir() and path.suffix == '.pretty':
            shutil.copytree(path, hw / path.name)
        elif path.name in ['collar-tracker.kicad_pro', 'collar-tracker.kicad_dru',
                           'fp-lib-table', 'NORDIC_LIBRARY_LICENSE.txt', 'NORDIC_LIBRARY_NOTICE.txt']:
            shutil.copy2(path, hw / path.name)
    (hw / 'Collar05.pretty').mkdir()
    fp_name, fp_text = gauge_footprint()
    (hw / 'Collar05.pretty' / (fp_name + '.kicad_mod')).write_text(fp_text)
    library = '\n'.join(s['text'] for s in sch.symbols.values())
    body = '\n'.join(sch.instance(p) for p in sch.parts)
    content = f'''(kicad_sch (version 20250114) (generator "collar_power_r05")
 (uuid {root_uuid}) (paper "A1")
 (title_block (title "Collar tracker — r05 power schematic candidate")
 (date "2026-10-25") (rev "0.5-power-WIP")
 (comment 1 "Not routed or released; power, RF, assembly and physical qualification remain open"))
 (lib_symbols {library})
 {body}
 {''.join(sch.graphics)}
 (sheet_instances (path "/" (page "1"))))
'''
    (hw / 'collar-tracker.kicad_sch').write_text(content)
    (hw / 'Collar.kicad_sym').write_text(
        '(kicad_symbol_lib (version 20250114) (generator "collar_power_r05")\n' +
        '\n'.join(s['text'].replace('(symbol "Collar:', '(symbol "', 1)
                  for s in sch.symbols.values()) + '\n)\n')
    (hw / 'sym-lib-table').write_text(
        '(sym_lib_table (version 7) (lib (name "Collar") (type "KiCad") '
        '(uri "${KIPRJMOD}/Collar.kicad_sym") (options "") (descr "Project symbols")))\n')
    table = (hw / 'fp-lib-table').read_text()
    table = table.rstrip()[:-1] + '\n(lib (name "Collar05") (type "KiCad") (uri "${KIPRJMOD}/Collar05.pretty") (options "") (descr "r05 reviewed land geometry; assembly qualification pending")))\n'
    for name in ['Resistor_SMD', 'Capacitor_SMD', 'Package_TO_SOT_SMD']:
        if f'(name "{name}")' not in table:
            table = table.rstrip()[:-1] + f'\n(lib (name "{name}") (type "KiCad") (uri "${{KICAD10_FOOTPRINT_DIR}}/{name}.pretty") (options "") (descr "KiCad library; drawing review required")))\n'
    (hw / 'fp-lib-table').write_text(table)
    (hw / 'design.json').write_text(json.dumps({'root_uuid': root_uuid, 'parts': sch.parts}, indent=2) + '\n')
    with (hw / 'bom.csv').open('w') as handle:
        fields = ['ref', 'value', 'mpn', 'footprint', 'dnp', 'onboard', 'status']
        writer = csv.DictWriter(handle, fieldnames=fields, lineterminator='\n')
        writer.writeheader()
        writer.writerows({key: p[key] for key in fields} for p in sch.parts if not p['ref'].startswith('#'))
    (out / 'evidence/build.json').write_text(json.dumps({
        'baseline_schematic_sha256': original_sha,
        'schematic_sha256': hashlib.sha256(content.encode()).hexdigest(),
        'builder_sha256': hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
        'component_count': len([p for p in sch.parts if not p['ref'].startswith('#')]),
        'pcb_created': False, 'electrical_release': False,
        'removed_components': ['R10', 'R11', 'C22'],
        'changed_existing_connections': {'R1.1': 'POWER_GOOD', 'U4.3': 'VIO_ENABLE', 'U1.73': 'FG_ALERT'},
    }, indent=2) + '\n')
    print(out)


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--name', default='power-r05-supervised')
    build(parser.parse_args().name)
