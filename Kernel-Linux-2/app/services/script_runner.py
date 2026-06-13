from __future__ import annotations

import subprocess
from dataclasses import dataclass
from pathlib import Path

from flask import current_app

from ..config import SCRIPT_DIR
from ..security import validate_script_name


class ScriptExecutionError(RuntimeError):
    pass


@dataclass
class ScriptResult:
    stdout: str
    stderr: str
    returncode: int
    script_path: str


class ScriptRunner:
    def __init__(self, allowed_scripts: set[str] | None = None):
        self.allowed_scripts = allowed_scripts or set()

    def run(self, script_name: str, args: list[str] | None = None, timeout: int | None = None) -> ScriptResult:
        script_name = validate_script_name(script_name)
        if self.allowed_scripts and script_name not in self.allowed_scripts:
            raise ScriptExecutionError(f"Script not allowed: {script_name}")

        script_path = Path(SCRIPT_DIR) / script_name
        if not script_path.exists():
            raise ScriptExecutionError(f"Script not found: {script_path}")

        command = ["bash", str(script_path)]
        if args:
            command.extend(args)

        try:
            completed = subprocess.run(
                command,
                check=False,
                capture_output=True,
                text=True,
                timeout=timeout or current_app.config["SCRIPT_TIMEOUT"],
            )
        except subprocess.TimeoutExpired as exc:
            raise ScriptExecutionError(f"Script timed out: {script_name}") from exc
        except OSError as exc:
            raise ScriptExecutionError(f"Failed to run script {script_name}: {exc}") from exc

        result = ScriptResult(
            stdout=completed.stdout.strip(),
            stderr=completed.stderr.strip(),
            returncode=completed.returncode,
            script_path=str(script_path),
        )
        if completed.returncode != 0:
            raise ScriptExecutionError(result.stderr or result.stdout or f"{script_name} failed")
        return result
