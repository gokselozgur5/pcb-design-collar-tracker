#!/usr/bin/env python3
"""Check the KiCad-exported netlist, independently of generator connectivity.

These checks catch symbol/export/wiring mistakes. They do not validate the RF,
power transients, battery, mechanical design, or heart-rate measurement.
"""
from pathlib import Path
import hashlib
import json
import re
import xml.etree.ElementTree as ET

ROOT = Path(__file__).resolve().parents[1]
tree = ET.parse(ROOT / 'evidence/collar-tracker.xml').getroot()
components = {c.attrib['ref']: c for c in tree.findall('./components/comp')}
nets = {}
pin_net = {}
for net in tree.findall('./nets/net'):
    name = net.attrib['name'].lstrip('/')
    nodes = {(n.attrib['ref'], n.attrib['pin']) for n in net.findall('node')}
    nets[name] = nodes
    for node in nodes:
        assert node not in pin_net, f'Pin on multiple nets: {node}'
        pin_net[node] = name

checks = []

def check(description, condition):
    assert condition, description
    checks.append(description)

def linked(ref, pin, net):
    return pin_net[(ref, str(pin))] == net

def value(ref):
    return components[ref].findtext('value')

grounds = {1, 7, 13, 15, 20, 25, 30, 34, 36, 38, 39, 40, 41, 43,
           46, 51, 55, 60, 66, 71, 76, *range(105, 114)}
reserved = {31, 32, 33, *range(81, 105)}
check('All 113 nRF9151 pins appear exactly once in exported nets',
      {p for r, p in pin_net if r == 'U1'} == {str(n) for n in range(1, 114)})
check('All 30 nRF9151 ground pins connect to GND',
      all(linked('U1', p, 'GND') for p in grounds))
check('All 27 reserved pins are individually isolated',
      all(nets[pin_net[('U1', str(p))]] == {('U1', str(p))} for p in reserved))
check('SIM_DET is isolated', nets[pin_net[('U1', '26')]] == {('U1', '26')})
check('SIM supply is separate from GPIO power and only feeds its cap/interface',
      nets['SIM_1V8'] == {('U1', '19'), ('C10', '1'), ('J6', '1')}
      and linked('U1', 65, 'VIO_1V8') and linked('U4', 5, 'VIO_1V8'))
check('SIM reset/data/clock map to the intended logical interface',
      nets['SIM_RST'] == {('U1', '16'), ('J6', '2')}
      and nets['SIM_IO'] == {('U1', '17'), ('J6', '4')}
      and nets['SIM_CLK'] == {('U1', '18'), ('J6', '3')})
check('DEC0 feeds only its 4.7uF bypass capacitor',
      nets['DEC0'] == {('U1', '24'), ('C7', '1')}
      and value('C7') == '4.7uF' and linked('C7', 2, 'GND'))
check('nRESET has a capacitor and series resistor, no external pull-up',
      nets['NRF_RESET'] == {('U1', '9'), ('C8', '1'), ('R2', '1')}
      and nets['DEBUG_RESET'] == {('R2', '2'), ('J7', '5')}
      and value('R2') == '1k' and linked('C8', 2, 'GND'))
check('LTE and GNSS RF ports remain separate',
      linked('U1', 35, 'LTE_RF') and linked('U1', 42, 'GPS_RF')
      and linked('C13', 2, 'GPS_RF') and linked('R3', 1, 'LTE_RF'))
check('GNSS filter/LNA bridge is 9.1nH between pins 7 and 8',
      nets['FILT_OUT'] == {('U2', '7'), ('L1', '1')}
      and nets['AMP_IN'] == {('U2', '8'), ('L1', '2')}
      and value('L1') == '9.1nH')
check('GNSS VCC and enable driver share the 1.8V logic domain',
      linked('U2', 3, 'VIO_1V8') and linked('U2', 2, 'GNSS_LNA_EN')
      and nets['COEX0'] == {('U1', '52'), ('R4', '1')}
      and linked('R5', 2, 'GND'))
check('Charger main pins map to input, SYS, battery and actual NTC interface',
      all(linked('U3', p, n) for p, n in
          {10:'VIN_5V', 1:'VSYS', 2:'VBAT', 5:'GND', 11:'GND', 6:'BAT_NTC'}.items())
      and nets['BAT_NTC'] == {('U3', '6'), ('J4', '3')})
check('Provisional charger settings are 18k VSET and 3k ISET',
      nets['ILIM_VSET'] == {('U3', '7'), ('R6', '1')}
      and nets['ISET'] == {('U3', '8'), ('R7', '1')}
      and value('R6') == '18k /1%' and value('R7') == '3k /1%'
      and linked('R6', 2, 'GND') and linked('R7', 2, 'GND'))
check('LIS2DW12 CS/SA0/VDD/VDDIO are high; reserved pin 7 is grounded',
      all(linked('U5', p, 'VIO_1V8') for p in (2, 3, 9, 10))
      and linked('U5', 7, 'GND'))
check('Battery ADC divider terminates at P0.13/AIN0 with a shunt capacitor',
      nets['BAT_ADC'] == {('U1', '73'), ('R10', '2'), ('R11', '1'), ('C22', '1')}
      and value('R10') == '2M' and value('R11') == '1M'
      and linked('R10', 1, 'VBAT') and linked('R11', 2, 'GND'))
check('Health interface reserves the intended 12 digital/power signals',
      all(linked('J5', p, n) for p, n in enumerate([
          'GND', 'VIO_1V8', 'VSYS', 'I2C_SDA', 'I2C_SCL', 'HEALTH_INT',
          'SPI_SCK', 'SPI_MOSI', 'SPI_MISO', 'HEALTH_CS', 'HEALTH_RESET',
          'HEALTH_EN'], start=1)))

footprint = ROOT / 'hardware/Collar.pretty/LGA_9151_12.1x11.1mm.kicad_mod'
pad_numbers = re.findall(r'\(pad\s+"(\d+)"', footprint.read_text())
check('Candidate footprint has one pad for each of the 113 nRF pins',
      len(pad_numbers) == 113 and set(pad_numbers) == {str(i) for i in range(1, 114)})

erc = json.loads((ROOT / 'evidence/erc.json').read_text())
default_ignored = {'single_global_label', 'four_way_junction',
                   'simulation_model_issue', 'footprint_filter'}
check('KiCad default ERC reports zero violations; only its four default checks are ignored',
      not any(sheet['violations'] for sheet in erc['sheets'])
      and {item['key'] for item in erc['ignored_checks']} == default_ignored)
report = {
    'status': 'passed; schematic connectivity only',
    'kicad_version': erc['kicad_version'],
    'checks_passed': checks,
    'components_in_netlist': len(components),
    'nets_including_isolated_pins': len(nets),
    'erc_default_ignored_checks': erc['ignored_checks'],
    'not_validated': [
        'PCB placement/routing: no PCB layout has been produced',
        'Candidate nRF footprint dimensions and paste against manufacturer drawing',
        'Missing component footprints and physical connectors/eSIM',
        'Hardware undervoltage cutoff and power sequencing',
        'Battery safety/NTC, RF impedance/matching and real current consumption',
        'Turkey operator/eSIM provisioning',
        'Heart-rate sensor, contact mechanics and measurement accuracy',
    ],
    'sha256': {str(p.relative_to(ROOT)): hashlib.sha256(p.read_bytes()).hexdigest()
               for p in [ROOT/'hardware/collar-tracker.kicad_sch',
                         ROOT/'hardware/Collar.kicad_sym', footprint,
                         ROOT/'evidence/collar-tracker.xml', ROOT/'evidence/erc.json']},
}
(ROOT / 'evidence/connectivity-checks.json').write_text(json.dumps(report, indent=2) + '\n')
print(json.dumps({'checks_passed':len(checks), 'components':len(components),
                  'erc_violations':0, 'scope':'schematic connectivity only'}))
