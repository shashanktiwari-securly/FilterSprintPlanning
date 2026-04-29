"""Canonical sprint-window overrides for the FILTER scrum team.

Jira's recorded sprint start/end often drifts by a day because sprints are
started/closed at different times of day (and the API returns UTC timestamps).
This module holds the team's authoritative 15-day Tuesday→Monday windows, which
the fetch + build scripts use in preference to the Jira values.

``SPRINT_OVERRIDES`` maps Jira sprint name → (start_date, end_date, both
inclusive). Any sprint missing from the mapping falls back to the Jira-reported
dates.
"""
from __future__ import annotations

from datetime import date, datetime, timedelta, timezone
from typing import Any

SPRINT_OVERRIDES: dict[str, tuple[date, date]] = {
    "sprint-Arthur":    (date(2026, 1, 6),  date(2026, 1, 19)),
    "sprint-Bertha":    (date(2026, 1, 20), date(2026, 2, 2)),
    "sprint-Cristobal": (date(2026, 2, 3),  date(2026, 2, 16)),
    "sprint-Dolly":     (date(2026, 2, 17), date(2026, 3, 2)),
    "sprint-Edouard":   (date(2026, 3, 3),  date(2026, 3, 16)),
    "sprint-Fay":       (date(2026, 3, 17), date(2026, 3, 30)),
    "sprint-Gonzalo":   (date(2026, 3, 31), date(2026, 4, 13)),
    "sprint-Hanna":     (date(2026, 4, 14), date(2026, 4, 27)),
}


def count_weekdays_inclusive(start: date, end: date) -> int:
    n = 0
    d = start
    while d <= end:
        if d.weekday() < 5:
            n += 1
        d += timedelta(days=1)
    return n


def apply_override(meta: dict[str, Any]) -> dict[str, Any]:
    """If ``meta["sprint_name"]`` is overridden, rewrite the date/working-day fields.

    Returns the same dict for call-site convenience. The following keys are
    updated in place when an override exists:
        start_date, end_date                     (ISO strings, canonical window)
        start_date_raw, end_date_raw             (ISO timestamps, 00:00:00+00:00
                                                  at canonical start and
                                                  23:59:59+00:00 at canonical end)
        working_days                             (weekday count across new window)
        override_applied                         (True)

    When no override exists, the dict is returned unchanged.
    """
    name = meta.get("sprint_name") or meta.get("name") or ""
    override = SPRINT_OVERRIDES.get(name)
    if not override:
        return meta
    start_d, end_d = override
    start_dt = datetime.combine(start_d, datetime.min.time()).replace(tzinfo=timezone.utc)
    # End-of-day for the last working day (used only for display / raw)
    end_dt = datetime.combine(end_d, datetime.max.time()).replace(
        tzinfo=timezone.utc, microsecond=0
    )
    meta["start_date"] = start_d.isoformat()
    meta["end_date"] = end_d.isoformat()
    meta["start_date_raw"] = start_dt.isoformat().replace("+00:00", "Z")
    meta["end_date_raw"] = end_dt.isoformat().replace("+00:00", "Z")
    meta["working_days"] = count_weekdays_inclusive(start_d, end_d)
    meta["override_applied"] = True
    return meta


def overridden_window(sprint_name: str) -> tuple[date, date] | None:
    """Return (start, end) if the sprint is overridden, else None."""
    return SPRINT_OVERRIDES.get(sprint_name)
