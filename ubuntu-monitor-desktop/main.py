#!/usr/bin/env python3
"""
Ubuntu Monitor Desktop — Linux Kernel Learning Tool

Entry point. Khởi động ứng dụng PyQt6 với giao diện monitor
sử dụng /proc filesystem và system calls thay vì shell commands.

Các khái niệm kernel được trình bày:
  - procfs: /proc/[PID]/, /proc/net/, /proc/stat, /proc/meminfo
  - sysfs: /sys/class/net/
  - System calls: stat(2), open(2), read(2), kill(2), access(2)
  - Kernel data structures: task_struct, sock, net_device, inode, dentry
"""

import sys
import os

# Thêm thư mục cha vào PYTHONPATH
sys.path.insert(0, os.path.abspath(os.path.dirname(__file__)))

from PyQt6.QtWidgets import QApplication
from PyQt6.QtGui import QFont

from ui.main_window import MainWindow
from app.database import init_db


def main():
    # Khởi tạo database (nếu cần)
    init_db()

    # Tạo application
    app = QApplication(sys.argv)
    app.setApplicationName("Ubuntu Monitor Desktop")

    # Font mặc định
    font = QFont("Segoe UI", 10)
    if not QFont(font).exactMatch():
        font = QFont("Ubuntu", 10)
    app.setFont(font)

    # Tạo và hiển thị main window
    window = MainWindow()
    window.show()

    sys.exit(app.exec())


if __name__ == "__main__":
    main()
