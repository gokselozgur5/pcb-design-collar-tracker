"""Regressions for the actual pack/charger selection mistakes."""
import json
from pathlib import Path
import sys
import unittest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'scripts'))
from check_pack_charge import calculate, current_screen, temperature_permits


class PackChargeTests(unittest.TestCase):
    def setUp(self):
        self.spec = json.loads((ROOT / 'assembly/pack-charge-r01/inputs.json').read_text())

    def test_50C_is_not_blocked_by_the_nominally_matching_ntc(self):
        finding = calculate(self.spec)['tabulated_50C']
        self.assertTrue(finding['charging_permitted_at_all_reviewed_corners'])
        self.assertTrue(finding['exceeds_candidate_charge_max_C'])
        self.assertGreater(finding['sensitivity_ts_V'][0], .125)

    def test_short_and_open_are_not_mistaken_for_a_valid_temperature(self):
        self.assertFalse(temperature_permits(0, .115, 1.0075))
        self.assertFalse(temperature_permits(1.1, .115, 1.0075))
        self.assertTrue(temperature_permits(.38, .115, 1.0075))

    def test_bare_cell_700mA_does_not_override_pack_350mA(self):
        pack = self.spec['pack_candidate']
        self.assertGreater(pack['bare_cell_discharge_max_A'], .6)
        result = current_screen(pack, .6)
        self.assertFalse(result['continuous_pass'])
        self.assertEqual(result['continuous_A'], .35)
        self.assertFalse(result['pulse_duty_cycle_qualified'])


if __name__ == '__main__':
    unittest.main()
