import copy
import json
import math
from pathlib import Path
import sys
import unittest

import numpy as np

sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'scripts'))
from check_internal_harness import BASE, check, OUT
from internal_harness_geometry import evaluate, physical_radii, certify_radius
from thermal_cable_geometry import spline


class InternalHarnessTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.spec=json.loads((OUT/'harness.json').read_text())

    def test_current_nominal_route_and_terminations(self):
        result=check(self.spec)
        self.assertEqual(result['result'],'NOMINAL_ROUTE_SCREEN_PASS')
        self.assertFalse(result['manufacturing_release'])

    def test_lowered_ground_wire_hits_populated_bodies(self):
        spec=copy.deepcopy(self.spec)
        for p in spec['wires'][1]['controls_mm']:p[2]-=1
        result=check(spec)
        collision=next(c for c in result['checks'] if c['name']=='black other populated bodies')
        self.assertFalse(collision['pass_'])

    def test_polarity_swap_is_rejected(self):
        spec=copy.deepcopy(self.spec)
        spec['wires'][0]['net'],spec['wires'][1]['net']=spec['wires'][1]['net'],spec['wires'][0]['net']
        result=check(spec)
        self.assertFalse(next(c for c in result['checks'] if c['name']=='native J3 and contact polarity')['pass_'])

    def test_charge_lead_cannot_pass_through_an_rf_guide(self):
        fit=json.loads((BASE/'antenna-fit.json').read_text())['scenarios'][2]
        clip=fit['clips'][2]
        x,y,z=clip['center']
        spec=copy.deepcopy(self.spec)
        spec['wires'][1]['controls_mm']=[[x+dx,y,z] for dx in [-6,-2,2,6]]
        result=check(spec)
        found=next(c for c in result['checks'] if c['name']=='black RF guide '+clip['name'])
        self.assertFalse(found['pass_'])
        self.assertLess(found['value'],0)

    def test_original_26_awg_bend_requirement_does_not_fit(self):
        spec=copy.deepcopy(self.spec)
        spec['wire']['minimum_bend_radius_mm']=8.382
        result=check(spec)
        self.assertFalse(next(c for c in result['checks'] if c['name']=='black continuous bend radius lower bound')['pass_'])

    def test_pcb_and_pad_move_together_but_terminal_does_not(self):
        cases=json.loads((BASE/'retention-checks.json').read_text())['cable_motion']['cases']
        index=next(i for i,c in enumerate(cases) if c['pcb_pose_mm']==[.76,0,self.spec['pcb_nominal_top_mm']])
        spec=copy.deepcopy(self.spec)
        for w in spec['wires']:
            for p in w['controls_mm']:p[0]+=.76
        rows={c['name']:c for c in check(spec,pose_index=index)['checks']}
        for colour in ['red','black']:
            self.assertTrue(rows[colour+' endpoint at native pad datum']['pass_'])
            self.assertTrue(rows[colour+' bonded conductor remains on native copper']['pass_'])
            self.assertFalse(rows[colour+' endpoint at terminal-hole datum']['pass_'])

    def test_bezier_bounds_contain_independent_dense_curve(self):
        control=self.spec['wires'][1]['controls_mm']
        bounded=evaluate(control,401)
        xyz,arc,radius,_=spline(control,40001)
        self.assertLessEqual(bounded['arc_lower'][-1],arc[-1]+1e-8)
        self.assertGreaterEqual(bounded['arc_upper'][-1],arc[-1]-1e-8)
        self.assertLessEqual(bounded['radius_lower'],float(radius.min())+1e-8)
        np.testing.assert_allclose(bounded['xyz'],xyz[::100],atol=1e-12)

    def test_straight_wire_and_stationary_control(self):
        line=[[0,0,0],[3,0,0],[6,0,0],[9,0,0]]
        self.assertTrue(math.isinf(evaluate(line)['radius_lower']))
        with self.assertRaises(ValueError):evaluate([[0,0,0]]*4)

    def test_refinement_tightens_a_bound_without_using_sampled_acceptance(self):
        control=self.spec['wires'][1]['controls_mm']
        coarse=evaluate(control,41)
        self.assertLess(coarse['radius_lower'],6.604)
        bound=certify_radius(control,coarse,6.604)
        self.assertGreaterEqual(bound['radius_lower_mm'],6.604)
        self.assertGreater(bound['evaluation_points'],len(coarse['xyz']))
        dense=float(spline(control,40001)[2].min())
        self.assertLessEqual(bound['radius_lower_mm'],dense+1e-8)

    def test_strip_boundary_includes_position_and_cut_error(self):
        c=evaluate([[0,0,0],[3,0,0],[6,0,0],[9,0,0]])
        radius,bare=physical_radii(c,self.spec['wire'])
        remaining=c['arc_upper'][-1]-c['arc_upper']
        i=int(np.argmin(abs(remaining-2.2)))
        # The strip is nominally 2.4mm. A 0.1mm cut error plus 0.15mm
        # position movement can bring insulation onto this 2.2mm station.
        self.assertFalse(bare[i])
        self.assertEqual(radius[i],self.spec['wire']['outside_diameter_max_mm']/2)


if __name__=='__main__':unittest.main()
