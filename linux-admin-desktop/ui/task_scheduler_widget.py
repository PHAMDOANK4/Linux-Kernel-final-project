from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QLineEdit,
    QPushButton, QTableWidget, QTableWidgetItem, QHeaderView,
    QTextEdit, QMessageBox, QSizePolicy, QSpacerItem, QGroupBox, QFormLayout,
)
from PyQt6.QtCore import Qt, QThread, pyqtSignal
from PyQt6.QtGui import QFont

from app.executor import ScriptExecutor
from app.parsers import parse_cron_jobs
from app.logging import logger


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

        title = QLabel("Task Scheduler (Cron)")
        title.setFont(QFont("", 20, QFont.Weight.Bold))
        title.setStyleSheet("color: #1f2933;")
        layout.addWidget(title)

        form_group = QGroupBox("New / Edit Cron Job")
        form_group.setStyleSheet("""
            QGroupBox {
                font-weight: bold; border: 2px solid #e2e8f0;
                border-radius: 8px; margin-top: 8px; padding: 16px;
                background: white;
            }
            QGroupBox::title {
                subcontrol-origin: margin; padding: 0 8px;
            }
        """)
        form_layout = QFormLayout()

        self.schedule_input = QLineEdit()
        self.schedule_input.setPlaceholderText("e.g. */5 * * * * or @daily")
        self.schedule_input.setStyleSheet("padding: 6px; border: 1px solid #ddd; border-radius: 4px;")
        form_layout.addRow("Schedule:", self.schedule_input)

        self.command_input = QLineEdit()
        self.command_input.setPlaceholderText("e.g. /usr/bin/backup.sh")
        self.command_input.setStyleSheet("padding: 6px; border: 1px solid #ddd; border-radius: 4px;")
        form_layout.addRow("Command:", self.command_input)

        btn_row = QHBoxLayout()
        btn_style = """
            QPushButton { padding: 6px 16px; border-radius: 5px;
                font-weight: bold; font-size: 12px; }
        """

        create_btn = QPushButton("Create")
        create_btn.setStyleSheet(btn_style + "background: #0b7285; color: white;")
        create_btn.clicked.connect(self._create_job)
        btn_row.addWidget(create_btn)

        update_btn = QPushButton("Update")
        update_btn.setStyleSheet(btn_style + "background: #f59e0b; color: white;")
        update_btn.clicked.connect(self._update_job)
        btn_row.addWidget(update_btn)

        delete_btn = QPushButton("Delete")
        delete_btn.setStyleSheet(btn_style + "background: #ef4444; color: white;")
        delete_btn.clicked.connect(self._delete_job)
        btn_row.addWidget(delete_btn)

        run_btn = QPushButton("Run Now")
        run_btn.setStyleSheet(btn_style + "background: #10b981; color: white;")
        run_btn.clicked.connect(self._run_job)
        btn_row.addWidget(run_btn)

        btn_row.addSpacerItem(QSpacerItem(40, 20, QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Minimum))

        refresh_btn = QPushButton("Refresh")
        refresh_btn.setStyleSheet(btn_style + "background: #64748b; color: white;")
        refresh_btn.clicked.connect(self._load_cron)
        btn_row.addWidget(refresh_btn)

        form_layout.addRow("", btn_row)
        form_group.setLayout(form_layout)
        layout.addWidget(form_group)

        self.table = QTableWidget()
        self.table.setColumnCount(7)
        self.table.setHorizontalHeaderLabels([
            "Line", "Schedule", "Command", "Minute", "Hour", "Day", "Month", "Weekday"
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
            QTableWidget::item { padding: 4px; }
            QHeaderView::section {
                background: #f8fafc; padding: 6px;
                border: none; font-weight: bold; font-size: 11px;
            }
        """)
        self.table.itemClicked.connect(self._job_selected)
        layout.addWidget(self.table, 1)

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
        self.schedule_input.setText(schedule)
        self.command_input.setText(command)

    def _create_job(self):
        schedule = self.schedule_input.text().strip()
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
        schedule = self.schedule_input.text().strip()
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
