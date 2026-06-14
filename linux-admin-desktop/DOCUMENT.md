# Tài liệu Dự án Linux Administration Desktop

## Hệ thống quản trị Linux qua giao diện đồ họa

---

# Mục lục

1. [Tổng quan dự án](#1-tổng-quan-dự-án)
2. [Phân tích yêu cầu](#2-phân-tích-yêu-cầu)
3. [Thiết kế kiến trúc hệ thống](#3-thiết-kế-kiến-trúc-hệ-thống)
4. [Use Case](#4-use-case)
5. [Chức năng chi tiết](#5-chức-năng-chi-tiết)
6. [Cơ sở lý thuyết hệ thống](#6-cơ-sở-lý-thuyết-hệ-thống)
7. [Hướng dẫn cài đặt và sử dụng](#7-hướng-dẫn-cài-đặt-và-sử-dụng)
8. [Minh họa luồng xử lý](#8-minh-họa-luồng-xử-lý)
9. [Kết luận và hướng phát triển](#9-kết-luận-và-hướng-phát-triển)

---

# 1. Tổng quan dự án

## 1.1. Giới thiệu

**Linux Administration Desktop** là một ứng dụng桌面 (desktop application) quản trị hệ thống Linux dành cho người quản trị (admin) và người dùng thông thường. Ứng dụng cung cấp giao diện đồ họa trực quan để thực hiện các tác vụ quản trị như:

- Quản lý file và thư mục (CRUD: tạo, xem, sửa, xóa)
- Quản lý thời gian hệ thống (set time, timezone, NTP sync)
- Quản lý package (APT: install, remove, upgrade, search)
- Quản lý tác vụ định kỳ (Cron job: create, update, delete, run)
- Xem audit log (nhật ký hành động người dùng)

Điểm đặc biệt: ứng dụng sử dụng **shell scripts** làm backend thay vì gọi trực tiếp system calls. Điều này minh họa cách xây dựng một lớp abstraction phía trên các công cụ Linux command-line.

## 1.2. Mục tiêu

| Mục tiêu | Mô tả |
|---|---|
| **Quản trị tập trung** | Cung cấp một giao diện duy nhất cho nhiều tác vụ quản trị Linux |
| **Phân quyền** | Admin có toàn quyền, user chỉ xem được thông tin cơ bản |
| **Audit trail** | Ghi lại mọi hành động quan trọng vào database + file log |
| **An toàn** | Xác thực mật khẩu, không cho phép truy cập trái phép |
| **Dễ sử dụng** | Giao diện trực quan, không cần nhớ câu lệnh phức tạp |

## 1.3. Công nghệ sử dụng

| Công nghệ | Vai trò |
|---|---|
| **Python 3.12** | Ngôn ngữ chính |
| **PyQt6** | GUI framework (desktop application) |
| **SQLAlchemy 2.x** | ORM cho SQLite database |
| **Werkzeug** | Password hashing (PBKDF2) |
| **pytz** | Danh sách timezone |
| **Bash scripts** | Backend xử lý tác vụ hệ thống |
| **SQLite** | Lưu trữ user, action logs |
| **PyInstaller** | Đóng gói ứng dụng thành binary |

---

# 2. Phân tích yêu cầu

## 2.1. Yêu cầu chức năng

| ID | Yêu cầu | Mô tả |
|---|---|---|
| F01 | Đăng nhập | Xác thực người dùng với username + password |
| F02 | Phân quyền | 2 vai trò: admin (toàn quyền), user (chỉ xem thông tin) |
| F03 | File Browser | Duyệt thư mục, xem danh sách file (type, name, path) |
| F04 | Create File | Tạo file mới trong thư mục hiện tại |
| F05 | Create Folder | Tạo thư mục mới |
| F06 | Rename | Đổi tên file/thư mục |
| F07 | Copy | Copy file/thư mục đến đích |
| F08 | Move | Di chuyển file/thư mục |
| F09 | Delete | Xóa file/thư mục (có xác nhận) |
| F10 | Search File | Tìm kiếm file theo keyword |
| F11 | Chmod | Thay đổi permission mode |
| F12 | Chown | Thay đổi owner/group |
| F13 | Xem thời gian | Hiển thị thời gian hệ thống real-time |
| F14 | Set Time | Thiết lập thời gian hệ thống (admin) |
| F15 | Set Timezone | Thiết lập timezone (admin) |
| F16 | Enable/Disable NTP | Bật/tắt NTP (admin) |
| F17 | Sync NTP | Đồng bộ thời gian qua NTP (admin) |
| F18 | List Packages | Danh sách package đã cài (dpkg-query) |
| F19 | Search Package | Tìm package trong danh sách |
| F20 | Install Package | Cài package mới qua apt (admin) |
| F21 | Remove Package | Gỡ package (admin) |
| F22 | Upgrade Package | Nâng cấp package (admin) |
| F23 | List Cron Jobs | Danh sách cron jobs hiện tại (admin) |
| F24 | Create Cron Job | Thêm cron job mới (admin) |
| F25 | Update Cron Job | Sửa cron job (admin) |
| F26 | Delete Cron Job | Xóa cron job (admin) |
| F27 | Run Job Now | Chạy ngay một job (admin) |
| F28 | Audit Logs | Xem lịch sử hành động người dùng (admin) |
| F29 | Logout | Đăng xuất và quay về màn hình login |
| F30 | Dashboard | Trang chào với thông tin user và role |

## 2.2. Yêu cầu phi chức năng

| ID | Yêu cầu | Mô tả |
|---|---|---|
| NF01 | Bảo mật | Mật khẩu được hash bằng werkzeug (PBKDF2) |
| NF02 | Audit trail | Mọi hành động đều ghi vào DB + file log |
| NF03 | Non-blocking | Dùng QThread cho các tác vụ dài (install package) |
| NF04 | Portable | Chạy trên Ubuntu/Debian (dùng apt, dpkg, timedatectl) |
| NF05 | Packaging | Hỗ trợ đóng gói bằng PyInstaller |

## 2.3. Ma trận phân quyền

| Chức năng | Admin | User |
|---|---|---|
| Dashboard | ✔ | ✔ |
| File Browser | ✔ | ✔ |
| Create/Delete/Rename/... | ✔ | ❌ (disabled) |
| System Time (view) | ✔ | ✔ |
| Set Time / Timezone / NTP | ✔ | ❌ |
| Package List | ✔ | ✔ |
| Install / Remove / Upgrade | ✔ | ❌ |
| Task Scheduler (Cron) | ✔ | ❌ |
| Audit Logs | ✔ | ❌ |

---

# 3. Thiết kế kiến trúc hệ thống

## 3.1. Kiến trúc tổng thể

```
┌─────────────────────────────────────────────────────────────┐
│                    UI Layer (PyQt6)                          │
│                                                             │
│  ┌──────────────┐  ┌──────────────────────────────────┐    │
│  │ LoginWindow  │  │         MainWindow                │    │
│  │ (QDialog)    │  │  ┌──────────────┐                │    │
│  │  - username  │  │  │   Sidebar    │ QStackedWidget  │    │
│  │  - password  │  │  │  (QListW.)   │                 │    │
│  │  - gradient  │  │  │             │ ┌─────────────┐ │    │
│  │    theme     │  │  │ • Dashboard │ │ Dashboard   │ │    │
│  └──────┬───────┘  │  │ • File Mgt  │ │ (welcome)   │ │    │
│         │          │  │ • Time      │ ├─────────────┤ │    │
│    accept()        │  │ • Packages  │ │ FileManager │ │    │
│         │          │  │ • Scheduler │ │ Widget      │ │    │
│         ▼          │  │ • Logs      │ ├─────────────┤ │    │
│  ┌──────────┐      │  │             │ │ SystemTime  │ │    │
│  │  Auth    │      │  │             │ │ Widget      │ │    │
│  │ Manager  │      │  │             │ ├─────────────┤ │    │
│  └──────────┘      │  │             │ │ PackageMgt  │ │    │
│                    │  │             │ │ Widget      │ │    │
│                    │  │             │ ├─────────────┤ │    │
│                    │  │             │ │ TaskSched   │ │    │
│                    │  │             │ │ Widget      │ │    │
│                    │  │             │ ├─────────────┤ │    │
│                    │  │             │ │ LogsViewer  │ │    │
│                    │  │             │ └─────────────┘ │    │
│                    │  └──────────────┘                 │    │
│                    └───────────────────────────────────┘    │
│                           │                                 │
│                           ▼                                 │
│  ┌────────────────────────────────────────────────────┐     │
│  │                 App Module Layer                    │     │
│  │  ┌─────────┐  ┌─────────┐  ┌─────────┐  ┌───────┐ │     │
│  │  │auth.py  │  │executor │  │parsers  │  │logging│ │     │
│  │  │         │  │.py      │  │.py      │  │.py    │ │     │
│  │  │- login  │  │- Script │  │- parse  │  │- DB   │ │     │
│  │  │- logout │  │  Exec   │  │  file   │  │  log  │ │     │
│  │  │- RBAC   │  │  utor   │  │  listing│  │- file │ │     │
│  │  │         │  │- run()  │  │- parse  │  │  log  │ │     │
│  │  │         │  │         │  │  cron   │  │       │ │     │
│  │  └─────────┘  └────┬────┘  └─────────┘  └───────┘ │     │
│  │                    │                                │     │
│  │  ┌─────────────────▼──────────────────────────┐     │     │
│  │  │            database.py                      │     │     │
│  │  │  - User model (id, username, hash, role)    │     │     │
│  │  │  - ActionLog model (user, action, result)   │     │     │
│  │  │  - init_db() — tạo user mặc định            │     │     │
│  │  └─────────────────────────────────────────────┘     │     │
│  └──────────────────┬───────────────────────────────────┘     │
│                     │                                        │
│                     ▼                                        │
│  ┌────────────────────────────────────────────────────┐     │
│  │              Shell Script Backend                   │     │
│  │  ┌──────────┬──────────┬─────────┬──────────────┐  │     │
│  │  │ Files:   │ Time:    │ Pkgs:   │ Cron:        │  │     │
│  │  │ 26 .sh   │ set,show │ install,│ create,list, │  │     │
│  │  │ scripts  │ ntp, tz  │ remove, │ delete,run   │  │     │
│  │  └──────────┴──────────┴─────────┴──────────────┘  │     │
│  └──────────────────┬──────────────────────────────────┘     │
│                     │                                        │
│                     ▼                                        │
│  ┌────────────────────────────────────────────────────┐     │
│  │          Linux OS (system commands)                 │     │
│  │  mv, cp, rm, chmod, chown, apt, timedatectl,       │     │
│  │  crontab, dpkg, date, find                         │     │
│  └────────────────────────────────────────────────────┘     │
└─────────────────────────────────────────────────────────────┘
```

## 3.2. Sơ đồ package

```
linux-admin-desktop/
├── main.py                          # Entry point
├── requirements.txt                 # Python dependencies
├── .env.example                     # Biến môi trường mẫu
├── linux-admin-desktop.spec         # PyInstaller spec
├── app/
│   ├── __init__.py
│   ├── auth.py                      # Xác thực người dùng
│   ├── database.py                  # ORM models + init DB
│   ├── executor.py                  # Shell script executor
│   ├── parsers.py                   # Parse output: file listing, cron
│   ├── logging.py                   # Audit log (DB + file)
│   └── rbac.py                      # Role-based access helpers
├── ui/
│   ├── __init__.py
│   ├── login_window.py              # Login dialog
│   ├── main_window.py               # Main window + sidebar
│   ├── file_manager_widget.py       # File management UI
│   ├── system_time_widget.py        # System time UI
│   ├── package_manager_widget.py    # Package management UI
│   ├── task_scheduler_widget.py     # Cron job UI (admin)
│   └── logs_viewer_widget.py        # Audit log viewer (admin)
├── scripts/                         # Shell scripts (26 files)
│   ├── list_files.sh, create_file.sh, create_folder.sh
│   ├── rename_file.sh, copy_file.sh, move_file.sh
│   ├── delete_file.sh, search_file.sh
│   ├── chmod_file.sh, chown_file.sh
│   ├── show_time.sh, set_time.sh, set_timezone.sh
│   ├── enable_ntp.sh, disable_ntp.sh, sync_time.sh
│   ├── list_packages.sh, search_package.sh
│   ├── install_package.sh, remove_package.sh, upgrade_package.sh
│   ├── list_cron.sh, create_cron.sh, update_cron.sh
│   ├── delete_cron.sh, run_job.sh
├── instance/
│   └── dashboard.db                 # SQLite database
├── logs/
│   └── system.log                   # Audit log file
├── build/                           # PyInstaller build
└── dist/                            # PyInstaller dist
    └── linux-admin-desktop          # Binary executable
```

## 3.3. Nguyên tắc thiết kế

1. **Layered Architecture** — 4 lớp rõ ràng:
   - UI Layer (PyQt6 widgets)
   - App Layer (business logic, auth, executor, parsers)
   - Script Layer (Bash shell scripts)
   - OS Layer (system commands)

2. **Role-Based Access Control** — Mọi widget kiểm tra `auth.is_admin` trước khi hiển thị các nút admin

3. **Asynchronous Execution** — Script chạy trong `QThread` để không block GUI (đặc biệt khi install package có thể mất nhiều thời gian)

4. **Audit Trail** — Mọi hành động đều ghi vào SQLite database + file log với username, timestamp, action, result, detail

5. **Shell Script as Backend** — Các tác vụ quản trị được implement dưới dạng shell scripts riêng biệt, dễ bảo trì và mở rộng

## 3.4. Sơ đồ database

```
┌───────────────────┐      ┌──────────────────────────┐
│       User        │      │       ActionLog           │
├───────────────────┤      ├──────────────────────────┤
│ id (PK, int)      │      │ id (PK, int)              │
│ username (unique) │      │ username (FK→User)        │
│ password_hash     │      │ action (varchar 255)      │
│ role (admin/user) │      │ result (SUCCESS/FAILED)   │
│ created_at        │      │ detail (text)             │
└───────────────────┘      │ created_at                │
                           └──────────────────────────┘
```

---

# 4. Use Case

## 4.1. Actors

- **Admin**: Quản trị viên, có toàn quyền truy cập mọi chức năng
- **User**: Người dùng thông thường, chỉ xem được dashboard, file browser, thời gian, package list

## 4.2. Danh sách Use Case

| ID | Use Case | Actor | Mô tả |
|---|---|---|---|
| UC01 | Login | Admin/User | Đăng nhập với username + password |
| UC02 | Logout | Admin/User | Đăng xuất, quay về màn hình login |
| UC03 | View Dashboard | Admin/User | Xem trang chào + thông tin user |
| UC04 | Browse Files | Admin/User | Duyệt thư mục, xem danh sách file |
| UC05 | Create File | Admin | Tạo file mới |
| UC06 | Create Folder | Admin | Tạo thư mục mới |
| UC07 | Rename File | Admin | Đổi tên file/thư mục |
| UC08 | Copy File | Admin | Copy file/thư mục |
| UC09 | Move File | Admin | Di chuyển file/thư mục |
| UC10 | Delete File | Admin | Xóa file/thư mục (có xác nhận) |
| UC11 | Search File | Admin | Tìm file theo tên |
| UC12 | Change Permissions | Admin | Thay đổi chmod |
| UC13 | Change Owner | Admin | Thay đổi chown |
| UC14 | View System Time | Admin/User | Xem thời gian hiện tại |
| UC15 | Set System Time | Admin | Thiết lập thời gian |
| UC16 | Set Timezone | Admin | Thiết lập timezone |
| UC17 | Manage NTP | Admin | Enable/disable/sync NTP |
| UC18 | View Package List | Admin/User | Xem danh sách package đã cài |
| UC19 | Search Package | Admin/User | Tìm package |
| UC20 | Install Package | Admin | Cài package mới |
| UC21 | Remove Package | Admin | Gỡ package |
| UC22 | Upgrade Package | Admin | Nâng cấp package |
| UC23 | View Cron Jobs | Admin | Xem danh sách cron jobs |
| UC24 | Create Cron Job | Admin | Thêm cron job mới |
| UC25 | Update Cron Job | Admin | Sửa cron job |
| UC26 | Delete Cron Job | Admin | Xóa cron job |
| UC27 | Run Job Now | Admin | Chạy job ngay lập tức |
| UC28 | View Audit Logs | Admin | Xem lịch sử hành động |

## 4.3. Use Case chi tiết

### UC01: Login

| Mục | Mô tả |
|---|---|
| **Mô tả** | Người dùng đăng nhập bằng username và password |
| **Precondition** | Ứng dụng vừa khởi động |
| **Postcondition** | Nếu thành công → MainWindow hiện ra. Nếu thất bại → error message |
| **Luồng chính** | 1. User nhập username + password<br>2. Click Login hoặc Enter<br>3. `AuthManager.login()` gọi<br>4. Query user từ database<br>5. `check_password_hash()` verify<br>6. Nếu OK → `accept()` → MainWindow |

### UC05: Create File

| Mục | Mô tả |
|---|---|
| **Actor** | Admin |
| **Mô tả** | Tạo file mới trong thư mục hiện tại |
| **Luồng chính** | 1. User chọn thư mục trong File Browser<br>2. Click "New File"<br>3. Nhập tên file trong QInputDialog<br>4. `ScriptExecutor.run("create_file.sh", [path, name])`<br>5. File được tạo → reload danh sách |

### UC12: Change Permissions (Chmod)

| Mục | Mô tả |
|---|---|
| **Actor** | Admin |
| **Mô tả** | Thay đổi permission của file/thư mục |
| **Luồng chính** | 1. Click chuột phải vào file → context menu<br>2. Chọn "Chmod"<br>3. Nhập mode (vd: 755)<br>4. Chạy `chmod_file.sh` |
| **Kernel concept** | Permission bits: rwxr-xr-x = 755, struct inode.i_mode |

### UC14: View System Time

| Mục | Mô tả |
|---|---|
| **Actor** | Admin/User |
| **Mô tả** | Xem thời gian hệ thống, tự động refresh mỗi 2 giây |
| **Luồng chính** | 1. Click "System Time" trong sidebar<br>2. `show_time.sh` được gọi<br>3. Kết quả hiển thị ở font lớn<br>4. QTimer 2s tự động cập nhật |

### UC20: Install Package

| Mục | Mô tả |
|---|---|
| **Actor** | Admin |
| **Mô tả** | Cài package mới qua apt-get |
| **Luồng chính** | 1. Nhập tên package (vd: htop)<br>2. Click "Install"<br>3. `install_package.sh` chạy trong QThread<br>4. Output real-time hiển thị<br>5. Reload danh sách packages |

### UC24: Create Cron Job

| Mục | Mô tả |
|---|---|
| **Actor** | Admin |
| **Mô tả** | Thêm cron job mới |
| **Luồng chính** | 1. Nhập schedule (vd: `*/5 * * * *` hoặc `@daily`)<br>2. Nhập command (vd: `/usr/bin/backup.sh`)<br>3. Click "Create"<br>4. `create_cron.sh` được gọi<br>5. Reload danh sách cron jobs |

---

# 5. Chức năng chi tiết

## 5.1. Hệ thống xác thực (`app/auth.py`)

### 5.1.1. AuthManager

Lớp quản lý xác thực, lưu trạng thái đăng nhập:

```python
class AuthManager:
    def login(username, password) -> bool
    def logout()
    @property current_user -> dict | None
    @property is_authenticated -> bool
    @property is_admin -> bool
```

- `login()` query user từ DB, verify password hash bằng `werkzeug.security.check_password_hash()`
- Password hash được tạo bằng `generate_password_hash()` (PBKDF2 với SHA-256)

### 5.1.2. User mặc định

Khi khởi tạo database lần đầu, hai user được tạo tự động:

| Username | Password | Role |
|---|---|---|
| admin | admin123 | admin |
| user | user123 | user |

Có thể cấu hình qua biến môi trường: `ADMIN_USERNAME`, `ADMIN_PASSWORD`, `USER_USERNAME`, `USER_PASSWORD`.

## 5.2. Shell Script Executor (`app/executor.py`)

### 5.2.1. ScriptExecutor

```python
class ScriptExecutor:
    def run(script_name, args) -> tuple[bool, str]
```

- Tìm script trong thư mục `scripts/`
- Gọi `subprocess.run()` với timeout 120 giây
- Trả về (success: bool, output: str)

### 5.2.2. Danh sách scripts

| Module | Script | Mô tả | Command |
|---|---|---|---|
| **Files** | `list_files.sh` | Liệt kê file/ DIR | `ls`, `realpath`, `printf` |
| | `create_file.sh` | Tạo file | `touch` |
| | `create_folder.sh` | Tạo folder | `mkdir -p` |
| | `rename_file.sh` | Đổi tên | `mv` |
| | `copy_file.sh` | Copy | `cp -r` |
| | `move_file.sh` | Di chuyển | `mv` |
| | `delete_file.sh` | Xóa | `rm -rf` |
| | `search_file.sh` | Tìm kiếm | `find` |
| | `chmod_file.sh` | Permission | `chmod` |
| | `chown_file.sh` | Owner | `chown` |
| **Time** | `show_time.sh` | Xem thời gian | `date` |
| | `set_time.sh` | Đặt thời gian | `timedatectl` |
| | `set_timezone.sh` | Đặt timezone | `timedatectl` |
| | `enable_ntp.sh` | Bật NTP | `timedatectl` |
| | `disable_ntp.sh` | Tắt NTP | `timedatectl` |
| | `sync_time.sh` | Sync NTP | `timedatectl` |
| **Packages** | `list_packages.sh` | Danh sách | `dpkg-query` |
| | `search_package.sh` | Tìm kiếm | `dpkg-query -l` |
| | `install_package.sh` | Cài đặt | `apt-get install -y` |
| | `remove_package.sh` | Gỡ bỏ | `apt-get remove -y` |
| | `upgrade_package.sh` | Nâng cấp | `apt-get upgrade -y` |
| **Cron** | `list_cron.sh` | Liệt kê | `crontab -l` |
| | `create_cron.sh` | Thêm | `crontab -` |
| | `update_cron.sh` | Sửa | `crontab -` |
| | `delete_cron.sh` | Xóa | `crontab -` |
| | `run_job.sh` | Chạy ngay | `eval` |

## 5.3. File Manager (`ui/file_manager_widget.py` + 10 scripts)

### 5.3.1. Layout

- Path navigation bar (QLineEdit + Go + Up buttons)
- Action buttons row (New File, New Folder, Rename, Copy, Move, Delete, Search, Chmod, Chown, Refresh)
- File table (3 columns: Type, Name, Path)
- Output console (dark terminal style)
- Context menu (right-click) với các tác vụ tương tự

### 5.3.2. Danh sách file

Script `list_files.sh` output format:

```
DIR<tab>dirname<tab>/path/to/dir
FILE<tab>filename<tab>/path/to/file
```

Parser `parse_file_listing()` chuyển thành list of dict:

```python
[
    {"type": "DIR", "name": "docs", "path": "/home/docs", "is_dir": True},
    {"type": "FILE", "name": "readme.txt", "path": "/home/readme.txt", "is_dir": False},
]
```

### 5.3.3. Các tác vụ

Mỗi tác vụ chạy script tương ứng trong **ScriptThread** (QThread):

- **Create File**: `create_file.sh [path] [name]` → `touch "$path/$name"`
- **Copy**: `copy_file.sh [source] [dest]` → `cp -r "$source" "$dest"`
- **Delete**: `delete_file.sh [target]` → `rm -rf "$target"` (có xác nhận)
- **Rename**: `rename_file.sh [source] [new_name]` → `mv "$source" "$(dirname "$source")/$new_name"`
- **Chmod**: `chmod_file.sh [target] [mode]` → `chmod "$mode" "$target"`

## 5.4. System Time Manager (`ui/system_time_widget.py` + 6 scripts)

### 5.4.1. Layout

- **Time Display**: font lớn (28pt monospace), tự động refresh mỗi 2 giây
- **Admin panel** (chỉ hiện nếu `auth.is_admin`):
  - Set Time: input datetime + button
  - Set Timezone: dropdown (pytz.common_timezones) + button
  - NTP controls: Enable / Disable / Sync buttons

### 5.4.2. Các lệnh systemd

Các script sử dụng `timedatectl` — công cụ quản lý thời gian của systemd:

```bash
# Xem thời gian
timedatectl show --property=TimeUSec --value

# Đặt thời gian
timedatectl set-time "2026-06-14 14:30:00"

# Đặt timezone
timedatectl set-timezone Asia/Ho_Chi_Minh

# Bật/tắt NTP
timedatectl set-ntp true
timedatectl set-ntp false
```

## 5.5. Package Manager (`ui/package_manager_widget.py` + 5 scripts)

### 5.5.1. Layout

- Search bar + Search/Refresh buttons
- Admin action group: package name input + Install/Remove/Upgrade buttons
- Package list table (cột: Package Name)
- Output console

### 5.5.2. Các lệnh APT

Sử dụng công cụ quản lý package Debian/Ubuntu:

| Script | Command | Mô tả |
|---|---|---|
| `list_packages.sh` | `dpkg-query -W` | Liệt kê tất cả package đã cài |
| `search_package.sh` | `dpkg-query -l \| grep` | Tìm package theo tên |
| `install_package.sh` | `apt-get install -y` | Cài package (non-interactive) |
| `remove_package.sh` | `apt-get remove -y` | Gỡ package |
| `upgrade_package.sh` | `apt-get upgrade -y` | Nâng cấp package |

## 5.6. Task Scheduler (`ui/task_scheduler_widget.py` + 5 scripts)

### 5.6.1. Layout

- **Form group**: Schedule input (vd: `*/5 * * * *` hoặc `@daily`) + Command input
- **Action buttons**: Create, Update, Delete, Run Now, Refresh
- **Table**: Line, Schedule, Command, Minute, Hour, Day, Month, Weekday
- **Output console**

### 5.6.2. Cron expression parser

Hàm `parse_cron_schedule()` trong `app/parsers.py` hỗ trợ:

- **5-field format**: `minute hour day month weekday` → `*/5 * * * *`
- **Macros**: `@hourly`, `@daily`, `@midnight`, `@weekly`, `@monthly`, `@yearly`, `@annually`
- **Auto detect mode**: hourly / daily / weekly / monthly / yearly / custom

### 5.6.3. Crontab operations

Các script thao tác với `crontab`:

```bash
# List: crontab -l
# Create/Update/Delete: (crontab -l; echo "schedule command") | crontab -
# Run now: eval "$command"
```

## 5.7. Audit Log (`ui/logs_viewer_widget.py` + `app/logging.py`)

### 5.7.1. SystemLogger

```python
class SystemLogger:
    def log(username, action, success, detail):
        # Ghi vào file: logs/system.log
        # Ghi vào DB: ActionLog table
```

Mỗi log entry gồm:
- Timestamp
- Username
- Action (vd: `files:delete`, `time:set`, `packages:install`, `cron:create`)
- Result (SUCCESS / FAILED)
- Detail (thông tin chi tiết, tối đa 2000 ký tự)

### 5.7.2. Logs viewer

- Query 200 log gần nhất từ database
- Sắp xếp theo thời gian giảm dần
- Màu sắc: SUCCESS = xanh, FAILED = đỏ
- Chỉ admin mới xem được

---

# 6. Cơ sở lý thuyết hệ thống

## 6.1. Quản lý người dùng và phân quyền (RBAC)

**Role-Based Access Control (RBAC)** là mô hình bảo mật phổ biến trong quản trị hệ thống:

- **User** → **Role** → **Permission**
- Admin có role = "admin", User có role = "user"
- Mọi widget kiểm tra `auth.is_admin` trước khi hiển thị các nút admin

## 6.2. Password hashing với PBKDF2

Werkzeug sử dụng PBKDF2 (Password-Based Key Derivation Function 2) với SHA-256:

```
hash = pbkdf2_sha256(password, salt, iterations=260000)
```

- **Salt**: ngẫu nhiên 16 bytes, chống rainbow table attack
- **Iterations**: 260000 vòng lặp, làm chậm brute-force
- So sánh: `check_password_hash(hash, password)` — tự động trích xuất salt từ hash

## 6.3. Shell script execution

### 6.3.1. subprocess.run()

```python
subprocess.run(
    [script_path, *args],
    capture_output=True,   # stdout + stderr
    text=True,             # trả về string
    timeout=120,           # timeout 2 phút
    check=False,           # không raise exception nếu exit code ≠ 0
)
```

### 6.3.2. Ưu điểm của shell script backend

1. **Tận dụng công cụ có sẵn**: `cp`, `mv`, `rm`, `chmod`, `apt`, `timedatectl`, `crontab`
2. **Dễ mở rộng**: Thêm script mới không cần sửa code Python
3. **Bảo trì đơn giản**: Script độc lập, dễ test riêng lẻ

### 6.3.3. Hạn chế

1. **Phụ thuộc hệ thống**: Chạy trên Debian/Ubuntu (apt, dpkg)
2. **Bảo mật**: Cần cẩn thận với shell injection (tham số được truyền dưới dạng list, không phải string)
3. **Hiệu năng**: Mỗi lần gọi script tốn overhead process creation

## 6.4. Cơ chế cron (Cron daemon)

Cron là một system service chạy ngầm, đọc file crontab và thực thi lệnh theo lịch.

### 6.4.1. Crontab format

```
# ┌───────── minute (0-59)
# │ ┌───────── hour (0-23)
# │ │ ┌───────── day of month (1-31)
# │ │ │ ┌───────── month (1-12)
# │ │ │ │ ┌───────── weekday (0-7, 0=Sun)
# * * * * * command
```

### 6.4.2. Macro

| Macro | Thay thế | Chạy lúc |
|---|---|---|
| `@hourly` | `0 * * * *` | Đầu mỗi giờ |
| `@daily` | `0 0 * * *` | Nửa đêm |
| `@weekly` | `0 0 * * 0` | Chủ nhật 0h |
| `@monthly` | `0 0 1 * *` | Ngày 1 hàng tháng |

### 6.4.3. Crontab thao tác

- **List**: `crontab -l` — in nội dung crontab hiện tại
- **Edit**: `crontab -e` — mở editor
- **Replace**: `crontab -` — đọc từ stdin

Script `create_cron.sh` dùng cơ chế:
```bash
(crontab -l 2>/dev/null; echo "$schedule $command") | crontab -
```

## 6.5. Hệ thống thời gian Linux

### 6.5.1. systemd-timesyncd

Ubuntu sử dụng `systemd-timesyncd` để quản lý NTP:

```
timedatectl set-ntp true   # Bật NTP
timedatectl set-ntp false  # Tắt NTP
timedatectl set-time "..." # Đặt thời gian (chỉ khi NTP off)
```

### 6.5.2. Timezone database

Linux lưu timezone trong `/usr/share/zoneinfo/`. Các lệnh:

```
timedatectl list-timezones       # Liệt kê tz
timedatectl set-timezone Asia/Ho_Chi_Minh  # Đặt tz
```

## 6.6. APT Package Management

### 6.6.1. dpkg

`dpkg` là công cụ cấp thấp quản lý package .deb:

```bash
dpkg-query -W -f='${binary:Package}\t${Version}\n'  # List installed
dpkg-query -l 'pattern'                               # Search
```

### 6.6.2. apt-get

`apt-get` là frontend cao cấp, tự động xử lý dependencies:

```bash
apt-get update              # Cập nhật index
apt-get install -y htop     # Cài package (non-interactive)
apt-get remove -y htop      # Gỡ package
apt-get upgrade -y          # Nâng cấp tất cả
```

## 6.7. File permissions (chmod, chown)

### 6.7.1. Permission bits

```
rwx rwx rwx
 │   │   │
 │   │   └── Other (world)
 │   └────── Group
 └────────── User (owner)
```

Mỗi nhóm 3 bits: Read (4), Write (2), Execute (1)

| Octal | Binary | Permissions |
|---|---|---|
| 7 | 111 | rwx |
| 6 | 110 | rw- |
| 5 | 101 | r-x |
| 4 | 100 | r-- |
| 0 | 000 | --- |

Ví dụ: `755` = `rwxr-xr-x` (owner full, group/other read+execute)

### 6.7.2. chown

```bash
chown user:group file.txt
```

Thay đổi owner và group của file. User và group được tra cứu từ `/etc/passwd` và `/etc/group`.

---

# 7. Hướng dẫn cài đặt và sử dụng

## 7.1. Yêu cầu hệ thống

- Hệ điều hành: **Ubuntu 22.04+ hoặc Debian 11+**
- Python 3.10+
- Quyền sudo (cho các tác vụ admin: apt, timedatectl, crontab)
- pip (Python package manager)

## 7.2. Cài đặt

```bash
cd linux-admin-desktop

# Tạo virtual environment
python3 -m venv .venv
source .venv/bin/activate

# Cài dependencies
pip install -r requirements.txt

# (Optional) Cấu hình biến môi trường
cp .env.example .env
# Sửa .env nếu muốn đổi mật khẩu mặc định
```

## 7.3. Chạy ứng dụng

```bash
python3 main.py
```

Ứng dụng khởi động → Login window hiện ra.

## 7.4. Tài khoản mặc định

| Username | Password | Role |
|---|---|---|
| `admin` | `admin123` | Admin (toàn quyền) |
| `user` | `user123` | User (chỉ xem) |

## 7.5. Hướng dẫn sử dụng

### Dashboard
- Sau khi đăng nhập, dashboard hiển thị tên và role
- Click các mục ở sidebar để chuyển chức năng

### File Management
1. Click "File Management" trong sidebar
2. Duyệt thư mục bằng cách double-click hoặc nhập path
3. Chọn file → Click action button hoặc right-click → context menu
4. Output hiển thị ở console phía dưới

### System Time
1. Click "System Time" trong sidebar
2. Thời gian hiện tại hiển thị tự động refresh 2 giây
3. Admin có thể: set time, set timezone, bật/tắt/sync NTP

### Packages
1. Click "Packages" trong sidebar
2. Xem danh sách package đã cài
3. Admin: nhập tên package → Install / Remove / Upgrade
4. Tìm kiếm bằng ô Search

### Task Scheduler (admin only)
1. Click "Task Scheduler" trong sidebar
2. Nhập schedule (vd: `*/5 * * * *`) và command
3. Click Create/Update/Delete/Run Now

### Audit Logs (admin only)
1. Click "Audit Logs" trong sidebar
2. Xem 200 action gần nhất
3. Refresh để cập nhật

---

# 8. Minh họa luồng xử lý

## 8.1. Luồng đăng nhập

```
main.py
    │
    ├─ init_db() → tạo database + user mặc định
    │
    ├─ AuthManager()
    │
    ├─ LoginWindow(auth).exec()
    │   │
    │   ├─ User nhập username + password
    │   ├─ Click Login
    │   ├─ auth.login(username, password)
    │   │   ├─ Query User từ DB
    │   │   ├─ check_password_hash(hash, password)
    │   │   └─ Lưu current_user nếu OK
    │   │
    │   ├─ Nếu OK → accept() → MainWindow
    │   └─ Nếu FAIL → error_label.show()
    │
    └─ MainWindow(auth)
        ├─ _populate_nav()
        │   ├─ Nếu admin: thêm "Task Scheduler" + "Audit Logs"
        │   └─ Nếu user: chỉ 4 mục cơ bản
        ├─ _switch_page(index)
        └─ show()
```

## 8.2. Luồng thực thi script

```
User click "Install Package" (htop)
    │
    ▼
package_manager_widget._install_package()
    │
    ├─ self.pkg_name_input.text() → "htop"
    │
    ├─ logger.log("packages:install", ...)
    │
    ├─ thread = PackageThread(executor, "install_package.sh", ["htop"])
    │   └─ executor.run("install_package.sh", ["htop"])
    │       ├─ Tìm script: scripts/install_package.sh
    │       ├─ subprocess.run(["scripts/install_package.sh", "htop"], ...)
    │       │   └─ Script chạy: apt-get install -y htop
    │       └─ return (success, output)
    │
    ├─ thread.finished → _on_script_done()
    │   ├─ Append output vào console
    │   └─ _load_packages() reload table
    │
    └─ logger.log("packages:install", success, detail)
```

## 8.3. Luồng package management

```
get_interface_stats()
    │
    ▼
Đọc /proc/net/dev
    │
    ├─ Inter-|   Receive   |  Transmit
    │   face |bytes packets errs drop ... |bytes packets errs drop ...
    │   lo:  7251926  ...
    │   ens33: ...
    │
    ▼
parse_proc_net_dev() → list[dict]
    │
    ▼
Hiển thị lên QTableWidget (11 cột)
    │
    ▼
Tính traffic speed:
    ├─ get_traffic_snapshot() → snapshot1
    ├─ sleep(3s)
    ├─ get_traffic_snapshot() → snapshot2
    └─ speed = (snapshot2 - snapshot1) / 3
```

## 8.4. Luồng cron job creation

```
User nhập: schedule="*/5 * * * *", command="/usr/bin/backup.sh"
    │
    ▼
Click "Create"
    │
    ▼
task_scheduler_widget._create_job()
    │
    ├─ validate input (not empty)
    │
    ├─ thread = CronThread(executor, "create_cron.sh", ["*/5 * * * *", "/usr/bin/backup.sh"])
    │   └─ executor.run("create_cron.sh", ["*/5 * * * *", "/usr/bin/backup.sh"])
    │       └─ Script chạy:
    │           (crontab -l 2>/dev/null; echo "*/5 * * * * /usr/bin/backup.sh") | crontab -
    │
    ├─ _on_script_done(): reload danh sách
    │
    └─ logger.log("cron:create", True, "Schedule: */5 * * * *, Cmd: ...")
```

---

# 9. Kết luận và hướng phát triển

## 9.1. Đánh giá

Linux Administration Desktop là một ứng dụng desktop quản trị Linux với các ưu điểm:

| Tiêu chí | Đánh giá |
|---|---|
| **Tính đầy đủ** | 5 module chính: File, Time, Package, Cron, Audit |
| **Bảo mật** | Xác thực mật khẩu + phân quyền admin/user |
| **Audit trail** | Mọi hành động ghi vào DB và file |
| **UX** | Dark sidebar, gradient header, terminal output, context menu |
| **Portability** | Dùng script backend, dễ dàng chuyển đổi distro |

**Hạn chế:**
- Phụ thuộc vào apt/dpkg (chỉ chạy trên Debian/Ubuntu)
- Không hỗ trợ đa người dùng đồng thời
- Package install chạy trong thread nhưng apt-get có thể yêu cầu sudo

## 9.2. Hướng phát triển tương lai

| Tính năng | Mô tả |
|---|---|
| **User Management** | Thêm/xóa/sửa user trong GUI |
| **Service Management** | systemctl start/stop/restart services |
| **Network Config** | Quản lý network interfaces, IP, DNS |
| **Disk Management** | Xem disk usage, mount/umount |
| **Process Monitor** | Xem và kill processes (top-like) |
| **Firewall** | UFW frontend |
| **SSH Keys** | Quản lý SSH authorized keys |
| **Docker** | Docker container management |
| **Logs Viewer** | Xem journald logs |
| **Multi-language** | Hỗ trợ i18n |

## 9.3. Kiến thức Linux liên quan

| Chủ đề | Mô tả | Liên quan |
|---|---|---|
| **systemd** | Init system, service manager | timedatectl |
| **APT** | Advanced Package Tool | apt-get, dpkg |
| **Cron** | Job scheduler | crontab |
| **RBAC** | Role-based access control | User roles |
| **Shell script** | Bash programming | 26 shell scripts |
| **File permissions** | rwx, chmod, chown | File management |
| **PBKDF2** | Password hashing | werkzeug |

---

# Phụ lục

## A. Cấu trúc thư mục chi tiết

```
linux-admin-desktop/
├── main.py                    # Entry point (36 dòng)
├── requirements.txt           # PyQt6, SQLAlchemy, Werkzeug, pytz
├── .env.example               # Biến môi trường mẫu
├── linux-admin-desktop.spec   # PyInstaller spec
│
├── app/                       # Business logic (5 files, 260 dòng)
│   ├── __init__.py
│   ├── auth.py                # Xác thực (45 dòng)
│   ├── database.py            # ORM models (74 dòng)
│   ├── executor.py            # Script executor (38 dòng)
│   ├── logging.py             # Audit logger (32 dòng)
│   ├── parsers.py             # Output parsers (103 dòng)
│   └── rbac.py                # RBAC helpers (9 dòng)
│
├── ui/                        # GUI (7 files, ~1300 dòng)
│   ├── __init__.py
│   ├── login_window.py        # Login dialog (116 dòng)
│   ├── main_window.py         # Main window (171 dòng)
│   ├── file_manager_widget.py # File manager (330 dòng)
│   ├── system_time_widget.py  # System time (179 dòng)
│   ├── package_manager_widget.py # Package manager (214 dòng)
│   ├── task_scheduler_widget.py  # Cron jobs (221 dòng)
│   └── logs_viewer_widget.py  # Audit log viewer (98 dòng)
│
├── scripts/                   # Shell scripts (26 files)
│   ├── file_*.sh              # 10 scripts
│   ├── *time.sh               # 6 scripts
│   ├── *package*.sh           # 5 scripts
│   └── *cron*.sh / run_job.sh # 5 scripts
│
├── instance/
│   └── dashboard.db           # SQLite DB (tạo khi chạy)
├── logs/
│   └── system.log             # Audit log file
├── build/                     # PyInstaller build
└── dist/                      # PyInstaller output
    └── linux-admin-desktop    # Standalone binary
```

## B. Cài đặt PyInstaller (đóng gói)

```bash
pip install pyinstaller
pyinstaller linux-admin-desktop.spec

# Binary tại: dist/linux-admin-desktop
./dist/linux-admin-desktop
```

## C. So sánh hai dự án

| Tiêu chí | ubuntu-monitor-desktop | linux-admin-desktop |
|---|---|---|
| **Mục đích** | Học kernel Linux | Quản trị hệ thống |
| **Backend** | /proc filesystem + ctypes system calls | Shell scripts (bash) |
| **Xác thực** | Không | Có (admin/user) |
| **Phân quyền** | Không | Có (RBAC) |
| **Audit log** | Cơ bản (file only) | DB + File |
| **GUI** | Dark theme, tabs | Gradient + sidebar |
| **Kernel concepts** | task_struct, sock, inode, VFS | systemd, RBAC, cron, permissions |

## D. License

MIT License

---

*Tài liệu này được viết cho dự án Linux Administration Desktop.*
*phiên bản: 1.0 — tháng 6/2026*

---

*Hết tài liệu.*
