import copy
import json
from pathlib import Path
import sys
import unittest

import numpy as np

ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'scripts'))
from check_retention_assembly import bounds_and_screens
from antenna_cable_geometry import spline, point_box_distance


class RetentionTests(unittest.TestCase):
    def setUp(self):
        self.folder=ROOT/'mechanical/swim-r10-retention'
        self.p,self.profile,self.r=[json.loads((self.folder/name).read_text()) for name in
                                    ['parameters.json','fit-profile.json','retention.json']]
        self.parts=json.loads((self.folder/'antenna-fit.json').read_text())['scenarios'][2]['parts']

    def screen(self,p=None,profile=None,r=None):
        return bounds_and_screens(p or self.p,profile or self.profile,r or self.r,self.parts)

    def test_initial_carrier_clearance_failure_is_reproduced(self):
        initial=self.folder/'evidence/initial-clearance'
        p,profile,r=[json.loads((initial/name).read_text()) for name in
                     ['parameters.json','fit-profile.json','retention.json']]
        old=self.screen(p,profile,r)['minimum_component_gaps']['U12']
        self.assertLess(old['gap_mm'],.2)
        self.assertEqual(old['obstacle'],'carrier ledge')
        self.assertGreaterEqual(self.screen()['minimum_component_gaps']['U12']['gap_mm'],.2)

    def test_missing_motion_reliefs_reject_c10_and_r29(self):
        profile=copy.deepcopy(self.profile)
        profile['carrier_reliefs']=[row for row in profile['carrier_reliefs']
                                    if not row['name'].startswith(('C10 ','R29 '))]
        old=self.screen(profile=profile)['minimum_component_gaps']
        for ref in ['C10','R29']:
            self.assertLess(old[ref]['gap_mm'],.2)

    def test_oversize_frame_cannot_be_closed_against_the_seal(self):
        r=copy.deepcopy(self.r);r['frame']['height_mm']+=.2
        result=self.screen(r=r)
        close=next(x for x in result['checks'] if x['name']=='Lid closes at assigned stack limits')
        self.assertFalse(close['pass_'])
        self.assertLess(close['minimum_gap_mm'],0)

    def test_missing_capture_tab_is_rejected(self):
        r=copy.deepcopy(self.r);r['capture_tabs_xy_mm'].pop()
        result=self.screen(r=r)
        capture=next(x for x in result['checks'] if x['name']=='Four tabs retain the smallest board')
        self.assertFalse(capture['pass_'])

    def test_old_sim_bridge_fails_the_assembled_tolerance_stack(self):
        r=copy.deepcopy(self.r);r['sim_bridge_bottom_z_mm']=10.65
        result=self.screen(r=r)
        card=next(x for x in result['checks'] if x['name']=='SIM insertion clears bridge with PCB seated')
        self.assertFalse(card['pass_'])
        self.assertAlmostEqual(card['minimum_gap_mm'],.15)

    def test_old_gnss_path_fails_when_the_board_lifts(self):
        part=next(x for x in self.parts if x['ref']=='J1')
        a,b,c,d=part['envelope_xy_bounds_mm'];z0,z1=part['envelope_z_mm']
        def gap(folder,lift):
            control=np.array(json.loads((folder/'routing-controls.json').read_text())['GNSS'])
            control[:2,2]+=lift
            xyz,_,_,step=spline(control,4001)
            return float(point_box_distance(xyz,[a,b,z0+lift],[c,d,z1+lift]).min())-.715-step/2
        self.assertLess(gap(ROOT/'mechanical/swim-r09-pack-request',.2),.2)
        self.assertGreaterEqual(gap(self.folder,11.75-11.24088),.2)


if __name__=='__main__':
    unittest.main()
