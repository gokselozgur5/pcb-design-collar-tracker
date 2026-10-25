"""Reject unsafe regressions in the new power candidate, without claiming bench proof."""
import copy
import importlib.util
import json
from pathlib import Path
import unittest

ROOT = Path(__file__).resolve().parents[1]
spec = importlib.util.spec_from_file_location('power_r05', ROOT / 'scripts/check_power_r05.py')
power = importlib.util.module_from_spec(spec)
spec.loader.exec_module(power)


class PowerR05Test(unittest.TestCase):
    def setUp(self):
        self.old = power.read(ROOT / 'evidence/power-review-r04i/native-power.json')
        self.new = power.read(power.TRIAL / 'evidence/native-netlist.json')
        self.inputs = power.read(power.TRIAL / 'evidence/timing-inputs.json')

    def move(self, pin, net):
        for pins in self.new['nets'].values():
            if pin in pins:
                pins.remove(pin)
        self.new['nets'].setdefault(net, []).append(pin)

    def test_native_candidate_retains_unrelated_connections(self):
        result = power.check_topology(self.old, self.new)
        self.assertEqual(result['unchanged_connected_existing_pins'], 205)
        self.assertEqual(set(result['existing_changes']), {'R1.1', 'U4.3', 'U1.73'})

    def test_restoring_always_on_gpio_supply_is_rejected(self):
        self.move('U4.3', '/VSYS')
        with self.assertRaisesRegex(ValueError, 'existing connection: U4.3'):
            power.check_topology(self.old, self.new)

    def test_battery_pullup_on_gpio_is_rejected(self):
        self.move('R23.1', '/VBAT')
        with self.assertRaisesRegex(ValueError, 'power/interface pin: R23.1'):
            power.check_topology(self.old, self.new)

    def test_reversed_fet_source_is_rejected(self):
        self.move('Q1.1', '/VIO_1V8')
        with self.assertRaisesRegex(ValueError, 'power/interface pin: Q1.1'):
            power.check_topology(self.old, self.new)

    def test_short_restart_delay_is_rejected(self):
        self.inputs['restart_cap_effective_nF'] = [47, 60]
        with self.assertRaisesRegex(ValueError, 'Conditional design bound failed'):
            power.timing(self.inputs)

    def test_old_enable_cap_cannot_supply_shutdown_time(self):
        self.inputs['enable_cap_effective_uF'] = [.06, .1265]
        with self.assertRaisesRegex(ValueError, 'Conditional design bound failed'):
            power.timing(self.inputs)

    def test_calculations_keep_their_unqualified_status(self):
        result = power.verify()
        self.assertEqual(result['electrical_acceptance'], 'HOLD')
        self.assertFalse(result['physical_test'])
        self.assertTrue(result['unqualified'])
        self.assertGreater(result['analysis']['bounds']['enable_low_hold_min_s'], 1)


if __name__ == '__main__':
    unittest.main()
