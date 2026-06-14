"""
Main Window — cửa sổ chính của Ubuntu Monitor Desktop.

Kiến trúc giao diện:
  - QTabWidget với 4 tab chính:
      1. Process  — process monitor (/proc/[PID]/)
      2. File     — file browser (VFS + stat)
      3. Socket   — socket listing (/proc/net/)
      4. Network  — network stats (/proc/net/dev + /sys/class/net/)
  - Dark theme với accent xanh dương
  - Real-time refresh (2-3 giây) qua QTimer
"""

import sys
import os

from PyQt6.QtCore import Qt
from PyQt6.QtGui import QFont, QAction, QIcon
from PyQt6.QtWidgets import (
    QApplication, QMainWindow, QTabWidget, QMenuBar, QStatusBar,
    QLabel, QMessageBox, QVBoxLayout, QWidget,
)

from ui.styles import COLORS, TAB_STYLE, SCROLLBAR_STYLE
from ui.process_tab import ProcessTab
from ui.file_tab import FileTab
from ui.socket_tab import SocketTab
from ui.network_tab import NetworkTab


APP_STYLE = f"""
    QMainWindow {{
        background: {COLORS["bg"]};
    }}
    QWidget {{
        background: {COLORS["bg"]};
        color: {COLORS["text"]};
        font-family: 'Segoe UI', 'Ubuntu', 'Noto Sans', sans-serif;
    }}
    QStatusBar {{
        background: {COLORS["bg_secondary"]};
        color: {COLORS["text_secondary"]};
        border-top: 1px solid {COLORS["border"]};
        font-size: 11px;
    }}
    QMenuBar {{
        background: {COLORS["bg_secondary"]};
        color: {COLORS["text_secondary"]};
        border-bottom: 1px solid {COLORS["border"]};
        font-size: 12px;
    }}
    QMenuBar::item:selected {{
        background: {COLORS["accent_light"]};
        color: {COLORS["text"]};
    }}
    QMenu {{
        background: {COLORS["surface"]};
        color: {COLORS["text"]};
        border: 1px solid {COLORS["border"]};
        padding: 4px;
    }}
    QMenu::item:selected {{
        background: {COLORS["accent_light"]};
    }}
    QGroupBox {{
        border: 1px solid {COLORS["border"]};
        border-radius: 8px;
        margin-top: 12px;
        padding: 16px;
        font-weight: bold;
        font-size: 12px;
        color: {COLORS["text_secondary"]};
    }}
    QGroupBox::title {{
        subcontrol-origin: margin;
        left: 12px;
        padding: 0 6px;
    }}
    {TAB_STYLE}
    {SCROLLBAR_STYLE}
"""


class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Ubuntu Monitor Desktop — Linux Kernel Learning Tool")
        self.setMinimumSize(1200, 750)
        self.resize(1400, 850)

        # Center window
        self._center_window()

        # Setup UI
        self._setup_menu()
        self._setup_tabs()
        self._setup_statusbar()

        # Apply global stylesheet
        self.setStyleSheet(APP_STYLE)

    def _center_window(self):
        screen = QApplication.primaryScreen()
        if screen:
            center = screen.availableGeometry().center()
            self.move(int(center.x() - self.width() / 2),
                      int(center.y() - self.height() / 2))

    def _setup_menu(self):
        menubar = self.menuBar()

        # File menu
        file_menu = menubar.addMenu("File")
        refresh_action = QAction("Refresh All", self)
        refresh_action.setShortcut("Ctrl+R")
        refresh_action.triggered.connect(self._refresh_all)
        file_menu.addAction(refresh_action)
        file_menu.addSeparator()
        exit_action = QAction("Exit", self)
        exit_action.setShortcut("Ctrl+Q")
        exit_action.triggered.connect(self.close)
        file_menu.addAction(exit_action)

        # View menu
        view_menu = menubar.addMenu("View")
        for i, name in enumerate(["Process", "File", "Socket", "Network"]):
            act = QAction(f"{name} Tab", self)
            act.setShortcut(f"Ctrl+{i+1}")
            act.triggered.connect(lambda checked, idx=i: self.tabs.setCurrentIndex(idx))
            view_menu.addAction(act)

        # Help menu
        help_menu = menubar.addMenu("Help")
        about_action = QAction("About", self)
        about_action.triggered.connect(self._show_about)
        help_menu.addAction(about_action)

    def _setup_tabs(self):
        self.tabs = QTabWidget()
        self.tabs.setDocumentMode(True)
        self.tabs.setTabPosition(QTabWidget.TabPosition.North)

        self.process_tab = ProcessTab()
        self.file_tab = FileTab()
        self.socket_tab = SocketTab()
        self.network_tab = NetworkTab()

        self.tabs.addTab(self.process_tab, "📊 Process")
        self.tabs.addTab(self.file_tab, "📁 File")
        self.tabs.addTab(self.socket_tab, "🔌 Socket")
        self.tabs.addTab(self.network_tab, "🌐 Network")

        self.setCentralWidget(self.tabs)

    def _setup_statusbar(self):
        self.status = QStatusBar()
        self.status_label = QLabel("Ready | Monitoring /proc in real-time")
        self.status_label.setStyleSheet(f"color: {COLORS['text_secondary']}; padding: 2px 8px;")
        self.status.addWidget(self.status_label)
        self.setStatusBar(self.status)

    def _refresh_all(self):
        self.process_tab._refresh_processes()
        self.socket_tab._refresh_sockets()
        self.network_tab._refresh_all()
        self.status.showMessage("Refreshed all data", 3000)

    def _show_about(self):
        QMessageBox.about(
            self,
            "About Ubuntu Monitor Desktop",
            "Ubuntu Monitor Desktop\n\n"
            "A Linux Kernel Learning Tool\n\n"
            "Key concepts demonstrated:\n"
            "  • /proc filesystem — process, memory, network info\n"
            "  • System calls — stat(2), open(2), read(2), kill(2)\n"
            "  • Kernel data structures — task_struct, sock, net_device\n"
            "  • VFS — virtual file system abstraction\n"
            "  • procfs — dynamic kernel-to-userspace communication\n\n"
            "Built with Python + PyQt6\n"
            "License: MIT",
        )
