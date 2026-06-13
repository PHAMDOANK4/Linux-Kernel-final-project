from __future__ import annotations

from flask import Blueprint, jsonify, render_template, request

from ..extensions import db
from ..models import AuditLog, Role, User
from ..services.audit_service import record_audit
from ..utils.context import get_current_user
from ..utils.decorators import admin_required, login_required

admin_bp = Blueprint("admin", __name__, url_prefix="/admin")


@admin_bp.get("/users")
@login_required
@admin_required
def users():
    return render_template("admin/users.html")


def _user_to_json(u: User) -> dict:
    return {
        "id": u.id,
        "username": u.username,
        "full_name": u.full_name,
        "role": u.role_name,
        "is_active": u.is_active,
        "created_at": u.created_at.strftime("%Y-%m-%d %H:%M:%S") if u.created_at else "",
    }


@admin_bp.get("/api/users")
@login_required
@admin_required
def api_list_users():
    users_list = User.query.order_by(User.username.asc()).all()
    return jsonify({"users": [_user_to_json(u) for u in users_list]})


@admin_bp.post("/api/users")
@login_required
@admin_required
def api_create_user():
    user = get_current_user()
    data = request.get_json(silent=True) or {}
    username = data.get("username", "").strip()
    password = data.get("password", "")
    role_name = data.get("role", "Operator")
    full_name = data.get("full_name", "").strip()

    if not username or not password:
        return jsonify({"error": "Username và password không được để trống"}), 400
    role = Role.query.filter_by(name=role_name).first()
    if not role:
        return jsonify({"error": "Role không hợp lệ"}), 400
    if User.query.filter_by(username=username).first():
        return jsonify({"error": "Username đã tồn tại"}), 400

    new_user = User(username=username, full_name=full_name, role=role)
    new_user.set_password(password)
    db.session.add(new_user)
    db.session.commit()
    record_audit(user.username, "Create User", "Admin", "SUCCESS", username)
    return jsonify({"success": True, "message": "Tạo người dùng thành công", "user": _user_to_json(new_user)})


@admin_bp.post("/api/users/<int:user_id>/toggle")
@login_required
@admin_required
def api_toggle_user(user_id: int):
    admin_user = get_current_user()
    target = db.session.get(User, user_id)
    if not target:
        return jsonify({"error": "Không tìm thấy người dùng"}), 404
    target.is_active = not target.is_active
    db.session.commit()
    status = "kích hoạt" if target.is_active else "vô hiệu hóa"
    record_audit(admin_user.username, "Toggle User", "Admin", "SUCCESS", f"{target.username} -> {status}")
    return jsonify({"success": True, "message": f"Đã {status} người dùng", "user": _user_to_json(target)})


@admin_bp.post("/api/users/<int:user_id>/edit")
@login_required
@admin_required
def api_edit_user(user_id: int):
    admin_user = get_current_user()
    target = db.session.get(User, user_id)
    if not target:
        return jsonify({"error": "Không tìm thấy người dùng"}), 404
    data = request.get_json(silent=True) or {}
    full_name = data.get("full_name", "").strip()
    role_name = data.get("role", "")
    if full_name:
        target.full_name = full_name
    if role_name:
        role = Role.query.filter_by(name=role_name).first()
        if not role:
            return jsonify({"error": "Role không hợp lệ"}), 400
        target.role = role
    db.session.commit()
    record_audit(admin_user.username, "Edit User", "Admin", "SUCCESS", target.username)
    return jsonify({"success": True, "message": "Cập nhật thành công", "user": _user_to_json(target)})


@admin_bp.post("/api/users/<int:user_id>/reset-pw")
@login_required
@admin_required
def api_reset_password(user_id: int):
    admin_user = get_current_user()
    target = db.session.get(User, user_id)
    if not target:
        return jsonify({"error": "Không tìm thấy người dùng"}), 404
    data = request.get_json(silent=True) or {}
    password = data.get("password", "")
    if not password or len(password) < 3:
        return jsonify({"error": "Mật khẩu phải có ít nhất 3 ký tự"}), 400
    target.set_password(password)
    db.session.commit()
    record_audit(admin_user.username, "Reset Password", "Admin", "SUCCESS", target.username)
    return jsonify({"success": True, "message": "Đặt lại mật khẩu thành công"})


@admin_bp.post("/api/users/<int:user_id>/delete")
@login_required
@admin_required
def api_delete_user(user_id: int):
    admin_user = get_current_user()
    target = db.session.get(User, user_id)
    if not target:
        return jsonify({"error": "Không tìm thấy người dùng"}), 404
    if target.id == admin_user.id:
        return jsonify({"error": "Không thể xóa chính mình"}), 400
    username = target.username
    db.session.delete(target)
    db.session.commit()
    record_audit(admin_user.username, "Delete User", "Admin", "SUCCESS", username)
    return jsonify({"success": True, "message": f"Đã xóa người dùng {username}"})


@admin_bp.get("/api/roles")
@login_required
@admin_required
def api_list_roles():
    roles = Role.query.order_by(Role.name.asc()).all()
    return jsonify({"roles": [{"id": r.id, "name": r.name, "description": r.description} for r in roles]})


@admin_bp.get("/api/audit-logs")
@login_required
@admin_required
def api_audit_logs():
    logs = AuditLog.query.order_by(AuditLog.timestamp.desc()).limit(50).all()
    return jsonify({
        "logs": [
            {
                "id": log.id,
                "username": log.username,
                "action": log.action,
                "module": log.module,
                "result": log.result,
                "details": log.details,
                "timestamp": log.timestamp.strftime("%Y-%m-%d %H:%M:%S") if log.timestamp else "",
            }
            for log in logs
        ]
    })
