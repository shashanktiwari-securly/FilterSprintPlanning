"""Assemble dashboard JSON from Jira search dumps (paginated issue payloads)."""

from __future__ import annotations

import json
import os
from calendar import monthrange
from datetime import date, datetime, timezone
from pathlib import Path
from urllib.parse import quote

ROOT = Path(__file__).resolve().parent
OUT = ROOT / "reports" / "filter-zendesk-weekly-dashboard.json"
DONE_AT_PATH = ROOT / "reports" / "jira-done-at.json"

PROJECTS = [
    {"key": "AICHAT", "name": "Product_AIChat", "label": "AIChat"},
    {"key": "AWARE", "name": "product_AWARE", "label": "Aware"},
    {"key": "RESP", "name": "product_CaseManager", "label": "Case Manager"},
    {"key": "COM", "name": "Pass-Flex Common Services", "label": "Comm"},
    {"key": "DD", "name": "DyKnow & Reveal", "label": "DD"},
    {"key": "DE", "name": "OPS_DE", "label": "DE"},
    {"key": "DEVOPS", "name": "ops_devops", "label": "DevOps"},
    {"key": "FILTER", "name": "product_FILTER", "label": "Filter"},
    {"key": "FLEX", "name": "Flex", "label": "Flex"},
    {"key": "HOME", "name": "product_HOME", "label": "Home"},
    {"key": "MDMCLASS", "name": "product_MDM_CLASSROOM", "label": "MDM Class"},
    {"key": "PRODUCT24", "name": "product_oncall", "label": "On-Call"},
    {"key": "PAGESCAN", "name": "prod_pagescan", "label": "PageScan"},
    {"key": "PASS", "name": "Pass", "label": "Pass"},
]
PROJECT_BY_KEY = {p["key"]: p for p in PROJECTS}
PROJECT_LIST = ", ".join(p["key"] for p in PROJECTS)
CREATED_FROM = "2026-08-01"
CREATED_FROM_LABEL = "1 Aug 2026"
TITLE = "Monthly Escape Defect and Support Request Dashboard"
JIRA_URL = os.environ.get("JIRA_URL", "https://securly.atlassian.net").rstrip("/")
ISSUE_FIELDS = [
    "summary",
    "status",
    "issuetype",
    "priority",
    "created",
    "updated",
    "resolutiondate",
    "statuscategorychangedate",
    "project",
    "assignee",
    "customfield_11201",
]

SNAPSHOT = ""
SNAPSHOT_DT = datetime.min.replace(tzinfo=timezone.utc)
MONTHS: list[dict] = []
MONTH_BY_ID: dict[str, dict] = {}

JQL_CREATED = (
    f"project in ({PROJECT_LIST}) AND issuetype in "
    '("Escape Defect", "Support Request") AND "Zendesk Ticket Count" > 0 '
    f'AND created >= "{CREATED_FROM}" ORDER BY created ASC'
)
JQL_OPEN = (
    f"project in ({PROJECT_LIST}) AND issuetype in "
    '("Escape Defect", "Support Request") AND "Zendesk Ticket Count" > 0 '
    f'AND created >= "{CREATED_FROM}" AND statusCategory != Done ORDER BY created ASC'
)
JQL_DONE = (
    f"project in ({PROJECT_LIST}) AND issuetype in "
    '("Escape Defect", "Support Request") AND "Zendesk Ticket Count" > 0 '
    f'AND created >= "{CREATED_FROM}" AND statusCategory = Done ORDER BY created ASC'
)


def build_months(start: date, end: date) -> list[dict]:
    months: list[dict] = []
    year, month = start.year, start.month
    while (year, month) <= (end.year, end.month):
        last_day = monthrange(year, month)[1]
        start_d = date(year, month, 1)
        end_d = date(year, month, last_day)
        months.append(
            {
                "id": f"{year:04d}-{month:02d}",
                "label": start_d.strftime("%b %Y"),
                "start": start_d.isoformat(),
                "end": end_d.isoformat(),
                "partial": end < end_d,
            }
        )
        if month == 12:
            year, month = year + 1, 1
        else:
            month += 1
    return months


def set_clock(now: datetime | None = None) -> None:
    global SNAPSHOT, SNAPSHOT_DT, MONTHS, MONTH_BY_ID
    snapshot = now or datetime.now(timezone.utc)
    if snapshot.tzinfo is None:
        snapshot = snapshot.replace(tzinfo=timezone.utc)
    SNAPSHOT_DT = snapshot
    SNAPSHOT = snapshot.date().isoformat()
    MONTHS = build_months(date.fromisoformat(CREATED_FROM), snapshot.date())
    MONTH_BY_ID = {m["id"]: m for m in MONTHS}


set_clock()


def parse_jira_dt(value: str | None) -> datetime | None:
    if not value:
        return None
    s = value
    if len(s) >= 5 and s[-5] in "+-" and s[-4:].isdigit():
        s = s[:-2] + ":" + s[-2:]
    return datetime.fromisoformat(s)


def empty_counts() -> dict:
    return {
        "created": 0,
        "escape_defect": 0,
        "support_request": 0,
        "done": 0,
        "open": 0,
        "zendesk": 0,
    }


def bump(bucket: dict, issue: dict) -> None:
    bucket["created"] += 1
    if issue["type"] == "Escape Defect":
        bucket["escape_defect"] += 1
    else:
        bucket["support_request"] += 1
    if issue["is_done"]:
        bucket["done"] += 1
    else:
        bucket["open"] += 1
    bucket["zendesk"] += issue["zendesk_count"] or 0


def month_for(created: datetime) -> dict:
    mid = created.strftime("%Y-%m")
    return MONTH_BY_ID.get(mid, MONTHS[-1])


def load_issues(paths: list[Path]) -> list[dict]:
    seen: dict[str, dict] = {}
    for path in paths:
        payload = json.loads(path.read_text(encoding="utf-8"))
        for raw in payload.get("issues", []):
            fields = raw.get("fields") or {}
            key = raw["key"]
            project = fields.get("project") or {}
            project_key = project.get("key")
            if project_key not in PROJECT_BY_KEY:
                continue
            meta = PROJECT_BY_KEY[project_key]
            created = parse_jira_dt(fields.get("created"))
            if created is None:
                continue
            if created.date().isoformat() < CREATED_FROM:
                continue
            resolved = parse_jira_dt(fields.get("resolutiondate"))
            status_cat_changed = parse_jira_dt(fields.get("statuscategorychangedate"))
            status = fields.get("status") or {}
            status_cat = ((status.get("statusCategory") or {}).get("name")) or ""
            issuetype = (fields.get("issuetype") or {}).get("name") or ""
            assignee = fields.get("assignee") or {}
            priority = fields.get("priority") or {}
            zd = fields.get("customfield_11201") or 0
            try:
                zd = int(zd)
            except (TypeError, ValueError):
                zd = 0
            month = month_for(created)
            seen[key] = {
                "key": key,
                "url": f"https://securly.atlassian.net/browse/{key}",
                "summary": fields.get("summary") or "",
                "type": issuetype,
                "priority": priority.get("name"),
                "zendesk_count": zd,
                "status": status.get("name") or "",
                "status_category": status_cat,
                "resolution": None,
                "assignee": assignee.get("displayName") or "Unassigned",
                "reporter": "—",
                "project_key": project_key,
                "project_name": meta["name"],
                "project_label": meta["label"],
                "created": created.isoformat(),
                "created_date": created.date().isoformat(),
                "resolved": resolved.isoformat() if resolved else None,
                "resolved_date": resolved.date().isoformat() if resolved else None,
                "statuscategorychangedate": (
                    status_cat_changed.isoformat() if status_cat_changed else None
                ),
                "created_month": {
                    "id": month["id"],
                    "label": month["label"],
                    "start": month["start"],
                    "end": month["end"],
                    "partial": month["partial"],
                },
                "is_done": status_cat == "Done",
            }
    issues = list(seen.values())
    issues.sort(key=lambda i: (i["created"], i["key"]))
    return issues


def looks_like_dashboard(path: Path) -> bool:
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return False
    return isinstance(payload, dict) and "created_issues" in payload


def load_dashboard_issues(path: Path) -> list[dict]:
    payload = json.loads(path.read_text(encoding="utf-8"))
    seen: dict[str, dict] = {}
    for raw in payload.get("created_issues", []):
        created = parse_jira_dt(raw.get("created"))
        if created is None:
            continue
        if created.date().isoformat() < CREATED_FROM:
            continue
        project_key = raw.get("project_key")
        if project_key not in PROJECT_BY_KEY:
            continue
        month = month_for(created)
        issue = dict(raw)
        issue["created_month"] = {
            "id": month["id"],
            "label": month["label"],
            "start": month["start"],
            "end": month["end"],
            "partial": month["partial"],
        }
        seen[issue["key"]] = issue
    issues = list(seen.values())
    issues.sort(key=lambda i: (i["created"], i["key"]))
    return issues


def load_all(paths: list[Path]) -> list[dict]:
    seen: dict[str, dict] = {}
    for path in paths:
        chunk = (
            load_dashboard_issues(path)
            if looks_like_dashboard(path)
            else load_issues([path])
        )
        for issue in chunk:
            seen[issue["key"]] = issue
    issues = list(seen.values())
    issues.sort(key=lambda i: (i["created"], i["key"]))
    return issues


def jira_link(jql: str) -> str:
    return "https://securly.atlassian.net/issues/?jql=" + quote(jql, safe="")


def load_done_at_overlay(path: Path) -> dict[str, dict]:
    if not path.exists():
        return {}
    payload = json.loads(path.read_text(encoding="utf-8"))
    return payload if isinstance(payload, dict) else {}


def apply_done_at_overlay(issues: list[dict], overlay: dict[str, dict]) -> None:
    for issue in issues:
        rec = overlay.get(issue["key"]) or {}
        if rec.get("statuscategorychangedate") and not issue.get("statuscategorychangedate"):
            issue["statuscategorychangedate"] = rec["statuscategorychangedate"]
        if rec.get("resolved") and not issue.get("resolved"):
            issue["resolved"] = rec["resolved"]
            resolved = parse_jira_dt(rec["resolved"])
            issue["resolved_date"] = resolved.date().isoformat() if resolved else issue.get("resolved_date")


def snapshot_done_at(issue: dict) -> datetime | None:
    if not issue.get("is_done"):
        return None
    created = parse_jira_dt(issue.get("created"))
    scc = parse_jira_dt(issue.get("statuscategorychangedate"))
    resolved = parse_jira_dt(issue.get("resolved"))
    if scc and scc <= SNAPSHOT_DT and (created is None or scc >= created):
        return scc
    if resolved and resolved <= SNAPSHOT_DT and (created is None or resolved >= created):
        return resolved
    if resolved and created and resolved >= created:
        return resolved
    return None


def round_days(seconds: float) -> float:
    return round(seconds / 86400, 2)


def attach_time_to_done(issues: list[dict]) -> None:
    for issue in issues:
        done_at = snapshot_done_at(issue)
        created = parse_jira_dt(issue.get("created"))
        issue["done_at"] = done_at.isoformat() if done_at else None
        issue["done_date"] = done_at.date().isoformat() if done_at else None
        if done_at and created:
            issue["time_to_done_days"] = round_days((done_at - created).total_seconds())
        else:
            issue["time_to_done_days"] = None


def avg_days(values: list[float]) -> float | None:
    if not values:
        return None
    return round(sum(values) / len(values), 2)


def window_note() -> str:
    labels = []
    for month in MONTHS:
        label = month["label"]
        if month.get("partial"):
            label += " (partial)"
        labels.append(label)
    joined = ", ".join(labels) if labels else SNAPSHOT
    return f"{joined} through the live Jira refresh."


def fetch_jira_search_pages() -> list[dict]:
    from build_sprint_matrix_report import search_jql_page

    issues: list[dict] = []
    token: str | None = None
    while True:
        page = search_jql_page(JIRA_URL, JQL_CREATED, ISSUE_FIELDS, 100, token)
        issues.extend(page.get("issues") or [])
        token = page.get("nextPageToken")
        if page.get("isLast", not token) or not token:
            break
    return issues


def fetch_jira_issues() -> list[dict]:
    if not os.environ.get("JIRA_EMAIL") or not os.environ.get("JIRA_API_TOKEN"):
        raise RuntimeError("JIRA_EMAIL and JIRA_API_TOKEN are required for a live Jira pull")
    return load_issue_payload({"issues": fetch_jira_search_pages()})


def load_issue_payload(payload: dict) -> list[dict]:
    tmp = ROOT / "reports" / ".jira-live-page.json"
    tmp.parent.mkdir(parents=True, exist_ok=True)
    tmp.write_text(json.dumps(payload), encoding="utf-8")
    try:
        return load_issues([tmp])
    finally:
        if tmp.exists():
            tmp.unlink()


def build_dashboard(issues: list[dict], live: bool = False) -> dict:
    apply_done_at_overlay(issues, load_done_at_overlay(DONE_AT_PATH))
    attach_time_to_done(issues)
    product_kpis = []
    for proj in PROJECTS:
        bucket = empty_counts()
        times: list[float] = []
        for issue in issues:
            if issue["project_key"] == proj["key"]:
                bump(bucket, issue)
                if issue.get("time_to_done_days") is not None:
                    times.append(issue["time_to_done_days"])
        product_kpis.append({
            **proj,
            **bucket,
            "done_pct": round(100 * bucket["done"] / bucket["created"]) if bucket["created"] else 0,
            "not_done_pct": round(100 * bucket["open"] / bucket["created"]) if bucket["created"] else 0,
            "avg_days_to_done": avg_days(times),
            "done_with_time": len(times),
        })

    monthly = []
    for month in MONTHS:
        by_project = {p["key"]: empty_counts() for p in PROJECTS}
        totals = empty_counts()
        for issue in issues:
            if issue["created_month"]["id"] != month["id"]:
                continue
            bump(by_project[issue["project_key"]], issue)
            bump(totals, issue)
        monthly.append({**month, "by_project": by_project, "totals": totals})

    kpis = empty_counts()
    all_times: list[float] = []
    for issue in issues:
        bump(kpis, issue)
        if issue.get("time_to_done_days") is not None:
            all_times.append(issue["time_to_done_days"])
    avg_to_done = avg_days(all_times)

    product_kpis.sort(key=lambda p: p["label"].lower())
    ranked = sorted(product_kpis, key=lambda p: (-p["created"], p["label"]))
    top = [p for p in ranked if p["created"] > 0][:5]
    zero = sorted(p["label"] for p in product_kpis if p["created"] == 0)
    top_txt = ", ".join(f"{p['label']} {p['created']}" for p in top)
    headline = (
        f"{kpis['created']} Zendesk-linked tickets created since {CREATED_FROM_LABEL} "
        f"({kpis['escape_defect']} Escape Defect, {kpis['support_request']} Support Request). "
        f"{kpis['done']} Done (statusCategory = Done) vs {kpis['open']} not Done "
        f"(statusCategory != Done). "
        + (
            f"Average time from created to Done is {avg_to_done:.1f} days "
            f"across {len(all_times)} of {kpis['done']} Done tickets. "
            if avg_to_done is not None else
            "No Done tickets have a usable created-to-Done timestamp. "
        )
        + f"Highest intake: {top_txt}."
    )
    if zero:
        headline += f" No matching tickets yet: {', '.join(zero)}."

    return {
        "title": TITLE,
        "generated_at": SNAPSHOT_DT.strftime("%Y-%m-%dT%H:%M:%SZ"),
        "snapshot_date": SNAPSHOT,
        "live": live,
        "source": JIRA_URL,
        "projects": PROJECTS,
        "filters": {
            "issue_types": ["Escape Defect", "Support Request"],
            "zendesk_ticket_count": "> 0",
            "created_from": CREATED_FROM,
            "created_from_label": CREATED_FROM_LABEL,
            "grain": "month",
        },
        "jql": {
            "created": JQL_CREATED,
            "created_open": JQL_OPEN,
            "created_done": JQL_DONE,
        },
        "links": {
            "created": jira_link(JQL_CREATED),
            "created_open": jira_link(JQL_OPEN),
            "created_done": jira_link(JQL_DONE),
        },
        "kpis": {
            "created": kpis["created"],
            "created_escape_defect": kpis["escape_defect"],
            "created_support_request": kpis["support_request"],
            "created_done": kpis["done"],
            "created_open": kpis["open"],
            "done_pct": round(100 * kpis["done"] / kpis["created"]) if kpis["created"] else 0,
            "not_done_pct": round(100 * kpis["open"] / kpis["created"]) if kpis["created"] else 0,
            "avg_days_to_done": avg_to_done,
            "done_with_time": len(all_times),
        },
        "product_kpis": product_kpis,
        "monthly": monthly,
        "created_issues": issues,
        "headline": headline,
        "notes": {
            "scope": (
                "Includes AIChat, Aware, Case Manager (RESP), Comm, DD, DE, DevOps, Filter, "
                "Flex, Home, MDM Class, On-Call (PRODUCT24), PageScan, and Pass. "
                "Products with 0 had no Escape Defect or Support Request with Zendesk "
                f"Ticket Count > 0 since {CREATED_FROM_LABEL}. Done vs not Done uses Jira "
                "statusCategory = Done versus statusCategory != Done. Average time to Done "
                "is created → statuscategorychangedate (when the ticket entered Done), "
                "falling back to resolutiondate if the category-change date is missing or "
                "after the snapshot (for example if the ticket was later reopened)."
            ),
            "window": window_note(),
        },
    }


def write_dashboard(data: dict) -> None:
    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text(json.dumps(data, indent=2) + "\n", encoding="utf-8")
    print(f"wrote {OUT} ({len(data.get('created_issues') or [])} issues)")
    for p in data["product_kpis"]:
        print(
            f"  {p['label']:16} created={p['created']:3} open={p['open']:3} "
            f"done={p['done']:3} avg_to_done={p['avg_days_to_done'] or '—'} "
            f"zd={p['zendesk']:3}"
        )


def live_dashboard() -> dict:
    set_clock()
    dump = ROOT / "reports" / "jira-live-issues.json"
    try:
        issues = fetch_jira_issues()
        print(f"live Jira pull: {len(issues)} issues", flush=True)
        return build_dashboard(issues, live=True)
    except Exception as exc:
        print(f"live Jira pull unavailable ({exc}); using local snapshot", flush=True)
    if dump.exists():
        return build_dashboard(load_all([dump]), live=False)
    if OUT.exists():
        return build_dashboard(load_all([OUT]), live=False)
    raise RuntimeError(
        "No Jira credentials and no local snapshot. Set JIRA_EMAIL and "
        "JIRA_API_TOKEN, or provide reports/jira-live-issues.json."
    )


def main(paths: list[str]) -> None:
    set_clock()
    issues = load_all([Path(p) for p in paths])
    data = build_dashboard(issues, live=False)
    write_dashboard(data)


if __name__ == "__main__":
    import sys

    if len(sys.argv) == 2 and sys.argv[1] in {"--live", "live"}:
        write_dashboard(live_dashboard())
    elif len(sys.argv) < 2:
        raise SystemExit(
            "usage: assemble_zendesk_dashboard.py <jira-page.json> [...]"
            " | assemble_zendesk_dashboard.py --live"
        )
    else:
        main(sys.argv[1:])
