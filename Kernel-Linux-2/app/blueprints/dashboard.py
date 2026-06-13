from __future__ import annotations

from datetime import datetime, timezone

from flask import Blueprint, jsonify, render_template, session

from ..extensions import db
from ..models import AuditLog
from ..services.audit_service import record_audit
from ..services.system_service import system_service
from ..utils.context import get_current_user
from ..utils.decorators import login_required
from ..utils.helpers import parse_key_value_output, parse_table_output

dashboard_bp = Blueprint("dashboard", __name__)


@dashboard_bp.get("/")
@login_required
def index():
    user = get_current_user()
    record_audit(user.username, "View Dashboard", "Dashboard", "SUCCESS", "Dashboard opened")
    return render_template("dashboard/index.html", user=user)


@dashboard_bp.get("/api/dashboard/metrics")
@login_required
def metrics():
    overview = parse_key_value_output(system_service.system_overview())
    top_procs = parse_table_output(system_service.top_processes())
    net_ifaces = parse_table_output(system_service.network_info())
    all_procs = parse_table_output(system_service.list_processes())

    recent = (
        db.session.query(AuditLog)
        .order_by(AuditLog.timestamp.desc())
        .limit(10)
        .all()
    )

    return jsonify({
        "status": "success",
        "system": {
            "cpu_percent": overview.get("cpu_usage", "0"),
            "memory_percent": overview.get("memory_usage", "0"),
            "disk_percent": overview.get("disk_usage", "0"),
            "uptime": overview.get("uptime", "0"),
            "process_count": len(all_procs),
            "network_sent": 0,
            "network_recv": 0,
        },
        "top_processes": [
            {
                "pid": p.get("col_1", ""),
                "name": p.get("col_2", ""),
                "user": p.get("col_3", ""),
                "cpu": p.get("col_4", "0"),
                "mem": p.get("col_5", "0"),
                "status": p.get("col_6", ""),
                "start": p.get("col_7", ""),
            }
            for p in top_procs
        ],
        "network_interfaces": [
            {
                "interface": n.get("col_1", ""),
                "ip": n.get("col_2", ""),
                "mac": n.get("col_3", ""),
                "netmask": n.get("col_4", ""),
                "bytes_sent": 0,
                "bytes_recv": 0,
                "status": "",
            }
            for n in net_ifaces
        ],
        "recent_activities": [
            {
                "time": a.timestamp.strftime("%H:%M:%S") if a.timestamp else "",
                "user": a.username,
                "action": f"{a.action} ({a.module})",
            }
            for a in recent
        ],
    })
