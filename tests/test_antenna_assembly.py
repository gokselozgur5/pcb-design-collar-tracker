"""Discriminating geometry failures for the populated antenna assembly."""
import copy
import json
from pathlib import Path
import sys
import unittest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT/'scripts'))
from check_antenna_assembly import evaluate


class AntennaAssemblyTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        folder=ROOT/'mechanical/swim-r08-antennas'
        cls.inputs=[json.loads((folder/name).read_text()) for name in
                    ['components.native.json','fit-profile.json','parameters.json','routing-controls.json']]

    def result(self, change):
        n,profile,p,controls=copy.deepcopy(self.inputs)
        change(n,profile,p,controls)
        report,_,_=evaluate(n,profile,p,controls,1001)
        # Coarse sampling deliberately triggers the resolution gate, so inspect
        # the specific physical failure, never aggregate success at this density.
        return {c['name']:c for c in report['checks']}

    def test_previous_lid_height_intersects_routed_cables(self):
        checks=self.result(lambda n,f,p,c:p['body']['size'].__setitem__(2,15.1))
        self.assertFalse(checks['LTE below lid']['pass_'])
        self.assertFalse(checks['GNSS below lid']['pass_'])

    def test_same_cable_path_is_not_a_valid_two_cable_assembly(self):
        checks=self.result(lambda n,f,p,c:c.__setitem__('GNSS',copy.deepcopy(c['LTE'])))
        self.assertFalse(checks['Cable-to-cable clearance']['pass_'])
        self.assertLess(checks['Cable-to-cable clearance']['conservative_gap_mm'],0)

    def test_lowered_cable_hits_populated_board(self):
        def lower(n,f,p,c):
            for point in c['LTE']:
                point[2]-=2
        checks=self.result(lower)
        self.assertFalse(checks['LTE populated bodies']['pass_'])

    def test_own_feed_exception_does_not_hide_other_antenna(self):
        def move(n,f,p,c):
            p['antenna_reservations'][1]['center']=[0,-7,17.9]
            p['antenna_reservations'][1]['size']=[40.7,16,.4]
        checks=self.result(move)
        self.assertFalse(checks['LTE antenna bodies']['pass_'])
        other=checks['LTE antenna bodies']['rows'][1]
        self.assertFalse(other['intentional_feed_joint_excluded'])
        self.assertLess(other['conservative_gap_mm'],0)


if __name__=='__main__':
    unittest.main()
