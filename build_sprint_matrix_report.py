"""
Fetch Jira sprint-scope metrics per product/month cell and write JSON + Markdown.

Metrics (per methodology note in output):
  - planned_scope_issues: issues assigned to the sprint(s) in the cell (current Jira
    snapshot for closed sprints = final sprint scope).
  - completed_issues: subset in status category Done.
  - completion_rate_pct: completed / planned_scope_issues (reference).
  - original_estimate_hours_*: sums of Jira Original estimate (timeoriginalestimate → hours);
    primary track: original_estimate_hours_completion_pct = done hours / planned hours.
  - story_points_*: reference only (customfield_10005 when present).

Requires env: JIRA_EMAIL, JIRA_API_TOKEN, JIRA_URL (e.g. https://securly.atlassian.net)
Optional: JIRA_STORY_POINTS_FIELD (default customfield_10005)

Usage:
  python build_sprint_matrix_report.py
"""
from __future__ import annotations

import base64
import json
import os
import sys
import time
import urllib.error
import urllib.parse
import urllib.request
from typing import Any

STORY_POINTS_FIELD = os.environ.get("JIRA_STORY_POINTS_FIELD", "customfield_10005")

# Normalized matrix: product label, calendar month, Jira project key, sprint name(s)
MATRIX: list[dict[str, Any]] = [
    {"product": "product_home", "month": "2026-01", "jira_project": "HOME", "sprints": ["sprint-Home-Arthur"]},
    {"product": "product_home", "month": "2026-01", "jira_project": "HOME", "sprints": ["sprint-Home-Bertha"]},
    {"product": "product_home", "month": "2026-02", "jira_project": "HOME", "sprints": ["sprint-Home-Cristobal"]},
    {"product": "product_home", "month": "2026-02", "jira_project": "HOME", "sprints": ["sprint-Home-Dolly"]},
    {"product": "product_home", "month": "2026-03", "jira_project": "HOME", "sprints": ["sprint-Home-Edouard"]},
    {"product": "product_home", "month": "2026-03", "jira_project": "HOME", "sprints": ["sprint-Home-Fay"]},
    {"product": "product_home", "month": "2026-01", "jira_project": "HOME", "sprints": ["sprint-Aware-Arthur"]},
    # product_MDM_CLASSROOM
    {"product": "product_MDM_CLASSROOM", "month": "2026-01", "jira_project": "MDMCLASS", "sprints": ["sprint-MDMCL-Arthur"]},
    {"product": "product_MDM_CLASSROOM", "month": "2026-01", "jira_project": "MDMCLASS", "sprints": ["sprint-MDMCL-Bertha"]},
    {"product": "product_MDM_CLASSROOM", "month": "2026-02", "jira_project": "MDMCLASS", "sprints": ["sprint-MDMCL-Cristobal"]},
    {"product": "product_MDM_CLASSROOM", "month": "2026-02", "jira_project": "MDMCLASS", "sprints": ["sprint-MDMCL-Dolly"]},
    {"product": "product_MDM_CLASSROOM", "month": "2026-03", "jira_project": "MDMCLASS", "sprints": ["sprint-MDMCL-Edouard"]},
    {"product": "product_MDM_CLASSROOM", "month": "2026-03", "jira_project": "MDMCLASS", "sprints": ["sprint-MDMCL-Fay"]},
    # product_oncall (Jira name product_oncall → key PRODUCT24)
    {"product": "product_oncall", "month": "2026-01", "jira_project": "PRODUCT24", "sprints": ["sprint-Arthur"]},
    {"product": "product_oncall", "month": "2026-01", "jira_project": "PRODUCT24", "sprints": ["sprint-Bertha"]},
    {"product": "product_oncall", "month": "2026-02", "jira_project": "PRODUCT24", "sprints": ["sprint-Cristobal"]},
    {"product": "product_oncall", "month": "2026-02", "jira_project": "PRODUCT24", "sprints": ["sprint-Dolly"]},
    {"product": "product_oncall", "month": "2026-03", "jira_project": "PRODUCT24", "sprints": ["sprint-Cases-Edouard"]},
    {"product": "product_oncall", "month": "2026-03", "jira_project": "PRODUCT24", "sprints": ["sprint-Cases-Fay"]},
    # product_RESPOND (key RESP)
    {"product": "product_RESPOND", "month": "2026-01", "jira_project": "RESP", "sprints": ["sprint-Arthur"]},
    {"product": "product_RESPOND", "month": "2026-01", "jira_project": "RESP", "sprints": ["sprint-Bertha"]},
    {"product": "product_RESPOND", "month": "2026-02", "jira_project": "RESP", "sprints": ["sprint-Cristobal"]},
    {"product": "product_RESPOND", "month": "2026-02", "jira_project": "RESP", "sprints": ["sprint-Dolly"]},
    {"product": "product_RESPOND", "month": "2026-03", "jira_project": "RESP", "sprints": ["sprint-Cases-Edouard"]},
    {"product": "product_RESPOND", "month": "2026-03", "jira_project": "RESP", "sprints": ["sprint-Cases-Fay"]},
    # product_FILTER
    {"product": "product_FILTER", "month": "2026-01", "jira_project": "FILTER", "sprints": ["sprint-Arthur"]},
    {"product": "product_FILTER", "month": "2026-01", "jira_project": "FILTER", "sprints": ["sprint-Bertha"]},
    {"product": "product_FILTER", "month": "2026-02", "jira_project": "FILTER", "sprints": ["sprint-Cristobal"]},
    {"product": "product_FILTER", "month": "2026-02", "jira_project": "FILTER", "sprints": ["sprint-Dolly"]},
    {"product": "product_FILTER", "month": "2026-03", "jira_project": "FILTER", "sprints": ["sprint-Edouard"]},
    {"product": "product_FILTER", "month": "2026-03", "jira_project": "FILTER", "sprints": ["sprint-Fay"]},
    # PASS
    {"product": "PASS", "month": "2026-01", "jira_project": "PASS", "sprints": ["PASS Sprint 40"]},
    {"product": "PASS", "month": "2026-01", "jira_project": "PASS", "sprints": ["PASS Sprint 41"]},
    {"product": "PASS", "month": "2026-02", "jira_project": "PASS", "sprints": ["PASS Sprint 42"]},
    {"product": "PASS", "month": "2026-02", "jira_project": "PASS", "sprints": ["PASS Sprint 43"]},
    {"product": "PASS", "month": "2026-03", "jira_project": "PASS", "sprints": ["PASS Sprint 44"]},
    {"product": "PASS", "month": "2026-03", "jira_project": "PASS", "sprints": ["PASS Sprint 45"]},
    # FLEX & COM — Jira project "Flex" (key FLEX)
    {"product": "FLEX & COM", "month": "2026-01", "jira_project": "FLEX", "sprints": ["FLEX/COM Sprint 128"]},
    {"product": "FLEX & COM", "month": "2026-01", "jira_project": "FLEX", "sprints": ["FLEX/COM Sprint 129"]},
    {"product": "FLEX & COM", "month": "2026-02", "jira_project": "FLEX", "sprints": ["FLEX/COM Sprint 130"]},
    {"product": "FLEX & COM", "month": "2026-02", "jira_project": "FLEX", "sprints": ["FLEX/COM Sprint 131"]},
    {"product": "FLEX & COM", "month": "2026-03", "jira_project": "FLEX", "sprints": ["FLEX/COM Sprint 132"]},
    {"product": "FLEX & COM", "month": "2026-03", "jira_project": "FLEX", "sprints": ["FLEX/COM Sprint 133"]},
    # product_aware
    {"product": "product_aware", "month": "2026-01", "jira_project": "AWARE", "sprints": ["sprint-Aware-Bertha"]},
    {"product": "product_aware", "month": "2026-02", "jira_project": "AWARE", "sprints": ["sprint-Aware-Cristobal"]},
    {"product": "product_aware", "month": "2026-02", "jira_project": "AWARE", "sprints": ["sprint-Aware-Dolly"]},
    {"product": "product_aware", "month": "2026-03", "jira_project": "AWARE", "sprints": ["sprint-Aware-Edouard"]},
    {"product": "product_aware", "month": "2026-03", "jira_project": "AWARE", "sprints": ["sprint-Aware-Fay"]},
    # AIChat — combined sprints per month
    {"product": "AIChat", "month": "2026-01", "jira_project": "AICHAT", "sprints": ["sprint-AIChat-Zephyr", "sprint-AIChat-Arthur"]},
    {"product": "AIChat", "month": "2026-02", "jira_project": "AICHAT", "sprints": ["sprint-AIChat-Bertha", "sprint-AIChat-38", "sprint-AIChat-39"]},
    {
        "product": "AIChat",
        "month": "2026-03",
        "jira_project": "AICHAT",
        "sprints": [
            "sprint-AIChat-41",
            "sprint-AIChat-42",
            "sprint-AIChat-43",
            "sprint-AIChat-44",
            "sprint-AIChat-45",
        ],
    },
    # Platform
    {"product": "Platform", "month": "2026-01", "jira_project": "PLATFORM", "sprints": ["sprint-Platform-Arthur", "sprint-Platform-Bertha"]},
    {"product": "Platform", "month": "2026-02", "jira_project": "PLATFORM", "sprints": ["sprint-Platform-Cristobal", "sprint-Platform-Dolly"]},
    {"product": "Platform", "month": "2026-03", "jira_project": "PLATFORM", "sprints": ["sprint-Platform-Edouard", "sprint-Platform-Fay"]},
]


def jql_for_cell(project: str, sprints: list[str]) -> str:
    quoted = ", ".join(json.dumps(s) for s in sprints)
    return f"project = {project} AND sprint in ({quoted})"


def auth_header() -> str:
    email = os.environ["JIRA_EMAIL"]
    token = os.environ["JIRA_API_TOKEN"]
    creds = base64.b64encode(f"{email}:{token}".encode()).decode()
    return f"Basic {creds}"


def search_jql_page(
    base: str,
    jql: str,
    fields: list[str],
    max_results: int,
    next_page_token: str | None,
) -> dict[str, Any]:
    """Jira Cloud: GET /rest/api/3/search is deprecated (410); use POST /search/jql."""
    url = f"{base}/rest/api/3/search/jql"
    body: dict[str, Any] = {
        "jql": jql,
        "maxResults": max_results,
        "fields": fields,
    }
    if next_page_token:
        body["nextPageToken"] = next_page_token
    payload = json.dumps(body).encode("utf-8")
    req = urllib.request.Request(
        url,
        data=payload,
        method="POST",
        headers={
            "Accept": "application/json",
            "Content-Type": "application/json",
            "Authorization": auth_header(),
        },
    )
    try:
        with urllib.request.urlopen(req, timeout=120) as resp:
            return json.load(resp)
    except urllib.error.HTTPError as e:
        body = e.read().decode(errors="replace")
        raise RuntimeError(f"Jira HTTP {e.code}: {body[:2000]}") from e


def issue_done(issue: dict[str, Any]) -> bool:
    cat = (issue.get("fields") or {}).get("status", {}).get("statusCategory") or {}
    return (cat.get("key") or "") == "done"


def story_points(issue: dict[str, Any]) -> float | None:
    raw = (issue.get("fields") or {}).get(STORY_POINTS_FIELD)
    if raw is None:
        return None
    try:
        return float(raw)
    except (TypeError, ValueError):
        return None


def original_estimate_hours(issue: dict[str, Any]) -> float:
    """Jira timeoriginalestimate is seconds; convert to hours. Missing → 0."""
    raw = (issue.get("fields") or {}).get("timeoriginalestimate")
    if raw is None:
        return 0.0
    try:
        return float(raw) / 3600.0
    except (TypeError, ValueError):
        return 0.0


def timespent_hours(issue: dict[str, Any]) -> float:
    """Jira timespent (work logged) is seconds; convert to hours."""
    raw = (issue.get("fields") or {}).get("timespent")
    if raw is None:
        return 0.0
    try:
        return float(raw) / 3600.0
    except (TypeError, ValueError):
        return 0.0


def aggregate_cell(base: str, project: str, sprints: list[str]) -> dict[str, Any]:
    jql = jql_for_cell(project, sprints)
    page_size = 100
    next_token: str | None = None
    planned = 0
    completed = 0
    sp_planned = 0.0
    sp_completed = 0.0
    sp_missing = 0
    est_planned = 0.0
    est_done = 0.0
    time_spent_h = 0.0
    issues_without_original_estimate = 0
    type_counts: dict[str, int] = {}
    field_ids = [
        "key",
        "status",
        "issuetype",
        STORY_POINTS_FIELD,
        "timeoriginalestimate",
        "timespent",
    ]

    while True:
        data = search_jql_page(base, jql, field_ids, page_size, next_token)
        issues = data.get("issues") or []
        for issue in issues:
            planned += 1
            fld = issue.get("fields") or {}
            it = (fld.get("issuetype") or {}).get("name") or "Unknown"
            type_counts[it] = type_counts.get(it, 0) + 1
            if issue_done(issue):
                completed += 1
            sp = story_points(issue)
            if sp is not None:
                sp_planned += sp
                if issue_done(issue):
                    sp_completed += sp
            else:
                sp_missing += 1
            if fld.get("timeoriginalestimate") is None:
                issues_without_original_estimate += 1
            eh = original_estimate_hours(issue)
            est_planned += eh
            if issue_done(issue):
                est_done += eh
            time_spent_h += timespent_hours(issue)
        if data.get("isLast") or not issues:
            break
        next_token = data.get("nextPageToken")
        if not next_token:
            break
        time.sleep(0.15)

    pct = round(100.0 * completed / planned, 1) if planned else 0.0
    sp_pct = round(100.0 * sp_completed / sp_planned, 1) if sp_planned else None
    est_pct = round(100.0 * est_done / est_planned, 1) if est_planned > 0 else None
    return {
        "jql": jql,
        "planned_scope_issues": planned,
        "completed_issues": completed,
        "completion_rate_pct": pct,
        "original_estimate_hours_planned_sum": round(est_planned, 2),
        "original_estimate_hours_done_sum": round(est_done, 2),
        "original_estimate_hours_completion_pct": est_pct,
        "issues_without_original_estimate": issues_without_original_estimate,
        "timespent_hours_sum": round(time_spent_h, 2),
        "story_points_field": STORY_POINTS_FIELD,
        "story_points_planned_sum": round(sp_planned, 2),
        "story_points_completed_sum": round(sp_completed, 2),
        "story_points_completion_pct": sp_pct,
        "issues_without_story_points": sp_missing,
        "issue_type_counts": dict(sorted(type_counts.items(), key=lambda x: (-x[1], x[0]))),
    }


def build_markdown(rows: list[dict[str, Any]]) -> str:
    lines = [
        "# Sprint matrix — planned scope vs completed (Jira)",
        "",
        "**Generated:** see JSON `generated_at`.",
        "",
        "## Methodology",
        "",
        "- **Planned (scope):** issues matching `project = X AND sprint in (...)` for the named sprint(s). "
        "For completed sprints, this matches Jira’s sprint assignment (final scope including items added mid-sprint).",
        "- **Completed:** issues whose **status category** is **Done** (includes Closed, Done, Closed without action, etc.).",
        "- **Primary track metric — Original estimate (hours):** sum of Jira **Original estimate** "
        "(`timeoriginalestimate`, seconds → hours) across all in-scope issues vs sum on **Done** issues. "
        "Issues with no estimate contribute **0** to both sums. **Est. done %** = done hours ÷ planned hours.",
        "- **Story points (reference only):** sum of `customfield_10005` where populated — not used as the delivery track bar.",
        "- **PHP / Go migration (GM):** not a separate row; work is executed in other teams’ sprints. "
        "Issues filed under **FILTER**, **RESP**, etc. appear in those product queries; use `project = GM` in Jira for migration-only backlog.",
        "",
        "## Project key mapping",
        "",
        "| Report label | Jira key | Jira project name |",
        "|--------------|----------|-------------------|",
        "| AIChat | AICHAT | Product_AIChat |",
        "| FLEX & COM | FLEX | Flex |",
        "| PASS | PASS | Pass |",
        "| Platform | PLATFORM | Platform |",
        "| product_aware | AWARE | product_AWARE |",
        "| product_FILTER | FILTER | product_FILTER |",
        "| product_home | HOME | product_HOME |",
        "| product_MDM_CLASSROOM | MDMCLASS | product_MDM_CLASSROOM |",
        "| product_oncall | PRODUCT24 | product_oncall |",
        "| product_RESPOND | RESP | product_RESPOND |",
        "",
        "## Matrix",
        "",
        "| Product | Month | Sprint(s) | Scope | Done | Issue done % | Est. h planned | Est. h done | Est. done % | SP ref |",
        "|---------|-------|-------------|------:|-----:|-------------:|---------------:|------------:|------------:|--------|",
    ]
    for r in rows:
        m = r["month"]
        agg = r["metrics"]
        if agg.get("error"):
            lines.append(
                "| {product} | {month} | {sprints} | *error* | — | — | — | — | — | — |".format(
                    product=r["product"],
                    month=m,
                    sprints=", ".join(r["sprints"]),
                )
            )
            continue
        sp_pct = agg.get("story_points_completion_pct")
        sp_pct_s = "" if sp_pct is None else f"{sp_pct:.1f}"
        est_pct = agg.get("original_estimate_hours_completion_pct")
        est_pct_s = "" if est_pct is None else f"{est_pct:.1f}"
        lines.append(
            "| {product} | {month} | {sprints} | {scope} | {done} | {ipct}% | {eph} | {edh} | {epct} | {sp}/{spd} ({sppct}) |".format(
                product=r["product"],
                month=m,
                sprints=", ".join(r["sprints"]),
                scope=agg.get("planned_scope_issues", ""),
                done=agg.get("completed_issues", ""),
                ipct=agg.get("completion_rate_pct", ""),
                eph=agg.get("original_estimate_hours_planned_sum", ""),
                edh=agg.get("original_estimate_hours_done_sum", ""),
                epct=est_pct_s,
                sp=agg.get("story_points_planned_sum", ""),
                spd=agg.get("story_points_completed_sum", ""),
                sppct=sp_pct_s,
            )
        )
    lines.append("")
    lines.append("## JQL index")
    lines.append("")
    for r in rows:
        jq = r["metrics"].get("jql", "")
        lines.append(f"- **{r['product']}** {r['month']} — `{jq}`")
    err_rows = [r for r in rows if r["metrics"].get("error")]
    if err_rows:
        lines.append("")
        lines.append("## Cells with fetch errors")
        lines.append("")
        for r in err_rows:
            lines.append(f"- **{r['product']}** {r['month']}: {r['metrics'].get('error')}")
    lines.append("")
    return "\n".join(lines)


def main() -> None:
    base = os.environ.get("JIRA_URL", "").rstrip("/")
    if not base:
        print("Set JIRA_URL, JIRA_EMAIL, JIRA_API_TOKEN", file=sys.stderr)
        sys.exit(1)
    out_dir = os.path.dirname(os.path.abspath(__file__))
    rows: list[dict[str, Any]] = []
    errors: list[str] = []

    for cell in MATRIX:
        product = cell["product"]
        month = cell["month"]
        proj = cell["jira_project"]
        sprints = cell["sprints"]
        label = f"{product} {month} {sprints}"
        try:
            metrics = aggregate_cell(base, proj, sprints)
        except Exception as e:
            errors.append(f"{label}: {e}")
            metrics = {
                "jql": jql_for_cell(proj, sprints),
                "error": str(e),
                "planned_scope_issues": None,
                "completed_issues": None,
                "completion_rate_pct": None,
                "original_estimate_hours_planned_sum": None,
                "original_estimate_hours_done_sum": None,
                "original_estimate_hours_completion_pct": None,
                "timespent_hours_sum": None,
                "story_points_planned_sum": None,
                "story_points_completed_sum": None,
                "story_points_completion_pct": None,
            }
        rows.append(
            {
                "product": product,
                "month": month,
                "jira_project": proj,
                "sprints": sprints,
                "metrics": metrics,
            }
        )
        print(f"OK {label} -> {metrics.get('planned_scope_issues')} issues", flush=True)

    import datetime

    report = {
        "generated_at": datetime.datetime.now(datetime.timezone.utc).isoformat(),
        "jira_base": base,
        "methodology": {
            "planned": "Issues in sprint per JQL (see each cell metrics.jql).",
            "completed": "statusCategory.key == done",
            "primary_track_metric": (
                "original_estimate_hours: sum of timeoriginalestimate (hours) on scope vs on Done; "
                "missing estimate = 0."
            ),
            "story_points_field": STORY_POINTS_FIELD,
            "story_points_note": "Reference only; not the primary track bar.",
        },
        "rows": rows,
        "errors": errors,
    }
    json_path = os.path.join(out_dir, "sprint_matrix_report.json")
    md_path = os.path.join(out_dir, "sprint_matrix_report.md")
    with open(json_path, "w", encoding="utf-8") as f:
        json.dump(report, f, indent=2)
    with open(md_path, "w", encoding="utf-8") as f:
        f.write(build_markdown(rows))
    print(f"Wrote {json_path} and {md_path}")
    if errors:
        print("Errors:", file=sys.stderr)
        for e in errors:
            print(e, file=sys.stderr)
        sys.exit(2)


if __name__ == "__main__":
    main()
