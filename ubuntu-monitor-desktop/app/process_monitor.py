"""
Process Monitor — thu thập dữ liệu tiến trình từ /proc filesystem.

Thay vì dùng lệnh shell (ps, top), module này đọc trực tiếp từ /proc
để lấy thông tin process từ kernel:
  - /proc/[PID]/status  → trạng thái, UID, bộ nhớ
  - /proc/[PID]/stat    → CPU time, parent PID
  - /proc/[PID]/cmdline → dòng lệnh khởi động
  - /proc/[PID]/fd/     → danh sách file descriptor
  - /proc/[PID]/cwd     → thư mục làm việc hiện tại

Nguyên lý kernel:
  Mỗi process trong Linux được kernel quản lý qua struct task_struct
  (định nghĩa trong include/linux/sched.h). Các trường chính:
    - pid: process ID (duy nhất trong namespace)
    - parent: con trỏ đến task_struct của parent (PPID)
    - comm: tên process (tối đa 16 ký tự)
    - state: trạng thái hiện tại (TASK_RUNNING, TASK_INTERRUPTIBLE, ...)
    - prio, static_prio, normal_prio: độ ưu tiên scheduling
    - utime, stime: thời gian CPU ở user/kernel mode
    - mm: con trỏ đến struct mm_struct (quản lý bộ nhớ ảo)
    - fs: thông tin filesystem (cwd, root)
    - files: bảng file descriptor
    - signal: signal handlers và pending signals
"""

import os
from typing import Optional

from app.kernel_utils import (
    read_proc_file,
    parse_proc_stat_to_dict,
    parse_proc_status,
    get_process_uid,
    get_username_from_uid,
    parse_mem_info,
)


def list_all_pids() -> list[int]:
    """
    Quét /proc để lấy danh sách PID đang hoạt động.
    
    Trong kernel, các process được lưu trong hash table pid_hash[]
    và linked list qua task_struct.tasks. Directory /proc được
    generate động bởi kernel khi userspace đọc directory entries.
    """
    pids = []
    try:
        for entry in os.listdir("/proc"):
            if entry.isdigit():
                pids.append(int(entry))
    except PermissionError:
        pass
    return sorted(pids)


def get_process_info(pid: int) -> Optional[dict]:
    """
    Thu thập toàn bộ thông tin một process.
    
    Kết hợp dữ liệu từ nhiều file trong /proc/[PID]/ để có
    cái nhìn đầy đủ về process theo góc nhìn kernel.
    """
    stat_content = read_proc_file(f"/proc/{pid}/stat")
    if not stat_content:
        return None

    stat = parse_proc_stat_to_dict(stat_content)
    status = parse_proc_status(read_proc_file(f"/proc/{pid}/status"))
    cmdline = read_proc_file(f"/proc/{pid}/cmdline").replace("\x00", " ").strip()

    uid = get_process_uid(pid)
    username = get_username_from_uid(uid) if uid else "?"

    # Tính %CPU dựa trên utime+stime (jiffies từ kernel timer)
    # Trong kernel, jiffies là đơn vị thời gian cơ bản (thường 4ms = 250Hz)
    utime = int(stat.get("utime", 0))
    stime = int(stat.get("stime", 0))
    total_cpu = utime + stime

    # %RAM dựa trên RSS (Resident Set Size) — số trang vật lý
    # Mỗi trang = 4096 bytes trên hầu hết kiến trúc
    rss_pages = int(stat.get("rss", 0))
    rss_bytes = rss_pages * 4096

    # Đọc /proc/meminfo để tính %RAM
    mem_info = parse_mem_info(read_proc_file("/proc/meminfo"))
    mem_total_kb = 0
    for line_val in mem_info.get("MemTotal", "").split():
        try:
            mem_total_kb = int(line_val)
            break
        except ValueError:
            continue

    mem_percent = 0.0
    if mem_total_kb > 0:
        mem_percent = round(rss_bytes / 1024 / mem_total_kb * 100, 1)

    # Lấy PPID
    ppid = int(stat.get("ppid", 0))

    # Xác định trạng thái process
    # Các trạng thái kernel: include/linux/sched.h
    # R (TASK_RUNNING), S (TASK_INTERRUPTIBLE), D (TASK_UNINTERRUPTIBLE),
    # Z (EXIT_ZOMBIE), T (TASK_STOPPED), t (TASK_TRACED)
    state_code = stat.get("state", "?")
    state_map = {
        "R": "Running", "S": "Sleeping", "D": "Waiting",
        "Z": "Zombie", "T": "Stopped", "t": "Traced",
    }
    state = state_map.get(state_code, state_code)

    # Số luồng (threads)
    threads = int(stat.get("num_threads", 0))

    # Độ ưu tiên (nice value)
    nice = int(stat.get("nice", 0))

    # Đọc /proc/[PID]/exe (symlink đến executable)
    exe = ""
    try:
        exe = os.readlink(f"/proc/{pid}/exe")
    except (OSError, PermissionError):
        pass

    return {
        "pid": pid,
        "ppid": ppid,
        "name": status.get("Name", stat.get("comm", "")),
        "state": state,
        "state_code": state_code,
        "username": username,
        "uid": uid,
        "cpu_time": total_cpu,
        "cpu_percent": 0.0,  # Được tính ở monitor layer
        "rss_bytes": rss_bytes,
        "mem_percent": mem_percent,
        "vsize": int(stat.get("vsize", 0)),
        "threads": threads,
        "nice": nice,
        "priority": int(stat.get("priority", 0)),
        "cmdline": cmdline if cmdline else status.get("Name", ""),
        "exe": exe,
    }


def get_process_detail(pid: int) -> dict:
    """
    Lấy thông tin chi tiết process từ /proc/[PID]/status.
    Dùng để hiển thị trong dialog detail.
    """
    status = parse_proc_status(read_proc_file(f"/proc/{pid}/status"))
    detail_lines = []

    # Đọc thông tin memory maps từ /proc/[PID]/smaps (nếu có quyền)
    # smaps chứa thông tin chi tiết về vùng nhớ ảo (VMA)
    # do kernel duy trì trong struct vm_area_struct
    for key, label in [
        ("Name", "Name"),
        ("State", "State"),
        ("Pid", "PID"),
        ("PPid", "PPID"),
        ("Uid", "UID"),
        ("Gid", "GID"),
        ("VmPeak", "Peak VM"),
        ("VmSize", "VM Size"),
        ("VmLck", "Locked VM"),
        ("VmRSS", "RSS"),
        ("VmData", "Data VM"),
        ("VmStk", "Stack VM"),
        ("VmExe", "Exec VM"),
        ("VmLib", "Library VM"),
        ("Threads", "Threads"),
        ("voluntary_ctxt_switches", "Voluntary Ctxt Switches"),
        ("nonvoluntary_ctxt_switches", "Involuntary Ctxt Switches"),
    ]:
        val = status.get(key, "")
        if val:
            detail_lines.append(f"{label}: {val}")

    # Đọc environment
    try:
        env = read_proc_file(f"/proc/{pid}/environ")
        if env:
            env_vars = [e for e in env.split("\x00") if "=" in e][:10]
            if env_vars:
                detail_lines.append("")
                detail_lines.append("Environment (first 10):")
                for e in env_vars:
                    detail_lines.append(f"  {e}")
    except Exception:
        pass

    return detail_lines


def get_process_fds(pid: int) -> list[dict]:
    """
    Đọc danh sách file descriptor từ /proc/[PID]/fd/.
    
    Mỗi process có bảng file descriptor (struct file **fdtab trong
    task_struct.files). Kernel quản lý các fd qua struct fdtable.
    
    Trong /proc/[PID]/fd/, mỗi symlink tương ứng một fd đang mở,
    trỏ đến đường dẫn thực tế (file, socket, pipe, ...).
    """
    fds = []
    fd_dir = f"/proc/{pid}/fd"
    try:
        for entry in os.listdir(fd_dir):
            fd_num = int(entry)
            try:
                target = os.readlink(os.path.join(fd_dir, entry))
                fds.append({"fd": fd_num, "target": target})
            except OSError:
                fds.append({"fd": fd_num, "target": "?"})
    except (PermissionError, FileNotFoundError, ProcessLookupError):
        pass
    return sorted(fds, key=lambda x: x["fd"])


def get_cpu_count() -> int:
    """Lấy số CPU core từ /proc/cpuinfo."""
    try:
        return os.cpu_count() or 1
    except Exception:
        return 1


def get_all_processes() -> list[dict]:
    """Lấy thông tin tất cả process, có kèm %CPU và %Memory."""
    pids = list_all_pids()
    processes = []
    # Lấy thông tin CPU (jiffies) để tính %CPU
    # Đọc /proc/stat để lấy tổng thời gian CPU
    cpu_jiffies_total = 0
    try:
        stat_content = read_proc_file("/proc/stat")
        for line in stat_content.splitlines():
            if line.startswith("cpu "):
                parts = line.split()
                cpu_jiffies_total = sum(int(x) for x in parts[1:])
                break
    except Exception:
        pass

    for pid in pids:
        try:
            info = get_process_info(pid)
            if info:
                # Tính %CPU = (process_jiffies / total_jiffies) * 100
                if cpu_jiffies_total > 0 and info.get("cpu_time", 0) > 0:
                    cpu_pct = round(info["cpu_time"] / cpu_jiffies_total * 100, 1)
                    info["cpu_percent"] = min(cpu_pct, 100.0)
                processes.append(info)
        except Exception:
            continue
    return processes


def get_system_summary() -> dict:
    """Tổng kết hệ thống: số process, CPU, memory."""
    pids = list_all_pids()
    total = len(pids)
    running = sleeping = zombie = 0
    total_rss = 0

    for pid in pids:
        try:
            info = get_process_info(pid)
            if not info:
                continue
            state_code = info.get("state_code", "")
            if state_code == "R":
                running += 1
            elif state_code in ("S", "D"):
                sleeping += 1
            elif state_code == "Z":
                zombie += 1
            total_rss += info.get("rss_bytes", 0)
        except Exception:
            continue

    # Đọc /proc/meminfo cho tổng RAM
    mem_info = parse_mem_info(read_proc_file("/proc/meminfo"))
    mem_total_kb = 0
    for val in mem_info.get("MemTotal", "").split():
        try:
            mem_total_kb = int(val)
            break
        except ValueError:
            continue

    mem_total_bytes = mem_total_kb * 1024
    mem_percent = round(total_rss / mem_total_bytes * 100, 1) if mem_total_bytes > 0 else 0

    # CPU percent từ /proc/stat (delta giữa 2 lần đọc)
    cpu_percent = 0.0
    try:
        stat_content = read_proc_file("/proc/stat")
        for line in stat_content.splitlines():
            if line.startswith("cpu "):
                parts = line.split()
                idle = int(parts[4])
                total_sum = sum(int(x) for x in parts[1:])
                if total_sum > 0:
                    cpu_percent = round((1 - idle / total_sum) * 100, 1)
                break
    except Exception:
        pass

    return {
        "total": total,
        "running": running,
        "sleeping": sleeping,
        "zombie": zombie,
        "cpu_percent": cpu_percent,
        "memory_percent": mem_percent,
        "total_rss": total_rss,
        "total_mem": mem_total_bytes,
    }


def send_signal_to_process(pid: int, sig: int = 9) -> bool:
    """Gửi signal đến process bằng os.kill (wrapper cho kill(2) system call)."""
    try:
        os.kill(pid, sig)
        return True
    except (ProcessLookupError, PermissionError):
        return False
