from werkzeug.security import check_password_hash
from app.database import User, get_session


class AuthManager:
    def __init__(self):
        self._user = None

    def login(self, username: str, password: str) -> bool:
        session = get_session()
        try:
            user = session.query(User).filter_by(username=username).first()
            if user and check_password_hash(user.password_hash, password):
                self._user = {
                    "id": user.id,
                    "username": user.username,
                    "role": user.role,
                }
                return True
            return False
        finally:
            session.close()

    def logout(self):
        self._user = None

    @property
    def current_user(self) -> dict | None:
        return self._user

    @property
    def is_authenticated(self) -> bool:
        return self._user is not None

    @property
    def is_admin(self) -> bool:
        return self._user is not None and self._user["role"] == "admin"

    @property
    def username(self) -> str:
        return self._user["username"] if self._user else ""

    @property
    def role(self) -> str:
        return self._user["role"] if self._user else ""
