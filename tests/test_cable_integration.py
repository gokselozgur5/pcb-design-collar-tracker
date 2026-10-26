import copy
import json
from pathlib import Path
import sys
import unittest

sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'scripts'))
from check_cable_integration import OUT, check_rf, check_charge_pose, validate_model, old


class CableIntegrationTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.model=json.loads((OUT/'routing.json').read_text())

    def test_nominal_rf_passes_existing_lid_apertures(self):
        validate_model(self.model)
        result=check_rf(self.model,[13])
        self.assertEqual(len(result),1)
        self.assertTrue(result[0]['pass_'],result[0]['checks'])

    def test_raising_gnss_further_rejects_rf_pair_clearance(self):
        model=copy.deepcopy(self.model)
        model['poses'][13]['cables'][1]['control_points_mm'][5][2]+=.1
        result=check_rf(model,[13])[0]
        separation=next(c for c in result['checks'] if c['name']=='RF pair separation')
        self.assertFalse(separation['pass_'])
        self.assertLess(separation['value'],.2)

    def test_curved_hole_does_not_follow_a_changed_cable(self):
        model=copy.deepcopy(self.model)
        model['poses'][13]['cables'][1]['control_points_mm'][9][0]+=2
        result=check_rf(model,[13])[0]
        aperture=next(c for c in result['checks'] if c['name']=='GNSS inside own guide bores')
        self.assertFalse(aperture['pass_'])
        self.assertLess(aperture['value'],0)

    def test_upper_charge_pose_passes_but_old_rf_route_does_not(self):
        self.assertTrue(check_charge_pose(self.model,14)['pass_'])
        model=copy.deepcopy(self.model)
        model['poses'][14]['cables']=copy.deepcopy(old[14]['cables'])
        result=check_charge_pose(model,14)
        self.assertTrue(any(not c['pass_'] and 'cable' in c['name'] for c in result['checks']))

    def test_length_change_is_not_accepted_as_slack(self):
        model=copy.deepcopy(self.model)
        model['poses'][14]['charge_controls'][1][4][0]+=.4
        result=check_charge_pose(model,14)
        self.assertFalse(result['fixed_length_pass'])
        self.assertFalse(result['pass_'])

    def test_missing_pose_and_changed_physical_guide_are_rejected(self):
        model=copy.deepcopy(self.model);model['poses'].pop()
        with self.assertRaises(ValueError):validate_model(model)
        model=copy.deepcopy(self.model);model['clips'][0]['bore_diameter_mm']+=.1
        with self.assertRaises(ValueError):validate_model(model)

    def test_nonfinite_geometry_is_rejected(self):
        model=copy.deepcopy(self.model)
        model['poses'][0]['charge_controls'][0][2][0]=float('nan')
        with self.assertRaises(ValueError):validate_model(model)


if __name__=='__main__':unittest.main()
