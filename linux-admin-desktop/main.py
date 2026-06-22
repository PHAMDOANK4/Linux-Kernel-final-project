#!/usr/bin/env python3
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from PyQt6.QtWidgets import QApplication

from app.auth import AuthManager
from app.database import init_db
from ui.main_window import MainWindow


def main():
    init_db()

    app = QApplication(sys.argv)
    app.setApplicationName("Linux Administration Desktop")
    app.setStyle("Fusion")

    auth = AuthManager()
    window = MainWindow(auth)
    window.show()
    sys.exit(app.exec())


if __name__ == "__main__":
    main()
