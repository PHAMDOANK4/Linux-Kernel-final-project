"""
Socket Monitor — theo dõi socket từ /proc/net/ và /proc/[PID]/fd/.

Thay vì dùng lệnh ss hoặc netstat, đọc trực tiếp từ các file
do kernel tạo động trong /proc/net/:
  - /proc/net/tcp  → TCP socket table
  - /proc/net/udp  → UDP socket table
  - /proc/net/unix → Unix domain socket table

Nguyên lý kernel:
  Mỗi socket trong kernel được quản lý bởi struct sock
  (định nghĩa trong include/net/sock.h). Các trường chính:
    - sk_daddr, sk_rcv_saddr: địa chỉ IP đích/nguồn
    - sk_dport, sk_num: port đích/nguồn (network byte order)
    - sk_state: trạng thái TCP (TCP_ESTABLISHED, TCP_LISTEN, ...)
    - sk_socket: con trỏ đến struct socket (lớp VFS)
    - sk_wq: wait queue cho I/O blocking
  
  File /proc/net/tcp được implement trong net/ipv4/tcp_ipv4.c
  (hàm tcp4_seq_show). Khi userspace đọc file này, kernel
  duyệt qua bảng hash các socket (tcp_hashinfo) và format output.
"""

from app.kernel_utils import (
    read_proc_file,
    parse_proc_net_tcp,
    parse_proc_net_udp,
    parse_proc_net_unix,
)


def get_tcp_sockets() -> list[dict]:
    """Đọc danh sách TCP socket từ /proc/net/tcp."""
    content = read_proc_file("/proc/net/tcp")
    return parse_proc_net_tcp(content)


def get_udp_sockets() -> list[dict]:
    """Đọc danh sách UDP socket từ /proc/net/udp."""
    content = read_proc_file("/proc/net/udp")
    return parse_proc_net_udp(content)


def get_unix_sockets() -> list[dict]:
    """Đọc danh sách Unix socket từ /proc/net/unix."""
    content = read_proc_file("/proc/net/unix")
    return parse_proc_net_unix(content)


def get_all_sockets() -> list[dict]:
    """Gộp tất cả socket (TCP + UDP + Unix) thành một danh sách."""
    result = []
    for s in get_tcp_sockets():
        s["protocol"] = "TCP"
        result.append(s)
    for s in get_udp_sockets():
        s["protocol"] = "UDP"
        result.append(s)
    for s in get_unix_sockets():
        s["protocol"] = "UNIX"
        result.append(s)
    return result


def get_sockets_summary() -> dict:
    """
    Thống kê nhanh các socket đang hoạt động.
    
    Hữu ích cho dashboard overview: đếm số kết nối theo trạng thái.
    Trong kernel, mỗi trạng thái TCP tương ứng một giá trị trong
    enum tcp_state (include/net/tcp_states.h).
    """
    tcp = get_tcp_sockets()
    udp = get_udp_sockets()
    unix = get_unix_sockets()

    state_count = {}
    for s in tcp:
        state = s.get("state", "UNKNOWN")
        state_count[f"TCP/{state}"] = state_count.get(f"TCP/{state}", 0) + 1

    return {
        "total_tcp": len(tcp),
        "total_udp": len(udp),
        "total_unix": len(unix),
        "total": len(tcp) + len(udp) + len(unix),
        "listening_ports": sum(1 for s in tcp if s.get("state") == "LISTEN"),
        "established": sum(1 for s in tcp if s.get("state") == "ESTABLISHED"),
        "state_count": state_count,
    }
