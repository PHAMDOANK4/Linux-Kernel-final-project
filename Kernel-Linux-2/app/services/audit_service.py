from __future__ import annotations

import logging
from typing import Any

from flask import current_app

from ..extensions import db
from ..models import AuditLog, SystemEvent

logger = logging.getLogger("ubuntu_monitor")


def record_audit(username: str, action: str, module: str, result: str, details: str = "") -> AuditLog:
    entry = AuditLog(
        username=username,
        action=action,
        module=module,
        result=result,
        details=details,
    )
    db.session.add(entry)
    db.session.commit()
    logger.info("%s %s %s %s %s", username, module, action, result, details)
    return entry


def record_system_event(event_type: str, target: str, module: str, message: str) -> SystemEvent:
    entry = SystemEvent(
        event_type=event_type,
        target=target,
        module=module,
        message=message,
    )
    db.session.add(entry)
    db.session.commit()
    logger.info("EVENT %s %s %s %s", module, event_type, target, message)
    return entry
