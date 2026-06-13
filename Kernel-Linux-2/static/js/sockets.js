const SOCK = {
  currentTool: 'list',

  init() {
    this.initTabs();
    this.initForms();
    this.showTool('list');
    this.loadOverview();
    document.getElementById('sk-last-update').textContent = new Date().toLocaleTimeString();
  },

  initTabs() {
    document.querySelectorAll('.sk-tool-tab').forEach(tab => {
      tab.addEventListener('click', () => {
        const tool = tab.dataset.tool;
        this.showTool(tool);
      });
    });
  },

  initForms() {
    document.querySelectorAll('.sk-tool-panel').forEach(panel => {
      const form = panel.querySelector('.sk-tool-form');
      if (!form) return;
      form.addEventListener('submit', async (e) => {
        e.preventDefault();
        const tool = panel.id.replace('panel-', '');
        const fd = new FormData(form);
        await this.executeTool(tool, Object.fromEntries(fd));
      });
    });
  },

  showTool(tool) {
    this.currentTool = tool;
    document.querySelectorAll('.sk-tool-tab').forEach(t => t.classList.toggle('active', t.dataset.tool === tool));
    document.querySelectorAll('.sk-tool-panel').forEach(p => p.classList.toggle('active', p.id === `panel-${tool}`));
  },

  async loadOverview() {
    try {
      const res = await this._post('/sockets/api/overview');
      if (res.error) return;
      const m = res.metrics || {};
      this.setKpi('sk-kpi-total', m.total || '0');
      this.setKpi('sk-kpi-tcp', m.tcp || '0');
      this.setKpi('sk-kpi-udp', m.udp || '0');
      this.setKpi('sk-kpi-listen', m.listening || '0');
      this.setKpi('sk-kpi-estab', m.established || '0');
      this.setKpi('sk-kpi-timewait', m.time_wait || '0');
      this.setKpi('sk-kpi-closewait', m.close_wait || '0');

      const tbody = document.getElementById('sk-top-proc-body');
      if (tbody && res.top_processes) {
        tbody.innerHTML = res.top_processes.map(r =>
          `<tr><td>${this._e(r.col_1 || '0')}</td><td>${this._e(r.col_2 || '-')}</td><td>${this._e(r.col_3 || '-')}</td></tr>`
        ).join('') || '<tr><td colspan="3" class="text-muted small">No data</td></tr>';
      }
    } catch (_) {}
  },

  setKpi(id, val) {
    const el = document.getElementById(id);
    if (el) el.textContent = val;
  },

  async executeTool(tool, params) {
    const viewer = document.getElementById('sk-result-body');
    const title = document.getElementById('sk-result-title');
    viewer.innerHTML = '<span class="sk-spinner"></span> Running...';
    const names = { list: 'All Sockets', tcp: 'TCP Sockets', udp: 'UDP Sockets', listening: 'Listening Ports', byprocess: 'Socket By Process', stats: 'Connection Stats', close: 'Close Connection' };
    title.textContent = names[tool] || tool;

    let result;
    switch (tool) {
      case 'list': result = await this._post('/sockets/api/list'); break;
      case 'tcp': result = await this._post('/sockets/api/tcp'); break;
      case 'udp': result = await this._post('/sockets/api/udp'); break;
      case 'listening': result = await this._post('/sockets/api/listening'); break;
      case 'byprocess': result = await this._post('/sockets/api/by-process', params); break;
      case 'stats': result = await this._post('/sockets/api/stats'); break;
      case 'close': result = await this._post('/sockets/api/close', params); break;
    }

    if (result.error) {
      viewer.innerHTML = `<span class="text-sk-red">${this._e(result.error)}</span>`;
      return;
    }

    if (tool === 'close') {
      viewer.innerHTML = `<span class="text-sk-green">${this._e(result.message)}</span>`;
      if (result.output) viewer.innerHTML += `<pre class="mt-2 small">${this._e(result.output)}</pre>`;
      this.showToast(result.message, 'success');
      setTimeout(() => this.loadOverview(), 500);
      return;
    }

    if (tool === 'stats' && result.kind === 'json' && result.data) {
      viewer.innerHTML = '<dl class="row g-2 mb-0">' +
        Object.entries(result.data).map(([k, v]) =>
          `<dt class="col-sm-5 text-sk-cyan small">${this._e(k)}</dt><dd class="col-sm-7 font-monospace small fw-bold">${this._e(v)}</dd>`
        ).join('') + '</dl>';
      document.getElementById('sk-last-update').textContent = new Date().toLocaleTimeString();
      return;
    }

    this.renderTable(result);
  },

  renderTable(data) {
    const viewer = document.getElementById('sk-result-body');
    const rows = data.rows || [];
    const output = data.output || '';

    if (rows.length === 0) {
      viewer.innerHTML = `<pre class="mb-0">${this._e(output || 'No results')}</pre>`;
      document.getElementById('sk-last-update').textContent = new Date().toLocaleTimeString();
      return;
    }

    const headers = Object.keys(rows[0]);
    const stateCol = headers.findIndex(h => h.toLowerCase().includes('state') || h.includes('col_4'));
    const protoCol = headers.findIndex(h => h.toLowerCase().includes('proto') || h.includes('col_1'));

    let html = '<div class="sk-table-wrap"><table class="sk-table"><thead><tr>';
    html += headers.map(h => `<th>${this._e(h.replace(/^col_\d+/, ''))}</th>`).join('');
    html += '</tr></thead><tbody>';
    html += rows.map(row => {
      const vals = headers.map(h => row[h] || '');
      const state = stateCol >= 0 ? vals[stateCol] : '';
      const proto = protoCol >= 0 ? vals[protoCol] : '';
      const stateClass = this._stateClass(state, proto);
      return '<tr>' + vals.map((v, i) => {
        if (i === stateCol) return `<td><span class="sk-state-badge ${stateClass}">${this._e(v)}</span></td>`;
        return `<td>${this._e(v)}</td>`;
      }).join('') + '</tr>';
    }).join('');
    html += '</tbody></table></div>';
    if (output) html += `<details class="mt-2"><summary class="text-sk-cyan small" style="cursor:pointer">Raw output</summary><pre class="mt-1 small" style="color:var(--sk-text-muted)">${this._e(output)}</pre></details>`;
    viewer.innerHTML = html;
    document.getElementById('sk-last-update').textContent = new Date().toLocaleTimeString();
  },

  _stateClass(state, proto) {
    const s = state.toUpperCase();
    if (s === 'ESTAB' || s === 'ESTABLISHED') return 'sk-state-established';
    if (s === 'LISTEN') return 'sk-state-listen';
    if (s === 'TIME-WAIT' || s === 'TIME_WAIT') return 'sk-state-time-wait';
    if (s === 'CLOSE-WAIT' || s === 'CLOSE_WAIT') return 'sk-state-close-wait';
    return 'sk-state-other';
  },

  showToast(message, type) {
    const container = document.getElementById('sk-toast-container');
    if (!container) return;
    const toast = document.createElement('div');
    toast.className = `sk-toast p-3 mb-2 small`;
    toast.innerHTML = `<i class="fa fa-${type === 'success' ? 'check-circle text-sk-green' : 'exclamation-circle text-sk-red'} me-2"></i>${this._e(message)}`;
    container.appendChild(toast);
    setTimeout(() => { toast.style.opacity = '0'; toast.style.transition = 'opacity .3s'; setTimeout(() => toast.remove(), 300); }, 3000);
  },

  async _post(url, data) {
    const form = new URLSearchParams();
    if (data) for (const [k, v] of Object.entries(data)) { if (v !== undefined && v !== null) form.append(k, String(v)); }
    try {
      const res = await fetch(url, { method: 'POST', headers: { 'Content-Type': 'application/x-www-form-urlencoded' }, body: form });
      if (!res.ok) throw new Error((await res.text()) || `Request failed (${res.status})`);
      return await res.json();
    } catch (e) {
      return { error: e.message };
    }
  },

  _e(str) {
    if (!str) return '';
    return String(str).replace(/&/g, '&amp;').replace(/</g, '&lt;').replace(/>/g, '&gt;').replace(/"/g, '&quot;');
  },
};

document.addEventListener('DOMContentLoaded', () => SOCK.init());
