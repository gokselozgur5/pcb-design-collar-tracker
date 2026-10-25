#!/usr/bin/env python3
"""Check the r05i board at the catalog thickness interval in the saved enclosure.

Only the board thickness varies. Part-height, battery, antenna and assembly
assumptions remain those in the preserved r06 profile. No physical IP test.
"""
import argparse
import copy
import hashlib
import json
from pathlib import Path

from audit_populated_fit import evaluate

ROOT = Path(__file__).resolve().parents[1]
TRIAL = ROOT / 'experiments/power-r05i-rf-stack'
FIT = ROOT / 'mechanical/swim-r06-six-layer-fit'
sha = lambda path: hashlib.sha256(path.read_bytes()).hexdigest()


def main(trial=TRIAL):
    paths = [trial / 'evidence/components.native.json', FIT / 'fit-profile.json', FIT / 'parameters.json']
    native, profile, params = [json.loads(p.read_text()) for p in paths]
    assert sha(ROOT / native['source']) == native['source_sha256']
    results = []
    for thickness in [.71, .81, .84088, .91]:
        data, parameters = copy.deepcopy(native), copy.deepcopy(params)
        data['board_size_mm'][2] = parameters['pcb']['size'][2] = thickness
        report = evaluate(data, profile, parameters)
        original = evaluate(data, profile, parameters, reliefs=profile['carrier_reliefs'][:1])
        results.append(dict(thickness_mm=thickness, modeled_variation=True,
                            checked=report['checked'], pass_=report['checked_geometry_pass'],
                            violations=report['violations'], parts=report['parts'],
                            hardware_checks=report['hardware_checks'],
                            original_carrier_violations=original['violations']))
    result = dict(source_sha256=native['source_sha256'],
                  inputs={str(p.relative_to(ROOT)): sha(p) for p in paths},
                  checkers={str(p.relative_to(ROOT)): sha(p) for p in
                            [Path(__file__).resolve(), ROOT/'scripts/audit_populated_fit.py']},
                  scenarios=results, all_pass=all(x['pass_'] for x in results),
                  original_carrier_rejected=all(x['original_carrier_violations'] for x in results),
                  open_items=profile['open_items'],
                  scope='Analytical thickness sensitivity with board underside fixed at Z=10 mm. 0.71..0.91 mm comes from the catalog label; 0.84088 mm is the explicit CAD model. Existing component/assembly allowances retained. No material, retention, mesh, powered, RF or IP qualification.')
    (trial / 'evidence/thickness-fit.json').write_text(json.dumps(result, indent=2)+'\n')
    print(json.dumps({k: result[k] for k in ['all_pass', 'original_carrier_rejected']}))
    assert result['all_pass'] and result['original_carrier_rejected']


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--trial', type=Path, default=TRIAL)
    args = parser.parse_args()
    trial = args.trial.resolve()
    assert trial.is_relative_to(ROOT / 'experiments'), 'Keep evidence in an experiment'
    main(trial)
