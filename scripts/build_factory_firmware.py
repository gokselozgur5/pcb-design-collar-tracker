#!/usr/bin/env python3
"""Compile the observation image with a verified local SDK; never flash a board."""
import argparse
import hashlib
import json
import os
from pathlib import Path
import subprocess

from check_firmware_board import check

ROOT = Path(__file__).resolve().parents[1]


def build(sdk, directory, overlay=None):
    sdk, directory = sdk.resolve(), directory.resolve()
    if str(sdk).startswith('/Volumes/GOKSSD/') and not os.path.ismount('/Volumes/GOKSSD'):
        raise ValueError('GOKSSD is not mounted')
    lock = json.loads((ROOT / 'firmware/toolchain-lock.json').read_text())
    for module in lock['modules']:
        actual = subprocess.check_output(['git', 'rev-parse', 'HEAD'], cwd=sdk/module['path'], text=True).strip()
        if actual != module['commit']:
            raise ValueError('SDK revision mismatch: ' + module['name'])
    check()
    for name in ['cache', 'tmp']:
        (sdk/name).mkdir(exist_ok=True)
    env = os.environ.copy()
    env.update(PATH=str(sdk/'venv/bin') + os.pathsep + env['PATH'],
               ZEPHYR_BASE=str(sdk/'zephyr'),
               ZEPHYR_SDK_INSTALL_DIR=str(sdk/'zephyr-sdk-1.0.1'),
               ZEPHYR_TOOLCHAIN_VARIANT='zephyr', XDG_CACHE_HOME=str(sdk/'cache'),
               TMPDIR=str(sdk/'tmp'), PYTHONDONTWRITEBYTECODE='1', LC_ALL='C')
    args = [str(sdk/'venv/bin/west'), 'build', '--no-sysbuild', '-b', 'collar_r05l/nrf9151',
            '-d', str(directory), str(ROOT/'firmware/factory'), '--',
            '-DUSER_CACHE_DIR=' + str(sdk/'cache/zephyr'), '-DBOARD_ROOT=' + str(ROOT/'firmware')]
    if overlay:
        args.append('-DDTC_OVERLAY_FILE=' + str(overlay.resolve()))
    subprocess.run(args, env=env, cwd=sdk, check=True)
    artifacts = {}
    for name in ['zephyr.elf', 'zephyr.hex', 'zephyr.dts', '.config']:
        path = directory/'zephyr'/name
        artifacts[name] = dict(bytes=path.stat().st_size, sha256=hashlib.sha256(path.read_bytes()).hexdigest())
    result = dict(result='BUILD_PASS', board='collar_r05l/nrf9151', artifacts=artifacts,
                  flashed=False, physical_test=False, manufacturing_release=False)
    (directory/'build-result.json').write_text(json.dumps(result, indent=2) + '\n')
    return result


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--sdk-root', required=True, type=Path)
    parser.add_argument('--build-dir', required=True, type=Path)
    parser.add_argument('--overlay', type=Path)
    args = parser.parse_args()
    print(json.dumps(build(args.sdk_root, args.build_dir, args.overlay), indent=2))
