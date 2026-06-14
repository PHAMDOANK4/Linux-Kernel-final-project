from PyQt6.QtWidgets import (
    QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, QLabel,
    QPushButton, QListWidget, QStackedWidget, QMessageBox,
    QFrame, QApplication, QSizePolicy, QSpacerItem,
)
from PyQt6.QtCore import Qt
from PyQt6.QtGui import QFont

from ui.file_manager_widget import FileManagerWidget
from ui.task_scheduler_widget import TaskSchedulerWidget
from ui.system_time_widget import SystemTimeWidget
from ui.package_manager_widget import PackageManagerWidget
from ui.logs_viewer_widget import LogsViewerWidget


class MainWindow(QMainWindow):
    def __init__(self, auth_manager):
        super().__init__()
        self.auth = auth_manager
        self.setWindowTitle("Linux Administration Desktop")
        self.resize(1100, 720)

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

        logout_btn = QPushButton("Logout")
        logout_btn.setStyleSheet("""
            QPushButton {
                background: rgba(255,255,255,0.2); color: white;
                padding: 6px 16px; border-radius: 6px; font-size: 13px;
            }
            QPushButton:hover { background: rgba(255,255,255,0.35); }
        """)
        logout_btn.clicked.connect(self._handle_logout)
        header_layout.addWidget(logout_btn)

        main_layout.addWidget(header)

        body = QWidget()
        body_layout = QHBoxLayout(body)
        body_layout.setContentsMargins(0, 0, 0, 0)
        body_layout.setSpacing(0)

        sidebar = QFrame()
        sidebar.setFixedWidth(200)
        sidebar.setStyleSheet("""
            QFrame {
                background: #1e293b;
                border-right: 1px solid #334155;
            }
        """)
        sidebar_layout = QVBoxLayout(sidebar)
        sidebar_layout.setContentsMargins(0, 8, 0, 8)
        sidebar_layout.setSpacing(2)

        self.nav_list = QListWidget()
        self.nav_list.setStyleSheet("""
            QListWidget {
                background: transparent; border: none;
                font-size: 14px; color: #cbd5e1;
            }
            QListWidget::item {
                padding: 12px 16px; border-radius: 6px;
                margin: 2px 8px;
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

        self.stack = QStackedWidget()
        self.stack.setStyleSheet("background: #f4f7fb;")
        body_layout.addWidget(self.stack, 1)

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
            self.pages.append("Audit Logs")
            self.page_widgets.append(TaskSchedulerWidget(self.auth))
            self.page_widgets.append(LogsViewerWidget(self.auth))

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

    def _handle_logout(self):
        reply = QMessageBox.question(
            self, "Logout", "Are you sure you want to logout?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
        )
        if reply == QMessageBox.StandardButton.Yes:
            self.auth.logout()
            self.close()
