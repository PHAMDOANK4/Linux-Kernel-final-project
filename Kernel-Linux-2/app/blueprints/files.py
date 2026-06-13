from __future__ import annotations

import json

from flask import Blueprint, flash, jsonify, redirect, render_template, request, url_for

from ..services.audit_service import record_audit, record_system_event
from ..services.system_service import system_service
from ..utils.context import get_current_user
from ..utils.decorators import login_required
from ..utils.helpers import parse_key_value_output, parse_table_output

files_bp = Blueprint("files", __name__, url_prefix="/files")


@files_bp.get("")
@login_required
def index():
    user = get_current_user()
    return render_template("files/index.html", user=user)


def _run_file_tool(service_method, audit_action, path_arg, extra_args=None):
    user = get_current_user()
    path = path_arg or ""
    try:
        if extra_args:
            output = service_method(path, **extra_args)
        else:
            output = service_method(path) if path else service_method()
        rows = parse_table_output(output)
        kv = parse_key_value_output(output)
        kind = "table" if rows else ("kv" if kv else "raw")
        record_audit(user.username, audit_action, "Files", "SUCCESS", path or "all")
        return jsonify({"output": output, "rows": rows, "kind": kind})
    except Exception as exc:
        record_audit(user.username, audit_action, "Files", "FAIL", str(exc))
        return jsonify({"error": str(exc)}), 400


@files_bp.post("/api/open")
@login_required
def api_open_files():
    return _run_file_tool(
        lambda p: system_service.open_files(p) if p else system_service.open_files(),
        "Open Files",
        request.form.get("path", "").strip(),
    )


@files_bp.post("/api/locked")
@login_required
def api_locked_files():
    return _run_file_tool(
        lambda p: system_service.locked_files(p) if p else system_service.locked_files(),
        "Locked Files",
        request.form.get("path", "").strip(),
    )


@files_bp.post("/api/watch")
@login_required
def api_watch_file():
    user = get_current_user()
    path = request.form.get("path", "").strip()
    try:
        duration = int(request.form.get("duration", "10"))
        if duration < 1 or duration > 300:
            raise ValueError
    except (TypeError, ValueError):
        return jsonify({"error": "Duration must be an integer between 1 and 300"}), 400
    try:
        output = system_service.watch_file(path, duration)
        record_audit(user.username, "Watch File", "Files", "SUCCESS", path)
        record_system_event("WATCH", path, "Files", output)
        return jsonify({"output": output, "rows": [], "kind": "raw"})
    except Exception as exc:
        record_audit(user.username, "Watch File", "Files", "FAIL", str(exc))
        return jsonify({"error": str(exc)}), 400


@files_bp.post("/api/directory-size")
@login_required
def api_directory_size():
    return _run_file_tool(system_service.directory_size, "Directory Size", request.form.get("path", "").strip())


@files_bp.post("/api/large-files")
@login_required
def api_large_files():
    user = get_current_user()
    path = request.form.get("path", "").strip()
    size = request.form.get("size", "+100M").strip()
    try:
        output = system_service.large_files(path, size)
        rows = parse_table_output(output)
        kind = "table" if rows else "raw"
        record_audit(user.username, "Large Files", "Files", "SUCCESS", f"{path}:{size}")
        return jsonify({"output": output, "rows": rows, "kind": kind})
    except Exception as exc:
        record_audit(user.username, "Large Files", "Files", "FAIL", str(exc))
        return jsonify({"error": str(exc)}), 400


@files_bp.post("/api/permission")
@login_required
def api_file_permission():
    return _run_file_tool(system_service.file_permission, "File Permission", request.form.get("path", "").strip())
