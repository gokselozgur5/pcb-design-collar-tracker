"""Regressions for the previously grounded CE and unsafe hot-cell behavior."""
import copy
import json
from pathlib import Path
import sys
import unittest

sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'scripts'))
import check_charge_r05l as check


class ChargeInterlockTest(unittest.TestCase):
    def test_old_50C_failure_is_inhibited_with_corner_allowances(self):
        old=json.loads((check.ROOT/'assembly/pack-charge-r01/check.json').read_text())
        self.assertTrue(old['tabulated_50C']['charging_permitted_at_all_reviewed_corners'])
        new=check.calculate()
        self.assertFalse(new['original_50C_regression']['charge_enabled'])
        self.assertGreater(new['cell_45C_cutoff_margin_V'],0)
        self.assertGreater(new['cell_0C_cutoff_margin_V'],0)
        self.assertGreater(new['room_temperature_margin_V'],0)

    def test_restoring_grounded_ce_is_rejected(self):
        nets=json.loads((check.TRIAL/'evidence/native-netlist.json').read_text())['nets']
        check.validate_topology(nets)
        changed=copy.deepcopy(nets)
        changed['/CHARGE_DISABLE'].remove('U3.4');changed['/GND'].append('U3.4')
        with self.assertRaisesRegex(ValueError,'U3.4'):check.validate_topology(changed)

    def test_reversed_cold_comparator_is_rejected(self):
        nets=json.loads((check.TRIAL/'evidence/native-netlist.json').read_text())['nets']
        changed=copy.deepcopy(nets)
        changed['/BAT_NTC'].remove('U11.4');changed['/BAT_NTC'].append('U11.3')
        changed['/CHG_COLD_LIMIT'].remove('U11.3');changed['/CHG_COLD_LIMIT'].append('U11.4')
        with self.assertRaisesRegex(ValueError,'U11.3'):check.validate_topology(changed)

    def test_por_open_short_and_normal_logic(self):
        self.assertFalse(check.enabled(True,True,por=True))
        self.assertFalse(check.enabled(True,False))  # Open NTC: cold fault.
        self.assertFalse(check.enabled(False,True))  # Short NTC: hot fault.
        self.assertFalse(check.enabled(False,False))
        self.assertTrue(check.enabled(True,True))


if __name__=='__main__':unittest.main()
