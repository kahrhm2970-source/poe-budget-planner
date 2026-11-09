import copy
import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path
from decimal import Decimal
from planner import plan, unique_object

BASE = {'budget_w': 120, 'reserve_percent': 20, 'poe_ports': 8,
        'devices': [{'port': 1, 'pse_w': 30, 'port_limit_w': 30}]}

class PlannerTests(unittest.TestCase):
    def test_spare_capacity(self):
        r = plan(BASE)
        self.assertEqual((r['status'], r['free_poe_ports'], r['planning_limit_w']), ('WITHIN_INPUT_LIMITS', 7, '96'))
    def test_budget_exceeded(self):
        d = copy.deepcopy(BASE); d['budget_w'] = 20
        self.assertEqual(plan(d)['status'], 'BLOCKED')
    def test_reserve_only(self):
        d = copy.deepcopy(BASE); d['budget_w'] = 35
        self.assertEqual(plan(d)['status'], 'REVIEW')
    def test_per_port_limit(self):
        d = copy.deepcopy(BASE); d['devices'][0]['pse_w'] = 31
        self.assertEqual(plan(d)['over_limit_ports'], [1])
    def test_exact_boundary(self):
        d = copy.deepcopy(BASE); d['budget_w'] = 30; d['reserve_percent'] = 0
        self.assertEqual(plan(d)['status'], 'WITHIN_INPUT_LIMITS')
    def test_decimal_boundary(self):
        d = copy.deepcopy(BASE); d['budget_w'] = Decimal('0.3'); d['reserve_percent'] = 0
        d['devices'] = [{'port': n, 'pse_w': w, 'port_limit_w': 1} for n, w in [(1, Decimal('0.1')), (2, Decimal('0.2'))]]
        self.assertEqual(plan(d)['status'], 'WITHIN_INPUT_LIMITS')
    def test_bad_numbers(self):
        for value in [True, -1, 0, float('nan'), float('inf'), '30']:
            with self.subTest(value=value), self.assertRaises(ValueError):
                d = copy.deepcopy(BASE); d['budget_w'] = value; plan(d)
    def test_invalid_ports(self):
        for value in [0, 9, True, 1.5]:
            with self.subTest(value=value), self.assertRaises(ValueError):
                d = copy.deepcopy(BASE); d['devices'][0]['port'] = value; plan(d)
    def test_duplicate_ports(self):
        d = copy.deepcopy(BASE); d['devices'] *= 2
        with self.assertRaises(ValueError): plan(d)
    def test_schema(self):
        for change in [{'extra': 1}, {'devices': []}, {'reserve_percent': 100}]:
            with self.subTest(change=change), self.assertRaises(ValueError):
                d = copy.deepcopy(BASE); d.update(change); plan(d)
    def test_duplicate_keys(self):
        with self.assertRaises(ValueError):
            json.loads('{"budget_w":1,"budget_w":2}', object_pairs_hook=unique_object)
    def test_cli_exit_codes(self):
        with tempfile.TemporaryDirectory() as folder:
            path = Path(folder) / 'input.json'
            for budget, code in [(120, 0), (20, 1)]:
                path.write_text(json.dumps(dict(BASE, budget_w=budget)), encoding='utf-8')
                r = subprocess.run([sys.executable, str(Path(__file__).with_name('planner.py')), str(path)], capture_output=True)
                self.assertEqual(r.returncode, code); json.loads(r.stdout)
            path.write_text('{}')
            r = subprocess.run([sys.executable, str(Path(__file__).with_name('planner.py')), str(path)], capture_output=True)
            self.assertEqual(r.returncode, 2)

if __name__ == '__main__': unittest.main()
