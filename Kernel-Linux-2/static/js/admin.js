const AD = {
  _users: [],
  _roles: [],
  _logs: [],

  init() {
    this.loadUsers();
    this.loadRoles();
    this.loadAuditLogs();
    this.initEvents();
  },

  /* ── Events ───────────────────────────────── */
  initEvents() {
    const search = document.getElementById('ad-user-search');
    if (search) search.addEventListener('input', () => this.renderUsers());

    const roleFilter = document.getElementById('ad-filter-role');
    if (roleFilter) roleFilter.addEventListener('change', () => this.renderUsers());

    const statusFilter = document.getElementById('ad-filter-status');
    if (statusFilter) statusFilter.addEventListener('change', () => this.renderUsers());

    const logSearch = document.getElementById('ad-log-search');
    if (logSearch) logSearch.addEventListener('input', () => this.renderLogs());

    document.getElementById('ad-btn-create')?.addEventListener('click', () => this.openCreateModal());
    document.getElementById('ad-create-form')?.addEventListener('submit', (e) => { e.preventDefault(); this.createUser(); });
    document.getElementById('ad-edit-form')?.addEventListener('submit', (e) => { e.preventDefault(); this.editUser(); });
    document.getElementById('ad-pw-form')?.addEventListener('submit', (e) => { e.preventDefault(); this.resetPassword(); });
    document.getElementById('ad-confirm-delete')?.addEventListener('click', () => this.deleteUser());
    document.querySelectorAll('.ad-modal-close, .ad-modal-overlay').forEach(el => {
      el.addEventListener('click', (e) => {
        if (e.target === el || e.target.closest('.ad-modal-close')) this.closeAllModals();
      });
    });
    document.getElementById('ad-refresh-users')?.addEventListener('click', () => this.loadUsers());
  },

  /* ── Data Loading ─────────────────────────── */
  async loadUsers() {
    const tbody = document.getElementById('ad-user-body');
    if (tbody) tbody.innerHTML = '<tr><td colspan="6" class="text-center py-3"><span class="ad-spinner"></span> Đang tải…</td></tr>';
    try {
      const res = await fetch('/admin/api/users');
      const data = await res.json();
      if (data.error) throw new Error(data.error);
      this._users = data.users || [];
      this.renderUsers();
    } catch (_) {
      if (tbody) tbody.innerHTML = '<tr><td colspan="6" class="text-muted small text-center py-3">Lỗi tải dữ liệu</td></tr>';
    }
  },

  async loadRoles() {
    try {
      const res = await fetch('/admin/api/roles');
      const data = await res.json();
      this._roles = data.roles || [];
      this.populateRoleSelects();
    } catch (_) {}
  },

  populateRoleSelects() {
    const selects = document.querySelectorAll('.ad-role-select');
    selects.forEach(sel => {
      const current = sel.value;
      sel.innerHTML = this._roles.map(r => `<option value="${this._e(r.name)}">${this._e(r.name)}</option>`).join('');
      if (current) sel.value = current;
    });
  },

  async loadAuditLogs() {
    const tbody = document.getElementById('ad-log-body');
    try {
      const res = await fetch('/admin/api/audit-logs');
      const data = await res.json();
      this._logs = data.logs || [];
      this.renderLogs();
    } catch (_) {
      if (tbody) tbody.innerHTML = '<tr><td colspan="5" class="text-muted small text-center py-3">Lỗi tải nhật ký</td></tr>';
    }
  },

  /* ── Render Users ─────────────────────────── */
  renderUsers() {
    const tbody = document.getElementById('ad-user-body');
    if (!tbody) return;
    const q = (document.getElementById('ad-user-search')?.value || '').toLowerCase();
    const roleF = (document.getElementById('ad-filter-role')?.value || '').toLowerCase();
    const statusF = (document.getElementById('ad-filter-status')?.value || '');

    const filtered = this._users.filter(u => {
      if (q && !u.username.toLowerCase().includes(q) && !(u.full_name || '').toLowerCase().includes(q)) return false;
      if (roleF && u.role.toLowerCase() !== roleF) return false;
      if (statusF === 'active' && !u.is_active) return false;
      if (statusF === 'inactive' && u.is_active) return false;
      return true;
    });

    this.updateStats(filtered.length);

    tbody.innerHTML = filtered.map(u => {
      const statusClass = u.is_active ? 'ad-badge-active' : 'ad-badge-inactive';
      const statusText = u.is_active ? 'Hoạt động' : 'Vô hiệu';
      return `<tr>
        <td><strong>${this._e(u.username)}</strong></td>
        <td>${this._e(u.full_name || '—')}</td>
        <td><span class="ad-badge ad-badge-info">${this._e(u.role)}</span></td>
        <td>${this._e(u.created_at)}</td>
        <td><span class="ad-badge ${statusClass}">${statusText}</span></td>
        <td>
          <div class="d-flex gap-1">
            <button class="ad-btn ad-btn-xs" onclick="AD.openEditModal(${u.id})" title="Sửa"><i class="fa fa-pen"></i></button>
            <button class="ad-btn ad-btn-xs" onclick="AD.openPwModal(${u.id})" title="Đặt lại mật khẩu"><i class="fa fa-key"></i></button>
            <button class="ad-btn ad-btn-xs" onclick="AD.toggleUser(${u.id})" title="${u.is_active ? 'Vô hiệu hóa' : 'Kích hoạt'}"><i class="fa fa-${u.is_active ? 'pause' : 'play'}"></i></button>
            <button class="ad-btn ad-btn-xs" onclick="AD.openDeleteModal(${u.id}, '${this._e(u.username)}')" title="Xóa"><i class="fa fa-trash"></i></button>
          </div>
        </td>
      </tr>`;
    }).join('') || '<tr><td colspan="6" class="text-muted small text-center py-3">Không có kết quả</td></tr>';
  },

  updateStats(count) {
    const total = document.getElementById('ad-stat-total');
    const active = document.getElementById('ad-stat-active');
    const inactive = document.getElementById('ad-stat-inactive');
    if (total) total.textContent = this._users.length;
    const act = this._users.filter(u => u.is_active).length;
    if (active) active.textContent = act;
    if (inactive) inactive.textContent = this._users.length - act;
  },

  /* ── Render Logs ──────────────────────────── */
  renderLogs() {
    const tbody = document.getElementById('ad-log-body');
    if (!tbody) return;
    const q = (document.getElementById('ad-log-search')?.value || '').toLowerCase();
    const filtered = this._logs.filter(l => {
      const all = (l.username + ' ' + l.action + ' ' + l.module + ' ' + l.result + ' ' + l.details).toLowerCase();
      return !q || all.includes(q);
    });
    tbody.innerHTML = filtered.map(l => {
      const badgeClass = l.result === 'SUCCESS' ? 'ad-badge-ok' : 'ad-badge-fail';
      return `<tr>
        <td>${this._e(l.username)}</td>
        <td>${this._e(l.action)}</td>
        <td>${this._e(l.module)}</td>
        <td><span class="ad-badge ${badgeClass}">${this._e(l.result)}</span></td>
        <td class="small">${this._e(l.timestamp)}</td>
      </tr>`;
    }).join('') || '<tr><td colspan="5" class="text-muted small text-center py-3">Không có nhật ký</td></tr>';
  },

  /* ── Create User ──────────────────────────── */
  openCreateModal() {
    document.getElementById('ad-create-form').reset();
    document.getElementById('modal-create').classList.add('open');
  },

  async createUser() {
    const form = document.getElementById('ad-create-form');
    const data = Object.fromEntries(new FormData(form));
    const btn = form.querySelector('button[type="submit"]');
    btn.disabled = true; btn.innerHTML = '<span class="ad-spinner"></span> Đang tạo…';
    try {
      const res = await fetch('/admin/api/users', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(data),
      });
      const result = await res.json();
      if (result.error) { this.toast(result.error, 'danger'); return; }
      this.toast(result.message, 'success');
      this.closeAllModals();
      await this.loadUsers();
    } catch (_) { this.toast('Lỗi kết nối', 'danger'); }
    finally { btn.disabled = false; btn.innerHTML = '<i class="fa fa-plus me-1"></i>Tạo'; }
  },

  /* ── Toggle User ──────────────────────────── */
  async toggleUser(userId) {
    try {
      const res = await fetch(`/admin/api/users/${userId}/toggle`, { method: 'POST' });
      const result = await res.json();
      if (result.error) { this.toast(result.error, 'danger'); return; }
      this.toast(result.message, 'success');
      await this.loadUsers();
    } catch (_) { this.toast('Lỗi kết nối', 'danger'); }
  },

  /* ── Edit User ────────────────────────────── */
  openEditModal(userId) {
    const user = this._users.find(u => u.id === userId);
    if (!user) return;
    document.getElementById('edit-user-id').value = user.id;
    document.getElementById('edit-full-name').value = user.full_name || '';
    const roleSel = document.getElementById('edit-role');
    roleSel.innerHTML = this._roles.map(r =>
      `<option value="${this._e(r.name)}" ${r.name === user.role ? 'selected' : ''}>${this._e(r.name)}</option>`
    ).join('');
    document.getElementById('modal-edit').classList.add('open');
  },

  async editUser() {
    const userId = document.getElementById('edit-user-id').value;
    const data = {
      full_name: document.getElementById('edit-full-name').value,
      role: document.getElementById('edit-role').value,
    };
    const btn = document.querySelector('#modal-edit button[type="submit"]');
    btn.disabled = true; btn.innerHTML = '<span class="ad-spinner"></span>';
    try {
      const res = await fetch(`/admin/api/users/${userId}/edit`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(data),
      });
      const result = await res.json();
      if (result.error) { this.toast(result.error, 'danger'); return; }
      this.toast(result.message, 'success');
      this.closeAllModals();
      await this.loadUsers();
    } catch (_) { this.toast('Lỗi kết nối', 'danger'); }
    finally { btn.disabled = false; btn.innerHTML = 'Lưu'; }
  },

  /* ── Reset Password ───────────────────────── */
  openPwModal(userId) {
    document.getElementById('pw-user-id').value = userId;
    document.getElementById('pw-password').value = '';
    document.getElementById('modal-pw').classList.add('open');
  },

  async resetPassword() {
    const userId = document.getElementById('pw-user-id').value;
    const password = document.getElementById('pw-password').value;
    if (!password || password.length < 3) { this.toast('Mật khẩu phải có ít nhất 3 ký tự', 'danger'); return; }
    const btn = document.querySelector('#modal-pw button[type="submit"]');
    btn.disabled = true; btn.innerHTML = '<span class="ad-spinner"></span>';
    try {
      const res = await fetch(`/admin/api/users/${userId}/reset-pw`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ password }),
      });
      const result = await res.json();
      if (result.error) { this.toast(result.error, 'danger'); return; }
      this.toast(result.message, 'success');
      this.closeAllModals();
    } catch (_) { this.toast('Lỗi kết nối', 'danger'); }
    finally { btn.disabled = false; btn.innerHTML = 'Lưu'; }
  },

  /* ── Delete User ──────────────────────────── */
  openDeleteModal(userId, username) {
    document.getElementById('delete-user-id').value = userId;
    document.getElementById('delete-user-name').textContent = username;
    document.getElementById('modal-delete').classList.add('open');
  },

  async deleteUser() {
    const userId = document.getElementById('delete-user-id').value;
    const btn = document.getElementById('ad-confirm-delete');
    btn.disabled = true; btn.innerHTML = '<span class="ad-spinner"></span> Đang xóa…';
    try {
      const res = await fetch(`/admin/api/users/${userId}/delete`, { method: 'POST' });
      const result = await res.json();
      if (result.error) { this.toast(result.error, 'danger'); return; }
      this.toast(result.message, 'success');
      this.closeAllModals();
      await this.loadUsers();
    } catch (_) { this.toast('Lỗi kết nối', 'danger'); }
    finally { btn.disabled = false; btn.innerHTML = 'Xóa'; }
  },

  /* ── UI Helpers ───────────────────────────── */
  closeAllModals() {
    document.querySelectorAll('.ad-modal-overlay').forEach(m => m.classList.remove('open'));
  },

  toast(message, type = 'info') {
    const container = document.getElementById('ad-toast-container');
    if (!container) return;
    const toast = document.createElement('div');
    toast.className = `ad-toast ad-toast-${type}`;
    const icon = type === 'success' ? 'check-circle' : type === 'danger' ? 'exclamation-circle' : 'info-circle';
    toast.innerHTML = `<i class="fa fa-${icon} text-${type === 'danger' ? 'danger' : type}"></i><span>${this._e(message)}</span>`;
    container.appendChild(toast);
    setTimeout(() => { toast.style.opacity = '0'; toast.style.transition = 'opacity .3s'; setTimeout(() => toast.remove(), 300); }, 3000);
  },

  _e(str) {
    if (str === null || str === undefined) return '';
    return String(str).replace(/&/g, '&amp;').replace(/</g, '&lt;').replace(/>/g, '&gt;').replace(/"/g, '&quot;');
  },
};

document.addEventListener('DOMContentLoaded', () => AD.init());
