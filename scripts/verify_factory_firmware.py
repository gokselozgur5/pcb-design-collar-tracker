#!/usr/bin/env python3
"""Verify saved firmware source/build evidence, without compiling or flashing."""
import hashlib
import json
from pathlib import Path

from check_firmware_board import check

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT/'firmware/evidence/factory-r01'


def require(condition, message):
    if not condition:
        raise ValueError(message)


def verify():
    data = json.loads((OUT/'build-evidence.json').read_text())
    for name, digest in data['inputs'].items():
        require(hashlib.sha256((ROOT/name).read_bytes()).hexdigest() == digest,
                'Firmware evidence input changed: ' + name)
    native = check()
    require(native == data['native_board_check'], 'Changed native firmware contract')
    require(data['result'] == 'BUILD_PASS', 'Firmware build failed')
    require(data['compiler_exit'] == 0 and data['compiled_contract_assertions'] == 14,
            'Incomplete build contract')
    require(all(data['deferred_initialization'].values()), 'Early external initialization')
    require(data['radio_enabled'] is False and data['flashed'] is False
            and data['physical_test'] is False and data['manufacturing_release'] is False,
            'Unexpected firmware acceptance claim')
    control = json.loads((OUT/'negative-control.json').read_text())
    require(control['result'] == 'PASS' and control['compiler_exit'] != 0
            and all(control['diagnostics'].values()), 'Invalid negative compile control')
    log = (OUT/'negative-build.txt').read_text()
    require(all(message in log for message in control['diagnostics']), 'Missing compiler diagnostics')
    return dict(result='PASS', scope='Saved build evidence, not a physical test',
                board=data['board'], native_signals=len(native['signals']),
                compiled_contract_assertions=14, negative_compile_controls=2,
                flash_bytes=data['memory_usage_bytes']['flash'], ram_bytes=data['memory_usage_bytes']['ram'],
                radio_enabled=False, flashed=False, physical_test=False, manufacturing_release=False)


if __name__ == '__main__':
    print(json.dumps(verify(), indent=2))
