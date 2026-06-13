from __future__ import annotations

import logging
from logging.handlers import RotatingFileHandler
from pathlib import Path

from flask import Flask

from .config import Config, LOG_DIR
from .extensions import db
from .models import Role, User
from .utils.helpers import parse_display_output


def seed_data(app: Flask) -> None:
    with app.app_context():
        db.create_all()
        admin_role = Role.query.filter_by(name="Admin").first()
        if admin_role is None:
            admin_role = Role(name="Admin", description="Toàn quyền quản trị hệ thống")
            db.session.add(admin_role)
        operator_role = Role.query.filter_by(name="Operator").first()
        if operator_role is None:
            operator_role = Role(name="Operator", description="Chỉ xem thông tin")
            db.session.add(operator_role)
        db.session.commit()

        admin_username = app.config["DEFAULT_ADMIN_USERNAME"]
        admin = User.query.filter_by(username=admin_username).first()
        if admin is None:
            admin = User(username=admin_username, full_name="System Administrator", role=admin_role)
            admin.set_password(app.config["DEFAULT_ADMIN_PASSWORD"])
            db.session.add(admin)

        operator_username = app.config["DEFAULT_OPERATOR_USERNAME"]
        operator = User.query.filter_by(username=operator_username).first()
        if operator is None:
            operator = User(username=operator_username, full_name="System Operator", role=operator_role)
            operator.set_password(app.config["DEFAULT_OPERATOR_PASSWORD"])
            db.session.add(operator)

        db.session.commit()


def configure_logging(app: Flask) -> None:
    log_file = Path(app.config["SYSTEM_LOG_FILE"])
    log_file.parent.mkdir(exist_ok=True)

    formatter = logging.Formatter("%(asctime)s %(levelname)s %(message)s")
    file_handler = RotatingFileHandler(log_file, maxBytes=1_000_000, backupCount=5)
    file_handler.setFormatter(formatter)
    file_handler.setLevel(logging.INFO)

    stream_handler = logging.StreamHandler()
    stream_handler.setFormatter(formatter)
    stream_handler.setLevel(logging.INFO)

    app.logger.handlers.clear()
    app.logger.setLevel(logging.INFO)
    app.logger.addHandler(file_handler)
    app.logger.addHandler(stream_handler)
    logging.getLogger("ubuntu_monitor").handlers = [file_handler, stream_handler]
    logging.getLogger("ubuntu_monitor").setLevel(logging.INFO)


def create_app() -> Flask:
    app = Flask(
        __name__,
        instance_relative_config=True,
        template_folder="../templates",
        static_folder="../static",
    )
    app.config.from_object(Config)

    db.init_app(app)
    configure_logging(app)

    @app.context_processor
    def inject_helpers():
        return {"parse_display_output": parse_display_output}

    from .blueprints.admin import admin_bp
    from .blueprints.auth import auth_bp
    from .blueprints.dashboard import dashboard_bp
    from .blueprints.files import files_bp
    from .blueprints.network import network_bp
    from .blueprints.process import process_bp
    from .blueprints.sockets import sockets_bp

    app.register_blueprint(auth_bp)
    app.register_blueprint(dashboard_bp)
    app.register_blueprint(process_bp)
    app.register_blueprint(files_bp)
    app.register_blueprint(sockets_bp)
    app.register_blueprint(network_bp)
    app.register_blueprint(admin_bp)

    with app.app_context():
        seed_data(app)

    return app
