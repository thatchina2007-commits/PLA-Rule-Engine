/**
 * PLA Core Engine - Client-side Logic Mirror
 * Provides instantaneous offline execution of Boolean parsing, PLA matrix compilation,
 * Quine-McCluskey minimization, truth tables, and conflict detection.
 */

class PLACore {
  static VARIABLES = ['A', 'B', 'C', 'D'];
  static RAILS = ['A', "A'", 'B', "B'", 'C', "C'", 'D', "D'"];

  static cleanExpression(expr) {
    if (!expr) return "";
    let s = expr.trim();
    s = s.replace(/\bAND\b/gi, '*');
    s = s.replace(/\bOR\b/gi, '+');
    s = s.replace(/\bXOR\b/gi, '^');
    s = s.replace(/\bNOT\s*([A-Da-d])/gi, "$1'");
    s = s.replace(/~([A-Da-d])/g, "$1'");
    s = s.replace(/!([A-Da-d])/g, "$1'");
    s = s.toUpperCase();
    s = s.replace(/\s+/g, '');
    return s;
  }

  static evaluateMinterm(expr, a, b, c, d) {
    const cleaned = this.cleanExpression(expr);
    if (!cleaned) return 0;
    const vals = { A: a, B: b, C: c, D: d };

    // Standard SOP evaluate
    const orTerms = cleaned.split('+');
    for (let term of orTerms) {
      term = term.trim();
      if (!term) continue;
      // Extract literals: e.g. A'B'C
      const regex = /([A-D]'?)/g;
      let match;
      let termVal = 1;
      let hasLiterals = false;

      while ((match = regex.exec(term)) !== null) {
        hasLiterals = true;
        const lit = match[1];
        const v = lit[0];
        const inv = lit.endsWith("'");
        const exp = inv ? 0 : 1;
        if (vals[v] !== exp) {
          termVal = 0;
          break;
        }
      }

      if (hasLiterals && termVal === 1) return 1;
    }
    return 0;
  }

  static extractProductTerms(expr) {
    const cleaned = this.cleanExpression(expr);
    if (!cleaned) return [];
    const orTerms = cleaned.split('+').filter(t => t.trim().length > 0);
    const result = [];

    for (let t of orTerms) {
      const literals = t.match(/[A-D]'?/g) || [];
      const railConn = {};
      this.RAILS.forEach(r => railConn[r] = 0);
      const vars = { A: null, B: null, C: null, D: null };

      for (let lit of literals) {
        const v = lit[0];
        const inv = lit.endsWith("'");
        vars[v] = inv ? 0 : 1;
        if (inv) railConn[`${v}'`] = 1;
        else railConn[v] = 1;
      }

      const parts = [];
      for (let v of this.VARIABLES) {
        if (vars[v] !== null) {
          parts.push(vars[v] === 0 ? `${v}'` : v);
        }
      }
      const termStr = parts.length > 0 ? parts.join('') : t;
      result.push({
        raw: t,
        term_str: termStr,
        vars: vars,
        rails: railConn
      });
    }
    return result;
  }

  static compilePLA(rules, outputs) {
    const activeRules = rules.filter(r => r.active !== 0);
    const outputIds = outputs.map(o => o.id);
    const rawTerms = [];
    const termToOutputs = {};

    for (let rule of activeRules) {
      const extracted = this.extractProductTerms(rule.expression);
      for (let item of extracted) {
        const tStr = item.term_str;
        if (!termToOutputs[tStr]) {
          termToOutputs[tStr] = new Set();
          rawTerms.push(item);
        }
        termToOutputs[tStr].add(rule.target_output);
      }
    }

    const productTerms = [];
    const andMatrix = [];
    const orMatrix = [];

    rawTerms.forEach((item, idx) => {
      const tStr = item.term_str;
      const termObj = {
        id: `P${idx}`,
        index: idx,
        term_str: tStr,
        vars: item.vars,
        rails: item.rails,
        outputs: Array.from(termToOutputs[tStr])
      };
      productTerms.push(termObj);
      andMatrix.push(this.RAILS.map(r => item.rails[r] || 0));
    });

    outputIds.forEach(outId => {
      const row = productTerms.map(t => t.outputs.includes(outId) ? 1 : 0);
      orMatrix.push(row);
    });

    return {
      rules: activeRules,
      outputs: outputs,
      outputIds: outputIds,
      productTerms: productTerms,
      andMatrix: andMatrix,
      orMatrix: orMatrix
    };
  }

  static evaluate(compiled, a, b, c, d) {
    const railsStatus = {
      'A': a, "A'": 1 - a,
      'B': b, "B'": 1 - b,
      'C': c, "C'": 1 - c,
      'D': d, "D'": 1 - d
    };

    const activeTerms = {};
    compiled.productTerms.forEach(term => {
      let hasConn = false;
      let satisfied = true;
      for (let r of this.RAILS) {
        if (term.rails[r] === 1) {
          hasConn = true;
          if (railsStatus[r] !== 1) {
            satisfied = false;
            break;
          }
        }
      }
      activeTerms[term.id] = (hasConn && satisfied) ? 1 : 0;
    });

    const outputResults = {};
    compiled.outputIds.forEach((outId, outIdx) => {
      let val = 0;
      compiled.productTerms.forEach((term, tIdx) => {
        if (compiled.orMatrix[outIdx][tIdx] === 1 && activeTerms[term.id] === 1) {
          val = 1;
        }
      });
      outputResults[outId] = val;
    });

    return {
      inputs: { A: a, B: b, C: c, D: d },
      railsStatus: railsStatus,
      activeTerms: activeTerms,
      outputs: outputResults
    };
  }

  static generateTruthTable(compiled) {
    const table = [];
    for (let m = 0; m < 16; m++) {
      const a = (m >> 3) & 1;
      const b = (m >> 2) & 1;
      const c = (m >> 1) & 1;
      const d = (m >> 0) & 1;
      const evalRes = this.evaluate(compiled, a, b, c, d);
      table.push({
        minterm: `m${m}`,
        m_index: m,
        A: a, B: b, C: c, D: d,
        binary: `${a}${b}${c}${d}`,
        active_terms: Object.keys(evalRes.activeTerms).filter(k => evalRes.activeTerms[k] === 1),
        outputs: evalRes.outputs
      });
    }
    return table;
  }

  static detectConflicts(compiled) {
    const conflicts = [];
    const redundancies = [];
    const warnings = [];

    // Duplicate check
    const termMap = {};
    for (let rule of compiled.rules) {
      const extracted = this.extractProductTerms(rule.expression);
      for (let item of extracted) {
        const tStr = item.term_str;
        if (termMap[tStr]) {
          redundancies.push({
            type: 'Duplicate Product Term',
            severity: 'Warning',
            term: tStr,
            first_rule: termMap[tStr].rule_name,
            duplicate_rule: rule.name,
            suggestion: `Product term '${tStr}' is repeated. Share this single AND gate in the PLA matrix across outputs to save chip area.`
          });
        } else {
          termMap[tStr] = { rule_name: rule.name, output: rule.target_output };
        }
      }
    }

    // Subsumption and overlap check
    const ruleMinterms = {};
    for (let rule of compiled.rules) {
      const mts = new Set();
      for (let m = 0; m < 16; m++) {
        const a = (m >> 3) & 1;
        const b = (m >> 2) & 1;
        const c = (m >> 1) & 1;
        const d = (m >> 0) & 1;
        if (this.evaluateMinterm(rule.expression, a, b, c, d) === 1) {
          mts.add(m);
        }
      }
      ruleMinterms[rule.name] = { output: rule.target_output, minterms: mts };
    }

    const ruleNames = Object.keys(ruleMinterms);
    for (let i = 0; i < ruleNames.length; i++) {
      for (let j = i + 1; j < ruleNames.length; j++) {
        const r1 = ruleNames[i];
        const r2 = ruleNames[j];
        const m1 = ruleMinterms[r1].minterms;
        const m2 = ruleMinterms[r2].minterms;
        const out1 = ruleMinterms[r1].output;
        const out2 = ruleMinterms[r2].output;

        if (out1 === out2 && m1.size > 0 && m2.size > 0) {
          const isSubset = (s1, s2) => [...s1].every(x => s2.has(x));
          if (m1.size === m2.size && isSubset(m1, m2)) {
            conflicts.push({
              type: 'Identical Functionality Overlap',
              severity: 'Warning',
              rule_a: r1,
              rule_b: r2,
              output: out1,
              suggestion: `Rules '${r1}' and '${r2}' cover the exact same input minterms for output ${out1}. Merge them into a single rule.`
            });
          } else if (isSubset(m1, m2)) {
            redundancies.push({
              type: 'Absorption Redundancy (Subsumption)',
              severity: 'Info',
              smaller_rule: r1,
              larger_rule: r2,
              output: out1,
              suggestion: `Rule '${r2}' completely subsumes '${r1}'. You can safely deactivate '${r1}'.`
            });
          } else if (isSubset(m2, m1)) {
            redundancies.push({
              type: 'Absorption Redundancy (Subsumption)',
              severity: 'Info',
              smaller_rule: r2,
              larger_rule: r1,
              output: out1,
              suggestion: `Rule '${r1}' completely subsumes '${r2}'. You can safely deactivate '${r2}'.`
            });
          }
        }
      }
    }

    // Safety Interlock Notice
    const table = this.generateTruthTable(compiled);
    for (let row of table) {
      if (row.outputs.Y4 === 1 && row.outputs.Y1 === 1) {
        warnings.push({
          type: 'Concurrent Safety Lockout & Data Operation',
          severity: 'Notice',
          minterm: row.minterm,
          binary: row.binary,
          suggestion: `At input state ${row.binary}, Safety Lockout (Y4) fires alongside primary operation (Y1). Verify if hardware muting is desired.`
        });
        break;
      }
    }

    const healthScore = Math.max(0, 100 - (conflicts.length * 15 + redundancies.length * 5));

    return {
      total_conflicts: conflicts.length,
      total_redundancies: redundancies.length,
      total_warnings: warnings.length,
      health_score: healthScore,
      conflicts: conflicts,
      redundancies: redundancies,
      warnings: warnings
    };
  }
}

window.PLACore = PLACore;
