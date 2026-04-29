"""
P1 Escape Defect metrics for all product lines (same logic as filter_p1_escape_metrics.py):
- WIP: Escape Defect + P1 + statusCategory != Done
- Cap: FILTER_P1_MAX_CONCURRENT (default 3) applied to every product for comparison
- Monthly inflow: created in calendar month (year = FILTER_METRIC_YEAR)

Outputs:
  all_products_p1_escape_metrics.json
  all_products_p1_escape_metrics.md
  (HTML section via format_all_products_p1_html — consumed by render_sprint_matrix_html.py)
"""
from __future__ import annotations

import base64
import datetime
import json
import os
import sys
import time
import urllib.request
from typing import Any

ROOT = __file__.rsplit(os.sep, 1)[0]

MAX_CONCURRENT = int(os.environ.get("FILTER_P1_MAX_CONCURRENT", "3"))
YEAR = int(os.environ.get("FILTER_METRIC_YEAR", str(datetime.date.today().year)))

# Report label -> Jira project key (same mapping as sprint matrix)
PRODUCTS: list[tuple[str, str]] = [
    ("AIChat", "AICHAT"),
    ("FLEX & COM", "FLEX"),
    ("PASS", "PASS"),
    ("Platform", "PLATFORM"),
    ("product_aware", "AWARE"),
    ("product_FILTER", "FILTER"),
    ("product_home", "HOME"),
    ("product_MDM_CLASSROOM", "MDMCLASS"),
    ("product_oncall", "PRODUCT24"),
    ("product_RESPOND", "RESP"),
]


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
        time.sleep(0.1)
    return out


def count_created_month(
    base: str, project_key: str, start: datetime.date, end: datetime.date
) -> int:
    jql = (
        f'project = {project_key} AND issuetype = "Escape Defect" AND priority = P1 '
        f"AND created >= {start.isoformat()} AND created <= {end.isoformat()}"
    )
    return len(fetch_all_issues(base, jql, ["key"]))


def build() -> dict[str, Any]:
    base = os.environ.get("JIRA_URL", "").rstrip("/")
    if not base:
        print("Set JIRA_URL, JIRA_EMAIL, JIRA_API_TOKEN", file=sys.stderr)
        sys.exit(1)

    month_labels = []
    for month in range(1, 13):
        d = datetime.date(YEAR, month, 1)
        month_labels.append(d.strftime("%b %Y"))

    products_out: list[dict[str, Any]] = []
    comparison_wip: list[dict[str, Any]] = []
    comparison_monthly: list[dict[str, Any]] = []

    for label, pkey in PRODUCTS:
        jql_wip = (
            f'project = {pkey} AND issuetype = "Escape Defect" AND priority = P1 '
            "AND statusCategory != Done"
        )
        wip_issues = fetch_all_issues(
            base,
            jql_wip,
            ["key", "summary", "status", "priority"],
        )
        wip_count = len(wip_issues)
        compliant = wip_count <= MAX_CONCURRENT

        monthly: dict[str, int] = {}
        for month in range(1, 13):
            start = datetime.date(YEAR, month, 1)
            if month == 12:
                end = datetime.date(YEAR, 12, 31)
            else:
                end = datetime.date(YEAR, month + 1, 1) - datetime.timedelta(days=1)
            ml = month_labels[month - 1]
            monthly[ml] = count_created_month(base, pkey, start, end)

        ytd_total = sum(monthly.values())

        row = {
            "product_label": label,
            "jira_project": pkey,
            "wip_jql": jql_wip,
            "wip_count": wip_count,
            "max_concurrent": MAX_CONCURRENT,
            "compliant": compliant,
            "wip_status": "PASS" if compliant else "FAIL",
            "monthly_opened": monthly,
            "ytd_opened_total": ytd_total,
            "open_issues": [
                {
                    "key": i["key"],
                    "status": ((i.get("fields") or {}).get("status") or {}).get("name"),
                    "summary": (i.get("fields") or {}).get("summary"),
                }
                for i in wip_issues
            ],
        }
        products_out.append(row)
        comparison_wip.append(
            {
                "Product": label,
                "Jira": pkey,
                "WIP": wip_count,
                "Cap": MAX_CONCURRENT,
                "Status": row["wip_status"],
            }
        )
        comparison_monthly.append(
            {
                "Product": label,
                "Jira": pkey,
                **{ml: monthly[ml] for ml in month_labels},
                "YTD": ytd_total,
            }
        )

    return {
        "generated_at": datetime.datetime.now(datetime.timezone.utc).isoformat(),
        "jira_base": base,
        "year": YEAR,
        "cap": MAX_CONCURRENT,
        "methodology": {
            "wip": "Escape Defect + P1 + statusCategory != Done",
            "monthly": "Escape Defect + P1 + created in calendar month",
        },
        "products": products_out,
        "comparison_wip": comparison_wip,
        "comparison_monthly": comparison_monthly,
    }


def write_md(data: dict[str, Any]) -> str:
    lines = [
        "# P1 Escape Defect metrics — all products (comparison)",
        "",
        f"**Year:** {data['year']} · **WIP cap (comparison):** ≤ {data['cap']} · **Snapshot:** {data['generated_at']}",
        "",
        "## WIP vs cap (concurrent open)",
        "",
        "| Product | Jira | WIP | Cap | Status |",
        "|---------|------|----:|----:|--------|",
    ]
    for r in data["comparison_wip"]:
        lines.append(
            "| {p} | `{j}` | {w} | {c} | **{s}** |".format(
                p=r["Product"],
                j=r["Jira"],
                w=r["WIP"],
                c=r["Cap"],
                s=r["Status"],
            )
        )
    lines.append("")
    lines.append(f"## Monthly inflow ({data['year']}) — created per month (P1 Escape Defect)")
    lines.append("")
    month_keys = [
        datetime.date(data["year"], m, 1).strftime("%b %Y") for m in range(1, 13)
    ]
    header = "| Product | Jira | " + " | ".join(month_keys) + " | YTD |"
    sep = "|---------|------|" + "|".join([":---:"] * 12) + "| :---: |"
    lines.append(header)
    lines.append(sep)
    for r in data["comparison_monthly"]:
        cells = [r["Product"], f"`{r['Jira']}`"] + [str(r[k]) for k in month_keys] + [
            str(r["YTD"])
        ]
        lines.append("| " + " | ".join(cells) + " |")
    lines.append("")
    lines.append("## Open issues by product (WIP detail)")
    lines.append("")
    for p in data["products"]:
        lines.append(f"### {p['product_label']} (`{p['jira_project']}`) — WIP {p['wip_count']}")
        lines.append("")
        if not p["open_issues"]:
            lines.append("_None._")
        else:
            lines.append("| Key | Status | Summary |")
            lines.append("|-----|--------|---------|")
            for o in p["open_issues"]:
                sm = (o.get("summary") or "").replace("|", "\\|")[:100]
                lines.append(f"| {o['key']} | {o.get('status')} | {sm} |")
        lines.append("")
    lines.append("## JQL (WIP)")
    lines.append("")
    lines.append("```")
    lines.append(
        'project = <KEY> AND issuetype = "Escape Defect" AND priority = P1 AND statusCategory != Done'
    )
    lines.append("```")
    lines.append("")
    return "\n".join(lines)


def _html_esc(s: str) -> str:
    return (
        s.replace("&", "&amp;")
        .replace("<", "&lt;")
        .replace(">", "&gt;")
        .replace('"', "&quot;")
    )


def _month_bounds_for_year(year: int) -> list[tuple[str, str, str]]:
    """(label %b %Y, created >=, created <=) for each calendar month."""
    rows: list[tuple[str, str, str]] = []
    for month in range(1, 13):
        start = datetime.date(year, month, 1)
        if month == 12:
            end = datetime.date(year, 12, 31)
        else:
            end = datetime.date(year, month + 1, 1) - datetime.timedelta(days=1)
        rows.append((start.strftime("%b %Y"), start.isoformat(), end.isoformat()))
    return rows


def format_all_products_p1_html(data: dict[str, Any]) -> str:
    """Standalone HTML fragment for sprint_matrix_report.html (expects build() JSON shape)."""
    year = int(data["year"])
    cap = data["cap"]
    snap = _html_esc(str(data.get("generated_at", "")))
    meth = data.get("methodology", {})
    wip_desc = _html_esc(str(meth.get("wip", "")))
    mo_desc = _html_esc(str(meth.get("monthly", "")))

    wip_body: list[str] = []
    for r in data["comparison_wip"]:
        badge_cls = "pct-good" if r["Status"] == "PASS" else "pct-low"
        wip_body.append(
            "<tr>"
            f'<td class="product">{_html_esc(r["Product"])}</td>'
            f'<td><code>{_html_esc(r["Jira"])}</code></td>'
            f'<td class="num">{r["WIP"]}</td>'
            f'<td class="num">{r["Cap"]}</td>'
            f'<td class="num"><span class="badge {badge_cls}">{_html_esc(r["Status"])}</span></td>'
            "</tr>"
        )

    cm = data["comparison_monthly"]
    if not cm:
        return '<p class="err">No comparison_monthly data.</p>'
    first = cm[0]
    month_keys = [k for k in first if k not in ("Product", "Jira", "YTD")]

    mo_head = "".join(f'<th class="num">{_html_esc(k)}</th>' for k in month_keys)
    mo_rows: list[str] = []
    for r in cm:
        cells = "".join(f'<td class="num">{r[k]}</td>' for k in month_keys)
        mo_rows.append(
            "<tr>"
            f'<td class="product">{_html_esc(r["Product"])}</td>'
            f'<td><code>{_html_esc(r["Jira"])}</code></td>'
            f"{cells}"
            f'<td class="num"><strong>{r["YTD"]}</strong></td>'
            "</tr>"
        )

    bounds_rows = []
    for label, ge, le in _month_bounds_for_year(year):
        bounds_rows.append(
            "<tr>"
            f"<td>{_html_esc(label)}</td>"
            f"<td><code>{_html_esc(ge)}</code></td>"
            f"<td><code>{_html_esc(le)}</code></td>"
            "</tr>"
        )
    bounds_tbody = "\n".join(bounds_rows)

    return (
        '<section class="all-products-p1">\n'
        f'<h2>P1 Escape Defect — all products (WIP vs cap &amp; monthly inflow, {year})</h2>\n'
        f'<p class="subtitle pivot-note">Snapshot <strong>{snap}</strong>. '
        f"<strong>WIP:</strong> {wip_desc}. <strong>Cap (comparison):</strong> ≤ {cap}. "
        f"<strong>Monthly inflow:</strong> {mo_desc}.</p>\n"
        "<h3>WIP vs cap (concurrent open)</h3>\n"
        '<div class="table-scroll">\n'
        "  <table>\n"
        "    <thead><tr>"
        "<th>Product</th><th>Jira</th>"
        '<th class="num">WIP</th><th class="num">Cap</th><th class="num">Status</th>'
        "</tr></thead>\n"
        "    <tbody>\n"
        + "\n".join(wip_body)
        + "\n    </tbody>\n  </table>\n</div>\n"
        "<h3>Monthly inflow — P1 Escape Defect created per month</h3>\n"
        '<div class="table-scroll wide-p1-monthly">\n'
        "  <table>\n"
        "    <thead><tr>"
        "<th>Product</th><th>Jira</th>"
        f"{mo_head}"
        '<th class="num">YTD</th>'
        "</tr></thead>\n"
        "    <tbody>\n"
        + "\n".join(mo_rows)
        + "\n    </tbody>\n  </table>\n</div>\n"
        '<details class="method jql-verify">\n'
        "  <summary><strong>JQL — verify monthly inflow in Jira</strong></summary>\n"
        "  <p>Replace <code>PROJECT_KEY</code> with the Jira project column above. "
        "Issue counts should match each month column (and YTD = full-year query).</p>\n"
        "  <pre><code>"
        "project = PROJECT_KEY AND issuetype = &quot;Escape Defect&quot; AND priority = P1 "
        "AND created &gt;= YYYY-MM-DD AND created &lt;= YYYY-MM-DD"
        "</code></pre>\n"
        f"  <p><strong>Example ({year} April, FILTER):</strong></p>\n"
        "  <pre><code>"
        f"project = FILTER AND issuetype = &quot;Escape Defect&quot; AND priority = P1 "
        f"AND created &gt;= {year}-04-01 AND created &lt;= {year}-04-30"
        "</code></pre>\n"
        f"  <p><strong>{year} <code>created</code> date range per month</strong> (inclusive, same as this report):</p>\n"
        '  <div class="table-scroll">\n'
        "    <table>\n"
        "      <thead><tr><th>Month</th><th><code>created &gt;=</code></th>"
        "<th><code>created &lt;=</code></th></tr></thead>\n"
        "      <tbody>\n"
        f"{bounds_tbody}\n"
        "      </tbody>\n"
        "    </table>\n"
        "  </div>\n"
        "  <p><strong>WIP (concurrent)</strong> uses:</p>\n"
        "  <pre><code>"
        "project = PROJECT_KEY AND issuetype = &quot;Escape Defect&quot; AND priority = P1 "
        "AND statusCategory != Done"
        "</code></pre>\n"
        "</details>\n"
        "</section>\n"
    )


def main() -> None:
    data = build()
    jp = os.path.join(ROOT, "all_products_p1_escape_metrics.json")
    mp = os.path.join(ROOT, "all_products_p1_escape_metrics.md")
    with open(jp, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2)
    with open(mp, "w", encoding="utf-8") as f:
        f.write(write_md(data))
    print(f"Wrote {jp}")
    print(f"Wrote {mp}")


if __name__ == "__main__":
    main()
