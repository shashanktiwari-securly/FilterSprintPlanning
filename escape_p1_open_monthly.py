"""
P1 Escape Defects — **average concurrent count per sprint**, rolled up by month.

For **each sprint** named in the sprint matrix (each MATRIX cell, each sprint string):
  count issues where
    issuetype = "Escape Defect"
    AND priority = P1
    AND <concurrent filter> (default: not yet Done — still open in the sprint)

**Monthly value** (Jan / Feb / Mar) = **arithmetic mean** of those per-sprint counts for that
product in that calendar month. (If a month has one sprint, the average equals that sprint’s count.)

**Avg** column = mean of the three monthly values.

This answers: “on average, how many P1 Escape Defects were **concurrently** open **per sprint**
in each month?” (not one merged count across all sprints in the month).

Optional env:
  JIRA_P1_CONCURRENT_JQL — default `statusCategory != Done`
    (issues still active). Set to `status in ("Open", "Concurrent")` if you only want those statuses.

Outputs:
  escape_p1_open_monthly.json (includes sprint_breakdown)
  escape_p1_open_monthly.tsv, escape_p1_open_monthly.md
"""
from __future__ import annotations

import datetime
import json
import os
import sys
import time
import urllib.error
from collections import defaultdict
from pathlib import Path
from typing import Any

from build_sprint_matrix_report import MATRIX, search_jql_page
from sprint_matrix_monthly_pivot import PRODUCT_ORDER

ROOT = Path(__file__).resolve().parent

MONTH_KEYS_LABELS = [("2026-01", "Jan"), ("2026-02", "Feb"), ("2026-03", "Mar")]

# "Concurrent" = still in play (not completed). Override for literal Open/Concurrent only.
P1_CONCURRENT_JQL = os.environ.get(
    "JIRA_P1_CONCURRENT_JQL",
    "statusCategory != Done",
).strip()


def jql_p1_escape_per_sprint(project: str, sprint_name: str) -> str:
    sp = json.dumps(sprint_name)
    return (
        f"project = {project} AND sprint = {sp} "
        f'AND issuetype = "Escape Defect" AND priority = P1 '
        f"AND ({P1_CONCURRENT_JQL})"
    )


def count_issues(base: str, jql: str) -> int:
    next_token = None
    total = 0
    page_size = 100
    while True:
        try:
            data = search_jql_page(base, jql, ["key"], page_size, next_token)
        except urllib.error.HTTPError as e:
            raise RuntimeError(
                f"JQL failed ({jql[:200]}...): {e.read().decode(errors='replace')[:800]}"
            ) from e
        issues = data.get("issues") or []
        total += len(issues)
        if data.get("isLast") or not issues:
            break
        next_token = data.get("nextPageToken")
        if not next_token:
            break
        time.sleep(0.12)
    return total


def build_report() -> dict[str, Any]:
    base = os.environ.get("JIRA_URL", "").rstrip("/")
    if not base:
        print("Set JIRA_URL, JIRA_EMAIL, JIRA_API_TOKEN", file=sys.stderr)
        sys.exit(1)

    sprint_breakdown: list[dict[str, Any]] = []
    # (product, month) -> list of per-sprint counts
    by_product_month: dict[tuple[str, str], list[int]] = defaultdict(list)

    for cell in MATRIX:
        product = cell["product"]
        month = cell["month"]
        jp = cell["jira_project"]
        for sprint_name in cell["sprints"]:
            jql = jql_p1_escape_per_sprint(jp, sprint_name)
            n = count_issues(base, jql)
            sprint_breakdown.append(
                {
                    "product": product,
                    "month": month,
                    "jira_project": jp,
                    "sprint": sprint_name,
                    "concurrent_p1_escape_count": n,
                    "jql": jql,
                }
            )
            by_product_month[(product, month)].append(n)

    rows_out: list[dict[str, Any]] = []
    for product in PRODUCT_ORDER:
        entry: dict[str, Any] = {"product": product}
        month_avgs: list[float] = []
        for mk, label in MONTH_KEYS_LABELS:
            counts = by_product_month.get((product, mk), [])
            if not counts:
                entry[label] = None
                continue
            avg_m = round(sum(counts) / len(counts), 1)
            entry[label] = avg_m
            month_avgs.append(avg_m)
        entry["avg"] = (
            round(sum(month_avgs) / len(month_avgs), 1) if month_avgs else None
        )
        rows_out.append(entry)

    footer: dict[str, float | None] = {}
    for _mk, label in MONTH_KEYS_LABELS:
        vals = [r[label] for r in rows_out if r.get(label) is not None]
        footer[label] = round(sum(vals) / len(vals), 1) if vals else None
    overall = [footer[lb] for _, lb in MONTH_KEYS_LABELS if footer.get(lb) is not None]
    footer["Avg"] = round(sum(overall) / len(overall), 1) if overall else None

    return {
        "generated_at": datetime.datetime.now(datetime.timezone.utc).isoformat(),
        "jira_base": base,
        "methodology": {
            "issue_type": "Escape Defect",
            "priority": "P1",
            "concurrent_definition": P1_CONCURRENT_JQL,
            "per_sprint": (
                "For each sprint in the matrix, count matching issues (one query per sprint)."
            ),
            "monthly_value": (
                "Mean of per-sprint counts for that product in that calendar month."
            ),
            "row_avg": "Mean of Jan, Feb, and Mar monthly values.",
        },
        "rows": rows_out,
        "footer": footer,
        "sprint_breakdown": sprint_breakdown,
    }


def write_tsv(report: dict[str, Any]) -> str:
    lines = ["Product\tJan\tFeb\tMar\tAvg"]
    for r in report["rows"]:
        cells = [r["product"]]
        for c in ["Jan", "Feb", "Mar", "avg"]:
            v = r.get("avg") if c == "avg" else r.get(c)
            cells.append("" if v is None else str(v))
        lines.append("\t".join(cells))
    lines.append("")
    foot = ["Avg"]
    for c in ["Jan", "Feb", "Mar", "Avg"]:
        v = report["footer"].get(c)
        foot.append("" if v is None else str(v))
    lines.append("\t".join(foot))
    return "\n".join(lines) + "\n"


def write_md(report: dict[str, Any]) -> str:
    m = report["methodology"]
    lines = [
        "# Avg concurrent P1 Escape Defects per sprint (by month, 2026 Q1)",
        "",
        f"- **Concurrent:** `{m.get('concurrent_definition', '')}`",
        f"- **Per sprint:** {m.get('per_sprint', '')}",
        f"- **Monthly cell:** {m.get('monthly_value', '')}",
        f"- **Snapshot:** {report.get('generated_at', '')}",
        "",
        "| Product | Jan | Feb | Mar | Avg |",
        "|---------|-----|-----|-----|-----|",
    ]
    for r in report["rows"]:
        lines.append(
            "| {p} | {jan} | {feb} | {mar} | {avg} |".format(
                p=r["product"],
                jan=r.get("Jan", ""),
                feb=r.get("Feb", ""),
                mar=r.get("Mar", ""),
                avg=r.get("avg", ""),
            )
        )
    f = report["footer"]
    lines.append(
        "| **Avg** | {jan} | {feb} | {mar} | {avg} |".format(
            jan=f.get("Jan", ""),
            feb=f.get("Feb", ""),
            mar=f.get("Mar", ""),
            avg=f.get("Avg", ""),
        )
    )
    lines.append("")
    lines.append("## Per-sprint counts (detail)")
    lines.append("")
    lines.append("| Product | Month | Sprint | Count |")
    lines.append("|---------|-------|--------|------:|")
    for s in report.get("sprint_breakdown") or []:
        lines.append(
            "| {p} | {m} | {sp} | {c} |".format(
                p=s["product"],
                m=s["month"],
                sp=s["sprint"].replace("|", "\\|"),
                c=s["concurrent_p1_escape_count"],
            )
        )
    lines.append("")
    return "\n".join(lines)


def row_esc(s: str) -> str:
    return (
        s.replace("&", "&amp;")
        .replace("<", "&lt;")
        .replace(">", "&gt;")
        .replace('"', "&quot;")
    )


def td_num(v: int | float | None) -> str:
    if v is None:
        return '<td class="num">—</td>'
    return f'<td class="num">{v}</td>'


def format_p1_html(report: dict[str, Any]) -> str:
    rows = report["rows"]
    foot = report["footer"]
    m = report.get("methodology", {})
    conc = m.get("concurrent_definition", "statusCategory != Done")
    body = []
    for r in rows:
        body.append(
            "<tr>"
            f'<td class="product">{row_esc(r["product"])}</td>'
            f'{td_num(r.get("Jan"))}{td_num(r.get("Feb"))}{td_num(r.get("Mar"))}{td_num(r.get("avg"))}'
            "</tr>"
        )
    body.append(
        '<tr class="pivot-footer">'
        "<td><strong>Avg</strong></td>"
        f"{td_num(foot.get('Jan'))}{td_num(foot.get('Feb'))}{td_num(foot.get('Mar'))}{td_num(foot.get('Avg'))}"
        "</tr>"
    )
    return (
        '<h2>Avg concurrent P1 Escape Defects per sprint (Jan–Mar 2026)</h2>\n'
        f'<p class="subtitle pivot-note">Per sprint: count Escape Defect + P1 where <code>{row_esc(conc)}</code>. '
        "Each <strong>month</strong> cell is the <strong>average</strong> of those counts across all sprints "
        "in that month for the product. <strong>Avg</strong> column = mean of Jan–Mar. "
        "Point-in-time snapshot.</p>\n"
        '<div class="table-scroll pivot-wrap">\n'
        '  <table class="pivot">\n'
        "    <thead><tr><th>Product</th>"
        '<th class="num">Jan</th><th class="num">Feb</th><th class="num">Mar</th><th class="num">Avg</th>'
        "</tr></thead>\n"
        "    <tbody>\n"
        + "\n".join(body)
        + "\n    </tbody>\n  </table>\n</div>\n"
    )


def main() -> None:
    report = build_report()
    root = ROOT
    (root / "escape_p1_open_monthly.json").write_text(
        json.dumps(report, indent=2), encoding="utf-8"
    )
    (root / "escape_p1_open_monthly.tsv").write_text(write_tsv(report), encoding="utf-8")
    (root / "escape_p1_open_monthly.md").write_text(write_md(report), encoding="utf-8")
    print(f"Wrote {root / 'escape_p1_open_monthly.json'}")
    print(f"Wrote {root / 'escape_p1_open_monthly.tsv'}")
    print(f"Wrote {root / 'escape_p1_open_monthly.md'}")


if __name__ == "__main__":
    main()
