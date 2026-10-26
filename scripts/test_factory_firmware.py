#!/usr/bin/env python3
"""Compile an intentionally invalid board overlay in a separate build directory."""
import argparse
import json
from pathlib import Path
import subprocess
import sys

ROOT = Path(__file__).resolve().parents[1]


def run(sdk, directory, output):
    if directory.exists():
        raise ValueError('Choose a new negative-control directory; do not reuse a prior ELF')
    command = [sys.executable, str(ROOT/'scripts/build_factory_firmware.py'),
               '--sdk-root', str(sdk), '--build-dir', str(directory),
               '--overlay', str(ROOT/'firmware/tests/invalid-board.overlay')]
    result = subprocess.run(command, cwd=ROOT, text=True, stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(result.stdout)
    messages = ['CHG_STAT pin mismatch', 'I2C must wait for VIO']
    checks = {text: text in result.stdout for text in messages}
    report = dict(result='PASS' if result.returncode != 0 and all(checks.values()) else 'FAIL',
                  control='Incorrect pin and early I2C initialization must fail compilation',
                  compiler_exit=result.returncode, diagnostics=checks,
                  firmware_published=False, physical_test=False)
    output.with_suffix('.json').write_text(json.dumps(report, indent=2) + '\n')
    if report['result'] != 'PASS':
        raise ValueError('Negative compile control failed; inspect ' + str(output))
    return report


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--sdk-root', required=True, type=Path)
    parser.add_argument('--build-dir', required=True, type=Path)
    parser.add_argument('--log', required=True, type=Path)
    args = parser.parse_args()
    print(json.dumps(run(args.sdk_root, args.build_dir, args.log), indent=2))
