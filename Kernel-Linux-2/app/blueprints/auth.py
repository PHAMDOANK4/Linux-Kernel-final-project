from __future__ import annotations

from flask import Blueprint, flash, redirect, render_template, request, session, url_for

from ..extensions import db
from ..models import User
from ..services.audit_service import record_audit
from ..utils.context import get_current_user

auth_bp = Blueprint("auth", __name__)


@auth_bp.get("/login")
def login():
    if session.get("user_id"):
        return redirect(url_for("dashboard.index"))
    return render_template("auth/login.html")


@auth_bp.post("/login")
def login_post():
    username = request.form.get("username", "").strip()
    password = request.form.get("password", "")
    user = User.query.filter_by(username=username).first()

    if not user or not user.is_active or not user.check_password(password):
        flash("Thông tin đăng nhập không hợp lệ.", "danger")
        if username:
            record_audit(username, "Login", "Auth", "FAIL", "Invalid credentials")
        return redirect(url_for("auth.login"))

    session["user_id"] = user.id
    session["username"] = user.username
    session["role"] = user.role_name
    record_audit(user.username, "Login", "Auth", "SUCCESS", "User logged in")
    flash("Đăng nhập thành công.", "success")
    return redirect(url_for("dashboard.index"))


@auth_bp.get("/logout")
def logout():
    user = get_current_user()
    if user:
        record_audit(user.username, "Logout", "Auth", "SUCCESS", "User logged out")
    session.clear()
    flash("Đã đăng xuất.", "info")
    return redirect(url_for("auth.login"))
