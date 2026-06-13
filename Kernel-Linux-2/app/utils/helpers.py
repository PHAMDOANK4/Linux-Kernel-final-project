from __future__ import annotations

import json
import re
from datetime import datetime
from typing import Any


def human_bytes(value: float) -> str:
    units = ["B", "KB", "MB", "GB", "TB"]
    amount = float(value)
    for unit in units:
        if amount < 1024 or unit == units[-1]:
            return f"{amount:.2f} {unit}"
        amount /= 1024
    return f"{amount:.2f} B"


def format_datetime(value: datetime | None) -> str:
    if value is None:
        return "-"
    return value.strftime("%Y-%m-%d %H:%M:%S")


def parse_table_output(output: str) -> list[dict[str, str]]:
    rows: list[dict[str, str]] = []
    lines = [line.strip() for line in output.splitlines() if line.strip() and not line.strip().startswith("#")]
    if not lines:
        return rows

    start_index = 0
    if len(lines) > 1:
        first_parts = [segment.strip() for segment in lines[0].split("|")]
        header_like = all(re.fullmatch(r"[A-Za-z0-9 %._/-]+", part or "") for part in first_parts)
        if header_like and any(not part.isdigit() for part in first_parts):
            start_index = 1

    for raw_line in lines[start_index:]:
        line = raw_line.strip()
        parts = [segment.strip() for segment in line.split("|")]
        rows.append({f"col_{index + 1}": part for index, part in enumerate(parts)})
    return rows


def parse_key_value_output(output: str) -> dict[str, str]:
    parsed: dict[str, str] = {}
    for raw_line in output.splitlines():
        line = raw_line.strip()
        if not line or line.startswith("#"):
            continue
        if "=" in line:
            key, value = line.split("=", 1)
            parsed[key.strip().lower().replace(" ", "_")] = value.strip()
        elif ":" in line:
            key, value = line.split(":", 1)
            parsed[key.strip().lower().replace(" ", "_")] = value.strip()
    return parsed


def parse_display_output(output: str) -> dict[str, Any]:
    text = (output or "").strip()
    if not text:
        return {"kind": "raw", "text": ""}

    if text.startswith("{") or text.startswith("["):
        try:
            payload = json.loads(text)
        except json.JSONDecodeError:
            payload = None
        else:
            if isinstance(payload, dict):
                items = list(payload.items())
                return {"kind": "kv", "items": items, "text": text}
            if isinstance(payload, list) and payload and isinstance(payload[0], dict):
                headers = list(payload[0].keys())
                rows = [[str(row.get(header, "")) for header in headers] for row in payload]
                return {"kind": "table", "headers": headers, "rows": rows, "text": text}

    lines = [line.strip() for line in text.splitlines() if line.strip()]
    if not lines:
        return {"kind": "raw", "text": text}

    if len(lines) == 1:
        line = lines[0]
        for separator in ("=", ":", "|"):
            if separator in line:
                key, value = line.split(separator, 1)
                if key.strip() and value.strip():
                    return {"kind": "kv", "items": [(key.strip(), value.strip())], "text": text}
        return {"kind": "raw", "text": text}

    if all("|" in line for line in lines):
        segments = [line.split("|") for line in lines]
        width = len(segments[0])
        if width >= 2 and all(len(segment) == width for segment in segments):
            headers = [value.strip() for value in segments[0]]
            rows = [[value.strip() for value in segment] for segment in segments[1:]]
            return {"kind": "table", "headers": headers, "rows": rows, "text": text}

    kv_items: list[tuple[str, str]] = []
    for line in lines:
        for separator in ("=", ":"):
            if separator in line:
                key, value = line.split(separator, 1)
                if key.strip() and value.strip():
                    kv_items.append((key.strip(), value.strip()))
                    break
    if kv_items and len(kv_items) == len(lines):
        return {"kind": "kv", "items": kv_items, "text": text}

    return {"kind": "raw", "text": text}
