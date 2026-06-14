def parse_file_listing(output: str) -> list[dict]:
    entries: list[dict] = []
    for line in output.splitlines():
        parts = line.split("\t", 2)
        if len(parts) != 3:
            continue
        item_type, name, full_path = parts
        is_dir = item_type == "DIR"
        entries.append({
            "type": item_type,
            "name": name,
            "path": full_path,
            "is_dir": is_dir,
            "icon": "folder" if is_dir else "file",
        })
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
        jobs.append({
            "line_number": line_number,
            "raw_line": line,
            "schedule": schedule,
            "command": command,
            **schedule_data,
        })
    return jobs
