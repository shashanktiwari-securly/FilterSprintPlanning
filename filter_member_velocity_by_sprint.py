"""
product_FILTER — per-member velocity by sprint (Jira).

**Velocity (primary):** sum of **Original estimate** hours (`timeoriginalestimate` → hours) on
issues **in sprint scope** and **Done** (status category). Issues with no original estimate
contribute **0** hours.

**Also tracked:** Story Points (`customfield_10005`) on the same Done issues — see second table
in Markdown and fields in JSON.

**Assignee:** current Jira assignee on each issue; issues with no assignee are bucketed as
`(Unassigned)`.

**Sprints:** same cells as `build_sprint_matrix_report.MATRIX` for `product_FILTER` only.

**Team roster** (fixed member list + order for tables), first match wins:
  1. Env `FILTER_TEAM_ROSTER="Name A,Name B"` (comma-separated).
  2. File `filter_team_roster.txt` — one **display name** per line (must match Jira). `#` comments ok.
  3. **`Securly-PjM-Skills.md`** — Part 2 tables: **Developers**, **Manual QA**, **Automation Testing**
     (same order as the doc: devs → QA → automation).

If none of the above yields a list, members are all assignees seen in Jira (sorted; `(Unassigned)` last).

Env: `JIRA_URL`, `JIRA_EMAIL`, `JIRA_API_TOKEN` · optional `JIRA_STORY_POINTS_FIELD`

Optional: `FILTER_VELOCITY_ESTIMATE_USE_AGGREGATE=1` — if an issue has no direct original estimate,
use `aggregatetimeoriginalestimate` (useful when only parents carry rollups; may double-count if
both parent and child are in the same sprint — default off).

Outputs:
  filter_member_velocity_by_sprint.json
  filter_member_velocity_by_sprint.md
  filter_member_velocity_by_sprint.tsv (hours)
  filter_member_velocity_by_sprint_story_points.tsv (SP, same layout)
"""
from __future__ import annotations

import datetime
import json
import os
import sys
from collections import defaultdict
from pathlib import Path
from typing import Any

from build_sprint_matrix_report import (
    MATRIX,
    issue_done,
    jql_for_cell,
    story_points,
    STORY_POINTS_FIELD,
)
from filter_p1_escape_metrics import fetch_all_issues

ROOT = Path(__file__).resolve().parent
UNASSIGNED = "(Unassigned)"

USE_AGGREGATE_ESTIMATE = os.environ.get("FILTER_VELOCITY_ESTIMATE_USE_AGGREGATE", "").strip() == "1"

PRODUCT_FILTER = "product_FILTER"
JSON_OUT = ROOT / "filter_member_velocity_by_sprint.json"
MD_OUT = ROOT / "filter_member_velocity_by_sprint.md"
TSV_OUT = ROOT / "filter_member_velocity_by_sprint.tsv"
TSV_SP_OUT = ROOT / "filter_member_velocity_by_sprint_story_points.tsv"
ROSTER_FILE = ROOT / "filter_team_roster.txt"
SKILLS_MD = ROOT / "Securly-PjM-Skills.md"


def parse_roster_from_skills_md(path: Path) -> list[str]:
    """Part 2 roster: Developers, Manual QA, Automation Testing tables."""
    text = path.read_text(encoding="utf-8")
    bounds = [
        ("#### Developers", "#### Manual QA"),
        ("#### Manual QA", "#### Automation Testing"),
        ("#### Automation Testing", "### Jira issue hierarchy"),
    ]
    names: list[str] = []
    for start_marker, end_marker in bounds:
        try:
            s = text.index(start_marker)
            e = text.index(end_marker, s + len(start_marker))
        except ValueError:
            continue
        chunk = text[s:e]
        for line in chunk.splitlines():
            line = line.strip()
            if not line.startswith("|"):
                continue
            if "------" in line[:20]:
                continue
            parts = [p.strip() for p in line.strip("|").split("|")]
            if len(parts) < 2:
                continue
            name = parts[0].replace("**", "").strip()
            if not name or name == "Name":
                continue
            if name not in names:
                names.append(name)
    return names


def load_roster() -> tuple[list[str] | None, str]:
    raw = os.environ.get("FILTER_TEAM_ROSTER", "").strip()
    if raw:
        names = [x.strip() for x in raw.split(",") if x.strip()]
        return names, "FILTER_TEAM_ROSTER"
    if ROSTER_FILE.is_file():
        lines = ROSTER_FILE.read_text(encoding="utf-8").splitlines()
        out = [ln.strip() for ln in lines if ln.strip() and not ln.strip().startswith("#")]
        if out:
            return out, ROSTER_FILE.name
    if SKILLS_MD.is_file():
        try:
            parsed = parse_roster_from_skills_md(SKILLS_MD)
            if parsed:
                return parsed, SKILLS_MD.name
        except OSError:
            pass
    return None, "none"


def assignee_name(issue: dict[str, Any]) -> str:
    a = (issue.get("fields") or {}).get("assignee")
    if not a:
        return UNASSIGNED
    return (a.get("displayName") or a.get("emailAddress") or UNASSIGNED).strip() or UNASSIGNED


def original_estimate_seconds(issue: dict[str, Any]) -> int | None:
    """Direct original estimate; None if unset."""
    raw = (issue.get("fields") or {}).get("timeoriginalestimate")
    if raw is None:
        return None
    try:
        return int(raw)
    except (TypeError, ValueError):
        return None


def aggregate_estimate_seconds(issue: dict[str, Any]) -> int | None:
    raw = (issue.get("fields") or {}).get("aggregatetimeoriginalestimate")
    if raw is None:
        return None
    try:
        return int(raw)
    except (TypeError, ValueError):
        return None


def estimate_hours_for_velocity(issue: dict[str, Any]) -> float:
    """
    Hours from Jira time tracking. Default: timeoriginalestimate only.
    If FILTER_VELOCITY_ESTIMATE_USE_AGGREGATE=1 and direct is null, use aggregate.
    """
    direct = original_estimate_seconds(issue)
    if direct is not None:
        return direct / 3600.0
    if USE_AGGREGATE_ESTIMATE:
        agg = aggregate_estimate_seconds(issue)
        if agg is not None:
            return agg / 3600.0
    return 0.0


def aggregate_sprint(
    base: str, project: str, sprints: list[str]
) -> dict[str, Any]:
    jql = jql_for_cell(project, sprints)
    fields = [
        "key",
        "issuetype",
        "status",
        "assignee",
        STORY_POINTS_FIELD,
        "timeoriginalestimate",
        "aggregatetimeoriginalestimate",
    ]
    issues = fetch_all_issues(base, jql, fields)

    by_name: dict[str, dict[str, float | int]] = defaultdict(
        lambda: {
            "issues_in_scope": 0,
            "issues_done": 0,
            "story_points_in_scope": 0.0,
            "story_points_done": 0.0,
            "estimate_hours_in_scope": 0.0,
            "estimate_hours_done": 0.0,
        }
    )

    for iss in issues:
        name = assignee_name(iss)
        sp = story_points(iss)
        done = issue_done(iss)
        est_h = estimate_hours_for_velocity(iss)
        row = by_name[name]
        row["issues_in_scope"] += 1
        row["estimate_hours_in_scope"] += est_h
        if sp is not None:
            row["story_points_in_scope"] += sp
            if done:
                row["story_points_done"] += sp
        if done:
            row["issues_done"] += 1
            row["estimate_hours_done"] += est_h

    # Round for JSON readability
    for _n, row in by_name.items():
        row["story_points_in_scope"] = round(float(row["story_points_in_scope"]), 2)
        row["story_points_done"] = round(float(row["story_points_done"]), 2)
        row["estimate_hours_in_scope"] = round(float(row["estimate_hours_in_scope"]), 2)
        row["estimate_hours_done"] = round(float(row["estimate_hours_done"]), 2)

    return {
        "jql": jql,
        "issue_count": len(issues),
        "by_assignee": dict(sorted(by_name.items(), key=lambda x: (-x[1]["issues_in_scope"], x[0]))),
    }


def finalize_member_order(roster: list[str] | None, seen: set[str]) -> list[str]:
    """Roster from env / file / skills: **only** those names (+ Unassigned if present in data)."""
    if roster:
        out: list[str] = []
        for n in roster:
            if n and n not in out:
                out.append(n)
        if UNASSIGNED in seen:
            if UNASSIGNED not in out:
                out.append(UNASSIGNED)
        return out
    out = sorted(n for n in seen if n != UNASSIGNED)
    if UNASSIGNED in seen:
        out.append(UNASSIGNED)
    return out


def sprint_label(month: str, sprints: list[str]) -> str:
    # One column per sprint (avoid "|" — it breaks markdown tables).
    sp = "+".join(sprints)
    return f"{month} · {sp}"


def main() -> None:
    base = os.environ.get("JIRA_URL", "").rstrip("/")
    if not base:
        print("Set JIRA_URL, JIRA_EMAIL, JIRA_API_TOKEN", file=sys.stderr)
        sys.exit(1)

    roster, roster_source = load_roster()

    cells = [c for c in MATRIX if c["product"] == PRODUCT_FILTER]
    if not cells:
        print("No product_FILTER rows in MATRIX.", file=sys.stderr)
        sys.exit(1)

    sprint_rows: list[dict[str, Any]] = []
    all_seen: set[str] = set()

    for cell in cells:
        project = cell["jira_project"]
        sprints = cell["sprints"]
        month = cell["month"]
        agg = aggregate_sprint(base, project, sprints)
        for name in agg["by_assignee"]:
            all_seen.add(name)
        sprint_rows.append(
            {
                "month": month,
                "sprint_names": sprints,
                "column_label": sprint_label(month, sprints),
                "jql": agg["jql"],
                "issue_count": agg["issue_count"],
                "by_assignee": agg["by_assignee"],
            }
        )

    members = finalize_member_order(roster, all_seen)

    report = {
        "generated_at": datetime.datetime.now(datetime.timezone.utc).isoformat(),
        "jira_base": base,
        "product": PRODUCT_FILTER,
        "jira_project": "FILTER",
        "story_points_field": STORY_POINTS_FIELD,
        "roster_source": roster_source,
        "roster_explicit": roster,
        "members_ordered": members,
        "methodology": {
            "velocity_hours_done": (
                "Sum of original estimate (timeoriginalestimate, seconds→hours) per issue; "
                "only issues with status category Done. Missing estimate → 0 unless "
                "FILTER_VELOCITY_ESTIMATE_USE_AGGREGATE=1 (then aggregatetimeoriginalestimate "
                "when direct estimate null)."
            ),
            "velocity_story_points_done": (
                "Sum of story points on issues in sprint scope with status category Done."
            ),
            "assignee": "Current assignee field; empty assignee → (Unassigned).",
            "sprint_scope": "Same JQL as sprint matrix: project FILTER AND sprint in (...).",
            "estimate_aggregate_fallback": USE_AGGREGATE_ESTIMATE,
        },
        "sprints": sprint_rows,
    }

    JSON_OUT.write_text(json.dumps(report, indent=2), encoding="utf-8")

    col_labels = [s["column_label"] for s in sprint_rows]

    def fmt_num(x: float) -> str:
        if abs(x - round(x)) < 1e-6:
            return str(int(round(x)))
        return f"{x:.1f}"

    md_lines = [
        "# product_FILTER — velocity by assignee (original estimate hours, Done)",
        "",
        f"**Generated:** {report['generated_at']}",
        "**Velocity:** sum of **Original estimate** (`timeoriginalestimate`) in **hours** on "
        "issues in sprint scope with **Done** status category.",
        f"**Aggregate fallback:** `FILTER_VELOCITY_ESTIMATE_USE_AGGREGATE=1` → "
        f"{'on' if USE_AGGREGATE_ESTIMATE else 'off'}",
        f"**Story points field (reference):** `{STORY_POINTS_FIELD}`",
        f"**Roster:** {roster_source}",
        "",
        "## Velocity (original estimate hours — Done)",
        "",
        "| Member | " + " | ".join(col_labels) + " | **Σ h done** |",
        "|--------|" + "|".join(["--------:" for _ in col_labels]) + "|------------:|",
    ]
    member_h_totals: dict[str, float] = defaultdict(float)
    for m in members:
        cells_h: list[str] = []
        for sr in sprint_rows:
            row = sr["by_assignee"].get(m)
            h = float(row["estimate_hours_done"]) if row else 0.0
            cells_h.append(fmt_num(h))
            member_h_totals[m] += h
        t = member_h_totals[m]
        md_lines.append("| " + m + " | " + " | ".join(cells_h) + f" | {fmt_num(t)} |")

    md_lines.append("")
    md_lines.append("## Sprint totals (hours + issues)")
    md_lines.append("")
    md_lines.append("| Sprint | Est. hours done (team) | Issues done |")
    md_lines.append("|--------|-------------------------:|------------:|")
    for sr in sprint_rows:
        h_team = sum(float(v["estimate_hours_done"]) for v in sr["by_assignee"].values())
        iss_done = sum(int(v["issues_done"]) for v in sr["by_assignee"].values())
        lab = sr["column_label"]
        md_lines.append(f"| {lab} | {fmt_num(h_team)} | {iss_done} |")
    md_lines.append("")
    md_lines.append("## Story points (Done) — reference")
    md_lines.append("")
    md_lines.append("| Member | " + " | ".join(col_labels) + " | **Σ SP done** |")
    md_lines.append("|--------|" + "|".join(["--------:" for _ in col_labels]) + "|------------:|")
    member_sp_totals: dict[str, float] = defaultdict(float)
    for m in members:
        cells_sp: list[str] = []
        for sr in sprint_rows:
            row = sr["by_assignee"].get(m)
            sp = float(row["story_points_done"]) if row else 0.0
            cells_sp.append(fmt_num(sp))
            member_sp_totals[m] += sp
        t = member_sp_totals[m]
        md_lines.append("| " + m + " | " + " | ".join(cells_sp) + f" | {fmt_num(t)} |")
    md_lines.append("")
    md_lines.append("## Sprint totals (SP done)")
    md_lines.append("")
    md_lines.append("| Sprint | SP done (team) | Issues done |")
    md_lines.append("|--------|----------------:|------------:|")
    for sr in sprint_rows:
        sp_team = sum(float(v["story_points_done"]) for v in sr["by_assignee"].values())
        iss_done = sum(int(v["issues_done"]) for v in sr["by_assignee"].values())
        lab = sr["column_label"]
        md_lines.append(f"| {lab} | {fmt_num(sp_team)} | {iss_done} |")
    md_lines.append("")
    MD_OUT.write_text("\n".join(md_lines), encoding="utf-8")

    # TSV: hours primary
    tsv_h_header = ["Member"] + col_labels + ["Total_hours_est_done"]
    tsv_h_rows = ["\t".join(tsv_h_header)]
    for m in members:
        row_cells = [m]
        rt = 0.0
        for sr in sprint_rows:
            row = sr["by_assignee"].get(m)
            h = float(row["estimate_hours_done"]) if row else 0.0
            rt += h
            row_cells.append(fmt_num(h))
        row_cells.append(fmt_num(rt))
        tsv_h_rows.append("\t".join(row_cells))
    TSV_OUT.write_text("\n".join(tsv_h_rows) + "\n", encoding="utf-8")

    tsv_sp_header = ["Member"] + col_labels + ["Total_SP_done"]
    tsv_sp_rows = ["\t".join(tsv_sp_header)]
    for m in members:
        row_cells = [m]
        rt = 0.0
        for sr in sprint_rows:
            row = sr["by_assignee"].get(m)
            sp = float(row["story_points_done"]) if row else 0.0
            rt += sp
            row_cells.append(fmt_num(sp))
        row_cells.append(fmt_num(rt))
        tsv_sp_rows.append("\t".join(row_cells))
    TSV_SP_OUT.write_text("\n".join(tsv_sp_rows) + "\n", encoding="utf-8")

    print(f"Wrote {JSON_OUT}")
    print(f"Wrote {MD_OUT}")
    print(f"Wrote {TSV_OUT} (hours)")
    print(f"Wrote {TSV_SP_OUT} (story points)")
    print(f"Sprints: {len(sprint_rows)} · Members listed: {len(members)}")


if __name__ == "__main__":
    main()
