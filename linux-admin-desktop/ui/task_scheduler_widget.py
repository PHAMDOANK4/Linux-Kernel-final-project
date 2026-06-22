from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QLineEdit,
    QPushButton, QTableWidget, QTableWidgetItem, QHeaderView,
    QTextEdit, QMessageBox, QFrame, QSpinBox, QComboBox,
    QStackedWidget, QButtonGroup,
)
from PyQt6.QtCore import Qt, QThread, pyqtSignal
from PyQt6.QtGui import QFont

from app.executor import ScriptExecutor
from app.parsers import parse_cron_jobs
from app.logging import logger


BTN = """
    QPushButton {{
        background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
            stop:0 {top}, stop:1 {bottom});
        color: white; padding: 7px 18px;
        border-radius: 6px; font-weight: bold; font-size: 12px;
        border: none;
    }}
    QPushButton:hover {{
        background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
            stop:0 {hover_top}, stop:1 {hover_bottom});
    }}
    QPushButton:pressed {{
        background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
            stop:0 {press}, stop:1 {press});
    }}
"""

MODE_BTN = """
    QPushButton {{
        padding: 6px 14px; border-radius: 6px;
        font-weight: bold; font-size: 11px;
        border: 2px solid {border};
        background: {bg}; color: {fg};
    }}
    QPushButton:hover {{
        background: {hover_bg};
    }}
    QPushButton:checked {{
        background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
            stop:0 {check_top}, stop:1 {check_bottom});
        color: white; border-color: transparent;
    }}
"""

WEEKDAYS = ["Sun", "Mon", "Tue", "Wed", "Thu", "Fri", "Sat"]
WEEKDAYS_FULL = ["Sunday", "Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday"]
MONTHS = ["Jan", "Feb", "Mar", "Apr", "May", "Jun",
          "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"]
MONTHS_FULL = ["January", "February", "March", "April", "May", "June",
               "July", "August", "September", "October", "November", "December"]


def _build_cron(mode: str, minute: int, hour: int, day: int, month: int, weekday: int, custom: str) -> str:
    if mode == "custom":
        return custom.strip()
    m = str(minute)
    h = str(hour)
    d = str(day) if mode == "monthly" or mode == "yearly" else "*"
    mo = str(month) if mode == "yearly" else "*"
    w = str(weekday) if mode == "weekly" else "*"
    return f"{m} {h} {d} {mo} {w}"


class CronThread(QThread):
    finished = pyqtSignal(bool, str)

    def __init__(self, executor, script_name, args=None):
        super().__init__()
        self.executor = executor
        self.script_name = script_name
        self.args = args or []

    def run(self):
        success, output = self.executor.run(self.script_name, self.args)
        self.finished.emit(success, output)


class TaskSchedulerWidget(QWidget):
    def __init__(self, auth_manager):
        super().__init__()
        self.auth = auth_manager
        self.executor = ScriptExecutor()
        self._setup_ui()
        self._load_cron()

    def _setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(24, 24, 24, 24)
        layout.setSpacing(12)

        title = QLabel("Task Scheduler (Cron)")
        title.setFont(QFont("", 20, QFont.Weight.Bold))
        title.setStyleSheet("color: #1f2933;")
        layout.addWidget(title)

        card = QFrame()
        card.setStyleSheet("""
            QFrame { background: white; border-radius: 12px;
                border: 1px solid #e2e8f0; padding: 16px; }
        """)
        card_layout = QVBoxLayout(card)
        card_layout.setContentsMargins(16, 12, 16, 16)
        card_layout.setSpacing(10)

        card_title = QLabel("Schedule Builder")
        card_title.setFont(QFont("", 12, QFont.Weight.Bold))
        card_title.setStyleSheet("color: #334155; border: none;")
        card_layout.addWidget(card_title)

        mode_row = QHBoxLayout()
        mode_row.setSpacing(6)
        self.mode_btns = QButtonGroup(self)

        self._mode_btn("Hourly", 0, mode_row)
        self._mode_btn("Daily", 1, mode_row)
        self._mode_btn("Weekly", 2, mode_row)
        self._mode_btn("Monthly", 3, mode_row)
        self._mode_btn("Yearly", 4, mode_row)
        self._mode_btn("Custom", 5, mode_row)
        mode_row.addStretch()

        self.mode_btns.buttonClicked.connect(self._switch_mode)
        card_layout.addLayout(mode_row)

        self.schedule_stack = QStackedWidget()
        self._build_hourly_page()
        self._build_daily_page()
        self._build_weekly_page()
        self._build_monthly_page()
        self._build_yearly_page()
        self._build_custom_page()
        card_layout.addWidget(self.schedule_stack)

        preview_row = QHBoxLayout()
        preview_label = QLabel("Cron:")
        preview_label.setStyleSheet("color: #64748b; font-size: 12px; font-weight: bold;")
        preview_row.addWidget(preview_label)

        self.cron_preview = QLabel("Select a schedule mode")
        self.cron_preview.setStyleSheet("""
            QLabel {
                background: #f1f5f9; color: #0b7285;
                padding: 6px 12px; border-radius: 4px;
                font-family: monospace; font-size: 13px; font-weight: bold;
            }
        """)
        preview_row.addWidget(self.cron_preview, 1)
        card_layout.addLayout(preview_row)

        self.command_input = QLineEdit()
        self.command_input.setPlaceholderText("Command or script path (e.g. /usr/bin/backup.sh)")
        self.command_input.setStyleSheet("""
            QLineEdit { padding: 8px; border: 2px solid #e2e8f0;
                border-radius: 6px; font-size: 13px; }
            QLineEdit:focus { border-color: #0b7285; }
        """)
        card_layout.addWidget(self.command_input)

        btn_row = QHBoxLayout()
        btn_row.setSpacing(8)

        create_btn = QPushButton("Create")
        create_btn.setStyleSheet(BTN.format(
            top="#0b7285", bottom="#0a5a6f",
            hover_top="#1565c0", hover_bottom="#0b7285", press="#094c5e",
        ))
        create_btn.clicked.connect(self._create_job)
        btn_row.addWidget(create_btn)

        update_btn = QPushButton("Update")
        update_btn.setStyleSheet(BTN.format(
            top="#f59e0b", bottom="#d97706",
            hover_top="#fbbf24", hover_bottom="#f59e0b", press="#b45309",
        ))
        update_btn.clicked.connect(self._update_job)
        btn_row.addWidget(update_btn)

        delete_btn = QPushButton("Delete")
        delete_btn.setStyleSheet(BTN.format(
            top="#ef4444", bottom="#dc2626",
            hover_top="#f87171", hover_bottom="#ef4444", press="#b91c1c",
        ))
        delete_btn.clicked.connect(self._delete_job)
        btn_row.addWidget(delete_btn)

        run_btn = QPushButton("Run Now")
        run_btn.setStyleSheet(BTN.format(
            top="#10b981", bottom="#059669",
            hover_top="#34d399", hover_bottom="#10b981", press="#047857",
        ))
        run_btn.clicked.connect(self._run_job)
        btn_row.addWidget(run_btn)

        btn_row.addStretch()

        refresh_btn = QPushButton("Refresh")
        refresh_btn.setStyleSheet(BTN.format(
            top="#64748b", bottom="#475569",
            hover_top="#94a3b8", hover_bottom="#64748b", press="#334155",
        ))
        refresh_btn.clicked.connect(self._load_cron)
        btn_row.addWidget(refresh_btn)

        card_layout.addLayout(btn_row)
        layout.addWidget(card)

        self.table = QTableWidget()
        self.table.setColumnCount(8)
        self.table.setHorizontalHeaderLabels([
            "Line", "Schedule", "Command", "Min", "Hour", "Day", "Month", "Weekday"
        ])
        self.table.horizontalHeader().setStretchLastSection(True)
        self.table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        self.table.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)
        self.table.setAlternatingRowColors(True)
        self.table.setStyleSheet("""
            QTableWidget {
                background: white; border: 1px solid #e2e8f0;
                border-radius: 8px; gridline-color: #f1f5f9;
                font-size: 12px;
            }
            QTableWidget::item { padding: 6px; }
            QHeaderView::section {
                background: #f8fafc; padding: 8px;
                border: none; font-weight: bold; font-size: 11px;
            }
        """)
        self.table.itemClicked.connect(self._job_selected)
        layout.addWidget(self.table, 1)

        self.output = QTextEdit()
        self.output.setReadOnly(True)
        self.output.setMaximumHeight(150)
        self.output.setStyleSheet("""
            QTextEdit {
                background: #1e293b; color: #f8fafc;
                border-radius: 8px; padding: 10px;
                font-family: monospace; font-size: 12px;
            }
            QScrollBar:vertical {
                background: #0f172a; width: 8px;
                border-radius: 4px;
            }
            QScrollBar::handle:vertical {
                background: #475569; border-radius: 4px;
                min-height: 20px;
            }
            QScrollBar::handle:vertical:hover { background: #64748b; }
            QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {
                height: 0; background: none;
            }
        """)
        layout.addWidget(self.output)

        self.mode_btns.button(0).setChecked(True)
        self._switch_mode(self.mode_btns.button(0))

    def _mode_btn(self, text, id_, layout):
        btn = QPushButton(text)
        btn.setCheckable(True)
        btn.setStyleSheet(MODE_BTN.format(
            border="#cbd5e1", bg="transparent", fg="#475569",
            hover_bg="#f1f5f9",
            check_top="#0b7285", check_bottom="#0a5a6f",
        ))
        self.mode_btns.addButton(btn, id_)
        layout.addWidget(btn)

    def _make_spin(self, min_val, max_val, default=0):
        s = QSpinBox()
        s.setRange(min_val, max_val)
        s.setValue(default)
        s.setStyleSheet("""
            QSpinBox {
                padding: 6px; border: 2px solid #e2e8f0;
                border-radius: 6px; font-size: 13px;
            }
            QSpinBox:focus { border-color: #0b7285; }
        """)
        return s

    def _build_hourly_page(self):
        page = QWidget()
        row = QHBoxLayout(page)
        row.setContentsMargins(0, 4, 0, 4)
        row.addWidget(QLabel("At minute:"))
        self.h_min = self._make_spin(0, 59, 0)
        row.addWidget(self.h_min)
        row.addStretch()
        self.schedule_stack.addWidget(page)

    def _build_daily_page(self):
        page = QWidget()
        row = QHBoxLayout(page)
        row.setContentsMargins(0, 4, 0, 4)
        row.addWidget(QLabel("At:"))
        self.d_hour = self._make_spin(0, 23, 9)
        row.addWidget(self.d_hour)
        row.addWidget(QLabel(":"))
        self.d_min = self._make_spin(0, 59, 0)
        row.addWidget(self.d_min)
        row.addStretch()
        self.schedule_stack.addWidget(page)

    def _build_weekly_page(self):
        page = QWidget()
        row = QHBoxLayout(page)
        row.setContentsMargins(0, 4, 0, 4)
        row.addWidget(QLabel("Day:"))
        self.w_day = QComboBox()
        for d in WEEKDAYS_FULL:
            self.w_day.addItem(d)
        self.w_day.setStyleSheet("""
            QComboBox { padding: 6px; border: 2px solid #e2e8f0;
                border-radius: 6px; font-size: 13px; }
            QComboBox:focus { border-color: #0b7285; }
        """)
        row.addWidget(self.w_day)
        row.addSpacing(16)
        row.addWidget(QLabel("At:"))
        self.w_hour = self._make_spin(0, 23, 9)
        row.addWidget(self.w_hour)
        row.addWidget(QLabel(":"))
        self.w_min = self._make_spin(0, 59, 0)
        row.addWidget(self.w_min)
        row.addStretch()
        self.schedule_stack.addWidget(page)

    def _build_monthly_page(self):
        page = QWidget()
        row = QHBoxLayout(page)
        row.setContentsMargins(0, 4, 0, 4)
        row.addWidget(QLabel("Day:"))
        self.m_day = self._make_spin(1, 31, 1)
        row.addWidget(self.m_day)
        row.addSpacing(16)
        row.addWidget(QLabel("At:"))
        self.m_hour = self._make_spin(0, 23, 9)
        row.addWidget(self.m_hour)
        row.addWidget(QLabel(":"))
        self.m_min = self._make_spin(0, 59, 0)
        row.addWidget(self.m_min)
        row.addStretch()
        self.schedule_stack.addWidget(page)

    def _build_yearly_page(self):
        page = QWidget()
        row = QHBoxLayout(page)
        row.setContentsMargins(0, 4, 0, 4)
        row.addWidget(QLabel("Month:"))
        self.y_month = QComboBox()
        for m in MONTHS_FULL:
            self.y_month.addItem(m)
        self.y_month.setStyleSheet("""
            QComboBox { padding: 6px; border: 2px solid #e2e8f0;
                border-radius: 6px; font-size: 13px; }
            QComboBox:focus { border-color: #0b7285; }
        """)
        row.addWidget(self.y_month)
        row.addSpacing(16)
        row.addWidget(QLabel("Day:"))
        self.y_day = self._make_spin(1, 31, 1)
        row.addWidget(self.y_day)
        row.addSpacing(16)
        row.addWidget(QLabel("At:"))
        self.y_hour = self._make_spin(0, 23, 9)
        row.addWidget(self.y_hour)
        row.addWidget(QLabel(":"))
        self.y_min = self._make_spin(0, 59, 0)
        row.addWidget(self.y_min)
        row.addStretch()
        self.schedule_stack.addWidget(page)

    def _build_custom_page(self):
        page = QWidget()
        row = QHBoxLayout(page)
        row.setContentsMargins(0, 4, 0, 4)
        row.addWidget(QLabel("Cron expression:"))
        self.custom_input = QLineEdit()
        self.custom_input.setPlaceholderText("e.g. */5 * * * *  or  @daily")
        self.custom_input.setStyleSheet("""
            QLineEdit { padding: 8px; border: 2px solid #e2e8f0;
                border-radius: 6px; font-size: 13px; }
            QLineEdit:focus { border-color: #0b7285; }
        """)
        row.addWidget(self.custom_input, 1)
        self.schedule_stack.addWidget(page)

        self.custom_input.textChanged.connect(self._update_preview)

    def _switch_mode(self, btn):
        idx = self.mode_btns.id(btn)
        self.schedule_stack.setCurrentIndex(idx)
        self._update_preview()

    def _get_cron_schedule(self) -> str:
        btn = self.mode_btns.checkedButton()
        if not btn:
            return ""
        mode_idx = self.mode_btns.id(btn)
        modes = ["hourly", "daily", "weekly", "monthly", "yearly", "custom"]
        mode = modes[mode_idx]

        if mode == "hourly":
            return _build_cron(mode, self.h_min.value(), 0, 1, 1, 0, "")
        elif mode == "daily":
            return _build_cron(mode, self.d_min.value(), self.d_hour.value(), 1, 1, 0, "")
        elif mode == "weekly":
            return _build_cron(mode, self.w_min.value(), self.w_hour.value(), 1, 1, self.w_day.currentIndex(), "")
        elif mode == "monthly":
            return _build_cron(mode, self.m_min.value(), self.m_hour.value(), self.m_day.value(), 1, 0, "")
        elif mode == "yearly":
            return _build_cron(mode, self.y_min.value(), self.y_hour.value(), self.y_day.value(), self.y_month.currentIndex() + 1, 0, "")
        elif mode == "custom":
            return self.custom_input.text().strip()

    def _update_preview(self, *args):
        cron = self._get_cron_schedule()
        if cron:
            self.cron_preview.setText(cron)
        else:
            self.cron_preview.setText("Select a schedule mode")

    def _log_action(self, action, success, detail):
        logger.log(self.auth.username, f"cron:{action}", success, detail)

    def _run_cron_script(self, script_name, args=None):
        self.output.append(f"$ {script_name} {' '.join(args or [])}\n")
        self.thread = CronThread(self.executor, script_name, args)
        self.thread.finished.connect(self._on_script_done)
        self.thread.start()

    def _on_script_done(self, success, output):
        if success:
            self.output.append(f"✓ {output}\n")
        else:
            self.output.append(f"✗ {output}\n")
        self._load_cron()

    def _load_cron(self):
        success, output = self.executor.run("list_cron.sh")
        if success:
            jobs = parse_cron_jobs(output)
            self.table.setRowCount(len(jobs))
            for row, job in enumerate(jobs):
                self.table.setItem(row, 0, QTableWidgetItem(str(job["line_number"])))
                self.table.setItem(row, 1, QTableWidgetItem(job["schedule"]))
                self.table.setItem(row, 2, QTableWidgetItem(job["command"]))
                self.table.setItem(row, 3, QTableWidgetItem(job["minute"]))
                self.table.setItem(row, 4, QTableWidgetItem(job["hour"]))
                self.table.setItem(row, 5, QTableWidgetItem(job["day_of_month"]))
                self.table.setItem(row, 6, QTableWidgetItem(job["month"]))
                self.table.setItem(row, 7, QTableWidgetItem(job["weekday"]))
        else:
            self.output.append(f"✗ {output}\n")

    def _job_selected(self, item):
        row = item.row()
        schedule = self.table.item(row, 1).text() if self.table.item(row, 1) else ""
        command = self.table.item(row, 2).text() if self.table.item(row, 2) else ""

        parts = schedule.split()
        if len(parts) == 5:
            m, h, d, mo, w = parts
            if m == "*" and h != "*":
                self.mode_btns.button(1).setChecked(True)
                self.d_min.setValue(0)
                self.d_hour.setValue(int(h))
            elif m != "*" and h == "*":
                self.mode_btns.button(0).setChecked(True)
                self.h_min.setValue(int(m))
            elif m != "*" and h != "*" and d == "*" and mo == "*" and w != "*":
                self.mode_btns.button(2).setChecked(True)
                self.w_min.setValue(int(m))
                self.w_hour.setValue(int(h))
                self.w_day.setCurrentIndex(int(w))
            elif m != "*" and h != "*" and d != "*" and mo == "*" and w == "*":
                self.mode_btns.button(3).setChecked(True)
                self.m_min.setValue(int(m))
                self.m_hour.setValue(int(h))
                self.m_day.setValue(int(d))
            elif m != "*" and h != "*" and d != "*" and mo != "*" and w == "*":
                self.mode_btns.button(4).setChecked(True)
                self.y_min.setValue(int(m))
                self.y_hour.setValue(int(h))
                self.y_day.setValue(int(d))
                self.y_month.setCurrentIndex(int(mo) - 1)
            else:
                self.mode_btns.button(5).setChecked(True)
                self.custom_input.setText(schedule)
            self._switch_mode(self.mode_btns.checkedButton())
        else:
            self.mode_btns.button(5).setChecked(True)
            self.custom_input.setText(schedule)
            self._switch_mode(self.mode_btns.checkedButton())

        self.command_input.setText(command)

    def _create_job(self):
        schedule = self._get_cron_schedule()
        command = self.command_input.text().strip()
        if not schedule or not command:
            QMessageBox.warning(self, "Error", "Please fill in both schedule and command.")
            return
        self._run_cron_script("create_cron.sh", [schedule, command])

    def _update_job(self):
        row = self.table.currentRow()
        if row < 0:
            QMessageBox.warning(self, "Error", "Please select a cron job first.")
            return
        match_text = self.table.item(row, 2).text() if self.table.item(row, 2) else ""
        schedule = self._get_cron_schedule()
        command = self.command_input.text().strip()
        if not schedule or not command:
            QMessageBox.warning(self, "Error", "Please fill in both schedule and command.")
            return
        self._run_cron_script("update_cron.sh", [match_text, schedule, command])

    def _delete_job(self):
        row = self.table.currentRow()
        if row < 0:
            QMessageBox.warning(self, "Error", "Please select a cron job first.")
            return
        reply = QMessageBox.question(
            self, "Confirm Delete",
            "Are you sure you want to delete this cron job?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
        )
        if reply == QMessageBox.StandardButton.Yes:
            match_text = self.table.item(row, 2).text() if self.table.item(row, 2) else ""
            self._run_cron_script("delete_cron.sh", [match_text])

    def _run_job(self):
        command = self.command_input.text().strip()
        if not command:
            QMessageBox.warning(self, "Error", "Please enter a command to run.")
            return
        self._run_cron_script("run_job.sh", [command])
