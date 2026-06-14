from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QLabel, QTableWidget, QTableWidgetItem,
    QHeaderView, QPushButton, QHBoxLayout, QTextEdit, QSizePolicy, QSpacerItem,
)
from PyQt6.QtCore import Qt
from PyQt6.QtGui import QFont

from app.database import ActionLog, get_session


class LogsViewerWidget(QWidget):
    def __init__(self, auth_manager):
        super().__init__()
        self.auth = auth_manager
        self._setup_ui()
        self._load_logs()

    def _setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(24, 24, 24, 24)

        title = QLabel("Audit Logs")
        title.setFont(QFont("", 20, QFont.Weight.Bold))
        title.setStyleSheet("color: #1f2933;")
        layout.addWidget(title)

        subtitle = QLabel("Last 200 actions — read only")
        subtitle.setStyleSheet("color: #64748b; margin-bottom: 8px;")
        layout.addWidget(subtitle)

        self.table = QTableWidget()
        self.table.setColumnCount(5)
        self.table.setHorizontalHeaderLabels([
            "Timestamp", "User", "Action", "Result", "Detail"
        ])
        self.table.horizontalHeader().setStretchLastSection(True)
        self.table.horizontalHeader().setSectionResizeMode(0, QHeaderView.ResizeMode.ResizeToContents)
        self.table.horizontalHeader().setSectionResizeMode(1, QHeaderView.ResizeMode.ResizeToContents)
        self.table.horizontalHeader().setSectionResizeMode(2, QHeaderView.ResizeMode.ResizeToContents)
        self.table.horizontalHeader().setSectionResizeMode(3, QHeaderView.ResizeMode.ResizeToContents)
        self.table.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)
        self.table.setAlternatingRowColors(True)
        self.table.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)
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
        layout.addWidget(self.table, 1)

        btn_row = QHBoxLayout()
        btn_row.addSpacerItem(QSpacerItem(40, 20, QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Minimum))

        refresh_btn = QPushButton("Refresh")
        refresh_btn.setStyleSheet("""
            QPushButton { background: #0b7285; color: white;
                padding: 8px 20px; border-radius: 6px; font-weight: bold; }
            QPushButton:hover { background: #1565c0; }
        """)
        refresh_btn.clicked.connect(self._load_logs)
        btn_row.addWidget(refresh_btn)

        layout.addLayout(btn_row)

    def _load_logs(self):
        session = get_session()
        try:
            logs = (
                session.query(ActionLog)
                .order_by(ActionLog.created_at.desc())
                .limit(200)
                .all()
            )
            self.table.setRowCount(len(logs))
            for row, log in enumerate(logs):
                self.table.setItem(row, 0, QTableWidgetItem(
                    log.created_at.strftime("%Y-%m-%d %H:%M:%S")
                ))
                self.table.setItem(row, 1, QTableWidgetItem(log.username))
                self.table.setItem(row, 2, QTableWidgetItem(log.action))
                self.table.setItem(row, 3, QTableWidgetItem(log.result))

                result_item = self.table.item(row, 3)
                if log.result == "SUCCESS":
                    result_item.setForeground(Qt.GlobalColor.darkGreen)
                else:
                    result_item.setForeground(Qt.GlobalColor.red)

                self.table.setItem(row, 4, QTableWidgetItem(log.detail[:200]))
        finally:
            session.close()
