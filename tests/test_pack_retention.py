"""Reject physical fit regressions in the conditional r12 pack-retention study."""
import json
from pathlib import Path
import sys
import unittest

ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'scripts'))
from check_pack_retention import evaluate


class PackRetentionTests(unittest.TestCase):
    def setUp(self):
        base=ROOT/'mechanical/swim-r11-thermal-fit'
        self.spec=json.loads((ROOT/'mechanical/swim-r12-pack-retention/pack-retention.json').read_text())
        self.parameters=json.loads((base/'parameters.json').read_text())
        self.retention=json.loads((base/'retention.json').read_text())
        self.parts=json.loads((base/'antenna-fit.json').read_text())['scenarios'][2]['parts']
        self.thermal=json.loads((base/'retention-checks.json').read_text())['thermal']
        self.thermal_spec=json.loads((base/'thermal.json').read_text())

    def result(self):
        return evaluate(self.spec,self.parameters,self.retention,self.parts,self.thermal,self.thermal_spec)

    def failing(self):
        return {c['name'] for c in self.result()['checks'] if not c['pass_']}

    def test_current_geometry_checks_all_components(self):
        r=self.result()
        self.assertEqual(r['result'],'CONDITIONAL_PACK_RETENTION_GEOMETRY_PASS')
        self.assertEqual(len(r['component_clearances']),85)
        self.assertEqual(len(r['moving_pack_clearances']),85)
        self.assertGreaterEqual(min(r['guaranteed_capture_areas_mm2']),1)
        self.assertFalse(r['physical_pack_retention_qualified'])

    def test_raised_original_floor_overfills_capture_gap(self):
        self.spec['pack_body_bottom_z_mm']=2.1
        self.spec['cradle']['platform_top_z_mm']=2.1
        self.spec['cradle']['wall_top_z_mm']=7.4
        self.assertIn('maximum pack to cap underside',self.failing())

    def test_missing_component_reliefs_hit_sim_and_capacitors(self):
        self.spec['cap']['component_reliefs_xy_mm']=[]
        self.assertIn('all 85 populated envelopes clear new solids',self.failing())

    def test_sensor_stack_must_clear_pcb_at_full_lift(self):
        # Seated-stack fit alone misses this increase: full permitted travel
        # puts the cover too near the bottom-side SIM holder.
        self.spec['ntc_stack_height_max_mm']+=.1
        self.assertIn('lifted NTC cover clears all populated envelopes',self.failing())

    def test_unconfirmed_smaller_pack_can_escape_capture_regions(self):
        self.spec['pack_body_minimum_for_capture_mm']=[29,27.5,4.8]
        self.assertTrue(any('guaranteed pack overlap' in n for n in self.failing()))

    def test_long_contact_thread_hits_cradle(self):
        self.parameters['contacts']['thread_length']=4.4
        self.assertTrue(any('cradle wall to M3 thread' in n for n in self.failing()))

    def test_north_capture_tongue_is_required(self):
        self.spec['cap']['capture_tongues_xy_mm']=[]
        self.assertIn('guaranteed pack overlap quadrant 4',self.failing())


if __name__=='__main__':
    unittest.main()
