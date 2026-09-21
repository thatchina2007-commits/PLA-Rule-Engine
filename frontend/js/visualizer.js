/**
 * PLA Interactive Matrix Visualizer (HTML5 Canvas)
 * Renders the programmable AND plane, OR plane, fusible crosspoints, and live animated signal pulses.
 */

class PLAVisualizer {
  constructor(canvasId) {
    this.canvas = document.getElementById(canvasId);
    if (!this.canvas) return;
    this.ctx = this.canvas.getContext('2d');
    this.animationFrameId = null;
    this.particles = [];
    this.pulseTime = 0;

    this.compiled = null;
    this.evalState = null;

    this.resizeCanvas();
    window.addEventListener('resize', () => this.resizeCanvas());
    this.startAnimation();
  }

  resizeCanvas() {
    if (!this.canvas) return;
    const rect = this.canvas.parentElement.getBoundingClientRect();
    this.canvas.width = rect.width;
    this.canvas.height = 480;
    this.render();
  }

  update(compiled, evalState) {
    this.compiled = compiled;
    this.evalState = evalState;
    this.render();
  }

  startAnimation() {
    const loop = () => {
      this.pulseTime += 0.05;
      this.render();
      this.animationFrameId = requestAnimationFrame(loop);
    };
    this.animationFrameId = requestAnimationFrame(loop);
  }

  render() {
    if (!this.canvas || !this.ctx) return;
    const ctx = this.ctx;
    const w = this.canvas.width;
    const h = this.canvas.height;

    // Clear background
    ctx.fillStyle = '#070b12';
    ctx.fillRect(0, 0, w, h);

    if (!this.compiled || !this.evalState) {
      ctx.fillStyle = '#64748b';
      ctx.font = '14px Inter, sans-serif';
      ctx.textAlign = 'center';
      ctx.fillText('Compiling PLA Architecture...', w / 2, h / 2);
      return;
    }

    const { productTerms, andMatrix, orMatrix, outputIds } = this.compiled;
    const { railsStatus, activeTerms, outputs } = this.evalState;

    const rails = ['A', "A'", 'B', "B'", 'C', "C'", 'D', "D'"];
    const numRails = rails.length;
    const numTerms = Math.min(productTerms.length, 10); // show up to 10 terms comfortably
    const numOutputs = outputIds.length;

    // Layout coordinates
    const leftMargin = 90;
    const railSpacing = Math.min(36, (w * 0.35) / numRails);
    const andStartX = leftMargin;
    const andEndX = andStartX + (numRails - 1) * railSpacing;

    const termStartY = 80;
    const termSpacing = Math.min(36, (h - 140) / Math.max(numTerms, 1));
    const andGateX = andEndX + 45;

    const orStartX = andGateX + 60;
    const outSpacing = Math.min(50, (w - orStartX - 100) / Math.max(numOutputs, 1));

    // 1. Draw Title and Labels
    ctx.fillStyle = '#38bdf8';
    ctx.font = 'bold 11px JetBrains Mono, monospace';
    ctx.textAlign = 'center';
    ctx.fillText('PROGRAMMABLE AND PLANE', (andStartX + andEndX) / 2, 28);
    ctx.fillStyle = '#a855f7';
    ctx.fillText('PROGRAMMABLE OR PLANE', orStartX + (numOutputs * outSpacing) / 2, 28);

    // 2. Draw Vertical Rails (Inputs & Inverters)
    for (let r = 0; r < numRails; r++) {
      const rx = andStartX + r * railSpacing;
      const rName = rails[r];
      const isHigh = railsStatus[rName] === 1;

      // Label at top
      ctx.fillStyle = isHigh ? '#00f2fe' : '#64748b';
      ctx.font = 'bold 12px JetBrains Mono, monospace';
      ctx.textAlign = 'center';
      ctx.fillText(rName, rx, 52);

      // Line
      ctx.strokeStyle = isHigh ? '#00f2fe' : '#1e293b';
      ctx.lineWidth = isHigh ? 2.5 : 1.2;
      if (isHigh) {
        ctx.shadowColor = '#00f2fe';
        ctx.shadowBlur = 8;
      } else {
        ctx.shadowBlur = 0;
      }
      ctx.beginPath();
      ctx.moveTo(rx, 60);
      ctx.lineTo(rx, termStartY + numTerms * termSpacing);
      ctx.stroke();
      ctx.shadowBlur = 0;
    }

    // 3. Draw Horizontal Product Term Lines & AND Crosspoints
    for (let t = 0; t < numTerms; t++) {
      const ty = termStartY + t * termSpacing;
      const termObj = productTerms[t];
      const isTermActive = activeTerms[termObj.id] === 1;

      // Line from before first rail to AND gate
      ctx.strokeStyle = isTermActive ? '#10b981' : '#1e293b';
      ctx.lineWidth = isTermActive ? 2.5 : 1.2;
      if (isTermActive) {
        ctx.shadowColor = '#10b981';
        ctx.shadowBlur = 10;
      }
      ctx.beginPath();
      ctx.moveTo(andStartX - 15, ty);
      ctx.lineTo(andGateX, ty);
      ctx.stroke();
      ctx.shadowBlur = 0;

      // Draw AND gate symbol at andGateX
      this.drawAndGate(ctx, andGateX, ty, isTermActive);

      // Term label (P0, P1...)
      ctx.fillStyle = isTermActive ? '#10b981' : '#64748b';
      ctx.font = '10px JetBrains Mono, monospace';
      ctx.textAlign = 'right';
      ctx.fillText(termObj.term_str || termObj.id, andStartX - 20, ty + 4);

      // Draw Programmable AND Crosspoints (Fuses)
      for (let r = 0; r < numRails; r++) {
        const rx = andStartX + r * railSpacing;
        if (andMatrix[t] && andMatrix[t][r] === 1) {
          const rName = rails[r];
          const fuseActive = railsStatus[rName] === 1;
          ctx.beginPath();
          ctx.arc(rx, ty, 4.5, 0, Math.PI * 2);
          ctx.fillStyle = fuseActive ? '#00f2fe' : '#475569';
          ctx.fill();
          ctx.strokeStyle = fuseActive ? '#fff' : '#070b12';
          ctx.lineWidth = 1;
          ctx.stroke();
        }
      }

      // Line extending from AND gate to OR plane
      const postAndX = andGateX + 18;
      const orLineEndX = orStartX + (numOutputs - 1) * outSpacing + 25;
      ctx.strokeStyle = isTermActive ? '#10b981' : '#1e293b';
      ctx.lineWidth = isTermActive ? 2.5 : 1.2;
      if (isTermActive) {
        ctx.shadowColor = '#10b981';
        ctx.shadowBlur = 8;
      }
      ctx.beginPath();
      ctx.moveTo(postAndX, ty);
      ctx.lineTo(orLineEndX, ty);
      ctx.stroke();
      ctx.shadowBlur = 0;

      // Draw OR Crosspoints for this product term
      for (let o = 0; o < numOutputs; o++) {
        const ox = orStartX + o * outSpacing;
        if (orMatrix[o] && orMatrix[o][t] === 1) {
          const orFuseActive = isTermActive;
          ctx.beginPath();
          ctx.arc(ox, ty, 4.5, 0, Math.PI * 2);
          ctx.fillStyle = orFuseActive ? '#10b981' : '#475569';
          ctx.fill();
          ctx.strokeStyle = orFuseActive ? '#fff' : '#070b12';
          ctx.lineWidth = 1;
          ctx.stroke();
        }
      }
    }

    // 4. Draw Vertical Output Lines & OR Gates
    for (let o = 0; o < numOutputs; o++) {
      const ox = orStartX + o * outSpacing;
      const outId = outputIds[o];
      const isOutHigh = outputs[outId] === 1;

      // Output vertical line
      ctx.strokeStyle = isOutHigh ? '#f59e0b' : '#1e293b';
      ctx.lineWidth = isOutHigh ? 2.5 : 1.2;
      if (isOutHigh) {
        ctx.shadowColor = '#f59e0b';
        ctx.shadowBlur = 10;
      }
      ctx.beginPath();
      ctx.moveTo(ox, termStartY - 15);
      ctx.lineTo(ox, termStartY + numTerms * termSpacing + 20);
      ctx.stroke();
      ctx.shadowBlur = 0;

      // Draw OR Gate symbol at the bottom
      const orGateY = termStartY + numTerms * termSpacing + 35;
      this.drawOrGate(ctx, ox, orGateY, isOutHigh);

      // Output Label & Logic Level
      ctx.fillStyle = isOutHigh ? '#f59e0b' : '#64748b';
      ctx.font = 'bold 12px JetBrains Mono, monospace';
      ctx.textAlign = 'center';
      ctx.fillText(outId, ox, orGateY + 36);

      // Logic level badge
      ctx.fillStyle = isOutHigh ? 'rgba(245, 158, 11, 0.2)' : 'rgba(100, 116, 139, 0.2)';
      ctx.strokeStyle = isOutHigh ? '#f59e0b' : '#334155';
      ctx.fillRect(ox - 16, orGateY + 44, 32, 20);
      ctx.strokeRect(ox - 16, orGateY + 44, 32, 20);
      ctx.fillStyle = isOutHigh ? '#fff' : '#64748b';
      ctx.font = 'bold 11px JetBrains Mono, monospace';
      ctx.fillText(isOutHigh ? 'HIGH' : 'LOW', ox, orGateY + 58);
    }
  }

  drawAndGate(ctx, x, y, active) {
    ctx.save();
    ctx.strokeStyle = active ? '#10b981' : '#475569';
    ctx.fillStyle = active ? 'rgba(16, 185, 129, 0.25)' : '#111827';
    ctx.lineWidth = 1.8;
    ctx.beginPath();
    ctx.moveTo(x - 4, y - 10);
    ctx.lineTo(x + 4, y - 10);
    ctx.arc(x + 4, y, 10, -Math.PI / 2, Math.PI / 2);
    ctx.lineTo(x - 4, y + 10);
    ctx.closePath();
    ctx.fill();
    ctx.stroke();
    ctx.restore();
  }

  drawOrGate(ctx, x, y, active) {
    ctx.save();
    ctx.strokeStyle = active ? '#f59e0b' : '#475569';
    ctx.fillStyle = active ? 'rgba(245, 158, 11, 0.25)' : '#111827';
    ctx.lineWidth = 1.8;
    ctx.beginPath();
    ctx.moveTo(x - 12, y - 8);
    ctx.quadraticCurveTo(x, y - 3, x + 12, y - 8);
    ctx.quadraticCurveTo(x + 8, y + 10, x, y + 18);
    ctx.quadraticCurveTo(x - 8, y + 10, x - 12, y - 8);
    ctx.closePath();
    ctx.fill();
    ctx.stroke();
    ctx.restore();
  }
}

window.PLAVisualizer = PLAVisualizer;
