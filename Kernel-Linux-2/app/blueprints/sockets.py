from __future__ import annotations

import json

from flask import Blueprint, jsonify, render_template, request

from ..services.audit_service import record_audit
from ..services.system_service import system_service
from ..utils.context import get_current_user
from ..utils.decorators import login_required, role_required
from ..utils.helpers import parse_key_value_output, parse_table_output

sockets_bp = Blueprint("sockets", __name__, url_prefix="/sockets")


@sockets_bp.get("")
@login_required
def index():
    user = get_current_user()
    return render_template("sockets/index.html", user=user)


def _run(service_method, audit_action, audit_detail, args=None):
    user = get_current_user()
    try:
        output = service_method(*args) if args else service_method()
        rows = parse_table_output(output)
        kv = parse_key_value_output(output)
        kind = "table" if rows else ("kv" if kv else "raw")
        record_audit(user.username, audit_action, "Socket", "SUCCESS", audit_detail)
        return jsonify({"output": output, "rows": rows, "kind": kind})
    except Exception as exc:
        record_audit(user.username, audit_action, "Socket", "FAIL", str(exc))
        return jsonify({"error": str(exc)}), 400


def _try_parse_int(val):
    try:
        return int(val) if val else None
    except (TypeError, ValueError):
        raise ValueError("PID and port must be integers.")


@sockets_bp.post("/api/list")
@login_required
def api_socket_list():
    return _run(system_service.socket_list, "Socket List", "All sockets")


@sockets_bp.post("/api/tcp")
@login_required
def api_tcp_socket():
    return _run(system_service.tcp_socket, "TCP Socket", "TCP sockets")


@sockets_bp.post("/api/udp")
@login_required
def api_udp_socket():
    return _run(system_service.udp_socket, "UDP Socket", "UDP sockets")


@sockets_bp.post("/api/listening")
@login_required
def api_listening_ports():
    return _run(system_service.listening_ports, "Listening Ports", "Listening ports")


@sockets_bp.post("/api/by-process")
@login_required
def api_socket_process():
    user = get_current_user()
    try:
        pid = _try_parse_int(request.form.get("pid", "").strip())
        port = _try_parse_int(request.form.get("port", "").strip())
    except ValueError as exc:
        return jsonify({"error": str(exc)}), 400
    try:
        output = system_service.socket_process(pid, port)
        rows = parse_table_output(output)
        record_audit(user.username, "Socket Process", "Socket", "SUCCESS", f"pid={pid},port={port}")
        return jsonify({"output": output, "rows": rows, "kind": "table" if rows else "raw"})
    except Exception as exc:
        record_audit(user.username, "Socket Process", "Socket", "FAIL", str(exc))
        return jsonify({"error": str(exc)}), 400


@sockets_bp.post("/api/stats")
@login_required
def api_connection_stats():
    user = get_current_user()
    try:
        output = system_service.connection_stats()
        try:
            data = json.loads(output)
            return jsonify({"output": output, "data": data, "kind": "json"})
        except json.JSONDecodeError:
            return jsonify({"output": output, "kind": "raw"})
    except Exception as exc:
        record_audit(user.username, "Connection Stats", "Socket", "FAIL", str(exc))
        return jsonify({"error": str(exc)}), 400


@sockets_bp.post("/api/overview")
@login_required
def api_overview():
    user = get_current_user()
    try:
        output = system_service.socket_by_state()
        kv = parse_key_value_output(output)
        top_proc = system_service.socket_top_processes()
        top_rows = parse_table_output(top_proc)
        record_audit(user.username, "Socket Overview", "Socket", "SUCCESS", "Overview")
        return jsonify({"metrics": kv, "top_processes": top_rows})
    except Exception as exc:
        return jsonify({"error": str(exc)}), 400


@sockets_bp.post("/api/close")
@login_required
@role_required("Admin")
def api_close_connection():
    user = get_current_user()
    try:
        pid = _try_parse_int(request.form.get("pid", "").strip())
        port = _try_parse_int(request.form.get("port", "").strip())
    except ValueError as exc:
        return jsonify({"error": str(exc)}), 400
    try:
        result = system_service.close_connection(pid, port)
        record_audit(user.username, "Close Connection", "Socket", "SUCCESS", f"pid={pid},port={port}")
        return jsonify({"success": True, "message": result.message, "output": result.output})
    except Exception as exc:
        record_audit(user.username, "Close Connection", "Socket", "FAIL", str(exc))
        return jsonify({"error": str(exc)}), 400
