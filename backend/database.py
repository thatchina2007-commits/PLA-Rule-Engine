import sqlite3
import os
import json
from datetime import datetime

DB_PATH = os.path.join(os.path.dirname(__file__), '..', 'data', 'pla_engine.db')

def get_connection():
    os.makedirs(os.path.dirname(DB_PATH), exist_ok=True)
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn

def init_db():
    conn = get_connection()
    cursor = conn.cursor()

    # Create tables
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS outputs (
        id TEXT PRIMARY KEY,
        name TEXT NOT NULL,
        description TEXT,
        color TEXT DEFAULT '#00f2fe'
    )
    ''')

    cursor.execute('''
    CREATE TABLE IF NOT EXISTS rules (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        name TEXT NOT NULL,
        expression TEXT NOT NULL,
        target_output TEXT NOT NULL,
        active INTEGER DEFAULT 1,
        description TEXT,
        priority INTEGER DEFAULT 1,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY (target_output) REFERENCES outputs(id)
    )
    ''')

    cursor.execute('''
    CREATE TABLE IF NOT EXISTS test_cases (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        title TEXT NOT NULL,
        category TEXT NOT NULL, -- 'normal' or 'edge'
        a INTEGER NOT NULL,
        b INTEGER NOT NULL,
        c INTEGER NOT NULL,
        d INTEGER NOT NULL,
        expected_json TEXT NOT NULL,
        description TEXT
    )
    ''')

    cursor.execute('''
    CREATE TABLE IF NOT EXISTS datasets (
        id TEXT PRIMARY KEY,
        name TEXT NOT NULL,
        category TEXT NOT NULL,
        data_json TEXT NOT NULL,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    )
    ''')

    cursor.execute('''
    CREATE TABLE IF NOT EXISTS audit_logs (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        action TEXT,
        details TEXT,
        timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    )
    ''')

    conn.commit()

    # Check if outputs exist, else seed
    cursor.execute('SELECT COUNT(*) FROM outputs')
    if cursor.fetchone()[0] == 0:
        seed_default_data(cursor)
        conn.commit()

    conn.close()

def seed_default_data(cursor):
    # Default Outputs
    default_outputs = [
        ('Y1', 'Output Y1 (Full Adder Sum)', 'Sum output of inputs A, B, C', '#00f2fe'),
        ('Y2', 'Output Y2 (Full Adder Carry)', 'Majority carry generation for A, B, C', '#10b981'),
        ('Y3', 'Output Y3 (Parity / Match)', 'Parity/Match flag based on input pattern', '#f59e0b'),
        ('Y4', 'Output Y4 (Safety Interlock)', 'Active interlock when A and B active without D', '#ef4444')
    ]
    cursor.executemany('INSERT INTO outputs (id, name, description, color) VALUES (?, ?, ?, ?)', default_outputs)

    # Default Rules (SOP expressions using variables A, B, C, D)
    default_rules = [
        ('FA_Sum_P1', "A'B'C", 'Y1', 1, 'Full Adder Sum Term 1: ~A ~B C', 1),
        ('FA_Sum_P2', "A'BC'", 'Y1', 1, 'Full Adder Sum Term 2: ~A B ~C', 1),
        ('FA_Sum_P3', "AB'C'", 'Y1', 1, 'Full Adder Sum Term 3: A ~B ~C', 1),
        ('FA_Sum_P4', "ABC", 'Y1', 1, 'Full Adder Sum Term 4: A B C', 1),
        ('FA_Carry_P1', "AB", 'Y2', 1, 'Full Adder Carry Term 1: A and B', 1),
        ('FA_Carry_P2', "BC", 'Y2', 1, 'Full Adder Carry Term 2: B and C', 1),
        ('FA_Carry_P3', "AC", 'Y2', 1, 'Full Adder Carry Term 3: A and C', 1),
        ('Parity_Match', "ABCD + A'B'C'D'", 'Y3', 1, 'Extreme Boundary Match (All 1s or All 0s)', 2),
        ('Interlock_Lockout', "ABD'", 'Y4', 1, 'High priority lockout: A and B high with D low', 3)
    ]
    cursor.executemany(
        'INSERT INTO rules (name, expression, target_output, active, description, priority) VALUES (?, ?, ?, ?, ?, ?)',
        default_rules
    )

    # 10 Normal Test Cases
    normal_tests = [
        ('Normal Test 1: Quiescent State', 'normal', 0, 0, 0, 0, json.dumps({'Y1': 0, 'Y2': 0, 'Y3': 1, 'Y4': 0}), 'All inputs 0; Y3 fires due to A\'B\'C\'D\' minterm'),
        ('Normal Test 2: Single Bit C High', 'normal', 0, 0, 1, 0, json.dumps({'Y1': 1, 'Y2': 0, 'Y3': 0, 'Y4': 0}), 'Only C=1 -> Sum=1, Carry=0'),
        ('Normal Test 3: Single Bit B High', 'normal', 0, 1, 0, 0, json.dumps({'Y1': 1, 'Y2': 0, 'Y3': 0, 'Y4': 0}), 'Only B=1 -> Sum=1, Carry=0'),
        ('Normal Test 4: Two Bits Active (B and C)', 'normal', 0, 1, 1, 0, json.dumps({'Y1': 0, 'Y2': 1, 'Y3': 0, 'Y4': 0}), 'B=1, C=1 -> Sum=0, Carry=1'),
        ('Normal Test 5: Single Bit A High', 'normal', 1, 0, 0, 0, json.dumps({'Y1': 1, 'Y2': 0, 'Y3': 0, 'Y4': 0}), 'Only A=1 -> Sum=1, Carry=0'),
        ('Normal Test 6: Two Bits Active (A and C)', 'normal', 1, 0, 1, 0, json.dumps({'Y1': 0, 'Y2': 1, 'Y3': 0, 'Y4': 0}), 'A=1, C=1 -> Sum=0, Carry=1'),
        ('Normal Test 7: Two Bits Active (A and B, D=0)', 'normal', 1, 1, 0, 0, json.dumps({'Y1': 0, 'Y2': 1, 'Y3': 0, 'Y4': 1}), 'A=1, B=1, D=0 -> Carry=1 and Safety Interlock Y4=1'),
        ('Normal Test 8: Two Bits Active (A and B, D=1)', 'normal', 1, 1, 0, 1, json.dumps({'Y1': 0, 'Y2': 1, 'Y3': 0, 'Y4': 0}), 'A=1, B=1, D=1 -> Carry=1, Safety Interlock suppressed by D=1'),
        ('Normal Test 9: All Three Arithmetic Active (A, B, C, D=0)', 'normal', 1, 1, 1, 0, json.dumps({'Y1': 1, 'Y2': 1, 'Y3': 0, 'Y4': 1}), 'Full Adder Sum=1, Carry=1, Interlock=1'),
        ('Normal Test 10: All Four Active (A, B, C, D)', 'normal', 1, 1, 1, 1, json.dumps({'Y1': 1, 'Y2': 1, 'Y3': 1, 'Y4': 0}), 'Sum=1, Carry=1, Parity Match Y3=1, Interlock suppressed')
    ]
    cursor.executemany(
        'INSERT INTO test_cases (title, category, a, b, c, d, expected_json, description) VALUES (?, ?, ?, ?, ?, ?, ?, ?)',
        normal_tests
    )

    # 5 Edge / Fault Test Cases
    edge_tests = [
        ('Edge Test 1: Saturation State (All Ones)', 'edge', 1, 1, 1, 1, json.dumps({'Y1': 1, 'Y2': 1, 'Y3': 1, 'Y4': 0}), 'Maximum fan-in stress test; verifies multi-output driving'),
        ('Edge Test 2: Low-Z Zero State (All Zeros)', 'edge', 0, 0, 0, 0, json.dumps({'Y1': 0, 'Y2': 0, 'Y3': 1, 'Y4': 0}), 'Ground state isolation; checks inverted rail leakage'),
        ('Edge Test 3: Interlock Threshold Transition', 'edge', 1, 1, 0, 0, json.dumps({'Y1': 0, 'Y2': 1, 'Y3': 0, 'Y4': 1}), 'Tests D\' override edge condition without intermediate state glitches'),
        ('Edge Test 4: Parity Inversion Edge (0111)', 'edge', 0, 1, 1, 1, json.dumps({'Y1': 0, 'Y2': 1, 'Y3': 0, 'Y4': 0}), 'Single 0 bit amongst 1s; ensures high-Z immunity on Y3'),
        ('Edge Test 5: Dynamic Hazard Boundary (1001)', 'edge', 1, 0, 0, 1, json.dumps({'Y1': 1, 'Y2': 0, 'Y3': 0, 'Y4': 0}), 'Boundary transition between A and D active states')
    ]
    cursor.executemany(
        'INSERT INTO test_cases (title, category, a, b, c, d, expected_json, description) VALUES (?, ?, ?, ?, ?, ?, ?, ?)',
        edge_tests
    )

    # Seed Preset Datasets
    preset_datasets = [
        ('ds_arithmetic', 'Full Adder & Subtractor Dataset', 'arithmetic', json.dumps([
            {'A': 0, 'B': 0, 'C': 0, 'D': 0, 'expected_Y1': 0, 'expected_Y2': 0, 'expected_Y3': 1, 'expected_Y4': 0},
            {'A': 0, 'B': 0, 'C': 1, 'D': 0, 'expected_Y1': 1, 'expected_Y2': 0, 'expected_Y3': 0, 'expected_Y4': 0},
            {'A': 0, 'B': 1, 'C': 0, 'D': 0, 'expected_Y1': 1, 'expected_Y2': 0, 'expected_Y3': 0, 'expected_Y4': 0},
            {'A': 0, 'B': 1, 'C': 1, 'D': 0, 'expected_Y1': 0, 'expected_Y2': 1, 'expected_Y3': 0, 'expected_Y4': 0},
            {'A': 1, 'B': 0, 'C': 0, 'D': 0, 'expected_Y1': 1, 'expected_Y2': 0, 'expected_Y3': 0, 'expected_Y4': 0},
            {'A': 1, 'B': 0, 'C': 1, 'D': 0, 'expected_Y1': 0, 'expected_Y2': 1, 'expected_Y3': 0, 'expected_Y4': 0},
            {'A': 1, 'B': 1, 'C': 0, 'D': 0, 'expected_Y1': 0, 'expected_Y2': 1, 'expected_Y3': 0, 'expected_Y4': 1},
            {'A': 1, 'B': 1, 'C': 1, 'D': 1, 'expected_Y1': 1, 'expected_Y2': 1, 'expected_Y3': 1, 'expected_Y4': 0}
        ])),
        ('ds_decoder', '2-to-4 Decoder with Active Enable', 'decoder', json.dumps([
            {'A': 0, 'B': 0, 'C': 0, 'D': 1, 'name': 'D0 Active'},
            {'A': 0, 'B': 1, 'C': 0, 'D': 1, 'name': 'D1 Active'},
            {'A': 1, 'B': 0, 'C': 0, 'D': 1, 'name': 'D2 Active'},
            {'A': 1, 'B': 1, 'C': 0, 'D': 1, 'name': 'D3 Active'}
        ]))
    ]
    cursor.executemany(
        'INSERT INTO datasets (id, name, category, data_json) VALUES (?, ?, ?, ?)',
        preset_datasets
    )

def reset_to_defaults():
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute('DROP TABLE IF EXISTS audit_logs')
    cursor.execute('DROP TABLE IF EXISTS datasets')
    cursor.execute('DROP TABLE IF EXISTS test_cases')
    cursor.execute('DROP TABLE IF EXISTS rules')
    cursor.execute('DROP TABLE IF EXISTS outputs')
    conn.commit()
    conn.close()
    init_db()
