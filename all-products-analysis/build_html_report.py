"""
Build an interactive HTML dashboard from analysis_output.json.
Shows, for each product, a monthly completion comparison and per-sprint detail.
Output: SPRINT_COMPLETION_REPORT.html  (self-contained, data embedded inline)
"""
import json, os
from collections import defaultdict

HERE = os.path.dirname(__file__)
data = json.load(open(os.path.join(HERE, 'analysis_output.json')))

MONTHS = ['2026-01', '2026-02', '2026-03', '2026-04', '2026-05', '2026-06', '2026-07']
MONTH_LABEL = {'2026-01': 'Jan', '2026-02': 'Feb', '2026-03': 'Mar', '2026-04': 'Apr',
               '2026-05': 'May', '2026-06': 'Jun', '2026-07': 'Jul'}
PRODUCT_ORDER = ['AIChat', 'FLEX & COM', 'PASS', 'Platform', 'product_aware', 'product_home',
                 'product_MDM_CLASSROOM', 'product_oncall', 'product_RESPOND', 'product_FILTER']
KEY_BY_NAME = {
    'AIChat': 'AICHAT', 'FLEX & COM': 'FLEX', 'PASS': 'PASS', 'Platform': 'PLATFORM',
    'product_aware': 'AWARE', 'product_home': 'HOME', 'product_MDM_CLASSROOM': 'MDMCLASS',
    'product_oncall': 'PRODUCT24', 'product_RESPOND': 'RESP', 'product_FILTER': 'FILTER',
}

sprints = data['sprints']
cov = data['coverage_issue_counts']

# Build per-product month + sprint aggregates (only Jan-Jul 2026 buckets shown; Dec sprints roll into their start month if 2026)
pm = defaultdict(lambda: defaultdict(lambda: {'planned': 0, 'done': 0}))
prod_sprints = defaultdict(list)
for s in sprints:
    prod_sprints[s['product']].append(s)
    if s['month'] in MONTHS:
        pm[s['product']][s['month']]['planned'] += s['planned']
        pm[s['product']][s['month']]['done'] += s['done']

# Portfolio + per product closed-sprint rollups
def rollup(items):
    p = sum(s['planned'] for s in items); d = sum(s['done'] for s in items)
    return d, p, (round(d / p * 100) if p else None)

products_payload = []
for prod in PRODUCT_ORDER:
    ss = sorted(prod_sprints[prod], key=lambda s: (s['start'] or '', s['name']))
    closed = [s for s in ss if s['state'] == 'closed']
    d, p, pc = rollup(closed)
    monthly = []
    for m in MONTHS:
        cell = pm[prod].get(m)
        if cell and cell['planned']:
            monthly.append({'month': MONTH_LABEL[m], 'planned': cell['planned'],
                            'done': cell['done'], 'pct': round(cell['done'] / cell['planned'] * 100)})
        else:
            monthly.append({'month': MONTH_LABEL[m], 'planned': 0, 'done': 0, 'pct': None})
    products_payload.append({
        'name': prod, 'key': KEY_BY_NAME[prod],
        'closedDone': d, 'closedPlanned': p, 'closedPct': pc,
        'downloaded': cov[KEY_BY_NAME[prod]],
        'monthly': monthly,
        'sprints': [{'name': s['name'], 'window': (f"{s['start']} → {s['end']}" if s['start'] else '—'),
                     'state': s['state'], 'planned': s['planned'], 'done': s['done'],
                     'notDone': s['planned'] - s['done'], 'pct': s['pct'], 'month': s['month']}
                    for s in ss],
    })

closed_all = [s for s in sprints if s['state'] == 'closed']
active_all = [s for s in sprints if s['state'] == 'active']
pd_all, pp_all, ppct_all = rollup(closed_all)

payload = {
    'generated': data['generated'],
    'months': [MONTH_LABEL[m] for m in MONTHS],
    'portfolio': {'done': pd_all, 'planned': pp_all, 'pct': ppct_all,
                  'sprintCount': len(sprints), 'closed': len(closed_all), 'active': len(active_all),
                  'totalIssues': sum(cov.values())},
    'products': products_payload,
}

HTML = """<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="utf-8"/>
<meta name="viewport" content="width=device-width, initial-scale=1"/>
<title>Sprint Completion Report — Securly Engineering</title>
<style>
  :root {
    --bg:#0f172a; --panel:#1e293b; --panel2:#273449; --ink:#e2e8f0; --muted:#94a3b8;
    --line:#334155; --good:#22c55e; --ok:#84cc16; --warn:#eab308; --bad:#f97316; --crit:#ef4444;
    --accent:#38bdf8;
  }
  * { box-sizing:border-box; }
  body { margin:0; background:var(--bg); color:var(--ink);
    font-family:-apple-system,BlinkMacSystemFont,"Segoe UI",Roboto,Helvetica,Arial,sans-serif; font-size:14px; }
  header { padding:24px 28px; border-bottom:1px solid var(--line); background:linear-gradient(180deg,#111c33,#0f172a); }
  h1 { margin:0 0 6px; font-size:22px; }
  .sub { color:var(--muted); font-size:13px; }
  .wrap { padding:20px 28px 60px; max-width:1500px; margin:0 auto; }
  .cards { display:flex; gap:14px; flex-wrap:wrap; margin:18px 0 26px; }
  .card { background:var(--panel); border:1px solid var(--line); border-radius:12px; padding:16px 18px; min-width:150px; }
  .card .n { font-size:26px; font-weight:700; }
  .card .l { color:var(--muted); font-size:12px; margin-top:2px; }
  h2 { font-size:16px; margin:30px 0 12px; border-left:3px solid var(--accent); padding-left:10px; }
  table { border-collapse:collapse; width:100%; background:var(--panel); border-radius:10px; overflow:hidden; }
  th, td { padding:9px 11px; text-align:left; border-bottom:1px solid var(--line); white-space:nowrap; }
  th { background:var(--panel2); color:var(--muted); font-weight:600; font-size:12px; text-transform:uppercase; letter-spacing:.03em; position:sticky; top:0; }
  td.num, th.num { text-align:right; font-variant-numeric:tabular-nums; }
  tr:hover td { background:#20304a; }
  .pill { display:inline-block; min-width:52px; text-align:center; padding:3px 8px; border-radius:999px; font-weight:700; font-size:12px; color:#0b1220; }
  .p-good{background:var(--good);} .p-ok{background:var(--ok);} .p-warn{background:var(--warn);}
  .p-bad{background:var(--bad);} .p-crit{background:var(--crit);} .p-none{background:#475569; color:#cbd5e1;}
  .state { font-size:11px; padding:2px 7px; border-radius:6px; }
  .st-closed{ background:#334155; color:#cbd5e1; }
  .st-active{ background:#0ea5e9; color:#04283b; font-weight:700; }
  .bar { height:8px; border-radius:6px; background:#334155; overflow:hidden; min-width:80px; display:inline-block; vertical-align:middle; width:110px; }
  .bar > i { display:block; height:100%; }
  .controls { margin:8px 0 18px; }
  select, input { background:var(--panel2); color:var(--ink); border:1px solid var(--line); border-radius:8px; padding:7px 10px; font-size:13px; }
  details { background:var(--panel); border:1px solid var(--line); border-radius:12px; margin:12px 0; overflow:hidden; }
  summary { cursor:pointer; padding:14px 18px; font-size:15px; font-weight:600; list-style:none; display:flex; align-items:center; gap:12px; }
  summary::-webkit-details-marker { display:none; }
  summary .caret { color:var(--muted); transition:transform .15s; }
  details[open] summary .caret { transform:rotate(90deg); }
  summary .spacer { flex:1; }
  .mono { font-variant-numeric:tabular-nums; }
  .scroll { overflow-x:auto; }
  .legend { color:var(--muted); font-size:12px; margin:6px 0 0; }
  .legend b{ color:var(--ink); }
  .note { color:var(--muted); font-size:12px; margin-top:8px; }
  .prodgrid td:first-child { font-weight:600; }
  .heat { text-align:center; font-weight:700; color:#0b1220; border-radius:6px; }
  footer { color:var(--muted); font-size:12px; padding:22px 28px; border-top:1px solid var(--line); }
</style>
</head>
<body>
<header>
  <h1>Sprint Completion Report — Planned vs Completed</h1>
  <div class="sub">Securly Engineering · all products · 1 Jan 2026 → 15 Jul 2026 · source: securly.atlassian.net · generated __GEN__</div>
</header>
<div class="wrap">
  <div class="cards" id="cards"></div>

  <h2>Portfolio — monthly completion heatmap (all products)</h2>
  <div class="legend">Cell = completion % (issues Done ÷ planned) for sprints starting that month. Hover a cell for counts. <b>Jul is in-flight.</b></div>
  <div class="scroll"><table id="heatmap" class="prodgrid"></table></div>

  <h2>Delivery ranking — closed sprints (Jan–Jun 2026)</h2>
  <div class="scroll"><table id="ranking"></table></div>

  <h2>Per-product detail — monthly &amp; sprint level</h2>
  <div class="controls">
    <label>Filter sprints: </label>
    <select id="stateFilter">
      <option value="all">All states</option>
      <option value="closed">Closed only</option>
      <option value="active">Active only</option>
    </select>
    <input id="search" placeholder="search sprint name…" />
  </div>
  <div id="products"></div>

  <p class="note">Completion = issues in the <b>Done</b> status category ÷ total issues in the sprint's final scope.
  This is a scope-vs-done proxy (no changelog): it does not separate committed-at-start from added-mid-sprint work.
  Sprints are matched to each product's own board(s). July sprints are active/in-flight.</p>
</div>
<footer>Generated from <code>analysis_output.json</code> · <code>python3 build_html_report.py</code></footer>

<script>
const DATA = __DATA__;

function cls(p){ if(p===null) return 'p-none'; if(p>=90) return 'p-good'; if(p>=80) return 'p-ok'; if(p>=65) return 'p-warn'; if(p>=50) return 'p-bad'; return 'p-crit'; }
function heatColor(p){ if(p===null) return '#475569';
  const stops=[[50,'#ef4444'],[65,'#f97316'],[80,'#eab308'],[90,'#84cc16'],[100,'#22c55e']];
  for(const [t,c] of stops){ if(p<t) return c; } return '#22c55e'; }
function pill(p){ return p===null? '<span class="pill p-none">—</span>' : `<span class="pill ${cls(p)}">${p}%</span>`; }

// Cards
const pf = DATA.portfolio;
document.getElementById('cards').innerHTML = [
  ['Portfolio completion', pf.pct+'%', 'closed sprints (Jan–Jun)'],
  ['Issues done / planned', pf.done.toLocaleString()+' / '+pf.planned.toLocaleString(), 'closed sprints'],
  ['Sprints analysed', pf.sprintCount, pf.closed+' closed · '+pf.active+' active'],
  ['Products', DATA.products.length, 'tracked lines'],
  ['Issues in dataset', pf.totalIssues.toLocaleString(), 'downloaded from Jira'],
].map(([l,n,s])=>`<div class="card"><div class="n">${n}</div><div class="l">${l}</div><div class="l">${s}</div></div>`).join('');

// Heatmap
let h = '<thead><tr><th>Product</th>' + DATA.months.map(m=>`<th class="num">${m}</th>`).join('') + '</tr></thead><tbody>';
for(const pr of DATA.products){
  h += `<tr><td>${pr.name} <span class="l" style="color:var(--muted)">(${pr.key})</span></td>`;
  for(const m of pr.monthly){
    if(m.pct===null){ h += '<td class="num"><span style="color:var(--muted)">—</span></td>'; }
    else { h += `<td class="num"><span class="heat" title="${m.done}/${m.planned}" style="display:inline-block;min-width:46px;padding:4px 6px;background:${heatColor(m.pct)}">${m.pct}%</span></td>`; }
  }
  h += '</tr>';
}
h += '</tbody>';
document.getElementById('heatmap').innerHTML = h;

// Ranking
const ranked = DATA.products.filter(p=>p.closedPlanned>0).slice().sort((a,b)=>b.closedPct-a.closedPct);
let r = '<thead><tr><th>#</th><th>Product</th><th class="num">Done / Planned</th><th>Completion</th><th></th></tr></thead><tbody>';
ranked.forEach((p,i)=>{
  r += `<tr><td class="num">${i+1}</td><td>${p.name} <span class="l" style="color:var(--muted)">(${p.key})</span></td>`+
       `<td class="num mono">${p.closedDone.toLocaleString()} / ${p.closedPlanned.toLocaleString()}</td>`+
       `<td>${pill(p.closedPct)}</td>`+
       `<td><span class="bar"><i style="width:${p.closedPct}%;background:${heatColor(p.closedPct)}"></i></span></td></tr>`;
});
r += '</tbody>';
document.getElementById('ranking').innerHTML = r;

// Per-product detail
function render(){
  const stateF = document.getElementById('stateFilter').value;
  const q = document.getElementById('search').value.trim().toLowerCase();
  let out = '';
  for(const pr of DATA.products){
    let sp = pr.sprints;
    if(stateF!=='all') sp = sp.filter(s=>s.state===stateF);
    if(q) sp = sp.filter(s=>s.name.toLowerCase().includes(q));
    // monthly mini-table
    let mtbl = '<div class="scroll"><table><thead><tr><th>Month</th>'+DATA.months.map(m=>`<th class="num">${m}</th>`).join('')+'</tr></thead><tbody>';
    mtbl += '<tr><td>Completion</td>'+pr.monthly.map(m=>`<td class="num">${m.pct===null?'—':pill(m.pct)}</td>`).join('')+'</tr>';
    mtbl += '<tr><td>Done / Planned</td>'+pr.monthly.map(m=>`<td class="num mono">${m.planned?m.done+'/'+m.planned:'—'}</td>`).join('')+'</tr>';
    mtbl += '</tbody></table></div>';
    // sprint table
    let stbl = '<div class="scroll"><table><thead><tr><th>Sprint</th><th>Window</th><th>State</th><th class="num">Planned</th><th class="num">Done</th><th class="num">Not done</th><th>Completion</th><th></th></tr></thead><tbody>';
    if(sp.length===0){ stbl += '<tr><td colspan="8" style="color:var(--muted)">no sprints match filter</td></tr>'; }
    for(const s of sp){
      stbl += `<tr><td class="mono">${s.name}</td><td class="mono" style="color:var(--muted)">${s.window}</td>`+
              `<td><span class="state st-${s.state}">${s.state}</span></td>`+
              `<td class="num">${s.planned}</td><td class="num">${s.done}</td><td class="num">${s.notDone}</td>`+
              `<td>${pill(s.pct)}</td>`+
              `<td><span class="bar"><i style="width:${s.pct}%;background:${heatColor(s.pct)}"></i></span></td></tr>`;
    }
    stbl += '</tbody></table></div>';
    out += `<details><summary><span class="caret">▶</span> ${pr.name} <span class="l" style="color:var(--muted)">(${pr.key})</span>`+
           `<span class="spacer"></span>${pill(pr.closedPct)} <span class="l" style="color:var(--muted)">closed · ${pr.closedDone}/${pr.closedPlanned} · ${pr.downloaded.toLocaleString()} issues</span></summary>`+
           `<div style="padding:0 18px 18px">`+
           `<div class="legend" style="margin:10px 0 6px"><b>Monthly</b></div>${mtbl}`+
           `<div class="legend" style="margin:16px 0 6px"><b>Per sprint</b></div>${stbl}`+
           `</div></details>`;
  }
  document.getElementById('products').innerHTML = out;
}
document.getElementById('stateFilter').addEventListener('change', render);
document.getElementById('search').addEventListener('input', render);
render();
</script>
</body>
</html>
"""

html = HTML.replace('__GEN__', payload['generated']).replace('__DATA__', json.dumps(payload))
out = os.path.join(HERE, 'SPRINT_COMPLETION_REPORT.html')
open(out, 'w').write(html)
print('HTML written:', out, len(html), 'chars')
