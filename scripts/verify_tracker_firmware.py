#!/usr/bin/env python3
"""Check saved tracker build/test evidence. Does not compile, flash or contact a service."""
import hashlib
import json
from pathlib import Path

from check_firmware_board import check

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT/'firmware/evidence/tracker-r01'


def require(value, message):
    if not value:
        raise ValueError(message)


def verify():
    data = json.loads((OUT/'build-evidence.json').read_text())
    for name, digest in data['inputs'].items():
        path = (ROOT/name).resolve()
        require(path.is_relative_to(ROOT), 'Tracker input escapes checkout')
        require(hashlib.sha256(path.read_bytes()).hexdigest() == digest,
                'Tracker evidence input changed: '+name)
    require(data['native_board_check'] == check(), 'Changed native tracker pin contract')
    require(data['result'] == 'BUILD_PASS' and data['compiler_exit'] == 0, 'Tracker build failed')
    require(data['board'] == 'collar_tracker_r05l/nrf9151/ns', 'Unexpected tracker target')
    for name, saved in [('zephyr/.config', 'compiled.config'), ('zephyr/zephyr.dts', 'compiled.dts')]:
        require(hashlib.sha256((OUT/saved).read_bytes()).hexdigest() == data['artifacts'][name]['sha256'],
                'Changed compiled tracker configuration')
    inspection = data['image_inspection']
    require(inspection['result'] == 'PASS' and inspection['programmed_storage_bytes'] == 0,
            'Invalid linked-image inspection')
    require(inspection['reset_vectors']['secure']['address'] == 0 and
            inspection['reset_vectors']['application']['address'] == 0x40000,
            'Unexpected reset-vector layout')
    require(inspection['storage'] == dict(address=0xf8000, bytes=32768, sectors=8),
            'Unexpected persistent-storage map')
    tests = json.loads((OUT/'tests.json').read_text())
    require(tests['result'] == 'PASS' and all(s['exit'] == 0 for s in tests['suites']),
            'Tracker regressions failed')
    require(tests['receiver_tests'] == 7 and tests['c_crash_boundaries'] == 6 and
            tests['corrupted_record_bytes'] == 40, 'Incomplete tracker host coverage')
    require('Ran 7 tests' in (OUT/'receiver-tests.txt').read_text() and
            '\nOK\n' in (OUT/'receiver-tests.txt').read_text(), 'Missing receiver test result')
    require(data['flashed'] is False and data['physical_test'] is False and
            data['manufacturing_release'] is False and inspection['signed_boot'] is False and
            inspection['ota'] is False, 'Unexpected tracker acceptance claim')
    controls = json.loads((OUT/'image-controls.json').read_text())
    require(controls['result'] == 'PASS' and len(controls['rejected_mutations']) == 2,
            'Missing linked-image negative controls')
    return dict(result='PASS', scope='Saved build and host tests; not an actual modem test',
                board=data['board'], memory_usage_bytes=data['memory_usage_bytes'],
                queue_capacity=64, receiver_tests=7, crash_boundaries=6,
                corrupted_record_bytes=40, linked_image_controls=2,
                merged_sha256=inspection['merged_sha256'], radio_enabled=True,
                flashed=False, physical_test=False, manufacturing_release=False)


if __name__ == '__main__':
    print(json.dumps(verify(), indent=2))
