import os
from datetime import datetime

from app.database import ActionLog, get_session, DATA_DIR

LOG_FILE = os.path.join(DATA_DIR, "logs", "system.log")


class SystemLogger:
    def log(self, username: str, action: str, success: bool, detail: str):
        result = "SUCCESS" if success else "FAILED"
        now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        line = f"{now} | user={username} | action={action} | result={result} | detail={detail}\n"

        os.makedirs(os.path.dirname(LOG_FILE), exist_ok=True)
        with open(LOG_FILE, "a", encoding="utf-8") as f:
            f.write(line)

        session = get_session()
        try:
            session.add(ActionLog(
                username=username,
                action=action,
                result=result,
                detail=detail[:2000],
            ))
            session.commit()
        finally:
            session.close()


logger = SystemLogger()
