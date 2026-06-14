"""
Process Tab — hiển thị danh sách process với real-time monitoring.

Kiến trúc:
  - /proc/[PID]/status: trạng thái process (tên, state, memory)
  - /proc/[PID]/stat: thông tin scheduling (CPU time, nice)
  - /proc/[PID]/io: I/O stats (read/write bytes)
  - /proc/[PID]/fd/: file descriptors (socket, file handles)
  - /proc/[PID]/cmdline: command line arguments
"""

import os
import signal
import time
from datetime import datetime

from PyQt6.QtCore import Qt, QTimer, QThread, pyqtSignal
from PyQt6.QtGui import QFont
from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QTableWidget, QTableWidgetItem,
    QPushButton, QLabel, QHeaderView, QAbstractItemView, QSplitter,
    QTextEdit, QGroupBox, QGridLayout, QLineEdit, QFrame, QMessageBox,
    QComboBox,
)

from . import styles
from app.process_monitor import (
    get_all_processes,
    get_process_detail,
    send_signal_to_process,
    get_system_summary,
)
from app.database import record_action


class ProcessMonitorThread(QThread):
    data_ready = pyqtSignal(list)

    def run(self):
        while not self.isInterruptionRequested():
            try:
                processes = get_all_processes()
                self.data_ready.emit(processes)
            except Exception:
                pass
            time.sleep(2)


class ProcessTab(QWidget):
    def __init__(self):
        super().__init__()
        self._processes = []
        self._filtered = []
        self.setup_ui()
        self.start_monitoring()

    def setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(12)

        # ── Header ──
        header = QHBoxLayout()
        title = QLabel("Process Monitor")
        title.setStyleSheet(styles.TITLE_STYLE)
        header.addWidget(title)

        header.addStretch()

        self.filter_input = QLineEdit()
        self.filter_input.setPlaceholderText("🔍 Filter by name or PID...")
        self.filter_input.setStyleSheet(styles.INPUT_STYLE)
        self.filter_input.setMaximumWidth(280)
        self.filter_input.textChanged.connect(self._filter_processes)
        header.addWidget(self.filter_input)

        self.kill_btn = QPushButton("✕ Kill Process")
        self.kill_btn.setStyleSheet(styles.BTN_DANGER)
        self.kill_btn.clicked.connect(self._kill_selected)
        header.addWidget(self.kill_btn)

        self.refresh_btn = QPushButton("↻ Refresh")
        self.refresh_btn.setStyleSheet(styles.BTN_PRIMARY)
        self.refresh_btn.clicked.connect(self._force_refresh)
        header.addWidget(self.refresh_btn)

        layout.addLayout(header)

        # ── Summary cards ──
        summary = self._build_summary_cards()
        layout.addWidget(summary)

        # ── Process table ──
        self.table = QTableWidget()
        self.table.setStyleSheet(styles.TABLE_STYLE)
        self.table.setAlternatingRowColors(True)
        self.table.setSelectionBehavior(QAbstractItemView.SelectionBehavior.SelectRows)
        self.table.setSelectionMode(QAbstractItemView.SelectionMode.SingleSelection)
        self.table.setEditTriggers(QAbstractItemView.EditTrigger.NoEditTriggers)
        self.table.verticalHeader().setVisible(False)

        columns = [
            ("PID", 70), ("Name", 160), ("State", 80), ("CPU%", 70),
            ("Memory", 80), ("RSS", 80), ("Threads", 60), ("FDs", 50),
            ("User", 80), ("Priority", 60), ("Nice", 50), ("Started", 140),
            ("Command", 280),
        ]
        self.table.setColumnCount(len(columns))
        for i, (name, w) in enumerate(columns):
            self.table.setColumnWidth(i, w)
        self.table.setHorizontalHeaderLabels([c[0] for c in columns])
        self.table.horizontalHeader().setStretchLastSection(True)

        self.table.doubleClicked.connect(self._show_process_detail)
        layout.addWidget(self.table, stretch=1)

        # ── Detail panel ──
        self.detail_panel = QTextEdit()
        self.detail_panel.setStyleSheet(styles.TERMINAL_STYLE)
        self.detail_panel.setMaximumHeight(200)
        self.detail_panel.setReadOnly(True)
        layout.addWidget(self.detail_panel)

    def _build_summary_cards(self) -> QFrame:
        frame = QFrame()
        frame.setStyleSheet(f"""
            QFrame {{
                background: {styles.COLORS["bg_secondary"]};
                border: 1px solid {styles.COLORS["border"]};
                border-radius: 10px;
                padding: 12px;
            }}
        """)
        grid = QHBoxLayout(frame)
        grid.setSpacing(20)

        cards = [
            ("Total Processes", "total", "0"),
            ("Running", "running", "0"),
            ("Sleeping", "sleeping", "0"),
            ("Zombie", "zombie", "0"),
            ("CPU Usage", "cpu", "0%"),
            ("Total Memory", "mem", "0 GB"),
        ]
        self._summary_labels = {}
        for label, key, default in cards:
            card = QVBoxLayout()
            val = QLabel(default)
            val.setStyleSheet(f"""
                color: {styles.COLORS["accent"]};
                font-size: 24px;
                font-weight: bold;
            """)
            val.setAlignment(Qt.AlignmentFlag.AlignCenter)
            lbl = QLabel(label)
            lbl.setStyleSheet(f"""
                color: {styles.COLORS["text_secondary"]};
                font-size: 11px;
                font-weight: bold;
                text-transform: uppercase;
            """)
            lbl.setAlignment(Qt.AlignmentFlag.AlignCenter)
            card.addWidget(val)
            card.addWidget(lbl)

            self._summary_labels[key] = val
            grid.addLayout(card)

        return frame

    def start_monitoring(self):
        self._timer = QTimer()
        self._timer.timeout.connect(self._refresh_processes)
        self._timer.start(2000)  # Refresh mỗi 2 giây (real-time)

    def _refresh_processes(self):
        try:
            self._processes = get_all_processes()
            self._filter_processes()
            self._update_summary()
        except Exception as e:
            pass

    def _filter_processes(self):
        q = self.filter_input.text().strip().lower()
        if q:
            self._filtered = [
                p for p in self._processes
                if q in p["name"].lower() or q in str(p["pid"])
            ]
        else:
            self._filtered = list(self._processes)
        self._populate_table()

    def _populate_table(self):
        self.table.setRowCount(len(self._filtered))
        for row, p in enumerate(self._filtered):
            items = [
                p["pid"],
                p["name"],
                p["state"],
                p["cpu_percent"],
                p["mem_percent"],
                self._fmt_mem(p.get("rss_bytes", 0)),
                p["threads"],
                p.get("num_fds", "?"),
                p["username"],
                p["priority"],
                p["nice"],
                p.get("started", ""),
                p.get("cmdline", "")[:80],
            ]
            for col, val in enumerate(items):
                item = QTableWidgetItem(str(val))
                if val == -1 or val == "?" or val == "":
                    item.setText("-")
                if col in (3, 4):  # CPU%, Memory%
                    try:
                        v = float(str(val).replace("%", ""))
                        if v > 50:
                            item.setForeground(self._color(styles.COLORS["danger"]))
                        elif v > 20:
                            item.setForeground(self._color(styles.COLORS["warning"]))
                    except ValueError:
                        pass
                self.table.setItem(row, col, item)

    def _update_summary(self):
        summary = get_system_summary()
        self._summary_labels["total"].setText(str(summary.get("total", 0)))
        self._summary_labels["running"].setText(str(summary.get("running", 0)))
        self._summary_labels["sleeping"].setText(str(summary.get("sleeping", 0)))
        self._summary_labels["zombie"].setText(str(summary.get("zombie", 0)))
        self._summary_labels["cpu"].setText(f"{summary.get('cpu_percent', 0):.1f}%")
        mem = summary.get("memory_percent", 0)
        self._summary_labels["mem"].setText(f"{mem:.1f}%")

    def _fmt_mem(self, bytes_val):
        if bytes_val and bytes_val != -1:
            mb = bytes_val / 1024 / 1024
            if mb < 1024:
                return f"{mb:.1f} MB"
            return f"{mb / 1024:.1f} GB"
        return "-"

    def _color(self, hex_color):
        from PyQt6.QtGui import QColor
        return QColor(hex_color)

    def _kill_selected(self):
        row = self.table.currentRow()
        if row < 0:
            return
        pid = self._filtered[row]["pid"]
        name = self._filtered[row]["name"]

        reply = QMessageBox.warning(
            self, "Kill Process",
            f"Kill {name} (PID {pid})?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.Cancel,
        )
        if reply == QMessageBox.StandardButton.Yes:
            try:
                os.kill(pid, signal.SIGKILL)
                record_action("kill", "process", f"Killed PID {pid} ({name})")
                QMessageBox.information(self, "Done", f"Signal SIGKILL sent to PID {pid}")
                self._refresh_processes()
            except ProcessLookupError:
                QMessageBox.warning(self, "Error", f"Process {pid} not found")
            except PermissionError:
                QMessageBox.warning(self, "Error", "Permission denied")

    def _force_refresh(self):
        self._refresh_processes()

    def _show_process_detail(self, index):
        row = index.row()
        p = self._filtered[row]
        detail = get_process_detail(p["pid"])
        if isinstance(detail, list):
            self.detail_panel.setText("\n".join(detail))
        elif isinstance(detail, dict):
            lines = [f"{k}: {v}" for k, v in detail.items()]
            self.detail_panel.setText("\n".join(lines))
