"""
FILTER — P1 Escape Defects that were **concurrently open** (not Done) as of a calendar date.

**Current WIP** (your dashboards): `statusCategory != Done` — a *now* snapshot.

**Point-in-time** (this script): Jira Cloud can express “status category was not Done on date D”
using the historical `WAS` / `ON` operators on `statusCategory` (same meaning as WIP, at end of day).

Env:
  JIRA_URL, JIRA_EMAIL, JIRA_API_TOKEN
  FILTER_P1_AS_OF_DATE=2026-03-31   (ISO date; or pass as first CLI arg)

Optional:
  FILTER_P1_AS_OF_MODE=statusCategory   (default) | resolution
    - statusCategory: aligns with `statusCategory != Done` (recommended).
    - resolution: fallback if historical statusCategory JQL is rejected — uses
      created <= D and (unresolved OR resolved after D). May disagree with Done
      workflows that clear resolution differently.

Outputs:
  filter_p1_escape_as_of.json
  filter_p1_escape_as_of.md
"""
from __future__ import annotations

import datetime
import json
import os
import sys

from filter_p1_escape_metrics import fetch_all_issues

ROOT = os.path.dirname(os.path.abspath(__file__))


def _parse_date(s: str) -> datetime.date:
    s = s.strip()
    return datetime.date.fromisoformat(s)


def build_jql(as_of: datetime.date, mode: str) -> str:
    d = as_of.isoformat()
    base = (
        f'project = FILTER AND issuetype = "Escape Defect" AND priority = P1 '
        f'AND created <= "{d}"'
    )
    if mode == "statusCategory":
        # Jira Cloud: historical status category (same idea as statusCategory != Done).
        # If this errors, try: statusCategory in ("To Do", "In Progress") on "YYYY-MM-DD"
        return f'{base} AND statusCategory was not in ("Done") on "{d}"'
    if mode == "resolution":
        return (
            f"{base} AND (resolution is EMPTY OR resolutiondate > \"{d}\")"
        )
    raise ValueError(f"Unknown FILTER_P1_AS_OF_MODE: {mode!r}")


def main() -> None:
    base = os.environ.get("JIRA_URL", "").rstrip("/")
    if not base:
        print("Set JIRA_URL, JIRA_EMAIL, JIRA_API_TOKEN", file=sys.stderr)
        sys.exit(1)

    raw = (os.environ.get("FILTER_P1_AS_OF_DATE") or "").strip()
    if not raw and len(sys.argv) >= 2:
        raw = sys.argv[1].strip()
    if not raw:
        print(
            "Set FILTER_P1_AS_OF_DATE=YYYY-MM-DD or pass the date as first argument.",
            file=sys.stderr,
        )
        sys.exit(1)

    as_of = _parse_date(raw)
    mode = os.environ.get("FILTER_P1_AS_OF_MODE", "statusCategory").strip().lower()
    if mode not in ("statuscategory", "resolution"):
        print("FILTER_P1_AS_OF_MODE must be statusCategory or resolution", file=sys.stderr)
        sys.exit(1)
    if mode == "statuscategory":
        mode = "statusCategory"

    jql = build_jql(as_of, mode)
    issues = fetch_all_issues(
        base,
        jql,
        ["key", "summary", "status", "priority", "created", "resolutiondate"],
    )

    report = {
        "generated_at": datetime.datetime.now(datetime.timezone.utc).isoformat(),
        "jira_base": base,
        "as_of_date": as_of.isoformat(),
        "mode": mode,
        "jql": jql,
        "count": len(issues),
        "issues": [
            {
                "key": i["key"],
                "summary": (i.get("fields") or {}).get("summary"),
                "status": ((i.get("fields") or {}).get("status") or {}).get("name"),
                "created": (i.get("fields") or {}).get("created"),
                "resolutiondate": (i.get("fields") or {}).get("resolutiondate"),
            }
            for i in issues
        ],
    }

    lines = [
        f"# FILTER — P1 Escape Defects open as of **{as_of.isoformat()}**",
        "",
        f"- **Mode:** `{mode}`",
        f"- **Count:** {len(issues)}",
        "",
        "## JQL",
        "",
        "```",
        jql,
        "```",
        "",
        "## Issues",
        "",
        "| Key | Status | Created | Summary |",
        "|-----|--------|---------|---------|",
    ]
    for row in report["issues"]:
        sm = (row.get("summary") or "").replace("|", "\\|")[:120]
        cr = (row.get("created") or "")[:10]
        lines.append(
            f"| {row['key']} | {row.get('status')} | {cr} | {sm} |"
        )
    lines.append("")

    jp = os.path.join(ROOT, "filter_p1_escape_as_of.json")
    mp = os.path.join(ROOT, "filter_p1_escape_as_of.md")
    with open(jp, "w", encoding="utf-8") as f:
        json.dump(report, f, indent=2)
    with open(mp, "w", encoding="utf-8") as f:
        f.write("\n".join(lines))

    print(f"Wrote {jp}")
    print(f"Wrote {mp}")
    print(f"As of {as_of.isoformat()} ({mode}): {len(issues)} P1 Escape Defect(s) open")


if __name__ == "__main__":
    main()
