from __future__ import annotations

from dataclasses import asdict

from core.utils.time_utils import parse_iso


class ConflictHandler:
    def should_apply(self, current: object | None, incoming: object) -> bool:
        if current is None:
            return True
        current_data = asdict(current)
        incoming_data = asdict(incoming)
        current_updated = parse_iso(current_data.get("updated_at"))
        incoming_updated = parse_iso(incoming_data.get("updated_at"))
        if current_updated and incoming_updated:
            return incoming_updated >= current_updated
        return True
