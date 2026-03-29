from __future__ import annotations

from datetime import UTC, datetime, timedelta


def utc_now() -> datetime:
    return datetime.now(tz=UTC)


def utc_now_iso() -> str:
    return utc_now().isoformat()


def parse_iso(value: str | None) -> datetime | None:
    if not value:
        return None
    return datetime.fromisoformat(value)


def format_dt(value: str | None) -> str:
    if not value:
        return "Never"
    dt = parse_iso(value)
    if not dt:
        return "Never"
    local_dt = dt.astimezone()
    return local_dt.strftime("%Y-%m-%d %H:%M")


def format_relative(value: str | None) -> str:
    dt = parse_iso(value)
    if not dt:
        return "Never"
    delta = utc_now() - dt.astimezone(UTC)
    seconds = int(delta.total_seconds())
    if seconds < 60:
        return "Just now"
    if seconds < 3600:
        return f"{seconds // 60}m ago"
    if seconds < 86400:
        return f"{seconds // 3600}h ago"
    return f"{seconds // 86400}d ago"


def format_duration(seconds: int | float | None) -> str:
    total = max(int(seconds or 0), 0)
    hours, remainder = divmod(total, 3600)
    minutes, secs = divmod(remainder, 60)
    if hours:
        return f"{hours:02d}:{minutes:02d}:{secs:02d}"
    return f"{minutes:02d}:{secs:02d}"


def format_minutes(total_minutes: int) -> str:
    hours, minutes = divmod(total_minutes, 60)
    if hours:
        return f"{hours}h {minutes:02d}m"
    return f"{minutes}m"


def add_minutes(value: str, minutes: int) -> str:
    dt = parse_iso(value) or utc_now()
    return (dt + timedelta(minutes=minutes)).isoformat()
