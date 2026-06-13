from __future__ import annotations

from pathlib import Path
import os

BASE_DIR = Path(__file__).resolve().parent.parent
INSTANCE_DIR = BASE_DIR / "instance"
LOG_DIR = BASE_DIR / "logs"
SCRIPT_DIR = BASE_DIR / "scripts"

INSTANCE_DIR.mkdir(exist_ok=True)
LOG_DIR.mkdir(exist_ok=True)


class Config:
    SECRET_KEY = os.environ.get("SECRET_KEY", "change-me-in-production")
    SQLALCHEMY_DATABASE_URI = os.environ.get(
        "DATABASE_URL",
        f"sqlite:///{INSTANCE_DIR / 'ubuntu_monitor.db'}",
    )
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    SESSION_COOKIE_HTTPONLY = True
    SESSION_COOKIE_SAMESITE = "Lax"
    JSON_SORT_KEYS = False
    SYSTEM_LOG_FILE = str(LOG_DIR / "system.log")
    DEFAULT_ADMIN_USERNAME = os.environ.get("DEFAULT_ADMIN_USERNAME", "admin")
    DEFAULT_ADMIN_PASSWORD = os.environ.get("DEFAULT_ADMIN_PASSWORD", "Admin@12345")
    DEFAULT_OPERATOR_USERNAME = os.environ.get("DEFAULT_OPERATOR_USERNAME", "operator")
    DEFAULT_OPERATOR_PASSWORD = os.environ.get("DEFAULT_OPERATOR_PASSWORD", "Operator@12345")
    SCRIPT_TIMEOUT = int(os.environ.get("SCRIPT_TIMEOUT", "30"))
