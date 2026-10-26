"""Regressions for the missing rear bearing and changed contact stack."""
import copy
import json
from pathlib import Path
import sys
import unittest

sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'scripts'))
from check_contact_retention import OUT, dimensions, evaluate
from export_contact_retention import bearing_vertices


class ContactRetention(unittest.TestCase):
    def setUp(self):self.spec=json.loads((OUT/'contact.json').read_text())
    def failures(self):return [x['name'] for x in dimensions(self.spec)['checks'] if not x['pass_']]
    def test_actual_stack(self):self.assertEqual(self.failures(),[])
    def test_old_stem_cannot_reach_new_bearing(self):
        self.spec['contact']['stem_length_mm']=7.5
        self.assertIn('shoulder cannot bottom before the terminal bears on the body',self.failures())
    def test_short_thread_cannot_engage_complete_stack(self):
        self.spec['contact']['thread_length_mm']=2.8
        self.assertIn('thread projects beyond complete maximum nut stack',self.failures())
    def test_pocket_must_not_reach_seal(self):
        self.spec['pocket']['bearing_x_mm']=23.4
        self.assertIn('pocket to inner lid-gland wall',self.failures())
    def test_sub_m3_hole_is_rejected(self):
        self.spec['terminal']['thread_hole_diameter_mm']=2.54
        self.assertIn('terminal hole clears maximum M3 thread',self.failures())
    def test_swapped_contacts_are_rejected(self):
        a,b=self.spec['polarity'];a['net'],b['net']=b['net'],a['net']
        self.assertIn('polarity follows r13 and native J3 pinout',self.failures())
    def test_old_round_stack_has_no_lateral_bearing(self):
        self.spec['terminal']['base_width_mm']=6.4
        failures=[x['name'] for x in evaluate(self.spec)['checks'] if not x['pass_']]
        self.assertTrue(any('bearing area' in x for x in failures))
    def test_bearing_validator_rejects_real_overlap(self):
        x=self.spec['pocket']['bearing_x_mm']
        bearing_vertices([[x,8,5]],self.spec)
        with self.assertRaises(ValueError):bearing_vertices([[x+.01,8,5]],self.spec)
        with self.assertRaises(ValueError):bearing_vertices([],self.spec)


if __name__=='__main__':unittest.main()
