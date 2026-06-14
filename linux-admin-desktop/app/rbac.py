from app.auth import AuthManager


def require_admin(auth: AuthManager) -> bool:
    return auth.is_admin


def require_auth(auth: AuthManager) -> bool:
    return auth.is_authenticated
