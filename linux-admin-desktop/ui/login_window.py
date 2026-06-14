from PyQt6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QLabel, QLineEdit,
    QPushButton, QMessageBox, QSpacerItem, QSizePolicy, QFrame,
)
from PyQt6.QtCore import Qt
from PyQt6.QtGui import QFont


class LoginWindow(QDialog):
    def __init__(self, auth_manager):
        super().__init__()
        self.auth = auth_manager
        self.setWindowTitle("Linux Administration Desktop — Login")
        self.setFixedSize(420, 320)
        self.setStyleSheet("""
            QDialog {
                background: qlineargradient(x1:0, y1:0, x2:1, y2:1,
                    stop:0 #0b7285, stop:1 #1565c0);
            }
        """)
        self._setup_ui()

    def _setup_ui(self):
        layout = QVBoxLayout()
        layout.setAlignment(Qt.AlignmentFlag.AlignCenter)

        layout.addSpacerItem(QSpacerItem(20, 40, QSizePolicy.Policy.Minimum, QSizePolicy.Policy.Expanding))

        title = QLabel("Linux Administration")
        title.setFont(QFont("", 22, QFont.Weight.Bold))
        title.setStyleSheet("color: white;")
        title.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(title)

        subtitle = QLabel("Desktop Dashboard")
        subtitle.setFont(QFont("", 14))
        subtitle.setStyleSheet("color: rgba(255,255,255,0.8);")
        subtitle.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(subtitle)

        layout.addSpacerItem(QSpacerItem(20, 30, QSizePolicy.Policy.Minimum, QSizePolicy.Policy.Minimum))

        card = QFrame()
        card.setStyleSheet("""
            QFrame {
                background: white;
                border-radius: 12px;
                padding: 20px;
            }
        """)
        card_layout = QVBoxLayout()

        self.username_input = QLineEdit()
        self.username_input.setPlaceholderText("Username")
        self.username_input.setStyleSheet("""
            QLineEdit {
                padding: 10px; border: 2px solid #ddd;
                border-radius: 6px; font-size: 14px;
            }
            QLineEdit:focus { border-color: #0b7285; }
        """)
        card_layout.addWidget(self.username_input)

        self.password_input = QLineEdit()
        self.password_input.setPlaceholderText("Password")
        self.password_input.setEchoMode(QLineEdit.EchoMode.Password)
        self.password_input.setStyleSheet("""
            QLineEdit {
                padding: 10px; border: 2px solid #ddd;
                border-radius: 6px; font-size: 14px;
            }
            QLineEdit:focus { border-color: #0b7285; }
        """)
        card_layout.addWidget(self.password_input)

        self.error_label = QLabel()
        self.error_label.setStyleSheet("color: #d32f2f; font-size: 12px;")
        self.error_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.error_label.hide()
        card_layout.addWidget(self.error_label)

        login_btn = QPushButton("Login")
        login_btn.setStyleSheet("""
            QPushButton {
                background: #0b7285; color: white; padding: 10px;
                border-radius: 6px; font-size: 15px; font-weight: bold;
            }
            QPushButton:hover { background: #1565c0; }
            QPushButton:pressed { background: #094c5e; }
        """)
        login_btn.clicked.connect(self._handle_login)
        card_layout.addWidget(login_btn)

        card.setLayout(card_layout)
        layout.addWidget(card)

        layout.addSpacerItem(QSpacerItem(20, 40, QSizePolicy.Policy.Minimum, QSizePolicy.Policy.Expanding))

        self.setLayout(layout)

        self.password_input.returnPressed.connect(login_btn.click)

    def _handle_login(self):
        username = self.username_input.text().strip()
        password = self.password_input.text()

        if not username or not password:
            self.error_label.setText("Please enter username and password.")
            self.error_label.show()
            return

        if self.auth.login(username, password):
            self.accept()
        else:
            self.error_label.setText("Invalid username or password.")
            self.error_label.show()
