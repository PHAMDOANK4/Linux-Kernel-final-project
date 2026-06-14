# Requirement Analysis: Linux Administration Dashboard — Desktop App

> Phân tích yêu cầu dựa trên project `Kernel-Linux` (Flask Web) để xây dựng ứng dụng Desktop tương đương.

---

## 1. Tổng Quan

Project gốc là Web Dashboard quản trị Linux bằng Flask + Shell Script.  
Mục tiêu: chuyển thành Desktop App giữ nguyên business logic và shell scripts.

| Mục | Mô tả |
|---|---|
| Tên | Linux Administration Desktop |
| Nền tảng | Linux (các script phụ thuộc Linux commands) |
| Loại ứng dụng | Desktop GUI (native) |
| Ngôn ngữ | Python 3.12+ |
| GUI Framework | **PyQt6 / PySide6** (recommended) |

---

## 2. Kiến Trúc Hệ Thống (3 Lớp)

### Lớp 1 — Presentation (GUI)
- Cửa sổ Login, Dashboard, các tab module
- Widgets native: table, text edit, button, form, tree view
- Xác nhận trước thao tác nguy hiểm (delete, remove)

### Lớp 2 — Business Logic (Python)
- Xác thực + phân quyền (Auth + RBAC)
- Gọi shell script qua `subprocess.run()`
- Ghi log file + database
- Parse output của script thành dữ liệu hiển thị

### Lớp 3 — System Layer (Shell Script)
- 26 file `.sh` trong thư mục `scripts/`
- Giữ nguyên, không thay đổi

```
┌──────────────────────────────────┐
│  Presentation (PyQt6 Widgets)    │
│  - Login Window, Tab Widget      │
│  - QTableView, QTextEdit, Forms  │
├──────────────────────────────────┤
│  Business Logic (Python)         │
│  - auth.py, rbac.py, executor.py │
│  - database.py, parsers.py       │
│  - logging.py                    │
├──────────────────────────────────┤
│  System Layer (Shell Scripts)    │
│  - scripts/*.sh (26 files)       │
└──────────────────────────────────┘
```

---

## 3. Modules & Chức Năng

| Module | Chức năng | Quyền |
|---|---|---|
| **Authentication** | Đăng nhập/Đăng xuất, session in-memory | Tất cả |
| **File Management** | List file/dir, Tạo file/folder, Rename, Copy, Move, Delete, Search, Chmod, Chown | Tất cả |
| **Task Scheduler** | List cron, Create/Update/Delete cron, Chạy job ngay lập tức | Admin |
| **System Time** | Xem giờ, Set giờ, Set timezone, Bật/Tắt NTP, Đồng bộ NTP | Xem: tất cả; Sửa: admin |
| **Package Management** | List gói, Search, Install, Remove, Upgrade | Xem/Search: tất cả; CRUD: admin |
| **Audit Logs** | Xem log hành động (200 bản ghi gần nhất) | Admin |

---

## 4. Công Nghệ Đề Xuất

| Thành phần | Lựa chọn | Ghi chú |
|---|---|---|
| GUI | **PyQt6 / PySide6** | Native, mạnh, tài liệu tốt |
| Database | SQLAlchemy + SQLite | Giữ nguyên từ project gốc |
| Password | `werkzeug.security` | generate_password_hash / check_password_hash |
| Subprocess | `subprocess.run()` | Timeout 120s, capture output |
| Async UI | `QThread` / `QProcess` | Chạy script không block GUI |
| Build | PyInstaller | Đóng gói thành 1 file .desktop |

---

## 5. Database Schema (Giữ Nguyên)

### Bảng `users`
```sql
CREATE TABLE users (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    username VARCHAR(64) UNIQUE NOT NULL,
    password_hash VARCHAR(255) NOT NULL,
    role VARCHAR(16) NOT NULL DEFAULT 'user',
    created_at DATETIME NOT NULL
);
```

### Bảng `action_logs`
```sql
CREATE TABLE action_logs (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    username VARCHAR(64) NOT NULL,
    action VARCHAR(255) NOT NULL,
    result VARCHAR(32) NOT NULL,
    detail TEXT NOT NULL,
    created_at DATETIME NOT NULL
);
```

### Tài khoản mặc định
| Username | Password | Role |
|---|---|---|
| admin | admin123 | admin |
| user | user123 | user |

Cấu hình qua file `.env` hoặc Settings dialog.

---

## 6. Phân Quyền (RBAC Matrix)

| Hành động | User | Admin |
|---|---|---|
| Xem file | ✓ | ✓ |
| Tạo/Sửa/Xóa file | ✓ | ✓ |
| Chmod/Chown | ✓ | ✓ |
| Xem giờ hệ thống | ✓ | ✓ |
| Set giờ/múi giờ | ✗ | ✓ |
| Bật/Tắt/Dong bo NTP | ✗ | ✓ |
| Xem danh sách gói | ✓ | ✓ |
| Install/Remove/Upgrade gói | ✗ | ✓ |
| Quản lý cron | ✗ | ✓ |
| Xem audit logs | ✗ | ✓ |

---

## 7. Yêu Cầu Giao Diện Theo Module

### 7.1 Login Window
- Ô username + password
- Nút Login → kiểm tra → mở Main Window
- Label báo lỗi nếu sai thông tin

### 7.2 Dashboard (Main Window)
- Thanh navigation (tab bar hoặc sidebar)
- Hiển thị username + role badge
- Nút Logout
- Quick-access buttons tới các module

### 7.3 File Management
- **Breadcrumb** đường dẫn + ô nhập path + nút Go
- **QTableView** list file: cột Type (DIR/FILE), Name, Path
- Nút hành động: Create File, Create Folder, Rename, Copy, Move, Delete, Search, Chmod, Chown
- **Right-click context menu** trên mỗi dòng
- **QTextEdit** (read-only) hiển thị output command

### 7.4 Task Scheduler (Cron)
- **QTableView** danh sách cron jobs: line number, schedule, command
- Các trường schedule được parse thành minute/hour/day/month/weekday
- Form Add/Edit: nhập schedule + command
- Nút: Create, Update, Delete, Run Now
- Output panel

### 7.5 System Time
- Hiển thị thời gian hiện tại (real-time update)
- Nút Set Time (admin only) → dialog pick time
- Nút Set Timezone (admin only) → dropdown list timezone
- Switch/Checkbox Enable/Disable NTP
- Nút Sync NTP
- Output panel

### 7.6 Package Management
- **QTableView** danh sách gói đã cài
- Ô Search + nút Search
- Nút Install, Remove, Upgrade (admin only, ẩn hoặc disable với user)
- Output panel

### 7.7 Audit Logs
- **QTableView** logs: timestamp, user, action, result, detail
- Read-only, 200 bản ghi gần nhất
- Admin only

---

## 8. Shell Scripts (Giữ Nguyên — 26 Files)

### Module File (10 scripts)
| Script | Chức năng |
|---|---|
| `list_files.sh <path>` | Liệt kê file/dir, format: `TYPE\tname\tfullpath` |
| `create_file.sh <dir> <name>` | Tạo file |
| `create_folder.sh <dir> <name>` | Tạo thư mục |
| `rename_file.sh <source> <new_name>` | Đổi tên |
| `copy_file.sh <source> <dest>` | Copy |
| `move_file.sh <source> <dest>` | Di chuyển |
| `delete_file.sh <target>` | Xóa |
| `search_file.sh <base_path> <keyword>` | Tìm kiếm |
| `chmod_file.sh <target> <mode>` | Đổi permission |
| `chown_file.sh <target> <owner> <group>` | Đổi owner |

### Module Cron (5 scripts)
| Script | Chức năng |
|---|---|
| `list_cron.sh` | Liệt kê crontab |
| `create_cron.sh <schedule> <command>` | Thêm cron job |
| `update_cron.sh <match_text> <schedule> <command>` | Sửa cron job |
| `delete_cron.sh <match_text>` | Xóa cron job |
| `run_job.sh <command>` | Chạy ngay lập tức |

### Module Time (7 scripts)
| Script | Chức năng |
|---|---|
| `show_time.sh` | Xem ngày giờ |
| `set_time.sh <datetime>` | Set ngày giờ |
| `set_timezone.sh <timezone>` | Set timezone |
| `enable_ntp.sh` | Bật NTP |
| `disable_ntp.sh` | Tắt NTP |
| `sync_time.sh` | Đồng bộ NTP |

### Module Package (5 scripts)
| Script | Chức năng |
|---|---|
| `list_packages.sh` | Liệt kê gói đã cài |
| `search_package.sh <keyword>` | Tìm kiếm gói |
| `install_package.sh <name>` | Cài gói |
| `remove_package.sh <name>` | Gỡ gói |
| `upgrade_package.sh [name]` | Nâng cấp (không tham số → upgrade all) |

---

## 9. Logging System (Giữ Nguyên)

### File log — `logs/system.log`
Format:
```
YYYY-MM-DD HH:MM:SS | user=<username> | action=<module:action> | result=SUCCESS|FAILED | detail=<output>
```

### Database log — Bảng `action_logs`
- Mỗi hành động → 1 bản ghi
- Lưu: username, action, result, detail (tối đa 2000 ký tự), created_at

### Khi nào ghi log?
- Mọi hành động có gọi shell script đều được ghi
- Cả thành công và thất bại

---

## 10. Xử Lý Lỗi

| Tình huống | Xử lý |
|---|---|
| Script không tồn tại | Return `(False, "Script not found: <name>")` |
| Script timeout (>=120s) | Return `(False, "Command timeout")` |
| Script exit code != 0 | Return `(False, <stderr>)` |
| Directory không tồn tại | Flash warning, fallback về `/home` |
| User không có quyền | Flash message + không thực thi |
| Exception không xác định | Catch-all, return `(False, str(exc))` |

---

## 11. Yêu Cầu Phi Chức Năng

| Yêu cầu | Chi tiết |
|---|---|
| Hệ điều hành | Linux (scripts dùng Linux-specific commands) |
| Python | 3.12+ |
| Thư viện chính | PyQt6, SQLAlchemy, Werkzeug |
| Đóng gói | PyInstaller → single executable |
| Responsiveness | Chạy script trong QThread để không block GUI |
| Bảo mật | Hash password, RBAC, audit log, không cho user truy cập shell trực tiếp |
| Privileges | Cần chạy root/sudo cho một số thao tác (time, apt, cron) |

---

## 12. Cấu Trúc Thư Mục Đề Xuất

```
linux-admin-desktop/
├── main.py                          # Entry point
├── requirements.txt                 # Python dependencies
├── .env.example                     # Mẫu cấu hình
├── README.md
│
├── app/
│   ├── __init__.py
│   ├── auth.py                      # Xác thực + session
│   ├── database.py                  # Models + init DB
│   ├── executor.py                  # subprocess wrapper
│   ├── logging.py                   # File + DB logger
│   ├── parsers.py                   # Parse file listing, cron schedule
│   └── rbac.py                      # Decorator kiểm tra quyền
│
├── ui/
│   ├── __init__.py
│   ├── login_window.py              # Cửa sổ đăng nhập
│   ├── main_window.py               # Cửa sổ chính + tab navigation
│   ├── file_manager_widget.py       # Tab File Management
│   ├── task_scheduler_widget.py     # Tab Task Scheduler
│   ├── system_time_widget.py        # Tab System Time
│   ├── package_manager_widget.py    # Tab Package Management
│   └── logs_viewer_widget.py        # Tab Audit Logs
│
├── scripts/                         # 26 shell scripts (giữ nguyên)
│   ├── list_files.sh
│   ├── create_file.sh
│   ├── ...
│   └── upgrade_package.sh
│
├── logs/                            # system.log (auto created)
└── instance/                        # dashboard.db (auto created)
```

---

## 13. So Sánh Web vs Desktop

| Tiêu chí | Web (Flask) | Desktop (PyQt6) |
|---|---|---|
| UI | HTML + Bootstrap 5 | Native Qt Widgets |
| Điều hướng | URL routes | Tab / Sidebar |
| Session | Flask session (cookie) | In-memory Python object |
| File listing | HTML table | QTableView + Model |
| Output | `<pre>` block | QTextEdit (monospace) |
| Async | Synchronous (block request) | QThread / QProcess |
| Confirm dialog | JavaScript `confirm()` | QMessageBox |
| Đóng gói | Docker / `python app.py` | PyInstaller → `.desktop` |
| Cập nhật UI | Render lại template | Signal/Slot cập nhật widget |
