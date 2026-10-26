"""Regressions for stretched wire, undersized cavity and unbounded bends."""
import copy
import json
import math
from pathlib import Path
import sys
import unittest

sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'scripts'))
from check_dock_wire_motion import OUT, amplitude_for, arc_length, evaluate


class DockWireMotionTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.source=json.loads((OUT/'dock.json').read_text())
        cls.result=evaluate(cls.source)

    def failures(self,s):
        return {c['name'] for c in evaluate(s)['checks'] if not c['pass_']}

    def test_nominal_and_full_motion_have_constant_length(self):
        self.assertEqual(self.result['result'],'CONDITIONAL_WIRE_GEOMETRY_PASS')
        self.assertGreater(self.result['inherited_dock']['unloaded_forward_play_bound_mm'],2)
        for pose in self.result['illustrative_poses']:
            self.assertAlmostEqual(pose['arc_length'],self.source['motion']['free_wire_length'],places=7)
        self.assertFalse(self.result['physical_qualification'])
        self.assertFalse(self.source['motion']['factory_endpoint_retention_qualified'])

    def test_straight_wire_cannot_span_forward_motion(self):
        with self.assertRaisesRegex(ValueError,'without stretching'):
            amplitude_for(31.8392,29.6971)

    def test_short_cut_fails_required_motion_reserve(self):
        s=copy.deepcopy(self.source)
        s['motion']['free_wire_length']=40.3
        self.assertIn('positive slack at longest endpoint span',self.failures(s))

    def test_shortened_span_exceeds_manufacturer_bend_limit(self):
        s=copy.deepcopy(self.source)
        s['motion']['fixed_end_x']=41
        self.assertIn('all-position continuous wire bend bound',self.failures(s))

    def test_omitting_housing_thermal_motion_fails(self):
        s=copy.deepcopy(self.source)
        s['motion']['fixed_end_thermal_allowance']=0
        self.assertIn('fixed-end thermal allowance covers housing CTE bound',self.failures(s))

    def test_omitting_wire_thermal_length_fails(self):
        s=copy.deepcopy(self.source)
        s['motion']['wire_service_length_allowance']=0
        self.assertIn('wire service allowance covers effective CTE bound',self.failures(s))

    def test_omitting_shell_movement_fails(self):
        s=copy.deepcopy(self.source)
        s['motion']['shell_clearance_allowance']=0
        self.assertIn('shell margin covers nearby feature and CTE motion',self.failures(s))

    def test_old_cavity_does_not_fit_the_loop(self):
        s=copy.deepcopy(self.source)
        s['dock']['wire_pocket_y']=[-10,10]
        self.assertIn('wire family clears cavity side',self.failures(s))

    def test_extra_wire_is_not_unconditionally_safer(self):
        s=copy.deepcopy(self.source)
        s['motion']['free_wire_length']=45
        names=self.failures(s)
        self.assertIn('all-position continuous wire bend bound',names)
        self.assertIn('wire family clears cavity side',names)

    def test_too_coarse_quadrature_cannot_claim_a_tight_bound(self):
        s=copy.deepcopy(self.source)
        s['motion']['arc_quadrature_panels']=16
        self.assertIn('quadrature allowance covers rigorous error',self.failures(s))

    def test_independent_polyline_and_curvature_at_pose_corners(self):
        # Independent 16k-segment arc summation and exact analytic curvature.
        # These are a regression cross-check, not the continuous proof itself.
        r=self.result
        for start in r['start_x_bounds']:
            for end in r['end_x_bounds']:
                for length in r['free_length_bounds']:
                    span=end-start
                    a=amplitude_for(span,length)
                    self.assertLessEqual(a,r['amplitude_upper_bound'])
                    n=16384
                    points=[(start+span*i/n,6+a*(1-math.cos(2*math.pi*i/n))/2) for i in range(n+1)]
                    measured=sum(math.dist(p,q) for p,q in zip(points,points[1:]))
                    self.assertAlmostEqual(measured,length,places=5)
                    for i in range(1001):
                        t=i/1000
                        dy=math.pi*a/span*math.sin(2*math.pi*t)
                        ddy=2*math.pi**2*a/span**2*math.cos(2*math.pi*t)
                        curvature=abs(ddy)/(1+dy*dy)**1.5
                        self.assertLessEqual(curvature,1/r['continuous_radius_lower_bound']+1e-12)

    def test_continuous_boxes_contain_sampled_corner_paths(self):
        r=self.result
        for start in r['start_x_bounds']:
            for end in r['end_x_bounds']:
                for length in r['free_length_bounds']:
                    a=amplitude_for(end-start,length)
                    for i in range(501):
                        t=i/500;x=start+(end-start)*t;y=6+a*(1-math.cos(2*math.pi*t))/2
                        self.assertTrue(any(b[0]<=x<=b[3] and b[1]<=y<=b[4] and b[2]<=5.5<=b[5]
                                            for b in r['swept_cells']))


if __name__=='__main__':unittest.main()
