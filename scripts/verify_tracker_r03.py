#!/usr/bin/env python3
"""Read-only verification of the saved r03 checkpoint; no SDK or key required."""
import hashlib
import json
from pathlib import Path

from check_firmware_board import check
from inspect_tracker_image import require

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT/'firmware/evidence/tracker-r03'


def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def verify():
    data = json.loads((OUT/'build-evidence.json').read_text())
    for name, expected in data['inputs'].items():
        path = (ROOT/name).resolve()
        require(path.is_relative_to(ROOT), 'r03 input escapes checkout')
        require(digest(path) == expected, 'Changed r03 input: '+name)
    for name, expected in data['compiled_inputs'].items():
        require(data['inputs'].get(name) == expected, 'Compiled r03 source not preserved: '+name)
    require(data['result'] == 'BUILD_PASS' and data['compiler_exit'] == 0 and
            data['board'] == 'collar_update_r05l/nrf9151/ns', 'Missing r03 target build')
    require(data['native_board_check'] == check(), 'Changed r03 native signal contract')
    image = data['image_inspection']
    require(image['result'] == 'PASS' and image['programmed_storage_bytes'] == 0 and
            image['programmed_secondary_bytes'] == 0 and image['signatures_verified_against_embedded_key'] is True,
            'Invalid saved r03 image inspection')
    require(image['complete_sha256'] == data['artifacts'][image['complete_hex']]['sha256'], 'Image identity mismatch')
    require(image['signed_hex']['signed_content_sha256'] == image['signed_bin']['signed_content_sha256'] and
            image['signed_hex']['spki_sha256'] == data['signing']['spki_sha256'], 'Signature/content identity mismatch')
    require([image['reset_vectors'][name]['address'] for name in ['bootloader', 'secure', 'application']] ==
            [0, 0x10200, 0x50000] and image['secondary_update_address'] == 0x81000 and
            image['storage'] == dict(address=0xf8000, bytes=32768), 'Unexpected signed image map')
    for saved, artifact, contract in [
            ('boot.config', 'mcuboot/zephyr/.config', image['boot_contract']),
            ('application.config', 'tracker-r03/zephyr/.config', image['application_contract'])]:
        path = OUT/saved
        require(digest(path) == data['artifacts'][artifact]['sha256'], 'Changed compiled r03 config')
        require(all(line in path.read_text().splitlines() for line in contract), 'Missing compiled r03 settings')
    tests = json.loads((OUT/'trial-tests.json').read_text())
    expected = {'policy': 0, 'factory': 0, 'healthy': 0, 'missing-ack': 42, 'late-evidence': 42, 'confirmation-failed': 42}
    require(tests['result'] == 'PASS' and tests['sanitizers'] == ['address', 'undefined'] and
            len(tests['scenarios']) == 6 and
            {s['case']: s['exit'] for s in tests['scenarios']} == expected and
            all(s['exit'] == s['expected_exit'] for s in tests['scenarios']), 'Incomplete trial tests')
    for name in expected:
        require('PASS ' in (OUT/('trial-'+name+'.txt')).read_text(), 'Missing trial output: '+name)
    controls = json.loads((OUT/'image-controls.json').read_text())
    require(controls['result'] == 'PASS' and controls['actual_complete_sha256'] == image['complete_sha256'] and
            controls['actual_signed_bin_sha256'] == data['artifacts']['tracker-r03/zephyr/zephyr.signed.bin']['sha256'] and
            len(controls['rejected_mutations']) == 9, 'Missing r03 image/key negative controls')
    for report in [tests, controls]:
        for name, expected_hash in report['inputs'].items():
            require(data['inputs'].get(name) == expected_hash, 'Tests used different r03 input: '+name)
    sim = json.loads((OUT/'mcuboot-simulator.json').read_text())
    require(sim['result'] == 'PASS' and sim['compiler_exit'] == 0 and
            digest(OUT/'mcuboot-simulator.txt') == sim['log_sha256'] and
            digest(OUT/'simulator-Cargo.lock') == sim['cargo_lock_sha256'], 'Incomplete MCUboot host simulation')
    for owner, fields in [(data, ['flashed', 'physical_test', 'production_key_accepted', 'manufacturing_release', 'ota_transport_implemented']),
                          (image, ['physical_boot_observed', 'ota_transport_implemented', 'manufacturing_release']),
                          (tests, ['hardware_reset_observed', 'actual_modem_test']),
                          (sim, ['actual_target_image_executed', 'hardware_reset_observed']),
                          (data['signing'], ['production_custody_accepted'])]:
        require(all(owner[k] is False for k in fields), 'Unexpected r03 production/hardware claim')
    return dict(result='PASS', scope='Saved signed target build and host tests; no powered-device acceptance',
                source_evidence_identities=len(data['inputs']), complete_sha256=image['complete_sha256'],
                trial_scenarios=6, image_key_negative_controls=9, simulator=sim['summaries'],
                memory_usage_bytes=data['memory_usage_bytes'], ota_transport_implemented=False,
                physical_boot_observed=False, manufacturing_release=False)


if __name__ == '__main__':
    print(json.dumps(verify(), indent=2))
