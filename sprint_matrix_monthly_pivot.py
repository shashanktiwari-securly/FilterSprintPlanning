"""
Monthly pivot: completion % (Done / Scope) per product × calendar month (2026 Q1).
Multiple sprints in the same product+month are combined (totals then %).

Outputs: sprint_matrix_monthly_pivot.tsv, sprint_matrix_monthly_pivot.md
Used by: render_sprint_matrix_html.py (HTML section)
"""
from __future__ import annotations

import json
from collections import defaultdict
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parent
JSON_PATH = ROOT / "sprint_matrix_report.json"

# Column order (2026)
MONTH_KEYS_LABELS = [("2026-01", "Jan"), ("2026-02", "Feb"), ("2026-03", "Mar")]

PRODUCT_ORDER = [
    "AIChat",
    "FLEX & COM",
    "PASS",
    "Platform",
    "product_aware",
    "product_FILTER",
    "product_home",
    "product_MDM_CLASSROOM",
    "product_oncall",
    "product_RESPOND",
]


def aggregate_by_product_month(rows: list[dict[str, Any]]) -> dict[str, dict[str, dict[str, int]]]:
    """product -> month_key -> {scope, done}"""
    agg: dict[str, dict[str, dict[str, int]]] = defaultdict(
        lambda: defaultdict(lambda: {"scope": 0, "done": 0})
    )
    for r in rows:
        m = r.get("metrics") or {}
        if m.get("error"):
            continue
        p = r["product"]
        month = r["month"]
        agg[p][month]["scope"] += m.get("planned_scope_issues") or 0
        agg[p][month]["done"] += m.get("completed_issues") or 0
    return agg


def completion_pct(scope: int, done: int) -> float | None:
    if not scope:
        return None
    return round(100.0 * done / scope, 1)


def build_pivot(
    agg: dict[str, dict[str, dict[str, int]]],
) -> tuple[list[dict[str, Any]], dict[str, float | None]]:
    """Return data rows (one per product) and footer column averages."""
    data_rows: list[dict[str, Any]] = []
    for product in PRODUCT_ORDER:
        entry: dict[str, Any] = {"product": product}
        month_pcts: list[float] = []
        for mk, label in MONTH_KEYS_LABELS:
            cell = agg.get(product, {}).get(mk)
            if cell and cell["scope"]:
                p = completion_pct(cell["scope"], cell["done"])
                entry[label] = p
                if p is not None:
                    month_pcts.append(p)
            else:
                entry[label] = None
        entry["Avg"] = round(sum(month_pcts) / len(month_pcts), 1) if month_pcts else None
        data_rows.append(entry)

    footer: dict[str, float | None] = {}
    for mk, label in MONTH_KEYS_LABELS:
        col_vals: list[float] = []
        for product in PRODUCT_ORDER:
            cell = agg.get(product, {}).get(mk)
            if cell and cell["scope"]:
                p = completion_pct(cell["scope"], cell["done"])
                if p is not None:
                    col_vals.append(p)
        footer[label] = round(sum(col_vals) / len(col_vals), 1) if col_vals else None

    overall_vals = [footer[lb] for _, lb in MONTH_KEYS_LABELS if footer.get(lb) is not None]
    footer["Avg"] = round(sum(overall_vals) / len(overall_vals), 1) if overall_vals else None
    return data_rows, footer


def format_tsv(data_rows: list[dict[str, Any]], footer: dict[str, float | None]) -> str:
    cols = ["Product", "Jan", "Feb", "Mar", "Avg"]
    lines = ["\t".join(cols)]
    for row in data_rows:
        cells = [row["product"]]
        for c in ["Jan", "Feb", "Mar", "Avg"]:
            v = row.get(c)
            cells.append("" if v is None else str(v))
        lines.append("\t".join(cells))
    lines.append("")
    foot = ["Avg"]
    for c in ["Jan", "Feb", "Mar", "Avg"]:
        v = footer.get(c)
        foot.append("" if v is None else str(v))
    lines.append("\t".join(foot))
    return "\n".join(lines) + "\n"


def format_markdown(data_rows: list[dict[str, Any]], footer: dict[str, float | None]) -> str:
    def cell(v: float | None) -> str:
        if v is None:
            return ""
        return f"{v}%"

    lines = [
        "# Monthly completion % by product (2026 Q1)",
        "",
        "Each cell is **Done / Scope × 100** for all Jira issues in that product’s sprints for the month "
        "(multiple sprints in the same month are merged).",
        "",
        "_PHP / Go migration (project GM) is not a product row; work in other projects’ sprints is counted under those products._",
        "",
        "| Product | Jan | Feb | Mar | Avg |",
        "|---------|-----|-----|-----|-----|",
    ]
    for row in data_rows:
        lines.append(
            "| {p} | {jan} | {feb} | {mar} | {avg} |".format(
                p=row["product"],
                jan=cell(row.get("Jan")),
                feb=cell(row.get("Feb")),
                mar=cell(row.get("Mar")),
                avg=cell(row.get("Avg")),
            )
        )
    lines.append("| **Avg** | {jan} | {feb} | {mar} | {avg} |".format(
        jan=cell(footer.get("Jan")),
        feb=cell(footer.get("Feb")),
        mar=cell(footer.get("Mar")),
        avg=cell(footer.get("Avg")),
    ))
    lines.append("")
    return "\n".join(lines)


def esc_html(s: str) -> str:
    return (
        s.replace("&", "&amp;")
        .replace("<", "&lt;")
        .replace(">", "&gt;")
        .replace('"', "&quot;")
    )


def format_pivot_html(data_rows: list[dict[str, Any]], footer: dict[str, float | None]) -> str:
    def pct_class(p: float | None) -> str:
        if p is None:
            return "pct-na"
        if p >= 90:
            return "pct-good"
        if p >= 70:
            return "pct-mid"
        return "pct-low"

    def td_val(v: float | None) -> str:
        if v is None:
            return '<td class="num">—</td>'
        return f'<td class="num"><span class="badge {pct_class(v)}">{v}%</span></td>'

    body = []
    for row in data_rows:
        body.append(
            "<tr>"
            f'<td class="product">{esc_html(row["product"])}</td>'
            f"{td_val(row.get('Jan'))}"
            f"{td_val(row.get('Feb'))}"
            f"{td_val(row.get('Mar'))}"
            f"{td_val(row.get('Avg'))}"
            "</tr>"
        )
    body.append(
        "<tr class=\"pivot-footer\">"
        "<td><strong>Avg</strong></td>"
        f"{td_val(footer.get('Jan'))}"
        f"{td_val(footer.get('Feb'))}"
        f"{td_val(footer.get('Mar'))}"
        f"{td_val(footer.get('Avg'))}"
        "</tr>"
    )
    return (
        '<h2>Monthly view — completion % (Jan–Mar 2026)</h2>\n'
        '<p class="subtitle pivot-note">Rows: your product list. '
        "<strong>Avg</strong> column: mean of Jan–Mar values where data exists. "
        "Footer <strong>Avg</strong>: mean of product rates for that month.</p>\n"
        '<div class="table-scroll pivot-wrap">\n'
        "  <table class=\"pivot\">\n"
        "    <thead><tr><th>Product</th>"
        '<th class="num">Jan</th><th class="num">Feb</th><th class="num">Mar</th><th class="num">Avg</th>'
        "</tr></thead>\n"
        "    <tbody>\n"
        + "\n".join(body)
        + "\n    </tbody>\n  </table>\n</div>\n"
    )


def load_pivot_from_json(path: Path) -> tuple[list[dict[str, Any]], dict[str, float | None]]:
    data = json.loads(path.read_text(encoding="utf-8"))
    agg = aggregate_by_product_month(data["rows"])
    return build_pivot(agg)


def main() -> None:
    data_rows, footer = load_pivot_from_json(JSON_PATH)
    (ROOT / "sprint_matrix_monthly_pivot.tsv").write_text(
        format_tsv(data_rows, footer), encoding="utf-8"
    )
    (ROOT / "sprint_matrix_monthly_pivot.md").write_text(
        format_markdown(data_rows, footer), encoding="utf-8"
    )
    print(f"Wrote {ROOT / 'sprint_matrix_monthly_pivot.tsv'}")
    print(f"Wrote {ROOT / 'sprint_matrix_monthly_pivot.md'}")


if __name__ == "__main__":
    main()
