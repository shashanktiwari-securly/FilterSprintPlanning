"""
Fetch FILTER sprint issues with full delivery fields (Time Spent, Original Estimate,
parent, dates, labels) for sprint-analysis workbooks.

Outputs::

    product_FILTER/<sprint>-sprint-data/issues.json
        sprint_meta:    same keys as fetch_filter_sprint_meta.py
        issues:         flat list of issue records (one per Jira issue currently in
                        sprint OR removed mid-flight). Each record has the columns the
                        sprint-analysis workbook needs.
        bucket:         {"completed": [keys], "not_completed": [keys], "removed": [keys]}

Implements the **hybrid worklog rule** from ``sprint-analysis.md``:

    - Single-sprint ticket: ``timespent`` (fallback ``aggregatetimespent``).
    - Multi-sprint ticket : SUM of worklog entries whose ``started`` is inside
      ``[sprint_start, sprint_end]``; row dropped if zero in-sprint logging.
    - Removed bucket: headline metric is **Original Estimate**, time-spent kept
      for reference (often 0).

Bucketing (top-down, first match wins) — same as ``sprint-analysis.md``::

    Removed       → keys returned by GreenHopper sprintreport puntedIssues
    Completed     → statusCategory=done OR status in {Resolved, Code Review}
    Not Completed → everything else still on the sprint

Env: JIRA_URL, JIRA_EMAIL, JIRA_API_TOKEN
Optional: JIRA_FILTER_BOARD_ID (default 281)

Usage::

    python fetch_filter_sprint_issues.py sprint-Hanna
"""
from __future__ import annotations

import argparse
import json
import os
import sys
import time
import urllib.error
import urllib.parse
import urllib.request
from datetime import date, datetime, timedelta, timezone
from typing import Any

ROOT = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, ROOT)

from build_sprint_matrix_report import auth_header, search_jql_page  # noqa: E402
from filter_jira_sprint_report import (  # noqa: E402
    _keys_from_map_added,
    _keys_from_rapid_block,
    find_sprint_on_boards,
    get_scrum_boards,
    http_get_json,
    order_boards_preferred_first,
    resolve_sprint_from_filter_project,
)
from sprint_overrides import overridden_window  # noqa: E402

PROJECT_KEY = "FILTER"
PROJECT_KEYS_IN_SCOPE = ("FILTER", "PTGM", "FDSE")
SPRINT_FIELD = "customfield_10020"  # standard Jira Cloud Sprint field
COMPLETED_STATUSES = {"Resolved", "Code Review"}

ISSUE_FIELDS = [
    "summary",
    "issuetype",
    "parent",
    "assignee",
    "status",
    "resolution",
    "priority",
    "created",
    "resolutiondate",
    "updated",
    "labels",
    "project",
    "timespent",
    "aggregatetimespent",
    "timeoriginalestimate",
    "worklog",
    SPRINT_FIELD,
]


def to_hours(seconds: Any) -> float:
    if seconds is None:
        return 0.0
    try:
        return round(float(seconds) / 3600.0, 2)
    except (TypeError, ValueError):
        return 0.0


def parse_iso_dt(s: str | None) -> datetime | None:
    if not s:
        return None
    txt = s.replace("Z", "+00:00")
    try:
        return datetime.fromisoformat(txt)
    except ValueError:
        try:
            return datetime.strptime(s[:19], "%Y-%m-%dT%H:%M:%S").replace(tzinfo=timezone.utc)
        except ValueError:
            return None


def iso_date_only(s: str | None) -> str | None:
    if not s:
        return None
    return s[:10]


def fetch_full_worklog(base: str, key: str) -> list[dict[str, Any]]:
    """Page through /rest/api/3/issue/{key}/worklog (max 5 000 per page)."""
    out: list[dict[str, Any]] = []
    start = 0
    while True:
        data = http_get_json(
            base,
            f"/rest/api/3/issue/{key}/worklog",
            {"startAt": str(start), "maxResults": "1000"},
        )
        worklogs = data.get("worklogs") or []
        out.extend(worklogs)
        total = int(data.get("total") or 0)
        start += len(worklogs)
        if not worklogs or start >= total:
            break
    return out


def in_sprint_worklog_hours(
    base: str,
    key: str,
    inline_worklog: dict[str, Any] | None,
    sprint_start: datetime,
    sprint_end_exclusive: datetime,
) -> float:
    """Sum worklog ``timeSpentSeconds`` whose ``started`` is in ``[start, end)``."""
    worklogs: list[dict[str, Any]]
    if inline_worklog and inline_worklog.get("total", 0) <= len(
        inline_worklog.get("worklogs") or []
    ):
        worklogs = inline_worklog.get("worklogs") or []
    else:
        worklogs = fetch_full_worklog(base, key)

    total_s = 0
    for w in worklogs:
        started = parse_iso_dt(w.get("started"))
        if started is None:
            continue
        if started.tzinfo is None:
            started = started.replace(tzinfo=timezone.utc)
        if sprint_start <= started < sprint_end_exclusive:
            total_s += int(w.get("timeSpentSeconds") or 0)
    return round(total_s / 3600.0, 2)


def collect_sprint_field(fields: dict[str, Any]) -> list[Any]:
    """Return the list of sprints recorded against the issue."""
    val = fields.get(SPRINT_FIELD)
    if val is None:
        val = fields.get("sprint")
    if val is None:
        return []
    if isinstance(val, list):
        return val
    if isinstance(val, dict):
        return [val]
    return []


def is_multi_sprint(sprint_field_value: list[Any]) -> bool:
    """Multi-sprint = issue has appeared on > 1 sprint."""
    if not sprint_field_value:
        return False
    if len(sprint_field_value) > 1:
        return True
    return False


def get_sprint_report(base: str, board_id: int, sprint_id: int) -> dict[str, Any]:
    return http_get_json(
        base,
        "/rest/greenhopper/1.0/rapid/charts/sprintreport",
        {"rapidViewId": str(board_id), "sprintId": str(sprint_id)},
    )


def fetch_sprint_meta(base: str, sprint_name: str) -> dict[str, Any]:
    pair = resolve_sprint_from_filter_project(base, sprint_name)
    if not pair:
        boards = order_boards_preferred_first(get_scrum_boards(base))
        pair = find_sprint_on_boards(base, boards, sprint_name)
    if not pair:
        raise SystemExit(f"Could not resolve sprint {sprint_name!r} on FILTER boards.")
    board_id, sprint_id = pair
    meta = http_get_json(base, f"/rest/agile/1.0/sprint/{sprint_id}")
    start_raw = meta.get("startDate")
    end_raw = meta.get("endDate")
    if not start_raw or not end_raw:
        raise SystemExit(
            f"Sprint {sprint_name!r} has no startDate/endDate in Jira yet (state={meta.get('state')})."
        )
    start_dt = parse_iso_dt(start_raw)
    end_dt = parse_iso_dt(end_raw)
    if start_dt is None or end_dt is None:
        raise SystemExit(f"Could not parse sprint dates for {sprint_name!r}.")
    if start_dt.tzinfo is None:
        start_dt = start_dt.replace(tzinfo=timezone.utc)
    if end_dt.tzinfo is None:
        end_dt = end_dt.replace(tzinfo=timezone.utc)
    end_dt_exclusive = end_dt
    start_d = start_dt.date()
    end_d = end_dt.date()
    jira_start_d, jira_end_d = start_d, end_d
    override_applied = False
    override = overridden_window(meta.get("name") or sprint_name)
    if override:
        ov_start, ov_end = override
        if (ov_start, ov_end) != (start_d, end_d):
            override_applied = True
            start_d, end_d = ov_start, ov_end
            start_dt = datetime.combine(start_d, datetime.min.time()).replace(
                tzinfo=timezone.utc
            )
            end_dt_exclusive = datetime.combine(end_d, datetime.max.time()).replace(
                tzinfo=timezone.utc, microsecond=0
            )
            start_raw = start_dt.isoformat().replace("+00:00", "Z")
            end_raw = end_dt_exclusive.isoformat().replace("+00:00", "Z")
            print(
                f"  applied canonical-window override: "
                f"{jira_start_d.isoformat()}→{jira_end_d.isoformat()}  ->  "
                f"{start_d.isoformat()}→{end_d.isoformat()}"
            )
    weekdays = 0
    d = start_d
    while d <= end_d:
        if d.weekday() < 5:
            weekdays += 1
        d += timedelta(days=1)
    return {
        "sprint_name": meta.get("name") or sprint_name,
        "sprint_id": sprint_id,
        "board_id": board_id,
        "origin_board_id": meta.get("originBoardId"),
        "state": meta.get("state"),
        "goal": meta.get("goal"),
        "start_date": start_d.isoformat(),
        "end_date": end_d.isoformat(),
        "start_date_raw": start_raw,
        "end_date_raw": end_raw,
        "jira_start_date": jira_start_d.isoformat(),
        "jira_end_date": jira_end_d.isoformat(),
        "override_applied": override_applied,
        "working_days": weekdays,
        "_start_dt": start_dt,
        "_end_dt": end_dt_exclusive,
    }


def http_get_issue(base: str, key: str, fields: list[str]) -> dict[str, Any]:
    return http_get_json(
        base,
        f"/rest/api/3/issue/{key}",
        {"fields": ",".join(fields)},
    )


def fetch_issues_for_jql(base: str, jql: str) -> list[dict[str, Any]]:
    out: list[dict[str, Any]] = []
    next_token: str | None = None
    page_size = 100
    while True:
        data = search_jql_page(base, jql, ISSUE_FIELDS, page_size, next_token)
        issues = data.get("issues") or []
        out.extend(issues)
        if data.get("isLast") or not issues:
            break
        next_token = data.get("nextPageToken")
        if not next_token:
            break
        time.sleep(0.1)
    return out


def normalize_issue(
    base: str,
    raw: dict[str, Any],
    sprint_name: str,
    sprint_start_dt: datetime,
    sprint_end_dt: datetime,
) -> dict[str, Any] | None:
    """Convert one Jira issue to our flat record. Returns None to drop multi-sprint zero-log."""
    key = raw.get("key", "")
    f = raw.get("fields") or {}
    issuetype = (f.get("issuetype") or {}).get("name") or ""
    parent = f.get("parent") or {}
    parent_key = parent.get("key")
    parent_type = ((parent.get("fields") or {}).get("issuetype") or {}).get("name") or ""
    assignee = (f.get("assignee") or {}).get("displayName")
    status_obj = f.get("status") or {}
    status = status_obj.get("name")
    status_cat = (status_obj.get("statusCategory") or {}).get("key") or ""
    resolution = (f.get("resolution") or {}).get("name") or ""
    priority = (f.get("priority") or {}).get("name") or ""
    project = (f.get("project") or {}).get("key") or ""
    labels = list(f.get("labels") or [])

    sprint_field_value = collect_sprint_field(f)
    multi_sprint = is_multi_sprint(sprint_field_value)
    inline_worklog = f.get("worklog") if isinstance(f.get("worklog"), dict) else None

    timespent_sec = f.get("timespent")
    if timespent_sec is None:
        timespent_sec = f.get("aggregatetimespent")
    timespent_h_total = to_hours(timespent_sec)
    if multi_sprint:
        in_sprint_h = in_sprint_worklog_hours(
            base, key, inline_worklog, sprint_start_dt, sprint_end_dt
        )
        time_spent = in_sprint_h
    else:
        time_spent = timespent_h_total

    original_estimate_h = to_hours(f.get("timeoriginalestimate"))

    return {
        "key": key,
        "issue_type": issuetype,
        "summary": f.get("summary") or "",
        "parent_key": parent_key,
        "parent_type": parent_type,
        "assignee": assignee,
        "status": status,
        "status_category": status_cat,
        "resolution": resolution,
        "priority": priority,
        "created": iso_date_only(f.get("created")),
        "resolved": iso_date_only(f.get("resolutiondate")),
        "updated": iso_date_only(f.get("updated")),
        "sprint": sprint_name,
        "time_spent_hrs": time_spent,
        "time_spent_total_hrs": timespent_h_total,
        "original_estimate_hrs": original_estimate_h,
        "project": project,
        "labels": labels,
        "blockers": "",
        "_multi_sprint": multi_sprint,
        "_drop_no_in_sprint_log": multi_sprint and time_spent == 0.0 and timespent_h_total > 0.0,
    }


def main() -> None:
    ap = argparse.ArgumentParser(description="Fetch FILTER sprint issues with hours.")
    ap.add_argument("sprint_name", nargs="?", default="sprint-Hanna", help="Jira sprint name")
    ap.add_argument(
        "--out",
        default=None,
        help="Path to write issues.json (default: product_FILTER/<sprint>-sprint-data/issues.json)",
    )
    args = ap.parse_args()

    for env_key in ("JIRA_URL", "JIRA_EMAIL", "JIRA_API_TOKEN"):
        if not os.environ.get(env_key):
            raise SystemExit(f"Missing environment variable {env_key}")
    base = os.environ["JIRA_URL"].rstrip("/")
    auth_header()  # validate envs

    sprint_meta = fetch_sprint_meta(base, args.sprint_name)
    sprint_start_dt: datetime = sprint_meta.pop("_start_dt")
    sprint_end_dt: datetime = sprint_meta.pop("_end_dt")

    print(
        f"sprint_name={sprint_meta['sprint_name']} id={sprint_meta['sprint_id']} "
        f"board={sprint_meta['board_id']} window={sprint_meta['start_date']}..{sprint_meta['end_date']}"
    )

    project_clause = ", ".join(PROJECT_KEYS_IN_SCOPE)
    jql = (
        f'project in ({project_clause}) AND sprint = "{sprint_meta["sprint_name"]}"'
    )
    print(f"Pulling current sprint scope:  {jql}")
    raw_issues = fetch_issues_for_jql(base, jql)
    print(f"  fetched {len(raw_issues)} issues currently in sprint")

    print("Pulling GreenHopper sprint report for puntedIssues + issueKeysAddedDuringSprint ...")
    report = get_sprint_report(
        base, sprint_meta["board_id"], sprint_meta["sprint_id"]
    )
    contents = (report.get("contents") or {})
    removed_keys = sorted(set(_keys_from_rapid_block(contents.get("puntedIssues"))))
    added_during_sprint_keys = set(
        _keys_from_map_added(contents.get("issueKeysAddedDuringSprint"))
    )
    print(
        f"  removed_keys = {len(removed_keys)} keys; "
        f"added_during_sprint = {len(added_during_sprint_keys)} keys"
    )

    in_sprint_keys = {(i.get("key") or "") for i in raw_issues}
    missing = [k for k in removed_keys if k and k not in in_sprint_keys]
    extra_issues: list[dict[str, Any]] = []
    for k in missing:
        try:
            extra_issues.append(http_get_issue(base, k, ISSUE_FIELDS))
            time.sleep(0.05)
        except RuntimeError as e:
            print(f"  warning: failed to fetch removed issue {k}: {e}")

    issue_records: list[dict[str, Any]] = []
    skipped_out_of_scope = 0
    for raw in list(raw_issues) + extra_issues:
        rec = normalize_issue(
            base, raw, sprint_meta["sprint_name"], sprint_start_dt, sprint_end_dt
        )
        if rec is None:
            continue
        if rec.pop("_drop_no_in_sprint_log", False):
            print(f"  drop multi-sprint w/o in-sprint worklog: {rec['key']}")
            continue
        rec.pop("_multi_sprint", None)
        if (rec.get("project") or "") not in PROJECT_KEYS_IN_SCOPE:
            skipped_out_of_scope += 1
            continue
        rec["added_during_sprint"] = rec["key"] in added_during_sprint_keys
        issue_records.append(rec)
    if skipped_out_of_scope:
        print(
            f"  dropped {skipped_out_of_scope} out-of-scope issues "
            f"(not in {PROJECT_KEYS_IN_SCOPE})"
        )

    completed_keys: list[str] = []
    not_completed_keys: list[str] = []
    removed_set = set(removed_keys)
    for rec in issue_records:
        k = rec["key"]
        if k in removed_set:
            continue
        if rec["status_category"] == "done" or rec["status"] in COMPLETED_STATUSES:
            completed_keys.append(k)
        else:
            not_completed_keys.append(k)

    out_payload = {
        "sprint_meta": sprint_meta,
        "bucket": {
            "removed": [k for k in removed_keys if any(r["key"] == k for r in issue_records)],
            "completed": completed_keys,
            "not_completed": not_completed_keys,
        },
        "issues": issue_records,
        "removed_keys_from_jira": removed_keys,
        "added_during_sprint_keys": sorted(added_during_sprint_keys),
    }

    out_path = args.out
    if not out_path:
        slug = sprint_meta["sprint_name"]
        out_dir = os.path.join(ROOT, "product_FILTER", f"{slug}-sprint-data")
        os.makedirs(out_dir, exist_ok=True)
        out_path = os.path.join(out_dir, "issues.json")
    with open(out_path, "w", encoding="utf-8") as f:
        json.dump(out_payload, f, indent=2, default=str)
        f.write("\n")

    print(
        f"\nWrote {out_path}\n"
        f"  completed={len(completed_keys)}, not_completed={len(not_completed_keys)}, "
        f"removed={len(out_payload['bucket']['removed'])}"
    )


if __name__ == "__main__":
    main()
