from __future__ import annotations

from flask import session

from ..extensions import db
from ..models import User


def get_current_user() -> User | None:
    user_id = session.get("user_id")
    if not user_id:
        return None
    return db.session.get(User, user_id)
