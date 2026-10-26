"""Reject physically different staking designs that violate the assigned envelopes."""
import copy
import json
from pathlib import Path
import sys
import unittest

ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'scripts'))
from check_charge_restraint import check_pose, validate


class ChargeRestraint(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.spec=json.loads((ROOT/'assembly/internal-charge-r03/restraint.json').read_text())
        cls.model=json.loads((ROOT/cls.spec['route_source']).read_text())
        cls.wire=json.loads((ROOT/'assembly/internal-charge-r02/harness.json').read_text())
        cls.reliefs=json.loads((ROOT/'mechanical/swim-r18-charge-clearance/retainer-reliefs.json').read_text())

    def result(self,spec,index=13,reliefs=None):
        return check_pose(spec,self.model['poses'][index],self.model,self.wire,
                          self.reliefs if reliefs is None else reliefs)

    def failed(self,row,name):
        self.assertTrue(any(not x['pass_'] and name in x['name'] for x in row['checks']))

    def test_nominal_and_old_limiting_pose(self):
        validate(self.spec)
        self.assertTrue(self.result(self.spec)['pass_'])
        self.assertTrue(self.result(self.spec,6)['pass_'])

    def test_oversized_staking_hits_r6_envelope(self):
        spec=copy.deepcopy(self.spec);spec['patches'][0]['high_mm'][0]=-13.25
        self.failed(self.result(spec),'expanded components')

    def test_old_left_corner_hits_swept_retainer(self):
        spec=copy.deepcopy(self.spec);spec['patches'][0]['low_mm'][0]=-17.5
        self.failed(self.result(spec,6),'swept retention')

    def test_underfilled_block_does_not_capture_conductor(self):
        spec=copy.deepcopy(self.spec);spec['patches'][0]['high_mm'][2]=12.5
        self.failed(self.result(spec),'bare conductor cover')

    def test_terminal_staking_needs_actual_r18_reliefs(self):
        reliefs=copy.deepcopy(self.reliefs);reliefs['cuts']=[]
        self.failed(self.result(self.spec,reliefs=reliefs),'terminal swept retention')

    def test_missing_owner_and_ptfe_bond_are_not_accepted(self):
        for alter in ['owner','PTFE','release']:
            spec=copy.deepcopy(self.spec)
            if alter=='owner':spec['patches'][0]['wires']=[1]
            elif alter=='PTFE':spec['adhesion_to_PTFE_relied_on']=True
            else:spec['holding_force_qualified']=True
            with self.subTest(alter=alter),self.assertRaises(ValueError):validate(spec)


if __name__=='__main__':
    unittest.main()
