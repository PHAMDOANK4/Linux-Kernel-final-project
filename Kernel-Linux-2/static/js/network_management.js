const NET = {
  autoTimer: null,
  refreshMs: 10000,

  init() {
    this.initTabs();
    this.initForms();
    this.initEvents();
    this.loadKPI();
    this.loadInterfaces();
    this.loadRoutes();
    this.setLastUpdate();

    const sel = document.getElementById('nm-refresh-interval');
    if (sel) {
      sel.addEventListener('change', () => {
        this.refreshMs = parseInt(sel.value) || 0;
        this.stopAuto();
        if (this.refreshMs > 0) this.startAuto();
      });
    }
    this.startAuto();
  },

  setLastUpdate() {
    const el = document.getElementById('nm-last-update');
    if (el) el.textContent = new Date().toLocaleTimeString();
  },

  initTabs() {
    document.querySelectorAll('.nm-tool-tab').forEach(tab => {
      tab.addEventListener('click', () => {
        document.querySelectorAll('.nm-tool-tab').forEach(t => t.classList.remove('active'));
        tab.classList.add('active');
        const tool = tab.dataset.tool;
        document.querySelectorAll('.nm-tool-form').forEach(f => f.classList.remove('active'));
        const form = document.getElementById('tool-' + tool);
        if (form) form.classList.add('active');
      });
    });
  },

  initForms() {
    document.querySelectorAll('.nm-tool-form').forEach(form => {
      const btn = form.querySelector('.nm-run-btn');
      if (!btn) return;
      btn.addEventListener('click', async () => {
        const tool = form.id.replace('tool-', '');
        const inputs = form.querySelectorAll('input, select');
        const params = {};
        inputs.forEach(inp => { if (inp.name) params[inp.name] = inp.value; });
        await this.executeTool(tool, params);
      });
    });
  },

  initEvents() {
    const ifaceSearch = document.getElementById('iface-search');
    if (ifaceSearch) ifaceSearch.addEventListener('input', () => this.filterInterfaces());
    const ifaceFilter = document.getElementById('iface-filter-status');
    if (ifaceFilter) ifaceFilter.addEventListener('change', () => this.filterInterfaces());
    const ifaceRefresh = document.getElementById('iface-refresh-btn');
    if (ifaceRefresh) ifaceRefresh.addEventListener('click', () => this.loadInterfaces());

    const routeSearch = document.getElementById('route-search');
    if (routeSearch) routeSearch.addEventListener('input', () => this.filterRoutes());
    const routeRefresh = document.getElementById('route-refresh-btn');
    if (routeRefresh) routeRefresh.addEventListener('click', () => this.loadRoutes());

    const copyBtn = document.getElementById('copy-result-btn');
    if (copyBtn) {
      copyBtn.addEventListener('click', () => {
        const body = document.getElementById('tool-result-body');
        if (!body) return;
        navigator.clipboard.writeText(body.textContent).catch(() => {});
      });
    }
  },

  /* ── KPI ──────────────────────────────────── */
  async loadKPI() {
    try {
      const res = await fetch('/network/api/overview');
      const data = await res.json();
      if (data.error) return;
      const ipVal = document.getElementById('kpi-ip-val');
      const ipSub = document.getElementById('kpi-ip-sub');
      if (ipVal) { ipVal.textContent = data.current_ip || '—'; ipVal.classList.remove('nm-skeleton'); }
      if (ipSub) ipSub.textContent = data.gateway ? 'GW: ' + data.gateway : 'Không có gateway';

      const ifVal = document.getElementById('kpi-ifaces-val');
      const ifSub = document.getElementById('kpi-ifaces-sub');
      if (ifVal) { ifVal.textContent = String(data.active_interfaces ?? '—'); ifVal.classList.remove('nm-skeleton'); }
      if (ifSub) ifSub.textContent = 'giao diện đang hoạt động';

      const stVal = document.getElementById('kpi-status-val');
      const stSub = document.getElementById('kpi-status-sub');
      const online = data.network_status === 'online';
      if (stVal) { stVal.textContent = online ? 'Online' : 'Offline'; stVal.classList.remove('nm-skeleton'); }
      if (stSub) stSub.textContent = online ? 'Bình thường' : 'Kiểm tra lại';

      this.setLastUpdate();
    } catch (_) {}
  },

  /* ── Interfaces ───────────────────────────── */
  async loadInterfaces() {
    const tbody = document.getElementById('iface-tbody');
    if (!tbody) return;
    tbody.innerHTML = '<tr><td colspan="5" class="text-center py-3"><span class="nm-spinner"></span> Đang tải…</td></tr>';
    try {
      const res = await fetch('/network/api/interfaces');
      const data = await res.json();
      if (data.error) throw new Error(data.error);
      this._allIfaces = data.interfaces || [];
      const el = document.getElementById('iface-count');
      if (el) el.textContent = this._allIfaces.length;
      this.filterInterfaces();
    } catch (_) {
      tbody.innerHTML = '<tr><td colspan="5" class="text-muted small text-center py-3">Lỗi tải dữ liệu</td></tr>';
    }
  },

  filterInterfaces() {
    const query = (document.getElementById('iface-search')?.value || '').toLowerCase();
    const status = (document.getElementById('iface-filter-status')?.value || '').toUpperCase();
    const tbody = document.getElementById('iface-tbody');
    const items = (this._allIfaces || []).filter(i => {
      const name = (i.Interface || i.name || '').toLowerCase();
      const ip = (i['IP Address'] || i.ip_address || i.ip || '');
      if (query && !name.includes(query) && !ip.toLowerCase().includes(query)) return false;
      if (status) {
        const isUp = ip && ip !== 'None' && ip !== '';
        if (status === 'UP' && !isUp) return false;
        if (status === 'DOWN' && isUp) return false;
      }
      return true;
    });
    tbody.innerHTML = items.map(i => {
      const name = i.Interface || i.name || '—';
      const ip = (i['IP Address'] || i.ip_address || i.ip || '—');
      const mac = (i['MAC Address'] || i.mac_address || i.mac || '—');
      const mask = i.Netmask || i.netmask || '—';
      const isUp = ip !== '—' && ip !== 'None';
      return `<tr>
        <td><strong>${this._e(name)}</strong></td>
        <td><span class="nm-tbl-badge ${isUp ? 'nm-tbl-up' : 'nm-tbl-down'}">${isUp ? 'UP' : 'DOWN'}</span></td>
        <td><code>${this._e(ip)}</code></td>
        <td><code>${this._e(mac)}</code></td>
        <td>${this._e(mask)}</td>
      </tr>`;
    }).join('') || '<tr><td colspan="5" class="text-muted small text-center py-3">Không có kết quả</td></tr>';
  },

  /* ── Routes ───────────────────────────────── */
  async loadRoutes() {
    const tbody = document.getElementById('route-tbody');
    if (!tbody) return;
    tbody.innerHTML = '<tr><td colspan="3" class="text-center py-3"><span class="nm-spinner"></span> Đang tải…</td></tr>';
    try {
      const res = await fetch('/network/api/routes');
      const data = await res.json();
      if (data.error) throw new Error(data.error);
      this._allRoutes = data.routes || [];
      this.filterRoutes();
    } catch (_) {
      tbody.innerHTML = '<tr><td colspan="3" class="text-muted small text-center py-3">Lỗi tải dữ liệu</td></tr>';
    }
  },

  filterRoutes() {
    const query = (document.getElementById('route-search')?.value || '').toLowerCase();
    const tbody = document.getElementById('route-tbody');
    const items = (this._allRoutes || []).filter(r => {
      const all = Object.values(r).join(' ').toLowerCase();
      return !query || all.includes(query);
    });
    tbody.innerHTML = items.map(r => {
      const dest = r.Destination || r.destination || '—';
      const gw = r.Gateway || r.gateway || '—';
      const iface = r.Iface || r.interface || r.Interface || '—';
      return `<tr><td><code>${this._e(dest)}</code></td><td><code>${this._e(gw)}</code></td><td>${this._e(iface)}</td></tr>`;
    }).join('') || '<tr><td colspan="3" class="text-muted small text-center py-3">Không có kết quả</td></tr>';
  },

  /* ── Execute Tool ─────────────────────────── */
  async executeTool(tool, params) {
    const body = document.getElementById('tool-result-body');
    const title = document.getElementById('tool-result-title');
    if (!body) return;
    body.innerHTML = '<div class="d-flex align-items-center gap-2"><span class="nm-spinner"></span> Đang chạy…</div>';
    if (title) title.textContent = tool.charAt(0).toUpperCase() + tool.slice(1);

    const apiPath = this._toolApi(tool);
    if (!apiPath) {
      body.textContent = 'Không rõ công cụ: ' + tool;
      return;
    }

    const fd = new FormData();
    for (const [k, v] of Object.entries(params)) {
      fd.append(k, v);
    }

    try {
      const res = await fetch(apiPath, { method: 'POST', body: fd });
      const data = await res.json();
      if (data.error) {
        body.innerHTML = '<span class="nm-err">' + this._e(data.error) + '</span>';
        return;
      }
      body.textContent = data.output || '(không có dữ liệu)';
    } catch (err) {
      body.textContent = 'Lỗi: ' + err.message;
    }
  },

  _toolApi(tool) {
    const map = {
      ping: '/network/api/ping',
      traceroute: '/network/api/traceroute',
      portcheck: '/network/api/port-check',
      portscan: '/network/api/port-scan',
      dns: '/network/api/dns',
      bandwidth: '/network/api/bandwidth',
      toggle: '/network/api/toggle',
      changeip: '/network/api/change-ip',
    };
    return map[tool] || null;
  },

  startAuto() {
    this.stopAuto();
    this.autoTimer = setInterval(() => {
      this.loadKPI();
      this.loadInterfaces();
      this.loadRoutes();
    }, this.refreshMs);
  },

  stopAuto() {
    if (this.autoTimer) { clearInterval(this.autoTimer); this.autoTimer = null; }
  },

  _e(str) {
    if (str === null || str === undefined) return '';
    return String(str).replace(/&/g, '&amp;').replace(/</g, '&lt;').replace(/>/g, '&gt;').replace(/"/g, '&quot;');
  },
};

document.addEventListener('DOMContentLoaded', () => NET.init());
