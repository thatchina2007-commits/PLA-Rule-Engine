import unittest
import sys
import os
import json

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'backend')))

from pla_engine import BooleanParser, QuineMcCluskey, PLAEngine
from database import init_db, get_connection, seed_default_data, reset_to_defaults
from synthetic_data import generate_random_dataset, get_preset_datasets

class TestPLAEngine(unittest.TestCase):

    def setUp(self):
        # Sample outputs
        self.outputs = [
            {'id': 'Y1', 'name': 'Sum', 'color': '#00f2fe'},
            {'id': 'Y2', 'name': 'Carry', 'color': '#10b981'},
            {'id': 'Y3', 'name': 'Parity', 'color': '#f59e0b'},
            {'id': 'Y4', 'name': 'Interlock', 'color': '#ef4444'}
        ]
        # Standard Full Adder + Interlock rules
        self.rules = [
            {'name': 'Sum1', 'expression': "A'B'C", 'target_output': 'Y1', 'active': 1},
            {'name': 'Sum2', 'expression': "A'BC'", 'target_output': 'Y1', 'active': 1},
            {'name': 'Sum3', 'expression': "AB'C'", 'target_output': 'Y1', 'active': 1},
            {'name': 'Sum4', 'expression': "ABC", 'target_output': 'Y1', 'active': 1},
            {'name': 'Carry1', 'expression': "AB", 'target_output': 'Y2', 'active': 1},
            {'name': 'Carry2', 'expression': "BC", 'target_output': 'Y2', 'active': 1},
            {'name': 'Carry3', 'expression': "AC", 'target_output': 'Y2', 'active': 1},
            {'name': 'Parity', 'expression': "ABCD + A'B'C'D'", 'target_output': 'Y3', 'active': 1},
            {'name': 'Interlock', 'expression': "ABD'", 'target_output': 'Y4', 'active': 1}
        ]
        self.engine = PLAEngine(self.rules, self.outputs)

    def test_boolean_parser(self):
        cleaned = BooleanParser.clean_expression("A AND B OR NOT C")
        self.assertEqual(cleaned, "A*B+C'")
        terms = BooleanParser.extract_product_terms("A'B + C D'")
        self.assertEqual(len(terms), 2)
        self.assertEqual(terms[0]['term_str'], "A'B")
        self.assertEqual(terms[1]['term_str'], "CD'")

    def test_full_adder_evaluation(self):
        # Test (0, 0, 0, 0): Sum=0, Carry=0, Parity=1 (A'B'C'D' matches), Interlock=0
        r0 = self.engine.evaluate_inputs(0, 0, 0, 0)
        self.assertEqual(r0['outputs']['Y1'], 0)
        self.assertEqual(r0['outputs']['Y2'], 0)
        self.assertEqual(r0['outputs']['Y3'], 1)
        self.assertEqual(r0['outputs']['Y4'], 0)

        # Test (0, 0, 1, 0): Sum=1, Carry=0, Parity=0, Interlock=0
        r1 = self.engine.evaluate_inputs(0, 0, 1, 0)
        self.assertEqual(r1['outputs']['Y1'], 1)
        self.assertEqual(r1['outputs']['Y2'], 0)
        self.assertEqual(r1['outputs']['Y3'], 0)
        self.assertEqual(r1['outputs']['Y4'], 0)

        # Test (0, 1, 1, 0): Sum=0, Carry=1, Parity=0, Interlock=0
        r3 = self.engine.evaluate_inputs(0, 1, 1, 0)
        self.assertEqual(r3['outputs']['Y1'], 0)
        self.assertEqual(r3['outputs']['Y2'], 1)

        # Test (1, 1, 1, 0): Sum=1, Carry=1, Parity=0, Interlock=1 (ABD' matches)
        r7 = self.engine.evaluate_inputs(1, 1, 1, 0)
        self.assertEqual(r7['outputs']['Y1'], 1)
        self.assertEqual(r7['outputs']['Y2'], 1)
        self.assertEqual(r7['outputs']['Y4'], 1)

    def test_truth_table_generation(self):
        tt = self.engine.generate_truth_table()
        self.assertEqual(len(tt), 16)
        # Check minterm index 0
        self.assertEqual(tt[0]['minterm'], 'm0')
        self.assertEqual(tt[0]['outputs']['Y3'], 1)

    def test_quine_mccluskey(self):
        # Minterms for majority function: 3, 5, 6, 7 (inputs B,C; A,C; A,B)
        # In 4-variable context: m3 (0011), m5 (0101), m6 (0110), m7 (0111)
        res = QuineMcCluskey.minimize([3, 5, 6, 7])
        self.assertTrue(len(res['minimal_terms']) > 0)
        # Verify minimizing single bit: m0 (0000) and m1 (0001) -> A'B'C'
        res2 = QuineMcCluskey.minimize([0, 1])
        self.assertIn("A'B'C'", res2['minimal_terms'])

    def test_conflict_detection(self):
        conflicting_rules = [
            {'name': 'R1', 'expression': "AB", 'target_output': 'Y1', 'active': 1},
            {'name': 'R2_Duplicate', 'expression': "AB", 'target_output': 'Y1', 'active': 1},
            {'name': 'R3_Subsumed', 'expression': "ABC", 'target_output': 'Y1', 'active': 1}
        ]
        test_engine = PLAEngine(conflicting_rules, self.outputs)
        report = test_engine.detect_conflicts()
        self.assertTrue(report['total_redundancies'] > 0 or report['total_conflicts'] > 0)

    def test_synthetic_data(self):
        dataset = generate_random_dataset(20, 0.2)
        self.assertEqual(len(dataset), 20)
        presets = get_preset_datasets()
        self.assertIn('arithmetic', presets)
        self.assertIn('priority_arbiter', presets)

if __name__ == '__main__':
    unittest.main()
