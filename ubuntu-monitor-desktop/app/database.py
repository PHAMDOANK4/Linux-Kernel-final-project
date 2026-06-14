"""
Database — SQLite audit log cho các thao tác người dùng.

Lưu lại tất cả hành động quan trọng (kill process, ping, ...)
vào SQLite database để phục vụ kiểm tra và học tập.
"""

import os
import sys
import logging
from datetime import datetime, timezone

from sqlalchemy import create_engine, Column, Integer, String, DateTime, Text
from sqlalchemy.orm import declarative_base, sessionmaker


def _get_data_dir():
    if getattr(sys, "frozen", False):
        return os.path.join(os.path.expanduser("~"), ".ubuntu-monitor-desktop")
    return os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))


DATA_DIR = _get_data_dir()
DB_PATH = os.path.join(DATA_DIR, "instance", "monitor.db")
LOG_FILE = os.path.join(DATA_DIR, "logs", "audit.log")

os.makedirs(os.path.join(DATA_DIR, "instance"), exist_ok=True)
os.makedirs(os.path.join(DATA_DIR, "logs"), exist_ok=True)

engine = create_engine(f"sqlite:///{DB_PATH}", echo=False)
SessionLocal = sessionmaker(bind=engine)
Base = declarative_base()

# File logging
logging.basicConfig(
    filename=LOG_FILE,
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
)
_file_logger = logging.getLogger("monitor")


class AuditLog(Base):
    __tablename__ = "audit_logs"

    id = Column(Integer, primary_key=True)
    timestamp = Column(DateTime, default=lambda: datetime.now(timezone.utc), nullable=False, index=True)
    action = Column(String(120), nullable=False)
    module = Column(String(80), nullable=False)
    detail = Column(Text, default="")


def init_db():
    Base.metadata.create_all(engine)


def get_session():
    return SessionLocal()


def record_action(action: str, module: str, detail: str = ""):
    """
    Ghi lại hành động vào DB và file log.
    
    Đây là cơ chế audit trail — mọi thao tác quan trọng đều
    được ghi lại để phục vụ debug và bảo mật.
    Uncomment session code khi cần DB logging.
    """
    # DB logging
    # session = get_session()
    # try:
    #     entry = AuditLog(action=action, module=module, detail=detail)
    #     session.add(entry)
    #     session.commit()
    # finally:
    #     session.close()

    # File logging (luôn hoạt động)
    _file_logger.info("[%s] %s — %s", module, action, detail)
