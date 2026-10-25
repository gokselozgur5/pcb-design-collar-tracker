"""Discriminating reachability controls for the read-only route proposer."""
import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'scripts'))
from raster_route import search


class RasterRouteTests(unittest.TestCase):
    def request(self, objects, end_layer=0):
        return dict(bounds=[0, 0, 4, 4], width=.2, net='/TEST', objects=objects,
                    starts=[[1, 2, 0]], ends=[[3, 2, end_layer]], state_limit=50000)

    def test_opposite_layer_can_cross_a_single_layer_barrier(self):
        barrier = ('pad', 0, '/OTHER', [1.8, 0, 2.2, 4], [1.8, 0, 2.2, 4])
        result = search(self.request([barrier]))
        self.assertEqual(result['status'], 'found')
        self.assertTrue(any(a[2] != b[2] for a, b in zip(result['points'], result['points'][1:])))
        self.assertEqual(result['points'][0], [1, 2, 0])
        self.assertEqual(result['points'][-1], [3, 2, 0])

    def test_two_layer_barrier_cannot_be_crossed(self):
        barriers = [('pad', layer, '/OTHER', [1.8, 0, 2.2, 4], [1.8, 0, 2.2, 4]) for layer in [0, 1]]
        self.assertEqual(search(self.request(barriers))['status'], 'no route')

    def test_same_net_pad_does_not_authorize_a_new_hole(self):
        pad = ('pad', 0, '/TEST', [0, 0, 4, 4], [0, 0, 4, 4])
        self.assertEqual(search(self.request([pad], end_layer=1))['status'], 'no route')

    def test_via_keepout_allows_tracks_but_prevents_layer_change(self):
        keepout = ('via_keepout', 0, '', [0, 0, 4, 4], [0, 0, 4, 4])
        self.assertEqual(search(self.request([keepout]))['status'], 'found')
        self.assertEqual(search(self.request([keepout], end_layer=1))['status'], 'no route')

    def test_extra_signal_layers_cross_outer_barriers(self):
        barriers = [('pad', layer, '/OTHER', [1.8, 0, 2.2, 4], [1.8, 0, 2.2, 4])
                    for layer in [0, 3]]
        request = self.request(barriers, end_layer=3)
        request['layer_count'] = 4
        result = search(request)
        self.assertEqual(result['status'], 'found')
        self.assertTrue(any(p[2] in [1, 2] for p in result['points']))
        self.assertEqual(result['points'][-1], [3, 2, 3])

    def test_through_via_checks_even_an_unused_signal_layer(self):
        blocker = ('pad', 2, '/OTHER', [0, 0, 4, 4], [0, 0, 4, 4])
        request = self.request([blocker], end_layer=3)
        request['layer_count'] = 4
        self.assertEqual(search(request)['status'], 'no route')

    def test_new_vias_require_a_ground_return_on_each_side_of_a_barrier(self):
        barrier = ('pad', 0, '/OTHER', [1.8,0,2.2,4], [1.8,0,2.2,4])
        request = self.request([barrier])
        request.update(via_ground_radius_mm=.5, ground_points=[[1,2]])
        self.assertEqual(search(request)['status'], 'no route')
        request['ground_points'].append([3,2])
        self.assertEqual(search(request)['status'], 'found')


if __name__ == '__main__':
    unittest.main()
