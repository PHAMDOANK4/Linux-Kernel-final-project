"""
Network Monitor — giám sát mạng từ /proc/net/ và /sys/class/net/.

Sử dụng procfs và sysfs để lấy thông tin mạng trực tiếp từ kernel:
  - /proc/net/dev  → thống kê RX/TX từng interface
  - /proc/net/route → bảng định tuyến IPv4
  - /sys/class/net/*/ → thông chi tiết interface (speed, duplex, ...)

Nguyên lý kernel:
  Mỗi network interface trong kernel được quản lý bởi struct net_device
  (định nghĩa trong include/linux/netdevice.h). Driver thông báo
  thống kê packet qua cơ chế: trong interrupt handler, driver gọi
  netif_rx() để đưa packet lên stack, kernel tự động cập nhật
  counters trong struct net_device_stats.
"""

import os
import subprocess
from typing import Optional

from app.kernel_utils import (
    read_proc_file,
    parse_proc_net_dev,
    parse_proc_net_route,
    get_uptime_seconds,
)


def get_interface_stats() -> list[dict]:
    """Lấy thống kê mạng từ /proc/net/dev."""
    content = read_proc_file("/proc/net/dev")
    return parse_proc_net_dev(content)


def get_interfaces_detail() -> list[dict]:
    """
    Lấy thông tin chi tiết interface từ /sys/class/net/.
    
    sysfs (/sys) là virtual filesystem khác, kernel dùng để xuất
    thông tin device model ra userspace. Mỗi interface có một
    directory trong /sys/class/net/<iface>/ với các file:
      - address: địa chỉ MAC
      - addr_len: độ dài địa chỉ
      - speed: tốc độ (Mbps)
      - duplex: full/half
      - carrier: trạng thái kết nối vật lý (0/1)
      - operstate: trạng thái hoạt động (up/down)
      - mtu: Maximum Transmission Unit 
    """
    interfaces = []
    sys_net = "/sys/class/net"
    try:
        for iface in os.listdir(sys_net):
            iface_path = os.path.join(sys_net, iface)
            info = {"name": iface}

            # Đọc các file sysfs attribute
            for attr, key in [
                ("address", "mac"),
                ("speed", "speed"),
                ("duplex", "duplex"),
                ("operstate", "operstate"),
                ("mtu", "mtu"),
                ("carrier", "carrier"),
                ("type", "type"),
            ]:
                try:
                    val = read_proc_file(os.path.join(iface_path, attr)).strip()
                    info[key] = val
                except Exception:
                    info[key] = "?"

            # Lấy địa chỉ IP (nếu có) qua cách đọc file hoặc ioctl
            ips = []
            try:
                # Đọc /proc/net/fib_trie hoặc dùng subprocess nhẹ (ip addr)
                # Do procfs không có sẵn IP, ta dùng subprocess một lần
                pass
            except Exception:
                pass

            interfaces.append(info)
    except PermissionError:
        pass

    return interfaces


def get_ip_addresses() -> dict:
    """
    Lấy địa chỉ IP của từng interface.
    
    Dùng subprocess vì kernel không expose IPv4/IPv6 address
    qua procfs một cách dễ đọc. kernel lưu IP address trong
    struct in_device.in_dev_list (cho IPv4).
    """
    result = {}
    try:
        output = subprocess.run(
            ["ip", "-o", "addr", "show"],
            capture_output=True, text=True, timeout=5
        ).stdout
        for line in output.splitlines():
            parts = line.split()
            if len(parts) >= 4:
                iface = parts[1].rstrip(":")
                addr = parts[3]
                if iface not in result:
                    result[iface] = []
                result[iface].append(addr)
    except (subprocess.TimeoutExpired, FileNotFoundError, PermissionError):
        pass
    return result


def get_route_table() -> list[dict]:
    """Lấy bảng định tuyến từ /proc/net/route."""
    content = read_proc_file("/proc/net/route")
    return parse_proc_net_route(content)


def ping_host(target: str, count: int = 4) -> list[str]:
    """
    Ping đến host.
    
    Lưu ý: Raw socket (ICMP) yêu cầu CAP_NET_RAW capability.
    Trong kernel, ping sử dụng socket AF_INET với protocol IPPROTO_ICMP,
    kernel xử lý ICMP echo request/reply trong net/ipv4/icmp.c.
    
    Vì lý do bảo mật, ta dùng /bin/ping (setuid) thay vì raw socket.
    """
    results = []
    try:
        output = subprocess.run(
            ["ping", "-c", str(count), "-W", "2", target],
            capture_output=True, text=True, timeout=15,
        )
        for line in output.stdout.splitlines():
            results.append(line)
        if output.returncode != 0:
            for line in output.stderr.splitlines():
                results.append(f"[ERROR] {line}")
    except subprocess.TimeoutExpired:
        results.append("[ERROR] Ping timed out")
    except FileNotFoundError:
        results.append("[ERROR] ping command not found")
    except PermissionError:
        results.append("[ERROR] Permission denied")
    return results


def get_traffic_snapshot() -> dict:
    """
    Chụp nhanh lưu lượng mạng để tính tốc độ.
    
    Dùng /proc/net/dev để lấy bytes/packets counter.
    Kernel cập nhật các counter này trong interrupt context
    (net/core/dev.c: net_rx_action() và dev_hard_start_xmit()).
    """
    interfaces = get_interface_stats()
    snapshot = {}
    for iface in interfaces:
        snapshot[iface["name"]] = {
            "rx_bytes": iface["rx_bytes"],
            "tx_bytes": iface["tx_bytes"],
            "rx_packets": iface["rx_packets"],
            "tx_packets": iface["tx_packets"],
        }
    return snapshot


def calculate_speed(before: dict, after: dict, interval: float) -> dict:
    """
    Tính tốc độ RX/TX từ hai snapshot.
    
    Công thức: speed = (bytes_after - bytes_before) / interval (bytes/s)
    """
    speeds = {}
    all_ifaces = set(before.keys()) | set(after.keys())
    for iface in all_ifaces:
        b = before.get(iface, {})
        a = after.get(iface, {})
        rx_bytes = a.get("rx_bytes", 0) - b.get("rx_bytes", 0)
        tx_bytes = a.get("tx_bytes", 0) - b.get("tx_bytes", 0)
        if interval > 0:
            speeds[iface] = {
                "rx_speed": rx_bytes / interval,
                "tx_speed": tx_bytes / interval,
                "rx_bytes": rx_bytes,
                "tx_bytes": tx_bytes,
                "rx_packets": a.get("rx_packets", 0) - b.get("rx_packets", 0),
                "tx_packets": a.get("tx_packets", 0) - b.get("tx_packets", 0),
            }
        else:
            speeds[iface] = {"rx_speed": 0, "tx_speed": 0, "rx_bytes": 0, "tx_bytes": 0}
    return speeds


def format_speed(bytes_per_sec: float) -> str:
    """Định dạng tốc độ (bytes/s → Kbps, Mbps)."""
    bits_per_sec = bytes_per_sec * 8
    if bits_per_sec < 1000:
        return f"{bits_per_sec:.0f} bps"
    elif bits_per_sec < 1000000:
        return f"{bits_per_sec / 1000:.1f} Kbps"
    else:
        return f"{bits_per_sec / 1000000:.2f} Mbps"
