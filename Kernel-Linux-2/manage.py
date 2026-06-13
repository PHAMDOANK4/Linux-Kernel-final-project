from __future__ import annotations

import argparse

from app import create_app
from app.extensions import db
from app.models import Role, User

app = create_app()


def init_db(create_admin: bool = False) -> None:
    with app.app_context():
        db.create_all()
        if create_admin:
            admin_role = Role.query.filter_by(name="Admin").first()
            if admin_role is None:
                admin_role = Role(name="Admin", description="Toàn quyền quản trị hệ thống")
                db.session.add(admin_role)
                db.session.commit()
            admin = User.query.filter_by(username=app.config["DEFAULT_ADMIN_USERNAME"]).first()
            if admin is None:
                admin = User(username=app.config["DEFAULT_ADMIN_USERNAME"], full_name="System Administrator", role=admin_role)
                admin.set_password(app.config["DEFAULT_ADMIN_PASSWORD"])
                db.session.add(admin)
                db.session.commit()


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("command", choices=["init-db"])
    parser.add_argument("--create-admin", action="store_true")
    args = parser.parse_args()

    if args.command == "init-db":
        init_db(create_admin=args.create_admin)
        print("Database initialized")
