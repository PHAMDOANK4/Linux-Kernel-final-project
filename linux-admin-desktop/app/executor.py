import os
import subprocess
import sys

def _get_scripts_dir():
    if getattr(sys, "frozen", False) and hasattr(sys, "_MEIPASS"):
        return os.path.join(sys._MEIPASS, "scripts")
    return os.path.join(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")), "scripts")

SCRIPTS_DIR = _get_scripts_dir()


class ScriptExecutor:
    def __init__(self, scripts_dir: str = SCRIPTS_DIR):
        self.scripts_dir = scripts_dir

    def run(self, script_name: str, args: list[str] | None = None) -> tuple[bool, str]:
        args = args or []
        script_path = os.path.join(self.scripts_dir, script_name)

        if not os.path.exists(script_path):
            return False, f"Script not found: {script_name}"

        try:
            completed = subprocess.run(
                [script_path, *args],
                capture_output=True,
                text=True,
                timeout=120,
                check=False,
            )
            output = (completed.stdout or completed.stderr or "").strip()
            output = output if output else "No output"
            return completed.returncode == 0, output
        except subprocess.TimeoutExpired:
            return False, "Command timeout"
        except Exception as exc:
            return False, str(exc)
