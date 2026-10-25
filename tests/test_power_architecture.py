"""Guard against turning incomplete or mismatched power evidence into acceptance."""
import copy
from pathlib import Path
import sys
import unittest
from unittest.mock import patch

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'scripts'))
import audit_power_architecture as audit


class PowerEvidenceTests(unittest.TestCase):
    def test_existing_board_reproduces_three_open_findings(self):
        result = audit.review()
        self.assertEqual(result['status'], 'HOLD')
        self.assertEqual([f['id'] for f in result['findings']],
                         ['PWR-01', 'PWR-02', 'PWR-03'])
        self.assertLess(result['findings'][0]['illustrative_nrf_V_without_component_losses'], 3.0)
        self.assertEqual(audit.verify_saved()['electrical_acceptance'], 'HOLD')

    def test_mismatched_ldo_enable_pad_is_rejected(self):
        original = audit.read

        def changed(path):
            data = copy.deepcopy(original(path))
            if path.name == 'route-geometry.json':
                for pad in data['pads']:
                    if pad['ref'] == 'U4' and pad['pin'] == '3':
                        pad['net'] = '/UNREVIEWED_ENABLE'
            return data

        with patch.object(audit, 'read', side_effect=changed):
            with self.assertRaisesRegex(ValueError, 'power pin mismatch: U4.3'):
                audit.review()

    def test_added_enable_control_requires_a_new_review(self):
        original = audit.read

        def changed(path):
            data = copy.deepcopy(original(path))
            if path.name == 'native-power.json':
                data['nets']['/NRF_ENABLE'].append('U6.1')
            return data

        with patch.object(audit, 'read', side_effect=changed):
            with self.assertRaisesRegex(ValueError, 'Power topology changed'):
                audit.review()


if __name__ == '__main__':
    unittest.main()
