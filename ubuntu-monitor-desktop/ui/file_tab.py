"""
File Tab — trình duyệt file system với /proc insights.

Hiển thị cấu trúc thư mục dạng tree, cho phép xem metadata
stat(2) của từng file: permissions, owner, size, inode, v.v.
"""

import os

from PyQt6.QtCore import Qt
from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QTreeWidget, QTreeWidgetItem,
    QPushButton, QLabel, QHeaderView, QTextEdit, QSplitter, QLineEdit,
    QFrame, QAbstractItemView,
)

from . import styles
from app.file_monitor import (
    list_directory,
    get_file_detail,
    read_text_file,
    is_text_file,
    format_file_size,
)
from app.kernel_utils import read_proc_file


class FileTab(QWidget):
    def __init__(self):
        super().__init__()
        self._current_path = "/"
        self.setup_ui()
        self.load_directory("/")

    def setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(12)

        # Header
        header = QHBoxLayout()
        title = QLabel("File Browser")
        title.setStyleSheet(styles.TITLE_STYLE)
        header.addWidget(title)

        header.addStretch()

        self.path_input = QLineEdit("/")
        self.path_input.setStyleSheet(styles.INPUT_STYLE)
        self.path_input.returnPressed.connect(self._navigate_to_path)
        header.addWidget(self.path_input, stretch=1)

        self.go_btn = QPushButton("Go")
        self.go_btn.setStyleSheet(styles.BTN_PRIMARY)
        self.go_btn.clicked.connect(self._navigate_to_path)
        header.addWidget(self.go_btn)

        self.up_btn = QPushButton("↑ Up")
        self.up_btn.setStyleSheet(styles.BTN_GHOST)
        self.up_btn.clicked.connect(self._go_up)
        header.addWidget(self.up_btn)

        layout.addLayout(header)

        # Content splitter
        splitter = QSplitter(Qt.Orientation.Horizontal)

        # Tree
        tree_container = QFrame()
        tree_container.setStyleSheet(f"""
            QFrame {{
                background: {styles.COLORS["bg_secondary"]};
                border: 1px solid {styles.COLORS["border"]};
                border-radius: 8px;
            }}
        """)
        tree_layout = QVBoxLayout(tree_container)
        tree_layout.setContentsMargins(8, 8, 8, 8)

        self.tree = QTreeWidget()
        self.tree.setStyleSheet(styles.TABLE_STYLE)
        self.tree.setHeaderLabels(["Name", "Type", "Size", "Permissions", "Owner", "Modified", "Inode"])
        self.tree.setColumnWidth(0, 200)
        self.tree.setColumnWidth(1, 80)
        self.tree.setColumnWidth(2, 80)
        self.tree.setColumnWidth(3, 90)
        self.tree.setColumnWidth(4, 80)
        self.tree.setColumnWidth(5, 150)
        self.tree.setColumnWidth(6, 70)
        self.tree.setAlternatingRowColors(True)
        self.tree.setSelectionMode(QAbstractItemView.SelectionMode.SingleSelection)
        self.tree.itemDoubleClicked.connect(self._on_item_double_click)
        tree_layout.addWidget(self.tree)
        splitter.addWidget(tree_container)

        # Detail / Preview panel
        detail_container = QFrame()
        detail_container.setStyleSheet(f"""
            QFrame {{
                background: {styles.COLORS["bg_secondary"]};
                border: 1px solid {styles.COLORS["border"]};
                border-radius: 8px;
            }}
        """)
        detail_layout = QVBoxLayout(detail_container)
        detail_layout.setContentsMargins(8, 8, 8, 8)

        detail_header = QLabel("File Detail / Preview")
        detail_header.setStyleSheet(f"""
            color: {styles.COLORS["text"]};
            font-size: 14px;
            font-weight: bold;
        """)
        detail_layout.addWidget(detail_header)

        self.detail_view = QTextEdit()
        self.detail_view.setStyleSheet(styles.TERMINAL_STYLE)
        self.detail_view.setReadOnly(True)
        detail_layout.addWidget(self.detail_view)
        splitter.addWidget(detail_container)

        splitter.setSizes([500, 400])
        layout.addWidget(splitter, stretch=1)

    def load_directory(self, path):
        self._current_path = path
        self.path_input.setText(path)
        self.tree.clear()
        self.detail_view.clear()

        # Parent directory entry (..)
        if path != "/":
            parent_item = QTreeWidgetItem(["..", "directory", "", "", "", "", ""])
            parent_item.setData(0, Qt.ItemDataRole.UserRole, os.path.dirname(path.rstrip("/")))
            font = parent_item.font(0)
            font.setBold(True)
            parent_item.setFont(0, font)
            parent_item.setForeground(0, self._color(styles.COLORS["accent"]))
            self.tree.addTopLevelItem(parent_item)

        entries = list_directory(path)
        for e in entries:
            item = QTreeWidgetItem([
                e["name"],
                e["type"],
                format_file_size(e["size"]) if e["type"] != "directory" else "-",
                e["permissions"],
                e["owner"],
                e["modified"],
                str(e.get("inode", "")),
            ])
            item.setData(0, Qt.ItemDataRole.UserRole, e["path"])
            item.setData(0, Qt.ItemDataRole.ToolTipRole, e["path"])

            # Color code by type
            if e["is_dir"]:
                item.setForeground(0, self._color(styles.COLORS["accent"]))
                font = item.font(0)
                font.setBold(True)
                item.setFont(0, font)

            self.tree.addTopLevelItem(item)

    def _on_item_double_click(self, item, column):
        path = item.data(0, Qt.ItemDataRole.UserRole)
        if not path:
            return

        # Find entry data
        name = item.text(0)
        if name == "..":
            self.load_directory(path)
            return

        entry_type = item.text(1)
        if entry_type == "directory":
            self.load_directory(path)
        else:
            self._show_file_detail(path)

    def _show_file_detail(self, path):
        detail = get_file_detail(path)
        lines = []
        for k, v in detail.items():
            lines.append(f"{k}: {v}")

        self.detail_view.setText("\n".join(lines))

        # Preview text files
        if is_text_file(path):
            content = read_text_file(path, max_size=51200)
            if content and not content.startswith("[Error"):
                preview = "\n" + "=" * 50 + "\nCONTENT PREVIEW:\n" + "=" * 50 + f"\n{content[:3000]}"
                self.detail_view.append(preview)

    def _navigate_to_path(self):
        path = self.path_input.text().strip()
        if os.path.isdir(path):
            self.load_directory(path)
        elif os.path.isfile(path):
            self._show_file_detail(path)
            dir_path = os.path.dirname(path)
            self.path_input.setText(dir_path)
            self._current_path = dir_path

    def _go_up(self):
        if self._current_path != "/":
            parent = os.path.dirname(self._current_path.rstrip("/"))
            self.load_directory(parent or "/")

    def _color(self, hex_color):
        from PyQt6.QtGui import QColor
        return QColor(hex_color)
