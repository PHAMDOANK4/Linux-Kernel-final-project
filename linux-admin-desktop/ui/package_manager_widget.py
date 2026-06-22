from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QLineEdit,
    QPushButton, QTableWidget, QTableWidgetItem, QHeaderView,
    QTextEdit, QMessageBox, QSizePolicy, QSpacerItem, QFrame,
)
from PyQt6.QtCore import Qt, QThread, pyqtSignal
from PyQt6.QtGui import QFont, QTextOption

from app.executor import ScriptExecutor
from app.logging import logger


BTN = """
    QPushButton {{
        background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
            stop:0 {top}, stop:1 {bottom});
        color: white; padding: 8px 20px;
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

CARD = """
    QFrame {{
        background: white; border-radius: 12px;
        border: 1px solid #e2e8f0;
        padding: {padding};
    }}
"""


class PackageThread(QThread):
    finished = pyqtSignal(bool, str)

    def __init__(self, executor, script_name, args=None):
        super().__init__()
        self.executor = executor
        self.script_name = script_name
        self.args = args or []

    def run(self):
        success, output = self.executor.run(self.script_name, self.args)
        self.finished.emit(success, output)


class PackageManagerWidget(QWidget):
    def __init__(self, auth_manager):
        super().__init__()
        self.auth = auth_manager
        self.executor = ScriptExecutor()
        self._setup_ui()
        self._load_packages()

    def _setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(24, 24, 24, 24)
        layout.setSpacing(12)

        title = QLabel("Package Management")
        title.setFont(QFont("", 20, QFont.Weight.Bold))
        title.setStyleSheet("color: #1f2933;")
        layout.addWidget(title)

        search_card = QFrame()
        search_card.setStyleSheet(CARD.format(padding="12px 16px"))
        search_layout = QHBoxLayout(search_card)
        search_layout.setContentsMargins(12, 8, 12, 8)

        self.search_input = QLineEdit()
        self.search_input.setPlaceholderText("Search packages...")
        self.search_input.setStyleSheet("""
            QLineEdit {
                padding: 8px 12px; border: 2px solid #e2e8f0;
                border-radius: 6px; font-size: 13px;
            }
            QLineEdit:focus { border-color: #0b7285; }
        """)
        search_layout.addWidget(self.search_input, 1)

        search_btn = QPushButton("Search")
        search_btn.setStyleSheet(BTN.format(
            top="#0b7285", bottom="#0a5a6f",
            hover_top="#1565c0", hover_bottom="#0b7285",
            press="#094c5e",
        ))
        search_btn.clicked.connect(self._search_package)
        search_layout.addWidget(search_btn)

        refresh_btn = QPushButton("Refresh")
        refresh_btn.setStyleSheet(BTN.format(
            top="#475569", bottom="#334155",
            hover_top="#64748b", hover_bottom="#475569",
            press="#1e293b",
        ))
        refresh_btn.clicked.connect(self._load_packages)
        search_layout.addWidget(refresh_btn)

        layout.addWidget(search_card)

        if self.auth.is_admin:
            action_card = QFrame()
            action_card.setStyleSheet(CARD.format(padding="12px 16px"))
            action_layout = QVBoxLayout(action_card)
            action_layout.setContentsMargins(16, 12, 16, 16)
            action_layout.setSpacing(10)

            action_title = QLabel("Package Actions")
            action_title.setFont(QFont("", 12, QFont.Weight.Bold))
            action_title.setStyleSheet("color: #334155; border: none;")
            action_layout.addWidget(action_title)

            input_row = QHBoxLayout()
            self.pkg_name_input = QLineEdit()
            self.pkg_name_input.setPlaceholderText("Package name (e.g. htop)")
            self.pkg_name_input.setStyleSheet("""
                QLineEdit {
                    padding: 8px 12px; border: 2px solid #e2e8f0;
                    border-radius: 6px; font-size: 13px;
                }
                QLineEdit:focus { border-color: #0b7285; }
            """)
            input_row.addWidget(self.pkg_name_input, 1)
            action_layout.addLayout(input_row)

            btn_row = QHBoxLayout()
            btn_row.setSpacing(10)

            install_btn = QPushButton("Install")
            install_btn.setStyleSheet(BTN.format(
                top="#10b981", bottom="#059669",
                hover_top="#34d399", hover_bottom="#10b981",
                press="#047857",
            ))
            install_btn.clicked.connect(self._install_package)
            btn_row.addWidget(install_btn)

            remove_btn = QPushButton("Remove")
            remove_btn.setStyleSheet(BTN.format(
                top="#ef4444", bottom="#dc2626",
                hover_top="#f87171", hover_bottom="#ef4444",
                press="#b91c1c",
            ))
            remove_btn.clicked.connect(self._remove_package)
            btn_row.addWidget(remove_btn)

            upgrade_btn = QPushButton("Upgrade")
            upgrade_btn.setStyleSheet(BTN.format(
                top="#f59e0b", bottom="#d97706",
                hover_top="#fbbf24", hover_bottom="#f59e0b",
                press="#b45309",
            ))
            upgrade_btn.clicked.connect(self._upgrade_package)
            btn_row.addWidget(upgrade_btn)

            btn_row.addStretch()
            action_layout.addLayout(btn_row)

            layout.addWidget(action_card)

        self.table = QTableWidget()
        self.table.setColumnCount(1)
        self.table.setHorizontalHeaderLabels(["Package Name"])
        self.table.horizontalHeader().setStretchLastSection(True)
        self.table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        self.table.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)
        self.table.setAlternatingRowColors(True)
        self.table.setStyleSheet("""
            QTableWidget {
                background: white; border: 1px solid #e2e8f0;
                border-radius: 8px; gridline-color: #f1f5f9;
                font-size: 13px;
            }
            QTableWidget::item { padding: 8px; }
            QHeaderView::section {
                background: #f8fafc; padding: 10px;
                border: none; font-weight: bold;
            }
        """)
        self.table.itemClicked.connect(self._package_selected)
        layout.addWidget(self.table, 2)

        output_card = QFrame()
        output_card.setStyleSheet(CARD.format(padding="0px"))
        output_card_layout = QVBoxLayout(output_card)
        output_card_layout.setContentsMargins(0, 0, 0, 0)
        output_card_layout.setSpacing(0)

        output_header = QFrame()
        output_header.setStyleSheet("background: #0f172a; border-radius: 12px 12px 0 0;")
        output_header.setFixedHeight(36)
        header_layout = QHBoxLayout(output_header)
        header_layout.setContentsMargins(12, 0, 12, 0)
        header_title = QLabel("Terminal Output")
        header_title.setStyleSheet("color: #94a3b8; font-size: 11px; font-weight: bold; border: none;")
        header_layout.addWidget(header_title)
        header_layout.addStretch()
        output_card_layout.addWidget(output_header)

        self.output = QTextEdit()
        self.output.setReadOnly(True)
        self.output.setMinimumHeight(80)
        self.output.setMaximumHeight(280)
        self.output.setWordWrapMode(QTextOption.WrapMode.WordWrap)
        self.output.setVerticalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAsNeeded)
        self.output.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        self.output.setStyleSheet("""
            QTextEdit {
                background: #1e293b; color: #f8fafc;
                padding: 10px 12px; border: none;
                font-family: monospace; font-size: 12px;
                border-radius: 0 0 12px 12px;
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
        output_card_layout.addWidget(self.output)

        clear_btn = QPushButton("Clear")
        clear_btn.setStyleSheet("""
            QPushButton {
                background: transparent; color: #64748b;
                padding: 2px 10px; border-radius: 4px;
                font-size: 11px; border: 1px solid #334155;
            }
            QPushButton:hover { background: #1e293b; color: #94a3b8; }
        """)
        clear_btn.clicked.connect(self.output.clear)
        header_layout.addWidget(clear_btn)

        layout.addWidget(output_card)

    def _append_output(self, text: str):
        doc = self.output.document()
        if doc.blockCount() > 500:
            cursor = self.output.textCursor()
            cursor.movePosition(cursor.MoveOperation.Start)
            cursor.movePosition(cursor.MoveOperation.Down, cursor.MoveMode.KeepAnchor, 250)
            cursor.removeSelectedText()
            cursor.deleteChar()
        self.output.append(text)
        scrollbar = self.output.verticalScrollBar()
        scrollbar.setValue(scrollbar.maximum())

    def _log_action(self, action, success, detail):
        logger.log(self.auth.username, f"packages:{action}", success, detail)

    def _run_pkg_script(self, script_name, args=None):
        self._append_output(f"$ {script_name} {' '.join(args or [])}")
        self.thread = PackageThread(self.executor, script_name, args)
        self.thread.finished.connect(self._on_script_done)
        self.thread.start()

    def _on_script_done(self, success, output):
        if success:
            self._append_output(f"✓ {output}")
        else:
            self._append_output(f"✗ {output}")

    def _load_packages(self):
        success, output = self.executor.run("list_packages.sh")
        if success:
            packages = [p.strip() for p in output.splitlines() if p.strip()]
            self.table.setRowCount(len(packages))
            for row, pkg in enumerate(packages):
                self.table.setItem(row, 0, QTableWidgetItem(pkg))
        else:
            self._append_output(f"✗ {output}")

    def _search_package(self):
        keyword = self.search_input.text().strip()
        if not keyword:
            QMessageBox.warning(self, "Error", "Please enter a search keyword.")
            return
        success, output = self.executor.run("search_package.sh", [keyword])
        self._append_output(f"$ search_package.sh {keyword}")
        if success:
            self._append_output(f"Results:\n{output}")
        else:
            self._append_output(f"✗ {output}")

    def _package_selected(self, item):
        text = item.text().strip()
        if " " in text:
            text = text.split()[0]
        self.pkg_name_input.setText(text)

    def _install_package(self):
        name = self.pkg_name_input.text().strip()
        if not name:
            QMessageBox.warning(self, "Error", "Please enter a package name.")
            return
        self._run_pkg_script("install_package.sh", [name])

    def _remove_package(self):
        name = self.pkg_name_input.text().strip()
        if not name:
            QMessageBox.warning(self, "Error", "Please enter a package name.")
            return
        reply = QMessageBox.question(
            self, "Confirm Remove",
            f"Are you sure you want to remove '{name}'?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
        )
        if reply == QMessageBox.StandardButton.Yes:
            self._run_pkg_script("remove_package.sh", [name])

    def _upgrade_package(self):
        name = self.pkg_name_input.text().strip()
        args = [name] if name else []
        self._run_pkg_script("upgrade_package.sh", args)
