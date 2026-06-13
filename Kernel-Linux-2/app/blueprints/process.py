from __future__ import annotations

from flask import Blueprint, jsonify, render_template, request

from ..services.audit_service import record_audit
from ..services.system_service import system_service
from ..utils.context import get_current_user
from ..utils.decorators import login_required, role_required
from ..utils.helpers import parse_key_value_output, parse_table_output

process_bp = Blueprint("process", __name__, url_prefix="/processes")


@process_bp.get("")
@login_required
def index():
    user = get_current_user()
    record_audit(user.username, "View Processes", "Process", "SUCCESS", "Opened process page")
    return render_template("process/index.html", user=user)


@process_bp.get("/api/list")
@login_required
def api_list():
    output = system_service.list_processes()
    rows = parse_table_output(output)
    return jsonify({
        "status": "success",
        "data": [
            {
                "pid": r.get("col_1", ""),
                "name": r.get("col_2", ""),
                "user": r.get("col_3", ""),
                "cpu": r.get("col_4", "0"),
                "mem": r.get("col_5", "0"),
                "status": r.get("col_6", ""),
                "start": r.get("col_7", ""),
            }
            for r in rows
        ],
    })


@process_bp.post("/api/search")
@login_required
def api_search():
    data = request.get_json(silent=True) or {}
    query = (data.get("query") or request.form.get("query", "")).strip()
    if not query:
        return jsonify({"status": "error", "message": "Vui lòng nhập từ khóa tìm kiếm"}), 400
    output = system_service.search_process(query)
    rows = parse_table_output(output)
    return jsonify({
        "status": "success",
        "data": [
            {
                "pid": r.get("col_1", ""),
                "name": r.get("col_2", ""),
                "user": r.get("col_3", ""),
                "cpu": r.get("col_4", "0"),
                "mem": r.get("col_5", "0"),
                "status": r.get("col_6", ""),
                "start": r.get("col_7", ""),
            }
            for r in rows
        ],
    })


@process_bp.get("/api/detail/<int:pid>")
@login_required
def api_detail(pid: int):
    output = system_service.process_detail(pid)
    kv = parse_key_value_output(output)
    return jsonify({"status": "success", "data": kv})


@process_bp.post("/api/kill/<int:pid>")
@login_required
@role_required("Admin")
def api_kill(pid: int):
    try:
        result = system_service.kill_process(pid, force=False)
        record_audit(get_current_user().username, "Kill Process", "Process", "SUCCESS", f"PID {pid}")
        return jsonify({"status": "success", "message": result.message})
    except Exception as e:
        record_audit(get_current_user().username, "Kill Process", "Process", "FAIL", str(e))
        return jsonify({"status": "error", "message": str(e)}), 400


@process_bp.post("/api/force-kill/<int:pid>")
@login_required
@role_required("Admin")
def api_force_kill(pid: int):
    try:
        result = system_service.kill_process(pid, force=True)
        record_audit(get_current_user().username, "Force Kill Process", "Process", "SUCCESS", f"PID {pid}")
        return jsonify({"status": "success", "message": result.message})
    except Exception as e:
        record_audit(get_current_user().username, "Force Kill Process", "Process", "FAIL", str(e))
        return jsonify({"status": "error", "message": str(e)}), 400


@process_bp.post("/api/restart-service")
@login_required
@role_required("Admin")
def api_restart_service():
    data = request.get_json(silent=True) or {}
    service_name = (data.get("service_name") or request.form.get("service_name", "")).strip()
    if not service_name:
        return jsonify({"status": "error", "message": "Vui lòng nhập tên dịch vụ"}), 400
    try:
        result = system_service.restart_service(service_name)
        record_audit(get_current_user().username, "Restart Service", "Process", "SUCCESS", service_name)
        return jsonify({"status": "success", "message": result.message})
    except Exception as e:
        record_audit(get_current_user().username, "Restart Service", "Process", "FAIL", str(e))
        return jsonify({"status": "error", "message": str(e)}), 400
