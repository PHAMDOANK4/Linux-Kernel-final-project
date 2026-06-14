import os
import sys
from datetime import datetime

from sqlalchemy import create_engine, Column, Integer, String, DateTime, Text
from sqlalchemy.orm import declarative_base, sessionmaker
from werkzeug.security import generate_password_hash


def _get_data_dir():
    if getattr(sys, "frozen", False):
        return os.path.join(os.path.expanduser("~"), ".linux-admin-desktop")
    return os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))


DATA_DIR = _get_data_dir()
DB_PATH = os.path.join(DATA_DIR, "instance", "dashboard.db")
engine = create_engine(f"sqlite:///{DB_PATH}", echo=False)
SessionLocal = sessionmaker(bind=engine)
Base = declarative_base()


class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True)
    username = Column(String(64), unique=True, nullable=False)
    password_hash = Column(String(255), nullable=False)
    role = Column(String(16), nullable=False, default="user")
    created_at = Column(DateTime, nullable=False, default=datetime.utcnow)


class ActionLog(Base):
    __tablename__ = "action_logs"

    id = Column(Integer, primary_key=True)
    username = Column(String(64), nullable=False)
    action = Column(String(255), nullable=False)
    result = Column(String(32), nullable=False)
    detail = Column(Text, nullable=False)
    created_at = Column(DateTime, nullable=False, default=datetime.utcnow)


def init_db():
    os.makedirs(os.path.join(DATA_DIR, "instance"), exist_ok=True)
    os.makedirs(os.path.join(DATA_DIR, "logs"), exist_ok=True)
    Base.metadata.create_all(engine)

    admin_username = os.getenv("ADMIN_USERNAME", "admin")
    admin_password = os.getenv("ADMIN_PASSWORD", "admin123")
    user_username = os.getenv("USER_USERNAME", "user")
    user_password = os.getenv("USER_PASSWORD", "user123")

    session = SessionLocal()
    try:
        if not session.query(User).filter_by(username=admin_username).first():
            session.add(User(
                username=admin_username,
                password_hash=generate_password_hash(admin_password),
                role="admin",
            ))
        if not session.query(User).filter_by(username=user_username).first():
            session.add(User(
                username=user_username,
                password_hash=generate_password_hash(user_password),
                role="user",
            ))
        session.commit()
    finally:
        session.close()


def get_session():
    return SessionLocal()
