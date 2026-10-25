"""Regression checks for real dock stroke, polarity and wire-route failures."""
import json
from pathlib import Path
import sys
import unittest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'scripts'))
from check_charge_dock import OUT, evaluate


class ChargeDockTests(unittest.TestCase):
    def setUp(self):
        self.spec = json.loads((OUT / 'dock.json').read_text())

    def failures(self):
        return {c['name'] for c in evaluate(self.spec)['checks'] if not c['pass_']}

    def test_baseline_and_full_compression_corners(self):
        result = evaluate(self.spec)
        self.assertEqual(result['result'], 'CONDITIONAL_DOCK_GEOMETRY_PASS')
        self.assertGreater(result['unloaded_forward_play_bound_mm'], 2)
        self.assertFalse(any(result['qualification'].values()))

    def test_original_six_mm_dock_is_too_short(self):
        self.spec['dock']['depth'] = 6
        self.assertIn('dock covers pin and cable termination', self.failures())

    def test_old_key_cannot_prevent_early_reverse_contact(self):
        self.spec['key'].update(length=1.3, z_min=10.8)
        self.assertIn('reversed key stops before earliest conductive touch', self.failures())
        self.assertIn('reversed key overlaps solid nose in Z', self.failures())

    def test_rear_seat_too_far_back_loses_contact(self):
        self.spec['dock']['flange_back_x'] += .5
        self.assertIn('minimum operating compression', self.failures())

    def test_rear_seat_too_far_forward_bottoms_spring(self):
        self.spec['dock']['flange_back_x'] -= .5
        self.assertIn('minimum remaining spring travel', self.failures())

    def test_large_front_bore_loses_positive_flange_capture(self):
        self.spec['dock']['upper_bore_d'] = 1.95
        self.assertIn('front flange bearing width', self.failures())

    def test_shortened_wire_splay_violates_continuous_radius(self):
        self.spec['harness']['route_x'] = [42, 52]
        self.assertIn('continuous tail bend lower bound', self.failures())


if __name__ == '__main__':
    unittest.main()
