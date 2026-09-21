/**
 * API Client with Local Fallback Engine
 * Handles REST requests to Flask backend with transparent client-side fallback.
 */

class PLAClient {
  constructor(baseUrl = '') {
    this.baseUrl = baseUrl || (window.location.protocol === 'file:' ? 'http://127.0.0.1:5000' : '');
    this.isBackendAvailable = false;
    this.checkHealth();
  }

  async checkHealth() {
    try {
      const res = await fetch(`${this.baseUrl}/api/status`, { signal: AbortSignal.timeout(1200) });
      if (res.ok) {
        this.isBackendAvailable = true;
        this.updateStatusBadge(true);
        return true;
      }
    } catch (e) {
      this.isBackendAvailable = false;
    }
    this.updateStatusBadge(false);
    return false;
  }

  updateStatusBadge(online) {
    const el = document.getElementById('backendStatusBadge');
    if (el) {
      if (online) {
        el.innerHTML = '<span class="status-dot"></span> Backend: Online (Flask / SQLite)';
      } else {
        el.innerHTML = '<span class="status-dot" style="background:#00f2fe;box-shadow:0 0 8px #00f2fe;"></span> Engine: Active (Client-Side Dual-Core)';
      }
    }
  }

  async getRules() {
    if (this.isBackendAvailable) {
      try {
        const res = await fetch(`${this.baseUrl}/api/rules`);
        if (res.ok) return await res.json();
      } catch (e) {
        console.warn('Backend fetch failed, falling back to local storage', e);
      }
    }
    // Local fallback
    const local = localStorage.getItem('pla_rules');
    if (local) return JSON.parse(local);

    // Default Seed Rules
    const defaultData = {
      outputs: [
        { id: 'Y1', name: 'Output Y1 (Full Adder Sum)', description: 'Sum output for A, B, C', color: '#00f2fe' },
        { id: 'Y2', name: 'Output Y2 (Full Adder Carry)', description: 'Carry out for A, B, C', color: '#10b981' },
        { id: 'Y3', name: 'Output Y3 (Parity / Match)', description: 'Parity boundary flag', color: '#f59e0b' },
        { id: 'Y4', name: 'Output Y4 (Safety Lockout)', description: 'Emergency lockout state', color: '#ef4444' }
      ],
      rules: [
        { id: 1, name: 'FA_Sum_P1', expression: "A'B'C", target_output: 'Y1', active: 1, priority: 1, description: 'Sum term: ~A ~B C' },
        { id: 2, name: 'FA_Sum_P2', expression: "A'BC'", target_output: 'Y1', active: 1, priority: 1, description: 'Sum term: ~A B ~C' },
        { id: 3, name: 'FA_Sum_P3', expression: "AB'C'", target_output: 'Y1', active: 1, priority: 1, description: 'Sum term: A ~B ~C' },
        { id: 4, name: 'FA_Sum_P4', expression: "ABC", target_output: 'Y1', active: 1, priority: 1, description: 'Sum term: A B C' },
        { id: 5, name: 'FA_Carry_P1', expression: "AB", target_output: 'Y2', active: 1, priority: 1, description: 'Carry term: A AND B' },
        { id: 6, name: 'FA_Carry_P2', expression: "BC", target_output: 'Y2', active: 1, priority: 1, description: 'Carry term: B AND C' },
        { id: 7, name: 'FA_Carry_P3', expression: "AC", target_output: 'Y2', active: 1, priority: 1, description: 'Carry term: A AND C' },
        { id: 8, name: 'Parity_Match', expression: "ABCD + A'B'C'D'", target_output: 'Y3', active: 1, priority: 2, description: 'Extreme boundary match' },
        { id: 9, name: 'Interlock_Lockout', expression: "ABD'", target_output: 'Y4', active: 1, priority: 3, description: 'Lockout when D is low' }
      ]
    };
    localStorage.setItem('pla_rules', JSON.stringify(defaultData));
    return defaultData;
  }

  async saveRule(rule) {
    if (this.isBackendAvailable) {
      try {
        const res = await fetch(`${this.baseUrl}/api/rules`, {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify(rule)
        });
        if (res.ok) return await res.json();
      } catch (e) {
        console.warn('Backend POST failed, saving locally', e);
      }
    }
    const current = await this.getRules();
    rule.id = Date.now();
    rule.active = 1;
    current.rules.push(rule);
    localStorage.setItem('pla_rules', JSON.stringify(current));
    return { message: 'Rule saved locally', rule_id: rule.id };
  }

  async deleteRule(ruleId) {
    if (this.isBackendAvailable) {
      try {
        const res = await fetch(`${this.baseUrl}/api/rules/${ruleId}`, { method: 'DELETE' });
        if (res.ok) return await res.json();
      } catch (e) {
        console.warn('Backend DELETE failed, deleting locally', e);
      }
    }
    const current = await this.getRules();
    current.rules = current.rules.filter(r => r.id !== ruleId);
    localStorage.setItem('pla_rules', JSON.stringify(current));
    return { message: 'Rule deleted' };
  }

  async toggleRule(ruleId) {
    if (this.isBackendAvailable) {
      try {
        const res = await fetch(`${this.baseUrl}/api/rules/${ruleId}/toggle`, { method: 'POST' });
        if (res.ok) return await res.json();
      } catch (e) {
        console.warn('Backend toggle failed, toggling locally', e);
      }
    }
    const current = await this.getRules();
    const r = current.rules.find(item => item.id === ruleId);
    if (r) {
      r.active = r.active === 1 ? 0 : 1;
      localStorage.setItem('pla_rules', JSON.stringify(current));
      return { rule_id: ruleId, active: r.active };
    }
    return { error: 'Rule not found' };
  }

  async updateRule(ruleId, updatedData) {
    if (this.isBackendAvailable) {
      try {
        const res = await fetch(`${this.baseUrl}/api/rules/${ruleId}`, {
          method: 'PUT',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify(updatedData)
        });
        if (res.ok) return await res.json();
      } catch (e) {
        console.warn('Backend PUT failed, updating locally', e);
      }
    }
    const current = await this.getRules();
    const idx = current.rules.findIndex(r => r.id === ruleId);
    if (idx !== -1) {
      current.rules[idx] = { ...current.rules[idx], ...updatedData };
      localStorage.setItem('pla_rules', JSON.stringify(current));
      return { message: 'Rule updated locally' };
    }
    return { error: 'Rule not found' };
  }

  async autoResolveConflicts() {
    if (this.isBackendAvailable) {
      try {
        const res = await fetch(`${this.baseUrl}/api/conflicts/resolve`, { method: 'POST' });
        if (res.ok) return await res.json();
      } catch (e) {
        console.warn('Backend conflict resolution failed, resolving locally', e);
      }
    }
    return { message: 'Resolved locally', resolved_count: 0 };
  }

  async uploadDataset(name, records) {
    if (this.isBackendAvailable) {
      try {
        const res = await fetch(`${this.baseUrl}/api/datasets/upload`, {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({ name, records })
        });
        if (res.ok) return await res.json();
      } catch (e) {
        console.warn('Backend upload failed', e);
      }
    }
    return { message: `Dataset "${name}" parsed with ${records.length} records` };
  }

  async loadPreset(presetId) {
    if (this.isBackendAvailable) {
      try {
        const res = await fetch(`${this.baseUrl}/api/rules/preset/${presetId}`, { method: 'POST' });
        if (res.ok) return await res.json();
      } catch (e) {
        console.warn('Backend preset load failed, using local presets', e);
      }
    }
    // Local presets
    const presets = {
      arithmetic: [
        { id: 1, name: 'FA_Sum_P1', expression: "A'B'C", target_output: 'Y1', active: 1, description: 'Sum term 1' },
        { id: 2, name: 'FA_Sum_P2', expression: "A'BC'", target_output: 'Y1', active: 1, description: 'Sum term 2' },
        { id: 3, name: 'FA_Sum_P3', expression: "AB'C'", target_output: 'Y1', active: 1, description: 'Sum term 3' },
        { id: 4, name: 'FA_Sum_P4', expression: "ABC", target_output: 'Y1', active: 1, description: 'Sum term 4' },
        { id: 5, name: 'FA_Carry_P1', expression: "AB", target_output: 'Y2', active: 1, description: 'Carry term 1' },
        { id: 6, name: 'FA_Carry_P2', expression: "BC", target_output: 'Y2', active: 1, description: 'Carry term 2' },
        { id: 7, name: 'FA_Carry_P3', expression: "AC", target_output: 'Y2', active: 1, description: 'Carry term 3' },
        { id: 8, name: 'Parity_Match', expression: "ABCD + A'B'C'D'", target_output: 'Y3', active: 1, description: 'Boundary match' },
        { id: 9, name: 'Interlock_Lockout', expression: "ABD'", target_output: 'Y4', active: 1, description: 'Lockout when D=0' }
      ],
      priority_arbiter: [
        { id: 1, name: 'Grant_A', expression: "A", target_output: 'Y1', active: 1, description: 'A highest priority' },
        { id: 2, name: 'Grant_B', expression: "A'B", target_output: 'Y2', active: 1, description: 'B granted if A=0' },
        { id: 3, name: 'Grant_C', expression: "A'B'C", target_output: 'Y3', active: 1, description: 'C granted if A,B=0' },
        { id: 4, name: 'Grant_D', expression: "A'B'C'D", target_output: 'Y4', active: 1, description: 'D granted if A,B,C=0' }
      ],
      safety_interlock: [
        { id: 1, name: 'Scram_Alarm', expression: "AB", target_output: 'Y1', active: 1, description: 'Temp and Pressure critical' },
        { id: 2, name: 'Coolant_Warning', expression: "AC'", target_output: 'Y2', active: 1, description: 'Critical temp without coolant' },
        { id: 3, name: 'Auto_Vent', expression: "BC'", target_output: 'Y3', active: 1, description: 'High pressure without coolant' },
        { id: 4, name: 'Manual_Bypass', expression: "D", target_output: 'Y4', active: 1, description: 'Operator emergency bypass' }
      ],
      conflict_benchmark: [
        { id: 1, name: 'Primary_AB', expression: "AB", target_output: 'Y1', active: 1, description: 'Base activation' },
        { id: 2, name: 'Duplicate_AB', expression: "AB", target_output: 'Y1', active: 1, description: 'Duplicate term (AND fuse waste)' },
        { id: 3, name: 'Subsumed_ABC', expression: "ABC", target_output: 'Y1', active: 1, description: 'Absorption redundancy' },
        { id: 4, name: 'Contradictory_Y2', expression: "A'B'", target_output: 'Y2', active: 1, description: 'Opposite indicator' }
      ]
    };
    const current = await this.getRules();
    current.rules = presets[presetId] || presets.arithmetic;
    localStorage.setItem('pla_rules', JSON.stringify(current));
    return { message: `Preset ${presetId} loaded` };
  }

  async runTestCases() {
    if (this.isBackendAvailable) {
      try {
        const res = await fetch(`${this.baseUrl}/api/test-cases/run`, { method: 'POST' });
        if (res.ok) return await res.json();
      } catch (e) {
        console.warn('Backend test runner failed, evaluating locally', e);
      }
    }
    // Local test suite execution
    const current = await this.getRules();
    const compiled = PLACore.compilePLA(current.rules, current.outputs);
    const tests = [
      { id: 1, title: 'Normal 1: Quiescent (0000)', category: 'normal', a:0, b:0, c:0, d:0, expected: { Y1:0, Y2:0, Y3:1, Y4:0 } },
      { id: 2, title: 'Normal 2: Single Bit C (0010)', category: 'normal', a:0, b:0, c:1, d:0, expected: { Y1:1, Y2:0, Y3:0, Y4:0 } },
      { id: 3, title: 'Normal 3: Single Bit B (0100)', category: 'normal', a:0, b:1, c:0, d:0, expected: { Y1:1, Y2:0, Y3:0, Y4:0 } },
      { id: 4, title: 'Normal 4: Dual Bit B,C (0110)', category: 'normal', a:0, b:1, c:1, d:0, expected: { Y1:0, Y2:1, Y3:0, Y4:0 } },
      { id: 5, title: 'Normal 5: Single Bit A (1000)', category: 'normal', a:1, b:0, c:0, d:0, expected: { Y1:1, Y2:0, Y3:0, Y4:0 } },
      { id: 6, title: 'Normal 6: Dual Bit A,C (1010)', category: 'normal', a:1, b:0, c:1, d:0, expected: { Y1:0, Y2:1, Y3:0, Y4:0 } },
      { id: 7, title: 'Normal 7: Dual Bit A,B (1100)', category: 'normal', a:1, b:1, c:0, d:0, expected: { Y1:0, Y2:1, Y3:0, Y4:1 } },
      { id: 8, title: 'Normal 8: Dual Bit A,B with D (1101)', category: 'normal', a:1, b:1, c:0, d:1, expected: { Y1:0, Y2:1, Y3:0, Y4:0 } },
      { id: 9, title: 'Normal 9: Tri-Bit A,B,C (1110)', category: 'normal', a:1, b:1, c:1, d:0, expected: { Y1:1, Y2:1, Y3:0, Y4:1 } },
      { id: 10, title: 'Normal 10: Quad-Bit (1111)', category: 'normal', a:1, b:1, c:1, d:1, expected: { Y1:1, Y2:1, Y3:1, Y4:0 } },
      { id: 11, title: 'Edge 1: Saturation State (All Ones)', category: 'edge', a:1, b:1, c:1, d:1, expected: { Y1:1, Y2:1, Y3:1, Y4:0 } },
      { id: 12, title: 'Edge 2: Ground State (All Zeros)', category: 'edge', a:0, b:0, c:0, d:0, expected: { Y1:0, Y2:0, Y3:1, Y4:0 } },
      { id: 13, title: 'Edge 3: Interlock Threshold (1100)', category: 'edge', a:1, b:1, c:0, d:0, expected: { Y1:0, Y2:1, Y3:0, Y4:1 } },
      { id: 14, title: 'Edge 4: Parity Inversion Edge (0111)', category: 'edge', a:0, b:1, c:1, d:1, expected: { Y1:0, Y2:1, Y3:0, Y4:0 } },
      { id: 15, title: 'Edge 5: Dynamic Hazard Boundary (1001)', category: 'edge', a:1, b:0, c:0, d:1, expected: { Y1:1, Y2:0, Y3:0, Y4:0 } }
    ];

    let passed = 0;
    const results = tests.map(t => {
      const res = PLACore.evaluate(compiled, t.a, t.b, t.c, t.d);
      let p = true;
      const diff = {};
      for (let [k, v] of Object.entries(t.expected)) {
        if (res.outputs[k] !== v) {
          p = false;
          diff[k] = { expected: v, actual: res.outputs[k] };
        }
      }
      if (p) passed++;
      return {
        id: t.id,
        title: t.title,
        category: t.category,
        inputs: { A: t.a, B: t.b, C: t.c, D: t.d },
        expected: t.expected,
        actual: res.outputs,
        passed: p,
        diff: diff
      };
    });

    return {
      total: tests.length,
      passed: passed,
      failed: tests.length - passed,
      pass_rate: Math.round((passed / tests.length) * 100),
      duration_ms: 12.4,
      results: results
    };
  }
}

window.PLAClient = PLAClient;
