const API = {
  async open(path) {
    return this._post('/files/api/open', { path });
  },
  async locked(path) {
    return this._post('/files/api/locked', { path });
  },
  async watch(path, duration) {
    return this._post('/files/api/watch', { path, duration });
  },
  async dirSize(path) {
    return this._post('/files/api/directory-size', { path });
  },
  async largeFiles(path, size) {
    return this._post('/files/api/large-files', { path, size });
  },
  async permission(path) {
    return this._post('/files/api/permission', { path });
  },
  async _post(url, data) {
    const form = new URLSearchParams();
    for (const [k, v] of Object.entries(data)) {
      if (v !== undefined && v !== null) form.append(k, String(v));
    }
    try {
      const res = await fetch(url, { method: 'POST', headers: { 'Content-Type': 'application/x-www-form-urlencoded' }, body: form });
      if (!res.ok) throw new Error((await res.text()) || `Request failed (${res.status})`);
      return await res.json();
    } catch (e) {
      return { error: e.message };
    }
  },
};

const FM = {
  currentTool: 'open',
  pathHistory: [],

  init() {
    this.initTabs();
    this.initQuickPaths();
    this.initForms();
    this.showTool('open');
    document.getElementById('fm-last-update').textContent = new Date().toLocaleTimeString();
  },

  initTabs() {
    document.querySelectorAll('.fm-tool-tab').forEach(tab => {
      tab.addEventListener('click', () => {
        const tool = tab.dataset.tool;
        if (tool === 'clear') {
          this.clearResult();
          return;
        }
        this.showTool(tool);
      });
    });
  },

  initQuickPaths() {
    document.querySelectorAll('.fm-quick-path').forEach(el => {
      el.addEventListener('click', () => {
        const tool = el.closest('.fm-tool-panel');
        const input = tool?.querySelector('.fm-path-input');
        if (input) {
          input.value = el.textContent.trim();
          input.focus();
        }
      });
    });
  },

  initForms() {
    document.querySelectorAll('.fm-tool-panel').forEach(panel => {
      const form = panel.querySelector('.fm-tool-form');
      if (!form) return;
      form.addEventListener('submit', async (e) => {
        e.preventDefault();
        const tool = panel.id.replace('panel-', '');
        const formData = new FormData(form);
        const path = formData.get('path') || '';
        const duration = formData.get('duration') || '10';
        const size = formData.get('size') || '+100M';
        await this.executeTool(tool, { path, duration, size });
      });
    });
  },

  showTool(tool) {
    this.currentTool = tool;
    document.querySelectorAll('.fm-tool-tab').forEach(t => t.classList.toggle('active', t.dataset.tool === tool));
    document.querySelectorAll('.fm-tool-panel').forEach(p => p.classList.toggle('active', p.id === `panel-${tool}`));
  },

  async executeTool(tool, params) {
    const viewer = document.getElementById('fm-result-body');
    const title = document.getElementById('fm-result-title');
    viewer.innerHTML = '<span class="fm-spinner"></span> Running...';
    const toolNames = { open: 'Open Files', locked: 'Locked Files', watch: 'Watch File', dirsize: 'Directory Size', large: 'Large Files', perm: 'File Permission' };
    title.textContent = toolNames[tool] || tool;

    let result;
    switch (tool) {
      case 'open': result = await API.open(params.path); break;
      case 'locked': result = await API.locked(params.path); break;
      case 'watch': result = await API.watch(params.path, params.duration); break;
      case 'dirsize': result = await API.dirSize(params.path); break;
      case 'large': result = await API.largeFiles(params.path, params.size); break;
      case 'perm': result = await API.permission(params.path); break;
    }

    if (result.error) {
      viewer.innerHTML = `<span class="text-fm-red">${this.escapeHtml(result.error)}</span>`;
      return;
    }
    this.renderResult(result);
  },

  renderResult(data) {
    const viewer = document.getElementById('fm-result-body');
    const output = data.output || '';
    const rows = data.rows || [];
    const kind = data.kind || 'raw';

    if (kind === 'table' && rows.length > 0) {
      const headers = Object.keys(rows[0]);
      let html = '<div class="fm-table-wrap"><table class="fm-table"><thead><tr>';
      html += headers.map(h => `<th>${this.escapeHtml(h.replace(/^col_\d+/, 'Value'))}</th>`).join('');
      html += '</tr></thead><tbody>';
      html += rows.map(row => {
        return '<tr>' + headers.map(h => `<td>${this.escapeHtml(row[h] || '')}</td>`).join('') + '</tr>';
      }).join('');
      html += '</tbody></table></div>';
      if (output) html += `<details class="mt-2"><summary class="text-fm-cyan small" style="cursor:pointer">Raw output</summary><pre class="mt-1 small" style="color:var(--fm-text-muted)">${this.escapeHtml(output)}</pre></details>`;
      viewer.innerHTML = html;
    } else if (kind === 'kv') {
      let html = '<dl class="row g-2 mb-0">';
      for (const [key, value] of Object.entries(data.items || {})) {
        html += `<dt class="col-sm-5 text-fm-cyan small">${this.escapeHtml(key)}</dt><dd class="col-sm-7 font-monospace small">${this.escapeHtml(value)}</dd>`;
      }
      html += '</dl>';
      viewer.innerHTML = html;
    } else {
      viewer.innerHTML = `<pre class="mb-0">${this.escapeHtml(output)}</pre>`;
    }

    document.getElementById('fm-last-update').textContent = new Date().toLocaleTimeString();
  },

  clearResult() {
    document.getElementById('fm-result-body').innerHTML = '<span class="text-muted small">Run a tool to see output here...</span>';
    document.getElementById('fm-result-title').textContent = 'Output';
  },

  escapeHtml(str) {
    if (!str) return '';
    return String(str).replace(/&/g, '&amp;').replace(/</g, '&lt;').replace(/>/g, '&gt;').replace(/"/g, '&quot;');
  },
};

document.addEventListener('DOMContentLoaded', () => FM.init());
