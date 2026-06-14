"""
File Monitor — thao tác với file system qua system calls.

Sử dụng các system calls của Linux kernel thay vì shell commands:
  - open(2), read(2), write(2): I/O cơ bản
  - stat(2), lstat(2): lấy thông tin file (inode metadata)
  - access(2): kiểm tra quyền truy cập
  - readlink(2): đọc symlink target
  - getdents(2): đọc directory entries (qua os.listdir)

Các khái niệm kernel liên quan:
  - inode: cấu trúc dữ liệu kernel lưu metadata của file trên disk
    (struct inode trong include/linux/fs.h)
  - dentry: directory entry, ánh xạ tên file → inode
    (struct dentry trong include/linux/dcache.h)
  - VFS: Virtual File System — lớp trừu tượng cho phép nhiều
    filesystem (ext4, xfs, tmpfs, procfs) hoạt động đồng nhất
"""

import os
import stat as stat_module
import time
from datetime import datetime
from typing import Optional


def list_directory(path: str) -> list[dict]:
    """
    Liệt kê nội dung thư mục.
    
    Sử dụng os.listdir() (wrapper cho getdents(2) system call).
    getdents(2) đọc struct linux_dirent từ kernel — mỗi dirent
    chứa: inode number, offset, length, type, name.
    """
    entries = []
    try:
        for name in os.listdir(path):
            full_path = os.path.join(path, name)
            try:
                # Sử dụng os.stat (wrapper cho stat(2) system call)
                # stat(2) lấy thông tin từ inode của file
                st = os.stat(full_path)
                entry = _stat_to_entry(name, full_path, st)
                entries.append(entry)
            except PermissionError:
                entries.append({
                    "name": name,
                    "path": full_path,
                    "type": "unknown",
                    "size": 0,
                    "permissions": "?",
                    "owner": "?",
                    "group": "?",
                    "modified": "",
                    "is_dir": False,
                })
    except PermissionError:
        pass
    except FileNotFoundError:
        pass

    # Sắp xếp: thư mục lên trước, theo tên alphabet
    entries.sort(key=lambda e: (not e["is_dir"], e["name"].lower()))
    return entries


def _stat_to_entry(name: str, full_path: str, st: os.stat_result) -> dict:
    """
    Chuyển đổi struct stat thành dictionary.
    
    struct stat do kernel trả về chứa (định nghĩa struct stat trong
    include/uapi/asm-generic/stat.h):
      - st_dev: device ID
      - st_ino: inode number
      - st_mode: file type + permission bits
      - st_nlink: số hard link
      - st_uid / st_gid: owner user/group
      - st_size: kích thước file (bytes)
      - st_atime / st_mtime / st_ctime: access/modify/change time
    """
    # Xác định loại file từ st_mode bits
    # Sử dụng macro POSIX: S_ISDIR, S_ISREG, S_ISLNK, S_ISFIFO, S_ISSOCK, S_ISBLK, S_ISCHR
    mode = st.st_mode
    if stat_module.S_ISDIR(mode):
        file_type = "directory"
    elif stat_module.S_ISREG(mode):
        file_type = "file"
    elif stat_module.S_ISLNK(mode):
        file_type = "symlink"
    elif stat_module.S_ISFIFO(mode):
        file_type = "fifo"
    elif stat_module.S_ISSOCK(mode):
        file_type = "socket"
    elif stat_module.S_ISBLK(mode):
        file_type = "block"
    elif stat_module.S_ISCHR(mode):
        file_type = "char"
    else:
        file_type = "other"

    # Chuyển đổi permission mode bits sang dạng rwx
    perms = ""
    for who in ["USR", "GRP", "OTH"]:
        for what in ["R", "W", "X"]:
            bit = getattr(stat_module, f"S_I{what}{who}")
            perms += what.lower() if (mode & bit) else "-"

    # Lấy username/gid từ /etc/passwd
    import pwd, grp
    try:
        owner = pwd.getpwuid(st.st_uid).pw_name
    except KeyError:
        owner = str(st.st_uid)
    try:
        group = grp.getgrgid(st.st_gid).gr_name
    except KeyError:
        group = str(st.st_gid)

    return {
        "name": name,
        "path": full_path,
        "type": file_type,
        "size": st.st_size,
        "permissions": perms,
        "mode_octal": oct(stat_module.S_IMODE(mode)),
        "owner": owner,
        "group": group,
        "uid": st.st_uid,
        "gid": st.st_gid,
        "modified": datetime.fromtimestamp(st.st_mtime).strftime("%Y-%m-%d %H:%M:%S"),
        "accessed": datetime.fromtimestamp(st.st_atime).strftime("%Y-%m-%d %H:%M:%S"),
        "inode": st.st_ino,
        "nlink": st.st_nlink,
        "is_dir": stat_module.S_ISDIR(mode),
        "is_symlink": stat_module.S_ISLNK(mode),
    }


def get_file_detail(path: str) -> dict:
    """Lấy thông tin chi tiết file."""
    try:
        st = os.stat(path)
        name = os.path.basename(path)
        return _stat_to_entry(name, path, st)
    except (PermissionError, FileNotFoundError):
        return {}


def read_text_file(path: str, max_size: int = 1048576) -> Optional[str]:
    """
    Đọc nội dung file text.
    
    Sử dụng open(2) + read(2) system calls qua Python file API.
    Kernel thực hiện:
      1. path_resolution() — tìm inode từ path
      2. do_sync_read() — đọc từ page cache (hoặc disk nếu cache miss)
      3. copy_to_user() — copy dữ liệu từ kernel space → user space
    """
    try:
        # Kiểm tra kích thước trước khi đọc
        st = os.stat(path)
        if st.st_size > max_size:
            return f"[File too large: {st.st_size} bytes (max {max_size})]"

        with open(path, "r", errors="replace") as f:
            return f.read(100000)  # Giới hạn 100K ký tự
    except (PermissionError, FileNotFoundError, IsADirectoryError) as e:
        return f"[Error: {e}]"


def is_text_file(path: str) -> bool:
    """Kiểm tra file có phải text không (heuristic: không có null byte)."""
    try:
        with open(path, "rb") as f:
            chunk = f.read(4096)
        return b"\x00" not in chunk
    except Exception:
        return False


def watch_file_changes(path: str, callback) -> object:
    """
    Theo dõi thay đổi file bằng polling (stat mtime).
    
    Lý tưởng nhất nên dùng inotify(7) — một kernel subsystem
    cho phép theo dõi file system events mà không cần polling.
    inotify hoạt động bằng cách đăng ký watch descriptor với kernel,
    kernel gửi event vào queue khi có thay đổi.
    
    Do inotify yêu cầu quyền và pyinotify có thể không available,
    ta dùng polling làm fallback.
    """
    class FileWatcher:
        def __init__(self, path, cb):
            self.path = path
            self.callback = cb
            self._last_mtime = 0
            try:
                self._last_mtime = os.stat(path).st_mtime
            except OSError:
                pass

        def check(self) -> bool:
            try:
                mtime = os.stat(self.path).st_mtime
                if mtime != self._last_mtime:
                    self._last_mtime = mtime
                    self.callback(self.path)
                    return True
            except OSError:
                pass
            return False

    return FileWatcher(path, callback)


def format_file_size(size_bytes: int) -> str:
    """Định dạng kích thước file (bytes → KB, MB, GB)."""
    if size_bytes < 1024:
        return f"{size_bytes} B"
    elif size_bytes < 1024 ** 2:
        return f"{size_bytes / 1024:.1f} KB"
    elif size_bytes < 1024 ** 3:
        return f"{size_bytes / 1024 ** 2:.1f} MB"
    else:
        return f"{size_bytes / 1024 ** 3:.2f} GB"
