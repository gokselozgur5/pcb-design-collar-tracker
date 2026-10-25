"""Regress actual rejected fit/seal configurations, not cosmetic CAD output."""
import copy
import json
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest

ROOT=Path(__file__).resolve().parents[1]
PARAMS=json.loads((ROOT/'mechanical/swim-r01/parameters.json').read_text())

class EnclosureChecks(unittest.TestCase):
    def run_case(self,p):
        (ROOT/'.runtime').mkdir(exist_ok=True)
        with tempfile.TemporaryDirectory(dir=ROOT/'.runtime',prefix='seal-regression-') as t:
            folder=Path(t);source=folder/'parameters.json';source.write_text(json.dumps(p))
            run=subprocess.run([sys.executable,str(ROOT/'scripts/build_swim_enclosure.py'),'--parameters',str(source),'--output',str(folder)],capture_output=True,text=True)
            return run.returncode,json.loads((folder/'checks.json').read_text())

    def test_current_declared_geometry(self):
        code,report=self.run_case(PARAMS)
        self.assertEqual(code,0)
        self.assertTrue(report['all_declared_geometry_checks_pass'])

    def test_old_contact_groove_overfills(self):
        p=copy.deepcopy(PARAMS);p['contacts']['groove_width']=2.5
        code,report=self.run_case(p)
        self.assertNotEqual(code,0)
        check=next(c for c in report['checks'] if c['name']=='Contact seal declared tolerance screen')
        self.assertFalse(check['pass_']);self.assertGreater(check['fill'][1],.85)

    def test_first_small_gland_leaves_thin_corner(self):
        p=copy.deepcopy(PARAMS);p['gland']['centerline_size']=[46.5,38.5]
        code,report=self.run_case(p)
        self.assertNotEqual(code,0)
        check=next(c for c in report['checks'] if c['name']=='Cavity-to-groove corner web')
        self.assertFalse(check['pass_']);self.assertLess(check['minimum_sampled_web_mm'],.3)

    def test_larger_cell_cannot_silently_replace_pack(self):
        p=copy.deepcopy(PARAMS);p['battery_reservation']['size']=[36,29,7]
        code,report=self.run_case(p)
        self.assertNotEqual(code,0)
        self.assertFalse(next(c for c in report['checks'] if c['name']=='Battery reservation below bottom components')['pass_'])

if __name__=='__main__':unittest.main()
