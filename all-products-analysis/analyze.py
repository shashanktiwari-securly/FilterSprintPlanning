"""
Sprint completion analysis (planned vs completed) for all products.

Data source: all-products-analysis/data/<PROJECT>.jsonl (one normalized issue per line).
Metric definitions:
  - A sprint is attributed an issue if the issue's sprint-history array contains that sprint.
  - "Planned" = number of issues whose final scope included the sprint (final sprint scope).
  - "Completed" = issues currently in the Done status category (statusCategory == 'done').
  - Completion % = Completed / Planned.
  - Story-point completion uses customfield_10005 / customfield_11247 where populated.
NOTE: This is a scope-vs-done proxy (no changelog), so it does not distinguish
      committed-at-start vs added-mid-sprint. FILTER has deeper committed/added data
      in product_FILTER/ from prior work.
"""
import json, glob, os
from datetime import datetime, timezone
from collections import defaultdict

DATA = os.path.join(os.path.dirname(__file__), 'data')
CUTOFF = datetime(2026, 1, 1, tzinfo=timezone.utc)
TODAY = datetime(2026, 7, 15, tzinfo=timezone.utc)

PRODUCT_NAME = {
    'AICHAT': 'AIChat', 'FLEX': 'FLEX & COM', 'PASS': 'PASS', 'PLATFORM': 'Platform',
    'AWARE': 'product_aware', 'HOME': 'product_home', 'MDMCLASS': 'product_MDM_CLASSROOM',
    'PRODUCT24': 'product_oncall', 'RESP': 'product_RESPOND', 'FILTER': 'product_FILTER',
}
# Each product's "own" board(s) so shared-board contamination is excluded.
PRODUCT_BOARDS = {
    'AICHAT': {1010}, 'FLEX': {400}, 'PASS': {712, 397}, 'PLATFORM': {1213},
    'AWARE': {778}, 'HOME': {368}, 'MDMCLASS': {1013},
    # oncall / RESPOND / FILTER share the "core" boards
    'PRODUCT24': {281, 339}, 'RESP': {281, 339}, 'FILTER': {281, 339},
}
MONTHS = ['2026-01', '2026-02', '2026-03', '2026-04', '2026-05', '2026-06', '2026-07']


def pdt(s):
    if not s:
        return None
    try:
        return datetime.fromisoformat(s.replace('Z', '+00:00'))
    except Exception:
        return None


def sprint_in_scope(sp):
    """Sprint counts if active/closed and it ran/closed on or after Jan 1 2026."""
    state = (sp.get('state') or '').lower()
    if state not in ('active', 'closed'):
        return False
    dates = [pdt(sp.get('startDate')), pdt(sp.get('completeDate')), pdt(sp.get('endDate'))]
    dates = [d for d in dates if d]
    if not dates:
        return state == 'active'
    return any(d >= CUTOFF for d in dates)


def sprint_month(sp):
    d = pdt(sp.get('startDate')) or pdt(sp.get('endDate'))
    return d.strftime('%Y-%m') if d else None


def load_issues(project):
    path = os.path.join(DATA, project + '.jsonl')
    out = []
    with open(path) as f:
        for line in f:
            line = line.strip()
            if line:
                out.append(json.loads(line))
    return out


def analyze():
    all_sprint_rows = []   # per (product, sprint)
    product_month = defaultdict(lambda: defaultdict(lambda: {'planned': 0, 'done': 0}))
    coverage = {}

    for proj in PRODUCT_NAME:
        issues = load_issues(proj)
        coverage[proj] = len(issues)
        boards = PRODUCT_BOARDS[proj]
        # sprint -> aggregated counts (dedupe issues per sprint)
        sprint_stats = {}
        for iss in issues:
            done = iss.get('statusCategory') == 'done'
            sp_pts = iss.get('storyPoints') or 0.0
            seen = set()
            for sp in iss.get('sprints') or []:
                if sp.get('boardId') not in boards:
                    continue
                if not sprint_in_scope(sp):
                    continue
                sid = sp.get('id')
                if sid in seen:
                    continue
                seen.add(sid)
                st = sprint_stats.setdefault(sid, {
                    'name': sp.get('name'), 'state': (sp.get('state') or '').lower(),
                    'month': sprint_month(sp), 'start': (sp.get('startDate') or '')[:10],
                    'end': (sp.get('completeDate') or sp.get('endDate') or '')[:10],
                    'planned': 0, 'done': 0, 'sp_planned': 0.0, 'sp_done': 0.0,
                })
                st['planned'] += 1
                st['sp_planned'] += sp_pts
                if done:
                    st['done'] += 1
                    st['sp_done'] += sp_pts
        for sid, st in sprint_stats.items():
            st['project'] = proj
            st['product'] = PRODUCT_NAME[proj]
            st['pct'] = round(st['done'] / st['planned'] * 100) if st['planned'] else 0
            all_sprint_rows.append(st)
            if st['month']:
                pm = product_month[proj][st['month']]
                pm['planned'] += st['planned']
                pm['done'] += st['done']

    return all_sprint_rows, product_month, coverage


if __name__ == '__main__':
    rows, pm, cov = analyze()
    rows.sort(key=lambda r: (r['product'], r['start']))
    result = {
        'generated': TODAY.strftime('%Y-%m-%d'),
        'coverage_issue_counts': cov,
        'sprints': rows,
        'product_month': {p: dict(m) for p, m in pm.items()},
    }
    with open(os.path.join(os.path.dirname(__file__), 'analysis_output.json'), 'w') as f:
        json.dump(result, f, indent=2)

    print("Downloaded issues per project:", cov)
    print("\nSprint rows:", len(rows))
    # monthly matrix
    print("\n=== MONTHLY COMPLETION % (issues done / planned) ===")
    hdr = f"{'PRODUCT':24}" + ''.join(f"{m[5:]:>9}" for m in MONTHS)
    print(hdr)
    for proj in PRODUCT_NAME:
        name = PRODUCT_NAME[proj]
        cells = []
        for m in MONTHS:
            d = pm[proj].get(m)
            if d and d['planned']:
                cells.append(f"{round(d['done']/d['planned']*100):>7}% ")
            else:
                cells.append(f"{'-':>9}")
        print(f"{name:24}" + ''.join(cells))
