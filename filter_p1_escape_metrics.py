"""
FILTER — P1 Escape Defect metrics for PM tracking.

1) **WIP cap:** No more than MAX_CONCURRENT (default 3) Escape Defects with priority P1
   in a **not-Done** state at any time. Script reports current count + compliance.

2) **Monthly inflow:** Count of Escape Defect + P1 **created** in each calendar month
   (default: current calendar year). Does not replace the WIP cap — tracks arrival rate.

Outputs:
  filter_p1_escape_metrics.json
  filter_p1_escape_metrics.md

Env: JIRA_URL, JIRA_EMAIL, JIRA_API_TOKEN
Optional: FILTER_P1_MAX_CONCURRENT=3, FILTER_METRIC_YEAR=2026
"""
from __future__ import annotations

import base64
import datetime
import json
import os
import sys
import time
import urllib.error
import urllib.request
from typing import Any

ROOT = __file__.rsplit(os.sep, 1)[0]

MAX_CONCURRENT = int(os.environ.get("FILTER_P1_MAX_CONCURRENT", "3"))
YEAR = int(os.environ.get("FILTER_METRIC_YEAR", str(datetime.date.today().year)))


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
    url = f"{base}/rest/api/3/search/jql"
    body: dict[str, Any] = {
        "jql": jql,
        "maxResults": max_results,
        "fields": fields,
    }
    if next_page_token:
        body["nextPageToken"] = next_page_token
    req = urllib.request.Request(
        url,
        data=json.dumps(body).encode("utf-8"),
        method="POST",
        headers={
            "Accept": "application/json",
            "Content-Type": "application/json",
            "Authorization": auth_header(),
        },
    )
    with urllib.request.urlopen(req, timeout=120) as resp:
        return json.load(resp)


def fetch_all_issues(base: str, jql: str, fields: list[str]) -> list[dict[str, Any]]:
    out: list[dict[str, Any]] = []
    tok = None
    while True:
        data = search_jql_page(base, jql, fields, 100, tok)
        out.extend(data.get("issues") or [])
        if data.get("isLast"):
            break
        tok = data.get("nextPageToken")
        if not tok:
            break
        time.sleep(0.12)
    return out


def main() -> None:
    base = os.environ.get("JIRA_URL", "").rstrip("/")
    if not base:
        print("Set JIRA_URL, JIRA_EMAIL, JIRA_API_TOKEN", file=sys.stderr)
        sys.exit(1)

    # Current concurrent (not Done) P1 Escape Defects on FILTER
    jql_wip = (
        'project = FILTER AND issuetype = "Escape Defect" AND priority = P1 '
        "AND statusCategory != Done"
    )
    wip_issues = fetch_all_issues(
        base, jql_wip, ["key", "summary", "status", "priority", "created", "updated"]
    )
    wip_count = len(wip_issues)
    compliant = wip_count <= MAX_CONCURRENT

    monthly_opened: list[dict[str, Any]] = []
    for month in range(1, 13):
        start = datetime.date(YEAR, month, 1)
        if month == 12:
            end = datetime.date(YEAR, 12, 31)
        else:
            end = datetime.date(YEAR, month + 1, 1) - datetime.timedelta(days=1)
        jql_m = (
            f'project = FILTER AND issuetype = "Escape Defect" AND priority = P1 '
            f"AND created >= {start.isoformat()} AND created <= {end.isoformat()}"
        )
        opened = fetch_all_issues(base, jql_m, ["key"])
        monthly_opened.append(
            {
                "month": month,
                "label": start.strftime("%b %Y"),
                "created_start": start.isoformat(),
                "created_end": end.isoformat(),
                "p1_escape_defects_opened": len(opened),
            }
        )

    report: dict[str, Any] = {
        "generated_at": datetime.datetime.now(datetime.timezone.utc).isoformat(),
        "jira_base": base,
        "policy": {
            "project": "FILTER",
            "issue_type": "Escape Defect",
            "priority": "P1",
            "max_concurrent_not_done": MAX_CONCURRENT,
            "wip_jql": jql_wip,
        },
        "wip_compliance": {
            "current_count": wip_count,
            "max_allowed": MAX_CONCURRENT,
            "compliant": compliant,
            "status": "PASS" if compliant else "FAIL — reduce WIP or raise limit",
        },
        "current_p1_escape_defects_open": [
            {
                "key": i["key"],
                "summary": (i.get("fields") or {}).get("summary"),
                "status": ((i.get("fields") or {}).get("status") or {}).get("name"),
            }
            for i in wip_issues
        ],
        "monthly_opened_in_year": monthly_opened,
    }

    md = build_markdown(report)
    json_path = os.path.join(ROOT, "filter_p1_escape_metrics.json")
    md_path = os.path.join(ROOT, "filter_p1_escape_metrics.md")
    with open(json_path, "w", encoding="utf-8") as f:
        json.dump(report, f, indent=2)
    with open(md_path, "w", encoding="utf-8") as f:
        f.write(md)
    print(f"Wrote {json_path}")
    print(f"Wrote {md_path}")
    print(f"WIP: {wip_count}/{MAX_CONCURRENT} — {'OK' if compliant else 'OVER LIMIT'}")


def build_markdown(r: dict[str, Any]) -> str:
    p = r["policy"]
    w = r["wip_compliance"]
    lines = [
        "# FILTER — P1 Escape Defect metrics",
        "",
        "## Metric definitions (PM)",
        "",
        "| Metric | Definition |",
        "|--------|------------|",
        "| **P1 Escape WIP** | Count of issues: project FILTER, type **Escape Defect**, priority **P1**, **status category ≠ Done** (any active state). |",
        "| **WIP cap** | Target: **≤ " + str(p["max_concurrent_not_done"]) + "** at any time. Breach if count exceeds cap until triaged. |",
        "| **Monthly opened** | Count of **same** issue type + priority with **created** date in that calendar month (inflow). |",
        "",
        f"**Snapshot:** {r.get('generated_at', '')}",
        "",
        "## WIP cap check",
        "",
        f"- **Current open P1 Escape Defects:** {w['current_count']}",
        f"- **Limit:** {w['max_allowed']}",
        f"- **Result:** **{w['status']}**",
        "",
    ]
    if r.get("current_p1_escape_defects_open"):
        lines.append("| Key | Status | Summary |")
        lines.append("|-----|--------|---------|")
        for row in r["current_p1_escape_defects_open"]:
            sm = (row.get("summary") or "").replace("|", "\\|")[:80]
            lines.append(f"| {row.get('key')} | {row.get('status')} | {sm} |")
        lines.append("")
    else:
        lines.append("_No open P1 Escape Defects (WIP = 0)._")
        lines.append("")

    lines.append(f"## Monthly inflow ({YEAR}) — P1 Escape Defects created")
    lines.append("")
    lines.append("| Month | Opened (created in month) |")
    lines.append("|-------|----------------------------:|")
    for m in r.get("monthly_opened_in_year") or []:
        lines.append(f"| {m['label']} | {m['p1_escape_defects_opened']} |")
    lines.append("")
    lines.append("## JQL reference")
    lines.append("")
    lines.append("**WIP (concurrent):**")
    lines.append("```")
    lines.append(p["wip_jql"])
    lines.append("```")
    lines.append("")
    return "\n".join(lines)


if __name__ == "__main__":
    main()
