"""Check internal-layer connectivity and its distinct foil-thickness assumption."""
import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'scripts'))
from audit_power_paths import make_graph, path


class PowerPathLayerTests(unittest.TestCase):
    def geometry(self):
        pads = []
        for ref, x in [('A', 0), ('B', 4)]:
            pads.append(dict(id=ref, ref=ref, pin='1', net='/TEST', layers=['F.Cu'],
                             poly=[[[x-.2,-.2],[x+.2,-.2],[x+.2,.2],[x-.2,.2]]]))
        return dict(pads=pads, tracks=[
            dict(id='left', net='/TEST', start=[0,0], end=[1,0], layer='F.Cu', width=.2),
            dict(id='inner', net='/TEST', start=[1,0], end=[3,0], layer='In2.Cu', width=.2),
            dict(id='right', net='/TEST', start=[3,0], end=[4,0], layer='F.Cu', width=.2),
        ], vias=[dict(id='v'+str(x), net='/TEST', pos=[x,0], diameter=.6, drill=.2,
                      layers=['F.Cu','In1.Cu','In2.Cu','In3.Cu','In4.Cu','B.Cu'])
                 for x in [1,3]])

    def result(self, inner_um):
        graph, terminals = make_graph(self.geometry(), '/TEST', 35, 20, .8, inner_um)
        return path(graph, terminals[('A','1')], terminals[('B','1')])

    def test_internal_signal_layer_connects_through_barrels(self):
        resistance, steps = self.result(17.5)
        self.assertIsNotNone(resistance)
        self.assertEqual(sum(s['kind']=='via' for s in steps), 2)
        self.assertTrue(any(s.get('layer')=='In2.Cu' for s in steps))

    def test_half_weight_inner_foil_doubles_only_inner_track_resistance(self):
        _, half = self.result(17.5)
        _, full = self.result(35)
        inner = lambda steps: sum(s['ohms'] for s in steps if s.get('layer')=='In2.Cu')
        other = lambda steps: sum(s['ohms'] for s in steps if s.get('layer')!='In2.Cu')
        self.assertAlmostEqual(inner(half), 2*inner(full))
        self.assertAlmostEqual(other(half), other(full))


if __name__ == '__main__':
    unittest.main()
