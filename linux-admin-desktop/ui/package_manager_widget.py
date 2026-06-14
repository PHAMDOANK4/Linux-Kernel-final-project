from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QLineEdit,
    QPushButton, QTableWidget, QTableWidgetItem, QHeaderView,
    QTextEdit, QMessageBox, QSizePolicy, QSpacerItem, QGroupBox, QFormLayout,
)
from PyQt6.QtCore import Qt, QThread, pyqtSignal
from PyQt6.QtGui import QFont

from app.executor import ScriptExecutor
from app.logging import logger


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

        title = QLabel("Package Management")
        title.setFont(QFont("", 20, QFont.Weight.Bold))
        title.setStyleSheet("color: #1f2933;")
        layout.addWidget(title)

        search_row = QHBoxLayout()
        self.search_input = QLineEdit()
        self.search_input.setPlaceholderText("Search packages...")
        self.search_input.setStyleSheet("""
            QLineEdit { padding: 8px; border: 2px solid #ddd;
                border-radius: 6px; font-size: 13px; }
            QLineEdit:focus { border-color: #0b7285; }
        """)
        search_row.addWidget(self.search_input, 1)

        search_btn = QPushButton("Search")
        search_btn.setStyleSheet("""
            QPushButton { background: #0b7285; color: white;
                padding: 8px 20px; border-radius: 6px; font-weight: bold; }
            QPushButton:hover { background: #1565c0; }
        """)
        search_btn.clicked.connect(self._search_package)
        search_row.addWidget(search_btn)

        refresh_btn = QPushButton("Refresh")
        refresh_btn.setStyleSheet("""
            QPushButton { background: #64748b; color: white;
                padding: 8px 16px; border-radius: 6px; }
            QPushButton:hover { background: #475569; }
        """)
        refresh_btn.clicked.connect(self._load_packages)
        search_row.addWidget(refresh_btn)

        layout.addLayout(search_row)

        if self.auth.is_admin:
            action_group = QGroupBox("Package Actions")
            action_group.setStyleSheet("""
                QGroupBox {
                    font-weight: bold; border: 2px solid #e2e8f0;
                    border-radius: 8px; margin-top: 8px; padding: 16px;
                    background: white;
                }
                QGroupBox::title { subcontrol-origin: margin; padding: 0 8px; }
            """)
            action_layout = QHBoxLayout()

            self.pkg_name_input = QLineEdit()
            self.pkg_name_input.setPlaceholderText("Package name (e.g. htop)")
            self.pkg_name_input.setStyleSheet("padding: 6px; border: 1px solid #ddd; border-radius: 4px;")
            action_layout.addWidget(self.pkg_name_input, 1)

            btn_style = """
                QPushButton { padding: 6px 16px; border-radius: 5px;
                    font-weight: bold; font-size: 12px; }
            """

            install_btn = QPushButton("Install")
            install_btn.setStyleSheet(btn_style + "background: #10b981; color: white;")
            install_btn.clicked.connect(self._install_package)
            action_layout.addWidget(install_btn)

            remove_btn = QPushButton("Remove")
            remove_btn.setStyleSheet(btn_style + "background: #ef4444; color: white;")
            remove_btn.clicked.connect(self._remove_package)
            action_layout.addWidget(remove_btn)

            upgrade_btn = QPushButton("Upgrade")
            upgrade_btn.setStyleSheet(btn_style + "background: #f59e0b; color: white;")
            upgrade_btn.clicked.connect(self._upgrade_package)
            action_layout.addWidget(upgrade_btn)

            action_group.setLayout(action_layout)
            layout.addWidget(action_group)

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
            QTableWidget::item { padding: 6px; }
            QHeaderView::section {
                background: #f8fafc; padding: 8px;
                border: none; font-weight: bold;
            }
        """)
        self.table.itemClicked.connect(self._package_selected)
        layout.addWidget(self.table, 1)

        self.output = QTextEdit()
        self.output.setReadOnly(True)
        self.output.setMaximumHeight(150)
        self.output.setStyleSheet("""
            QTextEdit {
                background: #111827; color: #f8fafc;
                border-radius: 8px; padding: 10px;
                font-family: monospace; font-size: 12px;
            }
        """)
        layout.addWidget(self.output)

    def _log_action(self, action, success, detail):
        logger.log(self.auth.username, f"packages:{action}", success, detail)

    def _run_pkg_script(self, script_name, args=None):
        self.output.append(f"$ {script_name} {' '.join(args or [])}\n")
        self.thread = PackageThread(self.executor, script_name, args)
        self.thread.finished.connect(self._on_script_done)
        self.thread.start()

    def _on_script_done(self, success, output):
        if success:
            self.output.append(f"✓ {output}\n")
        else:
            self.output.append(f"✗ {output}\n")

    def _load_packages(self):
        success, output = self.executor.run("list_packages.sh")
        if success:
            packages = [p.strip() for p in output.splitlines() if p.strip()]
            self.table.setRowCount(len(packages))
            for row, pkg in enumerate(packages):
                self.table.setItem(row, 0, QTableWidgetItem(pkg))
        else:
            self.output.append(f"✗ {output}\n")

    def _search_package(self):
        keyword = self.search_input.text().strip()
        if not keyword:
            QMessageBox.warning(self, "Error", "Please enter a search keyword.")
            return
        success, output = self.executor.run("search_package.sh", [keyword])
        self.output.append(f"$ search_package.sh {keyword}\n")
        if success:
            self.output.append(f"Results:\n{output}\n")
        else:
            self.output.append(f"✗ {output}\n")

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
