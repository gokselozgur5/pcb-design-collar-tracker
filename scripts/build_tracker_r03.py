#!/usr/bin/env python3
"""Build signed r03 images with an explicit local key. Never provision or flash."""
import argparse
import hashlib
import json
import os
from pathlib import Path
import subprocess

from check_firmware_board import check

ROOT = Path(__file__).resolve().parents[1]


def build(sdk, directory, key, config=None):
    sdk, directory, key = sdk.resolve(), directory.resolve(), key.resolve()
    if directory.exists() and any(directory.iterdir()):
        raise ValueError('Use a new empty build directory')
    for path in (sdk, directory):
        if str(path).startswith('/Volumes/GOKSSD/') and not os.path.ismount('/Volumes/GOKSSD'):
            raise ValueError('GOKSSD is not mounted')
        if not any(path.is_relative_to(p) for p in ('/Users/gok/codex', '/Volumes/GOKSSD/codex')):
            raise ValueError('Build and SDK must be inside a permitted workspace')
    if not key.is_file() or key.is_relative_to(sdk/'bootloader/mcuboot'):
        raise ValueError('Supply a private signing key outside the public SDK defaults')
    if any(c in str(key) for c in [',', '\n', '\r', '"']):
        raise ValueError('Signing key path is ambiguous to the SDK key-list parser')
    signing = json.loads(subprocess.check_output([
        str(sdk/'venv/bin/python'), str(ROOT/'scripts/tracker_signing_key.py'),
        str(key), '--sdk-root', str(sdk)], text=True))
    modules = []
    for lock in ('firmware/toolchain-lock.json', 'firmware/tracker/toolchain-lock.json'):
        modules.extend(json.loads((ROOT/lock).read_text())['modules'])
    for module in modules:
        actual = subprocess.check_output(['git', 'rev-parse', 'HEAD'], cwd=sdk/module['path'], text=True).strip()
        if actual != module['commit']:
            raise ValueError('SDK revision mismatch: '+module['name'])
    check()
    inputs = list((ROOT/'firmware/tracker-r03').rglob('*'))
    inputs += list((ROOT/'firmware/boards/goksel/collar_update_r05l').rglob('*'))
    inputs += list((ROOT/'firmware/tracker-r02/src').glob('*'))
    inputs += list((ROOT/'firmware/dts').rglob('*.yaml'))
    inputs += [ROOT/'firmware/factory/src/board_contract.h', ROOT/'firmware/tracker/src/outbox.c', ROOT/'firmware/tracker/src/outbox.h']
    hashes = {str(p.relative_to(ROOT)): hashlib.sha256(p.read_bytes()).hexdigest()
              for p in sorted(inputs) if p.is_file()}
    env = os.environ.copy()
    env.update(PATH=str(sdk/'venv/bin')+os.pathsep+env['PATH'],
               ZEPHYR_BASE=str(sdk/'zephyr'), ZEPHYR_SDK_INSTALL_DIR=str(sdk/'zephyr-sdk-1.0.1'),
               ZEPHYR_TOOLCHAIN_VARIANT='zephyr', XDG_CACHE_HOME=str(sdk/'cache'),
               TMPDIR=str(sdk/'tmp'), PYTHONDONTWRITEBYTECODE='1', LC_ALL='C')
    args = [str(sdk/'venv/bin/west'), 'build', '--sysbuild', '-b', 'collar_update_r05l/nrf9151/ns',
            '-d', str(directory), str(ROOT/'firmware/tracker-r03'), '--',
            '-DUSER_CACHE_DIR='+str(sdk/'cache/zephyr'), '-DBOARD_ROOT='+str(ROOT/'firmware'),
            '-Dmcuboot_USER_CACHE_DIR='+str(sdk/'cache/zephyr'),
            '-Dtracker-r03_USER_CACHE_DIR='+str(sdk/'cache/zephyr'),
            '-DDTS_ROOT='+str(ROOT/'firmware'), '-DSB_CONFIG_BOOT_SIGNATURE_KEY_FILE='+json.dumps(str(key))]
    if config:
        args.append('-DEXTRA_CONF_FILE='+str(config.resolve()))
    subprocess.run(args, env=env, cwd=sdk, check=True)
    for name, digest in hashes.items():
        if hashlib.sha256((ROOT/name).read_bytes()).hexdigest() != digest:
            raise ValueError('Input changed during build: '+name)
    public_path = directory/'signing-public.pem'
    public_path.write_text(signing['public_pem'])
    inspection = json.loads(subprocess.check_output([
        str(sdk/'venv/bin/python'), str(ROOT/'scripts/inspect_tracker_r03.py'),
        str(directory), '--public-key', str(public_path), '--merge'], text=True))
    result = dict(result='BUILD_PASS', board='collar_update_r05l/nrf9151/ns',
                  compiled_inputs=hashes, flashed=False, physical_test=False,
                  signing=signing, image_inspection=inspection,
                  production_key_accepted=False, manufacturing_release=False)
    (directory/'build-result.json').write_text(json.dumps(result, indent=2)+'\n')
    return result


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--sdk-root', required=True, type=Path)
    parser.add_argument('--build-dir', required=True, type=Path)
    parser.add_argument('--signing-key', required=True, type=Path)
    parser.add_argument('--config', type=Path)
    args = parser.parse_args()
    print(json.dumps(build(args.sdk_root, args.build_dir, args.signing_key, args.config), indent=2))
