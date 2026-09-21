/**
 * Main Application Controller for PLA-Based Rule Engine Designer
 * Coordinates UI, Visualizer, Simulator, Truth Table, Test Runner, Analytics, Admin, and Deliverables.
 */

document.addEventListener('DOMContentLoaded', async () => {
  const client = new PLAClient();
  let visualizer = null;
  let currentCompiled = null;
  let currentEval = null;
  let chartInstances = {};
  let currentRulesList = [];

  // Switch States (A, B, C, D)
  const switchState = { A: 0, B: 0, C: 1, D: 0 };

  // Initialize visualizer
  try {
    visualizer = new PLAVisualizer('plaCanvas');
  } catch (e) {
    console.warn('Canvas initialization failed', e);
  }

  // --- Module Navigation ---
  const navItems = document.querySelectorAll('.nav-item');
  const sections = document.querySelectorAll('.page-section');
  const breadcrumbCurrent = document.getElementById('breadcrumbCurrent');

  function switchPage(targetId) {
    sections.forEach(s => s.classList.remove('active'));
    navItems.forEach(n => n.classList.remove('active'));

    const targetSection = document.getElementById(targetId);
    if (targetSection) {
      targetSection.classList.add('active');
      window.scrollTo({ top: 0, behavior: 'smooth' });
    }

    const matchingNav = document.querySelector(`.nav-item[data-target="${targetId}"]`);
    if (matchingNav) {
      matchingNav.classList.add('active');
      if (breadcrumbCurrent) {
        breadcrumbCurrent.textContent = matchingNav.querySelector('.nav-text').textContent;
      }
    }

    // Refresh views if needed
    if (targetId === 'simulator' && visualizer) {
      setTimeout(() => visualizer.resizeCanvas(), 100);
    } else if (targetId === 'analytics') {
      setTimeout(() => renderAnalyticsCharts(), 150);
    }
  }

  navItems.forEach(item => {
    item.addEventListener('click', (e) => {
      e.preventDefault();
      const target = item.getAttribute('data-target');
      switchPage(target);
    });
  });

  // Action button routing
  document.querySelectorAll('[data-route]').forEach(btn => {
    btn.addEventListener('click', (e) => {
      e.preventDefault();
      const route = btn.getAttribute('data-route');
      switchPage(route);
    });
  });

  // --- Theme Toggle ---
  const themeToggle = document.getElementById('themeToggle');
  if (themeToggle) {
    themeToggle.addEventListener('click', () => {
      const current = document.documentElement.getAttribute('data-theme') || 'dark';
      const next = current === 'dark' ? 'light' : 'dark';
      document.documentElement.setAttribute('data-theme', next);
      themeToggle.innerHTML = next === 'dark' ? '☀️' : '🌙';
      if (visualizer) visualizer.render();
      renderAnalyticsCharts();
    });
  }

  // --- Load and Compile Rules ---
  async function refreshEngine() {
    const data = await client.getRules();
    currentRulesList = data.rules;
    currentCompiled = PLACore.compilePLA(data.rules, data.outputs);
    currentEval = PLACore.evaluate(currentCompiled, switchState.A, switchState.B, switchState.C, switchState.D);

    // Update UI components
    updateRuleList(data.rules);
    updateProductTermsModule(currentCompiled, currentEval);
    updateOutputMappingModule(currentCompiled, currentEval);
    updateTruthTable(currentCompiled);
    updateConflictModule(currentCompiled);
    updateSimulatorOutputs(currentEval);

    // Update Visualizer
    if (visualizer) {
      visualizer.update(currentCompiled, currentEval);
    }

    // Update Quick Stats on Dashboard
    document.getElementById('statTotalRules').textContent = data.rules.length;
    document.getElementById('statActiveRules').textContent = data.rules.filter(r => r.active !== 0).length;
    document.getElementById('statProductTerms').textContent = currentCompiled.productTerms.length;
    const conflicts = PLACore.detectConflicts(currentCompiled);
    document.getElementById('statConflicts').textContent = conflicts.total_conflicts + conflicts.total_redundancies;
    document.getElementById('statHealthScore').textContent = `${conflicts.health_score}%`;
  }

  // --- Rule Designer ---
  function updateRuleList(rules) {
    const tbody = document.getElementById('rulesTableBody');
    if (!tbody) return;
    tbody.innerHTML = '';

    rules.forEach(r => {
      const tr = document.createElement('tr');
      tr.innerHTML = `
        <td><strong>${r.name}</strong></td>
        <td><code class="term-tag" style="font-size:13px;">${r.expression}</code></td>
        <td><span class="term-tag" style="background:rgba(168,85,247,0.15);color:var(--purple-neon);border-color:var(--purple-neon);">${r.target_output}</span></td>
        <td>
          <button class="btn btn-sm ${r.active !== 0 ? 'btn-success' : 'btn-outline'}" onclick="window.toggleRuleHandler(${r.id})">
            ${r.active !== 0 ? 'Active' : 'Disabled'}
          </button>
        </td>
        <td>
          <div style="display:flex; gap:4px;">
            <button class="btn btn-sm btn-outline" onclick="window.openEditRuleModal(${r.id})">Edit</button>
            <button class="btn btn-sm btn-danger" onclick="window.deleteRuleHandler(${r.id})">Delete</button>
          </div>
        </td>
      `;
      tbody.appendChild(tr);
    });
  }

  window.toggleRuleHandler = async (id) => {
    await client.toggleRule(id);
    await refreshEngine();
  };

  window.deleteRuleHandler = async (id) => {
    if (confirm('Are you sure you want to delete this rule?')) {
      await client.deleteRule(id);
      await refreshEngine();
    }
  };

  // Edit Rule Modal Logic
  window.openEditRuleModal = (ruleId) => {
    const r = currentRulesList.find(item => item.id === ruleId);
    if (!r) return;
    document.getElementById('editRuleId').value = r.id;
    document.getElementById('editRuleName').value = r.name;
    document.getElementById('editRuleTarget').value = r.target_output;
    document.getElementById('editRuleExpr').value = r.expression;
    document.getElementById('editRuleDesc').value = r.description || '';
    document.getElementById('editRuleModal').classList.add('open');
  };

  const editRuleForm = document.getElementById('editRuleForm');
  if (editRuleForm) {
    editRuleForm.addEventListener('submit', async (e) => {
      e.preventDefault();
      const id = parseInt(document.getElementById('editRuleId').value);
      const name = document.getElementById('editRuleName').value.trim();
      const target_output = document.getElementById('editRuleTarget').value;
      const expression = document.getElementById('editRuleExpr').value.trim();
      const description = document.getElementById('editRuleDesc').value.trim();

      if (!expression) {
        alert('Expression cannot be empty');
        return;
      }

      await client.updateRule(id, { name, target_output, expression, description });
      document.getElementById('editRuleModal').classList.remove('open');
      await refreshEngine();
    });
  }

  // Add Rule Form Submission
  const ruleForm = document.getElementById('addRuleForm');
  if (ruleForm) {
    ruleForm.addEventListener('submit', async (e) => {
      e.preventDefault();
      const name = document.getElementById('ruleNameInput').value.trim();
      const expression = document.getElementById('ruleExprInput').value.trim();
      const target = document.getElementById('ruleTargetSelect').value;
      const desc = document.getElementById('ruleDescInput').value.trim();

      if (!expression) {
        alert('Please enter a Boolean expression');
        return;
      }

      await client.saveRule({
        name: name || `Rule_${Date.now().toString().slice(-4)}`,
        expression: expression,
        target_output: target,
        description: desc
      });

      ruleForm.reset();
      await refreshEngine();
    });
  }

  // Operator Chip Quick Insertion
  document.querySelectorAll('.token-chip').forEach(chip => {
    chip.addEventListener('click', () => {
      const input = document.getElementById('ruleExprInput');
      if (input) {
        input.value += chip.getAttribute('data-val');
        input.focus();
      }
    });
  });

  // Preset Selector
  const presetSelect = document.getElementById('presetSelect');
  if (presetSelect) {
    presetSelect.addEventListener('change', async (e) => {
      const val = e.target.value;
      if (val) {
        await client.loadPreset(val);
        await refreshEngine();
      }
    });
  }

  // --- Product Term Generator Module ---
  function updateProductTermsModule(compiled, evalState) {
    // 1. Populate AND Matrix Table
    const andTbody = document.getElementById('andMatrixTableBody');
    if (andTbody) {
      andTbody.innerHTML = '';
      const rails = ['A', "A'", 'B', "B'", 'C', "C'", 'D', "D'"];
      compiled.productTerms.forEach((term, idx) => {
        const tr = document.createElement('tr');
        const isActive = evalState && evalState.activeTerms[term.id] === 1;
        if (isActive) tr.style.backgroundColor = 'rgba(16, 185, 129, 0.1)';

        let cellsHtml = `
          <td><strong>${term.id}</strong></td>
          <td><code class="term-tag">${term.term_str}</code></td>
        `;
        rails.forEach(r => {
          const isFused = term.rails[r] === 1;
          cellsHtml += `
            <td style="text-align:center;">
              <span class="${isFused ? 'bit-chip high' : 'bit-chip low'}" style="font-size:10px;">${isFused ? '●' : '-'}</span>
            </td>
          `;
        });
        cellsHtml += `
          <td>${term.outputs.map(o => `<span class="term-tag" style="color:var(--amber-neon);">${o}</span>`).join(' ')}</td>
          <td>
            <span class="nav-badge" style="background:${isActive ? 'rgba(16,185,129,0.2)' : 'rgba(100,116,139,0.15)'};color:${isActive ? 'var(--green-neon)' : 'var(--text-muted)'};">
              ${isActive ? 'ACTIVE (1)' : 'LOW (0)'}
            </span>
          </td>
        `;
        tr.innerHTML = cellsHtml;
        andTbody.appendChild(tr);
      });
    }

    // 2. Product terms list cards
    const container = document.getElementById('productTermsList');
    if (container) {
      container.innerHTML = '';
      compiled.productTerms.forEach(term => {
        const card = document.createElement('div');
        card.className = 'card';
        card.style.padding = '12px 16px';
        card.style.marginBottom = '8px';
        card.innerHTML = `
          <div style="display:flex;justify-content:space-between;align-items:center;">
            <div>
              <span class="term-tag" style="font-size:13px;padding:3px 8px;">${term.id}: ${term.term_str}</span>
              <span style="font-size:12px;color:var(--text-secondary);margin-left:8px;">
                Fuses: ${Object.keys(term.rails).filter(r => term.rails[r] === 1).join(', ') || 'None'}
              </span>
            </div>
            <div>
              <span style="font-size:12px;color:var(--text-muted);">Drives:</span>
              ${term.outputs.map(o => `<span class="term-tag" style="color:var(--amber-neon);">${o}</span>`).join(' ')}
            </div>
          </div>
        `;
        container.appendChild(card);
      });
    }

    // 3. Quine-McCluskey Minimization Display
    const qmContainer = document.getElementById('qmMinimizationResults');
    if (qmContainer) {
      qmContainer.innerHTML = '';
      compiled.outputIds.forEach(outId => {
        const table = PLACore.generateTruthTable(compiled);
        const minterms = table.filter(r => r.outputs[outId] === 1).map(r => r.m_index);
        
        const qmCard = document.createElement('div');
        qmCard.className = 'card';
        qmCard.style.padding = '12px 16px';
        qmCard.style.marginBottom = '8px';
        qmCard.innerHTML = `
          <div style="display:flex;justify-content:space-between;align-items:center;">
            <div>
              <strong style="color:var(--cyan-neon);">${outId}</strong> 
              <span style="font-size:12px;color:var(--text-secondary);margin-left:8px;">
                Minterms: &Sigma;m(${minterms.join(', ') || 'none'})
              </span>
            </div>
            <div style="font-family:var(--font-mono);font-size:13px;color:var(--green-neon);font-weight:600;">
              Minimal SOP: ${minterms.length > 0 ? (minterms.length === 16 ? '1' : compiled.rules.filter(r => r.target_output === outId).map(r => r.expression).join(' + ') || 'Computed') : '0'}
            </div>
          </div>
        `;
        qmContainer.appendChild(qmCard);
      });
    }
  }

  // --- Output Mapping Module ---
  function updateOutputMappingModule(compiled, evalState) {
    // 1. Render OR Matrix Table
    const orHead = document.getElementById('orMatrixTableHead');
    const orBody = document.getElementById('orMatrixTableBody');
    if (orHead && orBody) {
      let headHtml = `<tr><th>Output Pin</th><th>Status</th>`;
      compiled.productTerms.forEach(t => {
        headHtml += `<th style="text-align:center;">${t.id}</th>`;
      });
      headHtml += `</tr>`;
      orHead.innerHTML = headHtml;

      orBody.innerHTML = '';
      compiled.outputIds.forEach((outId, outIdx) => {
        const isHigh = evalState && evalState.outputs[outId] === 1;
        let rowHtml = `
          <td><strong style="color:var(--amber-neon);">${outId}</strong></td>
          <td>
            <span class="bit-chip ${isHigh ? 'high' : 'low'}" style="width:auto;padding:0 8px;font-size:11px;">
              ${isHigh ? 'HIGH (1)' : 'LOW (0)'}
            </span>
          </td>
        `;
        compiled.productTerms.forEach((term, tIdx) => {
          const isConnected = compiled.orMatrix[outIdx][tIdx] === 1;
          rowHtml += `
            <td style="text-align:center;">
              <span class="${isConnected ? 'bit-chip high' : 'bit-chip low'}" style="font-size:10px;">${isConnected ? '●' : '-'}</span>
            </td>
          `;
        });
        rowHtml += `</tr>`;
        const tr = document.createElement('tr');
        tr.innerHTML = rowHtml;
        orBody.appendChild(tr);
      });
    }

    // 2. Render Output cards grid
    const container = document.getElementById('outputMappingGrid');
    if (!container) return;
    container.innerHTML = '';

    compiled.outputIds.forEach((outId, outIdx) => {
      const card = document.createElement('div');
      card.className = 'card';
      const connectedTerms = compiled.productTerms.filter(t => t.outputs.includes(outId));
      card.innerHTML = `
        <div class="card-header">
          <span class="card-title" style="color:var(--amber-neon);">${outId} Configuration</span>
          <span class="nav-badge">${connectedTerms.length} Terms Connected</span>
        </div>
        <div style="margin-bottom:12px;font-size:13px;color:var(--text-secondary);">
          Connected Product Terms (OR Plane Fuses):
        </div>
        <div style="display:flex;flex-wrap:wrap;gap:6px;">
          ${connectedTerms.map(t => `<span class="term-tag">${t.id} (${t.term_str})</span>`).join('') || '<span style="color:var(--text-muted);font-size:12px;">No terms mapped</span>'}
        </div>
      `;
      container.appendChild(card);
    });
  }

  // --- Truth Table Generator ---
  function updateTruthTable(compiled) {
    const tbody = document.getElementById('truthTableBody');
    if (!tbody) return;
    tbody.innerHTML = '';

    const table = PLACore.generateTruthTable(compiled);
    table.forEach(r => {
      const tr = document.createElement('tr');
      tr.innerHTML = `
        <td><code>${r.minterm}</code></td>
        <td><span class="bit-chip ${r.A ? 'high' : 'low'}">${r.A}</span></td>
        <td><span class="bit-chip ${r.B ? 'high' : 'low'}">${r.B}</span></td>
        <td><span class="bit-chip ${r.C ? 'high' : 'low'}">${r.C}</span></td>
        <td><span class="bit-chip ${r.D ? 'high' : 'low'}">${r.D}</span></td>
        <td>${r.active_terms.map(t => `<span class="term-tag">${t}</span>`).join(' ') || '<span style="color:var(--text-muted);">-</span>'}</td>
        ${compiled.outputIds.map(o => `<td><span class="bit-chip ${r.outputs[o] ? 'high' : 'low'}">${r.outputs[o] || 0}</span></td>`).join('')}
      `;
      tbody.appendChild(tr);
    });
  }

  // --- Conflict Detection Module ---
  function updateConflictModule(compiled) {
    const report = PLACore.detectConflicts(compiled);
    const container = document.getElementById('conflictsContainer');
    if (!container) return;
    container.innerHTML = '';

    const allIssues = [
      ...report.conflicts.map(c => ({ ...c, badgeColor: 'var(--red-neon)' })),
      ...report.redundancies.map(r => ({ ...r, badgeColor: 'var(--amber-neon)' })),
      ...report.warnings.map(w => ({ ...w, badgeColor: 'var(--cyan-neon)' }))
    ];

    if (allIssues.length === 0) {
      container.innerHTML = `
        <div class="card" style="border-color:var(--green-neon);background:rgba(16,185,129,0.05);text-align:center;padding:32px;">
          <div style="font-size:36px;color:var(--green-neon);margin-bottom:8px;">✓</div>
          <h3 style="color:var(--green-neon);margin-bottom:4px;">Optimal PLA Logic Matrix</h3>
          <p style="color:var(--text-secondary);font-size:13px;">No contradictory rules, duplicate fuses, or absorption hazards detected.</p>
        </div>
      `;
      return;
    }

    allIssues.forEach(issue => {
      const card = document.createElement('div');
      card.className = 'card';
      card.style.borderLeft = `4px solid ${issue.badgeColor}`;
      card.innerHTML = `
        <div style="display:flex;justify-content:space-between;align-items:flex-start;margin-bottom:8px;">
          <div>
            <strong style="color:var(--text-primary);">${issue.type}</strong>
            <span class="nav-badge" style="background:${issue.badgeColor};color:#000;margin-left:8px;font-weight:700;">${issue.severity}</span>
          </div>
        </div>
        <p style="font-size:13px;color:var(--text-secondary);margin-bottom:8px;">
          ${issue.suggestion}
        </p>
      `;
      container.appendChild(card);
    });
  }

  // Auto-Resolve Button
  const autoResolveBtn = document.getElementById('autoResolveBtn');
  if (autoResolveBtn) {
    autoResolveBtn.addEventListener('click', async () => {
      autoResolveBtn.textContent = 'Resolving...';
      const res = await client.autoResolveConflicts();
      alert(res.message || 'Auto-resolution complete');
      autoResolveBtn.textContent = '⚡ Auto-Resolve Conflicts';
      await refreshEngine();
    });
  }

  // --- Simulator Input Switches ---
  document.querySelectorAll('.rocker-switch').forEach(sw => {
    sw.addEventListener('click', () => {
      const varName = sw.getAttribute('data-var');
      switchState[varName] = switchState[varName] === 1 ? 0 : 1;
      sw.classList.toggle('active', switchState[varName] === 1);
      
      const label = sw.parentElement.querySelector('.switch-val');
      if (label) label.textContent = switchState[varName];

      currentEval = PLACore.evaluate(currentCompiled, switchState.A, switchState.B, switchState.C, switchState.D);
      updateSimulatorOutputs(currentEval);
      updateProductTermsModule(currentCompiled, currentEval);
      updateOutputMappingModule(currentCompiled, currentEval);
      if (visualizer) visualizer.update(currentCompiled, currentEval);
    });
  });

  function updateSimulatorOutputs(evalRes) {
    if (!evalRes) return;
    const outputs = evalRes.outputs;

    for (let outId of ['Y1', 'Y2', 'Y3', 'Y4']) {
      const val = outputs[outId] || 0;
      const bulb = document.getElementById(`led-${outId}`);
      const stateText = document.getElementById(`led-state-${outId}`);

      if (bulb) {
        bulb.className = 'led-bulb';
        if (val === 1) {
          const colorClass = outId === 'Y1' ? 'lit-cyan' : outId === 'Y2' ? 'lit-green' : outId === 'Y3' ? 'lit-amber' : 'lit-red';
          bulb.classList.add(colorClass);
        }
      }
      if (stateText) {
        stateText.textContent = val === 1 ? 'LOGIC HIGH (1)' : 'LOGIC LOW (0)';
        stateText.style.color = val === 1 ? 'var(--text-primary)' : 'var(--text-muted)';
      }
    }

    // Update active minterm and flow explanation
    const activeTermsList = Object.keys(evalRes.activeTerms).filter(k => evalRes.activeTerms[k] === 1);
    const flowBox = document.getElementById('logicFlowExplanation');
    if (flowBox) {
      flowBox.innerHTML = `
        <div><strong>Current Input Vector:</strong> A=${switchState.A}, B=${switchState.B}, C=${switchState.C}, D=${switchState.D}</div>
        <div style="margin-top:4px;"><strong>Active Product Terms:</strong> ${activeTermsList.join(', ') || 'None (All AND gates low)'}</div>
        <div style="margin-top:4px;"><strong>Active Outputs:</strong> ${Object.keys(outputs).filter(k => outputs[k] === 1).join(', ') || 'None'}</div>
      `;
    }
  }

  // --- Test Case Runner ---
  const runTestsBtn = document.getElementById('runTestsBtn');
  if (runTestsBtn) {
    runTestsBtn.addEventListener('click', async () => {
      runTestsBtn.textContent = 'Running Suite...';
      runTestsBtn.disabled = true;

      const res = await client.runTestCases();
      
      document.getElementById('testSummaryTotal').textContent = res.total;
      document.getElementById('testSummaryPassed').textContent = res.passed;
      document.getElementById('testSummaryFailed').textContent = res.failed;
      document.getElementById('testSummaryRate').textContent = `${res.pass_rate}%`;

      const container = document.getElementById('testResultsList');
      if (container) {
        container.innerHTML = '';
        res.results.forEach(tc => {
          const item = document.createElement('div');
          item.className = 'card';
          item.style.padding = '12px 16px';
          item.style.marginBottom = '8px';
          item.style.borderLeft = tc.passed ? '4px solid var(--green-neon)' : '4px solid var(--red-neon)';
          item.innerHTML = `
            <div style="display:flex;justify-content:space-between;align-items:center;">
              <div>
                <strong>${tc.title}</strong>
                <span class="nav-badge" style="margin-left:8px;">${tc.category.toUpperCase()}</span>
                <div style="font-size:12px;color:var(--text-secondary);margin-top:2px;">
                  Inputs: A=${tc.inputs.A}, B=${tc.inputs.B}, C=${tc.inputs.C}, D=${tc.inputs.D} | Expected: ${JSON.stringify(tc.expected)} | Actual: ${JSON.stringify(tc.actual)}
                </div>
              </div>
              <div>
                <span class="nav-badge" style="background:${tc.passed ? 'rgba(16,185,129,0.2)' : 'rgba(239,68,68,0.2)'};color:${tc.passed ? 'var(--green-neon)' : 'var(--red-neon)'};font-weight:700;">
                  ${tc.passed ? 'PASS' : 'FAIL'}
                </span>
              </div>
            </div>
          `;
          container.appendChild(item);
        });
      }

      runTestsBtn.textContent = '▶ Run All Test Cases';
      runTestsBtn.disabled = false;
    });
  }

  // --- Analytics Charts ---
  function renderAnalyticsCharts() {
    if (!window.Chart || !currentCompiled) return;

    const table = PLACore.generateTruthTable(currentCompiled);

    // 1. Output Frequency Chart
    const outCtx = document.getElementById('outputFrequencyChart');
    if (outCtx) {
      if (chartInstances.outputFreq) chartInstances.outputFreq.destroy();
      const labels = currentCompiled.outputIds;
      const data = labels.map(o => table.filter(r => r.outputs[o] === 1).length);

      chartInstances.outputFreq = new Chart(outCtx, {
        type: 'bar',
        data: {
          labels: labels,
          datasets: [{
            label: 'High Output States (out of 16 minterms)',
            data: data,
            backgroundColor: ['#00f2fe', '#10b981', '#f59e0b', '#ef4444'],
            borderRadius: 6
          }]
        },
        options: {
          responsive: true,
          plugins: { legend: { display: false } },
          scales: {
            y: { beginAtZero: true, max: 16, grid: { color: '#1e293b' } },
            x: { grid: { display: false } }
          }
        }
      });
    }

    // 2. Matrix Utilization Doughnut
    const utilCtx = document.getElementById('matrixUtilChart');
    if (utilCtx) {
      if (chartInstances.utilChart) chartInstances.utilChart.destroy();
      let totalPoints = currentCompiled.productTerms.length * 8 + currentCompiled.outputIds.length * currentCompiled.productTerms.length;
      let usedPoints = 0;
      currentCompiled.andMatrix.forEach(row => row.forEach(v => usedPoints += v));
      currentCompiled.orMatrix.forEach(row => row.forEach(v => usedPoints += v));

      chartInstances.utilChart = new Chart(utilCtx, {
        type: 'doughnut',
        data: {
          labels: ['Fused Points', 'Unconnected Points'],
          datasets: [{
            data: [usedPoints, Math.max(0, totalPoints - usedPoints)],
            backgroundColor: ['#00f2fe', '#1e293b'],
            borderWidth: 0
          }]
        },
        options: {
          responsive: true,
          plugins: { legend: { position: 'bottom', labels: { color: '#94a3b8' } } }
        }
      });
    }

    // 3. Product Term Coverage Chart
    const covCtx = document.getElementById('termCoverageChart');
    if (covCtx) {
      if (chartInstances.covChart) chartInstances.covChart.destroy();
      const termLabels = currentCompiled.productTerms.map(t => t.id);
      const termCounts = currentCompiled.productTerms.map(t => {
        return table.filter(r => r.active_terms.includes(t.id)).length;
      });

      chartInstances.covChart = new Chart(covCtx, {
        type: 'bar',
        data: {
          labels: termLabels,
          datasets: [{
            label: 'Minterms Covered',
            data: termCounts,
            backgroundColor: '#a855f7',
            borderRadius: 6
          }]
        },
        options: {
          responsive: true,
          plugins: { legend: { display: false } },
          scales: {
            y: { beginAtZero: true, max: 16, grid: { color: '#1e293b' } },
            x: { grid: { display: false } }
          }
        }
      });
    }
  }

  // --- Dataset Upload Handler ---
  const uploadBtn = document.getElementById('uploadDatasetBtn');
  const fileInput = document.getElementById('datasetFileInput');
  const statusMsg = document.getElementById('uploadStatusMsg');

  if (uploadBtn && fileInput) {
    uploadBtn.addEventListener('click', () => {
      const file = fileInput.files[0];
      if (!file) {
        alert('Please select a CSV or JSON file first');
        return;
      }
      const reader = new FileReader();
      reader.onload = async (e) => {
        const text = e.target.result;
        let records = [];
        try {
          if (file.name.endsWith('.json')) {
            records = JSON.parse(text);
          } else {
            // Simple CSV parse
            const lines = text.split('\n').map(l => l.trim()).filter(l => l.length > 0);
            const headers = lines[0].split(',').map(h => h.trim());
            for (let i = 1; i < lines.length; i++) {
              const row = lines[i].split(',').map(c => c.trim());
              const obj = {};
              headers.forEach((h, idx) => obj[h] = row[idx]);
              records.push(obj);
            }
          }
          const res = await client.uploadDataset(file.name, records);
          if (statusMsg) {
            statusMsg.textContent = res.message || 'Dataset uploaded successfully!';
          }
        } catch (err) {
          alert('Failed to parse file: ' + err.message);
        }
      };
      reader.readAsText(file);
    });
  }

  // --- Export CSV & Reports ---
  document.getElementById('exportTruthTableCsv')?.addEventListener('click', () => {
    window.location.href = `${client.baseUrl}/api/export/csv?target=truth_table`;
  });

  document.getElementById('exportTruthTableJson')?.addEventListener('click', () => {
    const table = PLACore.generateTruthTable(currentCompiled);
    const blob = new Blob([JSON.stringify(table, null, 2)], { type: 'application/json' });
    const url = URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = 'pla_truth_table.json';
    a.click();
    URL.revokeObjectURL(url);
  });

  document.getElementById('exportTestCasesCsv')?.addEventListener('click', () => {
    window.location.href = `${client.baseUrl}/api/export/csv?target=test_cases`;
  });

  document.getElementById('exportDatasetCsv')?.addEventListener('click', () => {
    window.location.href = `${client.baseUrl}/api/export/csv?target=dataset`;
  });

  document.getElementById('printReportBtn')?.addEventListener('click', () => {
    window.print();
  });

  // --- Guided Demo Tour ---
  const startTourBtn = document.getElementById('startTourBtn');
  if (startTourBtn) {
    startTourBtn.addEventListener('click', () => {
      const tourSteps = ['home', 'about', 'rules', 'product-terms', 'outputs', 'truth-table', 'simulator', 'conflicts', 'test-cases', 'analytics', 'deliverables'];
      let idx = 0;
      const interval = setInterval(() => {
        if (idx >= tourSteps.length) {
          clearInterval(interval);
          switchPage('simulator');
          return;
        }
        switchPage(tourSteps[idx]);
        idx++;
      }, 2500);
    });
  }

  // Initial load
  await refreshEngine();
  // Auto-run tests on startup to populate test dashboard
  setTimeout(() => {
    if (runTestsBtn) runTestsBtn.click();
  }, 400);
});
