#!/usr/bin/env python3
"""Add a hardware charging window to an isolated copy of the tested r05k.

Preserve every existing schematic object except the U3.4 net label, title and
sheet size. New outputs are combined by a NAND, never wired together. This
one-shot source builder does not claim routing or physical qualification.
"""
import csv
import hashlib
import json
from pathlib import Path
import shutil
import uuid

import build_draft as sch
from build_power_r05 import parse, emit, child, descend, Quoted

ROOT = Path(__file__).resolve().parents[1]
SOURCE = ROOT / 'experiments/power-r05k-selected-parts'
TARGET = ROOT / 'experiments/power-r05l-charge-interlock'
BASE_PCB = 'bea6c52a7f045b5fb21ac9714f3db0c70207f150aab3e9587b891f08e4e2b4d3'
BASE_SCH = 'fcb47f41d004b507394d275c48a8d412292cb65f8ed52438a0113ba8d1647f60'
sha = lambda p: hashlib.sha256(p.read_bytes()).hexdigest()


def land(name, count):
    """TI DCK0006A/DCK0005A land examples; no land shrinking for DFM."""
    length = .9 if count == 6 else .95
    pins = {1: (-1.1, -.65), 2: (-1.1, 0), 3: (-1.1, .65),
            4: (1.1, .65), 5: (1.1, 0), 6: (1.1, -.65)}
    if count == 5:
        pins.pop(6)
        pins[5] = (1.1, -.65)
    rows = [f'(footprint "{name}" (version 20240108) (generator "collar_charge_r05l")',
            '(layer "F.Cu") (attr smd)',
            f'(descr "TI DCK000{count}A manufacturer land: {length} x 0.4 mm, 2.2 mm rows, 0.65 mm pitch")',
            '(property "Reference" "REF**" (at 0 -1.7) (layer "F.Fab") (hide yes) (effects (font (size 0.8 0.8) (thickness 0.1))))',
            f'(property "Value" "{name}" (at 0 1.7) (layer "F.Fab") (hide yes) (effects (font (size 0.8 0.8) (thickness 0.1))))',
            '(fp_rect (start -0.7 -1.1) (end 0.7 1.1) (stroke (width 0.1) (type default)) (fill none) (layer "F.Fab"))',
            '(fp_rect (start -1.85 -1.35) (end 1.85 1.35) (stroke (width 0.05) (type default)) (fill none) (layer "F.CrtYd"))',
            '(fp_line (start -0.7 -1.1) (end -0.35 -0.75) (stroke (width 0.1) (type default)) (layer "F.Fab"))']
    for pin, (x, y) in pins.items():
        rows.append(f'(pad "{pin}" smd roundrect (at {x} {y}) (size {length} 0.4) '
                    '(layers "F.Cu" "F.Paste" "F.Mask") (roundrect_rratio 0.125) '
                    '(solder_mask_margin 0.02))')
    return '\n'.join(rows) + '\n)\n'


def main():
    hw = SOURCE / 'hardware'
    assert sha(hw / 'collar-tracker.kicad_pcb') == BASE_PCB
    assert sha(hw / 'collar-tracker.kicad_sch') == BASE_SCH
    assert not TARGET.exists(), 'Preserve all existing revisions'
    shutil.copytree(hw, TARGET / 'hardware', ignore=shutil.ignore_patterns('*.kicad_prl', '*.lck'))
    for folder in ['evidence', 'assembly', 'build']:
        (TARGET / folder).mkdir()
    hw = TARGET / 'hardware'
    design = json.loads((hw / 'design.json').read_text())
    root = parse((hw / 'collar-tracker.kicad_sch').read_text())
    by_ref = {p['ref']: p for p in design['parts']}
    assert by_ref['U3']['nets']['4'] == 'GND'
    symbol = next(s for s in child(root, 'lib_symbols')[1:] if s[1] == 'Collar:BQ25185')
    pin = next(p for p in descend(symbol, 'pin') if child(p, 'number')[1] == '4')
    x, y = by_ref['U3']['x'] + float(child(pin, 'at')[1]), by_ref['U3']['y'] - float(child(pin, 'at')[2])
    wire = next(w for w in root if isinstance(w, list) and w[0] == 'wire'
                and [float(v) for v in child(w, 'pts')[1][1:]] == [x, y])
    end = [float(v) for v in child(wire, 'pts')[2][1:]]
    label = next(v for v in root if isinstance(v, list) and v[0] == 'label'
                 and [float(i) for i in child(v, 'at')[1:3]] == end)
    assert label[1] == 'GND'
    label[1] = Quoted('CHARGE_DISABLE')
    by_ref['U3']['nets']['4'] = 'CHARGE_DISABLE'

    # Isolate new drawing UUIDs from all preserved instances and wires.
    sch.NS = uuid.UUID('0b2da1cb-4271-4fad-82c9-deb634c50f62')
    sch.ROOT_UUID = design['root_uuid']
    sch.counter, sch.parts, sch.graphics = 0, [], []
    sch.chip('TLV3012B-DCK', [(6, 'V+', 'power_in'), (3, 'IN+', 'input'), (4, 'IN-', 'input')],
             [(1, 'OUT', 'output'), (5, 'REF_1V242', 'output')], 25, [2],
             source='https://www.ti.com/lit/ds/symlink/tlv3012b.pdf')
    sch.chip('SN74LVC1G00-DCK', [(5, 'VCC', 'power_in'), (1, 'A_HOT_OK', 'input'), (2, 'B_COLD_OK', 'input')],
             [(4, 'Y_DISABLE', 'output')], 25, [3],
             source='https://www.ti.com/lit/ds/symlink/sn74lvc1g00.pdf')
    sch.add('U10', 'TLV3012B-DCK', 'TLV3012BIDCKR / HOT', 105, 620,
            {1:'CHG_HOT_OK', 2:'GND', 3:'BAT_NTC', 4:'CHG_HOT_LIMIT', 5:'CHG_HOT_REF', 6:'VSYS'},
            'Collar05L:TI_DCK0006A', 'TLV3012BIDCKR')
    sch.add('U11', 'TLV3012B-DCK', 'TLV3012BIDCKR / COLD', 305, 620,
            {1:'CHG_COLD_OK', 2:'GND', 3:'CHG_COLD_LIMIT', 4:'BAT_NTC', 5:'CHG_COLD_REF', 6:'VSYS'},
            'Collar05L:TI_DCK0006A', 'TLV3012BIDCKR')
    sch.add('U12', 'SN74LVC1G00-DCK', 'SN74LVC1G00DCKR', 505, 620,
            {1:'CHG_HOT_OK', 2:'CHG_COLD_OK', 3:'GND', 4:'CHARGE_DISABLE', 5:'VSYS'},
            'Collar05L:TI_DCK0005A', 'SN74LVC1G00DCKR')
    resistor = by_ref['R16']['footprint']
    capacitor = by_ref['C30']['footprint']
    rows = [
        ('R24','196k /0.1%','RT0402BRD07196KL',70,662,'CHG_HOT_REF','CHG_HOT_LIMIT'),
        ('R25','49.9k /0.1%','RT0402BRD0749K9L',140,662,'CHG_HOT_LIMIT','GND'),
        ('R26','27.4k /0.1%','RT0402BRD0727K4L',270,662,'CHG_COLD_REF','CHG_COLD_LIMIT'),
        ('R27','49.9k /0.1%','RT0402BRD0749K9L',340,662,'CHG_COLD_LIMIT','GND'),
        ('R28','100k','RC0402FR-07100KL',505,662,'VSYS','CHARGE_DISABLE'),
        ('R29','100k','RC0402FR-07100KL',70,692,'CHG_HOT_OK','GND'),
        ('R30','100k','RC0402FR-07100KL',270,692,'CHG_COLD_OK','GND')]
    for ref, val, mpn, x, y, a, b in rows:
        sch.add(ref, 'R', val, x, y, {1:a, 2:b}, resistor, mpn)
    for ref, x, y, net in [('C31',140,692,'VSYS'), ('C32',340,692,'VSYS'), ('C33',505,692,'VSYS')]:
        sch.add(ref, 'C', '100nF /16V', x, y, {1:net,2:'GND'}, capacitor, 'GRM155R71C104KA88D')
    for ref, x, y, net in [('C34',70,721,'CHG_HOT_REF'), ('C35',270,721,'CHG_COLD_REF'), ('C36',505,721,'BAT_NTC')]:
        sch.add(ref, 'C', '1nF /50V C0G', x, y, {1:net,2:'GND'}, capacitor, 'GRM1555C1H102JA01D')
    for p in sch.parts:
        p['status'] = 'Hardware charge-window candidate; assembled temperature/boot/fault qualification required'
        p['uuid'] = sch.uid(p['ref'])
    for name in ['TLV3012B-DCK','SN74LVC1G00-DCK']:
        child(root,'lib_symbols').append(parse(sch.symbols[name]['text']))
    external = parse((hw/'Collar.kicad_sym').read_text())
    for name in ['TLV3012B-DCK','SN74LVC1G00-DCK']:
        item = parse(sch.symbols[name]['text'])
        item[1] = Quoted(name)
        external.append(item)
    (hw/'Collar.kicad_sym').write_text(emit(external)+'\n')
    for part in sch.parts:
        root.extend(parse('(' + sch.instance(part) + ')'))
    sch.text('09 / HARDWARE CELL-TEMPERATURE CHARGE INTERLOCK', 30, 582, 2)
    sch.text('Both comparator outputs must be HIGH to enable charging. POR outputs LOW; NAND drives /CE HIGH.\n'
             'Always-on VSYS supply: independent of MCU/VIO reset and undervoltage shutdown.\n'
             'Candidate 103JT-025 must be bonded to the cell. Open/short sensor inhibits charging.\n'
             'Conservative window; threshold tolerance and thermal-coupling validation remain required.', 615, 600, 1.2)
    root.extend(parse('(' + '\n'.join(sch.graphics) + ')'))
    child(root,'paper')[1] = Quoted('A0')
    title = child(root,'title_block')
    child(title,'title')[1] = Quoted('Collar tracker — r05l hardware charge interlock')
    child(title,'rev')[1] = Quoted('0.5l-charge-WIP')
    (hw/'collar-tracker.kicad_sch').write_text(emit(root)+'\n')
    design['parts'].extend(sch.parts)
    (hw/'design.json').write_text(json.dumps(design,indent=2)+'\n')
    with (hw/'bom.csv').open('w',newline='') as f:
        fields=['ref','value','mpn','footprint','dnp','onboard','status']
        writer=csv.DictWriter(f,fieldnames=fields,lineterminator='\n');writer.writeheader()
        writer.writerows({key:p[key] for key in fields} for p in design['parts'] if not p['ref'].startswith('#'))
    lib=hw/'Collar05L.pretty';lib.mkdir()
    for count in [5,6]:
        (lib/f'TI_DCK000{count}A.kicad_mod').write_text(land(f'TI_DCK000{count}A',count))
    table=parse((hw/'fp-lib-table').read_text())
    table.append(parse('(lib (name "Collar05L") (type "KiCad") (uri "${KIPRJMOD}/Collar05L.pretty") (options "") (descr "TI charge interlock lands"))'))
    (hw/'fp-lib-table').write_text(emit(table)+'\n')
    receipt=dict(base_pcb_sha256=BASE_PCB,base_schematic_sha256=BASE_SCH,
                 schematic_sha256=sha(hw/'collar-tracker.kicad_sch'),
                 changed_original_pins={'U3.4':{'before':'GND','after':'CHARGE_DISABLE'}},
                 new_refs=[p['ref'] for p in sch.parts],
                 scope='Schematic implementation only. PCB is still an untouched seed until the separate PCB builder runs.')
    (TARGET/'evidence/schematic-seed.json').write_text(json.dumps(receipt,indent=2)+'\n')
    print(json.dumps(receipt,indent=2))


if __name__=='__main__':
    main()
