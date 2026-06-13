from __future__ import annotations

from functools import wraps

from flask import flash, redirect, session, url_for

from .context import get_current_user


def login_required(view):
    @wraps(view)
    def wrapped(*args, **kwargs):
        if not session.get("user_id"):
            flash("Vui lòng đăng nhập.", "warning")
            return redirect(url_for("auth.login"))
        return view(*args, **kwargs)

    return wrapped


def role_required(*allowed_roles):
    def decorator(view):
        @wraps(view)
        def wrapped(*args, **kwargs):
            user = get_current_user()
            if not user or user.role_name not in allowed_roles:
                flash("Bạn không có quyền thực hiện tác vụ này.", "danger")
                return redirect(url_for("dashboard.index"))
            return view(*args, **kwargs)

        return wrapped

    return decorator


def admin_required(view):
    return role_required("Admin")(view)
