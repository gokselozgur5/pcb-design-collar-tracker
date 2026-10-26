#!/usr/bin/env python3
"""Run pinned Nordic MCUboot host simulation, retaining flags and limitations."""
import argparse
import hashlib
import json
import os
from pathlib import Path
import re
import subprocess

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT/'.runtime/tracker-r03'


def test(sdk, target):
    if 'MCUBOOT_SKIP_SLOW_TESTS' in os.environ:
        raise ValueError('Unset MCUBOOT_SKIP_SLOW_TESTS; interruption tests must execute')
    sdk, target = sdk.resolve(), target.resolve()
    if not os.path.ismount('/Volumes/GOKSSD') or not target.is_relative_to('/Volumes/GOKSSD/codex'):
        raise ValueError('Use a target directory on mounted GOKSSD inside codex')
    lock = json.loads((ROOT/'firmware/tracker/toolchain-lock.json').read_text())
    module = next(m for m in lock['modules'] if m['path'] == 'bootloader/mcuboot')
    boot = sdk/module['path']
    commit = subprocess.check_output(['git', 'rev-parse', 'HEAD'], cwd=boot, text=True).strip()
    if commit != module['commit']:
        raise ValueError('MCUboot revision mismatch')
    subprocess.run(['git', 'diff', '--exit-code', 'HEAD', '--', 'boot', 'sim', 'ext/mbedtls'], cwd=boot, check=True)
    mac_sdk = subprocess.check_output(['xcrun', '--show-sdk-path'], text=True).strip()
    flags = ['-isystem', mac_sdk+'/usr/include',
             '-I'+str(ROOT/'firmware/tracker-r03/tests/mcuboot-host'),
             '-DMCUBOOT_DOWNGRADE_PREVENTION', '-DMCUBOOT_DOWNGRADE_PREVENTION_SECURITY_COUNTER=0',
             '-DCONFIG_MCUBOOT_MCUBOOT_IMAGE_NUMBER=-1',
             '-DCONFIG_NCS_MCUBOOT_IMG_VALIDATE_ATTEMPT_COUNT=1']
    env = os.environ.copy()
    rust = Path('/Users/gok/.rustup/toolchains/stable-aarch64-apple-darwin/bin')
    env.update(CARGO_HOME=str(sdk/'cargo-home'), CARGO_TARGET_DIR=str(target),
               RUSTC=str(rust/'rustc'), RUSTDOC=str(rust/'rustdoc'),
               CC='/opt/homebrew/bin/gcc-15', CFLAGS=' '.join(flags))
    args = [str(rust/'cargo'), 'test', '--locked', '--features', 'sig-ecdsa,swap-offset,validate-primary-slot']
    OUT.mkdir(parents=True, exist_ok=True)
    log = OUT/'mcuboot-simulator.txt'
    with log.open('w') as output:
        result = subprocess.run(args, cwd=boot/'sim', env=env, stdout=output, stderr=subprocess.STDOUT)
    return record_run(boot, log, result.returncode, commit, args, flags, env)


def record_run(boot, log, exit_code, commit, args, flags, env):
    """Record an observed Cargo exit and its log; this does not execute tests."""
    text = log.read_text()
    summaries = re.findall(r'test result: (\w+)\. (\d+) passed; (\d+) failed;', text)
    if exit_code != 0 or not summaries or any(s[0] != 'ok' or s[2] != '0' for s in summaries):
        raise ValueError('MCUboot simulation failed; inspect '+str(log))
    report = dict(result='PASS', compiler_exit=exit_code, mcuboot_commit=commit,
                  command=args, c_flags=flags, summaries=summaries,
                  compiler=subprocess.check_output([env['CC'], '--version'], text=True).splitlines()[0],
                  rustc=subprocess.check_output([env['RUSTC'], '--version'], text=True).strip(),
                  cargo_lock_sha256=hashlib.sha256((boot/'Cargo.lock').read_bytes()).hexdigest(),
                  mbedtls_commit=subprocess.check_output(['git', 'rev-parse', 'HEAD'], cwd=boot/'ext/mbedtls', text=True).strip(),
                  log_sha256=hashlib.sha256(log.read_bytes()).hexdigest(),
                  host_crypto='TinyCrypt ECDSA P-256; target uses Nordic Oberon',
                  geometry='Upstream simulator device geometries, not the collar flash driver',
                  feature_inapplicable_tests_return_early=True, actual_target_image_executed=False,
                  hardware_reset_observed=False)
    (OUT/'mcuboot-simulator.json').write_text(json.dumps(report, indent=2)+'\n')
    return report


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--sdk-root', type=Path, required=True)
    parser.add_argument('--target-dir', type=Path, required=True)
    args = parser.parse_args()
    print(json.dumps(test(args.sdk_root, args.target_dir), indent=2))
