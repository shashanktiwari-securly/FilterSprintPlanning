"""Render the Filter Zendesk weekly dashboard as standalone HTML + Markdown.

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
    lines = [
        f"# {data['title']}",
        "",
        f"Snapshot **{data['snapshot_date']}** · project **{data['project']['name']}** (`{data['project']['key']}`) · "
        f"Escape Defect + Support Request · Zendesk Ticket Count > 0 · weeks from **{data['filters']['created_from']}**.",
        "",
        "## Headline",
        "",
        f"Filter logged **{k['created']}** customer-ticketed tickets since 1 Aug 2026 "
        f"({k['created_escape_defect']} Escape Defect, {k['created_support_request']} Support Request), "
        f"covering **{k['created_zendesk']}** Zendesk tickets. "
        f"Only **{k['created_done']}** of those {k['created']} are Done. "
        f"In the same window the team resolved **{k['resolved']}** Zendesk-linked tickets "
        f"(mostly older backlog), covering **{k['resolved_zendesk']}** Zendesk tickets.",
        "",
        "## Live Jira views",
        "",
        f"- [Created since 1 Aug]({data['links']['created']})",
        f"- [Created and still open]({data['links']['created_open']})",
        f"- [Created and Done]({data['links']['created_done']})",
        f"- [Resolved since 1 Aug]({data['links']['resolved']})",
        "",
        "## Weekly created",
        "",
        md_row(["Week", "Created", "Escape Defect", "Support Request", "Zendesk", "Now Done", "Still open"]),
        md_row(["---", "---:", "---:", "---:", "---:", "---:", "---:"]),
    ]
    for w in data["weekly"]:
        label = w["label"] + (" (partial)" if w.get("partial") else "")
        lines.append(
            md_row(
                [
                    label,
                    w["created"],
                    w["created_escape_defect"],
                    w["created_support_request"],
                    w["created_zendesk"],
                    w["created_done"],
                    w["created_open"],
                ]
            )
        )
    lines += [
        md_row(
            [
                "**Total**",
                f"**{k['created']}**",
                f"**{k['created_escape_defect']}**",
                f"**{k['created_support_request']}**",
                f"**{k['created_zendesk']}**",
                f"**{k['created_done']}**",
                f"**{k['created_open']}**",
            ]
        ),
        "",
        "## Created ticket list",
        "",
        md_row(["Week", "Key", "Type", "P", "ZD", "Created", "Status", "Assignee", "Summary"]),
        md_row(["---", "---", "---", "---", "---:", "---", "---", "---", "---"]),
    ]
    for issue in data["created_issues"]:
        week = issue["created_week"]["id"] if issue.get("created_week") else ""
        lines.append(
            md_row(
                [
                    week,
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
        "## Weekly resolved",
        "",
        md_row(["Week", "Resolved", "Escape Defect", "Support Request", "Zendesk", "From Aug cohort"]),
        md_row(["---", "---:", "---:", "---:", "---:", "---:"]),
    ]
    for w in data["weekly"]:
        label = w["label"] + (" (partial)" if w.get("partial") else "")
        lines.append(
            md_row(
                [
                    label,
                    w["resolved"],
                    w["resolved_escape_defect"],
                    w["resolved_support_request"],
                    w["resolved_zendesk"],
                    w["resolved_from_aug_cohort"],
                ]
            )
        )
    lines += [
        md_row(
            [
                "**Total**",
                f"**{k['resolved']}**",
                f"**{k['resolved_escape_defect']}**",
                f"**{k['resolved_support_request']}**",
                f"**{k['resolved_zendesk']}**",
                f"**{k['resolved_from_aug_cohort']}**",
            ]
        ),
        "",
        "## Resolved ticket list",
        "",
        md_row(["Week", "Key", "Type", "P", "ZD", "Resolved", "Status", "Resolution", "Summary"]),
        md_row(["---", "---", "---", "---", "---:", "---", "---", "---", "---"]),
    ]
    for issue in data["resolved_issues"]:
        week = issue["resolved_week"]["id"] if issue.get("resolved_week") else ""
        lines.append(
            md_row(
                [
                    week,
                    f"[{issue['key']}]({issue['url']})",
                    "ED" if issue["type"] == "Escape Defect" else "SR",
                    issue["priority"] or "",
                    issue["zendesk_count"],
                    issue["resolved_date"] or "",
                    issue["status"],
                    issue["resolution"] or "",
                    issue["summary"].replace("|", "/"),
                ]
            )
        )
    lines += [
        "",
        "## Notes",
        "",
        f"- {k['excluded_created_without_zendesk']} additional Escape Defect / Support Request tickets were created "
        f"in the same window with Zendesk Ticket Count = 0 and are excluded. "
        f"Total ED+SR created = {k['total_ed_sr_created']}.",
        f"- {k['resolved_still_in_qa']} resolved tickets still show Ready for QA (not fully Done).",
        f"- Confluence copy: {data['links']['confluence']}",
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
    --accent:#38bdf8; --purple:#a78bfa; --created:#38bdf8; --closed:#22c55e;
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
  .wrap {{ padding:20px 28px 60px; max-width:1500px; margin:0 auto; }}
  .cards {{ display:flex; gap:14px; flex-wrap:wrap; margin:18px 0 26px; }}
  .card {{ background:var(--panel); border:1px solid var(--line); border-radius:12px; padding:16px 18px; min-width:150px; flex:1; }}
  .card .n {{ font-size:26px; font-weight:700; }}
  .card .l {{ color:var(--muted); font-size:12px; margin-top:2px; }}
  .card.warn .n {{ color:var(--warn); }}
  .card.bad .n {{ color:var(--crit); }}
  .card.good .n {{ color:var(--good); }}
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
  .links {{ display:flex; flex-wrap:wrap; gap:8px; margin:8px 0 18px; }}
  .links a {{ background:var(--panel2); border:1px solid var(--line); color:var(--accent);
    text-decoration:none; border-radius:8px; padding:6px 10px; font-size:12px; }}
  .links a:hover {{ border-color:var(--accent); }}
  .chart {{ display:grid; grid-template-columns:140px 1fr; gap:10px 16px; align-items:center;
    background:var(--panel); border:1px solid var(--line); border-radius:12px; padding:16px 18px; }}
  .barrow {{ display:flex; flex-direction:column; gap:6px; }}
  .bar {{ height:10px; border-radius:6px; background:#334155; overflow:hidden; position:relative; }}
  .bar > i {{ display:block; height:100%; }}
  .bar-meta {{ color:var(--muted); font-size:12px; font-variant-numeric:tabular-nums; }}
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
  <h1>Filter weekly dashboard</h1>
  <div class="sub">
    Zendesk-linked Escape Defects and Support Requests · product_FILTER ·
    from 1 Aug 2026 · snapshot <span id="snap"></span><br/>
    Source: <a href="https://securly.atlassian.net">securly.atlassian.net</a>
    · field <code>Zendesk Ticket Count</code> &gt; 0
    · weeks are 7-day buckets starting Saturday 1 Aug
  </div>
</header>
<div class="wrap">
  <div class="links" id="links"></div>
  <div class="cards" id="cards"></div>
  <div class="callout" id="headline"></div>

  <h2>Weekly created vs resolved</h2>
  <div class="legend"><b style="color:var(--created)">Blue</b> = created this week · <b style="color:var(--closed)">Green</b> = resolved this week (any create date). W4 is partial through the snapshot date.</div>
  <div class="chart" id="chart"></div>

  <h2>Weekly totals</h2>
  <div class="scroll"><table id="weekly"></table></div>

  <h2>Ticket list</h2>
  <div class="tabs">
    <button class="active" data-tab="created">Created since 1 Aug</button>
    <button data-tab="open">Still open</button>
    <button data-tab="done">Created and Done</button>
    <button data-tab="resolved">Resolved since 1 Aug</button>
  </div>
  <div class="controls">
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
  Git-hosted report from <code>reports/filter-zendesk-weekly-dashboard.json</code>
  · regenerate with <code>python3 build_filter_zendesk_weekly_dashboard.py</code>
  · also published at <code>docs/index.html</code> for GitHub Pages
</footer>
<script>
const DATA = {payload};
const $ = (id) => document.getElementById(id);

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
function weekId(issue, field) {{
  return issue[field] ? issue[field].id : '';
}}

$('snap').textContent = DATA.snapshot_date;
$('links').innerHTML = [
  ['Created since 1 Aug', DATA.links.created],
  ['Created and still open', DATA.links.created_open],
  ['Created and Done', DATA.links.created_done],
  ['Resolved since 1 Aug', DATA.links.resolved],
  ['Confluence copy', DATA.links.confluence],
].map(([l,u]) => `<a href="${{u}}" target="_blank" rel="noopener">${{l}}</a>`).join('');

const k = DATA.kpis;
$('cards').innerHTML = [
  [k.created, 'Created since 1 Aug', `${{k.created_escape_defect}} ED · ${{k.created_support_request}} SR`, ''],
  [k.created_zendesk, 'Zendesk tickets on created', 'customer impact attached to new Jiras', ''],
  [k.created_open, 'Still open from Aug cohort', `${{k.created_done}} Done of ${{k.created}}`, k.created_open > k.created_done ? 'warn' : 'good'],
  [k.resolved, 'Resolved since 1 Aug', `${{k.resolved_escape_defect}} ED · ${{k.resolved_support_request}} SR · ${{k.resolved_zendesk}} ZD`, 'good'],
  [k.resolved_from_aug_cohort, 'Aug cohort among resolved', 'closures are mostly older backlog', k.resolved_from_aug_cohort < 3 ? 'bad' : ''],
].map(([n,l,s,cls]) => `<div class="card ${{cls}}"><div class="n">${{n}}</div><div class="l">${{l}}</div><div class="l">${{s}}</div></div>`).join('');

$('headline').innerHTML =
  `<b>New customer-ticketed work is accumulating faster than it is closing.</b>
  ${{k.created}} created vs ${{k.created_done}} Done in the Aug cohort
  (${{Math.round(100*k.created_done/k.created)}}% done).
  W3 carries the most Zendesk impact (${{DATA.weekly[2].created_zendesk}} of ${{k.created_zendesk}} new Zendesk tickets),
  driven by FILTER-16485. Closures this month are almost all older backlog.`;

const maxBar = Math.max(...DATA.weekly.flatMap(w => [w.created, w.resolved, 1]));
$('chart').innerHTML = DATA.weekly.map(w => {{
  const tag = w.partial ? ' <span style="color:var(--muted)">(partial)</span>' : '';
  return `<div>${{w.label}}${{tag}}</div>
    <div class="barrow">
      <div class="bar"><i style="width:${{100*w.created/maxBar}}%;background:var(--created)"></i></div>
      <div class="bar"><i style="width:${{100*w.resolved/maxBar}}%;background:var(--closed)"></i></div>
      <div class="bar-meta">created ${{w.created}} (${{w.created_zendesk}} ZD) · resolved ${{w.resolved}} (${{w.resolved_zendesk}} ZD)</div>
    </div>`;
}}).join('');

let wt = '<thead><tr><th>Week</th><th class="num">Created</th><th class="num">ED</th><th class="num">SR</th><th class="num">ZD on created</th><th class="num">Now Done</th><th class="num">Still open</th><th class="num">Resolved</th><th class="num">ZD on resolved</th><th class="num">Resolved from Aug cohort</th></tr></thead><tbody>';
for (const w of DATA.weekly) {{
  wt += `<tr><td>${{w.label}}${{w.partial?' <span style="color:var(--muted)">(partial)</span>':''}}</td>
    <td class="num">${{w.created}}</td><td class="num">${{w.created_escape_defect}}</td>
    <td class="num">${{w.created_support_request}}</td><td class="num">${{w.created_zendesk}}</td>
    <td class="num">${{w.created_done}}</td><td class="num">${{w.created_open}}</td>
    <td class="num">${{w.resolved}}</td><td class="num">${{w.resolved_zendesk}}</td>
    <td class="num">${{w.resolved_from_aug_cohort}}</td></tr>`;
}}
wt += `<tr><td><b>Total</b></td><td class="num"><b>${{k.created}}</b></td>
  <td class="num"><b>${{k.created_escape_defect}}</b></td><td class="num"><b>${{k.created_support_request}}</b></td>
  <td class="num"><b>${{k.created_zendesk}}</b></td><td class="num"><b>${{k.created_done}}</b></td>
  <td class="num"><b>${{k.created_open}}</b></td><td class="num"><b>${{k.resolved}}</b></td>
  <td class="num"><b>${{k.resolved_zendesk}}</b></td><td class="num"><b>${{k.resolved_from_aug_cohort}}</b></td></tr></tbody>`;
$('weekly').innerHTML = wt;

const weekSel = $('weekFilter');
for (const w of DATA.weekly) {{
  const opt = document.createElement('option');
  opt.value = w.id; opt.textContent = w.label;
  weekSel.appendChild(opt);
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
['typeFilter','prioFilter','weekFilter','search'].forEach(id => $(id).addEventListener('input', render));

function sourceRows() {{
  if (tab === 'resolved') return DATA.resolved_issues.map(i => ({{...i, _week: weekId(i,'resolved_week'), _date: i.resolved_date, _mode:'resolved'}}));
  let rows = DATA.created_issues;
  if (tab === 'open') rows = rows.filter(i => !i.is_done);
  if (tab === 'done') rows = rows.filter(i => i.is_done);
  return rows.map(i => ({{...i, _week: weekId(i,'created_week'), _date: i.created_date, _mode:'created'}}));
}}

function render() {{
  const typeF = $('typeFilter').value;
  const prioF = $('prioFilter').value;
  const weekF = $('weekFilter').value;
  const q = $('search').value.trim().toLowerCase();
  let rows = sourceRows();
  if (typeF !== 'all') rows = rows.filter(i => i.type === typeF);
  if (prioF !== 'all') rows = rows.filter(i => i.priority === prioF);
  if (weekF !== 'all') rows = rows.filter(i => i._week === weekF);
  if (q) rows = rows.filter(i => [i.key, i.summary, i.assignee, i.status, i.resolution||''].join(' ').toLowerCase().includes(q));
  $('count').innerHTML = `<b>${{rows.length}}</b> tickets · ${{rows.reduce((s,i)=>s+i.zendesk_count,0)}} Zendesk tickets`;

  const dateLabel = tab === 'resolved' ? 'Resolved' : 'Created';
  let html = `<thead><tr><th>Week</th><th>Key</th><th>Type</th><th>P</th><th class="num">ZD</th><th>${{dateLabel}}</th><th>Status</th><th>Resolution</th><th>Assignee</th><th>Summary</th></tr></thead><tbody>`;
  if (!rows.length) html += '<tr><td colspan="10" style="color:var(--muted)">no tickets match filter</td></tr>';
  for (const i of rows) {{
    html += `<tr>
      <td>${{i._week}}</td>
      <td><a class="key" href="${{i.url}}" target="_blank" rel="noopener">${{i.key}}</a></td>
      <td>${{pillType(i.type)}}</td>
      <td>${{pillPrio(i.priority)}}</td>
      <td class="num">${{i.zendesk_count}}</td>
      <td class="num">${{i._date || '—'}}</td>
      <td>${{pillStatus(i)}}</td>
      <td>${{i.resolution || '—'}}</td>
      <td>${{i.assignee}}</td>
      <td class="summary">${{i.summary}}</td>
    </tr>`;
  }}
  html += '</tbody>';
  $('issues').innerHTML = html;
}}

$('notes').innerHTML =
  `${{k.excluded_created_without_zendesk}} additional Escape Defect / Support Request tickets were created since 1 Aug with Zendesk Ticket Count = 0 and are excluded (total ED+SR created = ${{k.total_ed_sr_created}}).
  ${{k.resolved_still_in_qa}} resolved tickets are still Ready for QA, not fully Done.
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
