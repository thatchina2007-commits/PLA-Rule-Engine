import os
import sys
import json
import time
import io
import csv
from flask import Flask, request, jsonify, send_from_directory, Response
from flask_cors import CORS

from database import init_db, get_connection, reset_to_defaults
from pla_engine import PLAEngine, BooleanParser, QuineMcCluskey
from synthetic_data import get_preset_datasets, generate_random_dataset

# Setup directories
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
FRONTEND_DIR = os.path.abspath(os.path.join(BASE_DIR, '..', 'frontend'))

app = Flask(__name__, static_folder=FRONTEND_DIR)
CORS(app)

# Initialize database on startup
init_db()

def get_engine() -> PLAEngine:
    """Instantiates a PLAEngine from the SQLite database."""
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute('SELECT * FROM outputs ORDER BY id')
    outputs = [dict(row) for row in cursor.fetchall()]
    cursor.execute('SELECT * FROM rules ORDER BY priority DESC, id ASC')
    rules = [dict(row) for row in cursor.fetchall()]
    conn.close()
    return PLAEngine(rules, outputs)

# Static file routes for Frontend SPA
@app.route('/')
def serve_index():
    return send_from_directory(FRONTEND_DIR, 'index.html')

@app.route('/<path:path>')
def serve_static(path):
    file_path = os.path.join(FRONTEND_DIR, path)
    if os.path.exists(file_path):
        return send_from_directory(FRONTEND_DIR, path)
    return send_from_directory(FRONTEND_DIR, 'index.html')

# API Endpoints
@app.route('/api/status', methods=['GET'])
def api_status():
    return jsonify({
        'status': 'online',
        'application': 'PLA-Based Rule Engine Designer',
        'version': '2.0.0',
        'syllabus_reference': 'EC2201 Digital Principles and System Design (Unit IV: PLDs)',
        'variables': ['A', 'B', 'C', 'D'],
        'backend': 'Python Flask with SQLite, NumPy, and Pandas'
    })

@app.route('/api/rules', methods=['GET', 'POST'])
def handle_rules():
    conn = get_connection()
    cursor = conn.cursor()

    if request.method == 'GET':
        cursor.execute('SELECT * FROM rules ORDER BY priority DESC, id ASC')
        rules = [dict(row) for row in cursor.fetchall()]
        cursor.execute('SELECT * FROM outputs ORDER BY id')
        outputs = [dict(row) for row in cursor.fetchall()]
        conn.close()
        return jsonify({'rules': rules, 'outputs': outputs})

    elif request.method == 'POST':
        data = request.json or {}
        name = data.get('name', f"Rule_{int(time.time())}")
        expression = data.get('expression', '').strip()
        target_output = data.get('target_output', 'Y1')
        description = data.get('description', '')
        priority = int(data.get('priority', 1))

        if not expression:
            conn.close()
            return jsonify({'error': 'Expression cannot be empty'}), 400

        cursor.execute(
            'INSERT INTO rules (name, expression, target_output, active, description, priority) VALUES (?, ?, ?, 1, ?, ?)',
            (name, expression, target_output, description, priority)
        )
        conn.commit()
        rule_id = cursor.lastrowid
        conn.close()
        return jsonify({'message': 'Rule created successfully', 'rule_id': rule_id}), 201

@app.route('/api/rules/<int:rule_id>', methods=['PUT', 'DELETE'])
def modify_rule(rule_id):
    conn = get_connection()
    cursor = conn.cursor()

    if request.method == 'DELETE':
        cursor.execute('DELETE FROM rules WHERE id = ?', (rule_id,))
        conn.commit()
        conn.close()
        return jsonify({'message': f'Rule {rule_id} deleted'})

    elif request.method == 'PUT':
        data = request.json or {}
        cursor.execute(
            '''UPDATE rules SET name = ?, expression = ?, target_output = ?, 
               active = ?, description = ?, priority = ? WHERE id = ?''',
            (
                data.get('name'),
                data.get('expression'),
                data.get('target_output'),
                data.get('active', 1),
                data.get('description', ''),
                data.get('priority', 1),
                rule_id
            )
        )
        conn.commit()
        conn.close()
        return jsonify({'message': f'Rule {rule_id} updated'})

@app.route('/api/rules/<int:rule_id>/toggle', methods=['POST'])
def toggle_rule(rule_id):
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute('SELECT active FROM rules WHERE id = ?', (rule_id,))
    row = cursor.fetchone()
    if not row:
        conn.close()
        return jsonify({'error': 'Rule not found'}), 404
    new_active = 0 if row['active'] == 1 else 1
    cursor.execute('UPDATE rules SET active = ? WHERE id = ?', (new_active, rule_id))
    conn.commit()
    conn.close()
    return jsonify({'rule_id': rule_id, 'active': new_active})

@app.route('/api/rules/preset/<preset_id>', methods=['POST'])
def load_preset(preset_id):
    presets = get_preset_datasets()
    if preset_id not in presets:
        return jsonify({'error': 'Preset not found'}), 404

    preset_data = presets[preset_id]
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute('DELETE FROM rules') # clear current rules
    for r in preset_data['rules']:
        cursor.execute(
            'INSERT INTO rules (name, expression, target_output, active, description, priority) VALUES (?, ?, ?, 1, ?, 1)',
            (r['name'], r['expression'], r['target_output'], r.get('description', ''))
        )
    conn.commit()
    conn.close()
    return jsonify({'message': f'Loaded preset: {preset_data["name"]}'})

@app.route('/api/evaluate', methods=['POST'])
def evaluate_circuit():
    data = request.json or {}
    inputs = data.get('inputs', {})
    a = int(inputs.get('A', 0))
    b = int(inputs.get('B', 0))
    c = int(inputs.get('C', 0))
    d = int(inputs.get('D', 0))

    engine = get_engine()
    result = engine.evaluate_inputs(a, b, c, d)
    return jsonify(result)

@app.route('/api/truth-table', methods=['GET'])
def get_truth_table():
    engine = get_engine()
    table = engine.generate_truth_table()
    return jsonify({
        'truth_table': table,
        'variables': ['A', 'B', 'C', 'D'],
        'outputs': engine.output_ids,
        'product_terms': [p['term_str'] for p in engine.product_terms]
    })

@app.route('/api/product-terms', methods=['GET'])
def get_product_terms():
    engine = get_engine()
    return jsonify({
        'product_terms': engine.product_terms,
        'and_matrix': engine.and_matrix,
        'or_matrix': engine.or_matrix,
        'outputs': engine.output_ids,
        'rails': ['A', "A'", 'B', "B'", 'C', "C'", 'D', "D'"]
    })

@app.route('/api/minimize', methods=['GET', 'POST'])
def minimize_expressions():
    engine = get_engine()
    summary = engine.get_minimization_summary()
    return jsonify(summary)

@app.route('/api/conflicts', methods=['GET'])
def get_conflicts():
    engine = get_engine()
    report = engine.detect_conflicts()
    return jsonify(report)

@app.route('/api/test-cases', methods=['GET'])
def get_test_cases():
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute('SELECT * FROM test_cases ORDER BY category DESC, id ASC')
    cases = []
    for row in cursor.fetchall():
        c = dict(row)
        c['expected'] = json.loads(c['expected_json'])
        cases.append(c)
    conn.close()
    return jsonify({'test_cases': cases})

@app.route('/api/test-cases/run', methods=['POST'])
def run_test_cases():
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute('SELECT * FROM test_cases ORDER BY category DESC, id ASC')
    cases = [dict(row) for row in cursor.fetchall()]
    conn.close()

    engine = get_engine()
    results = []
    passed_count = 0
    start_time = time.perf_counter()

    for c in cases:
        expected = json.loads(c['expected_json'])
        eval_res = engine.evaluate_inputs(c['a'], c['b'], c['c'], c['d'])
        actual = eval_res['outputs']

        # Determine pass/fail
        passed = True
        diff = {}
        for out_id, exp_val in expected.items():
            act_val = actual.get(out_id, 0)
            if exp_val != act_val:
                passed = False
                diff[out_id] = {'expected': exp_val, 'actual': act_val}

        if passed:
            passed_count += 1

        results.append({
            'id': c['id'],
            'title': c['title'],
            'category': c['category'],
            'inputs': {'A': c['a'], 'B': c['b'], 'C': c['c'], 'D': c['d']},
            'expected': expected,
            'actual': actual,
            'passed': passed,
            'diff': diff,
            'description': c.get('description', '')
        })

    duration_ms = round((time.perf_counter() - start_time) * 1000, 2)
    pass_rate = round((passed_count / len(cases)) * 100, 1) if cases else 0

    return jsonify({
        'total': len(cases),
        'passed': passed_count,
        'failed': len(cases) - passed_count,
        'pass_rate': pass_rate,
        'duration_ms': duration_ms,
        'results': results
    })

@app.route('/api/analytics', methods=['GET'])
def get_analytics():
    engine = get_engine()
    table = engine.generate_truth_table()
    
    # Output frequency distribution (percentage of time each output is HIGH)
    output_freq = {}
    for out_id in engine.output_ids:
        high_count = sum(1 for r in table if r['outputs'].get(out_id, 0) == 1)
        output_freq[out_id] = {
            'high_count': high_count,
            'low_count': 16 - high_count,
            'duty_cycle': round((high_count / 16.0) * 100, 1)
        }

    # Matrix utilization
    num_terms = len(engine.product_terms)
    num_rails = 8 # A, A', B, B', C, C', D, D'
    total_and_points = num_terms * num_rails
    used_and_points = sum(sum(row) for row in engine.and_matrix) if total_and_points > 0 else 0
    and_utilization = round((used_and_points / total_and_points) * 100, 1) if total_and_points > 0 else 0

    total_or_points = len(engine.output_ids) * num_terms
    used_or_points = sum(sum(row) for row in engine.or_matrix) if total_or_points > 0 else 0
    or_utilization = round((used_or_points / total_or_points) * 100, 1) if total_or_points > 0 else 0

    # Sensitivity Analysis: Switching activity for each input variable
    sensitivity = {}
    table_by_m = {r['m_index']: r for r in table}
    for var in ['A', 'B', 'C', 'D']:
        toggles = 0
        total_transitions = 0
        bit_pos = 3 - ['A', 'B', 'C', 'D'].index(var)
        for m in range(16):
            flipped_m = m ^ (1 << bit_pos)
            if flipped_m > m:
                total_transitions += 1
                row1 = table_by_m[m]
                row2 = table_by_m[flipped_m]
                for out_id in engine.output_ids:
                    if row1['outputs'].get(out_id, 0) != row2['outputs'].get(out_id, 0):
                        toggles += 1
        sensitivity[var] = round((toggles / (total_transitions * len(engine.output_ids))) * 100, 1) if total_transitions > 0 else 0

    # Term usage distribution
    term_usage = []
    for term in engine.product_terms:
        active_minterms = sum(1 for r in table if term['id'] in r['active_terms'])
        term_usage.append({
            'id': term['id'],
            'term_str': term['term_str'],
            'outputs_connected': len(term['outputs']),
            'active_minterms': active_minterms,
            'coverage_pct': round((active_minterms / 16.0) * 100, 1)
        })

    conflicts_summary = engine.detect_conflicts()

    return jsonify({
        'total_rules': len(engine.rules),
        'active_rules': len(engine.rules),
        'product_terms_count': num_terms,
        'matrix_utilization': {
            'and_plane': and_utilization,
            'or_plane': or_utilization,
            'total_crosspoints': total_and_points + total_or_points,
            'fused_crosspoints': used_and_points + used_or_points
        },
        'output_frequencies': output_freq,
        'input_sensitivity': sensitivity,
        'term_usage': term_usage,
        'health_score': conflicts_summary['health_score'],
        'conflict_counts': {
            'conflicts': conflicts_summary['total_conflicts'],
            'redundancies': conflicts_summary['total_redundancies'],
            'warnings': conflicts_summary['total_warnings']
        }
    })

@app.route('/api/datasets/preset', methods=['GET'])
def get_datasets():
    presets = get_preset_datasets()
    return jsonify(presets)

@app.route('/api/datasets/generate', methods=['POST'])
def generate_dataset_endpoint():
    data = request.json or {}
    samples = int(data.get('samples', 32))
    fault_rate = float(data.get('fault_rate', 0.1))
    dataset = generate_random_dataset(samples, fault_rate)
    return jsonify({'records': dataset, 'count': len(dataset)})

@app.route('/api/export/csv', methods=['GET'])
def export_csv():
    target = request.args.get('target', 'truth_table')
    engine = get_engine()

    output = io.StringIO()
    writer = csv.writer(output)

    if target == 'truth_table':
        table = engine.generate_truth_table()
        headers = ['Minterm', 'A', 'B', 'C', 'D', 'Active_Product_Terms'] + [f"Output_{o}" for o in engine.output_ids]
        writer.writerow(headers)
        for row in table:
            line = [
                row['minterm'], row['A'], row['B'], row['C'], row['D'],
                ";".join(row['active_terms'])
            ] + [row['outputs'].get(o, 0) for o in engine.output_ids]
            writer.writerow(line)
        filename = "pla_truth_table.csv"

    elif target == 'test_cases':
        conn = get_connection()
        cursor = conn.cursor()
        cursor.execute('SELECT * FROM test_cases ORDER BY id')
        cases = [dict(r) for r in cursor.fetchall()]
        conn.close()
        writer.writerow(['ID', 'Title', 'Category', 'A', 'B', 'C', 'D', 'Expected_Outputs', 'Description'])
        for c in cases:
            writer.writerow([c['id'], c['title'], c['category'], c['a'], c['b'], c['c'], c['d'], c['expected_json'], c.get('description', '')])
        filename = "pla_test_cases.csv"

    else:
        dataset = generate_random_dataset(32, 0.1)
        writer.writerow(['Sample_ID', 'A', 'B', 'C', 'D', 'Y1', 'Y2', 'Y3', 'Y4', 'Has_Fault', 'Fault_Type'])
        for r in dataset:
            writer.writerow([r['sample_id'], r['A'], r['B'], r['C'], r['D'], r['expected_Y1'], r['expected_Y2'], r['expected_Y3'], r['expected_Y4'], r['has_fault'], r['fault_type']])
        filename = "pla_synthetic_dataset.csv"

    return Response(
        output.getvalue(),
        mimetype="text/csv",
        headers={"Content-Disposition": f"attachment;filename={filename}"}
    )

@app.route('/api/reset', methods=['POST'])
def reset_database():
    reset_to_defaults()
    return jsonify({'message': 'Database reset to standard EC2201 defaults'})

@app.route('/api/download/source', methods=['GET'])
def download_source():
    import zipfile
    root_dir = os.path.abspath(os.path.join(BASE_DIR, '..'))
    memory_file = io.BytesIO()
    with zipfile.ZipFile(memory_file, 'w', zipfile.ZIP_DEFLATED) as zf:
        for foldername, subfolders, filenames in os.walk(root_dir):
            if '__pycache__' in foldername or '.git' in foldername:
                continue
            for filename in filenames:
                if filename.endswith('.db-journal') or filename.endswith('.pyc'):
                    continue
                filepath = os.path.join(foldername, filename)
                arcname = os.path.relpath(filepath, root_dir)
                zf.write(filepath, arcname)
    memory_file.seek(0)
    return Response(
        memory_file.getvalue(),
        mimetype="application/zip",
        headers={"Content-Disposition": "attachment;filename=pla_rule_engine_source.zip"}
    )

@app.route('/api/download/readme', methods=['GET'])
def download_readme():
    readme_path = os.path.abspath(os.path.join(BASE_DIR, '..', 'README.md'))
    if os.path.exists(readme_path):
        with open(readme_path, 'r', encoding='utf-8') as f:
            content = f.read()
        return Response(
            content,
            mimetype="text/markdown",
            headers={"Content-Disposition": "attachment;filename=README.md"}
        )
    return jsonify({'error': 'README not found'}), 404

@app.route('/api/datasets/upload', methods=['POST'])
def upload_dataset():
    data = request.json or {}
    dataset_name = data.get('name', f"Dataset_{int(time.time())}")
    records = data.get('records', [])
    if not records:
        return jsonify({'error': 'No records provided'}), 400
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute(
        'INSERT OR REPLACE INTO datasets (id, name, category, data_json) VALUES (?, ?, ?, ?)',
        (f"custom_{int(time.time())}", dataset_name, 'custom', json.dumps(records))
    )
    conn.commit()
    conn.close()
    return jsonify({'message': f'Dataset "{dataset_name}" uploaded successfully with {len(records)} records'})

@app.route('/api/conflicts/resolve', methods=['POST'])
def auto_resolve_conflicts():
    engine = get_engine()
    report = engine.detect_conflicts()
    conn = get_connection()
    cursor = conn.cursor()
    resolved_count = 0
    # Remove duplicate rules
    for red in report['redundancies']:
        if red['type'] == 'Duplicate Product Term':
            cursor.execute('DELETE FROM rules WHERE name = ?', (red['duplicate_rule'],))
            resolved_count += 1
    # Remove identical overlap rules
    for conf in report['conflicts']:
        if conf['type'] == 'Identical Functionality Overlap':
            cursor.execute('DELETE FROM rules WHERE name = ?', (conf['rule_b'],))
            resolved_count += 1
    conn.commit()
    conn.close()
    return jsonify({'message': f'Resolved {resolved_count} conflicts/redundancies automatically', 'resolved_count': resolved_count})

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    print(f"Starting PLA Rule Engine Designer backend on http://127.0.0.1:{port}")
    app.run(host='0.0.0.0', port=port, debug=False)
