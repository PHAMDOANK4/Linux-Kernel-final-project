"""
Socket Tab — xem danh sách socket từ /proc/net/ và chat qua TCP socket.

Gồm 2 sub-tab:
  - Monitor: đọc /proc/net/{tcp,udp,unix} hiển thị socket table
  - Chat: tạo TCP server / client để chat real-time

Kernel concepts:
  - TCP socket state machine trong include/net/tcp_states.h:
    TCP_ESTABLISHED=1, TCP_LISTEN=10, TCP_TIME_WAIT=6, ...
  - Mỗi socket được định danh bởi tuple {src_ip, src_port, dst_ip, dst_port}
  - struct sock chứa tất cả thông tin: sk_state, sk_uid, sk_rcvbuf, sk_sndbuf
  - accept() tạo socket mới cho mỗi kết nối (fd mới)
"""

from PyQt6.QtCore import Qt, QTimer
from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QTableWidget, QTableWidgetItem,
    QPushButton, QLabel, QHeaderView, QAbstractItemView, QTextEdit,
    QFrame, QComboBox, QTabWidget,
)

from . import styles
from app.socket_monitor import get_tcp_sockets, get_udp_sockets, get_unix_sockets, get_sockets_summary
from .chat_tab import ChatTab


class SocketTab(QWidget):
    def __init__(self):
        super().__init__()
        self.setup_ui()

    def setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)

        self.tabs = QTabWidget()
        self.tabs.setDocumentMode(True)

        self.monitor_tab = _SocketMonitorTab()
        self.tabs.addTab(self.monitor_tab, "Monitor")

        self.chat_tab = ChatTab()
        self.tabs.addTab(self.chat_tab, "Chat")

        layout.addWidget(self.tabs)

    def _refresh_sockets(self):
        self.monitor_tab._refresh_sockets()


class _SocketMonitorTab(QWidget):
    def __init__(self):
        super().__init__()
        self.setup_ui()
        self.start_monitoring()

    def setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(12)

        # Header
        header = QHBoxLayout()
        title = QLabel("Socket Monitor")
        title.setStyleSheet(styles.TITLE_STYLE)
        header.addWidget(title)
        header.addStretch()

        self.filter_combo = QComboBox()
        self.filter_combo.addItems(["All", "TCP", "UDP", "UNIX"])
        self.filter_combo.setStyleSheet(f"""
            QComboBox {{
                background: {styles.COLORS["input_bg"]};
                color: {styles.COLORS["text"]};
                padding: 6px 12px;
                border: 1px solid {styles.COLORS["border"]};
                border-radius: 6px;
            }}
        """)
        self.filter_combo.currentTextChanged.connect(self._refresh_sockets)
        header.addWidget(self.filter_combo)

        self.refresh_btn = QPushButton("↻ Refresh")
        self.refresh_btn.setStyleSheet(styles.BTN_PRIMARY)
        self.refresh_btn.clicked.connect(self._refresh_sockets)
        header.addWidget(self.refresh_btn)

        layout.addLayout(header)

        # Summary
        summary_frame = QFrame()
        summary_frame.setStyleSheet(f"""
            QFrame {{
                background: {styles.COLORS["bg_secondary"]};
                border: 1px solid {styles.COLORS["border"]};
                border-radius: 8px;
                padding: 8px;
            }}
        """)
        summary_layout = QHBoxLayout(summary_frame)
        self.summary_labels = {}
        for label in ("TCP", "UDP", "UNIX", "LISTEN", "ESTABLISHED"):
            lbl = QLabel(f"{label}: 0")
            lbl.setStyleSheet(f"color: {styles.COLORS['text']}; font-size: 12px; font-weight: bold;")
            summary_layout.addWidget(lbl)
            self.summary_labels[label] = lbl
        summary_layout.addStretch()
        layout.addWidget(summary_frame)

        # Table
        self.table = QTableWidget()
        self.table.setStyleSheet(styles.TABLE_STYLE)
        self.table.setAlternatingRowColors(True)
        self.table.setSelectionBehavior(QAbstractItemView.SelectionBehavior.SelectRows)
        self.table.setSelectionMode(QAbstractItemView.SelectionMode.SingleSelection)
        self.table.setEditTriggers(QAbstractItemView.EditTrigger.NoEditTriggers)
        self.table.verticalHeader().setVisible(False)

        columns = [
            ("Protocol", 60), ("State", 80), ("Local Address", 180),
            ("Remote Address", 180), ("UID", 50), ("Inode", 70),
            ("RX Queue", 70), ("TX Queue", 70), ("Path/Peer", 200),
        ]
        self.table.setColumnCount(len(columns))
        for i, (name, w) in enumerate(columns):
            self.table.setColumnWidth(i, w)
        self.table.setHorizontalHeaderLabels([c[0] for c in columns])
        self.table.horizontalHeader().setStretchLastSection(True)
        layout.addWidget(self.table, stretch=1)

    def start_monitoring(self):
        self._timer = QTimer()
        self._timer.timeout.connect(self._refresh_sockets)
        self._timer.start(3000)

    def _refresh_sockets(self):
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

        summary = get_sockets_summary()
        self.summary_labels["TCP"].setText(f"TCP: {summary['total_tcp']}")
        self.summary_labels["UDP"].setText(f"UDP: {summary['total_udp']}")
        self.summary_labels["UNIX"].setText(f"UNIX: {summary['total_unix']}")
        self.summary_labels["LISTEN"].setText(f"LISTEN: {summary['listening_ports']}")
        self.summary_labels["ESTABLISHED"].setText(f"ESTABLISHED: {summary['established']}")

        self.table.setRowCount(len(sockets))
        for row, s in enumerate(sockets):
            items = [
                s.get("protocol", "?"),
                s.get("state", "?"),
                s.get("local", "?"),
                s.get("remote", "?"),
                str(s.get("uid", "?")),
                str(s.get("inode", "?")),
                str(s.get("rx_queue", "?")),
                str(s.get("tx_queue", "?")),
                s.get("path", s.get("peer", "")),
            ]
            for col, val in enumerate(items):
                item = QTableWidgetItem(val)
                if s.get("state") == "LISTEN":
                    item.setForeground(self._color(styles.COLORS["success"]))
                elif s.get("state") == "ESTABLISHED":
                    item.setForeground(self._color(styles.COLORS["accent"]))
                self.table.setItem(row, col, item)

    def _color(self, hex_color):
        from PyQt6.QtGui import QColor
        return QColor(hex_color)
