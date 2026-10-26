#!/usr/bin/env python3
"""Exercise recovery policy and actual workers with host adapters; never flash."""
import hashlib
import json
import os
from pathlib import Path
import subprocess

ROOT = Path(__file__).resolve().parents[1]
APP = ROOT/'firmware/tracker-r02'
RUNTIME = ROOT/'.runtime/tracker-r02'


def test():
    RUNTIME.mkdir(parents=True, exist_ok=True)
    inputs = sorted(p for folder in ('src', 'tests') for p in (APP/folder).rglob('*') if p.is_file())
    hashes = {str(p.relative_to(ROOT)): hashlib.sha256(p.read_bytes()).hexdigest() for p in inputs}
    env = dict(os.environ, PYTHONDONTWRITEBYTECODE='1')
    common = ['clang', '-std=c11', '-Wall', '-Wextra', '-Werror',
              '-fsanitize=address,undefined', '-g', '-pthread',
              '-I'+str(APP/'tests/host'), '-I'+str(APP/'src'), str(APP/'src/recovery.c')]
    variants = {
        'recovery': [str(APP/'tests/recovery_test.c')],
        'dns-worker': ['-DCONFIG_TRACKER_DNS_SECONDS=1', '-DCONFIG_TRACKER_PORT=443',
                       '-DCONFIG_TRACKER_HOST="test.invalid"',
                       str(APP/'src/dns.c'), str(APP/'tests/dns_worker_test.c')],
        'supervisor': [str(APP/'src/supervisor.c'), str(APP/'tests/supervisor_test.c')],
    }
    for name, args in variants.items():
        subprocess.run(common+args+['-o', str(RUNTIME/(name+'-test'))],
                       cwd=ROOT, env=env, timeout=120, check=True)
    cases = [('recovery', 'recovery', []), ('dns-worker', 'dns-worker', [])]
    cases += [(mode, 'supervisor', [mode]) for mode in
              ('expired-main', 'modem-fault', 'missing-watchdog')]
    results = []
    for case, binary, args in cases:
        result = subprocess.run([str(RUNTIME/(binary+'-test'))]+args, cwd=ROOT, env=env,
                                stdout=subprocess.PIPE, stderr=subprocess.STDOUT,
                                text=True, timeout=30)
        (RUNTIME/(case+'-tests.txt')).write_text(result.stdout)
        print(result.stdout, end='')
        result.check_returncode()
        results.append(dict(case=case, exit=result.returncode))
    for name, digest in hashes.items():
        if hashlib.sha256((ROOT/name).read_bytes()).hexdigest() != digest:
            raise ValueError('Test input changed while running: '+name)
    report = dict(result='PASS', suites=results, sanitizers=['address', 'undefined'],
                  inputs=hashes, scheduler='POSIX adapter; not the Zephyr scheduler',
                  real_dns=False, actual_modem_test=False, hardware_reset_observed=False,
                  physical_power_failure_test=False)
    (RUNTIME/'tests.json').write_text(json.dumps(report, indent=2)+'\n')
    return report


if __name__ == '__main__':
    print(json.dumps(test(), indent=2))
