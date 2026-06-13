from __future__ import annotations

import ipaddress
import re
from pathlib import Path

SAFE_SCRIPT_NAME = re.compile(r"^[A-Za-z0-9_\-]+\.sh$")
SAFE_SERVICE_NAME = re.compile(r"^[A-Za-z0-9@._\-]+$")
SAFE_INTERFACE_NAME = re.compile(r"^[A-Za-z0-9@._:\-]+$")
SAFE_IDENTIFIER = re.compile(r"^[A-Za-z0-9@._\-/]+$")

ADMIN_ACTIONS = {
    "kill_process",
    "force_kill_process",
    "restart_service",
    "restart_network",
    "toggle_interface",
    "change_ip",
    "close_connection",
}


def ensure_positive_int(value: str, field_name: str) -> int:
    try:
        parsed = int(value)
    except (TypeError, ValueError) as exc:
        raise ValueError(f"{field_name} must be an integer") from exc
    if parsed <= 0:
        raise ValueError(f"{field_name} must be greater than zero")
    return parsed


def validate_pid(value: str) -> int:
    return ensure_positive_int(value, "PID")


def validate_port(value: str) -> int:
    parsed = ensure_positive_int(value, "port")
    if parsed > 65535:
        raise ValueError("port must be <= 65535")
    return parsed


def validate_path(value: str) -> str:
    if not value:
        raise ValueError("path is required")
    path = Path(value)
    if "\x00" in value or any(part == ".." for part in path.parts):
        raise ValueError("invalid path")
    return str(path)


def validate_service_name(value: str) -> str:
    if not value or not SAFE_SERVICE_NAME.match(value):
        raise ValueError("invalid service name")
    return value


def validate_interface_name(value: str) -> str:
    if not value or not SAFE_INTERFACE_NAME.match(value):
        raise ValueError("invalid interface name")
    return value


def validate_hostname_or_ip(value: str) -> str:
    if not value:
        raise ValueError("target is required")
    try:
        ipaddress.ip_address(value)
        return value
    except ValueError:
        pass
    if not re.match(r"^[A-Za-z0-9._\-]+$", value):
        raise ValueError("invalid hostname")
    return value


def validate_cidr(value: str) -> str:
    try:
        ipaddress.ip_interface(value)
    except ValueError as exc:
        raise ValueError("invalid CIDR") from exc
    return value


def validate_script_name(value: str) -> str:
    if not value or not SAFE_SCRIPT_NAME.match(value):
        raise ValueError("invalid script name")
    return value
