#!/usr/bin/env python3
"""Test the production trial guard with host I/O and an accelerated test clock."""
import hashlib
import json
from pathlib import Path
import subprocess

ROOT = Path(__file__).resolve().parents[1]
APP = ROOT/'firmware/tracker-r03'
OLD = ROOT/'firmware/tracker-r02'
OUT = ROOT/'.runtime/tracker-r03'


def test():
    OUT.mkdir(parents=True, exist_ok=True)
    inputs = [APP/'src'/name for name in ('trial.c', 'trial.h', 'trial_policy.c', 'trial_policy.h')]
    inputs += [p for p in (APP/'tests').rglob('*') if p.is_file()]
    inputs += [p for p in (OLD/'tests/host').rglob('*') if p.is_file()]
    inputs += [OLD/'src/supervisor.h', OLD/'src/recovery.h']
    hashes = {str(p.relative_to(ROOT)): hashlib.sha256(p.read_bytes()).hexdigest() for p in sorted(inputs)}
    args = ['clang', '-std=c11', '-Wall', '-Wextra', '-Werror', '-g',
            '-fsanitize=address,undefined', '-pthread', '-I'+str(APP/'src'), str(APP/'src/trial_policy.c')]
    subprocess.run(args+[str(APP/'tests/trial_policy_test.c'), '-o', str(OUT/'trial-policy-test')],
                   cwd=ROOT, timeout=120, check=True)
    subprocess.run(args+['-DCONFIG_TRACKER_TRIAL_SECONDS=600', '-DCONFIG_TRACKER_TRIAL_STABLE_SECONDS=30',
                        '-I'+str(APP/'tests/host'), '-I'+str(OLD/'tests/host'), '-I'+str(OLD/'src'),
                        str(APP/'src/trial.c'), str(APP/'tests/trial_runtime_test.c'),
                        '-o', str(OUT/'trial-runtime-test')], cwd=ROOT, timeout=120, check=True)
    cases = [('policy', 'trial-policy-test', [], 0)]
    cases += [(name, 'trial-runtime-test', [name], expected) for name, expected in
              [('factory', 0), ('healthy', 0), ('missing-ack', 42),
               ('late-evidence', 42), ('confirmation-failed', 42)]]
    results = []
    for name, binary, arguments, expected in cases:
        result = subprocess.run([str(OUT/binary)]+arguments, cwd=ROOT, timeout=10,
                                capture_output=True, text=True)
        output = result.stdout+result.stderr
        (OUT/('trial-'+name+'.txt')).write_text(output)
        if result.returncode != expected or 'PASS ' not in output:
            raise ValueError(f'{name} returned {result.returncode}, expected {expected}: {output}')
        print(output, end='')
        results.append(dict(case=name, exit=result.returncode, expected_exit=expected))
    for name, digest in hashes.items():
        if hashlib.sha256((ROOT/name).read_bytes()).hexdigest() != digest:
            raise ValueError('Test input changed: '+name)
    report = dict(result='PASS', scenarios=results, inputs=hashes,
                  sanitizers=['address', 'undefined'], accelerated_trial_clock=True,
                  host_reset_sentinel=42, hardware_reset_observed=False, actual_modem_test=False)
    (OUT/'trial-tests.json').write_text(json.dumps(report, indent=2)+'\n')
    return report


if __name__ == '__main__':
    print(json.dumps(test(), indent=2))
