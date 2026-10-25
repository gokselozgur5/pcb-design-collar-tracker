"""A self-consistent summary must not bypass the saved layout acceptance rules."""
from pathlib import Path
import sys
import unittest
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'scripts'))
import verify_routing_candidate as audit


class RoutingCheckpointTests(unittest.TestCase):
    trial = ROOT / 'experiments/power-r05h-six-layer'

    def test_a_track_on_a_ground_layer_is_rejected_even_if_inventory_agrees(self):
        read = audit.read
        def altered(path):
            value = read(path)
            if path.name == 'layout-inventory.json':
                value['ground_layer_tracks'] = 1
            if path.name == 'routing-checkpoint.json':
                value['inventory']['ground_layer_tracks'] = 1
            return value
        with patch.object(audit, 'read', side_effect=altered):
            with self.assertRaisesRegex(ValueError, 'Six-layer signal/ground allocation changed'):
                audit.verify(self.trial)

    def test_old_four_layer_export_cannot_qualify_a_six_layer_board(self):
        manifest = audit.read(self.trial / 'evidence/routing-checkpoint.json')
        read = audit.read
        def altered(path):
            value = read(path)
            if path.name == 'manifest.json':
                value['copper_layers'] = ['F.Cu','In1.Cu','In2.Cu','B.Cu']
            return value
        with patch.object(audit, 'read', side_effect=altered):
            with self.assertRaisesRegex(ValueError, 'Export layer order differs'):
                audit.verify_supplier(self.trial, manifest, manifest['source_sha256'],
                    ['F.Cu','In1.Cu','In2.Cu','In3.Cu','In4.Cu','B.Cu'])


if __name__ == '__main__':
    unittest.main()
