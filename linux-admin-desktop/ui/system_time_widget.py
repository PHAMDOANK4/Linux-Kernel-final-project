from datetime import datetime

from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QDateTimeEdit,
    QPushButton, QTextEdit, QMessageBox, QFrame, QComboBox,
    QCompleter,
)
from PyQt6.QtCore import Qt, QTimer
from PyQt6.QtGui import QFont

from app.executor import ScriptExecutor
from app.logging import logger
import pytz


CARD_STYLE = """
    QFrame {{
        background: white;
        border-radius: 12px;
        border: 1px solid #e2e8f0;
        padding: {padding};
    }}
"""

BTN_PRIMARY = """
    QPushButton {{
        background: {bg}; color: white;
        padding: 8px 18px; border-radius: 6px;
        font-weight: bold; font-size: 12px;
    }}
    QPushButton:hover {{ background: {hover}; }}
"""


def _parse_timedatectl(output: str) -> dict:
    info = {"timezone": "", "ntp": ""}
    for line in output.splitlines():
        line = line.strip()
        if line.startswith("Time zone:"):
            info["timezone"] = line.replace("Time zone:", "").strip()
        elif line.startswith("NTP service:"):
            info["ntp"] = line.replace("NTP service:", "").strip()
    return info


class SystemTimeWidget(QWidget):
    def __init__(self, auth_manager):
        super().__init__()
        self.auth = auth_manager
        self.executor = ScriptExecutor()
        self._status = {"timezone": "", "ntp": ""}
        self._setup_ui()
        self._refresh_clock()
        self._refresh_status()

        self._clock_timer = QTimer()
        self._clock_timer.timeout.connect(self._refresh_clock)
        self._clock_timer.start(1000)

        self._status_timer = QTimer()
        self._status_timer.timeout.connect(self._refresh_status)
        self._status_timer.start(30000)

    def _setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(24, 24, 24, 24)
        layout.setSpacing(16)

        title = QLabel("System Time")
        title.setFont(QFont("", 20, QFont.Weight.Bold))
        title.setStyleSheet("color: #1f2933;")
        layout.addWidget(title)

        clock_card = QFrame()
        clock_card.setStyleSheet("""
            QFrame {
                background: qlineargradient(x1:0, y1:0, x2:1, y2:1,
                    stop:0 #0f172a, stop:1 #1e293b);
                border-radius: 16px;
                padding: 28px 32px;
            }
        """)
        clock_layout = QVBoxLayout()
        clock_layout.setSpacing(4)

        self.time_display = QLabel()
        self.time_display.setFont(QFont("monospace", 44, QFont.Weight.Bold))
        self.time_display.setStyleSheet("color: #38bdf8;")
        self.time_display.setAlignment(Qt.AlignmentFlag.AlignCenter)
        clock_layout.addWidget(self.time_display)

        self.date_display = QLabel()
        self.date_display.setFont(QFont("", 14))
        self.date_display.setStyleSheet("color: #94a3b8;")
        self.date_display.setAlignment(Qt.AlignmentFlag.AlignCenter)
        clock_layout.addWidget(self.date_display)

        badge_row = QHBoxLayout()
        badge_row.setAlignment(Qt.AlignmentFlag.AlignCenter)
        badge_row.setSpacing(8)

        self.tz_badge = QLabel()
        self.tz_badge.setStyleSheet("""
            QLabel {
                background: rgba(56, 189, 248, 0.15);
                color: #7dd3fc; padding: 3px 12px;
                border-radius: 10px; font-size: 11px;
                font-weight: bold;
            }
        """)
        badge_row.addWidget(self.tz_badge)

        self.ntp_badge = QLabel()
        self.ntp_badge.setStyleSheet("""
            QLabel {
                background: rgba(74, 222, 128, 0.15);
                color: #86efac; padding: 3px 12px;
                border-radius: 10px; font-size: 11px;
                font-weight: bold;
            }
        """)
        badge_row.addWidget(self.ntp_badge)

        clock_layout.addLayout(badge_row)
        clock_card.setLayout(clock_layout)
        layout.addWidget(clock_card)

        if self.auth.is_admin:
            controls_layout = QHBoxLayout()
            controls_layout.setSpacing(16)

            controls_layout.addWidget(self._make_time_card(), 1)
            controls_layout.addWidget(self._make_tz_card(), 1)
            layout.addLayout(controls_layout)

            layout.addWidget(self._make_ntp_card())

        self.output = QTextEdit()
        self.output.setReadOnly(True)
        self.output.setMaximumHeight(120)
        self.output.setStyleSheet("""
            QTextEdit {
                background: #111827; color: #f8fafc;
                border-radius: 8px; padding: 10px;
                font-family: monospace; font-size: 12px;
            }
        """)
        layout.addWidget(self.output)

    def _card(self, title_text):
        card = QFrame()
        card.setStyleSheet(CARD_STYLE.format(padding="16px"))
        card_layout = QVBoxLayout(card)
        card_layout.setContentsMargins(16, 12, 16, 16)
        card_layout.setSpacing(10)

        lbl = QLabel(title_text)
        lbl.setFont(QFont("", 12, QFont.Weight.Bold))
        lbl.setStyleSheet("color: #334155; border: none;")
        card_layout.addWidget(lbl)

        return card, card_layout

    def _make_time_card(self):
        card, card_layout = self._card("Set Date & Time")

        self.datetime_input = QDateTimeEdit()
        self.datetime_input.setDateTime(datetime.now())
        self.datetime_input.setDisplayFormat("yyyy-MM-dd HH:mm:ss")
        self.datetime_input.setCalendarPopup(True)
        self.datetime_input.setStyleSheet("""
            QDateTimeEdit {
                padding: 8px; border: 2px solid #e2e8f0;
                border-radius: 6px; font-size: 13px;
            }
            QDateTimeEdit:focus { border-color: #0b7285; }
        """)
        card_layout.addWidget(self.datetime_input)

        row = QHBoxLayout()
        row.addStretch()
        set_btn = QPushButton("Set Time")
        set_btn.setStyleSheet(BTN_PRIMARY.format(bg="#0b7285", hover="#1565c0"))
        set_btn.clicked.connect(self._set_time)
        row.addWidget(set_btn)
        card_layout.addLayout(row)

        return card

    def _make_tz_card(self):
        card, card_layout = self._card("Timezone")

        self.tz_combo = QComboBox()
        self.tz_combo.setEditable(True)
        self.tz_combo.setInsertPolicy(QComboBox.InsertPolicy.NoInsert)
        self.tz_combo.setStyleSheet("""
            QComboBox {
                padding: 8px; border: 2px solid #e2e8f0;
                border-radius: 6px; font-size: 13px;
            }
            QComboBox:focus { border-color: #0b7285; }
            QComboBox::drop-down {
                border: none; width: 30px;
            }
            QComboBox QAbstractItemView {
                padding: 4px;
                min-width: 280px;
            }
            QComboBox QAbstractItemView::item {
                padding: 4px 8px;
            }
        """)

        groups: dict[str, list[str]] = {}
        for tz in pytz.common_timezones:
            parts = tz.split("/", 1)
            region = parts[0] if len(parts) > 1 else "Other"
            groups.setdefault(region, []).append(tz)

        all_items: list[str] = []
        for region in sorted(groups):
            header = f"── {region} ──"
            self.tz_combo.addItem(header)
            all_items.append(header)
            for tz in sorted(groups[region]):
                self.tz_combo.addItem(f"    {tz}")
                all_items.append(f"    {tz}")

        completer = QCompleter(all_items, self)
        completer.setCaseSensitivity(Qt.CaseSensitivity.CaseInsensitive)
        completer.setFilterMode(Qt.MatchFlag.MatchContains)
        self.tz_combo.setCompleter(completer)

        card_layout.addWidget(self.tz_combo)

        row = QHBoxLayout()
        row.addStretch()
        set_tz_btn = QPushButton("Set Timezone")
        set_tz_btn.setStyleSheet(BTN_PRIMARY.format(bg="#f59e0b", hover="#d97706"))
        set_tz_btn.clicked.connect(self._set_timezone)
        row.addWidget(set_tz_btn)
        card_layout.addLayout(row)

        return card

    def _make_ntp_card(self):
        card = QFrame()
        card.setStyleSheet(CARD_STYLE.format(padding="12px 16px"))
        card_layout = QVBoxLayout(card)
        card_layout.setContentsMargins(16, 12, 16, 16)
        card_layout.setSpacing(10)

        lbl = QLabel("NTP Synchronization")
        lbl.setFont(QFont("", 12, QFont.Weight.Bold))
        lbl.setStyleSheet("color: #334155; border: none;")
        card_layout.addWidget(lbl)

        btn_row = QHBoxLayout()
        btn_row.setSpacing(10)

        enable_btn = QPushButton("Enable")
        enable_btn.setStyleSheet(BTN_PRIMARY.format(bg="#10b981", hover="#059669"))
        enable_btn.clicked.connect(lambda: self._run_time_script("enable_ntp.sh"))
        btn_row.addWidget(enable_btn)

        disable_btn = QPushButton("Disable")
        disable_btn.setStyleSheet(BTN_PRIMARY.format(bg="#ef4444", hover="#dc2626"))
        disable_btn.clicked.connect(lambda: self._run_time_script("disable_ntp.sh"))
        btn_row.addWidget(disable_btn)

        sync_btn = QPushButton("Sync Now")
        sync_btn.setStyleSheet(BTN_PRIMARY.format(bg="#6366f1", hover="#4f46e5"))
        sync_btn.clicked.connect(lambda: self._run_time_script("sync_time.sh"))
        btn_row.addWidget(sync_btn)

        btn_row.addStretch()
        card_layout.addLayout(btn_row)

        return card

    def on_activate(self):
        self._refresh_clock()
        self._refresh_status()

    def _refresh_clock(self):
        now = datetime.now()
        self.time_display.setText(now.strftime("%H:%M:%S"))
        self.date_display.setText(now.strftime("%A, %d %B %Y"))

    def _select_tz_in_combo(self, tz_name: str):
        for i in range(self.tz_combo.count()):
            item = self.tz_combo.itemText(i).strip()
            if item == tz_name:
                self.tz_combo.setCurrentIndex(i)
                return

    def _refresh_status(self):
        success, output = self.executor.run("show_time.sh")
        if success:
            info = _parse_timedatectl(output)
            self._status = info
            if info["timezone"]:
                self.tz_badge.setText(f"  {info['timezone']}  ")
                self._select_tz_in_combo(info["timezone"])
            if info["ntp"]:
                active = info["ntp"] == "active"
                self.ntp_badge.setText(f"  NTP: {'ON' if active else 'OFF'}  ")
                color = "#86efac" if active else "#fca5a5"
                bg = "rgba(74, 222, 128, 0.15)" if active else "rgba(248, 113, 113, 0.15)"
                self.ntp_badge.setStyleSheet(f"""
                    QLabel {{
                        background: {bg};
                        color: {color}; padding: 3px 12px;
                        border-radius: 10px; font-size: 11px;
                        font-weight: bold;
                    }}
                """)

    def _log_action(self, action, success, detail):
        logger.log(self.auth.username, f"time:{action}", success, detail)

    def _run_time_script(self, script_name, args=None):
        self.output.append(f"$ {script_name} {' '.join(args or [])}\n")
        success, output = self.executor.run(script_name, args)
        if success:
            self.output.append(f"✓ {output}\n")
        else:
            self.output.append(f"✗ {output}\n")
        self._refresh_clock()
        self._refresh_status()

    def _set_time(self):
        dt = self.datetime_input.dateTime().toPyDateTime()
        new_time = dt.strftime("%Y-%m-%d %H:%M:%S")
        self._run_time_script("set_time.sh", [new_time])

    def _set_timezone(self):
        raw = self.tz_combo.currentText()
        tz = raw.strip()
        if not tz or tz.startswith("──"):
            QMessageBox.warning(self, "Error", "Please select a valid timezone (not a group header).")
            return
        self._run_time_script("set_timezone.sh", [tz])
