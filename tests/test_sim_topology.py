"""Topology regression: a named clamp must not hide an alternate copper path."""

import importlib.util
from pathlib import Path
import unittest

ROOT = Path(__file__).resolve().parents[1]
SPEC = importlib.util.spec_from_file_location(
    "sim_audit", ROOT / "scripts/audit_sim_topology.py"
)
AUDIT = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(AUDIT)


def pad(ident, x):
    return dict(
        id=ident,
        ref=ident,
        pin="1",
        net="/SIM",
        layers=["B.Cu"],
        pos=[x, 0],
        poly=[[[x - 0.4, -0.2], [x + 0.4, -0.2], [x + 0.4, 0.2], [x - 0.4, 0.2]]],
    )


def track(ident, start, end, layer="B.Cu"):
    return dict(id=ident, net="/SIM", start=start, end=end, layer=layer, width=0.2)


class SimTopologyTest(unittest.TestCase):
    def setUp(self):
        self.start, self.clamp, self.end = pad("J", 0), pad("D", 2), pad("U", 4)
        self.geometry = dict(
            pads=[self.start, self.clamp, self.end],
            tracks=[track("direct", [0, 0], [4, 0])],
            vias=[],
        )

    def bypasses(self):
        return AUDIT.bypasses_esd_land(self.geometry, self.clamp, self.start, self.end)

    def test_route_through_clamp(self):
        self.assertFalse(self.bypasses())

    def test_same_layer_branch_around_clamp(self):
        self.geometry["tracks"] += [
            track("a", [0, 0], [0, 1]),
            track("b", [0, 1], [4, 1]),
            track("c", [4, 1], [4, 0]),
        ]
        self.assertTrue(self.bypasses())

    def test_opposite_layer_without_vias_does_not_join(self):
        self.geometry["tracks"].append(track("other-side", [0.8, 0], [3.2, 0], "F.Cu"))
        self.assertFalse(self.bypasses())

    def test_opposite_layer_via_bypass(self):
        self.geometry["tracks"].append(track("other-side", [0.8, 0], [3.2, 0], "F.Cu"))
        self.geometry["vias"] = [
            dict(
                id=str(x), net="/SIM", pos=[x, 0], diameter=0.6, layers=["F.Cu", "B.Cu"]
            )
            for x in [0.8, 3.2]
        ]
        self.assertTrue(self.bypasses())


if __name__ == "__main__":
    unittest.main()
