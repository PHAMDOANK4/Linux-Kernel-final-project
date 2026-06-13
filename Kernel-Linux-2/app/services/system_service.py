from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

from flask import current_app

from ..security import (
    validate_cidr,
    validate_hostname_or_ip,
    validate_interface_name,
    validate_path,
    validate_pid,
    validate_port,
    validate_service_name,
)
from .audit_service import record_audit, record_system_event
from .script_runner import ScriptExecutionError, ScriptRunner


@dataclass
class ActionResponse:
    success: bool
    message: str
    output: str = ""
    data: dict | None = None


class SystemService:
    def __init__(self) -> None:
        self.runner = ScriptRunner(
            allowed_scripts={
                "process_list.sh",
                "process_detail.sh",
                "process_search.sh",
                "process_kill.sh",
                "process_force_kill.sh",
                "service_restart.sh",
                "open_files.sh",
                "locked_files.sh",
                "watch_file.sh",
                "directory_size.sh",
                "large_files.sh",
                "file_permission.sh",
                "socket_list.sh",
                "tcp_socket.sh",
                "udp_socket.sh",
                "listening_ports.sh",
                "socket_process.sh",
                "connection_stats.sh",
                "close_connection.sh",
                "socket_by_state.sh",
                "socket_top_processes.sh",
                "network_info.sh",
                "route_info.sh",
                "dns_info.sh",
                "ping_test.sh",
                "traceroute_test.sh",
                "port_check.sh",
                "port_scan.sh",
                "connection_list.sh",
                "bandwidth_monitor.sh",
                "restart_network.sh",
                "interface_toggle.sh",
                "change_ip.sh",
                "system_overview.sh",
                "top_processes.sh",
                "network_speed.sh",
            }
        )

    def _run(self, script_name: str, args: list[str] | None = None, timeout: int | None = None) -> str:
        result = self.runner.run(script_name, args=args, timeout=timeout)
        return result.stdout

    def list_processes(self) -> str:
        return self._run("process_list.sh")

    def process_detail(self, pid: int) -> str:
        return self._run("process_detail.sh", [str(validate_pid(str(pid)))])

    def search_process(self, query: str) -> str:
        if not query:
            raise ValueError("search query is required")
        return self._run("process_search.sh", [query])

    def kill_process(self, pid: int, force: bool = False) -> ActionResponse:
        script = "process_force_kill.sh" if force else "process_kill.sh"
        pid_value = validate_pid(str(pid))
        output = self._run(script, [str(pid_value)])
        return ActionResponse(True, f"Killed PID {pid_value}", output)

    def restart_service(self, service_name: str) -> ActionResponse:
        valid_service = validate_service_name(service_name)
        output = self._run("service_restart.sh", [valid_service])
        return ActionResponse(True, f"Restarted service {valid_service}", output)

    def open_files(self, path: str = "") -> str:
        args = [validate_path(path)] if path else []
        return self._run("open_files.sh", args)

    def locked_files(self, path: str = "") -> str:
        args = [validate_path(path)] if path else []
        return self._run("locked_files.sh", args)

    def watch_file(self, path: str, duration: int = 10) -> str:
        return self._run("watch_file.sh", [validate_path(path), str(max(1, duration))], timeout=duration + 5)

    def directory_size(self, path: str) -> str:
        return self._run("directory_size.sh", [validate_path(path)])

    def large_files(self, path: str, size: str = "+100M") -> str:
        return self._run("large_files.sh", [validate_path(path), size])

    def file_permission(self, path: str) -> str:
        return self._run("file_permission.sh", [validate_path(path)])

    def socket_list(self) -> str:
        return self._run("socket_list.sh")

    def tcp_socket(self) -> str:
        return self._run("tcp_socket.sh")

    def udp_socket(self) -> str:
        return self._run("udp_socket.sh")

    def listening_ports(self) -> str:
        return self._run("listening_ports.sh")

    def socket_process(self, pid: int | None = None, port: int | None = None) -> str:
        args: list[str] = []
        if pid is not None:
            args.extend(["--pid", str(validate_pid(str(pid)))])
        if port is not None:
            args.extend(["--port", str(validate_port(str(port)))])
        return self._run("socket_process.sh", args)

    def connection_stats(self) -> str:
        return self._run("connection_stats.sh")

    def close_connection(self, pid: int | None = None, port: int | None = None) -> ActionResponse:
        args: list[str] = []
        if pid is not None:
            args.extend(["--pid", str(validate_pid(str(pid)))])
        if port is not None:
            args.extend(["--port", str(validate_port(str(port)))])
        if not args:
            raise ValueError("pid or port is required")
        output = self._run("close_connection.sh", args)
        target = f"PID {pid}" if pid else f"port {port}"
        return ActionResponse(True, f"Closed connection for {target}", output)

    def socket_by_state(self) -> str:
        return self._run("socket_by_state.sh")

    def socket_top_processes(self) -> str:
        return self._run("socket_top_processes.sh")

    def network_info(self) -> str:
        return self._run("network_info.sh")

    def route_info(self) -> str:
        return self._run("route_info.sh")

    def dns_info(self) -> str:
        return self._run("dns_info.sh")

    def ping_test(self, target: str) -> str:
        return self._run("ping_test.sh", [validate_hostname_or_ip(target)])

    def traceroute_test(self, target: str) -> str:
        return self._run("traceroute_test.sh", [validate_hostname_or_ip(target)])

    def port_check(self, target: str, port: int) -> str:
        return self._run("port_check.sh", [validate_hostname_or_ip(target), str(validate_port(str(port)))])

    def port_scan(self, target: str, ports: str) -> str:
        return self._run("port_scan.sh", [validate_hostname_or_ip(target), ports])

    def connection_list(self) -> str:
        return self._run("connection_list.sh")

    def bandwidth_monitor(self, interface_name: str = "") -> str:
        args = [validate_interface_name(interface_name)] if interface_name else []
        return self._run("bandwidth_monitor.sh", args)

    def restart_network(self) -> ActionResponse:
        output = self._run("restart_network.sh")
        return ActionResponse(True, "Network service restarted", output)

    def interface_toggle(self, interface_name: str, state: str) -> ActionResponse:
        valid_interface = validate_interface_name(interface_name)
        if state not in {"up", "down"}:
            raise ValueError("state must be up or down")
        output = self._run("interface_toggle.sh", [valid_interface, state])
        return ActionResponse(True, f"Interface {valid_interface} set to {state}", output)

    def change_ip(self, interface_name: str, cidr: str, gateway: str = "") -> ActionResponse:
        valid_interface = validate_interface_name(interface_name)
        valid_cidr = validate_cidr(cidr)
        args = [valid_interface, valid_cidr]
        if gateway:
            args.append(validate_hostname_or_ip(gateway))
        output = self._run("change_ip.sh", args)
        return ActionResponse(True, f"IP changed on {valid_interface}", output)

    def system_overview(self) -> str:
        return self._run("system_overview.sh")

    def top_processes(self) -> str:
        return self._run("top_processes.sh")

    def network_speed(self) -> str:
        return self._run("network_speed.sh")


system_service = SystemService()
