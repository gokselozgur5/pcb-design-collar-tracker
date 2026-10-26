#!/usr/bin/env python3
"""Freeze r03 prototype evidence once; use the pinned SDK Python."""
import argparse
from datetime import datetime, timezone
import json
from pathlib import Path
import re
import shutil

from check_firmware_board import check
from inspect_tracker_image import require
from inspect_tracker_r03 import digest, inspect
from tracker_signing_key import inspect as inspect_key

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT/'firmware/evidence/tracker-r03'
RUNTIME = ROOT/'.runtime/tracker-r03'


def capture(directory, sdk, key):
    require(not OUT.exists(), 'Preserve the existing r03 checkpoint; use a new revision')
    data = json.loads((directory/'build-result.json').read_text())
    require(data['result'] == 'BUILD_PASS', 'Missing successful target build')
    signing = inspect_key(key, sdk)
    public = RUNTIME/'signing-public.pem'
    require(public.read_text() == signing['public_pem'], 'Different inspection key')
    data['signing'] = signing
    data['image_inspection'] = inspect(directory, public)
    require(data['image_inspection']['signed_hex']['spki_sha256'] == signing['spki_sha256'], 'Signing identity mismatch')
    tests = json.loads((RUNTIME/'trial-tests.json').read_text())
    controls = json.loads((RUNTIME/'image-controls.json').read_text())
    simulator = json.loads((RUNTIME/'mcuboot-simulator.json').read_text())
    for report in (tests, controls, simulator):
        require(report['result'] == 'PASS', 'Incomplete r03 tests')
    require(controls['actual_complete_sha256'] == data['image_inspection']['complete_sha256'], 'Controls tested another image')
    for source in [data['compiled_inputs'], tests['inputs'], controls['inputs']]:
        for name, expected in source.items():
            require(digest(ROOT/name) == expected, 'Input changed since build/test: '+name)
    artifacts = [
        'mcuboot/zephyr/zephyr.hex', 'mcuboot/zephyr/zephyr.elf', 'mcuboot/zephyr/.config',
        'mcuboot/zephyr/zephyr.dts', 'mcuboot/zephyr/autogen-pubkey.c',
        'tracker-r03/zephyr/zephyr.signed.hex', 'tracker-r03/zephyr/zephyr.signed.bin',
        'tracker-r03/zephyr/tfm_merged.hex', 'tracker-r03/zephyr/zephyr.elf',
        'tracker-r03/zephyr/.config', 'tracker-r03/zephyr/zephyr.dts',
        'tracker-r03/tfm/bin/tfm_s.hex', 'tracker-r03/tfm/bin/tfm_s.elf',
        'tracker-r03/tfm/CMakeCache.txt', 'collar-tracker-r03-prototype.hex',
    ]
    data['artifacts'] = {name: dict(sha256=digest(directory/name), bytes=(directory/name).stat().st_size) for name in artifacts}
    log = RUNTIME/'build-final.txt'
    cache_paths = re.findall(r'Cache files will be written to: (.+)', log.read_text())
    require(len(cache_paths) == 4 and all(Path(p).is_relative_to(sdk/'cache') for p in cache_paths),
            'Every sysbuild/application/bootloader/TF-M cache must stay in the task SDK')
    data['cmake_cache_paths'] = cache_paths
    memory = re.findall(r'^\s*(FLASH|RAM):\s+(\d+) B', log.read_text(), re.MULTILINE)
    require([m[0] for m in memory] == ['FLASH', 'RAM']*3, 'Unexpected target memory reports')
    data['memory_usage_bytes'] = {name: dict(flash=int(memory[2*i][1]), ram=int(memory[2*i+1][1]))
                                  for i, name in enumerate(['tfm', 'application', 'mcuboot'])}
    data['memory_usage_bytes']['modem_shared_reserved'] = 40960
    data['native_board_check'] = check()
    data['compiler_exit'] = 0
    data['captured_utc'] = datetime.now(timezone.utc).isoformat()
    data['prototype_key_only'] = True
    data['ota_transport_implemented'] = False
    data['unresolved'] = [
        'No actual board boot, signature rejection, watchdog handoff, trial/revert or power-cut test',
        'No OTA transport/staging; swap-offset requires secondary + 4096 bytes',
        'No production key custody, credentials, provisioning/debug-lock or r02 migration acceptance',
        'No real GNSS/LTE-M/TLS/modem, current, factory/SMT, RF or ingress acceptance',
        'No approved battery, physical assembly/strain-relief or supplier enquiry authorization',
    ]
    copies = [
        (directory/'mcuboot/zephyr/.config', 'boot.config'),
        (directory/'mcuboot/zephyr/zephyr.dts', 'boot.dts'),
        (directory/'mcuboot/zephyr/autogen-pubkey.c', 'boot-public-key.c'),
        (directory/'tracker-r03/zephyr/.config', 'application.config'),
        (directory/'tracker-r03/zephyr/zephyr.dts', 'application.dts'),
        (directory/'tracker-r03/tfm/CMakeCache.txt', 'tfm-config.txt'),
        (sdk/'bootloader/mcuboot/Cargo.lock', 'simulator-Cargo.lock'),
        (RUNTIME/'simulator-run.txt', 'simulator-metadata-recovery.txt'),
        (log, 'build.txt'),
    ]
    for name in ['trial-tests.json', 'image-controls.json', 'mcuboot-simulator.json', 'mcuboot-simulator.txt']:
        copies.append((RUNTIME/name, name))
    for scenario in tests['scenarios']:
        name = 'trial-'+scenario['case']+'.txt'
        copies.append((RUNTIME/name, name))
    require(digest(sdk/'bootloader/mcuboot/Cargo.lock') == simulator['cargo_lock_sha256'] and
            digest(RUNTIME/'mcuboot-simulator.txt') == simulator['log_sha256'], 'Simulator evidence changed')
    OUT.mkdir(parents=True)
    for source, name in copies:
        shutil.copyfile(source, OUT/name)
    paths = set(ROOT/name for name in data['compiled_inputs'])
    for report in (tests, controls):
        paths.update(ROOT/name for name in report['inputs'])
    for relative in ['firmware/tracker-r03', 'firmware/boards/goksel/collar_update_r05l']:
        paths.update(p for p in (ROOT/relative).rglob('*') if p.is_file())
    paths.update(p for p in OUT.iterdir() if p.is_file())
    paths.update(ROOT/'scripts'/name for name in [
        'build_tracker_r03.py', 'test_tracker_r03.py', 'tracker_signing_key.py', 'test_mcuboot_r03.py',
        'inspect_tracker_r03.py', 'test_tracker_r03_image.py', 'capture_tracker_r03.py',
        'verify_tracker_r03.py', 'inspect_tracker_image.py', 'inspect_tracker_r02.py', 'check_firmware_board.py'])
    paths.update(ROOT/name for name in ['firmware/toolchain-lock.json', 'firmware/tracker/toolchain-lock.json',
                                       'firmware/tracker/python-requirements.lock'])
    data['inputs'] = {str(p.relative_to(ROOT)): digest(p) for p in sorted(paths)}
    (OUT/'build-evidence.json').write_text(json.dumps(data, indent=2)+'\n')
    return dict(result='SAVED', inputs=len(paths), complete_sha256=data['image_inspection']['complete_sha256'])


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('build_dir', type=Path)
    parser.add_argument('--sdk-root', type=Path, required=True)
    parser.add_argument('--signing-key', type=Path, required=True)
    args = parser.parse_args()
    print(json.dumps(capture(args.build_dir, args.sdk_root, args.signing_key), indent=2))
