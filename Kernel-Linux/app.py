import os
import subprocess
from datetime import datetime
from functools import wraps

from flask import Flask, flash, redirect, render_template, request, session, url_for
from flask_sqlalchemy import SQLAlchemy
from werkzeug.security import check_password_hash, generate_password_hash

BASE_DIR = os.path.abspath(os.path.dirname(__file__))
DB_PATH = os.path.join(BASE_DIR, "instance", "dashboard.db")
SCRIPTS_DIR = os.path.join(BASE_DIR, "scripts")
LOG_FILE = os.path.join(BASE_DIR, "logs", "system.log")

app = Flask(__name__)
app.config["SECRET_KEY"] = os.getenv("SECRET_KEY", "dev-secret-key")
app.config["SQLALCHEMY_DATABASE_URI"] = f"sqlite:///{DB_PATH}"
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False

db = SQLAlchemy(app)


class User(db.Model):
    __tablename__ = "users"

    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(64), unique=True, nullable=False)
    password_hash = db.Column(db.String(255), nullable=False)
    role = db.Column(db.String(16), nullable=False, default="user")
    created_at = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)


class ActionLog(db.Model):
    __tablename__ = "action_logs"

    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(64), nullable=False)
    action = db.Column(db.String(255), nullable=False)
    result = db.Column(db.String(32), nullable=False)
    detail = db.Column(db.Text, nullable=False)
    created_at = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)


def init_db() -> None:
    os.makedirs(os.path.join(BASE_DIR, "instance"), exist_ok=True)
    os.makedirs(os.path.join(BASE_DIR, "logs"), exist_ok=True)

    with app.app_context():
        db.create_all()

        admin_username = os.getenv("ADMIN_USERNAME", "admin")
        admin_password = os.getenv("ADMIN_PASSWORD", "admin123")
        user_username = os.getenv("USER_USERNAME", "user")
        user_password = os.getenv("USER_PASSWORD", "user123")

        if not User.query.filter_by(username=admin_username).first():
            db.session.add(
                User(
                    username=admin_username,
                    password_hash=generate_password_hash(admin_password),
                    role="admin",
                )
            )

        if not User.query.filter_by(username=user_username).first():
            db.session.add(
                User(
                    username=user_username,
                    password_hash=generate_password_hash(user_password),
                    role="user",
                )
            )

        db.session.commit()


def current_user() -> dict:
    return {
        "id": session.get("user_id"),
        "username": session.get("username"),
        "role": session.get("role"),
    }


def login_required(view_func):
    @wraps(view_func)
    def wrapped(*args, **kwargs):
        if not session.get("user_id"):
            flash("Vui long dang nhap.", "warning")
            return redirect(url_for("login"))
        return view_func(*args, **kwargs)

    return wrapped


def admin_required(view_func):
    @wraps(view_func)
    def wrapped(*args, **kwargs):
        if session.get("role") != "admin":
            flash("Ban khong co quyen thuc hien thao tac nay.", "danger")
            return redirect(url_for("dashboard"))
        return view_func(*args, **kwargs)

    return wrapped


def run_script(script_name: str, args: list[str] | None = None) -> tuple[bool, str]:
    args = args or []
    script_path = os.path.join(SCRIPTS_DIR, script_name)

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
    except Exception as exc:  # pylint: disable=broad-exception-caught
        return False, str(exc)


def write_system_log(username: str, action: str, success: bool, detail: str) -> None:
    result = "SUCCESS" if success else "FAILED"
    now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    line = f"{now} | user={username} | action={action} | result={result} | detail={detail}\n"

    os.makedirs(os.path.dirname(LOG_FILE), exist_ok=True)
    with open(LOG_FILE, "a", encoding="utf-8") as log_file:
        log_file.write(line)

    with app.app_context():
        db.session.add(
            ActionLog(
                username=username,
                action=action,
                result=result,
                detail=detail[:2000],
            )
        )
        db.session.commit()


def set_module_result(module_name: str, success: bool, output: str) -> None:
    session[f"{module_name}_result"] = {
        "success": success,
        "output": output,
    }


def get_module_result(module_name: str) -> dict | None:
    return session.pop(f"{module_name}_result", None)


def parse_file_listing(output: str) -> list[dict]:
    entries: list[dict] = []
    for line in output.splitlines():
        parts = line.split("\t", 2)
        if len(parts) != 3:
            continue

        item_type, name, full_path = parts
        is_dir = item_type == "DIR"
        entries.append(
            {
                "type": item_type,
                "name": name,
                "path": full_path,
                "is_dir": is_dir,
                "icon": "folder" if is_dir else "file",
            }
        )
    return entries


def parse_cron_schedule(schedule: str) -> dict:
    schedule = schedule.strip()
    empty = {
        "mode": "custom",
        "minute": "*",
        "hour": "*",
        "day_of_month": "*",
        "month": "*",
        "weekday": "*",
    }

    if not schedule:
        return empty

    macro_map = {
        "@hourly": {"mode": "hourly", "minute": "0", "hour": "*", "day_of_month": "*", "month": "*", "weekday": "*"},
        "@daily": {"mode": "daily", "minute": "0", "hour": "0", "day_of_month": "*", "month": "*", "weekday": "*"},
        "@midnight": {"mode": "daily", "minute": "0", "hour": "0", "day_of_month": "*", "month": "*", "weekday": "*"},
        "@weekly": {"mode": "weekly", "minute": "0", "hour": "0", "day_of_month": "*", "month": "*", "weekday": "0"},
        "@monthly": {"mode": "monthly", "minute": "0", "hour": "0", "day_of_month": "1", "month": "*", "weekday": "*"},
        "@yearly": {"mode": "yearly", "minute": "0", "hour": "0", "day_of_month": "1", "month": "1", "weekday": "*"},
        "@annually": {"mode": "yearly", "minute": "0", "hour": "0", "day_of_month": "1", "month": "1", "weekday": "*"},
    }

    if schedule in macro_map:
        return macro_map[schedule]

    parts = schedule.split()
    if len(parts) != 5:
        return empty

    minute, hour, day_of_month, month, weekday = parts
    mode = "custom"

    if day_of_month == "*" and month == "*" and weekday == "*":
        if hour == "*" and minute != "*":
            mode = "hourly"
        elif minute != "*" and hour != "*":
            mode = "daily"
    elif day_of_month == "*" and month == "*" and weekday != "*" and minute != "*" and hour != "*":
        mode = "weekly"
    elif day_of_month != "*" and month == "*" and weekday == "*" and minute != "*" and hour != "*":
        mode = "monthly"
    elif day_of_month != "*" and month != "*" and weekday == "*" and minute != "*" and hour != "*":
        mode = "yearly"

    return {
        "mode": mode,
        "minute": minute,
        "hour": hour,
        "day_of_month": day_of_month,
        "month": month,
        "weekday": weekday,
    }


def parse_cron_jobs(output: str) -> list[dict]:
    jobs: list[dict] = []

    for line_number, raw_line in enumerate(output.splitlines(), start=1):
        line = raw_line.strip()
        if not line or line.startswith("#"):
            continue

        schedule = ""
        command = ""

        if line.startswith("@"):
            parts = line.split(None, 1)
            if len(parts) == 1:
                continue
            schedule = parts[0]
            command = parts[1]
        else:
            parts = line.split(None, 5)
            if len(parts) != 6:
                continue
            schedule = " ".join(parts[:5])
            command = parts[5]

        schedule_data = parse_cron_schedule(schedule)
        jobs.append(
            {
                "line_number": line_number,
                "raw_line": line,
                "schedule": schedule,
                "command": command,
                **schedule_data,
            }
        )

    return jobs


@app.route("/")
def index():
    if session.get("user_id"):
        return redirect(url_for("dashboard"))
    return redirect(url_for("login"))


@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        username = request.form.get("username", "").strip()
        password = request.form.get("password", "")

        user = User.query.filter_by(username=username).first()
        if user and check_password_hash(user.password_hash, password):
            session["user_id"] = user.id
            session["username"] = user.username
            session["role"] = user.role
            flash("Dang nhap thanh cong.", "success")
            return redirect(url_for("dashboard"))

        flash("Sai thong tin dang nhap.", "danger")

    return render_template("login.html")


@app.route("/logout")
@login_required
def logout():
    session.clear()
    flash("Da dang xuat.", "info")
    return redirect(url_for("login"))


@app.route("/dashboard")
@login_required
def dashboard():
    return render_template("index.html", user=current_user())


@app.route("/files", methods=["GET", "POST"])
@login_required
def file_management():
    user = current_user()
    path = request.args.get("path", "/home").strip() or "/home"
    path = os.path.abspath(path)

    if not os.path.isdir(path):
        flash(f"Duong dan khong hop le: {path}. Da chuyen ve /home.", "warning")
        path = "/home"

    if request.method == "POST":
        action = request.form.get("action", "")
        script_name = ""
        args: list[str] = []

        if action == "list":
            next_path = request.form.get("path", "/home").strip() or "/home"
            return redirect(url_for("file_management", path=next_path))
        elif action == "create_file":
            script_name = "create_file.sh"
            args = [request.form.get("directory", path), request.form.get("filename", "")]
        elif action == "create_folder":
            script_name = "create_folder.sh"
            args = [request.form.get("directory", path), request.form.get("foldername", "")]
        elif action == "rename":
            script_name = "rename_file.sh"
            args = [request.form.get("source", ""), request.form.get("new_name", "")]
        elif action == "copy":
            script_name = "copy_file.sh"
            args = [request.form.get("source", ""), request.form.get("destination", "")]
        elif action == "move":
            script_name = "move_file.sh"
            args = [request.form.get("source", ""), request.form.get("destination", "")]
        elif action == "delete":
            script_name = "delete_file.sh"
            args = [request.form.get("target", "")]
        elif action == "search":
            script_name = "search_file.sh"
            args = [request.form.get("base_path", path), request.form.get("keyword", "")]
        elif action == "chmod":
            script_name = "chmod_file.sh"
            args = [request.form.get("target", ""), request.form.get("mode", "")]
        elif action == "chown":
            script_name = "chown_file.sh"
            args = [
                request.form.get("target", ""),
                request.form.get("owner", ""),
                request.form.get("group", ""),
            ]

        success, output = run_script(script_name, args)
        write_system_log(user["username"], f"files:{action}", success, output)
        set_module_result("files", success, output)
        return redirect(url_for("file_management", path=path))

    parent_path = os.path.dirname(path.rstrip("/")) or "/"

    list_ok, list_output = run_script("list_files.sh", [path])
    entries = parse_file_listing(list_output) if list_ok else []
    result = get_module_result("files")

    return render_template(
        "file_management.html",
        user=user,
        path=path,
        parent_path=parent_path,
        list_ok=list_ok,
        list_output=list_output,
        entries=entries,
        result=result,
    )


@app.route("/cron", methods=["GET", "POST"])
@login_required
@admin_required
def task_scheduler():
    user = current_user()

    if request.method == "POST":
        action = request.form.get("action", "")
        script_name = ""
        args: list[str] = []

        if action == "create":
            script_name = "create_cron.sh"
            args = [request.form.get("schedule", ""), request.form.get("command", "")]
        elif action == "update":
            script_name = "update_cron.sh"
            args = [
                request.form.get("selected_line", request.form.get("match_text", "")),
                request.form.get("schedule", ""),
                request.form.get("command", ""),
            ]
        elif action == "delete":
            script_name = "delete_cron.sh"
            args = [request.form.get("selected_line", request.form.get("match_text", ""))]
        elif action == "run_now":
            script_name = "run_job.sh"
            args = [request.form.get("selected_command", request.form.get("command", ""))]

        success, output = run_script(script_name, args)
        write_system_log(user["username"], f"cron:{action}", success, output)
        set_module_result("cron", success, output)
        return redirect(url_for("task_scheduler"))

    list_ok, cron_output = run_script("list_cron.sh")
    cron_jobs = parse_cron_jobs(cron_output if list_ok else "")
    result = get_module_result("cron")

    return render_template(
        "task_scheduler.html",
        user=user,
        list_ok=list_ok,
        cron_output=cron_output,
        cron_jobs=cron_jobs,
        result=result,
    )


@app.route("/time", methods=["GET", "POST"])
@login_required
def system_time():
    user = current_user()

    if request.method == "POST":
        if user["role"] != "admin":
            flash("Chi admin moi duoc thay doi thoi gian he thong.", "danger")
            return redirect(url_for("system_time"))

        action = request.form.get("action", "")
        script_name = ""
        args: list[str] = []

        if action == "set_time":
            script_name = "set_time.sh"
            args = [request.form.get("new_time", "")]
        elif action == "set_timezone":
            script_name = "set_timezone.sh"
            args = [request.form.get("timezone", "")]
        elif action == "enable_ntp":
            script_name = "enable_ntp.sh"
        elif action == "disable_ntp":
            script_name = "disable_ntp.sh"
        elif action == "sync_time":
            script_name = "sync_time.sh"

        success, output = run_script(script_name, args)
        write_system_log(user["username"], f"time:{action}", success, output)
        set_module_result("time", success, output)
        return redirect(url_for("system_time"))

    show_ok, time_output = run_script("show_time.sh")
    result = get_module_result("time")

    return render_template(
        "system_time.html",
        user=user,
        show_ok=show_ok,
        time_output=time_output,
        result=result,
    )


@app.route("/packages", methods=["GET", "POST"])
@login_required
def package_management():
    user = current_user()

    if request.method == "POST":
        action = request.form.get("action", "")
        script_name = ""
        args: list[str] = []

        if action == "search":
            script_name = "search_package.sh"
            args = [request.form.get("keyword", "")]
        elif action == "install":
            if user["role"] != "admin":
                flash("Chi admin moi duoc cai package.", "danger")
                return redirect(url_for("package_management"))
            script_name = "install_package.sh"
            args = [request.form.get("package_name", "")]
        elif action == "remove":
            if user["role"] != "admin":
                flash("Chi admin moi duoc go package.", "danger")
                return redirect(url_for("package_management"))
            script_name = "remove_package.sh"
            args = [request.form.get("package_name", "")]
        elif action == "upgrade":
            if user["role"] != "admin":
                flash("Chi admin moi duoc nang cap package.", "danger")
                return redirect(url_for("package_management"))
            script_name = "upgrade_package.sh"
            package_name = request.form.get("package_name", "").strip()
            if package_name:
                args = [package_name]

        success, output = run_script(script_name, args)
        write_system_log(user["username"], f"packages:{action}", success, output)
        set_module_result("packages", success, output)
        return redirect(url_for("package_management"))

    list_ok, list_output = run_script("list_packages.sh")
    result = get_module_result("packages")

    return render_template(
        "package_management.html",
        user=user,
        list_ok=list_ok,
        list_output=list_output,
        result=result,
    )


@app.route("/logs")
@login_required
@admin_required
def view_logs():
    logs = ActionLog.query.order_by(ActionLog.created_at.desc()).limit(200).all()
    return render_template("logs.html", user=current_user(), logs=logs)


if __name__ == "__main__":
    init_db()
    app.run(host="0.0.0.0", port=5000, debug=False)
