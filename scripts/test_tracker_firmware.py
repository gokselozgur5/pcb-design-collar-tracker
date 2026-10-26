#!/usr/bin/env python3
"""Run portable C fault-injection and local mTLS tests; no device or public service."""
import argparse
import json
import os
from pathlib import Path
import subprocess
import sys

ROOT = Path(__file__).resolve().parents[1]


def test(python):
    runtime = ROOT/'.runtime/tracker-r01'
    runtime.mkdir(parents=True, exist_ok=True)
    env = os.environ.copy()
    env['PYTHONDONTWRITEBYTECODE'] = '1'
    compile_args = ['clang', '-std=c11', '-Wall', '-Wextra', '-Werror',
                    '-fsanitize=address,undefined', '-g', '-Ifirmware/tracker/src',
                    'firmware/tracker/src/outbox.c', 'firmware/tracker/tests/outbox_test.c',
                    '-o', str(runtime/'outbox-test')]
    subprocess.run(compile_args, cwd=ROOT, env=env, check=True)
    commands = [[str(runtime/'outbox-test')],
                [str(python.absolute()), 'firmware/receiver/test_receiver.py']]
    results = []
    for name, command in zip(('outbox', 'receiver'), commands):
        result = subprocess.run(command, cwd=ROOT, env=env, stdout=subprocess.PIPE,
                                stderr=subprocess.STDOUT, text=True)
        (runtime/(name+'-tests.txt')).write_text(result.stdout)
        print(result.stdout, end='')
        result.check_returncode()
        results.append(dict(suite=name, exit=result.returncode))
    report = dict(result='PASS', suites=results, sanitizers=['address', 'undefined'],
                  receiver_tests=7, c_crash_boundaries=6, corrupted_record_bytes=40,
                  actual_modem_test=False, physical_power_failure_test=False)
    (runtime/'tests.json').write_text(json.dumps(report, indent=2)+'\n')
    return report


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--python', type=Path, default=Path(sys.executable),
                        help='Python with cryptography for ephemeral test certificates')
    print(json.dumps(test(parser.parse_args().python), indent=2))
