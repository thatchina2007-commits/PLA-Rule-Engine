"""
PLA Core Engine: Boolean Parser, AND/OR Matrix Compiler, Quine-McCluskey Minimizer,
Truth Table Generator, and Rule Conflict Detection.
"""

import re
import itertools
from typing import List, Dict, Tuple, Set, Any, Optional

VARIABLES = ['A', 'B', 'C', 'D']
RAILS = ['A', "A'", 'B', "B'", 'C', "C'", 'D', "D'"]

class BooleanParser:
    """Parses and normalizes Boolean algebraic expressions with variables A, B, C, D."""

    @staticmethod
    def clean_expression(expr: str) -> str:
        """Standardizes operators: NOT, AND, OR, XOR."""
        if not expr:
            return ""
        s = expr.strip()
        # Replace word operators
        s = re.sub(r'\bAND\b', '*', s, flags=re.IGNORECASE)
        s = re.sub(r'\bOR\b', '+', s, flags=re.IGNORECASE)
        s = re.sub(r'\bXOR\b', '^', s, flags=re.IGNORECASE)
        s = re.sub(r'\bNOT\s*([A-Da-d])', r"\1'", s, flags=re.IGNORECASE)
        s = re.sub(r'~([A-Da-d])', r"\1'", s)
        s = re.sub(r'!([A-Da-d])', r"\1'", s)
        s = s.upper()
        # Remove whitespace
        s = re.sub(r'\s+', '', s)
        return s

    @staticmethod
    def evaluate_minterm(expr: str, a: int, b: int, c: int, d: int) -> int:
        """Evaluates an expression for a specific 4-bit input tuple."""
        cleaned = BooleanParser.clean_expression(expr)
        if not cleaned:
            return 0
        
        # Expand XOR if present: X ^ Y -> (X*Y' + X'*Y)
        # For evaluation, we can translate to python logical expression
        val_map = {'A': bool(a), 'B': bool(b), 'C': bool(c), 'D': bool(d)}
        
        # Replace prime notation e.g. A' with (not A)
        py_expr = cleaned
        py_expr = re.sub(r"([A-D])'", r"(not \1)", py_expr)
        
        # Insert * where implicit multiplication exists: e.g. AB -> A and B, or )A -> ) and A
        # First protect already placed operators
        # Match pattern: (Var or ')') followed by (Var or '(' or 'not')
        # We can do this iteratively
        pattern = r"([A-D\)])([A-D\(]|(?:not))"
        while re.search(pattern, py_expr):
            py_expr = re.sub(pattern, r"\1 and \2", py_expr)
            
        py_expr = py_expr.replace('*', ' and ')
        py_expr = py_expr.replace('+', ' or ')
        py_expr = py_expr.replace('^', ' ^ ')

        try:
            # Safe evaluation with restricted globals/locals
            res = eval(py_expr, {"__builtins__": None}, val_map)
            return 1 if bool(res) else 0
        except Exception:
            # Fallback simple evaluation for standard SOP forms
            return BooleanParser._fallback_sop_eval(cleaned, a, b, c, d)

    @staticmethod
    def _fallback_sop_eval(cleaned: str, a: int, b: int, c: int, d: int) -> int:
        vals = {'A': a, 'B': b, 'C': c, 'D': d}
        or_terms = cleaned.split('+')
        for term in or_terms:
            term = term.strip()
            if not term:
                continue
            # Parse literals in term (e.g. A'B'C)
            literals = re.findall(r"([A-D]'?)", term)
            term_val = 1
            for lit in literals:
                var = lit[0]
                inverted = lit.endswith("'")
                expected = 0 if inverted else 1
                if vals.get(var, 0) != expected:
                    term_val = 0
                    break
            if term_val == 1:
                return 1
        return 0

    @staticmethod
    def extract_product_terms(expr: str) -> List[Dict[str, Any]]:
        """
        Extracts product terms from an SOP expression.
        Returns a list of dicts with term representation, literals, and rail connections.
        """
        cleaned = BooleanParser.clean_expression(expr)
        if not cleaned:
            return []
        
        # Split by OR '+'
        terms = [t.strip() for t in cleaned.split('+') if t.strip()]
        result = []

        for t in terms:
            # Extract literals
            literals = re.findall(r"([A-D]'?)", t)
            rail_conn = {rail: 0 for rail in RAILS}
            term_dict = {'A': None, 'B': None, 'C': None, 'D': None}
            canonical_literals = []

            for lit in literals:
                var = lit[0]
                inv = lit.endswith("'")
                term_dict[var] = 0 if inv else 1
                if inv:
                    rail_conn[f"{var}'"] = 1
                else:
                    rail_conn[var] = 1

            # Format formatted string
            parts = []
            for v in VARIABLES:
                if term_dict[v] is not None:
                    parts.append(f"{v}'" if term_dict[v] == 0 else v)
            
            term_str = "".join(parts) if parts else t
            result.append({
                'raw': t,
                'term_str': term_str,
                'vars': term_dict,
                'rails': rail_conn
            })
        return result


class QuineMcCluskey:
    """Quine-McCluskey tabular minimization algorithm for 4 variables."""

    @staticmethod
    def minimize(minterms: List[int], dont_cares: List[int] = None) -> Dict[str, Any]:
        if dont_cares is None:
            dont_cares = []
        
        if not minterms:
            return {'minimal_terms': [], 'expression': '0', 'prime_implicants': []}
        if len(minterms) + len(dont_cares) == 16:
            return {'minimal_terms': ['1'], 'expression': '1', 'prime_implicants': ['----']}

        all_terms = sorted(list(set(minterms + dont_cares)))
        
        # Group by number of 1s in 4-bit binary
        groups: Dict[int, Set[str]] = {i: set() for i in range(5)}
        for m in all_terms:
            b = f"{m:04b}"
            ones = b.count('1')
            groups[ones].add(b)

        prime_implicants = set()
        current_groups = groups

        while True:
            next_groups: Dict[int, Set[str]] = {i: set() for i in range(4)}
            combined = set()
            found_combination = False

            for i in range(4):
                group1 = current_groups.get(i, set())
                group2 = current_groups.get(i + 1, set())
                for t1 in group1:
                    for t2 in group2:
                        diff = 0
                        diff_idx = -1
                        for idx in range(4):
                            if t1[idx] != t2[idx]:
                                diff += 1
                                diff_idx = idx
                        if diff == 1:
                            new_term = t1[:diff_idx] + '-' + t1[diff_idx+1:]
                            next_groups[i].add(new_term)
                            combined.add(t1)
                            combined.add(t2)
                            found_combination = True

            for g in current_groups.values():
                for t in g:
                    if t not in combined:
                        prime_implicants.add(t)

            if not found_combination:
                break
            current_groups = next_groups

        # Prime implicant chart for essential prime implicants
        pi_list = sorted(list(prime_implicants))
        chart = {m: [] for m in minterms}
        for pi in pi_list:
            for m in minterms:
                b = f"{m:04b}"
                match = True
                for i in range(4):
                    if pi[i] != '-' and pi[i] != b[i]:
                        match = False
                        break
                if match:
                    chart[m].append(pi)

        # Find essential prime implicants
        essential = set()
        for m, pis in chart.items():
            if len(pis) == 1:
                essential.add(pis[0])

        # Covered minterms
        covered = set()
        for pi in essential:
            for m in minterms:
                b = f"{m:04b}"
                if all(pi[i] == '-' or pi[i] == b[i] for i in range(4)):
                    covered.add(m)

        remaining_minterms = set(minterms) - covered
        final_pis = set(essential)

        # Greedy set cover for remaining
        while remaining_minterms:
            best_pi = None
            best_cover_count = -1
            for pi in pi_list:
                if pi in final_pis:
                    continue
                count = sum(1 for m in remaining_minterms if all(pi[i] == '-' or pi[i] == f"{m:04b}"[i] for i in range(4)))
                if count > best_cover_count:
                    best_cover_count = count
                    best_pi = pi
            if not best_pi or best_cover_count == 0:
                break
            final_pis.add(best_pi)
            covered_by_best = {m for m in remaining_minterms if all(best_pi[i] == '-' or best_pi[i] == f"{m:04b}"[i] for i in range(4))}
            remaining_minterms -= covered_by_best

        # Convert binary strings to SOP
        sop_terms = []
        for term in sorted(list(final_pis)):
            parts = []
            for i, char in enumerate(term):
                var = VARIABLES[i]
                if char == '1':
                    parts.append(var)
                elif char == '0':
                    parts.append(f"{var}'")
            sop_terms.append("".join(parts) if parts else "1")

        return {
            'minimal_terms': sop_terms,
            'expression': " + ".join(sop_terms) if sop_terms else "0",
            'prime_implicants': list(prime_implicants),
            'essential_prime_implicants': list(essential)
        }


class PLAEngine:
    """Manages rules, AND-plane / OR-plane matrix compilation, truth tables, and conflict analysis."""

    def __init__(self, rules: List[Dict[str, Any]], outputs: List[Dict[str, Any]]):
        self.rules = [r for r in rules if r.get('active', 1)]
        self.outputs = outputs
        self.output_ids = [o['id'] for o in outputs]
        self._compile_pla()

    def _compile_pla(self):
        """Compiles unique product terms and forms AND & OR matrix crosspoints."""
        # 1. Collect all product terms across active rules
        raw_terms = []
        term_to_outputs: Dict[str, Set[str]] = {}

        for rule in self.rules:
            expr = rule['expression']
            target = rule['target_output']
            extracted = BooleanParser.extract_product_terms(expr)
            for item in extracted:
                t_str = item['term_str']
                if t_str not in term_to_outputs:
                    term_to_outputs[t_str] = set()
                    raw_terms.append(item)
                term_to_outputs[t_str].add(target)

        # Unique product terms list
        self.product_terms = []
        self.and_matrix = [] # rows = terms, cols = RAILS [A, A', B, B', C, C', D, D']
        self.or_matrix = []  # rows = outputs, cols = terms

        for i, item in enumerate(raw_terms):
            t_str = item['term_str']
            term_obj = {
                'id': f"P{i}",
                'index': i,
                'term_str': t_str,
                'vars': item['vars'],
                'rails': item['rails'],
                'outputs': list(term_to_outputs[t_str])
            }
            self.product_terms.append(term_obj)
            # AND matrix row (vector of 8 values: 0 or 1 for fuse connection)
            self.and_matrix.append([item['rails'][r] for r in RAILS])

        # OR matrix: M rows (outputs) x K cols (terms)
        for out_id in self.output_ids:
            row = []
            for term_obj in self.product_terms:
                row.append(1 if out_id in term_obj['outputs'] else 0)
            self.or_matrix.append(row)

    def evaluate_inputs(self, a: int, b: int, c: int, d: int) -> Dict[str, Any]:
        """Evaluates live input vector and returns active rails, active terms, and output logic."""
        # Rail status
        rails_status = {
            'A': a, "A'": 1 - a,
            'B': b, "B'": 1 - b,
            'C': c, "C'": 1 - c,
            'D': d, "D'": 1 - d
        }

        # AND plane: A product term is active (1) iff ALL of its fused inputs are 1.
        # If term has no connections (empty), it is inactive (0).
        active_terms = {}
        for term in self.product_terms:
            t_id = term['id']
            has_connection = False
            all_satisfied = True
            for r in RAILS:
                if term['rails'][r] == 1:
                    has_connection = True
                    if rails_status[r] != 1:
                        all_satisfied = False
                        break
            active_terms[t_id] = 1 if (has_connection and all_satisfied) else 0

        # OR plane: An output is active (1) if AT LEAST ONE connected product term is active (1)
        output_results = {}
        for out_idx, out_id in enumerate(self.output_ids):
            out_val = 0
            for term_idx, term in enumerate(self.product_terms):
                if self.or_matrix[out_idx][term_idx] == 1 and active_terms[term['id']] == 1:
                    out_val = 1
                    break
            output_results[out_id] = out_val

        return {
            'inputs': {'A': a, 'B': b, 'C': c, 'D': d},
            'rails_status': rails_status,
            'active_terms': active_terms,
            'outputs': output_results
        }

    def generate_truth_table(self) -> List[Dict[str, Any]]:
        """Generates full 16-row truth table with minterm index, binary, terms, and outputs."""
        table = []
        for m in range(16):
            a = (m >> 3) & 1
            b = (m >> 2) & 1
            c = (m >> 1) & 1
            d = (m >> 0) & 1
            eval_res = self.evaluate_inputs(a, b, c, d)
            row = {
                'minterm': f"m{m}",
                'm_index': m,
                'A': a, 'B': b, 'C': c, 'D': d,
                'binary': f"{a}{b}{c}{d}",
                'active_terms': [tid for tid, act in eval_res['active_terms'].items() if act == 1],
                'outputs': eval_res['outputs']
            }
            table.append(row)
        return table

    def detect_conflicts(self) -> Dict[str, Any]:
        """
        Detects rule conflicts, redundancies, contradictions, and don't care hazards.
        """
        conflicts = []
        redundancies = []
        warnings = []

        # 1. Check for Duplicate or Redundant Product Terms across rules
        term_map = {}
        for rule in self.rules:
            extracted = BooleanParser.extract_product_terms(rule['expression'])
            for item in extracted:
                t_str = item['term_str']
                if t_str in term_map:
                    redundancies.append({
                        'type': 'Duplicate Product Term',
                        'severity': 'Warning',
                        'term': t_str,
                        'first_rule': term_map[t_str]['rule_name'],
                        'duplicate_rule': rule['name'],
                        'suggestion': f"Product term '{t_str}' is already generated. In a PLA, this AND gate term can be shared across outputs rather than duplicated."
                    })
                else:
                    term_map[t_str] = {'rule_name': rule['name'], 'output': rule['target_output']}

        # 2. Check for Contradictory Outputs across identical input states
        # E.g., If rule says Y1 = A and another rule or inhibit rule declares contradictory intention
        truth_table = self.generate_truth_table()

        # Check for minterm coverage per rule to detect overlapping/contradictory assertions
        rule_minterm_map = {}
        for rule in self.rules:
            mts = set()
            for m in range(16):
                a = (m >> 3) & 1
                b = (m >> 2) & 1
                c = (m >> 1) & 1
                d = (m >> 0) & 1
                if BooleanParser.evaluate_minterm(rule['expression'], a, b, c, d) == 1:
                    mts.add(m)
            rule_minterm_map[rule['name']] = {'output': rule['target_output'], 'minterms': mts, 'priority': rule.get('priority', 1)}

        # Detect Subsumption / Absorption: e.g. Rule A covers Rule AB
        rule_names = list(rule_minterm_map.keys())
        for i in range(len(rule_names)):
            for j in range(i + 1, len(rule_names)):
                r1, r2 = rule_names[i], rule_names[j]
                m1 = rule_minterm_map[r1]['minterms']
                m2 = rule_minterm_map[r2]['minterms']
                out1 = rule_minterm_map[r1]['output']
                out2 = rule_minterm_map[r2]['output']

                if out1 == out2 and m1 and m2:
                    if m1 == m2:
                        conflicts.append({
                            'type': 'Identical Functionality Overlap',
                            'severity': 'Warning',
                            'rule_a': r1,
                            'rule_b': r2,
                            'output': out1,
                            'overlapping_minterms': list(sorted(m1)),
                            'suggestion': f"Rules '{r1}' and '{r2}' cover the exact same minterms for {out1}. Combine or remove one."
                        })
                    elif m1.issubset(m2):
                        redundancies.append({
                            'type': 'Absorption Redundancy (Subsumption)',
                            'severity': 'Info',
                            'smaller_rule': r1,
                            'larger_rule': r2,
                            'output': out1,
                            'suggestion': f"Rule '{r2}' completely covers the conditions of '{r1}'. '{r1}' is redundant in SOP."
                        })
                    elif m2.issubset(m1):
                        redundancies.append({
                            'type': 'Absorption Redundancy (Subsumption)',
                            'severity': 'Info',
                            'smaller_rule': r2,
                            'larger_rule': r1,
                            'output': out1,
                            'suggestion': f"Rule '{r1}' completely covers the conditions of '{r2}'. '{r2}' is redundant in SOP."
                        })

        # 3. Check for Interlock / Mutually Exclusive Conflicts (e.g. Y1 Sum and Y4 Interlock active together)
        for row in truth_table:
            active_outs = [k for k, v in row['outputs'].items() if v == 1]
            if 'Y4' in active_outs and 'Y1' in active_outs:
                # Flag potential safety hazard if safety interlock is high while operational sum is high
                warnings.append({
                    'type': 'Concurrent Safety Interlock & Data Operation',
                    'severity': 'Notice',
                    'minterm': row['minterm'],
                    'binary': row['binary'],
                    'active_outputs': active_outs,
                    'suggestion': f"At input {row['binary']} ({row['minterm']}), Emergency Interlock (Y4) fires alongside operational output (Y1). In high-reliability logic, ensure output muting is implemented."
                })
                break # Report first instance to keep report clean

        # Calculate Logic Health Score
        total_issues = len(conflicts) + len(redundancies)
        health_score = max(0, 100 - (len(conflicts) * 15 + len(redundancies) * 5))

        return {
            'total_conflicts': len(conflicts),
            'total_redundancies': len(redundancies),
            'total_warnings': len(warnings),
            'health_score': health_score,
            'conflicts': conflicts,
            'redundancies': redundancies,
            'warnings': warnings
        }

    def get_minimization_summary(self) -> Dict[str, Any]:
        """Runs Quine-McCluskey minimization for each configured output."""
        results = {}
        truth_table = self.generate_truth_table()

        for out_id in self.output_ids:
            minterms = [row['m_index'] for row in truth_table if row['outputs'].get(out_id, 0) == 1]
            qm_res = QuineMcCluskey.minimize(minterms)
            results[out_id] = {
                'original_terms_count': sum(1 for p in self.product_terms if out_id in p['outputs']),
                'minterms': minterms,
                'minimized_terms': qm_res['minimal_terms'],
                'minimized_expression': qm_res['expression'],
                'prime_implicants': qm_res['prime_implicants']
            }
        return results
