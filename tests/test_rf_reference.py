"""Native-backed regression cases for RF reference-plane interpretation."""
import copy
import json
from pathlib import Path
import sys
import unittest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'scripts'))
from audit_rf_reference import analyze

EVIDENCE = ROOT / 'experiments/power-r05i-rf-stack/evidence'


class ReferencePlaneTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.before = json.loads((EVIDENCE/'baseline-rf-geometry.json').read_text())
        cls.after = json.loads((EVIDENCE/'rf-geometry.json').read_text())

    def test_centerline_alone_misses_original_antipad_intrusion(self):
        report = analyze(self.before)
        gnss = [t for t in report['tracks'] if t['net'] == '/GNSS_ANT']
        self.assertEqual(sum(t['unbacked_centerline_mm'] for t in gnss), 0)
        self.assertGreater(sum(t['unbacked_copper_mm2'] for t in gnss), .006)

    def test_revised_elbow_restores_full_projected_reference(self):
        report = analyze(self.after)
        self.assertEqual(report['port_route_unbacked_copper_mm2'], 0)
        self.assertEqual(report['native_contains_disagreements'], 0)
        self.assertEqual(report['matching_route_widths_mm'], [.2])
        self.assertEqual(report['rf_acceptance'], 'HOLD')

    def test_filling_holes_cannot_silently_pass(self):
        wrong = copy.deepcopy(self.after)
        wrong['zones'][0]['poly'] = [dict(outer=[[99,95],[141,95],[141,130],[99,130]], holes=[])]
        with self.assertRaisesRegex(AssertionError, 'native Contains'):
            analyze(wrong)

    def test_pad_cutout_requires_review_of_lower_power_copper(self):
        report = analyze(self.after)
        for pin in ['35', '42']:
            p = next(p for p in report['pads'] if p['ref'] == 'U1' and p['pin'] == pin)
            self.assertAlmostEqual(p['reference_overlap_fraction'], 1)
            self.assertTrue(any(t['net'] == '/VBAT' and t['clearance_mm'] == 0
                                for t in p['lower_copper_within_02mm']))


if __name__ == '__main__':
    unittest.main()
