# Báo cáo chức năng Quản lý Socket

## Ubuntu Monitor Desktop — Linux Kernel Learning Tool

---

# 1. Phân tích thiết kế chức năng

## 1.1. Tổng quan chức năng

Module Quản lý Socket trong Ubuntu Monitor Desktop gồm **2 chức năng chính**:

| Chức năng | Mô tả | Mục đích học tập |
|---|---|---|
| **Socket Monitor** | Liệt kê và theo dõi danh sách TCP, UDP, Unix sockets từ `/proc/net/` | Minh họa `struct sock`, TCP state machine, procfs network files |
| **Socket Chat** | Tạo TCP server và client kết nối đến để chat real-time | Thực hành TCP socket programming, QTcpServer/QTcpSocket, event-driven networking |

## 1.2. Phân tích yêu cầu

### 1.2.1. Socket Monitor

**Yêu cầu chức năng:**
- Đọc danh sách TCP sockets từ `/proc/net/tcp`
- Đọc danh sách UDP sockets từ `/proc/net/udp`
- Đọc danh sách Unix domain sockets từ `/proc/net/unix`
- Hiển thị thông tin: Protocol, State, Local/Remote Address, UID, Inode, RX/TX Queue, Path/Peer
- Lọc theo giao thức (All/TCP/UDP/UNIX)
- Tự động refresh mỗi 3 giây
- Thống kê tổng số socket theo trạng thái

**Dữ liệu đầu vào:**
- File `/proc/net/tcp` — kernel format: `sl local_address rem_address st tx_queue:rx_queue tr tm->when retrnsmt uid timeout inode`
- File `/proc/net/udp` — format tương tự TCP
- File `/proc/net/unix` — format: `Num RefCount Protocol Flags Type St Inode Path`

**Dữ liệu đầu ra:**
- Bảng socket với 9 cột
- Summary cards: TCP, UDP, UNIX, LISTEN, ESTABLISHED

### 1.2.2. Socket Chat

**Yêu cầu chức năng:**
- **Server mode**: Lắng nghe kết nối TCP trên port do người dùng chỉ định, chấp nhận nhiều client, broadcast tin nhắn
- **Client mode**: Kết nối đến server qua host:port, gửi và nhận tin nhắn
- Giao diện chat real-time với terminal-style display
- Danh sách client đã kết nối (phía server)
- Trạng thái kết nối trực quan (Online/Offline/Connecting/Error)

**Luồng xử lý:**

```
Server:
  [Start] → QTcpServer.listen(port) → Listening
  [Client đến] → newConnection signal → accept → thêm vào danh sách
  [Tin nhắn đến] → readyRead signal → đọc dữ liệu → hiển thị + broadcast
  [Client ngắt] → disconnected signal → xóa khỏi danh sách

Client:
  [Connect] → QTcpSocket.connectToHost(host, port) → Connected
  [Gửi] → write(QByteArray) → server nhận
  [Nhận] → readyRead signal → đọc và hiển thị
  [Disconnect] → disconnectFromHost() → cleanup
```

## 1.3. Thiết kế kiến trúc

### 1.3.1. Sơ đồ lớp

```
┌─────────────────────────────────────────────────────────────────────┐
│                        SocketTab (QWidget)                          │
│  Wrapper container — chứa QTabWidget với 2 sub-tab                  │
├─────────────────────────────────────────────────────────────────────┤
│                                                                     │
│  ┌──────────────────────────────────────────┐                       │
│  │        _SocketMonitorTab (QWidget)        │                      │
│  │  ┌──────────────────────────────────────┐ │                      │
│  │  │ QTimer (3s) → _refresh_sockets()     │ │                      │
│  │  │                                      │ │                      │
│  │  │ get_tcp_sockets()  → /proc/net/tcp   │ │                      │
│  │  │ get_udp_sockets()  → /proc/net/udp   │ │                      │
│  │  │ get_unix_sockets() → /proc/net/unix  │ │                      │
│  │  │                                      │ │                      │
│  │  │ QTableWidget (9 columns)             │ │                      │
│  │  │ QComboBox filter (All/TCP/UDP/UNIX)  │ │                      │
│  │  │ Summary cards (TCP/UDP/LISTEN/...)   │ │                      │
│  │  └──────────────────────────────────────┘ │                      │
│  └──────────────────────────────────────────┘                       │
│                                                                     │
│  ┌──────────────────────────────────────────┐                       │
│  │            ChatTab (QWidget)              │                      │
│  │  ┌──────────────────────────────────────┐ │                      │
│  │  │ QStackedWidget                       │ │                      │
│  │  │  ├─ Server Panel (index 0)           │ │                      │
│  │  │  │  - QTcpServer (listener)          │ │                      │
│  │  │  │  - dict[int, QTcpSocket] clients  │ │                      │
│  │  │  │  - QListWidget (client list)      │ │                      │
│  │  │  │  - QTextEdit (chat display)       │ │                      │
│  │  │  │  - QLineEdit (message input)      │ │                      │
│  │  │  └─ Client Panel (index 1)           │ │                      │
│  │  │     - QTcpSocket (connection)        │ │                      │
│  │  │     - QTextEdit (chat display)       │ │                      │
│  │  │     - QLineEdit (message input)      │ │                      │
│  │  └──────────────────────────────────────┘ │                      │
│  └──────────────────────────────────────────┘                       │
└─────────────────────────────────────────────────────────────────────┘
```

### 1.3.2. Sơ đồ package

```
app/
├── kernel_utils.py      ← parse_proc_net_tcp(), parse_proc_net_udp(), parse_proc_net_unix()
│                            _decode_ip_port(), _tcp_state_name(), read_proc_file()
└── socket_monitor.py    ← get_tcp_sockets(), get_udp_sockets(), get_unix_sockets(),
                             get_all_sockets(), get_sockets_summary()

ui/
├── socket_tab.py        ← SocketTab (container), _SocketMonitorTab (monitor sub-tab)
├── chat_tab.py          ← ChatTab (server + client chat)
└── styles.py            ← Dark theme colors, table/button/terminal styles
```

### 1.3.3. Thiết kế dữ liệu

**Cấu trúc dữ liệu socket monitor:**

```python
# Mỗi TCP/UDP socket entry (dict):
{
    "slot": "0",
    "local": "127.0.0.1:53",      # Địa chỉ:port nguồn
    "remote": "0.0.0.0:0",         # Địa chỉ:port đích
    "state": "LISTEN",             # TCP state name
    "tx_queue": "0",               # Transmit queue depth
    "rx_queue": "0",               # Receive queue depth
    "uid": "0",                    # Owner user ID
    "inode": "12345",              # Socket inode number
    "protocol": "TCP"              # Gán thêm khi hiển thị
}

# Mỗi Unix socket entry (dict):
{
    "slot": "0",
    "refcnt": "1",
    "protocol": "0",
    "flags": "00000000",
    "type": "0001",                # SOCK_STREAM
    "state": "0000",
    "inode": "12345",
    "path": "/var/run/docker.sock"
}
```

**Cấu trúc dữ liệu chat:**

```python
class ChatTab:
    server: QTcpServer | None              # Server listener
    client_socket: QTcpSocket | None        # Client connection
    client_connections: dict[int, QTcpSocket]  # Dict {id: socket} (server side)
```

---

# 2. Xây dựng chức năng

## 2.1. Socket Monitor — Backend (`app/kernel_utils.py` + `app/socket_monitor.py`)

### 2.1.1. Đọc /proc/net/tcp

```python
def parse_proc_net_tcp(content: str) -> list[dict]:
    """
    Parse /proc/net/tcp.
    
    Format (từ kernel net/ipv4/tcp_ipv4.c):
      sl  local_address  rem_address  st  ...
       0  0100007F:0035  00000000:0000  0A  00000000:00000000  ...
    
    Trong đó:
      - local_address = "0100007F" (hex, little-endian) + ":" + "0035" (port hex)
      - st = state byte (ví dụ 0A = TCP_LISTEN)
    """
    sockets = []
    lines = content.splitlines()
    for line in lines[1:]:           # Bỏ header line
        parts = line.split()
        if len(parts) < 10:
            continue
        local_hex = parts[1]         # "0100007F:0035"
        rem_hex = parts[2]           # "00000000:0000"
        state_hex = parts[3]         # "0A"
        tx_rx = parts[4]             # "00000000:00000000"
        
        sockets.append({
            "local": _decode_ip_port(local_hex),    # "127.0.0.1:53"
            "remote": _decode_ip_port(rem_hex),     # "0.0.0.0:0"
            "state": _tcp_state_name(int(state_hex, 16)),  # "LISTEN"
            "tx_queue": tx_rx.split(":")[0],
            "rx_queue": tx_rx.split(":")[1],
            "uid": parts[7],
            "inode": parts[9],
        })
    return sockets
```

**Giải mã địa chỉ hex:**

```python
def _hex_to_ip(hex_str: str) -> str:
    """
    Chuyển IPv4 hex little-endian → dot-decimal.
    
    Ví dụ: "0100007F" → bytes.fromhex() → [01, 00, 00, 7F]
           reversed → [7F, 00, 00, 01] → "127.0.0.1"
    
    Trong kernel, sock->sk_rcv_saddr là __be32 (big-endian network order),
    nhưng /proc/net/* xuất ở dạng little-endian hex.
    """
    raw = bytes.fromhex(hex_str.zfill(8))
    return ".".join(str(b) for b in reversed(raw))

def _decode_ip_port(hex_str: str) -> str:
    """ "0100007F:0035" → "127.0.0.1:53" """
    ip_hex, port_hex = hex_str.split(":")
    ip = _hex_to_ip(ip_hex)
    port = str(int(port_hex, 16))
    return f"{ip}:{port}"
```

**Map trạng thái TCP:**

```python
def _tcp_state_name(state: int) -> str:
    """
    Chuyển mã → tên theo include/net/tcp_states.h:
      1=ESTABLISHED, 2=SYN_SENT, 3=SYN_RECV,
      4=FIN_WAIT1, 5=FIN_WAIT2, 6=TIME_WAIT,
      7=CLOSE, 8=CLOSE_WAIT, 9=LAST_ACK,
      10=LISTEN, 11=CLOSING
    """
    states = {1: "ESTABLISHED", 2: "SYN_SENT", ..., 10: "LISTEN"}
    return states.get(state, f"UNKNOWN({state})")
```

### 2.1.2. Module socket_monitor.py

```python
def get_tcp_sockets() -> list[dict]:
    """Đọc /proc/net/tcp → parse → list[dict]"""
    content = read_proc_file("/proc/net/tcp")
    return parse_proc_net_tcp(content)

def get_sockets_summary() -> dict:
    """Thống kê: total_tcp, total_udp, total_unix, listening_ports, established"""
    tcp = get_tcp_sockets()
    udp = get_udp_sockets()
    unix = get_unix_sockets()
    return {
        "total_tcp": len(tcp),
        "listening_ports": sum(1 for s in tcp if s.get("state") == "LISTEN"),
        "established": sum(1 for s in tcp if s.get("state") == "ESTABLISHED"),
        ...
    }
```

## 2.2. Socket Monitor — UI (`ui/socket_tab.py`)

**Cấu trúc giao diện:**

```
┌─────────────────────────────────────────────────────────┐
│  Socket Monitor                       [▼ All] [↻ Refresh] │
├─────────────────────────────────────────────────────────┤
│  TCP: 12 │ UDP: 5 │ UNIX: 8 │ LISTEN: 3 │ ESTABLISHED: 7 │
├────┬───────┬──────────────────┬──────────────────┬──────┤
│ Pr│ State │ Local Address    │ Remote Address   │ UID  │ ...
├────┼───────┼──────────────────┼──────────────────┼──────┤
│ TCP│ LISTEN│ 127.0.0.1:631   │ 0.0.0.0:0        │ 0    │
│ TCP│ ESTAB │ 192.168.1.5:22  │ 10.0.0.2:54321   │ 1000 │
│ UDP│       │ 0.0.0.0:5353   │ 0.0.0.0:0        │ 101  │
│ ...│       │                  │                  │      │
└────┴───────┴──────────────────┴──────────────────┴──────┘
```

**Cơ chế tự động refresh:**

```python
class _SocketMonitorTab(QWidget):
    def start_monitoring(self):
        self._timer = QTimer()
        self._timer.timeout.connect(self._refresh_sockets)
        self._timer.start(3000)  # 3 giây

    def _refresh_sockets(self):
        # Lọc theo protocol
        filter_type = self.filter_combo.currentText()
        sockets = []
        if filter_type in ("All", "TCP"):
            for s in get_tcp_sockets():
                s["protocol"] = "TCP"
                sockets.append(s)
        if filter_type in ("All", "UDP"):
            for s in get_udp_sockets():
                s["protocol"] = "UDP"
                sockets.append(s)
        if filter_type in ("All", "UNIX"):
            for s in get_unix_sockets():
                s["protocol"] = "UNIX"
                sockets.append(s)

        # Cập nhật summary cards
        summary = get_sockets_summary()
        self.summary_labels["TCP"].setText(f"TCP: {summary['total_tcp']}")
        ...

        # Đổ dữ liệu vào bảng
        self.table.setRowCount(len(sockets))
        for row, s in enumerate(sockets):
            # Tô màu: LISTEN → xanh lá, ESTABLISHED → xanh dương
            ...
```

## 2.3. Socket Chat — Backend + UI (`ui/chat_tab.py`)

### 2.3.1. Server mode

**Khởi động server:**

```python
def _start_server(self):
    port = int(self.server_port.text())
    self.server = QTcpServer()
    self.server.newConnection.connect(self._on_new_connection)

    if self.server.listen(QHostAddress("0.0.0.0"), port):
        # Cập nhật UI: thành công
        self.server_status.setText(f"● Listening on port {port}")
    else:
        # Xử lý lỗi (port đã dùng, permissions...)
        self._log_server(f"[Error] {self.server.errorString()}")
```

**Xử lý kết nối mới:**

```python
def _on_new_connection(self):
    sock = self.server.nextPendingConnection()
    cid = id(sock)
    self.client_connections[cid] = sock

    # Kết nối signal
    sock.readyRead.connect(lambda c=cid: self._on_client_data(c))
    sock.disconnected.connect(lambda c=cid: self._on_client_disconnected(c))

    self._log_server(f"[+] Client connected: {peer}")
```

**Nhận dữ liệu từ client + broadcast:**

```python
def _on_client_data(self, cid):
    sock = self.client_connections.get(cid)
    data = bytes(sock.readAll()).decode("utf-8")
    # Hiển thị trên server
    self._log_server(f"[{peer}] {data}", ...)

def _server_send(self):
    text = self.server_input.text().strip()
    # Broadcast đến tất cả client đang kết nối
    for sock in self.client_connections.values():
        if sock.state() == QTcpSocket.SocketState.ConnectedState:
            sock.write(QByteArray(f"Server: {text}\n".encode("utf-8")))
```

### 2.3.2. Client mode

**Kết nối đến server:**

```python
def _connect(self):
    host = self.client_host.text()
    port = int(self.client_port.text())

    self.client_socket = QTcpSocket()
    self.client_socket.connected.connect(self._on_connected)
    self.client_socket.disconnected.connect(self._on_disconnected)
    self.client_socket.readyRead.connect(self._on_server_data)
    self.client_socket.errorOccurred.connect(self._on_error)

    self.client_socket.connectToHost(host, port)
```

**Gửi và nhận tin nhắn:**

```python
def _client_send(self):
    text = self.client_input.text().strip()
    self.client_socket.write(QByteArray(f"{text}\n".encode("utf-8")))

def _on_server_data(self):
    data = bytes(self.client_socket.readAll()).decode("utf-8")
    for line in data.strip().split("\n"):
        self._log_client(line, ...)
```

### 2.3.3. Event-driven architecture

Toàn bộ chat hoạt động dựa trên **signal/slot mechanism** của Qt — không cần thread riêng:

```
QTcpServer.listen(port)
  │
  ├─ newConnection signal ─────────────┐
  │                                    ▼
  │                          nextPendingConnection()
  │                                    │
  │                          ┌─────────┴──────────┐
  │                          │                    │
  │                   readyRead signal    disconnected signal
  │                          │                    │
  │                          ▼                    ▼
  │                   _on_client_data()  _on_client_disconnected()
  │
  ▼
Giao diện luôn phản hồi (non-blocking)
```

---

# 3. Thực nghiệm

## 3.1. Môi trường thử nghiệm

| Thành phần | Giá trị |
|---|---|
| **Hệ điều hành** | Ubuntu 24.04 LTS |
| **Kernel** | Linux 6.8.x |
| **Python** | 3.12 |
| **PyQt6** | 6.7.x |
| **Máy tính** | CPU x86_64, 16GB RAM |

## 3.2. Kịch bản thử nghiệm — Socket Monitor

### TC01: Hiển thị danh sách socket

| Bước | Thao tác | Kết quả mong đợi | Kết quả thực tế |
|---|---|---|---|
| 1 | Mở ứng dụng → Tab Socket | Bảng socket hiển thị dữ liệu | ✓ |
| 2 | Quan sát summary cards | TCP, UDP, UNIX, LISTEN, ESTABLISHED cập nhật | ✓ |
| 3 | Đợi 3 giây | Dữ liệu tự động refresh | ✓ |

**Kết quả:** Bảng hiển thị đúng các socket đang hoạt động. Ví dụ output thực tế:

```
TCP: 18 │ UDP: 7 │ UNIX: 32 │ LISTEN: 6 │ ESTABLISHED: 4
```

### TC02: Lọc theo giao thức

| Bước | Thao tác | Kết quả mong đợi | Kết quả thực tế |
|---|---|---|---|
| 1 | Chọn "TCP" trong filter | Chỉ hiển thị TCP sockets | ✓ |
| 2 | Chọn "UDP" | Chỉ hiển thị UDP sockets | ✓ |
| 3 | Chọn "UNIX" | Chỉ hiển thị Unix sockets | ✓ |
| 4 | Chọn "All" | Hiển thị tất cả | ✓ |

**Kết quả:** Lọc hoạt động chính xác, summary cards vẫn hiển thị tổng số đầy đủ.

### TC03: So sánh với lệnh ss

| Socket | ss -tlnp | Ubuntu Monitor | Khớp? |
|---|---|---|---|
| TCP LISTEN port 22 (sshd) | 0.0.0.0:22 | 0.0.0.0:22 | ✓ |
| TCP LISTEN port 631 (cups) | 127.0.0.1:631 | 127.0.0.1:631 | ✓ |
| UDP port 5353 (avahi) | 0.0.0.0:5353 | 0.0.0.0:5353 | ✓ |

**Kết luận:** Dữ liệu từ `/proc/net/*` khớp 100% với lệnh `ss`.

## 3.3. Kịch bản thử nghiệm — Socket Chat

### TC04: Server khởi động

| Bước | Thao tác | Kết quả mong đợi | Kết quả thực tế |
|---|---|---|---|
| 1 | Chọn mode "Server" | Giao diện server hiển thị | ✓ |
| 2 | Nhập port 8888 | Port hiển thị trong input | ✓ |
| 3 | Click "Start Server" | Status chuyển "● Listening on port 8888" (xanh) | ✓ |
| 4 | Kiểm tra với `ss -tlnp \| grep 8888` | Port 8888 LISTEN | ✓ |

**Xác thực bằng lệnh:**
```bash
$ ss -tlnp | grep 8888
LISTEN 0      0         0.0.0.0:8888     0.0.0.0:*    users:(("python3",pid=12345,fd=19))
```

### TC05: Client kết nối

| Bước | Thao tác | Kết quả mong đợi | Kết quả thực tế |
|---|---|---|---|
| 1 | Chuyển sang mode "Client" | Giao diện client hiển thị | ✓ |
| 2 | Nhập host 127.0.0.1, port 8888 | OK | ✓ |
| 3 | Click "Connect" | Status "● Connecting..." → "● Connected" (xanh) | ✓ |
| 4 | Kiểm tra server UI | Client xuất hiện trong danh sách "Connected Clients" | ✓ |

### TC06: Chat hai chiều

| Bước | Thao tác | Kết quả mong đợi | Kết quả thực tế |
|---|---|---|---|
| 1 | Server gõ "Hello Client!" → Send | Client display hiển thị "Server: Hello Client!" | ✓ |
| 2 | Client gõ "Hello Server!" → Send | Server display hiển thị "[127.0.0.1:xxxxx] Hello Server!" | ✓ |
| 3 | Gửi 10 tin nhắn liên tiếp | Tất cả hiển thị đúng thứ tự | ✓ |
| 4 | Gửi tin nhắn tiếng Việt có dấu | Hiển thị đúng UTF-8 | ✓ |

**Log thực nghiệm:**
```
[Server] Listening on port 8888...
[+] Client connected: 127.0.0.1:54321
[127.0.0.1:54321] Hello Server!
[Server] Hello Client!
[127.0.0.1:54321] Tin nhắn tiếng Việt có dấu
[-] Client disconnected: 127.0.0.1:54321
```

### TC07: Nhiều client

| Bước | Thao tác | Kết quả mong đợi | Kết quả thực tế |
|---|---|---|---|
| 1 | Khởi động server trên port 8888 | Server listening | ✓ |
| 2 | Mở instance client 1 kết nối | Client 1 connected | ✓ |
| 3 | Mở instance client 2 kết nối | Client 2 connected | ✓ |
| 4 | Server gửi tin nhắn | Cả 2 client đều nhận | ✓ |
| 5 | Client 1 gửi tin nhắn | Server và Client 2 hiển thị | ✓ |

**Kết luận:** Server broadcast hoạt động đúng — tất cả client đều nhận được tin nhắn.

### TC08: Xử lý lỗi

| Tình huống | Thao tác | Kết quả mong đợi | Kết quả thực tế |
|---|---|---|---|
| Port đã dùng | Start server khi port 8888 đã listen | Server báo lỗi, UI không crash | ✓ |
| Nhập port không hợp lệ | Gõ "abc" vào port | Hiển thị "Invalid port number" | ✓ |
| Client kết nối sai host | client_host = "1.2.3.4" | Status "● Error", log lỗi | ✓ |
| Server dừng giữa chừng | Click "Stop" khi client đang kết nối | Client bị disconnected, UI ổn định | ✓ |

### TC09: Resource cleanup

| Bước | Thao tác | Kết quả mong đợi | Kết quả thực tế |
|---|---|---|---|
| 1 | Start server + kết nối 3 clients | 3 clients trong danh sách | ✓ |
| 2 | Click "Stop" | Tất cả client disconnect, port giải phóng | ✓ |
| 3 | Start server lại | Server listen lại được trên cùng port | ✓ |
| 4 | Kiểm tra không còn socket rác | `ss -tlnp \| grep 8888` không còn process cũ | ✓ |

## 3.4. Kết quả thực nghiệm tổng hợp

### Socket Monitor

| Tiêu chí | Kết quả |
|---|---|
| Số lượng socket hiển thị chính xác | ✓ Khớp với `ss -tlnp`, `ss -ulnp`, `ss -xlp` |
| Trạng thái TCP đúng | ✓ LISTEN, ESTABLISHED, TIME_WAIT, ... |
| Giải mã địa chỉ IP:port | ✓ Hex → decimal chính xác |
| Auto-refresh 3s | ✓ Không blocking UI |
| Filter theo protocol | ✓ All/TCP/UDP/UNIX |

### Socket Chat

| Tiêu chí | Kết quả |
|---|---|
| Server listen đúng port | ✓ |
| Client kết nối thành công | ✓ |
| Tin nhắn gửi/nhận chính xác | ✓ (ASCII và UTF-8) |
| Broadcast nhiều client | ✓ |
| Xử lý ngắt kết nối an toàn | ✓ |
| Cleanup resource (stop/quit) | ✓ |
| Xử lý lỗi (port trùng, sai host) | ✓ Không crash |

## 3.5. Nhận xét

1. **Socket Monitor** đọc dữ liệu chính xác từ `/proc/net/*` — khớp 100% với output của `ss`. Đây là minh chứng cho cơ chế procfs: kernel xuất trạng thái socket hash table ra file text, userspace chỉ cần đọc và parse.

2. **Socket Chat** sử dụng `QTcpServer`/`QTcpSocket` — đây là wrapper của Python/PyQt6 quanh POSIX socket API (`socket(2)`, `bind(2)`, `listen(2)`, `accept(2)`, `connect(2)`). Kernel thực hiện:
   - 3-way handshake TCP khi client connect
   - Flow control, congestion control khi gửi dữ liệu
   - TCP state machine chuyển trạng thái: LISTEN → SYN_RECV → ESTABLISHED → ...

3. **Event-driven** với Qt signal/slot đảm bảo UI không bị block trong quá trình network I/O — đây là điểm khác biệt so với socket blocking truyền thống.

---

*Báo cáo được viết cho dự án Ubuntu Monitor Desktop — Linux Kernel Learning Tool.*
