"""
Fetch FILTER sprint start/end dates from Jira Software (Agile REST API).

Jira returns sprint boundaries on:
  GET /rest/agile/1.0/sprint/{sprintId}

The sprint id + board id are resolved the same way as ``filter_jira_sprint_report.py``:
first via ``project = FILTER AND sprint in ("...")`` on an issue; if no issues exist yet,
we scan Scrum boards for FILTER (prefer ``JIRA_FILTER_BOARD_ID``).

Env: JIRA_URL, JIRA_EMAIL, JIRA_API_TOKEN
Optional: JIRA_FILTER_BOARD_ID (default 281)

Usage:
  python fetch_filter_sprint_meta.py sprint-Hanna
  python fetch_filter_sprint_meta.py sprint-Hanna --out product_FILTER/sprint-Hanna-sprint-data/sprint-meta.json
"""
from __future__ import annotations

import argparse
import json
import os
import sys
from datetime import date, timedelta
from typing import Any

ROOT = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, ROOT)

from filter_jira_sprint_report import (  # noqa: E402
    find_sprint_on_boards,
    get_scrum_boards,
    http_get_json,
    order_boards_preferred_first,
    resolve_sprint_from_filter_project,
)
from sprint_overrides import apply_override  # noqa: E402


def count_weekdays_inclusive(start: date, end: date) -> int:
    n = 0
    d = start
    while d <= end:
        if d.weekday() < 5:
            n += 1
        d += timedelta(days=1)
    return n


def iso_to_date(iso: str | None) -> date | None:
    if not iso:
        return None
    return date.fromisoformat(iso[:10])


def resolve_board_and_sprint_id(base: str, sprint_name: str) -> tuple[int, int]:
    pair = resolve_sprint_from_filter_project(base, sprint_name)
    if pair:
        return pair
    boards = order_boards_preferred_first(get_scrum_boards(base))
    found = find_sprint_on_boards(base, boards, sprint_name)
    if found:
        return found
    raise SystemExit(
        f"Could not resolve sprint {sprint_name!r}: no FILTER issues in sprint and "
        "name not found on FILTER Scrum boards (check sprint name / board)."
    )


def main() -> None:
    ap = argparse.ArgumentParser(description="Fetch Jira sprint dates for FILTER.")
    ap.add_argument("sprint_name", nargs="?", default="sprint-Hanna", help="Jira sprint name")
    ap.add_argument(
        "--out",
        default=os.path.join(
            ROOT, "product_FILTER", "sprint-Hanna-sprint-data", "sprint-meta.json"
        ),
        help="Path to write sprint-meta.json",
    )
    args = ap.parse_args()

    for key in ("JIRA_URL", "JIRA_EMAIL", "JIRA_API_TOKEN"):
        if not os.environ.get(key):
            raise SystemExit(f"Missing environment variable {key}")

    base = os.environ["JIRA_URL"].rstrip("/")
    board_id, sprint_id = resolve_board_and_sprint_id(base, args.sprint_name)
    meta: dict[str, Any] = http_get_json(base, f"/rest/agile/1.0/sprint/{sprint_id}")

    start_d = iso_to_date(meta.get("startDate"))
    end_d = iso_to_date(meta.get("endDate"))
    if start_d is None or end_d is None:
        raise SystemExit(
            f"Sprint {args.sprint_name!r} (id={sprint_id}) has no startDate/endDate in Jira yet.\n"
            f"API payload (excerpt): {json.dumps({k: meta.get(k) for k in ('name', 'state', 'startDate', 'endDate')})}\n"
            "Backlog/future sprints often lack dates until the sprint is started or scheduled in Jira."
        )

    out = {
        "sprint_name": meta.get("name") or args.sprint_name,
        "sprint_id": sprint_id,
        "board_id": board_id,
        "origin_board_id": meta.get("originBoardId"),
        "state": meta.get("state"),
        "goal": meta.get("goal"),
        "start_date": start_d.isoformat(),
        "end_date": end_d.isoformat(),
        "start_date_raw": meta.get("startDate"),
        "end_date_raw": meta.get("endDate"),
        "jira_start_date": start_d.isoformat(),
        "jira_end_date": end_d.isoformat(),
        "working_days": count_weekdays_inclusive(start_d, end_d),
        "api_self": meta.get("self"),
    }

    apply_override(out)
    if out.get("override_applied"):
        print(
            f"  applied canonical-window override: "
            f"{out['jira_start_date']}→{out['jira_end_date']}  ->  "
            f"{out['start_date']}→{out['end_date']} ({out['working_days']} wdays)"
        )

    out_dir = os.path.dirname(os.path.abspath(args.out))
    if out_dir:
        os.makedirs(out_dir, exist_ok=True)
    with open(args.out, "w", encoding="utf-8") as f:
        json.dump(out, f, indent=2)
        f.write("\n")

    print(json.dumps(out, indent=2))
    print(f"\nWrote {args.out}")


if __name__ == "__main__":
    main()
