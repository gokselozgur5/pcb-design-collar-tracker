import copy
import json
from pathlib import Path
import sys
import unittest

import numpy as np

ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'scripts'))
from check_thermal_assembly import bounds_and_screens
from thermal_fit_bounds import evaluate
from thermal_cable_geometry import spline
from antenna_cable_geometry import spline as reference_spline


class ThermalTests(unittest.TestCase):
    def setUp(self):
        self.folder=ROOT/'mechanical/swim-r11-thermal-fit'
        self.p,self.profile,self.r,self.spec=[json.loads((self.folder/n).read_text()) for n in
            ['parameters.json','fit-profile.json','retention.json','thermal.json']]
        self.parts=json.loads((self.folder/'antenna-fit.json').read_text())['scenarios'][2]['parts']

    def test_r10_jams_under_the_same_declared_thermal_bounds(self):
        old=ROOT/'mechanical/swim-r10-retention'
        p,r=[json.loads((old/n).read_text()) for n in ['parameters.json','retention.json']]
        result=evaluate(p,r,self.spec,frame_material='pom')
        for name in ['Guide/PCB X','Locator/carrier X','Cavity/frame X','Lid closure']:
            row=next(c for c in result['checks'] if c['name']==name)
            self.assertFalse(row['pass_'],name)
            self.assertLess(row['minimum_mm'],0,name)
        current=evaluate(self.p,self.r,self.spec)
        self.assertTrue(all(c['pass_'] for c in current['checks']))

    def test_initial_motion_clearances_fail_before_the_reliefs(self):
        old=self.folder/'evidence/initial-motion'
        p,profile,r=[json.loads((old/n).read_text()) for n in ['parameters.json','fit-profile.json','retention.json']]
        before=bounds_and_screens(p,profile,r,self.parts)
        after=bounds_and_screens(self.p,self.profile,self.r,self.parts)
        for ref in ['C29','C33','U12']:
            self.assertLess(before['minimum_component_gaps'][ref]['gap_mm'],.2,ref)
            self.assertGreaterEqual(after['minimum_component_gaps'][ref]['gap_mm'],.2,ref)
        self.assertTrue(all(c['pass_'] for c in after['checks']))

    def test_missing_radial_key_cannot_claim_the_opposed_key_bound(self):
        r=copy.deepcopy(self.r);r['radial_keys'].pop()
        with self.assertRaisesRegex(AssertionError,'Four opposed keys'):
            evaluate(self.p,r,self.spec)

    def test_thicker_frame_prevents_lid_closure(self):
        r=copy.deepcopy(self.r);r['frame']['height_mm']+=.2
        row=next(c for c in evaluate(self.p,r,self.spec)['checks'] if c['name']=='Lid closure')
        self.assertFalse(row['pass_']);self.assertLess(row['minimum_mm'],0)

    def test_old_position_tolerance_is_not_ignored_at_keys(self):
        r=copy.deepcopy(self.r)
        for k in r['radial_keys']:
            axis=1 if k['axis']=='x' else 0
            k['slot_xy_mm'][axis]+=.025;k['slot_xy_mm'][axis+2]-=.025
        rows=[c for c in evaluate(self.p,r,self.spec)['checks'] if 'tangential fit' in c['name']]
        self.assertTrue(any(not c['pass_'] for c in rows))

    def test_missing_capture_tab_fails(self):
        r=copy.deepcopy(self.r);r['north_tabs_xy_mm'].pop()
        result=bounds_and_screens(self.p,self.profile,r,self.parts)
        self.assertFalse(next(c for c in result['checks'] if c['name']=='Four tabs overlap the guaranteed board interior')['pass_'])

    def test_vectorized_spline_matches_preserved_independent_evaluator(self):
        controls=json.loads((self.folder/'routing-controls.json').read_text())
        for name,control in controls.items():
            for actual,expected in zip(spline(control,4001),reference_spline(control,4001)):
                np.testing.assert_allclose(actual,expected,rtol=1e-10,atol=1e-10,err_msg=name)


if __name__=='__main__':
    unittest.main()
