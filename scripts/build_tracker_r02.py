#!/usr/bin/env python3
"""Build tracker r02 recovery on the frozen NS/TF-M board. Never flash hardware."""
import argparse
import hashlib
import json
import os
from pathlib import Path
import subprocess

from check_firmware_board import check
from inspect_tracker_image import inspect

ROOT = Path(__file__).resolve().parents[1]


def build(sdk, directory, config=None):
    sdk, directory = sdk.resolve(), directory.resolve()
    if directory.exists() and any(directory.iterdir()):
        raise ValueError('Use a new empty build directory; preserve earlier build evidence')
    for path in (sdk, directory):
        if str(path).startswith('/Volumes/GOKSSD/') and not os.path.ismount('/Volumes/GOKSSD'):
            raise ValueError('GOKSSD is not mounted')
        if not any(path.is_relative_to(p) for p in ('/Users/gok/codex', '/Volumes/GOKSSD/codex')):
            raise ValueError('Build and SDK must be inside a permitted workspace')
    modules = []
    for lock in ('firmware/toolchain-lock.json', 'firmware/tracker/toolchain-lock.json'):
        modules.extend(json.loads((ROOT / lock).read_text())['modules'])
    for module in modules:
        actual = subprocess.check_output(['git', 'rev-parse', 'HEAD'], cwd=sdk/module['path'], text=True).strip()
        if actual != module['commit']:
            raise ValueError('SDK revision mismatch: ' + module['name'])
    check()
    inputs = list((ROOT/'firmware/tracker-r02/src').glob('*'))
    inputs += [ROOT/'firmware/tracker-r02'/name for name in ('CMakeLists.txt', 'Kconfig', 'prj.conf')]
    inputs += [p for p in (ROOT/'firmware/boards/goksel/collar_tracker_r05l').iterdir()
               if p.name not in ('UPSTREAM.md', 'LICENSE.Apache-2.0')]
    inputs += list((ROOT/'firmware/dts').rglob('*.yaml'))
    inputs += [ROOT/'firmware/factory/src/board_contract.h', ROOT/'firmware/tracker/src/outbox.c', ROOT/'firmware/tracker/src/outbox.h']
    source_hashes = {str(p.relative_to(ROOT)): hashlib.sha256(p.read_bytes()).hexdigest()
                     for p in sorted(inputs) if p.is_file()}
    for name in ('cache', 'tmp'):
        (sdk/name).mkdir(exist_ok=True)
    env = os.environ.copy()
    env.update(PATH=str(sdk/'venv/bin') + os.pathsep + env['PATH'],
               ZEPHYR_BASE=str(sdk/'zephyr'),
               ZEPHYR_SDK_INSTALL_DIR=str(sdk/'zephyr-sdk-1.0.1'),
               ZEPHYR_TOOLCHAIN_VARIANT='zephyr', XDG_CACHE_HOME=str(sdk/'cache'),
               TMPDIR=str(sdk/'tmp'), PYTHONDONTWRITEBYTECODE='1', LC_ALL='C')
    args = [str(sdk/'venv/bin/west'), 'build', '--no-sysbuild', '-b',
            'collar_tracker_r05l/nrf9151/ns', '-d', str(directory),
            str(ROOT/'firmware/tracker-r02'), '--', '-DUSER_CACHE_DIR=' + str(sdk/'cache/zephyr'),
            '-DBOARD_ROOT=' + str(ROOT/'firmware')]
    if config:
        args.append('-DEXTRA_CONF_FILE=' + str(config.resolve()))
    subprocess.run(args, env=env, cwd=sdk, check=True)
    for name, digest in source_hashes.items():
        if hashlib.sha256((ROOT/name).read_bytes()).hexdigest() != digest:
            raise ValueError('Source changed during build: ' + name)
    inspection = inspect(directory)
    config_text = (directory/'zephyr/.config').read_text()
    required = ['CONFIG_WATCHDOG=y', 'CONFIG_HWINFO=y', 'CONFIG_MAIN_THREAD_PRIORITY=5',
                'CONFIG_NRF_MODEM_LIB_ON_FAULT_APPLICATION_SPECIFIC=y',
                '# CONFIG_NRF_WDT0_SECURE is not set']
    if not all(line in config_text.splitlines() for line in required):
        raise ValueError('Compiled watchdog/recovery contract mismatch')
    inspection['watchdog_contract'] = required
    inspection['hardware_reset_observed'] = False
    artifacts = {}
    for name in ('zephyr/zephyr.elf', 'zephyr/zephyr.hex', 'zephyr/zephyr.dts',
                 'zephyr/.config', inspection['merged_hex'], 'tfm/bin/tfm_s.elf'):
        path = directory/name
        artifacts[name] = dict(bytes=path.stat().st_size,
                               sha256=hashlib.sha256(path.read_bytes()).hexdigest())
    result = dict(result='BUILD_PASS', board='collar_tracker_r05l/nrf9151/ns',
                  artifacts=artifacts, image_inspection=inspection, compiled_inputs=source_hashes,
                  flashed=False, physical_test=False,
                  manufacturing_release=False)
    (directory/'build-result.json').write_text(json.dumps(result, indent=2) + '\n')
    return result


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--sdk-root', required=True, type=Path)
    parser.add_argument('--build-dir', required=True, type=Path)
    parser.add_argument('--config', type=Path)
    args = parser.parse_args()
    print(json.dumps(build(args.sdk_root, args.build_dir, args.config), indent=2))
