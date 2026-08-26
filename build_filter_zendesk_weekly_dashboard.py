"""Render the Zendesk monthly dashboard as standalone HTML + Markdown.

Reads reports/filter-zendesk-weekly-dashboard.json and writes:

  reports/filter-zendesk-weekly-dashboard.html
  reports/filter-zendesk-weekly-dashboard.md
  docs/index.html   (same HTML, for GitHub Pages)
"""

from __future__ import annotations

import json
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


def write_markdown(data: dict) -> str:
    k = data["kpis"]
    projects = data["projects"]
    lines = [
        f"# {data['title']}",
        "",
        f"Snapshot **{data['snapshot_date']}** · {len(projects)} products · "
        f"Escape Defect + Support Request · Zendesk Ticket Count > 0 · monthly from **{data['filters']['created_from']}**.",
        "",
        "## Headline",
        "",
        data.get("headline")
        or (
            f"**{k['created']}** Zendesk-linked tickets created since 1 Jul 2026 "
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
    for p in data["product_kpis"]:
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
    for p in data["product_kpis"]:
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
        "## Monthly created",
        "",
    ]
    header = ["Month", "Slice"] + [p["label"] for p in projects] + ["Total"]
    lines.append(md_row(header))
    lines.append(md_row(["---", "---"] + [":---:" for _ in header[2:]]))
    for m in data["monthly"]:
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
        md_row(["Month", "Product", "Key", "Type", "P", "ZD", "Created", "Status", "Assignee", "Summary"]),
        md_row(["---", "---", "---", "---", "---", "---:", "---", "---", "---", "---"]),
    ]
    for issue in data["created_issues"]:
        month = issue["created_month"]["label"] if issue.get("created_month") else ""
        lines.append(
            md_row(
                [
                    month,
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
        f"- [Created since 1 Jul]({data['links']['created']})",
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
    return f"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="utf-8"/>
<meta name="viewport" content="width=device-width, initial-scale=1"/>
<title>{esc(data['title'])}</title>
<style>
  :root {{
    --bg:#0f172a; --panel:#1e293b; --panel2:#273449; --ink:#e2e8f0; --muted:#94a3b8;
    --line:#334155; --good:#22c55e; --ok:#84cc16; --warn:#eab308; --bad:#f97316; --crit:#ef4444;
    --accent:#38bdf8; --created:#38bdf8;
  }}
  * {{ box-sizing:border-box; }}
  body {{ margin:0; background:var(--bg); color:var(--ink);
    font-family:-apple-system,BlinkMacSystemFont,"Segoe UI",Roboto,Helvetica,Arial,sans-serif; font-size:14px; }}
  header {{ padding:24px 28px; border-bottom:1px solid var(--line);
    background:linear-gradient(180deg,#111c33,#0f172a); }}
  h1 {{ margin:0 0 6px; font-size:22px; }}
  .sub {{ color:var(--muted); font-size:13px; line-height:1.5; }}
  .sub a {{ color:var(--accent); text-decoration:none; }}
  .sub a:hover {{ text-decoration:underline; }}
  .wrap {{ padding:20px 28px 60px; max-width:1800px; margin:0 auto; }}
  .cards {{ display:flex; gap:10px; flex-wrap:wrap; margin:18px 0 26px; }}
  .card {{ background:var(--panel); border:1px solid var(--line); border-radius:12px; padding:14px 16px; min-width:128px; flex:1 1 128px; }}
  .card .n {{ font-size:26px; font-weight:700; }}
  .card .l {{ color:var(--muted); font-size:12px; margin-top:2px; }}
  .card.warn .n {{ color:var(--warn); }}
  .card.good .n {{ color:var(--good); }}
  .card.done {{ border-color:#166534; }}
  .card.open {{ border-color:#a16207; }}
  .split {{ display:flex; height:8px; border-radius:999px; overflow:hidden; background:#334155; margin-top:8px; }}
  .split .done {{ background:var(--good); }}
  .split .open {{ background:var(--warn); }}
  .cmp {{ display:grid; grid-template-columns:minmax(110px,140px) 1fr 90px; gap:8px 14px; align-items:center;
    background:var(--panel); border:1px solid var(--line); border-radius:12px; padding:16px 18px; }}
  .bar.stack {{ display:flex; height:14px; border-radius:7px; overflow:hidden; background:#334155; }}
  .bar.stack .done {{ background:var(--good); height:100%; }}
  .bar.stack .open {{ background:var(--warn); height:100%; }}
  .cmp-meta {{ font-size:12px; font-variant-numeric:tabular-nums; white-space:nowrap; }}
  .cmp-meta .done {{ color:var(--good); font-weight:700; }}
  .cmp-meta .open {{ color:var(--warn); font-weight:700; }}
  td.done, th.done {{ color:var(--good); }}
  td.open, th.open {{ color:var(--warn); }}
  tr.row-done td {{ background:#13261c; }}
  tr.row-open td {{ background:#2a2410; }}
  tr.row-label td {{ color:var(--muted); font-weight:600; }}
  .legend .swatch {{ display:inline-block; width:10px; height:10px; border-radius:2px; margin:0 4px 0 10px; vertical-align:middle; }}
  .legend .swatch.done {{ background:var(--good); }}
  .legend .swatch.open {{ background:var(--warn); }}
  h2 {{ font-size:16px; margin:30px 0 12px; border-left:3px solid var(--accent); padding-left:10px; }}
  table {{ border-collapse:collapse; width:100%; background:var(--panel); border-radius:10px; overflow:hidden; }}
  th, td {{ padding:9px 11px; text-align:left; border-bottom:1px solid var(--line); }}
  th {{ background:var(--panel2); color:var(--muted); font-weight:600; font-size:12px;
    text-transform:uppercase; letter-spacing:.03em; position:sticky; top:0; }}
  td.num, th.num {{ text-align:right; font-variant-numeric:tabular-nums; white-space:nowrap; }}
  tr:hover td {{ background:#20304a; }}
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
  .bar {{ height:12px; border-radius:6px; background:#334155; overflow:hidden; }}
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
  .tabs button.active {{ background:#0ea5e9; color:#04283b; border-color:#0ea5e9; font-weight:700; }}
  a.key {{ color:var(--accent); text-decoration:none; font-weight:600; }}
  a.key:hover {{ text-decoration:underline; }}
  .note {{ color:var(--muted); font-size:12px; margin-top:10px; }}
  footer {{ color:var(--muted); font-size:12px; padding:22px 28px; border-top:1px solid var(--line); }}
  .callout {{ background:var(--panel); border:1px solid var(--line); border-left:4px solid var(--warn);
    border-radius:10px; padding:12px 16px; margin:8px 0 20px; color:var(--muted); }}
  .callout b {{ color:var(--ink); }}
  .summary {{ max-width:720px; white-space:normal; }}
</style>
</head>
<body>
<header>
  <h1>Monthly Zendesk-linked dashboard</h1>
  <div class="sub">
    Escape Defects and Support Requests · <span id="prodCount"></span> products ·
    from 1 Jul 2026 · snapshot <span id="snap"></span><br/>
    Source: <a href="https://securly.atlassian.net">securly.atlassian.net</a>
    · field <code>Zendesk Ticket Count</code> &gt; 0
    · grouped by calendar month
  </div>
</header>
<div class="wrap">
  <div class="links" id="links"></div>
  <div class="cards" id="cards"></div>
  <div class="callout" id="headline"></div>

  <h2>Done vs not Done</h2>
  <div class="legend">
    Comparison of Jira <b>statusCategory = Done</b> versus <b>statusCategory != Done</b>
    for the Jul+ cohort.
    <span class="swatch done"></span>Done
    <span class="swatch open"></span>Not Done
  </div>
  <div class="cmp" id="compareChart" style="margin-top:12px"></div>
  <div class="scroll" style="margin-top:16px"><table id="compare"></table></div>

  <h2>Monthly created by product</h2>
  <div class="legend">Each month is split into Created, Done, and Not Done so the statusCategory comparison is visible by month. Jul 2026 is complete. Aug 2026 is partial through the snapshot date. Respond (RESP) stays in the table even when the count is 0.</div>
  <div class="scroll" style="margin-top:16px"><table id="monthly"></table></div>

  <h2>Ticket list</h2>
  <div class="tabs">
    <button class="active" data-tab="created">Created since 1 Jul</button>
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
    <select id="monthFilter"><option value="all">All months</option></select>
    <input id="search" placeholder="search key, summary, assignee…"/>
  </div>
  <div class="legend" id="count"></div>
  <div class="scroll"><table id="issues"></table></div>
  <p class="note" id="notes"></p>
</div>
<footer>
  Git-hosted report from <code>reports/filter-zendesk-weekly-dashboard.json</code>
  · regenerate with <code>python3 build_filter_zendesk_weekly_dashboard.py</code>
  · also published at <code>docs/index.html</code> for GitHub Pages
</footer>
<script>
const DATA = {payload};
const $ = (id) => document.getElementById(id);
const PROJ_PILL = {{
  FILTER:'p-filter', AWARE:'p-aware', RESP:'p-respond',
  AICHAT:'p-aichat', PASS:'p-pass', FLEX:'p-flex', COM:'p-comm',
  MDMCLASS:'p-mdm', PAGESCAN:'p-pagescan', DD:'p-dd', DE:'p-de',
  DEVOPS:'p-devops', HOME:'p-home'
}};

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

$('snap').textContent = DATA.snapshot_date;
$('prodCount').textContent = DATA.projects.length;
$('links').innerHTML = [
  ['Created since 1 Jul', DATA.links.created],
  ['statusCategory != Done', DATA.links.created_open],
  ['statusCategory = Done', DATA.links.created_done],
].map(([l,u]) => `<a href="${{u}}" target="_blank" rel="noopener">${{l}}</a>`).join('');

const k = DATA.kpis;
const donePct = k.done_pct != null ? k.done_pct : (k.created ? Math.round(100*k.created_done/k.created) : 0);
const openPct = k.not_done_pct != null ? k.not_done_pct : (k.created ? Math.round(100*k.created_open/k.created) : 0);
const productCards = DATA.product_kpis.map(p => {{
  const cls = p.created === 0 ? '' : (p.open > p.done ? 'warn' : 'good');
  const split = p.created
    ? `<div class="split"><span class="done" style="width:${{p.done_pct||0}}%"></span><span class="open" style="width:${{p.not_done_pct||0}}%"></span></div>`
    : '';
  return [p.created, p.label, `${{p.done}} Done · ${{p.open}} not Done · ${{p.escape_defect}} ED / ${{p.support_request}} SR`, cls, split];
}});
$('cards').innerHTML = [
  [k.created, 'Created since 1 Jul', `${{k.created_escape_defect}} ED · ${{k.created_support_request}} SR · ${{DATA.projects.length}} products`, '', ''],
  [k.created_done, 'Done', `statusCategory = Done · ${{donePct}}% of created`, 'good done', ''],
  [k.created_open, 'Not Done', `statusCategory != Done · ${{openPct}}% of created`, k.created_open > k.created_done ? 'warn open' : 'open', ''],
  ...productCards
].map(([n,l,s,cls,split]) => `<div class="card ${{cls}}"><div class="n">${{n}}</div><div class="l">${{l}}</div><div class="l">${{s}}</div>${{split||''}}</div>`).join('');

$('headline').innerHTML = `<b>${{DATA.headline || ''}}</b>`;

const maxCreated = Math.max(...DATA.product_kpis.map(p => p.created), 1);
$('compareChart').innerHTML = DATA.product_kpis.map(p => {{
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
for (const p of DATA.product_kpis) {{
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

let mt = '<thead><tr><th>Month</th><th>Slice</th>' + DATA.projects.map(p => `<th class="num">${{p.label}}</th>`).join('') +
         '<th class="num">Total</th></tr></thead><tbody>';
for (const m of DATA.monthly) {{
  const label = `${{m.label}}${{m.partial?' <span style="color:var(--muted)">(partial)</span>':''}}`;
  const slices = [
    ['Created', 'row-label', 'created', null],
    ['Done', 'row-done', 'done', 'done'],
    ['Not Done', 'row-open', 'open', 'open'],
  ];
  for (const [name, rowCls, field, numCls] of slices) {{
    mt += `<tr class="${{rowCls}}"><td>${{label}}</td><td>${{name}}</td>`;
    for (const p of DATA.projects) {{
      const cls = numCls ? `num ${{numCls}}` : 'num';
      mt += `<td class="${{cls}}">${{m.by_project[p.key][field]}}</td>`;
    }}
    const tcls = numCls ? `num ${{numCls}}` : 'num';
    mt += `<td class="${{tcls}}">${{m.totals[field]}}</td></tr>`;
  }}
}}
mt += '</tbody>';
$('monthly').innerHTML = mt;

const projSel = $('projFilter');
for (const p of DATA.projects) {{
  const opt = document.createElement('option');
  opt.value = p.key; opt.textContent = p.label;
  projSel.appendChild(opt);
}}
const monthSel = $('monthFilter');
for (const m of DATA.monthly) {{
  const opt = document.createElement('option');
  opt.value = m.id; opt.textContent = m.label;
  monthSel.appendChild(opt);
}}

let tab = 'created';
document.querySelectorAll('.tabs button').forEach(btn => {{
  btn.addEventListener('click', () => {{
    document.querySelectorAll('.tabs button').forEach(b => b.classList.remove('active'));
    btn.classList.add('active');
    tab = btn.dataset.tab;
    render();
  }});
}});
['projFilter','typeFilter','prioFilter','monthFilter','search'].forEach(id => $(id).addEventListener('input', render));

function sourceRows() {{
  let rows = DATA.created_issues;
  if (tab === 'open') rows = rows.filter(i => !i.is_done);
  if (tab === 'done') rows = rows.filter(i => i.is_done);
  return rows;
}}

function render() {{
  const projF = $('projFilter').value;
  const typeF = $('typeFilter').value;
  const prioF = $('prioFilter').value;
  const monthF = $('monthFilter').value;
  const q = $('search').value.trim().toLowerCase();
  let rows = sourceRows();
  if (projF !== 'all') rows = rows.filter(i => i.project_key === projF);
  if (typeF !== 'all') rows = rows.filter(i => i.type === typeF);
  if (prioF !== 'all') rows = rows.filter(i => i.priority === prioF);
  if (monthF !== 'all') rows = rows.filter(i => i.created_month && i.created_month.id === monthF);
  if (q) rows = rows.filter(i => [i.key, i.summary, i.assignee, i.status, i.project_label].join(' ').toLowerCase().includes(q));
  $('count').innerHTML = `<b>${{rows.length}}</b> tickets`;

  let html = '<thead><tr><th>Month</th><th>Product</th><th>Key</th><th>Type</th><th>P</th><th class="num">ZD</th><th>Created</th><th>Status</th><th>Assignee</th><th>Summary</th></tr></thead><tbody>';
  if (!rows.length) html += '<tr><td colspan="10" style="color:var(--muted)">no tickets match filter</td></tr>';
  for (const i of rows) {{
    html += `<tr>
      <td>${{i.created_month ? i.created_month.label : '—'}}</td>
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

$('notes').innerHTML =
  `${{(DATA.notes && DATA.notes.scope) || ''}} ${{(DATA.notes && DATA.notes.window) || ''}}
  JQL: <code>${{DATA.jql.created}}</code>`;

render();
</script>
</body>
</html>
"""


def main() -> None:
    data = json.loads(JSON_PATH.read_text(encoding="utf-8"))
    html = write_html(data)
    md = write_markdown(data)
    HTML_PATH.write_text(html, encoding="utf-8")
    MD_PATH.write_text(md, encoding="utf-8")
    DOCS_PATH.parent.mkdir(parents=True, exist_ok=True)
    DOCS_PATH.write_text(html, encoding="utf-8")
    print(f"wrote {HTML_PATH.relative_to(ROOT)}")
    print(f"wrote {MD_PATH.relative_to(ROOT)}")
    print(f"wrote {DOCS_PATH.relative_to(ROOT)}")


if __name__ == "__main__":
    main()
