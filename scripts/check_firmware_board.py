#!/usr/bin/env python3
"""Bind the factory firmware's signal contract to the native r05l schematic."""
import hashlib
import json
from pathlib import Path

from build_power_r05 import child, descend, parse

ROOT = Path(__file__).resolve().parents[1]
BASE = ROOT / 'experiments/power-r05l-charge-interlock'
EXPECTED = {
    '/I2C_SDA': ('56', 'P0.00'),
    '/I2C_SCL': ('57', 'P0.01'),
    '/ACC_INT': ('58', 'P0.02'),
    '/HEALTH_EN': ('68', 'P0.09'),
    '/CHG_STAT': ('69', 'P0.10'),
    '/CHG_FAULT': ('70', 'P0.11'),
    '/FG_ALERT': ('73', 'P0.13'),
}


def check():
    schematic = BASE / 'hardware/collar-tracker.kicad_sch'
    netlist = BASE / 'evidence/native-netlist.json'
    exported = json.loads(netlist.read_text())
    digest = hashlib.sha256(schematic.read_bytes()).hexdigest()
    if digest != exported['schematic_sha256']:
        raise ValueError('Native netlist does not match the current schematic')
    lib = child(parse(schematic.read_text()), 'lib_symbols')
    symbol = next(s for s in lib[1:] if s[1] == 'Collar:nRF9151-LACA')
    pins = {child(p, 'number')[1]: child(p, 'name')[1] for p in descend(symbol, 'pin')}
    for net, (number, gpio) in EXPECTED.items():
        if pins[number] != gpio or 'U1.' + number not in exported['nets'][net]:
            raise ValueError('Firmware/native signal mismatch: ' + net)
    vio = exported['nets']['/VIO_1V8']
    if not {'U5.2', 'U5.3'}.issubset(vio):
        raise ValueError('LIS2DW12 I2C mode/address straps changed')
    if exported['mpns']['U5'] != 'LIS2DW12TR' or exported['mpns']['U9'] != 'MAX17048G+T10':
        raise ValueError('Sensor/gauge selection changed')
    return dict(result='PASS', schematic_sha256=digest,
                netlist_sha256=hashlib.sha256(netlist.read_bytes()).hexdigest(),
                signals={net: dict(package_pin=n, gpio=g) for net, (n, g) in EXPECTED.items()},
                accelerometer_i2c_address='0x19', fuel_gauge_i2c_address='0x36',
                physical_test=False)


if __name__ == '__main__':
    print(json.dumps(check(), indent=2))
