# Requirement Analysis: Ubuntu Monitoring & Network Administration — Desktop App

> Phân tích yêu cầu dựa trên project `Kernel-Linux-2` (Flask Web) để xây dựng ứng dụng Desktop tương đương.

---

## 1. Tổng Quan

Project gốc là **Ubuntu Monitoring & Network Administration** — hệ thống Web giám sát và quản trị Ubuntu 22.04 bằng Flask + Shell Script.

| Mục | Mô tả |
|---|---|
| Tên | Ubuntu Monitor Desktop |
| Nền tảng | Linux (Ubuntu 22.04) |
| Loại ứng dụng | Desktop GUI (native) |
| Ngôn ngữ | Python 3.12+ |
| GUI Framework | **PyQt6 / PySide6** (recommended) |

Điểm khác biệt chính so với project `Kernel-Linux`:
- **7 modules** thay vì 5 (thêm Process Management, Sockets, Admin User Management)
- **Phân quyền 2 cấp**: Admin + Operator (Operator chỉ xem, Admin mới được thao tác)
- **37 shell scripts** thay vì 26 (chuyên sâu về network, socket, process)
- **Input validation layer** chống command injection
- **Audit log + System event** tracking

---

## 2. Kiến Trúc Hệ Thống (3 Lớp)

```
┌──────────────────────────────────────┐
│  Presentation (PyQt6 Widgets)        │
│  - Login Window, Tab Navigation      │
│  - QTableView, QTextEdit, Forms      │
│  - Chart.js style → Qt Charts        │
├──────────────────────────────────────┤
│  Business Logic (Python Service)     │
│  - Blueprints → Tab Widgets          │
│  - Service Layer (SystemService)     │
│  - ScriptRunner + Security validation│
│  - AuditService (DB + File logger)   │
│  - Helpers (parse_table, parse_kv)   │
├──────────────────────────────────────┤
│  System Layer (Shell Scripts)        │
│  - 37 file `.sh` trong scripts/      │
│  - Network, Process, Socket, File    │
└──────────────────────────────────────┘
```

---

## 3. Modules & Chức Năng

| Module | Chức năng | Admin | Operator |
|---|---|---|---|
| **Authentication** | Login/Logout, session | ✓ | ✓ |
| **Dashboard** | System overview, CPU/Memory/Disk, top processes, network interfaces, recent activity, auto-refresh 5s | ✓ | ✓ |
| **Process Management** | List all processes, Search process, View detail, Kill process, Force kill, Restart service | ✓ | ✓ (view only) |
| **File System** | Open files, Locked files, Watch file (inotify), Directory size, Large files (>100M), File permissions | ✓ | ✓ |
| **Sockets** | List all sockets, TCP sockets, UDP sockets, Listening ports, Socket by process, Connection stats, Socket overview, Close connection | ✓ | ✓ (view only) |
| **Network** | Network overview, Interfaces, Routes, DNS, Ping test, Traceroute, Port check, Port scan, Connection list, Bandwidth monitor, Restart network, Toggle interface, Change IP | ✓ | ✓ (view only) |
| **Admin (User Mgmt)** | List users, Create user, Edit user, Toggle active, Reset password, Delete user, View audit logs | ✓ | ✗ |

---

## 4. Công Nghệ Đề Xuất

| Thành phần | Lựa chọn | Ghi chú |
|---|---|---|
| GUI | **PyQt6 / PySide6** | Native, mạnh, tài liệu tốt |
| Database | SQLAlchemy + SQLite | Giữ nguyên schema |
| Password | `werkzeug.security` | generate_password_hash / check_password_hash |
| Subprocess | `subprocess.run()` qua `ScriptRunner` | Timeout 30s, validate script name |
| Async UI | `QThread` / `QProcess` | Chạy script không block GUI |
| Input Validation | Security layer (validate_pid, validate_port, validate_path, validate_cidr, ...) | Chống command injection |
| Charts | **PyQtGraph** hoặc **Matplotlib** (backport) | Dashboard metrics |
| Build | PyInstaller | Đóng gói thành 1 executable |

---

## 5. Database Schema

### Bảng `roles`
```sql
CREATE TABLE roles (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name VARCHAR(50) UNIQUE NOT NULL,
    description VARCHAR(255) DEFAULT '',
    created_at DATETIME NOT NULL
);
```

### Bảng `users`
```sql
CREATE TABLE users (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    username VARCHAR(80) UNIQUE NOT NULL,
    password_hash VARCHAR(255) NOT NULL,
    full_name VARCHAR(120) DEFAULT '',
    is_active BOOLEAN DEFAULT 1 NOT NULL,
    role_id INTEGER NOT NULL REFERENCES roles(id),
    created_at DATETIME NOT NULL,
    updated_at DATETIME NOT NULL
);
```

### Bảng `audit_logs`
```sql
CREATE TABLE audit_logs (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    username VARCHAR(80) NOT NULL,
    action VARCHAR(120) NOT NULL,
    module VARCHAR(80) NOT NULL,
    timestamp DATETIME NOT NULL,
    result VARCHAR(30) NOT NULL,
    details TEXT DEFAULT ''
);
```

### Bảng `system_events`
```sql
CREATE TABLE system_events (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    event_type VARCHAR(80) NOT NULL,
    target VARCHAR(255) DEFAULT '',
    module VARCHAR(80) NOT NULL,
    message TEXT DEFAULT '',
    created_at DATETIME NOT NULL
);
```

### Tài khoản mặc định
| Username | Password | Role |
|---|---|---|
| admin | Admin@12345 | Admin |
| operator | Operator@12345 | Operator |

---

## 6. Phân Quyền (RBAC Matrix)

| Hành động | Operator | Admin |
|---|---|---|
| Xem Dashboard | ✓ | ✓ |
| Xem Process list, detail, search | ✓ | ✓ |
| Kill / Force kill process | ✗ | ✓ |
| Restart service | ✗ | ✓ |
| Xem Open files, Locked files | ✓ | ✓ |
| Watch file (inotify) | ✓ | ✓ |
| Xem Directory size, Large files, Permission | ✓ | ✓ |
| Xem Socket list (TCP/UDP/Listening) | ✓ | ✓ |
| Xem Connection stats, overview | ✓ | ✓ |
| Close connection | ✗ | ✓ |
| Xem Network overview, interfaces, routes, DNS | ✓ | ✓ |
| Ping, Traceroute, Port check/scan | ✓ | ✓ |
| Bandwidth monitor | ✓ | ✓ |
| Restart network, Toggle interface, Change IP | ✗ | ✓ |
| User management (CRUD users) | ✗ | ✓ |
| Xem audit logs | ✗ | ✓ |

---

## 7. Yêu Cầu Giao Diện Theo Module

### 7.1 Login Window
- Username + Password fields
- Nút Login → validate → mở Main Window
- Label báo lỗi nếu sai thông tin hoặc tài khoản bị vô hiệu hóa (`is_active = False`)

### 7.2 Dashboard (Main Window)
- **Sidebar navigation** với icon + text
- Modules: Dashboard, Processes, Files, Sockets, Network, Admin (chỉ admin)
- User info (username, role badge) + Logout button
- **Dashboard tab**: System overview cards (CPU, Memory, Disk, Uptime, Processes count)
- Top processes table (auto-refresh 5 giây)
- Network interfaces summary
- Recent audit activity list
- Có thể dùng **QTimer** cho auto-refresh

### 7.3 Process Management
- **QTableView** list processes: PID, Name, User, CPU%, MEM%, Status, Start Time
- **Search bar** + nút Search (lọc theo tên/PID)
- Double-click → **Process Detail dialog** (key-value display)
- Nút **Kill** (admin) → confirm dialog → gửi signal SIGTERM
- Nút **Force Kill** (admin) → confirm dialog → gửi signal SIGKILL
- Form **Restart Service** (admin): input service name + nút Restart
- Output panel hiển thị kết quả

### 7.4 File System
- **QTableView** kết quả theo từng tool:
  - Open Files: path → list file handles
  - Locked Files: path → list locked files
- **Watch File**: path input + duration (1-300s) → real-time output
- **Directory Size**: path → size summary
- **Large Files**: path + size filter (e.g. +100M) → table
- **File Permission**: path → permission info
- Output panel (monospace) hiển thị raw output

### 7.5 Sockets
- **Button group**: List All, TCP, UDP, Listening Ports
- **QTableView** kết quả socket (protocol, local addr, remote addr, state, PID)
- **Filter by Process**: PID input + Port input → filter
- **Connection Stats**: button → JSON/table display
- **Overview**: metrics (socket counts by state) + top processes
- **Close Connection** (admin): PID/Port input → confirm → close
- Output panel

### 7.6 Network
- **Overview tab**: Current IP, Gateway, Upload/Download speed, Active interfaces count, Status (online/offline)
- **Interface table**, **Route table**, **DNS table**
- **Tools section**:
  - Ping: target input + count → output
  - Traceroute: target input → output
  - Port Check: target + port → output
  - Port Scan: target + port range → output
  - Bandwidth: interface dropdown → output
- **Admin actions**:
  - Restart Network → confirm → execute
  - Toggle Interface: interface dropdown + up/down → confirm → execute
  - Change IP: interface + CIDR + gateway → confirm → execute
- Output panel

### 7.7 Admin — User Management
- **QTableView** users: ID, Username, Full Name, Role, Active, Created
- **Buttons**: Create User, Edit User, Toggle Active, Reset Password, Delete User
- **Create/Edit dialog**: username, password, full_name, role (dropdown: Admin/Operator)
- Confirm dialog cho delete và toggle active
- Không thể xóa chính mình

### 7.8 Admin — Audit Logs
- **QTableView** logs: Timestamp, User, Action, Module, Result, Details
- 50 bản ghi gần nhất
- Read-only, color-coded result (green SUCCESS / red FAIL)

---

## 8. Shell Scripts (37 Files)

### Module Process (7 scripts)
| Script | Chức năng |
|---|---|
| `process_list.sh` | List process (ps aux format) |
| `process_detail.sh <pid>` | Chi tiết process |
| `process_search.sh <query>` | Tìm kiếm process |
| `process_kill.sh <pid>` | Gửi SIGTERM |
| `process_force_kill.sh <pid>` | Gửi SIGKILL |
| `service_restart.sh <name>` | Restart systemd service |
| `top_processes.sh` | Top process theo CPU/MEM |

### Module File (6 scripts)
| Script | Chức năng |
|---|---|
| `open_files.sh [path]` | File đang mở (lsof) |
| `locked_files.sh [path]` | File bị lock |
| `watch_file.sh <path> <duration>` | Theo dõi file (inotify) |
| `directory_size.sh <path>` | Dung lượng thư mục |
| `large_files.sh <path> <size>` | File lớn hơn size |
| `file_permission.sh <path>` | Permission file |

### Module Socket (8 scripts)
| Script | Chức năng |
|---|---|
| `socket_list.sh` | Liệt kê socket |
| `tcp_socket.sh` | Socket TCP |
| `udp_socket.sh` | Socket UDP |
| `listening_ports.sh` | Cổng đang listen |
| `socket_process.sh [--pid] [--port]` | Socket theo process |
| `connection_stats.sh` | Thống kê kết nối |
| `close_connection.sh [--pid] [--port]` | Đóng kết nối |
| `socket_by_state.sh` | Socket theo trạng thái |
| `socket_top_processes.sh` | Top process dùng socket |

### Module Network (11 scripts)
| Script | Chức năng |
|---|---|
| `network_info.sh` | Thông tin interface |
| `route_info.sh` | Bảng định tuyến |
| `dns_info.sh` | DNS config |
| `ping_test.sh <target>` | Ping test |
| `traceroute_test.sh <target>` | Traceroute |
| `port_check.sh <target> <port>` | Kiểm tra port |
| `port_scan.sh <target> <range>` | Scan port |
| `connection_list.sh` | Danh sách kết nối |
| `bandwidth_monitor.sh [interface]` | Băng thông |
| `restart_network.sh` | Restart network |
| `interface_toggle.sh <iface> <up/down>` | Bật/tắt interface |
| `change_ip.sh <iface> <cidr> [gateway]` | Đổi IP |
| `network_speed.sh` | Tốc độ mạng |

### Module Common (1 script)
| Script | Chức năng |
|---|---|
| `common.sh` | Hàm dùng chung cho các script khác |
| `system_overview.sh` | Tổng quan hệ thống |

---

## 9. Input Validation Layer (Quan Trọng)

Desktop app cần copy toàn bộ validation từ `app/security.py`:

| Hàm | Mục đích |
|---|---|
| `validate_script_name(name)` | Chỉ cho phép `[A-Za-z0-9_\-]+.sh` |
| `validate_pid(value)` | Positive integer |
| `validate_port(value)` | 1-65535 |
| `validate_path(value)` | Không cho phép `..` hoặc null byte |
| `validate_service_name(name)` | `[A-Za-z0-9@._\-]+` |
| `validate_interface_name(name)` | `[A-Za-z0-9@._:\-]+` |
| `validate_hostname_or_ip(value)` | IP hoặc hostname hợp lệ |
| `validate_cidr(value)` | CIDR notation hợp lệ |

Các validation này phải được gọi **trước khi gọi shell script**, ở cả UI layer (disable nút) và Service layer.

---

## 10. Logging System

### File log — `logs/system.log`
```
<timestamp> <LEVEL> <username> <module> <action> <result> <details>
```

### Database log — Bảng `audit_logs`
- Mỗi hành động → 1 bản ghi
- Lưu: username, action, module, timestamp, result, details

### Database log — Bảng `system_events`
- Sử dụng cho các sự kiện đặc biệt (watch file, network restart)

### Khi nào ghi log?
- Login/logout
- View module (Dashboard, Processes, ...)
- Mọi hành động admin (kill, restart, change IP, ...)
- Cả thành công và thất bại

---

## 11. Xử Lý Lỗi

| Tình huống | Xử lý |
|---|---|
| Script không tồn tại | Raise `ScriptExecutionError` |
| Script timeout (>=30s) | Raise `ScriptExecutionError("Script timed out")` |
| Script exit code != 0 | Raise `ScriptExecutionError(stderr)` |
| Input không hợp lệ | Raise `ValueError` với message cụ thể |
| User không có quyền | Flash message + không thực thi |
| User bị vô hiệu hóa (`is_active=False`) | Từ chối đăng nhập |
| Path không hợp lệ | Validate trước, từ chối nếu có `..` |
| Exception không xác định | Catch-all, log + return error |

---

## 12. Yêu Cầu Phi Chức Năng

| Yêu cầu | Chi tiết |
|---|---|
| Hệ điều hành | Linux (Ubuntu 22.04, scripts dùng lsof, ss, ip, ping, traceroute, nc, inotify) |
| Python | 3.12+ |
| Thư viện chính | PyQt6, SQLAlchemy, Werkzeug |
| Đóng gói | PyInstaller → single executable |
| Responsiveness | QThread cho mọi shell script call |
| Bảo mật | Input validation + whitelist scripts + RBAC + audit log |
| Privileges | Cần sudo cho: `systemctl restart`, `ip link set`, `ip addr`, `kill`, `pkill` |
| Auto-refresh | Dashboard refresh mỗi 5 giây (QTimer) |
| Dependencies | `lsof`, `iproute2`, `iputils-ping`, `net-tools`, `procps`, `traceroute`, `netcat-openbsd`, `inotify-tools` |

---

## 13. Cấu Trúc Thư Mục Đề Xuất

```
ubuntu-monitor-desktop/
├── main.py                            # Entry point
├── requirements.txt
├── ubuntu-monitor-desktop.spec         # PyInstaller spec
├── .env.example
│
├── app/
│   ├── __init__.py
│   ├── auth.py                        # AuthManager
│   ├── database.py                    # Models + init_db
│   ├── executor.py                    # ScriptRunner (subprocess)
│   ├── logging.py                     # AuditService (file + DB)
│   ├── security.py                    # Input validation layer
│   ├── parsers.py                     # parse_table_output, parse_key_value_output
│   └── rbac.py                        # Role check
│
├── ui/
│   ├── __init__.py
│   ├── login_window.py                # Login dialog
│   ├── main_window.py                 # Main window + sidebar
│   ├── dashboard_widget.py            # Dashboard tab (metrics, charts)
│   ├── process_widget.py              # Process Management tab
│   ├── files_widget.py                # File System tab
│   ├── sockets_widget.py              # Sockets tab
│   ├── network_widget.py              # Network tab
│   ├── admin_users_widget.py          # User Management tab (admin)
│   └── admin_logs_widget.py           # Audit Logs tab (admin)
│
├── scripts/                           # 37 shell scripts (giữ nguyên)
│   ├── common.sh
│   ├── process_list.sh
│   ├── network_info.sh
│   ├── ...
│   └── change_ip.sh
│
├── logs/                              # system.log (auto created)
└── instance/                          # ubuntu_monitor.db (auto created)
```

---

## 14. So Sánh Web vs Desktop

| Tiêu chí | Web (Flask) | Desktop (PyQt6) |
|---|---|---|
| UI | Bootstrap 5 + Chart.js | Native Qt Widgets + PyQtGraph |
| Điều hướng | URL routes (7 blueprints) | Sidebar + QStackedWidget |
| Session | Flask session (cookie) | In-memory AuthManager |
| Dashboard metrics | REST API → Chart.js | QTimer + direct update widget |
| Subprocess | Synchronous (block request) | QThread (non-blocking) |
| Input validation | Server-side (security.py) | Client-side + Service layer |
| Script whitelist | `allowed_scripts` set | Same, copy as-is |
| Admin actions | Role decorator | `is_admin` property check |
| Đóng gói | Docker / gunicorn | PyInstaller → .desktop |
