"""Render sprint_matrix_report.json as a presentable standalone HTML file."""
from __future__ import annotations

import json
from collections import defaultdict
from pathlib import Path

from all_products_p1_escape_metrics import format_all_products_p1_html
from escape_p1_open_monthly import format_p1_html
from sprint_matrix_monthly_pivot import format_pivot_html, load_pivot_from_json

ROOT = Path(__file__).resolve().parent
JSON_PATH = ROOT / "sprint_matrix_report.json"
P1_JSON_PATH = ROOT / "escape_p1_open_monthly.json"
ALL_P1_JSON_PATH = ROOT / "all_products_p1_escape_metrics.json"
HTML_PATH = ROOT / "sprint_matrix_report.html"


def month_display(iso: str) -> str:
    parts = iso.split("-")
    y, m = parts[0], parts[1]
    names = {
        "01": "Jan",
        "02": "Feb",
        "03": "Mar",
        "04": "Apr",
        "05": "May",
        "06": "Jun",
        "07": "Jul",
        "08": "Aug",
        "09": "Sep",
        "10": "Oct",
        "11": "Nov",
        "12": "Dec",
    }
    return f"{names.get(m, m)} {y}"


def pct_class(pct: float | None) -> str:
    if pct is None:
        return "pct-na"
    if pct >= 90:
        return "pct-good"
    if pct >= 70:
        return "pct-mid"
    return "pct-low"


def esc(s: str) -> str:
    return (
        s.replace("&", "&amp;")
        .replace("<", "&lt;")
        .replace(">", "&gt;")
        .replace('"', "&quot;")
    )


def main() -> None:
    data = json.loads(JSON_PATH.read_text(encoding="utf-8"))
    generated = data.get("generated_at", "")
    base = data.get("jira_base", "")
    rows = data["rows"]

    try:
        pivot_rows, pivot_footer = load_pivot_from_json(JSON_PATH)
        monthly_pivot_html = format_pivot_html(pivot_rows, pivot_footer)
    except Exception as e:
        monthly_pivot_html = f'<p class="err">Monthly pivot could not be built: {esc(str(e))}</p>'

    try:
        if P1_JSON_PATH.exists():
            p1_data = json.loads(P1_JSON_PATH.read_text(encoding="utf-8"))
            escape_p1_html = format_p1_html(p1_data)
        else:
            escape_p1_html = (
                '<p class="muted">Run <code>python escape_p1_open_monthly.py</code> to generate '
                "Open / Concurrent P1 Escape Defect counts.</p>"
            )
    except Exception as e:
        escape_p1_html = f'<p class="err">P1 Escape Defect table could not be loaded: {esc(str(e))}</p>'

    try:
        if ALL_P1_JSON_PATH.exists():
            all_p1_data = json.loads(ALL_P1_JSON_PATH.read_text(encoding="utf-8"))
            all_products_p1_html = format_all_products_p1_html(all_p1_data)
        else:
            all_products_p1_html = (
                '<section class="all-products-p1"><p class="muted">Run '
                "<code>python all_products_p1_escape_metrics.py</code> to generate "
                "all-product P1 Escape WIP and monthly inflow tables.</p></section>"
            )
    except Exception as e:
        all_products_p1_html = (
            f'<section class="all-products-p1"><p class="err">'
            f"All-products P1 metrics could not be loaded: {esc(str(e))}</p></section>"
        )

    by_product: dict[str, list] = defaultdict(list)
    for r in rows:
        by_product[r["product"]].append(r)

    # Summary: primary = weighted original-estimate hours across cells; issue % = secondary
    summaries = []
    for product, prs in sorted(by_product.items()):
        rates = [
            p["metrics"]["completion_rate_pct"]
            for p in prs
            if p["metrics"].get("completion_rate_pct") is not None
            and p["metrics"].get("planned_scope_issues", 0)
        ]
        scopes = [
            p["metrics"].get("planned_scope_issues") or 0 for p in prs
        ]
        done = [
            p["metrics"].get("completed_issues") or 0
            for p in prs
        ]
        avg_issue = round(sum(rates) / len(rates), 1) if rates else None
        est_p = 0.0
        est_d = 0.0
        for p in prs:
            mm = p["metrics"]
            if mm.get("error"):
                continue
            est_p += float(mm.get("original_estimate_hours_planned_sum") or 0)
            est_d += float(mm.get("original_estimate_hours_done_sum") or 0)
        avg_est_pct = round(100.0 * est_d / est_p, 1) if est_p > 0 else None
        summaries.append(
            {
                "product": product,
                "cells": len(prs),
                "avg_issue_pct": avg_issue,
                "avg_est_pct": avg_est_pct,
                "est_hours_planned": est_p,
                "est_hours_done": est_d,
                "total_scope": sum(scopes),
                "total_done": sum(done),
            }
        )

    summary_cards = "".join(
        f"""<div class="card">
  <div class="card-label">{esc(s["product"])}</div>
  <div class="card-stat"><span class="big">{s["avg_est_pct"] if s["avg_est_pct"] is not None else "—"}</span><span class="unit">% est. (h) done</span></div>
  <div class="card-meta">{s["est_hours_done"]:,.1f} / {s["est_hours_planned"]:,.1f} h · issue avg {s["avg_issue_pct"] if s["avg_issue_pct"] is not None else "—"}% · {s["total_done"]:,} / {s["total_scope"]:,} issues · {s["cells"]} cells</div>
</div>"""
        for s in summaries
    )

    table_rows = []
    for r in rows:
        m = r["metrics"]
        err = m.get("error")
        if err:
            table_rows.append(
                f"""<tr class="row-error">
  <td>{esc(r["product"])}</td>
  <td>{month_display(r["month"])}</td>
  <td class="sprints">{esc(", ".join(r["sprints"]))}</td>
  <td colspan="7" class="err">{esc(err[:200])}</td>
</tr>"""
            )
            continue
        pct = m.get("completion_rate_pct")
        est_planned = float(m.get("original_estimate_hours_planned_sum") or 0)
        est_done = float(m.get("original_estimate_hours_done_sum") or 0)
        est_pct = m.get("original_estimate_hours_completion_pct")
        if est_pct is not None:
            est_badge_cls = pct_class(est_pct)
            est_badge = f'<span class="badge {est_badge_cls}">{est_pct:g}%</span>'
        else:
            est_badge = '<span class="muted" title="No original estimates on scope">—</span>'

        open_cnt = (m.get("planned_scope_issues") or 0) - (m.get("completed_issues") or 0)
        est_planned_s = f"{est_planned:g}" if est_planned else "0"
        est_done_s = f"{est_done:g}" if est_done or est_planned else "0"
        table_rows.append(
            f"""<tr>
  <td class="product">{esc(r["product"])}</td>
  <td>{month_display(r["month"])}</td>
  <td class="sprints">{esc(", ".join(r["sprints"]))}</td>
  <td class="num">{m.get("planned_scope_issues", 0):,}</td>
  <td class="num">{m.get("completed_issues", 0):,}</td>
  <td class="num open">{open_cnt:,}</td>
  <td class="num muted">{pct if pct is not None else "—"}%</td>
  <td class="num">{est_planned_s}</td>
  <td class="num">{est_done_s}</td>
  <td class="num">{est_badge}</td>
</tr>"""
        )

    html = f"""<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="utf-8" />
  <meta name="viewport" content="width=device-width, initial-scale=1" />
  <title>Sprint matrix — scope vs completion</title>
  <style>
    :root {{
      --bg: #0f1419;
      --surface: #1a2332;
      --surface2: #243044;
      --text: #e7ecf3;
      --muted: #8b9cb3;
      --accent: #5b9fd4;
      --border: #2d3d52;
      --good: #3d9a6d;
      --good-bg: rgba(61, 154, 109, 0.15);
      --mid: #c9a227;
      --mid-bg: rgba(201, 162, 39, 0.15);
      --low: #c44c4c;
      --low-bg: rgba(196, 76, 76, 0.15);
      --font: "Segoe UI", system-ui, -apple-system, sans-serif;
    }}
    * {{ box-sizing: border-box; }}
    body {{
      margin: 0;
      font-family: var(--font);
      background: var(--bg);
      color: var(--text);
      line-height: 1.5;
      font-size: 15px;
    }}
    .wrap {{ max-width: 1280px; margin: 0 auto; padding: 2rem 1.5rem 3rem; }}
    header {{
      border-bottom: 1px solid var(--border);
      padding-bottom: 1.5rem;
      margin-bottom: 2rem;
    }}
    h1 {{
      font-size: 1.75rem;
      font-weight: 600;
      margin: 0 0 0.35rem;
      letter-spacing: -0.02em;
    }}
    .subtitle {{ color: var(--muted); font-size: 0.95rem; margin: 0; }}
    .subtitle a {{ color: var(--accent); text-decoration: none; }}
    .subtitle a:hover {{ text-decoration: underline; }}

    .method {{
      background: var(--surface);
      border: 1px solid var(--border);
      border-radius: 10px;
      padding: 1rem 1.25rem;
      margin-bottom: 2rem;
      font-size: 0.9rem;
      color: var(--muted);
    }}
    .method strong {{ color: var(--text); }}
    .method ul {{ margin: 0.5rem 0 0; padding-left: 1.25rem; }}

    .cards {{
      display: grid;
      grid-template-columns: repeat(auto-fill, minmax(220px, 1fr));
      gap: 1rem;
      margin-bottom: 2rem;
    }}
    .card {{
      background: var(--surface);
      border: 1px solid var(--border);
      border-radius: 10px;
      padding: 1rem 1.15rem;
    }}
    .card-label {{
      font-size: 0.8rem;
      color: var(--muted);
      text-transform: uppercase;
      letter-spacing: 0.04em;
      margin-bottom: 0.35rem;
    }}
    .card-stat {{ margin-bottom: 0.35rem; }}
    .card-stat .big {{ font-size: 1.75rem; font-weight: 700; color: var(--text); }}
    .card-stat .unit {{ font-size: 0.85rem; color: var(--muted); margin-left: 0.25rem; }}
    .card-meta {{ font-size: 0.8rem; color: var(--muted); }}

    h2 {{
      font-size: 1.1rem;
      font-weight: 600;
      margin: 0 0 1rem;
      color: var(--text);
    }}

    .table-scroll {{
      overflow-x: auto;
      border: 1px solid var(--border);
      border-radius: 10px;
      background: var(--surface);
    }}
    table {{
      width: 100%;
      border-collapse: collapse;
      min-width: 1100px;
    }}
    thead th {{
      text-align: left;
      font-size: 0.72rem;
      text-transform: uppercase;
      letter-spacing: 0.06em;
      color: var(--muted);
      background: var(--surface2);
      padding: 0.85rem 1rem;
      border-bottom: 1px solid var(--border);
      white-space: nowrap;
    }}
    th.num, td.num {{ text-align: right; }}
    tbody td {{
      padding: 0.65rem 1rem;
      border-bottom: 1px solid var(--border);
      vertical-align: top;
    }}
    tbody tr:last-child td {{ border-bottom: none; }}
    tbody tr:hover td {{ background: rgba(91, 159, 212, 0.06); }}
    .product {{ font-weight: 500; white-space: nowrap; }}
    .sprints {{ font-size: 0.88rem; color: #b8c5d6; max-width: 320px; }}
    .open {{ color: #e0a84f; }}
    .muted {{ color: var(--muted); font-size: 0.9rem; }}
    .sp {{ font-size: 0.88rem; }}

    .badge {{
      display: inline-block;
      padding: 0.2rem 0.55rem;
      border-radius: 6px;
      font-weight: 600;
      font-size: 0.85rem;
    }}
    .pct-good {{ background: var(--good-bg); color: #6dccb0; }}
    .pct-mid {{ background: var(--mid-bg); color: #e8c65c; }}
    .pct-low {{ background: var(--low-bg); color: #e88a8a; }}
    .pct-na {{ background: var(--surface2); color: var(--muted); }}

    .row-error td {{ background: rgba(196, 76, 76, 0.08); }}
    .err {{ color: #e88a8a; font-size: 0.88rem; }}

    .pivot-wrap table.pivot {{ min-width: 520px; }}
    .pivot-note {{ color: var(--muted); font-size: 0.9rem; margin: -0.5rem 0 1rem; }}
    tr.pivot-footer td {{ background: var(--surface2); border-top: 2px solid var(--border); }}

    .all-products-p1 h3 {{
      font-size: 1rem;
      font-weight: 600;
      margin: 1.5rem 0 0.75rem;
      color: var(--text);
    }}
    .wide-p1-monthly table {{ min-width: 1180px; }}
    details.jql-verify {{ margin: 1rem 0 1.5rem; }}
    details.jql-verify summary {{ cursor: pointer; color: var(--accent); }}
    details.jql-verify summary:hover {{ text-decoration: underline; }}
    details.jql-verify pre {{
      margin: 0.5rem 0 1rem;
      padding: 0.75rem 1rem;
      background: var(--surface2);
      border: 1px solid var(--border);
      border-radius: 8px;
      overflow-x: auto;
      font-size: 0.82rem;
      line-height: 1.45;
    }}
    details.jql-verify p {{ margin: 0.5rem 0; }}

    footer {{
      margin-top: 2rem;
      padding-top: 1rem;
      border-top: 1px solid var(--border);
      font-size: 0.8rem;
      color: var(--muted);
    }}
    @media print {{
      body {{ background: #fff; color: #111; }}
      .wrap {{ max-width: none; padding: 0; }}
      :root {{
        --bg: #fff;
        --surface: #f6f8fb;
        --surface2: #e8ecf2;
        --text: #111;
        --muted: #555;
        --border: #ccc;
      }}
      .cards {{ break-inside: avoid; }}
      tbody tr:hover td {{ background: transparent; }}
    }}
  </style>
</head>
<body>
  <div class="wrap">
    <header>
      <h1>Sprint matrix — planned scope vs completed</h1>
      <p class="subtitle">Generated <strong>{esc(generated)}</strong> · Source <a href="{esc(base)}" target="_blank" rel="noopener">{esc(base)}</a></p>
    </header>

    <div class="method">
      <strong>Definitions</strong>
      <ul>
        <li><strong>Scope</strong> — issues matching each cell&rsquo;s JQL (sprint assignment in Jira).</li>
        <li><strong>Done</strong> — status category &ldquo;Done&rdquo; (includes Closed, Done, Closed without action, etc.).</li>
        <li><strong>Open</strong> — scope minus done (not yet in Done category).</li>
        <li><strong>Track (primary)</strong> — <strong>Original estimate</strong> hours from Jira (<code>timeoriginalestimate</code>): sum on Done issues ÷ sum on all in-scope issues. Missing estimate counts as 0. <strong>Est. %</strong> uses color bands; <strong>Issue %</strong> is shown for reference only.</li>
        <li><strong>Story points</strong> — not used for the track bar; SP may still exist on issues for backlog sizing only.</li>
        <li><strong>PHP / Go migration</strong> — no separate product row (project <code>GM</code>). Work scheduled in other teams&rsquo; sprints appears under those products; use <code>project = GM</code> for migration-only issues.</li>
      </ul>
    </div>

{monthly_pivot_html}

{escape_p1_html}

{all_products_p1_html}

    <h2>By product (original-estimate hours done % — weighted across sprint cells)</h2>
    <div class="cards">
{summary_cards}
    </div>

    <h2>Full matrix</h2>
    <div class="table-scroll">
      <table>
        <thead>
          <tr>
            <th>Product</th>
            <th>Month</th>
            <th>Sprint(s)</th>
            <th class="num">Scope</th>
            <th class="num">Done</th>
            <th class="num">Open</th>
            <th class="num">Issue %</th>
            <th class="num">Est. h</th>
            <th class="num">Est. h done</th>
            <th class="num">Est. %</th>
          </tr>
        </thead>
        <tbody>
{"".join(table_rows)}
        </tbody>
      </table>
    </div>

    <footer>
      Regenerate: <code>python build_sprint_matrix_report.py</code> ·
      <code>python sprint_matrix_monthly_pivot.py</code> (TSV/MD) ·
      <code>python escape_p1_open_monthly.py</code> (P1 Escape per sprint) ·
      <code>python all_products_p1_escape_metrics.py</code> (all products WIP + monthly inflow) ·
      <code>python render_sprint_matrix_html.py</code>
    </footer>
  </div>
</body>
</html>
"""

    HTML_PATH.write_text(html, encoding="utf-8")
    print(f"Wrote {HTML_PATH}")


if __name__ == "__main__":
    main()
