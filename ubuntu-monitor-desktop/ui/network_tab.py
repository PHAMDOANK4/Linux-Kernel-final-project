"""
Network Tab — giám sát network interface và routing.

Sử dụng /proc/net/dev và /sys/class/net/ để lấy:
  - Thống kê RX/TX bytes, packets, errors, drops
  - Tốc độ truyền/nhận real-time
  - Trạng thái link (carrier, speed, duplex)
  - Bảng định tuyến
"""

from PyQt6.QtCore import Qt, QTimer, QThread, pyqtSignal
from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QTableWidget, QTableWidgetItem,
    QPushButton, QLabel, QHeaderView, QAbstractItemView, QTextEdit,
    QFrame, QGroupBox, QGridLayout, QTabWidget, QLineEdit, QMessageBox,
)

from . import styles
from app.network_monitor import (
    get_interface_stats,
    get_route_table,
    get_ip_addresses,
    ping_host,
    get_traffic_snapshot,
    calculate_speed,
    format_speed,
)


class NetworkTab(QWidget):
    def __init__(self):
        super().__init__()
        self._traffic_before = {}
        self.setup_ui()
        self.start_monitoring()

    def setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(12)

        # Header
        header = QHBoxLayout()
        title = QLabel("Network Monitor")
        title.setStyleSheet(styles.TITLE_STYLE)
        header.addWidget(title)
        header.addStretch()
        self.refresh_btn = QPushButton("↻ Refresh")
        self.refresh_btn.setStyleSheet(styles.BTN_PRIMARY)
        self.refresh_btn.clicked.connect(self._refresh_all)
        header.addWidget(self.refresh_btn)
        layout.addLayout(header)

        # Sub-tabs
        self.tabs = QTabWidget()
        self.tabs.setStyleSheet(styles.TAB_STYLE)
        layout.addWidget(self.tabs, stretch=1)

        # ── Interface tab ──
        iface_tab = QWidget()
        iface_layout = QVBoxLayout(iface_tab)
        self.iface_table = QTableWidget()
        self.iface_table.setStyleSheet(styles.TABLE_STYLE)
        self.iface_table.setAlternatingRowColors(True)
        self.iface_table.setSelectionBehavior(QAbstractItemView.SelectionBehavior.SelectRows)
        self.iface_table.setEditTriggers(QAbstractItemView.EditTrigger.NoEditTriggers)
        self.iface_table.verticalHeader().setVisible(False)
        iface_columns = [
            ("Interface", 100), ("RX Bytes", 90), ("TX Bytes", 90),
            ("RX Packets", 90), ("TX Packets", 90), ("RX Errors", 80),
            ("TX Errors", 80), ("RX Drop", 70), ("TX Drop", 70),
            ("RX Speed", 90), ("TX Speed", 90),
        ]
        self.iface_table.setColumnCount(len(iface_columns))
        for i, (name, w) in enumerate(iface_columns):
            self.iface_table.setColumnWidth(i, w)
        self.iface_table.setHorizontalHeaderLabels([c[0] for c in iface_columns])
        self.iface_table.horizontalHeader().setStretchLastSection(True)
        iface_layout.addWidget(self.iface_table)
        self.tabs.addTab(iface_tab, "Interfaces")

        # ── Route tab ──
        route_tab = QWidget()
        route_layout = QVBoxLayout(route_tab)
        self.route_table = QTableWidget()
        self.route_table.setStyleSheet(styles.TABLE_STYLE)
        self.route_table.setAlternatingRowColors(True)
        self.route_table.setEditTriggers(QAbstractItemView.EditTrigger.NoEditTriggers)
        self.route_table.verticalHeader().setVisible(False)
        route_columns = [
            ("Interface", 80), ("Destination", 130), ("Gateway", 130),
            ("Mask", 130), ("Flags", 60), ("Metric", 60),
        ]
        self.route_table.setColumnCount(len(route_columns))
        for i, (name, w) in enumerate(route_columns):
            self.route_table.setColumnWidth(i, w)
        self.route_table.setHorizontalHeaderLabels([c[0] for c in route_columns])
        self.route_table.horizontalHeader().setStretchLastSection(True)
        route_layout.addWidget(self.route_table)
        self.tabs.addTab(route_tab, "Routing")

        # ── Ping tab ──
        ping_tab = QWidget()
        ping_layout = QVBoxLayout(ping_tab)

        ping_input_layout = QHBoxLayout()
        self.ping_input = QLineEdit()
        self.ping_input.setPlaceholderText("Enter hostname or IP...")
        self.ping_input.setStyleSheet(styles.INPUT_STYLE)
        self.ping_input.returnPressed.connect(self._execute_ping)
        ping_input_layout.addWidget(self.ping_input, stretch=1)

        self.ping_btn = QPushButton("Ping")
        self.ping_btn.setStyleSheet(styles.BTN_SUCCESS)
        self.ping_btn.clicked.connect(self._execute_ping)
        ping_input_layout.addWidget(self.ping_btn)
        ping_layout.addLayout(ping_input_layout)

        self.ping_output = QTextEdit()
        self.ping_output.setStyleSheet(styles.TERMINAL_STYLE)
        self.ping_output.setReadOnly(True)
        ping_layout.addWidget(self.ping_output)
        self.tabs.addTab(ping_tab, "Ping")

        self._refresh_all()

    def start_monitoring(self):
        self._traffic_before = get_traffic_snapshot()
        self._timer = QTimer()
        self._timer.timeout.connect(self._refresh_interfaces)
        self._timer.start(3000)

    def _refresh_all(self):
        self._refresh_interfaces()
        self._refresh_routes()

    def _refresh_interfaces(self):
        traffic_after = get_traffic_snapshot()
        speeds = calculate_speed(self._traffic_before, traffic_after, 3.0) if self._traffic_before else {}
        self._traffic_before = traffic_after

        stats = get_interface_stats()
        self.iface_table.setRowCount(len(stats))
        for row, iface in enumerate(stats):
            name = iface["name"]
            speed_info = speeds.get(name, {})
            items = [
                name,
                str(iface.get("rx_bytes", 0)),
                str(iface.get("tx_bytes", 0)),
                str(iface.get("rx_packets", 0)),
                str(iface.get("tx_packets", 0)),
                str(iface.get("rx_errors", 0)),
                str(iface.get("tx_errors", 0)),
                str(iface.get("rx_drop", 0)),
                str(iface.get("tx_drop", 0)),
                format_speed(speed_info.get("rx_speed", 0)),
                format_speed(speed_info.get("tx_speed", 0)),
            ]
            for col, val in enumerate(items):
                item = QTableWidgetItem(val)
                # Highlight lo (loopback)
                if name == "lo":
                    item.setForeground(self._color(styles.COLORS["text_muted"]))
                self.iface_table.setItem(row, col, item)

    def _refresh_routes(self):
        routes = get_route_table()
        self.route_table.setRowCount(len(routes))
        for row, r in enumerate(routes):
            items = [
                r.get("iface", ""),
                r.get("destination", ""),
                r.get("gateway", ""),
                r.get("mask", ""),
                r.get("flags", ""),
                str(r.get("metric", "")),
            ]
            for col, val in enumerate(items):
                self.route_table.setItem(row, col, QTableWidgetItem(str(val)))

    def _execute_ping(self):
        target = self.ping_input.text().strip()
        if not target:
            return
        self.ping_output.append(f"$ ping -c 4 {target}")
        self.ping_output.append("Pinging... (this may take a moment)")
        results = ping_host(target)
        self.ping_output.clear()
        for line in results:
            self.ping_output.append(line)

    def _color(self, hex_color):
        from PyQt6.QtGui import QColor
        return QColor(hex_color)
