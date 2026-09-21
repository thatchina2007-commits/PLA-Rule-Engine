"""
Synthetic Dataset Generators, Test Suites (10 Normal + 5 Edge Cases),
and Realistic Digital Logic Benchmarks.
"""

import random
import json
from typing import List, Dict, Any

def get_preset_datasets() -> Dict[str, Any]:
    """Returns library of comprehensive synthetic datasets for PLA testing."""
    return {
        'arithmetic': {
            'id': 'arithmetic',
            'name': 'Full Adder & Carry Generator (EC2201 Benchmark)',
            'description': '3-bit adder logic with inputs A, B (operands), C (carry-in), and D (mode selector)',
            'rules': [
                {'name': 'Sum_m1', 'expression': "A'B'C", 'target_output': 'Y1', 'description': 'Sum term m1: ~A ~B C'},
                {'name': 'Sum_m2', 'expression': "A'BC'", 'target_output': 'Y1', 'description': 'Sum term m2: ~A B ~C'},
                {'name': 'Sum_m4', 'expression': "AB'C'", 'target_output': 'Y1', 'description': 'Sum term m4: A ~B ~C'},
                {'name': 'Sum_m7', 'expression': "ABC", 'target_output': 'Y1', 'description': 'Sum term m7: A B C'},
                {'name': 'Carry_AB', 'expression': "AB", 'target_output': 'Y2', 'description': 'Carry term: A AND B'},
                {'name': 'Carry_BC', 'expression': "BC", 'target_output': 'Y2', 'description': 'Carry term: B AND C'},
                {'name': 'Carry_AC', 'expression': "AC", 'target_output': 'Y2', 'description': 'Carry term: A AND C'},
                {'name': 'Overflow_Flag', 'expression': "ABCD", 'target_output': 'Y3', 'description': 'High-order saturation condition'},
                {'name': 'Inhibit_Lockout', 'expression': "ABD'", 'target_output': 'Y4', 'description': 'Interlock lockout when mode D is 0'}
            ]
        },
        'priority_arbiter': {
            'id': 'priority_arbiter',
            'name': '4-Line Priority Arbiter & Bus Controller',
            'description': 'Resolves bus requests A (highest), B, C, D (lowest) into grant lines Y1, Y2, Y3, Y4',
            'rules': [
                {'name': 'Grant_A', 'expression': "A", 'target_output': 'Y1', 'description': 'A has highest priority grant'},
                {'name': 'Grant_B', 'expression': "A'B", 'target_output': 'Y2', 'description': 'B granted if A inactive'},
                {'name': 'Grant_C', 'expression': "A'B'C", 'target_output': 'Y3', 'description': 'C granted if A and B inactive'},
                {'name': 'Grant_D', 'expression': "A'B'C'D", 'target_output': 'Y4', 'description': 'D granted if A, B, and C inactive'}
            ]
        },
        'safety_interlock': {
            'id': 'safety_interlock',
            'name': 'Industrial Nuclear/Plant Safety Matrix',
            'description': 'Sensors: A (Temp Critical), B (Pressure High), C (Coolant Flow OK), D (Manual Override)',
            'rules': [
                {'name': 'Scram_Alarm', 'expression': "AB", 'target_output': 'Y1', 'description': 'Both Temp and Pressure critical -> Immediate SCRAM'},
                {'name': 'Coolant_Warning', 'expression': "AC'", 'target_output': 'Y2', 'description': 'Critical temp without coolant flow'},
                {'name': 'Auto_Vent', 'expression': "BC'", 'target_output': 'Y3', 'description': 'High pressure without coolant flow -> Vent valve'},
                {'name': 'Manual_Bypass', 'expression': "D", 'target_output': 'Y4', 'description': 'Operator emergency override active'}
            ]
        },
        'conflict_benchmark': {
            'id': 'conflict_benchmark',
            'name': 'Conflict & Redundancy Test Vector (For Diagnosis Testing)',
            'description': 'Contains intentional duplicate product terms and contradictory minterm overlaps',
            'rules': [
                {'name': 'Primary_AB', 'expression': "AB", 'target_output': 'Y1', 'description': 'Base activation term'},
                {'name': 'Duplicate_AB', 'expression': "AB", 'target_output': 'Y1', 'description': 'Intentional duplicate term (Redundant fuse)'},
                {'name': 'Subsumed_Term', 'expression': "ABC", 'target_output': 'Y1', 'description': 'Covered completely by AB (Absorption)'},
                {'name': 'Contradictory_Y2', 'expression': "A'B'", 'target_output': 'Y2', 'description': 'Opposite state indicator'}
            ]
        }
    }

def generate_random_dataset(num_samples: int = 32, fault_rate: float = 0.1) -> List[Dict[str, Any]]:
    """Generates synthetic dataset rows with variable combinations, labels, and faults."""
    records = []
    for i in range(num_samples):
        a = random.choice([0, 1])
        b = random.choice([0, 1])
        c = random.choice([0, 1])
        d = random.choice([0, 1])
        
        # Ground-truth Full Adder + Interlock
        sum_val = (a ^ b ^ c)
        carry_val = 1 if ((a & b) | (b & c) | (a & c)) else 0
        parity_val = 1 if ((a & b & c & d) or (not a and not b and not c and not d)) else 0
        interlock_val = 1 if (a & b & (not d)) else 0

        # Inject synthetic fault/noise if triggered
        has_fault = False
        fault_type = "None"
        if random.random() < fault_rate:
            has_fault = True
            fault_type = random.choice(["Bit Inversion", "Glitch Transient", "Floating Rail"])
            if fault_type == "Bit Inversion":
                sum_val = 1 - sum_val
            elif fault_type == "Floating Rail":
                interlock_val = 1

        records.append({
            'sample_id': f"S{i+1:03d}",
            'A': a, 'B': b, 'C': c, 'D': d,
            'expected_Y1': sum_val,
            'expected_Y2': carry_val,
            'expected_Y3': parity_val,
            'expected_Y4': interlock_val,
            'has_fault': has_fault,
            'fault_type': fault_type
        })
    return records
