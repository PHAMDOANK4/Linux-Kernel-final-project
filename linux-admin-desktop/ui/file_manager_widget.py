import os

from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QLineEdit,
    QPushButton, QTableWidget, QTableWidgetItem, QHeaderView,
    QTextEdit, QMessageBox, QFrame, QInputDialog, QFileDialog,
    QSizePolicy, QSpacerItem, QMenu,
)
from PyQt6.QtCore import Qt, QThread, pyqtSignal
from PyQt6.QtGui import QFont, QAction

from app.executor import ScriptExecutor
from app.parsers import parse_file_listing
from app.logging import logger


class ScriptThread(QThread):
    finished = pyqtSignal(bool, str)

    def __init__(self, executor, script_name, args=None):
        super().__init__()
        self.executor = executor
        self.script_name = script_name
        self.args = args or []

    def run(self):
        success, output = self.executor.run(self.script_name, self.args)
        self.finished.emit(success, output)


class FileManagerWidget(QWidget):
    def __init__(self, auth_manager):
        super().__init__()
        self.auth = auth_manager
        self.executor = ScriptExecutor()
        self.current_path = "/home"
        self._setup_ui()
        self._load_files()

    def _setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(24, 24, 24, 24)

        title = QLabel("File Management")
        title.setFont(QFont("", 20, QFont.Weight.Bold))
        title.setStyleSheet("color: #1f2933;")
        layout.addWidget(title)

        nav = QHBoxLayout()
        self.path_input = QLineEdit(self.current_path)
        self.path_input.setStyleSheet("""
            QLineEdit { padding: 8px; border: 2px solid #ddd;
                border-radius: 6px; font-size: 13px; }
            QLineEdit:focus { border-color: #0b7285; }
        """)
        nav.addWidget(self.path_input, 1)

        go_btn = QPushButton("Go")
        go_btn.setStyleSheet("""
            QPushButton { background: #0b7285; color: white;
                padding: 8px 20px; border-radius: 6px; font-weight: bold; }
            QPushButton:hover { background: #1565c0; }
        """)
        go_btn.clicked.connect(self._go_path)
        nav.addWidget(go_btn)

        parent_btn = QPushButton("..")
        parent_btn.setStyleSheet("""
            QPushButton { background: #64748b; color: white;
                padding: 8px 16px; border-radius: 6px; }
            QPushButton:hover { background: #475569; }
        """)
        parent_btn.clicked.connect(self._go_parent)
        nav.addWidget(parent_btn)

        layout.addLayout(nav)

        actions = QHBoxLayout()
        actions.setSpacing(6)

        btn_style = """
            QPushButton { background: #e2e8f0; color: #1e293b;
                padding: 6px 14px; border-radius: 5px; font-size: 12px; }
            QPushButton:hover { background: #cbd5e1; }
        """

        for text, cb in [
            ("New File", self._create_file),
            ("New Folder", self._create_folder),
            ("Rename", self._rename),
            ("Copy", self._copy),
            ("Move", self._move),
            ("Delete", self._delete),
            ("Search", self._search),
            ("Chmod", self._chmod),
            ("Chown", self._chown),
        ]:
            btn = QPushButton(text)
            btn.setStyleSheet(btn_style)
            btn.clicked.connect(cb)
            actions.addWidget(btn)

        actions.addSpacerItem(QSpacerItem(40, 20, QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Minimum))

        refresh_btn = QPushButton("Refresh")
        refresh_btn.setStyleSheet("""
            QPushButton { background: #0b7285; color: white;
                padding: 6px 14px; border-radius: 5px; font-weight: bold; }
            QPushButton:hover { background: #1565c0; }
        """)
        refresh_btn.clicked.connect(self._load_files)
        actions.addWidget(refresh_btn)

        layout.addLayout(actions)

        self.table = QTableWidget()
        self.table.setColumnCount(3)
        self.table.setHorizontalHeaderLabels(["Type", "Name", "Path"])
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
        self.table.setContextMenuPolicy(Qt.ContextMenuPolicy.CustomContextMenu)
        self.table.customContextMenuRequested.connect(self._context_menu)
        self.table.itemDoubleClicked.connect(self._item_double_clicked)
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
        logger.log(self.auth.username, f"files:{action}", success, detail)

    def _run_script(self, script_name, args=None):
        self.output.append(f"$ {script_name} {' '.join(args or [])}\n")
        self.thread = ScriptThread(self.executor, script_name, args)
        self.thread.finished.connect(self._on_script_done)
        self.thread.start()

    def _on_script_done(self, success, output):
        if success:
            self.output.append(f"✓ {output}\n")
        else:
            self.output.append(f"✗ {output}\n")
        self._load_files()

    def _load_files(self):
        success, output = self.executor.run("list_files.sh", [self.current_path])
        if success:
            entries = parse_file_listing(output)
            self.table.setRowCount(len(entries))
            for row, entry in enumerate(entries):
                self.table.setItem(row, 0, QTableWidgetItem(entry["type"]))
                self.table.setItem(row, 1, QTableWidgetItem(entry["name"]))
                self.table.setItem(row, 2, QTableWidgetItem(entry["path"]))
                if entry["is_dir"]:
                    self.table.item(row, 0).setBackground(Qt.GlobalColor.lightGray)
        else:
            self.output.append(f"✗ {output}\n")

    def _go_path(self):
        path = self.path_input.text().strip()
        path = os.path.abspath(path)
        if os.path.isdir(path):
            self.current_path = path
            self.path_input.setText(path)
            self._load_files()
        else:
            QMessageBox.warning(self, "Error", f"Invalid directory: {path}")

    def _go_parent(self):
        parent = os.path.dirname(self.current_path.rstrip("/")) or "/"
        self.current_path = parent
        self.path_input.setText(parent)
        self._load_files()

    def _item_double_clicked(self, item):
        row = item.row()
        path_item = self.table.item(row, 2)
        if path_item and self.table.item(row, 0).text() == "DIR":
            self.current_path = path_item.text()
            self.path_input.setText(self.current_path)
            self._load_files()

    def _context_menu(self, pos):
        row = self.table.indexAt(pos).row()
        if row < 0:
            return
        path = self.table.item(row, 2).text() if self.table.item(row, 2) else ""
        name = self.table.item(row, 1).text() if self.table.item(row, 1) else ""

        menu = QMenu(self)
        rename_action = QAction("Rename", self)
        copy_action = QAction("Copy", self)
        move_action = QAction("Move", self)
        delete_action = QAction("Delete", self)
        chmod_action = QAction("Chmod", self)
        chown_action = QAction("Chown", self)

        rename_action.triggered.connect(lambda: self._rename_with(path))
        copy_action.triggered.connect(lambda: self._copy_with(path))
        move_action.triggered.connect(lambda: self._move_with(path))
        delete_action.triggered.connect(lambda: self._delete_with(path, name))
        chmod_action.triggered.connect(lambda: self._chmod_with(path))
        chown_action.triggered.connect(lambda: self._chown_with(path))

        menu.addAction(rename_action)
        menu.addAction(copy_action)
        menu.addAction(move_action)
        menu.addSeparator()
        menu.addAction(delete_action)
        menu.addSeparator()
        menu.addAction(chmod_action)
        menu.addAction(chown_action)

        menu.exec(self.table.viewport().mapToGlobal(pos))

    def _get_selected_path(self):
        row = self.table.currentRow()
        if row >= 0 and self.table.item(row, 2):
            return self.table.item(row, 2).text()
        return ""

    def _create_file(self):
        name, ok = QInputDialog.getText(self, "Create File", "Filename:")
        if ok and name:
            self._run_script("create_file.sh", [self.current_path, name])

    def _create_folder(self):
        name, ok = QInputDialog.getText(self, "Create Folder", "Folder name:")
        if ok and name:
            self._run_script("create_folder.sh", [self.current_path, name])

    def _rename_with(self, source):
        new_name, ok = QInputDialog.getText(self, "Rename", "New name:", text=os.path.basename(source))
        if ok and new_name:
            self._run_script("rename_file.sh", [source, new_name])

    def _rename(self):
        path = self._get_selected_path()
        if path:
            self._rename_with(path)

    def _copy_with(self, source):
        dest, ok = QInputDialog.getText(self, "Copy", "Destination path:")
        if ok and dest:
            self._run_script("copy_file.sh", [source, dest])

    def _copy(self):
        path = self._get_selected_path()
        if path:
            self._copy_with(path)

    def _move_with(self, source):
        dest, ok = QInputDialog.getText(self, "Move", "Destination path:")
        if ok and dest:
            self._run_script("move_file.sh", [source, dest])

    def _move(self):
        path = self._get_selected_path()
        if path:
            self._move_with(path)

    def _delete_with(self, target, name):
        reply = QMessageBox.question(
            self, "Confirm Delete",
            f"Are you sure you want to delete '{name}'?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
        )
        if reply == QMessageBox.StandardButton.Yes:
            self._run_script("delete_file.sh", [target])

    def _delete(self):
        path = self._get_selected_path()
        name = self.table.item(self.table.currentRow(), 1).text() if self.table.currentRow() >= 0 else ""
        if path:
            self._delete_with(path, name)

    def _search(self):
        keyword, ok = QInputDialog.getText(self, "Search", "Search keyword:")
        if ok and keyword:
            success, output = self.executor.run("search_file.sh", [self.current_path, keyword])
            self.output.append(f"$ search_file.sh {self.current_path} {keyword}\n")
            if success:
                self.output.append(f"Result:\n{output}\n")
            else:
                self.output.append(f"✗ {output}\n")

    def _chmod_with(self, target):
        mode, ok = QInputDialog.getText(self, "Chmod", "Permission mode (e.g. 755):")
        if ok and mode:
            self._run_script("chmod_file.sh", [target, mode])

    def _chmod(self):
        path = self._get_selected_path()
        if path:
            self._chmod_with(path)

    def _chown_with(self, target):
        owner, ok1 = QInputDialog.getText(self, "Chown", "Owner:")
        if ok1 and owner:
            group, ok2 = QInputDialog.getText(self, "Chown", "Group:")
            if ok2:
                self._run_script("chown_file.sh", [target, owner, group])

    def _chown(self):
        path = self._get_selected_path()
        if path:
            self._chown_with(path)
