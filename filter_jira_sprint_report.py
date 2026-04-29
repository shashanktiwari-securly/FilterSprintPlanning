"""
Jira **Sprint report** (board) export for product **FILTER** — same categories as the UI:
  - **Completed in sprint** (Completed issues in this sprint)
  - **Completed outside** / other sprint (issues completed in another sprint; UI often labels
    "completed outside" / additional work context — API: `issuesCompletedInAnotherSprint`)
  - **Removed from sprint** (punted — `puntedIssues`)

Data source: GreenHopper chart API (Jira Software):
  `GET /rest/greenhopper/1.0/rapid/charts/sprintreport?rapidViewId={boardId}&sprintId={sprintId}`

Sprint resolution (**important**): same sprint *name* can exist on multiple boards. We first
resolve the sprint **as used by project FILTER** (`project = FILTER AND sprint in ("...")` on
one issue, then `GET /rest/agile/1.0/sprint/{id}` → `originBoardId`). That matches the FILTER
sprint matrix. The GreenHopper report is still **board-level** (other projects on the board
can appear in the same named sprint).

Optional: `JIRA_FILTER_BOARD_ID` — Scrum board to prefer when the same sprint name exists
on multiple boards (default **281** if no env set). Also used for fallback name→sprint scan.

Env: JIRA_URL, JIRA_EMAIL, JIRA_API_TOKEN

Outputs:
  filter_jira_sprint_report.json
  filter_jira_sprint_report.md
"""
from __future__ import annotations

import base64
import json
import os
import sys
import time
import urllib.error
import urllib.request
from typing import Any

from build_sprint_matrix_report import search_jql_page

ROOT = os.path.dirname(os.path.abspath(__file__))

# Sprint names (FILTER board) — same as sprint matrix
SPRINT_NAMES_IN_ORDER: list[str] = [
    "sprint-Arthur",
    "sprint-Bertha",
    "sprint-Cristobal",
    "sprint-Dolly",
    "sprint-Edouard",
    "sprint-Fay",
]

JSON_OUT = os.path.join(ROOT, "filter_jira_sprint_report.json")
MD_OUT = os.path.join(ROOT, "filter_jira_sprint_report.md")
PROJECT_KEY = "FILTER"


def extract_board_and_sprint_from_sprint_field(
    base: str, sprint_field: Any, name: str
) -> tuple[int, int] | None:
    """
    Jira often includes `boardId` on the sprint object attached to the issue — that is the
    board the team used (matches Sprint report). `originBoardId` from GET sprint can differ.
    """
    candidates: list[dict[str, Any]] = []
    if isinstance(sprint_field, dict) and sprint_field.get("name") == name:
        candidates = [sprint_field]
    elif isinstance(sprint_field, list):
        candidates = [s for s in sprint_field if isinstance(s, dict) and s.get("name") == name]
    for s in candidates:
        sid = int(s["id"])
        bid = s.get("boardId")
        if bid is not None:
            return int(bid), sid
        try:
            meta = http_get_json(base, f"/rest/agile/1.0/sprint/{sid}")
        except RuntimeError:
            continue
        ob = meta.get("originBoardId")
        if ob is not None:
            return int(ob), sid
    return None


def resolve_sprint_from_filter_project(base: str, sprint_name: str) -> tuple[int, int] | None:
    """Board id + sprint id for the sprint row that FILTER issues use (matches matrix)."""
    jql = f"project = {PROJECT_KEY} AND sprint in ({json.dumps(sprint_name)})"
    tok: str | None = None
    while True:
        data = search_jql_page(base, jql, ["sprint"], 50, tok)
        issues = data.get("issues") or []
        for iss in issues:
            pair = extract_board_and_sprint_from_sprint_field(
                base,
                (iss.get("fields") or {}).get("sprint"),
                sprint_name,
            )
            if pair is not None:
                return pair
        if data.get("isLast") or not issues:
            break
        tok = data.get("nextPageToken")
        if not tok:
            break
        time.sleep(0.12)
    return None


def filter_only_filter_keys(keys: list[str]) -> list[str]:
    return sorted(k for k in keys if k.startswith(f"{PROJECT_KEY}-"))


def auth_header() -> str:
    email = os.environ["JIRA_EMAIL"]
    token = os.environ["JIRA_API_TOKEN"]
    creds = base64.b64encode(f"{email}:{token}".encode()).decode()
    return f"Basic {creds}"


def http_get_json(base: str, path: str, params: dict[str, str] | None = None) -> Any:
    url = f"{base.rstrip('/')}{path}"
    if params:
        from urllib.parse import urlencode

        url += "?" + urlencode(params)
    req = urllib.request.Request(
        url,
        method="GET",
        headers={
            "Accept": "application/json",
            "Authorization": auth_header(),
        },
    )
    try:
        with urllib.request.urlopen(req, timeout=120) as resp:
            return json.load(resp)
    except urllib.error.HTTPError as e:
        body = e.read().decode(errors="replace")
        raise RuntimeError(f"GET {path} HTTP {e.code}: {body[:2000]}") from e


def get_scrum_boards(base: str) -> list[dict[str, Any]]:
    """Boards for FILTER; keep Scrum (sprint-capable) boards."""
    out: list[dict[str, Any]] = []
    start = 0
    while True:
        data = http_get_json(
            base,
            "/rest/agile/1.0/board",
            {
                "projectKeyOrId": PROJECT_KEY,
                "maxResults": "50",
                "startAt": str(start),
            },
        )
        for b in data.get("values") or []:
            if (b.get("type") or "").lower() == "scrum":
                out.append(b)
        if data.get("isLast"):
            break
        start += int(data.get("maxResults", 0) or 50)
        if not (data.get("values") or []):
            break
    return out


def order_boards_preferred_first(boards: list[dict[str, Any]]) -> list[dict[str, Any]]:
    """
    When several Scrum boards list the same sprint *name*, prefer the main FILTER
    team board. Set JIRA_FILTER_BOARD_ID (e.g. 281) to match the Sprint report UI.
    """
    prefer = os.environ.get("JIRA_FILTER_BOARD_ID", "281").strip()
    if not prefer:
        return boards
    try:
        pid = int(prefer)
    except ValueError:
        return boards
    return sorted(boards, key=lambda b: 0 if int(b["id"]) == pid else 1)


def iter_sprints_on_board(base: str, board_id: int) -> list[dict[str, Any]]:
    all_s: list[dict[str, Any]] = []
    start = 0
    while True:
        data = http_get_json(
            base,
            f"/rest/agile/1.0/board/{board_id}/sprint",
            {"startAt": str(start), "maxResults": "50"},
        )
        all_s.extend(data.get("values") or [])
        if data.get("isLast"):
            break
        start += int(data.get("maxResults", 0) or 50)
        if not (data.get("values") or []):
            break
    return all_s


def find_sprint_on_boards(
    base: str, boards: list[dict[str, Any]], name: str
) -> tuple[int, int] | None:
    for b in boards:
        bid = int(b["id"])
        for sp in iter_sprints_on_board(base, bid):
            if sp.get("name") == name:
                return bid, int(sp["id"])
    return None


def get_sprint_report(base: str, board_id: int, sprint_id: int) -> dict[str, Any]:
    return http_get_json(
        base,
        "/rest/greenhopper/1.0/rapid/charts/sprintreport",
        {
            "rapidViewId": str(board_id),
            "sprintId": str(sprint_id),
        },
    )


def _keys_from_rapid_block(block: Any) -> list[str]:
    """Parse completedIssues / puntedIssues style { issues: [ {key: ...} ] } or list."""
    if not block:
        return []
    if isinstance(block, list):
        return [
            str(x.get("key", ""))
            for x in block
            if isinstance(x, dict) and x.get("key")
        ]
    if isinstance(block, dict):
        issues = block.get("issues")
        if isinstance(issues, list):
            return [
                str(x.get("key", ""))
                for x in issues
                if isinstance(x, dict) and x.get("key")
            ]
    return []


def _keys_from_map_added(m: Any) -> list[str]:
    """issueKeysAddedDuringSprint is often { "KEY-1": true, ... }."""
    if not m:
        return []
    if isinstance(m, dict) and m:
        return sorted(k for k in m if k)
    return []


def parse_report_contents(data: dict[str, Any]) -> dict[str, Any]:
    raw = (data or {}).get("contents") or {}
    if not isinstance(raw, dict) and (data or {}).get("content"):
        raw = (data or {}).get("content") or {}
    return {
        "completed_in_sprint": _keys_from_rapid_block(raw.get("completedIssues")),
        "not_completed": _keys_from_rapid_block(
            raw.get("issuesNotCompletedInCurrentSprint")
        ),
        "completed_in_another_sprint": _keys_from_rapid_block(
            raw.get("issuesCompletedInAnotherSprint")
        ),
        "removed_from_sprint": _keys_from_rapid_block(raw.get("puntedIssues")),
        "issue_keys_added_during_sprint": _keys_from_map_added(
            raw.get("issueKeysAddedDuringSprint")
        ),
    }


def main() -> None:
    base = os.environ.get("JIRA_URL", "").rstrip("/")
    if not base:
        print("Set JIRA_URL, JIRA_EMAIL, JIRA_API_TOKEN", file=sys.stderr)
        sys.exit(1)

    board_id_env = os.environ.get("JIRA_FILTER_BOARD_ID", "").strip()
    if board_id_env:
        boards = [{"id": int(board_id_env), "name": f"board {board_id_env}"}]
    else:
        boards = order_boards_preferred_first(get_scrum_boards(base))
    if not boards:
        print("No Scrum board found for FILTER. Set JIRA_FILTER_BOARD_ID.", file=sys.stderr)
        sys.exit(1)

    resolved: dict[str, dict[str, Any]] = {}
    missing: list[str] = []
    for name in SPRINT_NAMES_IN_ORDER:
        found: tuple[int, int] | None = resolve_sprint_from_filter_project(base, name)
        resolution = "filter_project_sprint_field" if found else ""
        if not found and board_id_env:
            for sp in iter_sprints_on_board(base, int(board_id_env)):
                if sp.get("name") == name:
                    found = (int(board_id_env), int(sp["id"]))
                    resolution = "jira_filter_board_id_fallback"
                    break
        if not found:
            found = find_sprint_on_boards(base, boards, name)
            if found:
                resolution = "first_scrum_board_matching_name"
        if not found:
            missing.append(name)
            continue
        bid, sid = found
        time.sleep(0.15)
        try:
            report = get_sprint_report(base, bid, sid)
        except RuntimeError as e:
            resolved[name] = {
                "error": str(e),
                "board_id": bid,
                "sprint_id": sid,
            }
            continue
        parsed = parse_report_contents(report)
        def fo(k: str) -> list[str]:
            return filter_only_filter_keys(parsed.get(k) or [])

        resolved[name] = {
            "board_id": bid,
            "sprint_id": sid,
            "sprint_resolution": resolution,
            "jira_sprint_name": name,
            "sprint_info": (report or {}).get("sprint", {}),
            "raw_sprint_report_keys": list(((report or {}).get("contents") or {}).keys())
            if isinstance((report or {}).get("contents"), dict)
            else [],
            **parsed,
            "completed_in_sprint_FILTER_only": fo("completed_in_sprint"),
            "completed_in_another_sprint_FILTER_only": fo("completed_in_another_sprint"),
            "removed_from_sprint_FILTER_only": fo("removed_from_sprint"),
            "raw_report": report,
        }

    report_doc: dict[str, Any] = {
        "project": PROJECT_KEY,
        "jira_base": base,
        "sprints_requested": SPRINT_NAMES_IN_ORDER,
        "sprints_not_found": missing,
        "methodology": {
            "source": "GET /rest/greenhopper/1.0/rapid/charts/sprintreport",
            "completed_in_sprint": "contents.completedIssues — issues done as part of this sprint.",
            "completed_in_another_sprint": "contents.issuesCompletedInAnotherSprint — completed outside / in another sprint (UI naming varies).",
            "removed_from_sprint": "contents.puntedIssues — removed from the sprint (scope out).",
            "added_during_sprint": "contents.issueKeysAddedDuringSprint — keys added to sprint after start (reference).",
            "not_completed": "contents.issuesNotCompletedInCurrentSprint — not done at sprint end (reference).",
        },
        "sprints": resolved,
    }

    with open(JSON_OUT, "w", encoding="utf-8") as f:
        json.dump(report_doc, f, indent=2)

    lines = [
        "# FILTER — Jira Sprint report export",
        "",
        f"**Source:** GreenHopper `sprintreport` API · **Project:** {PROJECT_KEY}",
        "",
        "The sprint report is **board-scoped**: the same sprint can list issues from other "
        "projects on that board. Each section includes a **`FILTER-` only** line for the "
        "subset that matches the FILTER project.",
        "",
        "Per sprint, issue keys are grouped like the Jira **Sprint report** view:",
        "",
        "1. **Completed in this sprint** — `completedIssues`",
        "2. **Completed in another sprint / outside** — `issuesCompletedInAnotherSprint`",
        "3. **Removed from sprint** (punted) — `puntedIssues`",
        "",
        f"**Sprints not found on a Scrum board:** {', '.join(missing) if missing else 'none'}",
        "",
    ]

    for name in SPRINT_NAMES_IN_ORDER:
        if name not in resolved:
            continue
        block = resolved[name]
        lines.append(f"## {name}")
        lines.append("")
        if block.get("error"):
            lines.append(f"**Error:** `{block.get('error')[:500]}`")
            lines.append("")
            continue
        lines.append(f"- **Board id:** {block.get('board_id')} · **Sprint id:** {block.get('sprint_id')}")
        if block.get("sprint_resolution"):
            lines.append(f"- **Sprint resolution:** `{block.get('sprint_resolution')}`")
        if block.get("raw_sprint_report_keys"):
            lines.append(
                f"- **Raw `contents` keys:** `{', '.join(block['raw_sprint_report_keys'])}`"
            )
        lines.append("")

        def print_bucket(title: str, key: str, filter_key: str | None = None) -> None:
            keys = block.get(key) or []
            lines.append(f"### {title} ({len(keys)})")
            if keys:
                lines.append("")
                lines.append(", ".join(f"`{k}`" for k in keys))
            else:
                lines.append("")
            lines.append("")
            if filter_key and block.get(filter_key) is not None:
                fk = block.get(filter_key) or []
                if fk:
                    lines.append(
                        f"**{PROJECT_KEY} keys only:** {len(fk)} — "
                        + ", ".join(f"`{k}`" for k in fk)
                    )
                else:
                    lines.append(f"**{PROJECT_KEY} keys only:** 0")
                lines.append("")

        print_bucket(
            "1. Completed in this sprint",
            "completed_in_sprint",
            "completed_in_sprint_FILTER_only",
        )
        print_bucket(
            "2. Completed in another sprint (outside / additional context)",
            "completed_in_another_sprint",
            "completed_in_another_sprint_FILTER_only",
        )
        print_bucket(
            "3. Removed from sprint",
            "removed_from_sprint",
            "removed_from_sprint_FILTER_only",
        )

        if block.get("issue_keys_added_during_sprint"):
            print_bucket(
                "Reference — Added to sprint after start (issueKeysAddedDuringSprint)",
                "issue_keys_added_during_sprint",
            )

        nc = block.get("not_completed") or []
        if nc:
            print_bucket("Reference — Not completed in sprint (carryover)", "not_completed")

    lines.append("---")
    lines.append(f"**JSON:** `{os.path.basename(JSON_OUT)}` (includes full `raw_report` per sprint).")
    lines.append("")

    with open(MD_OUT, "w", encoding="utf-8") as f:
        f.write("\n".join(lines))

    print(f"Wrote {JSON_OUT}")
    print(f"Wrote {MD_OUT}")
    if missing:
        print("Missing sprints on board scan:", ", ".join(missing), file=sys.stderr)


if __name__ == "__main__":
    main()
