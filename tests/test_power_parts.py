"""Discriminating checks for the selected power circuit's analytical envelope."""
import copy
import json
from pathlib import Path
import sys
import unittest

ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'scripts'))
from check_power_parts import model, divider_current


class PowerPartsTests(unittest.TestCase):
    def setUp(self):
        self.config=json.loads((ROOT/'assembly/power-parts-r01/selection.json').read_text())

    def test_undersized_reset_cap_loses_one_second_disable(self):
        self.config['capacitors']['C25']['effective_nF'][0]=100
        result=model(self.config)
        self.assertFalse(result['conditional_checks']['recognized_fault_enable_low_at_least_1s'])

    def test_early_gpio_release_is_rejected(self):
        self.config['capacitors']['C26']['effective_nF'][0]=1
        result=model(self.config)
        self.assertFalse(result['conditional_checks']['gpio_at_least_6ms_after_enable_high'])

    def test_old_600ms_firmware_wait_is_too_short(self):
        self.config['assumptions']['firmware_initial_vio_wait_s']=.6
        result=model(self.config)
        self.assertFalse(result['conditional_checks']['firmware_wait_exceeds_modeled_gpio_enable'])

    def test_heavy_enable_load_cannot_be_hidden(self):
        self.config['assumptions']['enable_and_sense_load_max_uA']=30
        with self.assertRaisesRegex(ValueError,'guaranteed HIGH'):
            model(self.config)

    def test_unloaded_network_matches_parallel_series_equivalent(self):
        # R19 and the pull-up are a series path parallel to R17, above R18.
        rt,rb,rh,rp=200000,26100,3400000,10000
        equivalent=1/(1/rt+1/(rh+rp))+rb
        self.assertAlmostEqual(divider_current(3.6,rt,rb,rh,rp),3.6/equivalent,places=14)


if __name__=='__main__':unittest.main()
