from __future__ import annotations

from flask import Blueprint, jsonify, render_template, request

from ..services.audit_service import record_audit
from ..services.system_service import system_service
from ..utils.context import get_current_user
from ..utils.decorators import login_required, role_required
from ..utils.helpers import parse_key_value_output, parse_table_output

network_bp = Blueprint("network", __name__, url_prefix="/network")


@network_bp.get("")
@login_required
def index():
    user = get_current_user()
    return render_template("network/index.html", user=user)


def _run(service_method, audit_action, audit_detail, args=None):
    user = get_current_user()
    try:
        output = service_method(*args) if args else service_method()
        rows = parse_table_output(output)
        kv = parse_key_value_output(output)
        kind = "table" if rows else "kv" if kv else "raw"
        record_audit(user.username, audit_action, "Network", "SUCCESS", audit_detail)
        return jsonify({"output": output, "rows": rows, "kind": kind})
    except Exception as exc:
        record_audit(user.username, audit_action, "Network", "FAIL", str(exc))
        return jsonify({"error": str(exc)}), 400


@network_bp.get("/api/overview")
@login_required
def api_overview():
    user = get_current_user()
    try:
        speed = system_service.network_speed()
        info = system_service.network_info()
        route = system_service.route_info()
        dns = system_service.dns_info()
        conn = system_service.connection_list()

        speed_data = {}
        for line in speed.strip().split("\n"):
            if "=" in line:
                k, v = line.split("=", 1)
                speed_data[k.strip()] = v.strip()

        info_rows = parse_table_output(info) or []
        active = sum(
            1
            for i in info_rows
            if i.get("IP Address") and i["IP Address"] not in ("None", "", "127.0.0.1")
        )

        dns_rows = parse_table_output(dns) or []
        dns_servers = [r.get("DNS", "") for r in dns_rows if r.get("DNS")]

        conn_rows = parse_table_output(conn) or []

        record_audit(user.username, "Network Overview", "Network", "SUCCESS", "Overview")
        return jsonify({
            "current_ip": speed_data.get("current_ip", "—"),
            "gateway": speed_data.get("gateway", "—"),
            "upload_speed": speed_data.get("upload_speed", "0"),
            "download_speed": speed_data.get("download_speed", "0"),
            "active_interfaces": active,
            "interfaces": info_rows,
            "routes": parse_table_output(route) or [],
            "dns_servers": dns_servers,
            "active_connections": len(conn_rows),
            "network_status": "online" if active > 0 else "offline",
        })
    except Exception as exc:
        return jsonify({"error": str(exc)}), 500


@network_bp.get("/api/interfaces")
@login_required
def api_interfaces():
    user = get_current_user()
    try:
        output = system_service.network_info()
        rows = parse_table_output(output) or []
        record_audit(user.username, "Network Interfaces", "Network", "SUCCESS", "Interface list")
        return jsonify({"interfaces": rows})
    except Exception as exc:
        return jsonify({"error": str(exc)}), 500


@network_bp.post("/api/info")
@login_required
def api_info():
    return _run(system_service.network_info, "Network Info", "Interface information")


@network_bp.get("/api/routes")
@login_required
def api_routes():
    user = get_current_user()
    try:
        output = system_service.route_info()
        rows = parse_table_output(output) or []
        record_audit(user.username, "Routing Table", "Network", "SUCCESS", "Route list")
        return jsonify({"routes": rows})
    except Exception as exc:
        return jsonify({"error": str(exc)}), 500


@network_bp.post("/api/route")
@login_required
def api_route():
    return _run(system_service.route_info, "Route Info", "Routing table")


@network_bp.post("/api/dns")
@login_required
def api_dns():
    return _run(system_service.dns_info, "DNS Info", "DNS config")


@network_bp.post("/api/ping")
@login_required
def api_ping():
    user = get_current_user()
    target = request.form.get("target", "").strip()
    count = request.form.get("count", "4").strip()
    if not target:
        return jsonify({"error": "Target is required"}), 400
    try:
        output = system_service.ping_test(target)
        record_audit(user.username, "Ping Test", "Network", "SUCCESS", target)
        return jsonify({"output": output})
    except Exception as exc:
        record_audit(user.username, "Ping Test", "Network", "FAIL", str(exc))
        return jsonify({"error": str(exc)}), 400


@network_bp.post("/api/traceroute")
@login_required
def api_traceroute():
    user = get_current_user()
    target = request.form.get("target", "").strip()
    if not target:
        return jsonify({"error": "Target is required"}), 400
    try:
        output = system_service.traceroute_test(target)
        record_audit(user.username, "Traceroute", "Network", "SUCCESS", target)
        return jsonify({"output": output})
    except Exception as exc:
        record_audit(user.username, "Traceroute", "Network", "FAIL", str(exc))
        return jsonify({"error": str(exc)}), 400


@network_bp.post("/api/port-check")
@login_required
def api_port_check():
    user = get_current_user()
    target = request.form.get("target", "").strip()
    port = request.form.get("port", "").strip()
    if not target or not port:
        return jsonify({"error": "Target and port are required"}), 400
    try:
        p = int(port)
        if p < 1 or p > 65535:
            return jsonify({"error": "Port must be 1-65535"}), 400
        output = system_service.port_check(target, p)
        record_audit(user.username, "Port Check", "Network", "SUCCESS", f"{target}:{port}")
        return jsonify({"output": output})
    except ValueError:
        return jsonify({"error": "Port must be an integer"}), 400
    except Exception as exc:
        record_audit(user.username, "Port Check", "Network", "FAIL", str(exc))
        return jsonify({"error": str(exc)}), 400


@network_bp.post("/api/port-scan")
@login_required
def api_port_scan():
    user = get_current_user()
    target = request.form.get("target", "").strip()
    ports = request.form.get("ports", "1-1024").strip()
    if not target:
        return jsonify({"error": "Target is required"}), 400
    try:
        output = system_service.port_scan(target, ports)
        record_audit(user.username, "Port Scan", "Network", "SUCCESS", f"{target}:{ports}")
        return jsonify({"output": output})
    except Exception as exc:
        record_audit(user.username, "Port Scan", "Network", "FAIL", str(exc))
        return jsonify({"error": str(exc)}), 400


@network_bp.get("/api/connections")
@login_required
def api_connections():
    return _run(system_service.connection_list, "Connection List", "Current connections")


@network_bp.post("/api/bandwidth")
@login_required
def api_bandwidth():
    user = get_current_user()
    interface = request.form.get("interface", "").strip()
    try:
        output = system_service.bandwidth_monitor(interface)
        record_audit(user.username, "Bandwidth", "Network", "SUCCESS", interface or "all")
        return jsonify({"output": output})
    except Exception as exc:
        record_audit(user.username, "Bandwidth", "Network", "FAIL", str(exc))
        return jsonify({"error": str(exc)}), 400


@network_bp.post("/api/restart")
@login_required
@role_required("Admin")
def api_restart():
    user = get_current_user()
    try:
        result = system_service.restart_network()
        record_audit(user.username, "Restart Network", "Network", "SUCCESS", "Network restart")
        return jsonify({"success": True, "message": result.message, "output": result.output})
    except Exception as exc:
        record_audit(user.username, "Restart Network", "Network", "FAIL", str(exc))
        return jsonify({"error": str(exc)}), 400


@network_bp.post("/api/toggle")
@login_required
@role_required("Admin")
def api_toggle():
    user = get_current_user()
    interface = request.form.get("interface", "").strip()
    state = request.form.get("state", "down").strip()
    if not interface:
        return jsonify({"error": "Interface is required"}), 400
    if state not in ("up", "down"):
        return jsonify({"error": "State must be up or down"}), 400
    try:
        result = system_service.interface_toggle(interface, state)
        record_audit(user.username, "Toggle Interface", "Network", "SUCCESS", f"{interface}:{state}")
        return jsonify({"success": True, "message": result.message, "output": result.output})
    except Exception as exc:
        record_audit(user.username, "Toggle Interface", "Network", "FAIL", str(exc))
        return jsonify({"error": str(exc)}), 400


@network_bp.post("/api/change-ip")
@login_required
@role_required("Admin")
def api_change_ip():
    user = get_current_user()
    interface = request.form.get("interface", "").strip()
    cidr = request.form.get("cidr", "").strip()
    gateway = request.form.get("gateway", "").strip()
    if not interface or not cidr:
        return jsonify({"error": "Interface and CIDR are required"}), 400
    try:
        result = system_service.change_ip(interface, cidr, gateway)
        record_audit(user.username, "Change IP", "Network", "SUCCESS", f"{interface}:{cidr}")
        return jsonify({"success": True, "message": result.message, "output": result.output})
    except Exception as exc:
        record_audit(user.username, "Change IP", "Network", "FAIL", str(exc))
        return jsonify({"error": str(exc)}), 400
