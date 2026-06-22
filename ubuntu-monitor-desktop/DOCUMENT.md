# Tài liệu Dự án Ubuntu Monitor Desktop

## Linux Kernel Learning Tool

---

# Mục lục

1. [Tổng quan dự án](#1-tổng-quan-dự-án)
2. [Phân tích yêu cầu](#2-phân-tích-yêu-cầu)
3. [Thiết kế kiến trúc hệ thống](#3-thiết-kế-kiến-trúc-hệ-thống)
4. [Use Case](#4-use-case)
5. [Chức năng chi tiết](#5-chức-năng-chi-tiết)
6. [Cơ sở lý thuyết hệ thống](#6-cơ-sở-lý-thuyết-hệ-thống)
7. [Hướng dẫn cài đặt và sử dụng](#7-hướng-dẫn-cài-đặt-và-sử-dụng)
8. [Minh họa luồng xử lý dữ liệu](#8-minh-họa-luồng-xử-lý-dữ-liệu)
9. [Kết luận và hướng phát triển](#9-kết-luận-và-hướng-phát-triển)

---

# 1. Tổng quan dự án

## 1.1. Giới thiệu

**Ubuntu Monitor Desktop** là một ứng dụng giám sát hệ thống Linux được xây dựng với mục đích **học tập kiến trúc nhân Linux** (Linux kernel). Ứng dụng cung cấp giao diện đồ họa (GUI) để người dùng có thể trực quan quan sát cách kernel Linux quản lý tiến trình, bộ nhớ, file system, socket mạng và network interfaces.

Điểm đặc biệt: thay vì sử dụng các lệnh shell như `ps`, `top`, `ss`, `netstat`, `ip`, ứng dụng **đọc trực tiếp từ /proc filesystem** — cơ chế giao tiếp giữa kernel và userspace — và sử dụng **system calls** qua thư viện `ctypes`.

## 1.2. Mục tiêu

| Mục tiêu | Mô tả |
|---|---|
| **Học tập kernel** | Minh họa các khái niệm kernel như task_struct, sock, inode, VFS, procfs, sysfs |
| **Tương tác trực tiếp** | Đọc /proc filesystem thay vì dùng shell commands |
| **Real-time monitoring** | Cập nhật dữ liệu tự động mỗi 2-3 giây |
| **Giao diện trực quan** | Dark theme, bảng biểu, tree view, terminal-style output |
| **Không phụ thuộc web** | Loại bỏ hoàn toàn Flask, werkzeug, web dependencies |

## 1.3. Công nghệ sử dụng

| Công nghệ | Vai trò |
|---|---|
| **Python 3.12** | Ngôn ngữ lập trình chính |
| **PyQt6** | Thư viện GUI (cross-platform desktop application) |
| **SQLAlchemy 2.x** | ORM cho SQLite audit log |
| **ctypes** | Gọi trực tiếp libc system calls |
| **/proc filesystem** | Nguồn dữ liệu chính từ kernel |
| **/sys filesystem** | Thông tin network device |

---

# 2. Phân tích yêu cầu

## 2.1. Yêu cầu chức năng

| ID | Yêu cầu | Mô tả |
|---|---|---|
| F01 | Process Monitor | Hiển thị danh sách tiến trình với PID, tên, trạng thái, CPU%, Memory% |
| F02 | Process Detail | Xem chi tiết tiến trình: memory maps, environment, context switches |
| F03 | Kill Process | Gửi tín hiệu SIGKILL đến tiến trình qua kill(2) system call |
| F04 | Process Filter | Lọc tiến trình theo tên hoặc PID |
| F05 | System Summary | Thống kê tổng số process, running, sleeping, zombie, CPU, memory |
| F06 | File Browser | Duyệt cây thư mục với thông tin stat(2) chi tiết |
| F07 | File Preview | Xem nội dung file text |
| F08 | Socket Monitor | Liệt kê TCP/UDP/Unix sockets từ /proc/net/ |
| F09 | Network Stats | Thống kê RX/TX bytes, packets, errors, drops từng interface |
| F10 | Traffic Speed | Tính tốc độ mạng real-time (RX/TX speed) |
| F11 | Routing Table | Bảng định tuyến từ /proc/net/route |
| F12 | Ping | Gửi ICMP echo request |
| F13 | Audit Log | Ghi lại thao tác người dùng (kill process, ping) |
| F14 | Real-time Refresh | Tự động cập nhật dữ liệu mỗi 2-3 giây |
| F15 | Dark Theme | Giao diện tối với accent xanh dương |
| F16 | Socket Chat | Tạo TCP server/client để chat real-time qua QTcpServer/QTcpSocket |

## 2.2. Yêu cầu phi chức năng

| ID | Yêu cầu | Mô tả |
|---|---|---|
| NF01 | Hiệu năng | Không gây blocking UI khi đọc /proc (dùng QTimer) |
| NF02 | Bảo mật | Không chạy với root; tôn trọng quyền truy cập file |
| NF03 | Maintainability | Code có comment giải thích kernel concepts |
| NF04 | Portability | Chạy trên mọi bản phân phối Linux có /proc |

---

# 3. Thiết kế kiến trúc hệ thống

## 3.1. Kiến trúc tổng thể (Layered Architecture)

```
┌──────────────────────────────────────────────────────────┐
│                     UI Layer (PyQt6)                      │
│  ┌─────────────┬──────────┬────────────────┬──────────────┐  │
│  │ ProcessTab  │ FileTab  │   SocketTab    │ NetworkTab   │  │
│  │             │          │  ┌──────────┐  │              │  │
│  │ - QTable    │ - QTree  │  │ Monitor  │  │ - QTabWidget │  │
│  │ - QTimer    │ - Split  │  │ (procfs) │  │ - Interface  │  │
│  │ - Summary   │ - Pre-   │  ├──────────┤  │ - Route      │  │
│  │   Cards     │   view   │  │ Chat     │  │ - Ping Tab   │  │
│  │             │          │  │(TCP srv/ │  │              │  │
│  │             │          │  │ client)  │  │              │  │
│  │             │          │  └──────────┘  │              │  │
│  └──────┬──────┴─────┬────┴───────┬────────┴──────┬───────┘  │
│         │            │          │             │          │
│         ▼            ▼          ▼             ▼          │
│  ┌──────────────────────────────────────────────────┐    │
│  │               App Module Layer                    │    │
│  │  ┌──────────────┐   ┌──────────────┐             │    │
│  │  │process_      │   │file_monitor  │             │    │
│  │  │monitor.py    │   │.py           │             │    │
│  │  └──────┬───────┘   └──────┬───────┘             │    │
│  │  ┌──────┴───────┐   ┌──────┴───────┐             │    │
│  │  │socket_       │   │network_     │             │    │
│  │  │monitor.py    │   │monitor.py   │             │    │
│  │  └──────┬───────┘   └──────┬───────┘             │    │
│  │         │                  │                      │    │
│  │         └──────┬───────────┘                      │    │
│  │                ▼                                  │    │
│  │  ┌────────────────────────┐  ┌──────────────┐    │    │
│  │  │    kernel_utils.py     │  │  database.py │    │    │
│  │  │  (ctypes + procfs I/O) │  │  (SQLite)    │    │    │
│  │  └───────────┬────────────┘  └──────────────┘    │    │
│  └──────────────┼───────────────────────────────────┘    │
│                 ▼                                        │
│  ┌──────────────────────────────────────────────────┐    │
│  │            Linux Kernel (/proc, /sys)             │    │
│  │  ┌─────────┬──────────┬─────────┬────────────┐   │    │
│  │  │ /proc/  │ /proc/   │ /proc/  │ /sys/class │   │    │
│  │  │ [PID]/  │ /net/    │ /stat,  │ /net/      │   │    │
│  │  │         │          │ /meminfo│            │   │    │
│  │  └─────────┴──────────┴─────────┴────────────┘   │    │
│  └──────────────────────────────────────────────────┘    │
└──────────────────────────────────────────────────────────┘
```

## 3.2. Sơ đồ package

```
ubuntu-monitor-desktop/
├── main.py                  # Entry point
├── requirements.txt         # Dependencies
├── app/
│   ├── __init__.py
│   ├── kernel_utils.py      # System calls + /proc parsers
│   ├── process_monitor.py   # Process data collection
│   ├── file_monitor.py      # File system operations
│   ├── socket_monitor.py    # Socket listing
│   ├── network_monitor.py   # Network monitoring
│   └── database.py          # SQLite audit log
├── ui/
│   ├── __init__.py
│   ├── styles.py            # Colors + Qt stylesheets
│   ├── main_window.py       # QMainWindow (tabs, menu, status)
│   ├── process_tab.py       # Process tab widget
│   ├── file_tab.py          # File browser tab
│   ├── socket_tab.py        # Socket monitor tab (Monitor + Chat sub-tabs)
│   ├── chat_tab.py          # TCP server/client chat widget
│   └── network_tab.py       # Network monitor tab
├── logs/
│   └── audit.log            # Audit trail
└── instance/
    └── monitor.db           # SQLite database
```

## 3.3. Nguyên tắc thiết kế

1. **Separation of Concerns** — Tách biệt rõ ràng giữa:
   - `app/` — business logic đọc dữ liệu từ kernel
   - `ui/` — giao diện người dùng (PyQt6)
   - `kernel_utils.py` — I/O với kernel (duy nhất module này giao tiếp với /proc)

2. **No Shell Commands** — Tuyệt đối không dùng `subprocess` để gọi `ps`, `top`, `ss`, `netstat`. Ngoại lệ duy nhất: `ping` (vì raw socket yêu cầu CAP_NET_RAW).

3. **Real-time by Design** — Dùng `QTimer` để polling /proc định kỳ, không dùng thread (tránh race condition với Qt).

4. **Educational Comments** — Mỗi hàm có comment tiếng Việt giải thích kernel concept tương ứng (cấu trúc dữ liệu, system call, file trong kernel source).

---

# 4. Use Case

## 4.1. Actor

- **Người dùng (User)**: Người học Linux kernel, quản trị viên hệ thống.

## 4.2. Sơ đồ Use Case

```
                    ┌──────────────────────────────┐
                    │     Ubuntu Monitor Desktop    │
                    │                               │
    ┌───────────────┤    ┌─────────────────────┐   ├───────────────┐
    │               │    │   Monitor Process    │   │               │
    │               │    │  ┌───────────────┐   │   │               │
    │               │    │  │ View Processes │   │   │               │
    │               │    │  ├───────────────┤   │   │               │
    │               │    │  │ Filter Process │   │   │               │
    │               │    │  ├───────────────┤   │   │               │
    │               │    │  │ Kill Process   │   │   │               │
    │               │    │  ├───────────────┤   │   │               │
    │               │    │  │ View Detail    │   │   │               │
    │               │    │  └───────────────┘   │   │               │
    │               │    └─────────────────────┘   │               │
    │               │                               │               │
    │   ┌───────────┤    ┌─────────────────────┐   ├───────────┐   │
    │   │   User    │    │   Browse Files       │   │           │   │
    │   │           │    │  ┌───────────────┐   │   │           │   │
    │   │           ├────┤  │ Navigate Dir  │   ├───┤           │   │
    │   │           │    │  ├───────────────┤   │   │           │   │
    │   │           │    │  │ Open File      │   │   │           │   │
    │   │           │    │  ├───────────────┤   │   │           │   │
    │   │           │    │  │ Preview File   │   │   │           │   │
    │   │           │    │  └───────────────┘   │   │           │   │
    │   └───────────┤    └─────────────────────┘   ├───────────┘   │
    │               │                               │               │
    │               │    ┌─────────────────────┐   │               │
    │               │    │   Monitor Sockets    │   │               │
    │               │    │  ┌───────────────┐   │   │               │
    │               │    │  │ View Sockets  │   │   │               │
    │               │    │  ├───────────────┤   │   │               │
    │               │    │  │ Filter by     │   │   │               │
    │               │    │  │ Protocol      │   │   │               │
    │               │    │  ├───────────────┤   │   │               │
    │               │    │  │ Chat (TCP    │   │   │               │
    │               │    │  │ Server/      │   │   │               │
    │               │    │  │ Client)      │   │   │               │
    │               │    │  └───────────────┘   │   │               │
    │               │    └─────────────────────┘   │               │
    │               │                               │               │
    │               │    ┌─────────────────────┐   │               │
    │               │    │   Monitor Network    │   │               │
    │               │    │  ┌───────────────┐   │   │               │
    │               │    │  │ View Ifaces   │   │   │               │
    │               │    │  ├───────────────┤   │   │               │
    │               │    │  │ View Routes   │   │   │               │
    │               │    │  ├───────────────┤   │   │               │
    │               │    │  │ Ping Host     │   │   │               │
    │               │    │  └───────────────┘   │   │               │
    │               │    └─────────────────────┘   │               │
    └───────────────┘                               └───────────────┘
```

## 4.3. Use Case chi tiết

### UC01: Monitor Processes

| Mục | Mô tả |
|---|---|
| **Mô tả** | Người dùng xem danh sách tiến trình hệ thống với thông tin chi tiết |
| **Precondition** | Ứng dụng đã khởi động, tab Process đang active |
| **Postcondition** | Dữ liệu process được hiển thị và tự động refresh mỗi 2 giây |
| **Luồng chính** | 1. Tab Process được chọn<br>2. QTimer 2s gọi `get_all_processes()`<br>3. Dữ liệu hiển thị lên QTableWidget<br>4. Summary cards update |

### UC02: Kill Process

| Mục | Mô tả |
|---|---|
| **Mô tả** | Người dùng kết thúc một tiến trình bằng SIGKILL |
| **Luồng chính** | 1. User chọn process trong table<br>2. Click "Kill Process"<br>3. Hộp thoại xác nhận hiện ra<br>4. User xác nhận → `os.kill(pid, SIGKILL)` được gọi<br>5. Audit log được ghi lại |

### UC03: Browse File System

| Mục | Mô tả |
|---|---|
| **Mô tả** | Người dùng duyệt cây thư mục và xem thông tin file |
| **Luồng chính** | 1. Tab File được chọn<br>2. Cây thư mục hiển thị ở panel trái<br>3. Double-click directory → load nội dung<br>4. Double-click file → hiển thị stat detail + preview |

### UC04: Socket Chat

| Mục | Mô tả |
|---|---|
| **Mô tả** | Người dùng tạo TCP server và client kết nối đến để chat real-time |
| **Precondition** | Ứng dụng đã khởi động, tab Socket → sub-tab Chat đang active |
| **Postcondition** | Hai tiến trình có thể gửi/nhận tin nhắn text qua TCP |
| **Luồng chính (Server)** | 1. Chọn mode "Server"<br>2. Nhập port (mặc định 8888)<br>3. Click "Start Server" → `QTcpServer.listen()`<br>4. Server lắng nghe kết nối đến<br>5. Client kết nối → `newConnection` signal → `nextPendingConnection()`<br>6. Gửi tin nhắn → `write()` → client nhận qua `readyRead` |
| **Luồng chính (Client)** | 1. Chọn mode "Client"<br>2. Nhập host và port<br>3. Click "Connect" → `QTcpSocket.connectToHost()`<br>4. Kết nối thành công → `connected` signal<br>5. Gửi tin nhắn → `write()` → server broadcast đến các client khác |

### UC05: Ping Host

| Mục | Mô tả |
|---|---|
| **Mô tả** | Người dùng gửi ICMP echo request đến host |
| **Luồng chính** | 1. Tab Network → sub-tab Ping<br>2. Nhập hostname/IP<br>3. Click Ping → output hiển thị dạng terminal |

---

# 5. Chức năng chi tiết

## 5.1. Process Monitor (`app/process_monitor.py` + `ui/process_tab.py`)

### 5.1.1. Thu thập dữ liệu

Hàm `get_all_processes()`:
1. Quét `/proc/` lấy tất cả PID (directory có tên là số)
2. Với mỗi PID, đọc:
   - `/proc/[PID]/stat` → parse bằng `parse_proc_stat_to_dict()`
   - `/proc/[PID]/status` → parse bằng `parse_proc_status()`
   - `/proc/[PID]/cmdline` → dòng lệnh
   - `/proc/[PID]/exe` → symlink đến executable
3. Tính %CPU: `cpu_time / total_cpu_jiffies * 100`
4. Tính %Memory: `rss_bytes / mem_total * 100`

### 5.1.2. Hiển thị

| Cột | Nguồn dữ liệu | Ý nghĩa |
|---|---|---|
| PID | `/proc/[PID]/stat` | Process ID |
| Name | `/proc/[PID]/status` | Tên tiến trình |
| State | `/proc/[PID]/stat` | R=Running, S=Sleeping, D=Waiting, Z=Zombie |
| CPU% | Tính từ utime+stime | Phần trăm CPU sử dụng |
| Memory | RSS/pages*4096 | Phần trăm RAM |
| RSS | stat.rss * 4096 | Resident Set Size (bytes) |
| Threads | stat.num_threads | Số luồng |
| User | uid → /etc/passwd | Người dùng sở hữu |
| Priority | stat.priority | Độ ưu tiên scheduling |
| Nice | stat.nice | Nice value |
| Command | /proc/[PID]/cmdline | Dòng lệnh khởi động |

### 5.1.3. Summary Cards

6 card hiển thị: Total Processes, Running, Sleeping, Zombie, CPU Usage, Memory Usage.

## 5.2. File Browser (`app/file_monitor.py` + `ui/file_tab.py`)

### 5.2.1. Directory Listing

Hàm `list_directory(path)`:
- Sử dụng `os.listdir()` (wrapper cho `getdents(2)`)
- Mỗi entry gọi `os.stat()` (wrapper cho `stat(2)`)
- Parse `struct stat` → lấy inode, permissions, owner, size, mtime
- Phân loại file: directory, file, symlink, fifo, socket, block, char

### 5.2.2. File Preview

- Kiểm tra text file bằng heuristic (không có null byte)
- Đọc nội dung với giới hạn 100KB
- Hiển thị trong terminal-style text edit

## 5.3. Socket Monitor & Chat (`app/socket_monitor.py` + `ui/socket_tab.py` + `ui/chat_tab.py`)

Socket tab gồm 2 sub-tab: **Monitor** và **Chat**.

### 5.3.1. Monitor Sub-tab

Đọc trực tiếp từ `/proc/net/`:
- `/proc/net/tcp` → `parse_proc_net_tcp()` — danh sách TCP sockets
- `/proc/net/udp` → `parse_proc_net_udp()` — danh sách UDP sockets
- `/proc/net/unix` → `parse_proc_net_unix()` — Unix domain sockets

Mỗi socket entry chứa: local address, remote address, state, UID, inode, tx/rx queue.

### 5.3.2. Chat Sub-tab (`ui/chat_tab.py`)

Cho phép tạo TCP server và client kết nối đến để chat real-time, sử dụng **PyQt6 QtNetwork**:

| Thành phần | Công nghệ | Mô tả |
|---|---|---|
| **Server** | `QTcpServer` | Lắng nghe kết nối trên port, accept client mới qua signal `newConnection` |
| **Client** | `QTcpSocket` | Kết nối đến server qua host:port, gửi/nhận dữ liệu |
| **Event-driven** | Signal/Slot | `readyRead`, `connected`, `disconnected`, `errorOccurred` — không cần thread |

**Cơ chế hoạt động:**

```
Server Mode:
  QTcpServer.listen(port)
        │
        ▼
  newConnection signal → nextPendingConnection()
        │
        ▼
  Thêm socket vào client_connections dict
        │
        ├─ readyRead → _on_client_data() → hiển thị + broadcast
        └─ disconnected → _on_client_disconnected() → xóa khỏi danh sách

Client Mode:
  QTcpSocket.connectToHost(host, port)
        │
        ▼
  connected signal → cập nhật UI
        │
        ├─ readyRead → _on_server_data() → hiển thị tin nhắn
        └─ disconnected → _on_disconnected() → cập nhật UI

Gửi tin nhắn:
  socket.write(QByteArray) → kernel xử lý → gửi qua TCP stack → bên kia nhận
```

**Nguyên lý TCP kernel liên quan:**
- `QTcpServer.listen()` → kernel tạo socket ở trạng thái `TCP_LISTEN` (backlog trong `listen(2)` syscall)
- `QTcpSocket.connectToHost()` → kernel thực hiện 3-way handshake (SYN → SYN-ACK → ACK)
- `write()` → dữ liệu đi qua TCP stack: `tcp_sendmsg()` → chia segment → gửi qua network layer
- `readyRead` → kernel đã nhận dữ liệu và đặt vào `sk_receive_queue` (struct sock), userspace có thể đọc

### 5.3.3. Cách Python tương tác với socket trong kernel

Chương trình sử dụng **2 cơ chế** để tương tác với socket kernel:

#### Cơ chế 1: Đọc /proc/net/ (Socket Monitor — thụ động)

Python đọc file text do kernel tạo động — không tạo socket thật:

```
Python (userspace)                         Kernel
──────────────────────────────────────────────────────────
open("/proc/net/tcp")           → sys_open() → proc_reg_open()
                                     → tcp4_seq_show() được đăng ký
                                       làm callback cho seq_file
                                 
read(fd, buf, 4096)             → sys_read() → seq_read()
                                     → tcp4_seq_show() duyệt
                                       tcp_hashinfo (bảng hash
                                       chứa mọi struct sock đang mở)
                                     → format output thành dòng text
                                 
parse dòng text trả về:
  "  0: 0100007F:0035 ..."
  → _decode_ip_port("0100007F:0035")
      → bytes.fromhex("0100007F")
      → reversed → [127,0,0,1]
      → int("0035", 16) → 53
      → "127.0.0.1:53"
  → _tcp_state_name(0x0A)
      → states[10] = "LISTEN"
```

**File trong kernel source:**
- `/proc/net/tcp` → `net/ipv4/tcp_ipv4.c:tcp4_seq_show()` — đọc `struct sock` từ `tcp_hashinfo`
- `/proc/net/udp` → `net/ipv4/udp.c:udp4_seq_show()`
- `/proc/net/unix` → `net/unix/af_unix.c:unix_seq_show()`

Khi đọc `/proc/net/tcp`, kernel:
1. Duyệt bảng hash `tcp_hashinfo` (chứa tất cả TCP sockets đang mở)
2. Với mỗi `struct sock`, đọc: `sk_rcv_saddr` (IP nguồn), `sk_daddr` (IP đích), `sk_num` (port nguồn), `sk_dport` (port đích), `sk_state` (trạng thái TCP), `sk_uid` (người dùng), `sk_inode` (inode number)
3. Format các giá trị hex → ghi vào bộ đệm `seq_file`
4. `copy_to_user()` đưa dữ liệu từ kernel space → userspace

#### Cơ chế 2: QTcpServer/QTcpSocket (Socket Chat — chủ động)

Python tạo socket thật qua PyQt6 → Qt C++ → POSIX socket API → kernel:

```
Python layer              PyQt6 C++ layer          Kernel
──────────────────────────────────────────────────────────────
QTcpServer.listen(8888)
  ↓                         ↓
                     QTcpServer::listen()
                       ↓                       sys_socket(AF_INET,
                       socket(AF_INET,           SOCK_STREAM, 0)
                       SOCK_STREAM, 0)            → socket(BPF)
                                                   → struct socket
                                                   → struct sock
                       ↓                       sys_bind(3, sa, 16)
                       bind(3, port=8888)         → sock->sk_num = 8888
                                                   → TCP_CLOSE
                       ↓                       sys_listen(3, 50)
                       listen(3, 50)              → sock->sk_state
                                                   = TCP_LISTEN
                       ↓
                thêm vào event loop (poll/epoll)
                
QTcpSocket.connectToHost
  ("127.0.0.1", 8888)
                       ↓
                 connectToHost()
                       ↓                       sys_connect(3, sa, 16)
                       connect(3)                 → 3-way handshake:
                                                    SYN → SYN-ACK → ACK
                                                  → sock->sk_state
                                                    = TCP_ESTABLISHED
                       ↓
                poll() thông báo connected
                  → emit connected()

socket.write("Hello")
                       ↓
                 write(3, "Hello", 5)         sys_sendmsg()
                                                  → tcp_sendmsg()
                                                  → chia segment (MSS)
                                                  → sndbuf → tcp_transmit_skb()
                                                  → IP → NIC

readyRead signal ← emit readyRead()
                       ↑
                 poll() báo có dữ liệu
                       ↑
                 dữ liệu đến             TCP segment từ NIC
                                          → IRQ → tcp_v4_rcv()
                                          → tcp_data_queue()
                                          → đặt vào sk_receive_queue
                                          → wake up process (poll)
```

**Tóm lại:**

| Cơ chế | Kernel interaction | Mục đích | Đường đi |
|---|---|---|---|
| **Đọc /proc/net/** | Đọc file procfs | Quan sát socket thụ động | Python → open/read → VFS → procfs → tcp4_seq_show → tcp_hashinfo |
| **QTcpServer/Socket** | System call thật | Tạo socket thật để chat | Python → PyQt6 → Qt C++ → socket/bind/listen/connect/sendmsg → kernel TCP stack |

## 5.4. Network Monitor (`app/network_monitor.py` + `ui/network_tab.py`)

### 5.4.1. Interface Statistics

Đọc `/proc/net/dev` → thống kê cho từng interface:
- RX: bytes, packets, errors, drop
- TX: bytes, packets, errors, drop

### 5.4.2. Traffic Speed

So sánh 2 snapshot `/proc/net/dev` qua interval 3 giây:
- `speed = (bytes_after - bytes_before) / interval`
- Định dạng: bps, Kbps, Mbps

### 5.4.3. Routing Table

Đọc `/proc/net/route` → danh sách route entry:
- Interface, Destination, Gateway, Mask, Flags, Metric

## 5.5. Database / Audit Log (`app/database.py`)

- SQLite database (`instance/monitor.db`)
- File log (`logs/audit.log`)
- Ghi lại hành động: kill process, ping (có timestamp, module, detail)
- Hiện tại DB logging bị comment, chỉ file logging hoạt động

---

# 6. Cơ sở lý thuyết hệ thống

## 6.1. Proc Filesystem (procfs)

### 6.1.1. Giới thiệu

`/proc` là một pseudo-filesystem được kernel Linux tạo ra khi khởi động. Nó không lưu trữ dữ liệu trên disk — thay vào đó, kernel **sinh động** nội dung các file khi userspace đọc chúng. Mỗi file trong `/proc` tương ứng với một hàm trong kernel source.

### 6.1.2. Các file quan trọng

| File | Kernel Source | Nội dung |
|---|---|---|
| `/proc/[PID]/stat` | `fs/proc/array.c:do_task_stat()` | Thông tin scheduling, memory |
| `/proc/[PID]/status` | `fs/proc/array.c:proc_pid_status()` | Trạng thái, UID, GID, VmRSS |
| `/proc/[PID]/cmdline` | `fs/proc/base.c:proc_pid_cmdline()` | Dòng lệnh |
| `/proc/[PID]/fd/` | `fs/proc/fd.c` | File descriptors |
| `/proc/[PID]/environ` | `fs/proc/base.c:proc_pid_environ()` | Biến môi trường |
| `/proc/stat` | `fs/proc/stat.c` | Thống kê CPU |
| `/proc/meminfo` | `fs/proc/meminfo.c` | Thông tin bộ nhớ |
| `/proc/net/tcp` | `net/ipv4/tcp_ipv4.c:tcp4_seq_show()` | TCP socket table |
| `/proc/net/udp` | `net/ipv4/udp.c:udp4_seq_show()` | UDP socket table |
| `/proc/net/unix` | `net/unix/af_unix.c:unix_seq_show()` | Unix socket table |
| `/proc/net/dev` | `net/core/net-procfs.c:dev_seq_printf_stats()` | Interface stats |
| `/proc/net/route` | `net/ipv4/fib_trie.c:fib_trie_seq_show()` | Routing table |

### 6.1.3. Cơ chế hoạt động

Khi userspace gọi `read()` trên file `/proc/[PID]/stat`:

```
Userspace                          Kernel
───────────────────────────────────────────
1. open("/proc/pid/stat")
                       → sys_open()
                       → proc_reg_open()
                       → single_open(proc_pid_stat)

2. read(fd, buf, size)
                       → sys_read()
                       → proc_reg_read()
                       → seq_read()
                       → proc_pid_stat(seq_file)
                            ↓
                      Đọc task_struct của process
                      Format output → buffer

3. copy_to_user(buf, kernel_buf, len)
                       → Dữ liệu được copy từ
                         kernel space → user space
```

## 6.2. System Calls

### 6.2.1. kill(2) — Gửi tín hiệu đến process

```python
# Trong kernel_utils.py: sử dụng ctypes để gọi libc.kill()
_libc.kill(ctypes.c_int(pid), ctypes.c_int(sig))
```

Luồng xử lý trong kernel:
1. `kill()` → `sys_kill()` → `kill_something_info()`
2. Tìm `task_struct` theo PID (qua bảng hash `pid_hash[]`)
3. Kiểm tra quyền: `capable(CAP_KILL)` hoặc UID match
4. Gửi signal: `send_signal()` → thêm vào pending signal queue
5. Nếu process đang sleeping, đánh thức bằng `signal_wake_up()`

### 6.2.2. stat(2) — Lấy thông tin file

Khi gọi `os.stat(path)` (wrapper cho `stat(2)`):
1. Kernel thực hiện `path_resolution()` — duyệt từng component trong path
2. Tại mỗi bước, tìm dentry trong dcache hoặc đọc từ disk
3. Lấy inode từ dentry
4. Đọc struct inode → trả về struct stat (st_mode, st_ino, st_size, st_uid, st_gid, ...)

### 6.2.3. open(2) + read(2) — Đọc file

```python
with open(path, "r") as f:
    return f.read()
```

Trong kernel:
1. `open()` → `do_sys_open()` → `do_filp_open()` → `path_openat()`
2. `path_openat()` gọi `lookup_open()` → tìm/ tạo dentry + inode
3. Thực thi `inode->i_fop->open()` (tùy filesystem)
4. `read()` → `vfs_read()` → `file->f_op->read()` → `do_sync_read()`
5. Đọc từ page cache; nếu cache miss → đọc từ disk (block I/O)

## 6.3. Cấu trúc dữ liệu kernel quan trọng

### 6.3.1. struct task_struct (`include/linux/sched.h`)

Mỗi process trong kernel được quản lý bởi `struct task_struct`:

```c
struct task_struct {
    pid_t                   pid;            // Process ID
    pid_t                   tgid;           // Thread Group ID
    struct task_struct      *parent;        // Parent process
    char                    comm[TASK_COMM_LEN]; // Tên process (16 bytes)
    unsigned int            state;          // Trạng thái
    int                     prio;           // Độ ưu tiên động
    int                     static_prio;    // Độ ưu tiên tĩnh
    int                     normal_prio;    // Độ ưu tiên thường
    unsigned int            rt_priority;    // Thời gian thực priority
    struct list_head        tasks;          // Linked list các process
    struct mm_struct        *mm;            // Bộ nhớ ảo
    struct fs_struct        *fs;            // Filesystem thông tin
    struct files_struct     *files;         // File descriptors
    struct signal_struct    *signal;        // Signal handlers
    struct sighand_struct   *sighand;       // Signal handlers
    unsigned long           utime;          // User mode time (jiffies)
    unsigned long           stime;          // Kernel mode time (jiffies)
    long                    nice;           // Nice value
    // ... (hàng trăm field)
};
```

### 6.3.2. struct sock (`include/net/sock.h`)

Mỗi socket trong kernel được quản lý bởi `struct sock`:

```c
struct sock {
    struct sk_buff_head     sk_receive_queue;   // Receive buffer
    struct sk_buff_head     sk_write_queue;     // Send buffer
    __u32                   sk_daddr;           // Destination IPv4
    __u32                   sk_rcv_saddr;       // Source IPv4
    __u16                   sk_dport;           // Destination port (network order)
    __u16                   sk_num;             // Source port (network order)
    int                     sk_rcvbuf;          // Receive buffer size
    int                     sk_sndbuf;          // Send buffer size
    unsigned short          sk_type;            // SOCK_STREAM, SOCK_DGRAM, ...
    unsigned char           sk_state;           // TCP state
    int                     sk_uid;             // Owner UID
    // ...
};
```

### 6.3.3. struct inode (`include/linux/fs.h`)

Mỗi file/directory có một inode trong kernel:

```c
struct inode {
    umode_t                 i_mode;     // File type + permissions
    kuid_t                  i_uid;      // Owner UID
    kgid_t                  i_gid;      // Owner GID
    loff_t                  i_size;     // File size
    unsigned long           i_ino;      // Inode number
    struct timespec64       i_atime;    // Last access time
    struct timespec64       i_mtime;    // Last modify time
    struct timespec64       i_ctime;    // Last change time
    nlink_t                 i_nlink;    // Number of hard links
    struct super_block      *i_sb;      // Superblock (filesystem metadata)
    const struct inode_operations *i_op; // Inode operations
    // ...
};
```

### 6.3.4. struct net_device (`include/linux/netdevice.h`)

Mỗi network interface:

```c
struct net_device {
    char                    name[IFNAMSIZ]; // Tên interface (eth0, wlan0, ...)
    unsigned int            mtu;            // Maximum Transmission Unit
    unsigned char           *dev_addr;      // MAC address
    unsigned short          type;           // ARP protocol type
    struct net_device_stats stats;          // RX/TX statistics
    const struct net_device_ops *netdev_ops; // Device operations
    // ...
};
```

## 6.4. TCP State Machine

Các trạng thái TCP trong kernel (`include/net/tcp_states.h`):

```c
enum {
    TCP_ESTABLISHED = 1,
    TCP_SYN_SENT,       // 2
    TCP_SYN_RECV,       // 3
    TCP_FIN_WAIT1,      // 4
    TCP_FIN_WAIT2,      // 5
    TCP_TIME_WAIT,      // 6
    TCP_CLOSE,          // 7
    TCP_CLOSE_WAIT,     // 8
    TCP_LAST_ACK,       // 9
    TCP_LISTEN,         // 10
    TCP_CLOSING,        // 11
};
```

## 6.5. Virtual File System (VFS)

VFS là lớp trừu tượng cho phép Linux hỗ trợ nhiều filesystem khác nhau (ext4, xfs, tmpfs, procfs) thông qua cùng một giao diện:

```
                    ┌──────────────┐
                    │  System Call  │
                    │  Interface   │
                    └──────┬───────┘
                           │
                    ┌──────▼───────┐
                    │     VFS      │
                    │  (Virtual    │
                    │  File System)│
                    └──┬───┬───┬──┘
                       │   │   │
              ┌────────┘   │   └────────┐
              ▼            ▼            ▼
        ┌──────────┐ ┌──────────┐ ┌──────────┐
        │  procfs  │ │  ext4    │ │  sysfs   │
        │ (/proc)  │ │ (/home)  │ │ (/sys)   │
        └──────────┘ └──────────┘ └──────────┘
```

Mỗi filesystem implement các operations:
- `inode_operations`: create, lookup, link, unlink, mkdir, rmdir, rename
- `file_operations`: read, write, open, release, mmap, fsync

Procfs không có backing store trên disk — kernel tự tạo nội dung file qua các hàm callback.

## 6.6. Jiffies và Timer

Trong kernel, **jiffies** là đơn vị thời gian cơ bản. Kernel cập nhật counter jiffies mỗi timer interrupt (thường 250Hz = 4ms trên x86).

- `/proc/stat` chứa tổng số jiffies CPU đã sử dụng ở các chế độ: user, nice, system, idle
- Trong `/proc/[PID]/stat`, `utime` và `stime` là số jiffies process đã dùng
- %CPU = `(process_jiffies / total_jiffies) * 100`

## 6.7. Resident Set Size (RSS)

RSS (Resident Set Size) là số trang bộ nhớ vật lý mà một process đang sử dụng. Mỗi trang thường 4096 bytes. RSS khác với VSIZE (Virtual Memory Size) — VSIZE là tổng không gian địa chỉ ảo đã được ánh xạ.

Trong `/proc/[PID]/stat`, field `rss` là số trang vật lý. Công thức:
```
rss_bytes = rss_pages * PAGE_SIZE (thường 4096)
```

---

# 7. Hướng dẫn cài đặt và sử dụng

## 7.1. Yêu cầu hệ thống

- Hệ điều hành: Linux (Ubuntu khuyên dùng)
- Python 3.10+
- pip (Python package manager)
- Display server: X11 hoặc Wayland

## 7.2. Cài đặt

```bash
# Clone hoặc copy project
cd ubuntu-monitor-desktop

# Tạo virtual environment (khuyên dùng)
python3 -m venv .venv
source .venv/bin/activate

# Cài dependencies
pip install -r requirements.txt
```

## 7.3. Chạy ứng dụng

```bash
python3 main.py
```

Hoặc:

```bash
chmod +x main.py
./main.py
```

## 7.4. Hướng dẫn sử dụng

### Tab Process
- Quan sát danh sách process tự động cập nhật mỗi 2 giây
- Gõ vào ô "Filter by name or PID" để lọc
- Click row + "Kill Process" để kết thúc process (xác nhận trước)
- Double-click process → xem chi tiết ở panel dưới

### Tab File
- Nhập đường dẫn vào ô hoặc double-click directory trong tree
- Double-click file → xem stat detail + preview nội dung
- Click "Up" để lên thư mục cha

### Tab Socket

Socket tab có 2 sub-tab: **Monitor** và **Chat**.

**Monitor:**
- Xem danh sách TCP/UDP/Unix sockets đọc từ `/proc/net/`
- Chọn filter "All", "TCP", "UDP", hoặc "UNIX"
- Tự động refresh mỗi 3 giây

**Chat:**
- **Server mode**: Chọn "Server" → nhập port → "Start Server" → lắng nghe kết nối
- **Client mode**: Chọn "Client" → nhập host (VD: 127.0.0.1) và port → "Connect"
- Sau khi kết nối, gõ tin nhắn và Enter (hoặc click Send) để chat
- Server broadcast tin nhắn đến tất cả client đã kết nối
- Click "Stop" để dừng server / "Disconnect" để ngắt kết nối

### Tab Network
- **Interfaces**: xem RX/TX statistics + tốc độ real-time
- **Routing**: xem bảng định tuyến
- **Ping**: nhập hostname/IP, click Ping để kiểm tra kết nối

### Menu
- `File → Refresh All (Ctrl+R)`: refresh tất cả tab
- `File → Exit (Ctrl+Q)`: thoát
- `View → Process/File/Socket/Network Tab (Ctrl+1-4)`: chuyển tab chính
  - Trong Socket tab: chọn sub-tab Monitor hoặc Chat bằng chuột
- `Help → About`: thông tin ứng dụng

---

# 8. Minh họa luồng xử lý dữ liệu

## 8.1. Luồng Process Monitoring

```
QTimer (2 giây)
    │
    ▼
get_all_processes()
    │
    ├─ list_all_pids() → os.listdir("/proc")
    │
    └─ Với mỗi PID:
        │
        ├─ read_proc_file(f"/proc/{pid}/stat")
        │   → parse_proc_stat_to_dict()
        │
        ├─ read_proc_file(f"/proc/{pid}/status")
        │   → parse_proc_status()
        │
        ├─ read_proc_file(f"/proc/{pid}/cmdline")
        │   → xử lý null bytes
        │
        └─ os.readlink(f"/proc/{pid}/exe")
            → đường dẫn executable
    │
    ▼
Tính %CPU, %Memory
    │
    ▼
_processes = [dict, dict, ...]
    │
    ├─ _filter_processes()
    │   → Lọc theo tên/PID
    │
    ├─ _populate_table()
    │   → QTableWidget.setItem()
    │
    └─ _update_summary()
        → Cập nhật summary cards
```

## 8.2. Luồng Socket Monitoring

```
QTimer (3 giây)
    │
    ▼
_refresh_sockets()
    │
    ├─ get_tcp_sockets()
    │   → read_proc_file("/proc/net/tcp")
    │   → parse_proc_net_tcp()
    │
    ├─ get_udp_sockets()
    │   → read_proc_file("/proc/net/udp")
    │   → parse_proc_net_udp()
    │
    └─ get_unix_sockets()
        → read_proc_file("/proc/net/unix")
        → parse_proc_net_unix()
    │
    ▼
Hiển thị theo filter (All/TCP/UDP/UNIX)
    │
    ▼
Summary: TCP: X, UDP: Y, UNIX: Z, LISTEN: N, ESTABLISHED: M
```

## 8.3. Luồng Socket Chat

```
Server:
  [User] Click "Start Server"
     │
     ▼
  QTcpServer.listen(QHostAddress("0.0.0.0"), port)
     │
     ├─ Thành công: cập nhật status "Listening"
     │              server_status → success color
     │
     └─ Thất bại: log error + giữ nguyên UI
     │
     ▼
  [Client kết nối]
     │
     ▼
  QTcpServer.newConnection signal
     │
     ▼
  nextPendingConnection() → QTcpSocket mới
     │
     ├─ Thêm vào client_connections dict
     ├─ Thêm vào clients_list widget
     ├─ Kết nối readyRead signal → _on_client_data()
     └─ Kết nối disconnected signal → _on_client_disconnected()
     │
     ▼
  [Server gửi tin nhắn]
     │
     ▼
  _server_send() → broadcast đến tất cả client:
     for each sock in client_connections:
         sock.write(QByteArray("message"))

Client:
  [User] Click "Connect"
     │
     ▼
  QTcpSocket.connectToHost(host, port)
     │
     ├─ connected signal → cập nhật UI (Connected)
     ├─ errorOccurred signal → log error
     │
     ▼
  [Client gửi tin nhắn]
     │
     ▼
  _client_send() → client_socket.write(QByteArray("message"))
     │
     ▼
  [Server nhận]
     │
     ▼
  readyRead → _on_client_data() → readAll() → append chat display
```

## 8.4. Luồng Traffic Speed Calculation

```
lần 1: get_traffic_snapshot() → before = {iface: {rx_bytes, tx_bytes, ...}}
    │
    ▼
QTimer.sleep(3 giây)
    │
    ▼
lần 2: get_traffic_snapshot() → after = {iface: {rx_bytes, tx_bytes, ...}}
    │
    ▼
calculate_speed(before, after, interval=3.0)
    │
    └─ speed = (after.rx_bytes - before.rx_bytes) / 3.0
    │
    ▼
format_speed(bytes_per_sec) → bps / Kbps / Mbps
```

---

# 9. Kết luận và hướng phát triển

## 9.1. Kết luận

Ubuntu Monitor Desktop là một công cụ học tập Linux kernel thông qua thực hành. Ứng dụng đã đạt được các mục tiêu:

1. ✅ **Hiểu /proc filesystem**: đọc và parse trực tiếp các file /proc, hiểu cách kernel xuất dữ liệu
2. ✅ **System calls**: sử dụng ctypes để gọi libc, hiểu cơ chế chuyển từ userspace → kernel
3. ✅ **Kernel data structures**: minh họa task_struct, sock, inode, net_device
4. ✅ **Real-time monitoring**: QTimer-based polling, không blocking UI
5. ✅ **Không shell commands**: trừ ping (yêu cầu raw socket capability)
6. ✅ **Educational**: code comments giải thích chi tiết kernel concepts bằng tiếng Việt

## 9.2. Hướng phát triển tương lai

| Tính năng | Mô tả | Kernel concept liên quan |
|---|---|---|
| **inotify** | Thay polling bằng inotify(7) | Kernel event notification |
| **eBPF** | Dùng eBPF program để theo dõi system calls | eBPF verifier + maps |
| **cgroups** | Hiển thị control groups của process | cgroup v2 hierarchy |
| **Namespace** | Hiển thị Linux namespace (PID, net, mount) | clone(2) với CLONE_NEW* flags |
| **Kernel Modules** | Liệt kê kernel modules | `struct module` + /proc/modules |
| **io_uring** | Async I/O operations | io_uring system calls |
| **Perf Events** | Hardware performance counters | perf_event_open(2) |
| **LMDB** | Kernel same-page merging stats | /proc/ksm |
| **Process Tree** | Hiển thị cây process (pstree-like) | task_struct.parent + children |
| **Disk I/O** | /proc/diskstats + iostat | Block layer, request queue |

---

# Phụ lục

## A. Tham khảo kernel source

| File | Path trong kernel source |
|---|---|
| task_struct | `include/linux/sched.h` |
| sock | `include/net/sock.h` |
| inode | `include/linux/fs.h` |
| net_device | `include/linux/netdevice.h` |
| tcp_states | `include/net/tcp_states.h` |
| stat structure | `include/uapi/asm-generic/stat.h` |
| /proc/array.c | `fs/proc/array.c` |
| TCP socket seq show | `net/ipv4/tcp_ipv4.c` |
| /proc/net/dev | `net/core/net-procfs.c` |
| Scheduling | `kernel/sched/core.c` |

## B. License

MIT License — miễn phí sử dụng, sửa đổi, phân phối.

---

*Tài liệu này được viết cho dự án Ubuntu Monitor Desktop — Linux Kernel Learning Tool.*
*phiên bản: 1.0 — tháng 6/2026*

---

*Hết tài liệu.*
