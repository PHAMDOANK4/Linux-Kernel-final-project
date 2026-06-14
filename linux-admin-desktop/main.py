#!/usr/bin/env python3
import sys
import os
from pathlib import Path

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from PyQt6.QtWidgets import QApplication
from PyQt6.QtGui import QIcon

from app.database import init_db
from app.auth import AuthManager
from ui.login_window import LoginWindow
from ui.main_window import MainWindow


def main():
    init_db()

    app = QApplication(sys.argv)
    app.setApplicationName("Linux Administration Desktop")
    app.setStyle("Fusion")

    auth = AuthManager()

    login = LoginWindow(auth)
    if login.exec() == LoginWindow.DialogCode.Accepted:
        window = MainWindow(auth)
        window.show()
        sys.exit(app.exec())
    else:
        sys.exit(0)


if __name__ == "__main__":
    main()
