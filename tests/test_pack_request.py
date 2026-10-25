import copy
import json
from pathlib import Path
import sys
import unittest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT/'scripts'))
from check_pack_request import stack, validate_request
from check_charge_fit import evaluate


class PackRequestTests(unittest.TestCase):
    def setUp(self):
        self.request = json.loads((ROOT/'assembly/pack-r03/request.json').read_text())

    def test_unapproved_request_does_not_become_a_selected_part(self):
        validate_request(self.request)
        self.request['manufacturer_confirmed'] = True
        with self.assertRaisesRegex(ValueError, 'cannot approve'):
            validate_request(self.request)

    def test_oversize_sensor_bond_stack_is_rejected(self):
        self.request['mechanical']['ntc']['bond_thickness_budget_mm'] = .5
        with self.assertRaisesRegex(ValueError, 'exceeds'):
            validate_request(self.request)

    def test_swapped_factory_polarity_is_rejected(self):
        self.request['factory_interface'][0]['signal'] = 'GND'
        with self.assertRaisesRegex(ValueError, 'pinout changed'):
            validate_request(self.request)

    def test_original_board_height_fails_with_requested_pack(self):
        out = ROOT/'mechanical/swim-r09-pack-request'
        native, profile, params = [json.loads((out/n).read_text()) for n in
                                  ['components.native.json', 'fit-profile.json', 'parameters.json']]
        current = evaluate(native, profile, params)
        self.assertTrue(current['checked_geometry_pass'])
        old = copy.deepcopy(params)
        old['pcb']['bottom_z'] -= .4
        rejected = evaluate(native, profile, old)
        self.assertFalse(rejected['checked_geometry_pass'])
        self.assertTrue(any('battery reservation' in str(v) for v in rejected['violations']))


if __name__ == '__main__':
    unittest.main()
