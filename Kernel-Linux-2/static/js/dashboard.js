(function(){
  'use strict';

  const $ = id => document.getElementById(id);
  const qs = (el, s) => (el||document).querySelector(s);
  const qsa = (el, s) => (el||document).querySelectorAll(s);

  let intervalId = null;
  const DEFAULT_INTERVAL = 5000;

  function $(id) { return document.getElementById(id); }

  function fmt(s) { return s ?? '—'; }

  function nfmt(n) {
    if (n === null || n === undefined) return '—';
    const v = parseFloat(n);
    if (isNaN(v)) return '—';
    if (v >= 1e9) return (v/1e9).toFixed(1) + ' GB';
    if (v >= 1e6) return (v/1e6).toFixed(1) + ' MB';
    if (v >= 1e3) return (v/1e3).toFixed(1) + ' KB';
    return v.toFixed(1) + ' B';
  }

  function pct(v) {
    const n = parseFloat(v);
    return isNaN(n) ? '—' : n.toFixed(1) + '%';
  }

  function barPct(v, max=100) {
    const n = parseFloat(v);
    if (isNaN(n) || max <= 0) return 0;
    return Math.min(100, Math.max(0, (n/max)*100));
  }

  function kpiColor(v) {
    const n = parseFloat(v);
    if (isNaN(n)) return 'var(--db-blue)';
    if (n >= 90) return 'var(--db-red)';
    if (n >= 70) return 'var(--db-orange)';
    return 'var(--db-green)';
  }

  function renderKpi(id, label, value, sub, icon, color) {
    const el = $(id);
    if (!el) return;
    el.innerHTML = `
      <div class="db-kpi-icon" style="background:${color}22;color:${color}">${icon}</div>
      <div class="db-kpi-label">${label}</div>
      <div class="db-kpi-value">${value}</div>
      <div class="db-kpi-sub">${sub}</div>
    `;
  }

  function renderBar(value, max=100, color='var(--db-blue)') {
    const p = barPct(value, max);
    return `<div style="background:var(--db-surface-2);border-radius:4px;height:6px;overflow:hidden"><div style="height:100%;width:${p}%;background:${color};border-radius:4px;transition:width .4s ease"></div></div>`;
  }

  function loadMetrics() {
    fetch('/api/dashboard/metrics')
      .then(r => r.json())
      .then(d => {
        if (d.status !== 'success') return;
        const sys = d.system || {};
        const cpuPct = sys.cpu_percent ?? 0;
        const memPct = sys.memory_percent ?? 0;
        const diskPct = sys.disk_percent ?? 0;
        const uptimeSec = parseInt(sys.uptime) || 0;
        const days = Math.floor(uptimeSec / 86400);
        const hours = Math.floor((uptimeSec % 86400) / 3600);
        const mins = Math.floor((uptimeSec % 3600) / 60);
        const uptimeStr = days + 'd ' + hours + 'h ' + mins + 'm';
        const procCount = sys.process_count ?? '—';
        const netSent = sys.network_sent ?? 0;
        const netRecv = sys.network_recv ?? 0;

        renderKpi('db-kpi-cpu', 'CPU', pct(cpuPct), renderBar(cpuPct, 100, kpiColor(cpuPct)), '⚡', kpiColor(cpuPct));
        renderKpi('db-kpi-mem', 'RAM', pct(memPct), renderBar(memPct, 100, kpiColor(memPct)), '🧠', kpiColor(memPct));
        renderKpi('db-kpi-disk', 'Ổ đĩa', pct(diskPct), renderBar(diskPct, 100, kpiColor(diskPct)), '💾', kpiColor(diskPct));
        renderKpi('db-kpi-uptime', 'Uptime', uptimeStr, '', '⏱️', 'var(--db-cyan)');
        renderKpi('db-kpi-proc', 'Tiến trình', procCount, 'processes', '📊', 'var(--db-purple)');
        renderKpi('db-kpi-net', 'Mạng', nfmt(netSent) + ' / ' + nfmt(netRecv), '↑ tx / ↓ rx', '🌐', 'var(--db-blue)');

        const procList = d.top_processes || [];
        const tbody = qs(document.getElementById('db-proc-table'), 'tbody');
        if (tbody) {
          tbody.innerHTML = procList.map(p => {
            const pc = parseFloat(p.cpu) || 0;
            const pm = parseFloat(p.mem) || 0;
            return `<tr>
              <td><span style="color:var(--db-cyan)">${fmt(p.pid)}</span></td>
              <td>${fmt(p.name)}</td>
              <td>${fmt(p.user)}</td>
              <td>${pct(p.cpu)} ${renderBar(pc, 100, 'var(--db-orange)')}</td>
              <td>${pct(p.mem)} ${renderBar(pm, 100, 'var(--db-blue)')}</td>
            </tr>`;
          }).join('');
        }

        const netBody = qs(document.getElementById('db-net-table'), 'tbody');
        if (netBody) {
          const netIf = d.network_interfaces || [];
          netBody.innerHTML = netIf.map(n => {
            const tx = parseFloat(n.bytes_sent) || 0;
            const rx = parseFloat(n.bytes_recv) || 0;
            return `<tr>
              <td><span style="color:var(--db-cyan)">${fmt(n.interface)}</span></td>
              <td>${nfmt(tx)}</td>
              <td>${nfmt(rx)}</td>
              <td>${fmt(n.ip)}</td>
              <td>${fmt(n.status)}</td>
            </tr>`;
          }).join('');
        }

        const actBody = qs(document.getElementById('db-activity-table'), 'tbody');
        if (actBody) {
          const acts = d.recent_activities || [];
          actBody.innerHTML = acts.map(a => `<tr>
            <td>${fmt(a.time)}</td>
            <td>${fmt(a.user)}</td>
            <td>${fmt(a.action)}</td>
          </tr>`).join('');
        }
      })
      .catch(() => {});
  }

  function init() {
    loadMetrics();
    if (intervalId) clearInterval(intervalId);
    intervalId = setInterval(loadMetrics, DEFAULT_INTERVAL);
    document.addEventListener('visibilitychange', () => {
      if (document.hidden && intervalId) {
        clearInterval(intervalId);
        intervalId = null;
      } else if (!document.hidden && !intervalId) {
        loadMetrics();
        intervalId = setInterval(loadMetrics, DEFAULT_INTERVAL);
      }
    });
  }

  if (document.readyState === 'loading') document.addEventListener('DOMContentLoaded', init);
  else init();
})();
