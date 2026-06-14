from datetime import datetime

from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QLineEdit,
    QPushButton, QTextEdit, QMessageBox, QFrame, QGroupBox,
    QFormLayout, QTimeEdit, QDateEdit, QComboBox,
    QSizePolicy, QSpacerItem,
)
from PyQt6.QtCore import Qt, QTimer
from PyQt6.QtGui import QFont

from app.executor import ScriptExecutor
from app.logging import logger
import pytz


class SystemTimeWidget(QWidget):
    def __init__(self, auth_manager):
        super().__init__()
        self.auth = auth_manager
        self.executor = ScriptExecutor()
        self._setup_ui()
        self._refresh_timer()
        self._timer = QTimer()
        self._timer.timeout.connect(self._refresh_timer)
        self._timer.start(2000)

    def _setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(24, 24, 24, 24)

        title = QLabel("System Time")
        title.setFont(QFont("", 20, QFont.Weight.Bold))
        title.setStyleSheet("color: #1f2933;")
        layout.addWidget(title)

        info_card = QFrame()
        info_card.setStyleSheet("""
            QFrame { background: white; border-radius: 12px;
                padding: 20px; border: 1px solid #e2e8f0; }
        """)
        info_layout = QVBoxLayout()

        self.time_display = QLabel()
        self.time_display.setFont(QFont("monospace", 28, QFont.Weight.Bold))
        self.time_display.setStyleSheet("color: #0b7285;")
        self.time_display.setAlignment(Qt.AlignmentFlag.AlignCenter)
        info_layout.addWidget(self.time_display)

        info_card.setLayout(info_layout)
        layout.addWidget(info_card)

        if self.auth.is_admin:
            time_group = QGroupBox("Set Time / Timezone")
            time_group.setStyleSheet("""
                QGroupBox {
                    font-weight: bold; border: 2px solid #e2e8f0;
                    border-radius: 8px; margin-top: 8px; padding: 16px;
                    background: white;
                }
                QGroupBox::title { subcontrol-origin: margin; padding: 0 8px; }
            """)
            time_layout = QVBoxLayout()

            set_time_row = QHBoxLayout()
            self.date_input = type('obj', (object,), {'date': QDateEdit, 'time': QTimeEdit})()

            self.new_time_input = QLineEdit()
            self.new_time_input.setPlaceholderText("e.g. 2026-06-14 14:30:00")
            self.new_time_input.setStyleSheet("padding: 6px; border: 1px solid #ddd; border-radius: 4px;")
            set_time_row.addWidget(self.new_time_input, 1)

            set_time_btn = QPushButton("Set Time")
            set_time_btn.setStyleSheet("""
                QPushButton { background: #0b7285; color: white;
                    padding: 6px 16px; border-radius: 5px; font-weight: bold; }
                QPushButton:hover { background: #1565c0; }
            """)
            set_time_btn.clicked.connect(self._set_time)
            set_time_row.addWidget(set_time_btn)
            time_layout.addLayout(set_time_row)

            tz_row = QHBoxLayout()
            self.tz_combo = QComboBox()
            self.tz_combo.setEditable(True)
            for tz in pytz.common_timezones:
                self.tz_combo.addItem(tz)
            self.tz_combo.setStyleSheet("padding: 6px; border: 1px solid #ddd; border-radius: 4px;")
            tz_row.addWidget(self.tz_combo, 1)

            set_tz_btn = QPushButton("Set Timezone")
            set_tz_btn.setStyleSheet("""
                QPushButton { background: #f59e0b; color: white;
                    padding: 6px 16px; border-radius: 5px; font-weight: bold; }
                QPushButton:hover { background: #d97706; }
            """)
            set_tz_btn.clicked.connect(self._set_timezone)
            tz_row.addWidget(set_tz_btn)
            time_layout.addLayout(tz_row)

            ntp_row = QHBoxLayout()
            enable_ntp_btn = QPushButton("Enable NTP")
            enable_ntp_btn.setStyleSheet("""
                QPushButton { background: #10b981; color: white;
                    padding: 8px 16px; border-radius: 5px; font-weight: bold; }
                QPushButton:hover { background: #059669; }
            """)
            enable_ntp_btn.clicked.connect(lambda: self._run_time_script("enable_ntp.sh"))
            ntp_row.addWidget(enable_ntp_btn)

            disable_ntp_btn = QPushButton("Disable NTP")
            disable_ntp_btn.setStyleSheet("""
                QPushButton { background: #ef4444; color: white;
                    padding: 8px 16px; border-radius: 5px; font-weight: bold; }
                QPushButton:hover { background: #dc2626; }
            """)
            disable_ntp_btn.clicked.connect(lambda: self._run_time_script("disable_ntp.sh"))
            ntp_row.addWidget(disable_ntp_btn)

            sync_ntp_btn = QPushButton("Sync NTP")
            sync_ntp_btn.setStyleSheet("""
                QPushButton { background: #6366f1; color: white;
                    padding: 8px 16px; border-radius: 5px; font-weight: bold; }
                QPushButton:hover { background: #4f46e5; }
            """)
            sync_ntp_btn.clicked.connect(lambda: self._run_time_script("sync_time.sh"))
            ntp_row.addWidget(sync_ntp_btn)

            ntp_row.addSpacerItem(QSpacerItem(40, 20, QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Minimum))
            time_layout.addLayout(ntp_row)

            time_group.setLayout(time_layout)
            layout.addWidget(time_group)

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
        layout.addWidget(self.output, 1)

    def on_activate(self):
        self._refresh_timer()

    def _refresh_timer(self):
        success, output = self.executor.run("show_time.sh")
        if success:
            self.time_display.setText(output.strip())

    def _log_action(self, action, success, detail):
        logger.log(self.auth.username, f"time:{action}", success, detail)

    def _run_time_script(self, script_name, args=None):
        self.output.append(f"$ {script_name} {' '.join(args or [])}\n")
        success, output = self.executor.run(script_name, args)
        if success:
            self.output.append(f"✓ {output}\n")
        else:
            self.output.append(f"✗ {output}\n")
        self._refresh_timer()

    def _set_time(self):
        new_time = self.new_time_input.text().strip()
        if not new_time:
            QMessageBox.warning(self, "Error", "Please enter a date/time.")
            return
        self._run_time_script("set_time.sh", [new_time])

    def _set_timezone(self):
        tz = self.tz_combo.currentText().strip()
        if not tz:
            QMessageBox.warning(self, "Error", "Please select a timezone.")
            return
        self._run_time_script("set_timezone.sh", [tz])
