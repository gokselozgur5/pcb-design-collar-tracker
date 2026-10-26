import copy
import json
from pathlib import Path
import sys
import unittest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT/'scripts'))
from check_charge_thermal_clearance import supplemental, validate_reliefs, BASE, OUT
from check_cable_integration import check_rf


class ChargeThermalClearanceTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.old = json.loads((BASE/'routing.json').read_text())
        cls.new = json.loads((OUT/'routing.json').read_text())
        cls.reliefs = json.loads((OUT/'retainer-reliefs.json').read_text())

    def test_old_nominal_pass_misses_thermal_component_allowance(self):
        old_report = json.loads((BASE/'checks.json').read_text())
        self.assertTrue(old_report['poses'][13]['charge']['pass_'])
        checked = supplemental(self.old, 13, self.reliefs)
        failure = next(c for c in checked['checks'] if c['name'] == 'black thermal component envelopes')
        self.assertFalse(failure['pass_'])
        self.assertEqual(failure['obstacle'], 'U3')
        self.assertLess(failure['value'], .2)

    def test_new_nominal_route_clears_expanded_envelopes(self):
        self.assertTrue(supplemental(self.new, 13, self.reliefs)['pass_'])

    def test_removing_physical_reliefs_reproduces_frame_failure(self):
        unchanged = copy.deepcopy(self.reliefs)
        unchanged['cuts'] = []
        checked = supplemental(self.new, 13, unchanged)
        self.assertTrue(any(not c['pass_'] and 'swept retention' in c['name']
                            for c in checked['checks']))

    def test_gnss_lower_turn_needs_left_guide_compensation(self):
        broken = copy.deepcopy(self.new)
        broken['poses'][13]['cables'][1]['control_points_mm'][4][2] += .2
        checked = check_rf(broken, [13])[0]
        pair = next(c for c in checked['checks'] if c['name'] == 'RF pair separation')
        self.assertFalse(pair['pass_'])

    def test_capture_tab_cannot_be_removed(self):
        broken = copy.deepcopy(self.reliefs)
        broken['cuts'][0]['xy_mm'][1] = -9
        with self.assertRaisesRegex(ValueError, 'capture tab'):
            validate_reliefs(broken)

    def test_lower_bridge_cannot_be_thinned(self):
        broken = copy.deepcopy(self.reliefs)
        broken['cuts'][0]['bottom_z_mm'] = 11.9
        with self.assertRaisesRegex(ValueError, 'lower frame bridge'):
            validate_reliefs(broken)

    def test_key_cannot_be_cut(self):
        broken = copy.deepcopy(self.reliefs)
        broken['cuts'][0]['xy_mm'][3] = .5
        with self.assertRaisesRegex(ValueError, 'radial key'):
            validate_reliefs(broken)


if __name__ == '__main__':
    unittest.main()
