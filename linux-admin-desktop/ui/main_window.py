from PyQt6.QtWidgets import (
    QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, QLabel,
    QListWidget, QStackedWidget, QFrame, QSizePolicy, QSpacerItem,
    QScrollArea,
)
from PyQt6.QtCore import Qt
from PyQt6.QtGui import QFont

from ui.file_manager_widget import FileManagerWidget
from ui.task_scheduler_widget import TaskSchedulerWidget
from ui.system_time_widget import SystemTimeWidget
from ui.package_manager_widget import PackageManagerWidget


class MainWindow(QMainWindow):
    def __init__(self, auth_manager):
        super().__init__()
        self.auth = auth_manager
        self.setWindowTitle("Linux Administration Desktop")
        self.resize(960, 720)

        self._setup_ui()
        self._populate_nav()

    def _setup_ui(self):
        central = QWidget()
        self.setCentralWidget(central)

        main_layout = QVBoxLayout(central)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(0)

        header = QFrame()
        header.setStyleSheet("""
            QFrame {
                background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
                    stop:0 #0b7285, stop:1 #1565c0);
                padding: 8px 16px;
            }
        """)
        header.setFixedHeight(56)
        header_layout = QHBoxLayout(header)

        title = QLabel("Linux Administration Desktop")
        title.setFont(QFont("", 16, QFont.Weight.Bold))
        title.setStyleSheet("color: white;")
        header_layout.addWidget(title)

        header_layout.addSpacerItem(QSpacerItem(40, 20, QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Minimum))

        self.user_label = QLabel()
        self.user_label.setStyleSheet("""
            color: white; background: rgba(255,255,255,0.15);
            padding: 4px 12px; border-radius: 10px; font-size: 13px;
        """)
        header_layout.addWidget(self.user_label)

        main_layout.addWidget(header)

        body = QWidget()
        body_layout = QHBoxLayout(body)
        body_layout.setContentsMargins(0, 0, 0, 0)
        body_layout.setSpacing(0)

        sidebar = QFrame()
        sidebar.setFixedWidth(180)
        sidebar.setStyleSheet("""
            QFrame {
                background: #1e293b;
                border-right: 1px solid #334155;
            }
        """)
        sidebar_layout = QVBoxLayout(sidebar)
        sidebar_layout.setContentsMargins(0, 6, 0, 6)
        sidebar_layout.setSpacing(1)

        self.nav_list = QListWidget()
        self.nav_list.setStyleSheet("""
            QListWidget {
                background: transparent; border: none;
                font-size: 13px; color: #cbd5e1;
            }
            QListWidget::item {
                padding: 10px 14px; border-radius: 5px;
                margin: 1px 6px;
            }
            QListWidget::item:selected {
                background: #0b7285; color: white;
            }
            QListWidget::item:hover:!selected {
                background: #334155; color: white;
            }
        """)
        self.nav_list.currentRowChanged.connect(self._switch_page)
        sidebar_layout.addWidget(self.nav_list)

        body_layout.addWidget(sidebar)

        self.scroll = QScrollArea()
        self.scroll.setWidgetResizable(True)
        self.scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        self.scroll.setStyleSheet("""
            QScrollArea { border: none; background: #f4f7fb; }
            QScrollBar:vertical {
                background: #e2e8f0; width: 6px;
                border-radius: 3px;
            }
            QScrollBar::handle:vertical {
                background: #94a3b8; border-radius: 3px;
                min-height: 20px;
            }
            QScrollBar::handle:vertical:hover { background: #64748b; }
            QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {
                height: 0; background: none;
            }
        """)

        self.stack = QStackedWidget()
        self.stack.setStyleSheet("background: transparent;")
        self.scroll.setWidget(self.stack)

        body_layout.addWidget(self.scroll, 1)

        main_layout.addWidget(body, 1)

    def _populate_nav(self):
        self.pages = []
        self.page_widgets = []

        self.pages.append("Dashboard")
        self.pages.append("File Management")
        self.pages.append("System Time")
        self.pages.append("Packages")

        dash = QWidget()
        dash_layout = QVBoxLayout(dash)
        welcome = QLabel(f"Welcome, {self.auth.username}!")
        welcome.setFont(QFont("", 24, QFont.Weight.Bold))
        welcome.setStyleSheet("color: #1f2933;")
        welcome.setAlignment(Qt.AlignmentFlag.AlignCenter)
        dash_layout.addWidget(welcome)

        role_label = QLabel(f"Role: {self.auth.role.upper()}")
        role_label.setFont(QFont("", 14))
        role_label.setStyleSheet("color: #64748b;")
        role_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        dash_layout.addWidget(role_label)

        self.page_widgets.append(dash)
        self.page_widgets.append(FileManagerWidget(self.auth))
        self.page_widgets.append(SystemTimeWidget(self.auth))
        self.page_widgets.append(PackageManagerWidget(self.auth))

        if self.auth.is_admin:
            self.pages.append("Task Scheduler")
            self.page_widgets.append(TaskSchedulerWidget(self.auth))

        for w in self.page_widgets:
            self.stack.addWidget(w)

        self.nav_list.addItems(self.pages)
        self.user_label.setText(f"{self.auth.username}  •  {self.auth.role.upper()}")

    def _switch_page(self, index):
        if 0 <= index < len(self.page_widgets):
            widget = self.page_widgets[index]
            if hasattr(widget, "on_activate"):
                widget.on_activate()
            self.stack.setCurrentWidget(widget)
