(function(){
  'use strict';

  const $ = id => document.getElementById(id);
  const qs = (el, s) => (el || document).querySelector(s);
  const qsa = (el, s) => (el || document).querySelectorAll(s);

  let processes = [];
  let timerId = null;
  const REFRESH_MS = 8000;

  function escapeHtml(text) {
    const d = document.createElement('div');
    d.textContent = text;
    return d.innerHTML;
  }

  function toast(msg, type) {
    const el = document.createElement('div');
    el.className = 'pr-toast pr-toast-' + type;
    el.innerHTML = '<span>' + escapeHtml(msg) + '</span>';
    document.body.appendChild(el);
    setTimeout(() => { el.remove(); }, 3000);
  }

  function loading(show) {
    const tbody = qs($('pr-table'), 'tbody');
    if (!tbody) return;
    if (show) {
      tbody.innerHTML = '<tr><td colspan="8" style="text-align:center;padding:2.5rem 0;color:var(--pr-text-muted)">\n<div style="display:inline-block;width:20px;height:20px;border:2px solid var(--pr-border-2);border-top-color:var(--pr-cyan);border-radius:50%;animation:pr-spin .6s linear infinite;margin-bottom:8px"></div>\n<div>Đang tải...</div></td></tr>';
    }
  }

  function renderRow(p) {
    const cpu = parseFloat(p.cpu) || 0;
    const mem = parseFloat(p.mem) || 0;
    return '<tr data-pid="' + escapeHtml(p.pid) + '">\n' +
      '<td style="color:var(--pr-cyan);font-weight:600">' + escapeHtml(p.pid) + '</td>\n' +
      '<td>' + escapeHtml(p.name) + '</td>\n' +
      '<td>' + escapeHtml(p.user) + '</td>\n' +
      '<td>' + cpu.toFixed(1) + '%</td>\n' +
      '<td>' + mem.toFixed(1) + '%</td>\n' +
      '<td>' + escapeHtml(p.status) + '</td>\n' +
      '<td>' + escapeHtml(p.start) + '</td>\n' +
      '<td class="text-nowrap" style="display:flex;gap:4px">\n' +
      '  <button class="pr-btn pr-btn-sm pr-btn-ghost" onclick="window.__prDetail(' + escapeHtml(p.pid) + ')">🔍</button>\n' +
      '  <button class="pr-btn pr-btn-sm pr-btn-danger" onclick="window.__prKill(' + escapeHtml(p.pid) + ')">✕</button>\n' +
      '  <button class="pr-btn pr-btn-sm pr-btn-warning" onclick="window.__prForceKill(' + escapeHtml(p.pid) + ')">⚠</button>\n' +
      '</td>\n</tr>';
  }

  function renderTable(data) {
    processes = data;
    const tbody = qs($('pr-table'), 'tbody');
    if (!tbody) return;
    const q = ($('pr-search-input')?.value || '').toLowerCase().trim();
    const filtered = q ? processes.filter(p => (p.pid + '').includes(q) || (p.name || '').toLowerCase().includes(q) || (p.user || '').toLowerCase().includes(q)) : processes;
    if (!filtered.length) {
      tbody.innerHTML = '<tr><td colspan="8" style="text-align:center;color:var(--pr-text-muted);padding:2rem 0">' + (q ? 'Không tìm thấy tiến trình' : 'Không có tiến trình nào') + '</td></tr>';
      return;
    }
    tbody.innerHTML = filtered.map(renderRow).join('');
  }

  function loadProcesses() {
    fetch('/processes/api/list')
      .then(r => r.json())
      .then(d => {
        if (d.status === 'success') {
          renderTable(d.data || []);
        }
      })
      .catch(() => {});
  }

  function showDetail(pid) {
    fetch('/processes/api/detail/' + pid)
      .then(r => r.json())
      .then(d => {
        if (d.status !== 'success') { toast(d.message || 'Lỗi', 'error'); return; }
        const p = d.data || {};
        const modal = document.createElement('div');
        modal.className = 'pr-modal-overlay';
        modal.innerHTML = '<div class="pr-modal" style="max-width:560px">\n' +
          '  <div class="pr-modal-header">\n' +
          '    <div class="pr-modal-title">Chi tiết tiến trình #' + escapeHtml(pid) + '</div>\n' +
          '    <button class="pr-modal-close" onclick="this.closest(\'.pr-modal-overlay\').remove()">✕</button>\n' +
          '  </div>\n' +
          '  <div class="pr-modal-body">\n' +
          '    <dl class="pr-detail-grid">\n' +
          Object.entries(p).map(([k, v]) => '<dt>' + escapeHtml(k) + '</dt><dd>' + escapeHtml(String(v ?? '')) + '</dd>').join('\n') +
          '    </dl>\n' +
          '  </div>\n' +
          '  <div class="pr-modal-footer">\n' +
          '    <button class="pr-btn" onclick="this.closest(\'.pr-modal-overlay\').remove()">Đóng</button>\n' +
          '  </div>\n' +
          '</div>';
        document.body.appendChild(modal);
        modal.addEventListener('click', e => { if (e.target === modal) modal.remove(); });
      })
      .catch(() => toast('Lỗi khi tải chi tiết', 'error'));
  }

  function confirmKill(pid, force) {
    const label = force ? 'Force Kill' : 'Kill';
    const modal = document.createElement('div');
    modal.className = 'pr-modal-overlay';
    modal.innerHTML = '<div class="pr-modal" style="max-width:420px">\n' +
      '  <div class="pr-modal-header">\n' +
      '    <div class="pr-modal-title">Xác nhận ' + label + '</div>\n' +
      '    <button class="pr-modal-close" onclick="this.closest(\'.pr-modal-overlay\').remove()">✕</button>\n' +
      '  </div>\n' +
      '  <div class="pr-modal-body" style="font-size:.9rem;color:var(--pr-text-muted)">\n' +
      '    Bạn có chắc chắn muốn ' + (force ? 'force kill' : 'kill') + ' tiến trình <strong style="color:var(--pr-text)">PID ' + escapeHtml(pid) + '</strong>?\n' +
      '  </div>\n' +
      '  <div class="pr-modal-footer">\n' +
      '    <button class="pr-btn" onclick="this.closest(\'.pr-modal-overlay\').remove()">Hủy</button>\n' +
      '    <button class="pr-btn ' + (force ? 'pr-btn-warning' : 'pr-btn-danger') + '" id="pr-confirm-btn">Xác nhận</button>\n' +
      '  </div>\n' +
      '</div>';
    document.body.appendChild(modal);
    modal.addEventListener('click', e => { if (e.target === modal) modal.remove(); });
    $('pr-confirm-btn').addEventListener('click', () => {
      const endpoint = force ? '/processes/api/force-kill/' + pid : '/processes/api/kill/' + pid;
      fetch(endpoint, { method: 'POST' })
        .then(r => r.json())
        .then(d => {
          modal.remove();
          if (d.status === 'success') { toast(d.message || 'OK', 'success'); loadProcesses(); }
          else { toast(d.message || 'Lỗi', 'error'); }
        })
        .catch(() => { modal.remove(); toast('Lỗi kết nối', 'error'); });
    });
  }

  function restartService() {
    const modal = document.createElement('div');
    modal.className = 'pr-modal-overlay';
    modal.innerHTML = '<div class="pr-modal" style="max-width:420px">\n' +
      '  <div class="pr-modal-header">\n' +
      '    <div class="pr-modal-title">Khởi động lại dịch vụ</div>\n' +
      '    <button class="pr-modal-close" onclick="this.closest(\'.pr-modal-overlay\').remove()">✕</button>\n' +
      '  </div>\n' +
      '  <div class="pr-modal-body">\n' +
      '    <label style="display:block;font-size:.82rem;color:var(--pr-text-muted);margin-bottom:4px">Tên dịch vụ</label>\n' +
      '    <input type="text" id="pr-svc-input" placeholder="nginx, mysql, ssh..." style="width:100%;background:var(--pr-surface-2);border:1px solid var(--pr-border);color:var(--pr-text);padding:8px 10px;border-radius:6px;font-size:.88rem;outline:none">\n' +
      '  </div>\n' +
      '  <div class="pr-modal-footer">\n' +
      '    <button class="pr-btn" onclick="this.closest(\'.pr-modal-overlay\').remove()">Hủy</button>\n' +
      '    <button class="pr-btn pr-btn-primary" id="pr-svc-restart-btn">Khởi động lại</button>\n' +
      '  </div>\n' +
      '</div>';
    document.body.appendChild(modal);
    modal.addEventListener('click', e => { if (e.target === modal) modal.remove(); });
    $('pr-svc-restart-btn').addEventListener('click', () => {
      const name = $('pr-svc-input').value.trim();
      if (!name) { toast('Nhập tên dịch vụ', 'error'); return; }
      fetch('/processes/api/restart-service', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ service_name: name }),
      })
        .then(r => r.json())
        .then(d => {
          modal.remove();
          if (d.status === 'success') { toast(d.message || 'OK', 'success'); }
          else { toast(d.message || 'Lỗi', 'error'); }
        })
        .catch(() => { modal.remove(); toast('Lỗi kết nối', 'error'); });
    });
  }

  window.__prDetail = showDetail;
  window.__prKill = function(pid) { confirmKill(pid, false); };
  window.__prForceKill = function(pid) { confirmKill(pid, true); };
  window.__prRestartSvc = restartService;

  document.addEventListener('DOMContentLoaded', () => {
    const input = $('pr-search-input');
    if (input) {
      input.addEventListener('input', () => { renderTable(processes); });
    }
    loadProcesses();
    if (timerId) clearInterval(timerId);
    timerId = setInterval(loadProcesses, REFRESH_MS);
    document.addEventListener('visibilitychange', () => {
      if (document.hidden && timerId) { clearInterval(timerId); timerId = null; }
      else if (!document.hidden && !timerId) { loadProcesses(); timerId = setInterval(loadProcesses, REFRESH_MS); }
    });
  });
})();
