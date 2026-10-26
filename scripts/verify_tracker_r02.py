#!/usr/bin/env python3
"""Read-only r02 source/build/test identity check; no device qualification claim."""
import hashlib
import json
from pathlib import Path

from check_firmware_board import check
from inspect_tracker_image import require
from inspect_tracker_r02 import RECOVERY_CONTRACT

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT/'firmware/evidence/tracker-r02'


def verify():
    data = json.loads((OUT/'build-evidence.json').read_text())
    for name, digest in data['inputs'].items():
        path = (ROOT/name).resolve()
        require(path.is_relative_to(ROOT), 'r02 evidence input escapes checkout')
        require(hashlib.sha256(path.read_bytes()).hexdigest() == digest,
                'r02 evidence input changed: '+name)
    for name, digest in data['compiled_inputs'].items():
        require(data['inputs'].get(name) == digest, 'r02 compiled input not preserved: '+name)
    require(data['native_board_check'] == check(), 'Changed r02 native pin contract')
    require(data['result'] == 'BUILD_PASS' and data['compiler_exit'] == 0, 'r02 build failed')
    require(data['board'] == 'collar_tracker_r05l/nrf9151/ns', 'Unexpected r02 target')
    for name, saved in [('zephyr/.config', 'compiled.config'), ('zephyr/zephyr.dts', 'compiled.dts')]:
        require(hashlib.sha256((OUT/saved).read_bytes()).hexdigest() == data['artifacts'][name]['sha256'],
                'Changed r02 compiled configuration')
    config = (OUT/'compiled.config').read_text().splitlines()
    require(all(line in config for line in RECOVERY_CONTRACT), 'Missing compiled r02 recovery setting')
    image = data['image_inspection']
    require(image['result'] == 'PASS' and image['programmed_storage_bytes'] == 0,
            'Invalid r02 linked-image inspection')
    require(image['reset_vectors']['secure']['address'] == 0 and
            image['reset_vectors']['application']['address'] == 0x40000 and
            image['storage'] == dict(address=0xf8000, bytes=32768, sectors=8),
            'Unexpected r02 image/storage map')
    require(image['merged_sha256'] == data['artifacts'][image['merged_hex']]['sha256'],
            'r02 inspection does not match built image')
    require(data['recovery_inspection']['watchdog_contract'] == RECOVERY_CONTRACT and
            data['recovery_inspection']['merged_sha256'] == image['merged_sha256'],
            'r02 recovery inspection missing or stale')
    tests = json.loads((OUT/'tests.json').read_text())
    expected = {'recovery', 'dns-worker', 'expired-main', 'modem-fault', 'missing-watchdog'}
    require(tests['result'] == 'PASS' and len(tests['suites']) == len(expected) and
            {s['case'] for s in tests['suites']} == expected and
            all(s['exit'] == 0 for s in tests['suites']), 'Incomplete r02 host tests')
    require(tests['sanitizers'] == ['address', 'undefined'], 'Missing r02 sanitizers')
    for name, digest in tests['inputs'].items():
        require(data['inputs'].get(name) == digest, 'r02 tests used different inputs: '+name)
    for case in expected:
        require('PASS ' in (OUT/(case+'-tests.txt')).read_text(), 'Missing r02 test output: '+case)
    controls = json.loads((OUT/'image-controls.json').read_text())
    require(controls['result'] == 'PASS' and
            controls['actual_merged_sha256'] == image['merged_sha256'] and
            {m['name'] for m in controls['rejected_mutations']} == {
                'reset-into-storage', 'image-overwrites-nvs', 'watchdog-disabled', 'watchdog-secure-only'},
            'Missing r02 image/configuration negative controls')
    require(data['flashed'] is False and data['physical_test'] is False and
            data['manufacturing_release'] is False and image['signed_boot'] is False and
            image['ota'] is False and data['recovery_inspection']['hardware_reset_observed'] is False and
            tests['hardware_reset_observed'] is False and tests['actual_modem_test'] is False and
            tests['real_dns'] is False, 'Unexpected r02 acceptance claim')
    return dict(result='PASS', scope='Saved target build and host fault injection; hardware untested',
                board=data['board'], host_scenarios=len(expected),
                image_configuration_controls=4, merged_sha256=image['merged_sha256'],
                memory_usage_bytes=data['memory_usage_bytes'],
                flashed=False, hardware_reset_observed=False, manufacturing_release=False)


if __name__ == '__main__':
    print(json.dumps(verify(), indent=2))
