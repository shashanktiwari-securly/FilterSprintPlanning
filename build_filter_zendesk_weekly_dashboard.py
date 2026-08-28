"""Render the Zendesk weekly dashboard as standalone HTML + Markdown.

Reads reports/filter-zendesk-weekly-dashboard.json and writes:

  reports/filter-zendesk-weekly-dashboard.html
  reports/filter-zendesk-weekly-dashboard.md
  docs/index.html   (same HTML, for GitHub Pages)
"""

from __future__ import annotations

import json
from datetime import datetime
from pathlib import Path

ROOT = Path(__file__).resolve().parent
JSON_PATH = ROOT / "reports" / "filter-zendesk-weekly-dashboard.json"
HTML_PATH = ROOT / "reports" / "filter-zendesk-weekly-dashboard.html"
MD_PATH = ROOT / "reports" / "filter-zendesk-weekly-dashboard.md"
DOCS_PATH = ROOT / "docs" / "index.html"


def esc(s: object) -> str:
    return (
        str(s)
        .replace("&", "&amp;")
        .replace("<", "&lt;")
        .replace(">", "&gt;")
        .replace('"', "&quot;")
    )


def md_row(cells: list[object]) -> str:
    return "| " + " | ".join(str(c) for c in cells) + " |"


def fmt_days(value: object) -> str:
    if value is None or value == "":
        return "—"
    try:
        days = float(value)
    except (TypeError, ValueError):
        return "—"
    if days < 1:
        return f"{days * 24:.1f}h"
    return f"{days:.1f}d"


def created_from_label(data: dict) -> str:
    filters = data.get("filters") or {}
    if filters.get("created_from_label"):
        return filters["created_from_label"]
    raw = filters.get("created_from") or "2026-08-01"
    try:
        dt = datetime.fromisoformat(raw)
    except ValueError:
        return raw
    return f"{dt.day} {dt.strftime('%b')} {dt.year}"


def write_markdown(data: dict) -> str:
    k = data["kpis"]
    projects = sorted(data["projects"], key=lambda p: p["label"].lower())
    product_kpis = sorted(data["product_kpis"], key=lambda p: p["label"].lower())
    from_label = created_from_label(data)
    lines = [
        f"# {data['title']}",
        "",
        f"Snapshot **{data['snapshot_date']}** · {len(projects)} products · "
        f"Escape Defect + Support Request · Zendesk Ticket Count > 0 · weekly from **{data['filters']['created_from']}**.",
        "",
        "## Headline",
        "",
        data.get("headline")
        or (
            f"**{k['created']}** Zendesk-linked tickets created since {from_label} "
            f"({k['created_escape_defect']} Escape Defect, {k['created_support_request']} Support Request). "
            f"**{k['created_done']}** Done · **{k['created_open']}** still open."
        ),
        "",
        "## Done vs not Done",
        "",
        f"**{k['created_done']}** tickets are `statusCategory = Done` "
        f"({k.get('done_pct', 0)}%). "
        f"**{k['created_open']}** are `statusCategory != Done` "
        f"({k.get('not_done_pct', 0)}%).",
        "",
        md_row(["Product", "Key", "Created", "Done", "Not Done", "Done %", "Not Done %"]),
        md_row(["---", "---", "---:", "---:", "---:", "---:", "---:"]),
    ]
    for p in product_kpis:
        lines.append(
            md_row(
                [
                    p["label"],
                    p["key"],
                    p["created"],
                    p["done"],
                    p["open"],
                    f"{p.get('done_pct', 0)}%",
                    f"{p.get('not_done_pct', 0)}%",
                ]
            )
        )
    lines += [
        "",
        "## By product",
        "",
        md_row(["Product", "Key", "Created", "Escape Defect", "Support Request", "Done", "Not Done"]),
        md_row(["---", "---", "---:", "---:", "---:", "---:", "---:"]),
    ]
    for p in product_kpis:
        lines.append(
            md_row(
                [
                    p["label"],
                    p["key"],
                    p["created"],
                    p["escape_defect"],
                    p["support_request"],
                    p["done"],
                    p["open"],
                ]
            )
        )
    lines += [
        "",
        "## Weekly created",
        "",
    ]
    header = ["Week", "Slice"] + [p["label"] for p in projects] + ["Total"]
    lines.append(md_row(header))
    lines.append(md_row(["---", "---"] + [":---:" for _ in header[2:]]))
    for m in data.get("weekly") or data.get("monthly") or []:
        label = m["label"] + (" (partial)" if m.get("partial") else "")
        created_cells = [label, "Created"]
        done_cells = [label, "Done"]
        open_cells = [label, "Not Done"]
        for p in projects:
            bp = m["by_project"][p["key"]]
            created_cells.append(bp["created"])
            done_cells.append(bp["done"])
            open_cells.append(bp["open"])
        created_cells.append(m["totals"]["created"])
        done_cells.append(m["totals"]["done"])
        open_cells.append(m["totals"]["open"])
        lines.append(md_row(created_cells))
        lines.append(md_row(done_cells))
        lines.append(md_row(open_cells))
    lines += [
        "",
        "## Created ticket list",
        "",
        md_row(["Week", "Product", "Key", "Type", "P", "ZD", "Created", "Status", "Assignee", "Summary"]),
        md_row(["---", "---", "---", "---", "---", "---:", "---", "---", "---", "---"]),
    ]
    for issue in data["created_issues"]:
        week = (issue.get("created_week") or issue.get("created_month") or {})
        period = week.get("label") or ""
        lines.append(
            md_row(
                [
                    period,
                    issue["project_label"],
                    f"[{issue['key']}]({issue['url']})",
                    issue["type"],
                    issue["priority"] or "",
                    issue["zendesk_count"],
                    issue["created_date"],
                    issue["status"],
                    issue["assignee"],
                    issue["summary"].replace("|", "/"),
                ]
            )
        )
    lines += [
        "",
        "## Live Jira views",
        "",
        f"- [Created since {from_label}]({data['links']['created']})",
        f"- [statusCategory != Done]({data['links']['created_open']})",
        f"- [statusCategory = Done]({data['links']['created_done']})",
        "",
        "## Notes",
        "",
        f"- {data['notes'].get('scope', '')}",
        f"- {data['notes'].get('window', '')}",
        f"- JQL: `{data['jql']['created']}`",
        "",
    ]
    return "\n".join(lines)


def write_html(data: dict) -> str:
    payload = json.dumps(data, ensure_ascii=True)
    from_label = created_from_label(data)
    title = esc(data["title"])
    head = f"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="utf-8"/>
<meta name="viewport" content="width=device-width, initial-scale=1"/>
<meta http-equiv="Cache-Control" content="no-store"/>
<title>{title}</title>
<script>
(function(){{
  try {{
    if (localStorage.getItem('zd-dashboard-theme') === 'light') {{
      document.documentElement.setAttribute('data-theme','light');
    }}
  }} catch (e) {{}}
}})();
</script>
<style>
  :root {{
    --bg:#0f172a; --panel:#1e293b; --panel2:#273449; --ink:#e2e8f0; --muted:#94a3b8;
    --line:#334155; --good:#22c55e; --ok:#84cc16; --warn:#eab308; --bad:#f97316; --crit:#ef4444;
    --accent:#38bdf8; --created:#38bdf8; --header-bg:linear-gradient(180deg,#111c33,#0f172a);
    --hover:#20304a; --row-done:#13261c; --row-open:#2a2410; --track:#334155;
    --tab-active-bg:#0ea5e9; --tab-active-ink:#04283b;
  }}
  html[data-theme="light"] {{
    --bg:#f1f5f9; --panel:#ffffff; --panel2:#e2e8f0; --ink:#0f172a; --muted:#475569;
    --line:#cbd5e1; --accent:#0369a1; --created:#0284c7;
    --header-bg:linear-gradient(180deg,#ffffff,#f8fafc);
    --hover:#e2e8f0; --row-done:#dcfce7; --row-open:#fef3c7; --track:#cbd5e1;
    --tab-active-bg:#0284c7; --tab-active-ink:#ffffff;
  }}
  * {{ box-sizing:border-box; }}
  body {{ margin:0; background:var(--bg); color:var(--ink);
    font-family:-apple-system,BlinkMacSystemFont,"Segoe UI",Roboto,Helvetica,Arial,sans-serif; font-size:14px; }}
  header {{ padding:24px 28px; border-bottom:1px solid var(--line);
    background:var(--header-bg); }}
  .header-row {{ display:flex; justify-content:space-between; align-items:flex-start; gap:16px; }}
  .header-actions {{ display:flex; gap:8px; flex-shrink:0; }}
  .theme-toggle {{
    background:var(--panel2); color:var(--ink); border:1px solid var(--line);
    border-radius:999px; padding:8px 14px; cursor:pointer; font-size:13px; font-weight:600;
    white-space:nowrap; flex-shrink:0;
  }}
  .theme-toggle:hover {{ border-color:var(--accent); color:var(--accent); }}
  h1 {{ margin:0 0 6px; font-size:22px; }}
  .sub {{ color:var(--muted); font-size:13px; line-height:1.5; }}
  .sub a {{ color:var(--accent); text-decoration:none; }}
  .sub a:hover {{ text-decoration:underline; }}
  #liveStatus {{ font-weight:600; }}
  #liveStatus.ok {{ color:var(--good); }}
  #liveStatus.stale {{ color:var(--warn); }}
  .wrap {{ padding:20px 28px 60px; max-width:1800px; margin:0 auto; }}
  .cards {{ display:flex; gap:10px; flex-wrap:wrap; margin:18px 0 12px; }}
  .cards.overview {{ margin-bottom:16px; }}
  .cards.overview .card {{ min-width:200px; flex:1 1 220px; }}
  .cards.products {{ display:grid; grid-template-columns:repeat(7, minmax(0,1fr)); gap:10px; margin:0 0 26px; }}
  .card {{ background:var(--panel); border:1px solid var(--line); border-radius:12px; padding:14px 16px; min-width:128px; flex:1 1 128px; }}
  .cards.products .card {{ min-width:0; flex:unset; }}
  @media (max-width:1200px) {{
    .cards.products {{ grid-template-columns:repeat(4, minmax(0,1fr)); }}
  }}
  .card .n {{ font-size:26px; font-weight:700; }}
  .card .l {{ color:var(--muted); font-size:12px; margin-top:2px; }}
  .card.warn .n {{ color:var(--warn); }}
  .card.good .n {{ color:var(--good); }}
  .card.done {{ border-color:#166534; }}
  .card.open {{ border-color:#a16207; }}
  .split {{ display:flex; height:8px; border-radius:999px; overflow:hidden; background:var(--track); margin-top:8px; }}
  .split .done {{ background:var(--good); }}
  .split .open {{ background:var(--warn); }}
  .cmp {{ display:grid; grid-template-columns:minmax(110px,140px) 1fr 90px; gap:8px 14px; align-items:center;
    background:var(--panel); border:1px solid var(--line); border-radius:12px; padding:16px 18px; }}
  .cmp.avg {{ grid-template-columns:minmax(110px,140px) 1fr 120px; }}
  .bar.stack {{ display:flex; height:14px; border-radius:7px; overflow:hidden; background:var(--track); }}
  .bar.stack .done {{ background:var(--good); height:100%; }}
  .bar.stack .open {{ background:var(--warn); height:100%; }}
  .bar.stack .avg {{ background:var(--accent); height:100%; }}
  .cmp-meta {{ font-size:12px; font-variant-numeric:tabular-nums; white-space:nowrap; }}
  .cmp-meta .done {{ color:var(--good); font-weight:700; }}
  .cmp-meta .open {{ color:var(--warn); font-weight:700; }}
  td.done, th.done {{ color:var(--good); }}
  td.open, th.open {{ color:var(--warn); }}
  tr.row-done td {{ background:var(--row-done); }}
  tr.row-open td {{ background:var(--row-open); }}
  tr.row-label td {{ color:var(--muted); font-weight:600; }}
  .legend .swatch {{ display:inline-block; width:10px; height:10px; border-radius:2px; margin:0 4px 0 10px; vertical-align:middle; }}
  .legend .swatch.done {{ background:var(--good); }}
  .legend .swatch.open {{ background:var(--warn); }}
  .legend .swatch.avg {{ background:var(--accent); }}
  h2 {{ font-size:16px; margin:30px 0 12px; border-left:3px solid var(--accent); padding-left:10px; }}
  table {{ border-collapse:collapse; width:100%; background:var(--panel); border-radius:10px; overflow:hidden; }}
  th, td {{ padding:9px 11px; text-align:left; border-bottom:1px solid var(--line); }}
  th {{ background:var(--panel2); color:var(--muted); font-weight:600; font-size:12px;
    text-transform:uppercase; letter-spacing:.03em; position:sticky; top:0; }}
  th.sortable {{ cursor:pointer; user-select:none; white-space:nowrap; }}
  th.sortable:hover {{ color:var(--ink); }}
  th.sortable .arrow {{ margin-left:4px; opacity:.35; font-size:10px; }}
  th.sortable.active {{ color:var(--ink); }}
  th.sortable.active .arrow {{ opacity:1; color:var(--accent); }}
  td.num, th.num {{ text-align:right; font-variant-numeric:tabular-nums; white-space:nowrap; }}
  tr:hover td {{ background:var(--hover); }}
  .scroll {{ overflow-x:auto; }}
  .pill {{ display:inline-block; padding:2px 8px; border-radius:999px; font-weight:700; font-size:11px; }}
  .p-ed {{ background:#7c3aed; color:#f5f3ff; }}
  .p-sr {{ background:#0369a1; color:#e0f2fe; }}
  .p-p1 {{ background:var(--crit); color:#fff; }}
  .p-p2 {{ background:var(--warn); color:#0b1220; }}
  .p-p3 {{ background:#334155; color:#cbd5e1; }}
  .st-done {{ background:#14532d; color:#bbf7d0; }}
  .st-progress {{ background:#854d0e; color:#fef08a; }}
  .st-todo {{ background:#1e3a5f; color:#bfdbfe; }}
  .p-filter {{ background:#0e7490; color:#ecfeff; }}
  .p-aware {{ background:#6d28d9; color:#f5f3ff; }}
  .p-oncall {{ background:#b45309; color:#fffbeb; }}
  .p-respond {{ background:#047857; color:#ecfdf5; }}
  .p-aichat {{ background:#4f46e5; color:#eef2ff; }}
  .p-pass {{ background:#0f766e; color:#ccfbf1; }}
  .p-flex {{ background:#be185d; color:#fce7f3; }}
  .p-comm {{ background:#475569; color:#e2e8f0; }}
  .p-mdm {{ background:#c2410c; color:#ffedd5; }}
  .p-pagescan {{ background:#4d7c0f; color:#ecfccb; }}
  .p-dd {{ background:#a21caf; color:#fae8ff; }}
  .p-de {{ background:#0369a1; color:#e0f2fe; }}
  .p-devops {{ background:#334155; color:#cbd5e1; }}
  .p-home {{ background:#9f1239; color:#ffe4e6; }}
  .links {{ display:flex; flex-wrap:wrap; gap:8px; margin:8px 0 18px; }}
  .links a {{ background:var(--panel2); border:1px solid var(--line); color:var(--accent);
    text-decoration:none; border-radius:8px; padding:6px 10px; font-size:12px; }}
  .links a:hover {{ border-color:var(--accent); }}
  .chart {{ display:grid; grid-template-columns:120px 1fr; gap:10px 16px; align-items:center;
    background:var(--panel); border:1px solid var(--line); border-radius:12px; padding:16px 18px; }}
  .bar {{ height:12px; border-radius:6px; background:var(--track); overflow:hidden; }}
  .bar > i {{ display:block; height:100%; background:var(--created); }}
  .bar-meta {{ color:var(--muted); font-size:12px; font-variant-numeric:tabular-nums; margin-top:4px; }}
  .legend {{ color:var(--muted); font-size:12px; margin:8px 0 0; }}
  .legend b {{ color:var(--ink); }}
  .controls {{ display:flex; flex-wrap:wrap; gap:8px; margin:8px 0 14px; align-items:center; }}
  select, input {{ background:var(--panel2); color:var(--ink); border:1px solid var(--line);
    border-radius:8px; padding:7px 10px; font-size:13px; }}
  input {{ min-width:220px; }}
  .tabs {{ display:flex; gap:6px; margin:8px 0 14px; }}
  .tabs button {{ background:var(--panel2); color:var(--ink); border:1px solid var(--line);
    border-radius:8px; padding:7px 12px; cursor:pointer; }}
  .tabs button.active {{ background:var(--tab-active-bg); color:var(--tab-active-ink); border-color:var(--tab-active-bg); font-weight:700; }}
  a.key {{ color:var(--accent); text-decoration:none; font-weight:600; }}
  a.key:hover {{ text-decoration:underline; }}
  .note {{ color:var(--muted); font-size:12px; margin-top:10px; }}
  code {{ background:var(--panel2); padding:1px 5px; border-radius:4px; }}
  footer {{ color:var(--muted); font-size:12px; padding:22px 28px; border-top:1px solid var(--line); }}
  .jira-panel {{
    display:none; margin:12px 28px 0; padding:14px 16px; background:var(--panel);
    border:1px solid var(--line); border-radius:10px; flex-wrap:wrap; gap:8px; align-items:center;
  }}
  .jira-panel.open {{ display:flex; }}
  .jira-panel p {{ margin:0; color:var(--muted); font-size:12px; flex:1 1 320px; line-height:1.45; }}
  .jira-panel input {{ min-width:180px; }}
  .jira-panel a {{ color:var(--accent); font-size:12px; }}
  #jiraMsg {{ color:var(--warn); font-size:12px; }}
  .callout {{ background:var(--panel); border:1px solid var(--line); border-left:4px solid var(--warn);
    border-radius:10px; padding:12px 16px; margin:8px 0 20px; color:var(--muted); }}
  .callout b {{ color:var(--ink); }}
  .summary {{ max-width:720px; white-space:normal; }}
</style>
</head>
<body>
<header>
  <div class="header-row">
    <div>
      <h1>{title}</h1>
      <div class="sub">
        Escape Defects and Support Requests · <span id="prodCount"></span> products ·
        from 1 Aug 2026 · <span id="liveStatus">loading Jira…</span><br/>
        Source: <a href="https://securly.atlassian.net">securly.atlassian.net</a>
        · field <code>Zendesk Ticket Count</code> &gt; 0
        · grouped by calendar week (Mon–Sun)
      </div>
    </div>
    <div class="header-actions">
      <button type="button" id="jiraToggle" class="theme-toggle" aria-pressed="false">Connect Jira</button>
      <button type="button" id="themeToggle" class="theme-toggle" aria-pressed="false">Light mode</button>
    </div>
  </div>
</header>
<div id="jiraPanel" class="jira-panel">
  <p>
    Save a Jira API token in this browser so every refresh queries live ticket counts from
    <code>api.atlassian.com</code>. The token stays in local storage and is not uploaded to GitHub.
    Create a token at
    <a href="https://id.atlassian.com/manage-profile/security/api-tokens" target="_blank" rel="noopener">id.atlassian.com</a>.
  </p>
  <input id="jiraEmail" type="email" autocomplete="username" placeholder="you@securly.com"/>
  <input id="jiraToken" type="password" autocomplete="off" placeholder="Jira API token"/>
  <button type="button" id="jiraSave" class="theme-toggle">Save and refresh</button>
  <button type="button" id="jiraClear" class="theme-toggle">Disconnect</button>
  <span id="jiraMsg"></span>
</div>
<div class="wrap">
  <div class="links" id="links"></div>
  <div class="cards overview" id="overview"></div>
  <div class="cards products" id="cards"></div>
  <div class="callout" id="headline"></div>

  <h2>Done vs not Done</h2>
  <div class="legend">
    Comparison of Jira <b>statusCategory = Done</b> versus <b>statusCategory != Done</b>
    for the created cohort.
    <span class="swatch done"></span>Done
    <span class="swatch open"></span>Not Done
  </div>
  <div class="cmp" id="compareChart" style="margin-top:12px"></div>
  <div class="scroll" style="margin-top:16px"><table id="compare"></table></div>

  <h2>Weekly created by product</h2>
  <div class="legend">Each week is split into Created, Done, and Not Done so the statusCategory comparison is visible by week. Weeks run Monday–Sunday; the first and last weeks are clipped to the dashboard window and show that date range. On-Call (PRODUCT24) and Case Manager (RESP) stay in the table even when the count is 0. Products are listed alphabetically.</div>
  <div class="scroll" style="margin-top:16px"><table id="weekly"></table></div>

  <h2>Ticket list</h2>
  <div class="tabs">
    <button class="active" data-tab="created">Created since {esc(from_label)}</button>
    <button data-tab="open">Not Done</button>
    <button data-tab="done">Done</button>
  </div>
  <div class="controls">
    <select id="projFilter"><option value="all">All products</option></select>
    <select id="typeFilter">
      <option value="all">All types</option>
      <option value="Escape Defect">Escape Defect</option>
      <option value="Support Request">Support Request</option>
    </select>
    <select id="prioFilter">
      <option value="all">All priorities</option>
      <option value="P1">P1</option>
      <option value="P2">P2</option>
      <option value="P3">P3</option>
    </select>
    <select id="weekFilter"><option value="all">All weeks</option></select>
    <input id="search" placeholder="search key, summary, assignee…"/>
  </div>
  <div class="legend" id="count"></div>
  <div class="scroll"><table id="issues"></table></div>
  <p class="note" id="notes"></p>
</div>
<footer>
  Git-hosted report · Connect Jira once in this browser to pull live counts on every refresh
  · fallback snapshot in <code>docs/live.json</code>
  · also published at <code>docs/index.html</code> for GitHub Pages
</footer>
<script>
let DATA = {payload};
const $ = (id) => document.getElementById(id);
const THEME_KEY = 'zd-dashboard-theme';
function applyTheme(theme) {{
  document.documentElement.setAttribute('data-theme', theme);
  try {{ localStorage.setItem(THEME_KEY, theme); }} catch (e) {{}}
  const btn = $('themeToggle');
  const isLight = theme === 'light';
  btn.textContent = isLight ? 'Dark mode' : 'Light mode';
  btn.setAttribute('aria-pressed', isLight ? 'true' : 'false');
  btn.setAttribute('aria-label', isLight ? 'Switch to dark mode' : 'Switch to light mode');
}}
applyTheme(document.documentElement.getAttribute('data-theme') === 'light' ? 'light' : 'dark');
$('themeToggle').addEventListener('click', () => {{
  applyTheme(document.documentElement.getAttribute('data-theme') === 'light' ? 'dark' : 'light');
}});
const PROJ_PILL = {{
  FILTER:'p-filter', AWARE:'p-aware', PRODUCT24:'p-oncall', RESP:'p-respond',
  AICHAT:'p-aichat', PASS:'p-pass', FLEX:'p-flex', COM:'p-comm',
  MDMCLASS:'p-mdm', PAGESCAN:'p-pagescan', DD:'p-dd', DE:'p-de',
  DEVOPS:'p-devops', HOME:'p-home'
}};
const byLabel = (a, b) => String(a.label||'').localeCompare(String(b.label||''), undefined, {{sensitivity:'base'}});
function products() {{ return [...DATA.projects].sort(byLabel); }}
function productKpis() {{ return [...DATA.product_kpis].sort(byLabel); }}
function periods() {{ return DATA.weekly || DATA.monthly || []; }}
function issuePeriod(i) {{ return i.created_week || i.created_month || null; }}
function fromLabel() {{
  return (DATA.filters && DATA.filters.created_from_label) || '{esc(from_label)}';
}}

function fmtDays(d) {{
  if (d == null || d === '') return '—';
  const n = Number(d);
  if (!Number.isFinite(n)) return '—';
  if (n < 1) return (n * 24).toFixed(1) + 'h';
  return n.toFixed(1) + 'd';
}}
function pillType(t) {{
  return t === 'Escape Defect'
    ? '<span class="pill p-ed">Escape Defect</span>'
    : '<span class="pill p-sr">Support Request</span>';
}}
function pillPrio(p) {{
  const cls = p === 'P1' ? 'p-p1' : p === 'P2' ? 'p-p2' : 'p-p3';
  return `<span class="pill ${{cls}}">${{p || '—'}}</span>`;
}}
function pillStatus(issue) {{
  const cat = issue.status_category;
  const cls = cat === 'Done' ? 'st-done' : cat === 'In Progress' ? 'st-progress' : 'st-todo';
  return `<span class="pill ${{cls}}">${{issue.status}}</span>`;
}}
function pillProj(issue) {{
  const cls = PROJ_PILL[issue.project_key] || 'p-p3';
  return `<span class="pill ${{cls}}">${{issue.project_label}}</span>`;
}}

let tab = 'created';
let sortKey = 'created';
let sortDir = 1;
const PRIO_RANK = {{P1:1, P2:2, P3:3}};
const ISSUE_COLS = [
  ['week', 'Week', ''],
  ['product', 'Product', ''],
  ['key', 'Key', ''],
  ['type', 'Type', ''],
  ['prio', 'P', ''],
  ['zd', 'ZD', 'num'],
  ['created', 'Created', 'num'],
  ['status', 'Status', ''],
  ['assignee', 'Assignee', ''],
  ['summary', 'Summary', ''],
];

function setLiveStatus(text, kind) {{
  const el = $('liveStatus');
  el.textContent = text;
  el.className = kind || '';
}}

function paint() {{
  const PRODUCTS = products();
  const PRODUCT_KPIS = productKpis();
  const from = fromLabel();
  document.title = DATA.title || document.title;
  const h1 = document.querySelector('h1');
  if (h1 && DATA.title) h1.textContent = DATA.title;
  const createdTab = document.querySelector('.tabs button[data-tab="created"]');
  if (createdTab) createdTab.textContent = `Created since ${{from}}`;
  $('prodCount').textContent = PRODUCTS.length;
  if (DATA.live) {{
    setLiveStatus(`live from Jira · ${{DATA.generated_at || DATA.snapshot_date}}`, 'ok');
  }} else if (DATA._fromLiveApi) {{
    setLiveStatus(`Jira snapshot ${{DATA.snapshot_date}} · Connect Jira to pull live counts on refresh`, 'stale');
  }} else {{
    setLiveStatus(`Jira snapshot ${{DATA.snapshot_date}} · Connect Jira to pull live counts on refresh`, 'stale');
  }}
  $('links').innerHTML = [
    [`Created since ${{from}}`, DATA.links.created],
    ['statusCategory != Done', DATA.links.created_open],
    ['statusCategory = Done', DATA.links.created_done],
  ].map(([l,u]) => `<a href="${{u}}" target="_blank" rel="noopener">${{l}}</a>`).join('');

  const k = DATA.kpis;
  const donePct = k.done_pct != null ? k.done_pct : (k.created ? Math.round(100*k.created_done/k.created) : 0);
  const openPct = k.not_done_pct != null ? k.not_done_pct : (k.created ? Math.round(100*k.created_open/k.created) : 0);
  const cardHtml = ([n,l,s,cls,split]) => `<div class="card ${{cls}}"><div class="n">${{n}}</div><div class="l">${{l}}</div><div class="l">${{s}}</div>${{split||''}}</div>`;
  $('overview').innerHTML = [
    [k.created, `Created since ${{from}}`, `${{k.created_escape_defect}} ED · ${{k.created_support_request}} SR · ${{PRODUCTS.length}} products`, '', ''],
    [k.created_done, 'Done', `statusCategory = Done · ${{donePct}}% of created`, 'good done', ''],
    [k.created_open, 'Not Done', `statusCategory != Done · ${{openPct}}% of created`, k.created_open > k.created_done ? 'warn open' : 'open', ''],
  ].map(cardHtml).join('');
  $('cards').innerHTML = PRODUCT_KPIS.map(p => {{
    const cls = p.created === 0 ? '' : (p.open > p.done ? 'warn' : 'good');
    const split = p.created
      ? `<div class="split"><span class="done" style="width:${{p.done_pct||0}}%"></span><span class="open" style="width:${{p.not_done_pct||0}}%"></span></div>`
      : '';
    return cardHtml([p.created, p.label, `${{p.done}} Done · ${{p.open}} not Done · ${{p.escape_defect}} ED / ${{p.support_request}} SR`, cls, split]);
  }}).join('');

  $('headline').innerHTML = `<b>${{DATA.headline || ''}}</b>`;

  const maxCreated = Math.max(...PRODUCT_KPIS.map(p => p.created), 1);
  $('compareChart').innerHTML = PRODUCT_KPIS.map(p => {{
    const doneW = p.created ? (100 * p.done / maxCreated) : 0;
    const openW = p.created ? (100 * p.open / maxCreated) : 0;
    return `<div>${{p.label}}</div>
      <div class="bar stack">
        <span class="done" style="width:${{doneW}}%"></span>
        <span class="open" style="width:${{openW}}%"></span>
      </div>
      <div class="cmp-meta"><span class="done">${{p.done}}</span> / <span class="open">${{p.open}}</span></div>`;
  }}).join('');

  let ct = '<thead><tr><th>Product</th><th>Key</th><th class="num">Created</th><th class="num done">Done</th><th class="num open">Not Done</th><th class="num">Done %</th><th class="num">Not Done %</th></tr></thead><tbody>';
  for (const p of PRODUCT_KPIS) {{
    ct += `<tr>
      <td>${{p.label}}</td>
      <td><code>${{p.key}}</code></td>
      <td class="num">${{p.created}}</td>
      <td class="num done">${{p.done}}</td>
      <td class="num open">${{p.open}}</td>
      <td class="num">${{p.created ? (p.done_pct + '%') : '—'}}</td>
      <td class="num">${{p.created ? (p.not_done_pct + '%') : '—'}}</td>
    </tr>`;
  }}
  ct += `<tr>
    <td><b>Total</b></td><td></td>
    <td class="num"><b>${{k.created}}</b></td>
    <td class="num done"><b>${{k.created_done}}</b></td>
    <td class="num open"><b>${{k.created_open}}</b></td>
    <td class="num"><b>${{donePct}}%</b></td>
    <td class="num"><b>${{openPct}}%</b></td>
  </tr></tbody>`;
  $('compare').innerHTML = ct;

  let mt = '<thead><tr><th>Week</th><th>Slice</th>' + PRODUCTS.map(p => `<th class="num">${{p.label}}</th>`).join('') +
           '<th class="num">Total</th></tr></thead><tbody>';
  for (const m of periods()) {{
    const label = `${{m.label}}${{m.partial?' <span style="color:var(--muted)">(partial)</span>':''}}`;
    const slices = [
      ['Created', 'row-label', 'created', null],
      ['Done', 'row-done', 'done', 'done'],
      ['Not Done', 'row-open', 'open', 'open'],
    ];
    for (const [name, rowCls, field, numCls] of slices) {{
      mt += `<tr class="${{rowCls}}"><td>${{label}}</td><td>${{name}}</td>`;
      for (const p of PRODUCTS) {{
        const cls = numCls ? `num ${{numCls}}` : 'num';
        mt += `<td class="${{cls}}">${{m.by_project[p.key][field]}}</td>`;
      }}
      const tcls = numCls ? `num ${{numCls}}` : 'num';
      mt += `<td class="${{tcls}}">${{m.totals[field]}}</td></tr>`;
    }}
  }}
  mt += '</tbody>';
  $('weekly').innerHTML = mt;

  const projSel = $('projFilter');
  const prevProj = projSel.value;
  projSel.innerHTML = '<option value="all">All products</option>';
  for (const p of PRODUCTS) {{
    const opt = document.createElement('option');
    opt.value = p.key; opt.textContent = p.label;
    projSel.appendChild(opt);
  }}
  if ([...projSel.options].some(o => o.value === prevProj)) projSel.value = prevProj;

  const weekSel = $('weekFilter');
  const prevWeek = weekSel.value;
  weekSel.innerHTML = '<option value="all">All weeks</option>';
  for (const m of periods()) {{
    const opt = document.createElement('option');
    opt.value = m.id; opt.textContent = m.partial ? `${{m.label}} (partial)` : m.label;
    weekSel.appendChild(opt);
  }}
  if ([...weekSel.options].some(o => o.value === prevWeek)) weekSel.value = prevWeek;

  $('notes').innerHTML =
    `${{(DATA.notes && DATA.notes.scope) || ''}} ${{(DATA.notes && DATA.notes.window) || ''}}
    JQL: <code>${{DATA.jql.created}}</code>`;
  render();
}}

function sourceRows() {{
  let rows = DATA.created_issues;
  if (tab === 'open') rows = rows.filter(i => !i.is_done);
  if (tab === 'done') rows = rows.filter(i => i.is_done);
  return rows;
}}

function sortValue(i, key) {{
  if (key === 'week') return issuePeriod(i) ? issuePeriod(i).id : '';
  if (key === 'product') return i.project_label || '';
  if (key === 'key') return i.key || '';
  if (key === 'type') return i.type || '';
  if (key === 'prio') return PRIO_RANK[i.priority] || 99;
  if (key === 'zd') return i.zendesk_count || 0;
  if (key === 'created') return i.created_date || '';
  if (key === 'status') return i.status || '';
  if (key === 'assignee') return i.assignee || '';
  if (key === 'summary') return i.summary || '';
  return '';
}}

function sortRows(rows) {{
  return [...rows].sort((a, b) => {{
    const va = sortValue(a, sortKey);
    const vb = sortValue(b, sortKey);
    if (typeof va === 'number' && typeof vb === 'number') return (va - vb) * sortDir;
    return String(va).localeCompare(String(vb), undefined, {{numeric:true, sensitivity:'base'}}) * sortDir;
  }});
}}

function sortHeader() {{
  return '<thead><tr>' + ISSUE_COLS.map(([key, label, cls]) => {{
    const active = sortKey === key ? 'active' : '';
    const arrow = sortKey === key ? (sortDir === 1 ? '▲' : '▼') : '↕';
    const extra = cls ? ` ${{cls}}` : '';
    return `<th class="sortable${{extra}} ${{active}}" data-sort="${{key}}">${{label}}<span class="arrow">${{arrow}}</span></th>`;
  }}).join('') + '</tr></thead>';
}}

function render() {{
  const projF = $('projFilter').value;
  const typeF = $('typeFilter').value;
  const prioF = $('prioFilter').value;
  const weekF = $('weekFilter').value;
  const q = $('search').value.trim().toLowerCase();
  let rows = sourceRows();
  if (projF !== 'all') rows = rows.filter(i => i.project_key === projF);
  if (typeF !== 'all') rows = rows.filter(i => i.type === typeF);
  if (prioF !== 'all') rows = rows.filter(i => i.priority === prioF);
  if (weekF !== 'all') rows = rows.filter(i => issuePeriod(i) && issuePeriod(i).id === weekF);
  if (q) rows = rows.filter(i => [i.key, i.summary, i.assignee, i.status, i.project_label].join(' ').toLowerCase().includes(q));
  rows = sortRows(rows);
  $('count').innerHTML = `<b>${{rows.length}}</b> tickets`;

  let html = sortHeader() + '<tbody>';
  if (!rows.length) html += '<tr><td colspan="10" style="color:var(--muted)">no tickets match filter</td></tr>';
  for (const i of rows) {{
    const period = issuePeriod(i);
    html += `<tr>
      <td>${{period ? period.label : '—'}}</td>
      <td>${{pillProj(i)}}</td>
      <td><a class="key" href="${{i.url}}" target="_blank" rel="noopener">${{i.key}}</a></td>
      <td>${{pillType(i.type)}}</td>
      <td>${{pillPrio(i.priority)}}</td>
      <td class="num">${{i.zendesk_count}}</td>
      <td class="num">${{i.created_date || '—'}}</td>
      <td>${{pillStatus(i)}}</td>
      <td>${{i.assignee}}</td>
      <td class="summary">${{i.summary}}</td>
    </tr>`;
  }}
  html += '</tbody>';
  $('issues').innerHTML = html;
}}

document.querySelectorAll('.tabs button').forEach(btn => {{
  btn.addEventListener('click', () => {{
    document.querySelectorAll('.tabs button').forEach(b => b.classList.remove('active'));
    btn.classList.add('active');
    tab = btn.dataset.tab;
    render();
  }});
}});
['projFilter','typeFilter','prioFilter','weekFilter','search'].forEach(id => $(id).addEventListener('input', render));
$('issues').addEventListener('click', (e) => {{
  const th = e.target.closest('th[data-sort]');
  if (!th) return;
  const key = th.dataset.sort;
  if (sortKey === key) sortDir *= -1;
  else {{ sortKey = key; sortDir = 1; }}
  render();
}});

async function loadLive() {{
  const candidates = ['api/live', 'live.json'];
  for (const path of candidates) {{
    try {{
      const r = await fetch(path + '?t=' + Date.now(), {{ cache: 'no-store' }});
      if (!r.ok) continue;
      const data = await r.json();
      if (data && data.kpis) {{
        DATA = data;
        DATA._fromLiveApi = path === 'api/live';
        return path;
      }}
    }} catch (e) {{}}
  }}
  return null;
}}

"""
    live_js = (ROOT / "jira-live.js").read_text(encoding="utf-8")
    tail = """
bindJiraPanel();
(async function boot() {
  paint();
  setLiveStatus('refreshing from Jira…', '');
  try {
    await refreshDashboard();
  } catch (e) {
    setLiveStatus('Jira refresh failed · ' + (e.message || e), 'stale');
    await loadLive();
  }
  paint();
})();
</script>
</body>
</html>
"""
    return head + live_js + tail


def main() -> None:
    data = json.loads(JSON_PATH.read_text(encoding="utf-8"))
    html = write_html(data)
    md = write_markdown(data)
    HTML_PATH.write_text(html, encoding="utf-8")
    MD_PATH.write_text(md, encoding="utf-8")
    DOCS_PATH.parent.mkdir(parents=True, exist_ok=True)
    DOCS_PATH.write_text(html, encoding="utf-8")
    live_path = DOCS_PATH.parent / "live.json"
    live_path.write_text(json.dumps(data) + "\n", encoding="utf-8")
    print(f"wrote {HTML_PATH.relative_to(ROOT)}")
    print(f"wrote {MD_PATH.relative_to(ROOT)}")
    print(f"wrote {DOCS_PATH.relative_to(ROOT)}")
    print(f"wrote {live_path.relative_to(ROOT)}")


if __name__ == "__main__":
    main()
