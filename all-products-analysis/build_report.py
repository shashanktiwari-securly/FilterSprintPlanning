"""
Build the markdown program-manager report from analysis_output.json.
Outputs: SPRINT_COMPLETION_REPORT.md
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

# product -> month -> {planned, done}
pm = defaultdict(lambda: defaultdict(lambda: {'planned': 0, 'done': 0}))
prod_sprints = defaultdict(list)
for s in sprints:
    prod_sprints[s['product']].append(s)
    if s['month']:
        pm[s['product']][s['month']]['planned'] += s['planned']
        pm[s['product']][s['month']]['done'] += s['done']


def pct(done, planned):
    return round(done / planned * 100) if planned else None


def cell(d):
    if d and d['planned']:
        return f"{pct(d['done'], d['planned'])}% ({d['done']}/{d['planned']})"
    return "—"


lines = []
w = lines.append

w("# Securly Engineering — Sprint Completion Report (Planned vs Completed)")
w("")
w(f"**Generated:** {data['generated']}  |  **Window:** 1 Jan 2026 → 15 Jul 2026  |  **Source:** securly.atlassian.net (Jira MCP)")
w("")
w("Prepared from a program-manager viewpoint across all 10 tracked products. "
  "Completion is measured as **issues in the *Done* status category ÷ total issues in the sprint's final scope**.")
w("")

# ---------- Executive summary ----------
w("## 1. Executive summary")
w("")
# portfolio closed-sprint completion (exclude active/July in-flight)
closed = [s for s in sprints if s['state'] == 'closed']
tot_p = sum(s['planned'] for s in closed)
tot_d = sum(s['done'] for s in closed)
active = [s for s in sprints if s['state'] == 'active']
w(f"- **{len(sprints)} sprints** analysed across **10 products** "
  f"({len(closed)} closed, {len(active)} active/in-flight).")
w(f"- **Portfolio delivery on closed sprints: {pct(tot_d, tot_p)}%** "
  f"({tot_d:,} of {tot_p:,} committed issues completed).")
w("- Completion is highest for the **product-line teams** (Home, Aware, RESPOND, MDM/Classroom) "
  "and lowest for **Platform** and **AIChat**, which carry more multi-sprint / research work that rolls over.")
w("- **July figures are low by design** — those sprints are still **active** (in-flight) as of the report date, "
  "so their scope is only partially burned down.")
w("")

# ---------- Portfolio ranking (closed only) ----------
w("### Delivery ranking — closed sprints only (Jan–Jun 2026)")
w("")
w("| Rank | Product | Completed / Planned | Completion % |")
w("|------|---------|--------------------|--------------|")
rank = []
for prod in PRODUCT_ORDER:
    cs = [s for s in prod_sprints[prod] if s['state'] == 'closed']
    p = sum(s['planned'] for s in cs); d = sum(s['done'] for s in cs)
    if p:
        rank.append((prod, d, p, pct(d, p)))
rank.sort(key=lambda x: -x[3])
for i, (prod, d, p, pc) in enumerate(rank, 1):
    w(f"| {i} | {prod} ({KEY_BY_NAME[prod]}) | {d:,} / {p:,} | **{pc}%** |")
w("")

# ---------- Monthly matrix ----------
w("## 2. Monthly completion comparison (all products)")
w("")
w("Each cell = completion % with `(done/planned)` issue counts. A sprint is attributed to the "
  "month it **started** in. Months with no sprint for a product show `—`.")
w("")
hdr = "| Product | " + " | ".join(MONTH_LABEL[m] for m in MONTHS) + " |"
w(hdr)
w("|" + "---|" * (len(MONTHS) + 1))
for prod in PRODUCT_ORDER:
    row = [f"{prod} ({KEY_BY_NAME[prod]})"]
    for m in MONTHS:
        row.append(cell(pm[prod].get(m)))
    w("| " + " | ".join(row) + " |")
w("")
w("> Jul 2026 sprints are **active/in-flight** — low % reflects work still in progress, not a delivery miss.")
w("")

# ---------- Per-product sprint detail ----------
w("## 3. Sprint-level detail by product")
w("")
for prod in PRODUCT_ORDER:
    ss = sorted(prod_sprints[prod], key=lambda s: (s['start'] or '', s['name']))
    cs = [s for s in ss if s['state'] == 'closed']
    p = sum(s['planned'] for s in cs); d = sum(s['done'] for s in cs)
    avg = pct(d, p)
    w(f"### {prod}  (`{KEY_BY_NAME[prod]}`)")
    w("")
    w(f"Closed-sprint completion: **{avg}%** ({d}/{p} issues). Downloaded issues in dataset: {cov[KEY_BY_NAME[prod]]:,}.")
    w("")
    w("| Sprint | Window | State | Planned | Done | Completion % |")
    w("|--------|--------|-------|---------|------|--------------|")
    for s in ss:
        window = f"{s['start']} → {s['end']}" if s['start'] else "—"
        pcs = f"{s['pct']}%"
        state = s['state']
        w(f"| {s['name']} | {window} | {state} | {s['planned']} | {s['done']} | {pcs} |")
    w("")

# ---------- Methodology ----------
w("## 4. Methodology, data coverage & caveats")
w("")
w("**Data pull.** All issues that belong to a 2026 sprint were exported per project via the Jira MCP "
  "(`searchJiraIssuesUsingJql`), keyset-paginated to completion. Normalised issue records "
  "(`key, project, issuetype, status, statusCategory, created, resolved, storyPoints, sprints[]`) "
  "are stored as JSON Lines under `all-products-analysis/data/<PROJECT>.jsonl`.")
w("")
w("**Downloaded issue counts (post-dedupe):**")
w("")
w("| Project | Issues |")
w("|---------|--------|")
for prod in PRODUCT_ORDER:
    w(f"| {prod} ({KEY_BY_NAME[prod]}) | {cov[KEY_BY_NAME[prod]]:,} |")
w(f"| **Total** | **{sum(cov.values()):,}** |")
w("")
w("**Metric definitions.**")
w("- *Planned* = distinct issues whose sprint history includes the sprint (final sprint scope).")
w("- *Completed* = issues currently in the **Done** status category (`done`).")
w("- *Completion %* = Completed ÷ Planned.")
w("- Sprints are filtered to those **active or closed** with activity on/after 1 Jan 2026, and matched to "
  "each product's own board(s) to avoid cross-board contamination from issues that moved between projects.")
w("")
w("**Caveats.**")
w("1. **Scope proxy, not commitment snapshot.** Without sprint-report changelogs this measures *final scope vs "
  "current Done*, so it does not separate committed-at-start work from items added mid-sprint. For true "
  "committed-vs-added tracking, see the richer `product_FILTER/` datasets from earlier work.")
w("2. **Current status.** \"Done\" uses the issue's *current* status category, not its status at sprint close; "
  "a reopened item can shift historical numbers slightly.")
w("3. **Active sprints (Jul).** In-flight sprints are shown for completeness but are not delivery misses.")
w("4. **Shared board products.** oncall / RESPOND / FILTER share the core board sprint pool; each product's "
  "table reflects only the sprints its own issues participated in.")
w("")
w("**Reproduce:** `python3 analyze.py` (recompute metrics) then `python3 build_report.py` (regenerate this report).")

open(os.path.join(HERE, 'SPRINT_COMPLETION_REPORT.md'), 'w').write("\n".join(lines) + "\n")
print("Report written:", len("\n".join(lines)), "chars")
