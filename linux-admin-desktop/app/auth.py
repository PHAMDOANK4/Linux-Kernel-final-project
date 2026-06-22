import getpass


class AuthManager:
    def __init__(self):
        self._user = {
            "id": 1,
            "username": getpass.getuser(),
            "role": "admin",
        }

    @property
    def current_user(self) -> dict:
        return self._user

    @property
    def is_authenticated(self) -> bool:
        return True

    @property
    def is_admin(self) -> bool:
        return True

    @property
    def username(self) -> str:
        return self._user["username"]

    @property
    def role(self) -> str:
        return self._user["role"]
