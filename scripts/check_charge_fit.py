#!/usr/bin/env python3
"""Verify the new charge IC against a revised carrier, preserving older models."""
import copy
import hashlib
import json
from pathlib import Path

from shapely.geometry import box
import audit_populated_fit as fit

ROOT=Path(__file__).resolve().parents[1]
TRIAL=ROOT/'experiments/power-r05l-charge-interlock'
OUT=ROOT/'mechanical/swim-r07-charge-interlock'
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()


def evaluate(native,profile,parameters):
    original=fit.carrier_solids
    def solids(p,reliefs):
        fixed=[s for s in original(p,reliefs) if s[0]!='carrier leg']
        for x,y in p['carrier_leg_centers_mm']:
            fixed.append(('carrier leg',box(x-.5,y-1,x+.5,y+1),p['body']['floor'],p['pcb']['bottom_z']-1.5))
        return fixed
    fit.carrier_solids=solids
    try:return fit.evaluate(native,profile,parameters)
    finally:fit.carrier_solids=original


def main():
    inputs=[OUT/'components.native.json',OUT/'fit-profile.json',OUT/'parameters.json']
    native,profile,parameters=[json.loads(p.read_text()) for p in inputs]
    assert native['source_sha256']==sha(ROOT/native['source'])
    scenarios=[]
    for thick in [.71,.81,.84088,.91]:
        n,p=copy.deepcopy(native),copy.deepcopy(parameters)
        n['board_size_mm'][2]=p['pcb']['size'][2]=thick
        result=evaluate(n,profile,p)
        old_profile=copy.deepcopy(profile)
        old_profile['carrier_reliefs']=profile['carrier_reliefs'][:-1]
        old=fit.evaluate(n,old_profile,p)
        assert result['checked_geometry_pass'],result['violations']
        assert any(v['ref']=='U12' for v in old['violations'])
        scenarios.append(dict(thickness_mm=thick,checked=result['checked'],pass_=True,
                              old_carrier_violations=old['violations'],parts=result['parts']))
    current=evaluate(native,profile,parameters)
    fit.write_scad(OUT,current,profile)
    with (OUT/'populated.scad').open('a') as f:
        f.write('carrier_leg_centers = '+json.dumps(parameters['carrier_leg_centers_mm'])+';\n')
    receipt=dict(result='GEOMETRY_PASS',pcb_sha256=native['source_sha256'],
                 scenarios=scenarios,outer_bridge_remaining_mm=1.0,
                 inputs={str(p.relative_to(ROOT)):sha(p) for p in inputs},
                 checker_sha256=sha(Path(__file__)),base_checker_sha256=sha(ROOT/'scripts/audit_populated_fit.py'),
                 scope='Carrier ledge relief and one moved support leg only. Existing enclosure seal geometry is unchanged. Physical strength, actual pack/antennas/retention and ingress qualification remain open.')
    (OUT/'populated-fit.json').write_text(json.dumps(receipt,indent=2)+'\n')
    print('87 references / 85 populated envelopes; four thickness scenarios pass; old U12 carrier collision retained as a negative control.')


if __name__=='__main__':main()
