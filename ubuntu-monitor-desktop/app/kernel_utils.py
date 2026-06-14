"""
Kernel utility layer — giao tiếp trực tiếp với kernel Linux qua /proc filesystem
và system calls (ctypes). Module này thể hiện các khái niệm lập trình nhân Linux.

Nguyên tắc:
  - procfs (/proc) là một pseudo-filesystem do kernel cung cấp,
    cho phép userspace đọc trạng thái kernel dưới dạng file text.
  - Các file trong /proc được tạo động bởi kernel khi được đọc.
  - System calls qua libc là giao diện giữa userspace và kernel.
"""

import os
import pwd
import struct
import ctypes
import ctypes.util
from typing import Optional

# ---------------------------------------------------------------------------
# System call wrappers via libc (ctypes)
# ---------------------------------------------------------------------------
# Trong Linux, libc là thư viện C chuẩn, cung cấp wrapper cho system calls.
# Sử dụng ctypes để gọi trực tiếp vào libc, minh họa cơ chế system call.

_libc = ctypes.CDLL(ctypes.util.find_library("c"), use_errno=True)


def syscall_kill(pid: int, sig: int = 15) -> None:
    """
    Gọi system call kill(2) qua libc.
    
    Trong kernel Linux: kill(2) gửi signal đến process.
    - Hệ thống signal handling trong kernel:
      * kernel tra bảng process descriptor để tìm process theo PID
      * kiểm tra quyền (capability) của process gửi
      * delivery signal qua cơ chế sigpending/pending signal queue
    """
    ret = _libc.kill(ctypes.c_int(pid), ctypes.c_int(sig))
    if ret != 0:
        errno = ctypes.get_errno()
        raise OSError(errno, os.strerror(errno))


def syscall_getpid() -> int:
    """Gọi system call getpid(2) — lấy PID của process hiện tại."""
    return _libc.getpid()


# ---------------------------------------------------------------------------
# ProcFS parsers — đọc và phân tích cấu trúc file trong /proc
# ---------------------------------------------------------------------------
# Mỗi file trong /proc có format riêng do kernel định nghĩa.
# Các hàm dưới đây implement parser tương ứng.


def read_proc_file(path: str) -> str:
    """
    Đọc file từ procfs.
    Linux kernel tạo nội dung file ngay khi open(2) được gọi.
    Dữ liệu được generate bởi các hàm trong fs/proc/ của kernel.
    """
    try:
        with open(path, "r", errors="replace") as f:
            return f.read()
    except (PermissionError, FileNotFoundError, ProcessLookupError):
        return ""


def parse_proc_stat_to_dict(stat_content: str) -> dict:
    """
    Parse /proc/[PID]/stat — chứa thông tin process statistics
    do kernel cập nhật trong struct task_struct.
    
    struct task_struct trong kernel include/sched.h chứa:
      - pid_t pid;
      - char comm[TASK_COMM_LEN];
      - long state;
      - unsigned long utime, stime;  (thời gian user/kernel mode)
      - long priority, nice;
      - ... (hàng trăm field khác)
    
    Format: pid (comm) state ppid pgrp session tty_nr tty_pgrp flags
            min_flt cmin_flt maj_flt cmaj_flt utime stime ...
    """
    try:
        # Tên process có thể chứa dấu ngoặc đơn, cần xử lý riêng
        # Ví dụ: "1234 (bash) S 1233 ..."
        pid_end = stat_content.index("(")
        comm_end = stat_content.rindex(")")
        comm = stat_content[pid_end + 1 : comm_end]
        rest = stat_content[comm_end + 2:].split()
        fields = stat_content[:pid_end].split() + [comm] + rest
    except ValueError:
        return {}

    keys = [
        "pid", "comm", "state", "ppid", "pgrp", "session", "tty_nr",
        "tty_pgrp", "flags", "min_flt", "cmin_flt", "maj_flt", "cmaj_flt",
        "utime", "stime", "cutime", "cstime", "priority", "nice", "num_threads",
        "it_real_value", "start_time", "vsize", "rss", "rsslim",
    ]
    result = {}
    for i, key in enumerate(keys):
        if i < len(fields):
            result[key] = fields[i]
    return result


def parse_proc_status(status_content: str) -> dict:
    """
    Parse /proc/[PID]/status — thông tin process từ kernel ở dạng key: value.
    
    Chứa các field quan trọng:
      - Name: tên process (từ task_struct.comm)
      - State: trạng thái (R-running, S-sleeping, D-uninterruptible, Z-zombie, T-stopped)
      - Pid / PPid
      - Uid / Gid (real, effective, saved, filesystem)
      - VmRSS: bộ nhớ vật lý đang dùng
      - Threads: số luồng
    """
    data = {}
    for line in status_content.splitlines():
        if ":" in line:
            key, value = line.split(":", 1)
            data[key.strip()] = value.strip()
    return data


def parse_proc_net_tcp(content: str) -> list[dict]:
    """
    Parse /proc/net/tcp — danh sách TCP socket từ kernel.
    
    Trong kernel, mỗi socket được quản lý bởi struct sock trong net/core/sock.c.
    File /proc/net/tcp được implement trong net/ipv4/tcp_ipv4.c (hàm tcp4_seq_show).
    
    Format:
      sl  local_address  rem_address  st  tx_queue:rx_queue  tr  tm->when  retrnsmt
      uid  timeout  inode
      
    Địa chỉ được mã hóa dạng hex: "0100007F:0035" = 127.0.0.1:53
    """
    sockets = []
    lines = content.splitlines()
    # Bỏ qua header line đầu tiên
    for line in lines[1:]:
        parts = line.split()
        if len(parts) < 10:
            continue
        try:
            local_hex = parts[1]
            rem_hex = parts[2]
            state_hex = parts[3]
            tx_rx = parts[4]
            inode = parts[9]

            sockets.append({
                "slot": parts[0].rstrip(":"),
                "local": _decode_ip_port(local_hex),
                "remote": _decode_ip_port(rem_hex),
                "state": _tcp_state_name(int(state_hex, 16)),
                "tx_queue": tx_rx.split(":")[0],
                "rx_queue": tx_rx.split(":")[1],
                "uid": parts[7],
                "inode": inode,
            })
        except (IndexError, ValueError):
            continue
    return sockets


def parse_proc_net_udp(content: str) -> list[dict]:
    """Parse /proc/net/udp — format tương tự /proc/net/tcp."""
    sockets = []
    lines = content.splitlines()
    for line in lines[1:]:
        parts = line.split()
        if len(parts) < 10:
            continue
        try:
            local_hex = parts[1]
            rem_hex = parts[2]
            state_hex = parts[3]
            sockets.append({
                "slot": parts[0].rstrip(":"),
                "local": _decode_ip_port(local_hex),
                "remote": _decode_ip_port(rem_hex),
                "state": _tcp_state_name(int(state_hex, 16)) if int(state_hex, 16) <= 11 else "UNKNOWN",
                "uid": parts[7],
                "inode": parts[9],
            })
        except (IndexError, ValueError):
            continue
    return sockets


def parse_proc_net_unix(content: str) -> list[dict]:
    """Parse /proc/net/unix — Unix domain sockets."""
    sockets = []
    lines = content.splitlines()
    for line in lines[1:]:
        parts = line.split()
        if len(parts) < 8:
            continue
        try:
            sockets.append({
                "slot": parts[0].rstrip(":"),
                "refcnt": parts[1],
                "protocol": parts[2],
                "flags": parts[3],
                "type": parts[4],
                "state": parts[5],
                "inode": parts[6],
                "path": parts[7] if len(parts) > 7 else "",
            })
        except (IndexError, ValueError):
            continue
    return sockets


def parse_proc_net_dev(content: str) -> list[dict]:
    """
    Parse /proc/net/dev — thống kê mạng từng interface.
    
    Kernel cập nhật các counter này trong struct net_device_stats
    khi xử lý packet (interrupt handler trong net/core/dev.c).
    
    Format:
      Inter-|   Receive   |  Transmit
      face |bytes packets errs drop ... |bytes packets errs drop ...
    """
    interfaces = []
    lines = content.splitlines()
    # Bỏ 2 dòng header
    for line in lines[2:]:
        if ":" not in line:
            continue
        name, stats = line.split(":", 1)
        name = name.strip()
        values = stats.split()
        if len(values) >= 16:
            interfaces.append({
                "name": name,
                "rx_bytes": int(values[0]),
                "rx_packets": int(values[1]),
                "rx_errors": int(values[2]),
                "rx_drop": int(values[3]),
                "tx_bytes": int(values[8]),
                "tx_packets": int(values[9]),
                "tx_errors": int(values[10]),
                "tx_drop": int(values[11]),
            })
    return interfaces


def parse_proc_net_route(content: str) -> list[dict]:
    """
    Parse /proc/net/route — bảng định tuyến IPv4 từ kernel.
    
    Kernel maintain routing table trong struct fib_table (fib_hash.c).
    Mỗi dòng là một route entry do kernel quản lý.
    
    Format:
      Iface   Destination  Gateway  Flags  RefCnt  Use  Metric  Mask ...
    """
    routes = []
    lines = content.splitlines()
    for line in lines[1:]:
        parts = line.split()
        if len(parts) < 8:
            continue
        try:
            dest_hex = parts[1]
            gw_hex = parts[2]
            mask_hex = parts[7]
            routes.append({
                "interface": parts[0],
                "destination": _decode_ip_hex(dest_hex),
                "gateway": _decode_ip_hex(gw_hex),
                "flags": parts[3],
                "metric": parts[6],
                "mask": _decode_ip_hex(mask_hex),
            })
        except (IndexError, ValueError):
            continue
    return routes


def parse_cpu_info(proc_stat_content: str) -> dict:
    """
    Parse CPU usage từ /proc/stat.
    
    Dòng đầu tiên "cpu ..." chứa tổng thời gian CPU ở các chế độ:
      user, nice, system, idle, iowait, irq, softirq, steal, guest, guest_nice
    
    Các counter này được kernel cập nhật trong hàm account_process_tick()
    (kernel/sched/cputime.c) mỗi timer interrupt.
    """
    for line in proc_stat_content.splitlines():
        if line.startswith("cpu "):
            parts = line.split()
            if len(parts) >= 5:
                user = int(parts[1])
                nice = int(parts[2])
                system = int(parts[3])
                idle = int(parts[4])
                total = user + nice + system + idle
                if len(parts) > 5:
                    total += sum(int(p) for p in parts[5:] if p.isdigit())
                return {
                    "user": user,
                    "nice": nice,
                    "system": system,
                    "idle": idle,
                    "total": total,
                }
    return {}


def parse_mem_info(content: str) -> dict:
    """
    Parse /proc/meminfo — thông tin bộ nhớ từ kernel.
    
    Kernel maintain các thông số này trong struct sysinfo
    và cập nhật qua các hàm mm/page_alloc.c.
    
    Các giá trị quan trọng:
      - MemTotal: tổng RAM vật lý
      - MemAvailable: RAM khả dụng (tính cả cache có thể thu hồi)
      - SwapTotal / SwapFree: thông tin swap
    """
    info = {}
    for line in content.splitlines():
        if ":" in line:
            key, value = line.split(":", 1)
            info[key.strip()] = value.strip()
    return info


def get_uptime_seconds(content: str) -> float:
    """
    Parse /proc/uptime — thời gian hoạt động của hệ thống.
    
    Kernel đếm số giây kể từ boot trong biến global xtime.tv_sec
    (cập nhật bởi timer interrupt trong kernel/time/timekeeping.c).
    """
    try:
        return float(content.split()[0])
    except (IndexError, ValueError):
        return 0.0


# ---------------------------------------------------------------------------
# Helper functions
# ---------------------------------------------------------------------------

def _hex_to_ip(hex_str: str) -> str:
    """
    Chuyển địa chỉ IPv4 dạng hex (little-endian 32-bit) sang dot-decimal.
    
    Ví dụ: "0100007F" → "127.0.0.1"
    
    Trong kernel, địa chỉ IP được lưu dưới dạng __be32 (big-endian),
    nhưng /proc/net/* hiển thị ở dạng little-endian hex.
    """
    try:
        raw = bytes.fromhex(hex_str.zfill(8))
        return ".".join(str(b) for b in reversed(raw))
    except (ValueError, TypeError):
        return "0.0.0.0"


def _decode_ip_port(hex_str: str) -> str:
    """
    Giải mã địa chỉ:port từ hex.
    Format trong /proc/net/*: "0100007F:0035" → "127.0.0.1:53"
    """
    try:
        ip_hex, port_hex = hex_str.split(":")
        ip = _hex_to_ip(ip_hex)
        port = str(int(port_hex, 16))
        return f"{ip}:{port}"
    except (ValueError, IndexError):
        return hex_str


def _decode_ip_hex(hex_str: str) -> str:
    """Giải mã địa chỉ IPv4 dạng hex 32-bit từ /proc/net/route."""
    return _hex_to_ip(hex_str)


def _tcp_state_name(state: int) -> str:
    """
    Chuyển mã trạng thái TCP (integer) thành tên theo RFC 793.
    
    Định nghĩa trong kernel: include/net/tcp_states.h
      TCP_ESTABLISHED = 1, TCP_SYN_SENT = 2, TCP_SYN_RECV = 3,
      TCP_FIN_WAIT1 = 4, TCP_FIN_WAIT2 = 5, TCP_TIME_WAIT = 6,
      TCP_CLOSE = 7, TCP_CLOSE_WAIT = 8, TCP_LAST_ACK = 9,
      TCP_LISTEN = 10, TCP_CLOSING = 11
    """
    states = {
        1: "ESTABLISHED", 2: "SYN_SENT", 3: "SYN_RECV",
        4: "FIN_WAIT1", 5: "FIN_WAIT2", 6: "TIME_WAIT",
        7: "CLOSE", 8: "CLOSE_WAIT", 9: "LAST_ACK",
        10: "LISTEN", 11: "CLOSING",
    }
    return states.get(state, f"UNKNOWN({state})")


def get_process_uid(pid: int) -> Optional[int]:
    """Lấy UID thực của process từ /proc/[PID]/status."""
    status = parse_proc_status(read_proc_file(f"/proc/{pid}/status"))
    uid_line = status.get("Uid", "")
    if uid_line:
        try:
            return int(uid_line.split("\t")[0])
        except (ValueError, IndexError):
            return None
    return None


def get_username_from_uid(uid: int) -> str:
    """Tra cứu username từ UID qua file /etc/passwd."""
    try:
        return pwd.getpwuid(uid).pw_name
    except KeyError:
        return str(uid)


def get_process_env(pid: int, key: str) -> Optional[str]:
    """Đọc biến môi trường từ /proc/[PID]/environ."""
    try:
        content = read_proc_file(f"/proc/{pid}/environ")
        for entry in content.split("\x00"):
            if entry.startswith(f"{key}="):
                return entry.split("=", 1)[1]
    except Exception:
        pass
    return None
