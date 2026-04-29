"""Compute one row of headline metrics for a sprint.

Reads ``product_FILTER/<sprint>-sprint-data/{sprint-meta.json, issues.json}``,
applies the same date-aware roster + holiday rules used by
``build_sprint_analysis.py``, and returns a dict ready for the monthly
comparison report.

The dict shape is intentionally flat so it can be consumed by simple
spreadsheet-style code.
"""
from __future__ import annotations

import json
import re
from datetime import date
from pathlib import Path

import compute_capacity as cap

ROOT = Path(__file__).resolve().parent

PRIORITY_ORDER = ["P0", "P1", "P2", "P3", "P4", "(none)"]
PROJECT_KEYS_IN_SCOPE = ("FILTER", "PTGM", "FDSE")
MISC_BUFFER_PCT = 0.20

SUBTASK_TYPES: set[str] = {
    "Dev",
    "QA",
    "Automation",
    "Review",
    "Test Case Creation",
    "Debug",
}
P1_ESC_PATTERN = re.compile(r"p1\s*escal", re.IGNORECASE)

CORE_TEAM_ORDER = list(cap.CORE_TEAM)


def is_subtask(rec: dict) -> bool:
    return (rec.get("issue_type") or "") in SUBTASK_TYPES


def is_p1_escalation(rec: dict) -> bool:
    if not P1_ESC_PATTERN.search(rec.get("summary") or ""):
        return False
    if (rec.get("issue_type") or "") != "Escape Defect":
        return False
    if (rec.get("priority") or "") != "P1":
        return False
    return True


def active_team_for_sprint(sprint_start: date, sprint_end: date) -> list[str]:
    out: list[str] = []
    for name in CORE_TEAM_ORDER:
        bounds = cap.ROSTER_DATES.get(name)
        if not bounds:
            out.append(name)
            continue
        start_d, end_d = bounds
        if start_d and sprint_end < start_d:
            continue
        if end_d and sprint_start > end_d:
            continue
        out.append(name)
    return out


def priority_breakdown(records: list[dict], by_key: dict[str, dict]) -> dict:
    out = {
        p: {"count": 0, "count_all": 0, "hours": 0.0, "keys": [], "_keys": set()}
        for p in PRIORITY_ORDER
    }
    for rec in records:
        rollup_key = (
            rec.get("parent_key")
            if is_subtask(rec) and rec.get("parent_key")
            else rec.get("key")
        )
        parent_rec = by_key.get(rollup_key) if rollup_key else None
        pri_source = parent_rec or rec
        pri = pri_source.get("priority") or rec.get("priority") or ""
        bucket = out.get(pri) or out["(none)"]
        if rollup_key and rollup_key not in bucket["_keys"]:
            bucket["_keys"].add(rollup_key)
            bucket["keys"].append(rollup_key)
            bucket["count"] += 1
        bucket["count_all"] += 1
        bucket["hours"] = round(bucket["hours"] + float(rec.get("time_spent_hrs") or 0.0), 2)
    for v in out.values():
        v.pop("_keys", None)
    return {k: v for k, v in out.items() if k in PRIORITY_ORDER}


def _sum(records: list[dict], field: str) -> float:
    return round(sum(float(r.get(field) or 0.0) for r in records), 2)


def anchor_month(sprint_start: date, sprint_end: date) -> tuple[int, int]:
    """Return (year, month) — the month with the most weekdays in the sprint window.
    Tie-break: earlier month wins."""
    by_month: dict[tuple[int, int], int] = {}
    d = sprint_start
    from datetime import timedelta

    while d <= sprint_end:
        if d.weekday() < 5:
            by_month[(d.year, d.month)] = by_month.get((d.year, d.month), 0) + 1
        d += timedelta(days=1)
    return max(by_month.items(), key=lambda kv: (kv[1], -(kv[0][0] * 12 + kv[0][1])))[0]


def compute_metrics(folder: Path) -> dict:
    issues_file = folder / "issues.json"
    if not issues_file.is_file():
        raise FileNotFoundError(f"Missing {issues_file}")
    payload = json.loads(issues_file.read_text(encoding="utf-8"))
    sprint_meta = payload["sprint_meta"]
    issues = payload["issues"]
    bucket = payload["bucket"]

    sprint_name = sprint_meta["sprint_name"]
    sprint_start = date.fromisoformat(sprint_meta["start_date"])
    sprint_end = date.fromisoformat(sprint_meta["end_date"])
    sprint_wd = int(sprint_meta["working_days"])

    active = active_team_for_sprint(sprint_start, sprint_end)
    active_set = set(active)
    holidays = cap.company_holidays_in_sprint(sprint_start, sprint_end)
    holiday_count = len(holidays)
    holiday_descr = ", ".join(f"{d:%d-%b}: {name}" for d, name in holidays) or "—"
    eff_wd = cap.effective_working_days_in_sprint(sprint_start, sprint_end)

    avail_hours = cap.compute_availability_hours(sprint_start, sprint_end)
    available = round(sum(avail_hours[p] for p in active), 2)
    misc_buf = round(available * MISC_BUFFER_PCT, 2)
    net_available = round(available - misc_buf, 2)

    by_key = {r["key"]: r for r in issues}
    completed = [
        by_key[k] for k in bucket["completed"] if k in by_key and by_key[k].get("assignee") in active_set
    ]
    spillover = [
        by_key[k] for k in bucket["not_completed"] if k in by_key and by_key[k].get("assignee") in active_set
    ]
    removed = [
        by_key[k] for k in bucket["removed"] if k in by_key and by_key[k].get("assignee") in active_set
    ]

    completed_hrs = _sum(completed, "time_spent_hrs")
    completed_oe = _sum(completed, "original_estimate_hrs")
    spillover_hrs = _sum(spillover, "time_spent_hrs")
    spillover_oe = _sum(spillover, "original_estimate_hrs")
    removed_hrs = _sum(removed, "time_spent_hrs")
    removed_oe = _sum(removed, "original_estimate_hrs")
    engaged_hrs = round(completed_hrs + spillover_hrs, 2)
    ideal_capacity_hrs = round(eff_wd * 8.0 * 0.9 * len(active), 2)

    planned_completed = [r for r in completed if not r.get("added_during_sprint")]
    planned_spillover = [r for r in spillover if not r.get("added_during_sprint")]
    planned_completed_oe = _sum(planned_completed, "original_estimate_hrs")
    planned_spillover_oe = _sum(planned_spillover, "original_estimate_hrs")

    in_sprint_tickets = len(completed) + len(spillover)
    in_sprint_oe = round(completed_oe + spillover_oe, 2)
    planned_in_sprint_tickets = len(planned_completed) + len(planned_spillover)
    planned_in_sprint_oe = round(planned_completed_oe + planned_spillover_oe, 2)

    completion_tickets = len(completed) / in_sprint_tickets if in_sprint_tickets else 0
    completion_hours = completed_oe / in_sprint_oe if in_sprint_oe else 0
    plan_completion_tickets = (
        len(planned_completed) / planned_in_sprint_tickets if planned_in_sprint_tickets else 0
    )
    plan_completion_hours = (
        planned_completed_oe / planned_in_sprint_oe if planned_in_sprint_oe else 0
    )

    midsprint_added_recs = [
        r for r in issues
        if r.get("added_during_sprint") and r.get("assignee") in active_set
    ]
    midsprint_added_core = len(midsprint_added_recs)
    midsprint_added_keys = sorted(
        (r.get("key") or "") for r in midsprint_added_recs
    )

    p1_recs = [r for r in issues if is_p1_escalation(r)]
    p1_total = len(p1_recs)
    p1_open = sum(1 for r in p1_recs if (r.get("status_category") or "") != "done")
    p1_keys = sorted((r.get("key") or "") for r in p1_recs)
    p1_open_keys = sorted(
        (r.get("key") or "")
        for r in p1_recs
        if (r.get("status_category") or "") != "done"
    )

    spillover_keys = sorted((r.get("key") or "") for r in spillover)
    removed_keys = sorted((r.get("key") or "") for r in removed)

    completed_priority = priority_breakdown(completed, by_key)
    completed_parents_total = sum(v["count"] for v in completed_priority.values())

    project_dist: dict[str, int] = {}
    for r in issues:
        p = r.get("project") or "(none)"
        project_dist[p] = project_dist.get(p, 0) + 1

    inactive_excluded = [n for n in CORE_TEAM_ORDER if n not in active_set]

    am_y, am_m = anchor_month(sprint_start, sprint_end)
    return {
        "sprint_name": sprint_name,
        "sprint_id": sprint_meta.get("sprint_id"),
        "start": sprint_start,
        "end": sprint_end,
        "anchor_year": am_y,
        "anchor_month": am_m,
        "anchor_month_label": date(am_y, am_m, 1).strftime("%b %Y"),
        "working_days": sprint_wd,
        "company_holidays": holiday_count,
        "company_holidays_descr": holiday_descr,
        "effective_working_days": eff_wd,
        "active_team": len(active),
        "inactive_excluded": inactive_excluded,
        "available_hrs": available,
        "misc_buffer_hrs": misc_buf,
        "net_available_hrs": net_available,
        "ideal_capacity_hrs": ideal_capacity_hrs,
        "completed_records": len(completed),
        "completed_parents": completed_parents_total,
        "completed_hrs": completed_hrs,
        "completed_oe_hrs": completed_oe,
        "spillover_records": len(spillover),
        "spillover_hrs": spillover_hrs,
        "spillover_oe_hrs": spillover_oe,
        "spillover_keys": spillover_keys,
        "removed_records": len(removed),
        "removed_hrs": removed_hrs,
        "removed_oe_hrs": removed_oe,
        "removed_keys": removed_keys,
        "engaged_hrs": engaged_hrs,
        "in_sprint_tickets": in_sprint_tickets,
        "in_sprint_oe": in_sprint_oe,
        "completion_tickets": completion_tickets,
        "completion_hours": completion_hours,
        "plan_completion_tickets": plan_completion_tickets,
        "plan_completion_hours": plan_completion_hours,
        "midsprint_additions_core": midsprint_added_core,
        "midsprint_added_keys": midsprint_added_keys,
        "p1_escalations_total": p1_total,
        "p1_escalations_open": p1_open,
        "p1_escalation_keys": p1_keys,
        "p1_escalation_open_keys": p1_open_keys,
        "priority": completed_priority,
        "project_dist": project_dist,
        "efficiency_vs_net_available": (
            round(completed_hrs / net_available, 4) if net_available else 0
        ),
    }


def discover_sprints(root: Path | None = None) -> list[Path]:
    base = (root or ROOT) / "product_FILTER"
    if not base.is_dir():
        return []
    return sorted(
        p for p in base.iterdir() if p.is_dir() and (p / "issues.json").is_file()
    )
