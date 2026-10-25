"""Retain the actual rejected interference cases for the populated assembly."""
import importlib.util
import json
from pathlib import Path
import unittest

ROOT = Path(__file__).resolve().parents[1]
spec = importlib.util.spec_from_file_location('fit', ROOT / 'scripts/audit_populated_fit.py')
fit = importlib.util.module_from_spec(spec)
spec.loader.exec_module(fit)


class PopulatedFitTests(unittest.TestCase):
    def setUp(self):
        folder = ROOT / 'mechanical/swim-r02-fit'
        self.native = json.loads((folder / 'components.native.json').read_text())
        self.profile = json.loads((folder / 'fit-profile.json').read_text())
        self.parameters = json.loads((folder / 'parameters.json').read_text())

    def evaluate(self, **kwargs):
        return fit.evaluate(self.native, self.profile, self.parameters, **kwargs)

    def test_revised_carrier_clears_populated_board_and_backing_stack(self):
        result = self.evaluate()
        self.assertTrue(result['checked_geometry_pass'])
        self.assertEqual(result['checked'], 53)
        self.assertFalse(result['production_assembly_complete'])

    def test_original_carrier_rejects_d1_and_contacts(self):
        result = self.evaluate(reliefs=self.profile['carrier_reliefs'][:1])
        self.assertFalse(result['checked_geometry_pass'])
        self.assertIn(('D1', 'carrier ledge'), [(v['ref'], v['obstacle']) for v in result['violations']])
        self.assertTrue(any(c['obstacle'] == 'carrier ledge' and not c['pass_'] for c in result['hardware_checks']))

    def test_m4_backing_hardware_rejects_floor_and_board_clearance(self):
        self.profile['contact_retention'].update(thread_major_mm=4.0, nut_across_flats_max_mm=7.0,
                                                nut_thickness_max_mm=2.2, all_orientation_diameter_mm=8.1)
        self.parameters['contacts']['thread_major'] = 4.0
        self.parameters['contacts']['center_z'] = 5.8
        result = self.evaluate()
        self.assertFalse(result['checked_geometry_pass'])
        failed = {c['obstacle'] for c in result['hardware_checks'] if not c['pass_']}
        self.assertTrue({'floor', 'board underside'} <= failed)

    def test_taller_factory_wire_termination_hits_battery(self):
        next(p for p in self.profile['parts'] if p['ref'] == 'J4')['height_max_mm'] = 2.1
        result = self.evaluate()
        self.assertFalse(result['checked_geometry_pass'])
        self.assertIn(('J4', 'battery reservation'), [(v['ref'], v['obstacle']) for v in result['violations']])

    def test_new_tuning_population_requires_profile_update(self):
        next(p for p in self.native['parts'] if p['ref'] == 'C11')['dnp'] = False
        with self.assertRaisesRegex(AssertionError, 'DNP mismatch'):
            self.evaluate()

    def test_missing_component_is_not_silently_skipped(self):
        self.profile['parts'] = [p for p in self.profile['parts'] if p['ref'] != 'J6']
        with self.assertRaisesRegex(AssertionError, 'Incomplete fit profile'):
            self.evaluate()


if __name__ == '__main__':
    unittest.main()
