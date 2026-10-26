"""Reject clamp dimensions that lose compression, fit or screw engagement."""
import copy
import json
from pathlib import Path
import sys
import unittest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT/'scripts'))
from check_dock_wire_clamp import evaluate


class ClampChecks(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.source = json.loads((ROOT/'mechanical/swim-r15-wire-clamp/dock.json').read_text())

    def changed(self, **clamp):
        spec = copy.deepcopy(self.source)
        spec['clamp'].update(clamp)
        return evaluate(spec)

    def rejected(self, result, name):
        self.assertEqual(result['result'], 'CLAMP_GEOMETRY_HOLD')
        row = next(c for c in result['checks'] if c['name'] == name)
        self.assertFalse(row['pass_'], row)

    def test_nominal_and_independent_sheet_limits(self):
        result = evaluate(self.source)
        self.assertEqual(result['result'], 'CLAMP_GEOMETRY_PASS')
        lo, hi = result['local_pad_displacement_fraction']
        self.assertLess(lo, .06)
        self.assertGreater(hi, .43)
        self.assertFalse(result['physical_retention_qualified'])

    def test_open_gap_loses_pad_contact(self):
        self.rejected(self.changed(gap=2.4), 'minimum local pad displacement')

    def test_small_gap_overcompresses_pad(self):
        self.rejected(self.changed(gap=1.5), 'maximum local pad displacement')

    def test_nominal_only_sheet_assumption_is_not_supplier_tolerance(self):
        result = self.changed(pad_thickness=.6)
        self.rejected(result, 'minimum local pad displacement')

    def test_short_screw_does_not_reach_nut(self):
        self.rejected(self.changed(screw_length=8), 'minimum axial nut overlap')

    def test_long_screw_protrudes_through_bottom(self):
        self.rejected(self.changed(screw_length=12), 'clamp screws stay above dock bottom')

    def test_clamp_cannot_shift_the_free_wire_end(self):
        self.rejected(self.changed(pad_x=[50, 56]), 'pad front defines the inherited end plane')

    def test_old_splice_location_hits_cap(self):
        self.rejected(self.changed(first_splice_x=48.5), 'splice stays beyond clamp cap')

    def test_nominal_pad_pocket_rejects_maximum_sheet_outline(self):
        self.rejected(self.changed(pad_pocket_extra=0), 'maximum incoming pad fits its pocket')

    def test_old_narrow_wire_cavity_is_not_accepted(self):
        spec = copy.deepcopy(self.source)
        spec['dock']['wire_pocket_y'] = [-10, 10]
        self.rejected(evaluate(spec), 'inherited continuous wire screen passes')


if __name__ == '__main__':
    unittest.main()
