#!/usr/bin/env python3
"""Freeze verified r02 default-build evidence once; do not replace a checkpoint."""
import argparse
from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path
import re
import shutil

from check_firmware_board import check
from inspect_tracker_image import require
from inspect_tracker_r02 import inspect

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT/'firmware/evidence/tracker-r02'
RUNTIME = ROOT/'.runtime/tracker-r02'


def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def capture(directory, log):
    require(not OUT.exists(), 'r02 checkpoint exists; preserve it and use a new revision')
    data = json.loads((directory/'build-result.json').read_text())
    require(data['result'] == 'BUILD_PASS', 'Build result is not successful')
    for name, expected in data['compiled_inputs'].items():
        require(digest(ROOT/name) == expected, 'Build input changed: '+name)
    for name, expected in data['artifacts'].items():
        require(digest(directory/name) == expected['sha256'], 'Build artifact changed: '+name)
    config = (directory/'zephyr/.config').read_text().splitlines()
    require('CONFIG_TRACKER_HOST=""' in config and 'CONFIG_TRACKER_DEVICE_ID=""' in config,
            'Only the default unprovisioned configuration can be published by this helper')
    data['recovery_inspection'] = inspect(directory)
    tests = json.loads((RUNTIME/'tests.json').read_text())
    require(tests['result'] == 'PASS', 'r02 tests have not passed')
    for name, expected in tests['inputs'].items():
        require(digest(ROOT/name) == expected, 'Test input changed: '+name)
    controls = json.loads((RUNTIME/'image-controls.json').read_text())
    require(controls['result'] == 'PASS' and
            controls['actual_merged_sha256'] == data['recovery_inspection']['merged_sha256'],
            'r02 controls did not test this build')
    memory = re.findall(r'^\s*(FLASH|RAM):\s+(\d+) B', log.read_text(), re.MULTILINE)
    require([name for name, _ in memory] == ['FLASH', 'RAM', 'FLASH', 'RAM'],
            'Expected TF-M then application memory reports')
    data['memory_usage_bytes'] = dict(
        tfm=dict(flash=int(memory[0][1]), ram=int(memory[1][1])),
        application=dict(flash=int(memory[2][1]), ram=int(memory[3][1])),
        modem_shared_reserved=40960)
    data['native_board_check'] = check()
    data['compiler_exit'] = 0  # build-result.json is written only after a successful compiler exit.
    data['captured_utc'] = datetime.now(timezone.utc).isoformat()
    data['unresolved'] = [
        'No actual watchdog reset, modem/SIM/DNS or powered-board test',
        'No physical NVS power-cut test, current measurement or stack-margin measurement',
        'No signed boot/update, provisioning or factory integration',
        'No live API/credentials, approved battery, assembly or ingress qualification',
    ]
    OUT.mkdir(parents=True)
    for name, saved in [('zephyr/.config', 'compiled.config'), ('zephyr/zephyr.dts', 'compiled.dts'),
                        ('tfm/CMakeCache.txt', 'tfm-config.txt')]:
        shutil.copyfile(directory/name, OUT/saved)
    shutil.copyfile(log, OUT/'build.txt')
    for name in ['tests.json', 'image-controls.json'] + [s['case']+'-tests.txt' for s in tests['suites']]:
        shutil.copyfile(RUNTIME/name, OUT/name)
    paths = set(ROOT/name for name in data['compiled_inputs'])
    paths.update(p for p in (ROOT/'firmware/tracker-r02').rglob('*') if p.is_file())
    paths.update(p for p in OUT.iterdir() if p.is_file())
    paths.update(ROOT/'scripts'/name for name in (
        'build_tracker_r02.py', 'test_tracker_r02.py', 'inspect_tracker_r02.py',
        'test_tracker_r02_image.py', 'capture_tracker_r02.py', 'verify_tracker_r02.py',
        'inspect_tracker_image.py', 'test_tracker_image.py', 'check_firmware_board.py'))
    paths.update(ROOT/name for name in (
        'firmware/toolchain-lock.json', 'firmware/tracker/toolchain-lock.json',
        'firmware/tracker/python-requirements.lock',
        'firmware/evidence/tracker-r01/build-evidence.json'))
    data['inputs'] = {str(p.relative_to(ROOT)): digest(p) for p in sorted(paths)}
    (OUT/'build-evidence.json').write_text(json.dumps(data, indent=2)+'\n')
    return dict(result='SAVED', inputs=len(paths), merged_sha256=data['image_inspection']['merged_sha256'])


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('build_dir', type=Path)
    parser.add_argument('--build-log', required=True, type=Path)
    args = parser.parse_args()
    print(json.dumps(capture(args.build_dir, args.build_log), indent=2))
