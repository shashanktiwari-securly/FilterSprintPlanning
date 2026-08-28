const JIRA_CLOUD_ID = '28cddaa0-3ea8-450b-b2e6-df904c378dc4';
const JIRA_SEARCH = 'https://api.atlassian.com/ex/jira/' + JIRA_CLOUD_ID + '/rest/api/3/search/jql';
const ISSUE_FIELDS = [
  'summary', 'status', 'issuetype', 'priority', 'created', 'updated',
  'resolutiondate', 'statuscategorychangedate', 'project', 'assignee',
  'customfield_11201',
];
const CRED_EMAIL = 'zd-jira-email';
const CRED_TOKEN = 'zd-jira-token';
const MONTH_NAMES = ['Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun', 'Jul', 'Aug', 'Sep', 'Oct', 'Nov', 'Dec'];

function getJiraCreds() {
  try {
    const email = localStorage.getItem(CRED_EMAIL) || '';
    const token = localStorage.getItem(CRED_TOKEN) || '';
    if (email && token) return { email, token };
  } catch (e) {}
  return null;
}

function setJiraCreds(email, token) {
  localStorage.setItem(CRED_EMAIL, email);
  localStorage.setItem(CRED_TOKEN, token);
}

function clearJiraCreds() {
  try {
    localStorage.removeItem(CRED_EMAIL);
    localStorage.removeItem(CRED_TOKEN);
  } catch (e) {}
}

function utcDate(iso) {
  const [y, m, d] = iso.split('-').map(Number);
  return new Date(Date.UTC(y, m - 1, d));
}

function isoFromUtc(d) {
  return d.toISOString().slice(0, 10);
}

function addUtcDays(d, n) {
  const x = new Date(d.getTime());
  x.setUTCDate(x.getUTCDate() + n);
  return x;
}

function mondayOf(d) {
  const day = d.getUTCDay();
  const offset = day === 0 ? 6 : day - 1;
  return addUtcDays(d, -offset);
}

function formatRange(start, end) {
  const a = start.getUTCDate() + ' ' + MONTH_NAMES[start.getUTCMonth()];
  const b = end.getUTCDate() + ' ' + MONTH_NAMES[end.getUTCMonth()];
  if (start.getTime() === end.getTime()) return a;
  if (start.getUTCFullYear() !== end.getUTCFullYear()) {
    return a + ' ' + start.getUTCFullYear() + ' – ' + b + ' ' + end.getUTCFullYear();
  }
  return a + ' – ' + b;
}

function isoWeekId(d) {
  const tmp = new Date(Date.UTC(d.getUTCFullYear(), d.getUTCMonth(), d.getUTCDate()));
  const day = tmp.getUTCDay() || 7;
  tmp.setUTCDate(tmp.getUTCDate() + 4 - day);
  const yearStart = new Date(Date.UTC(tmp.getUTCFullYear(), 0, 1));
  const week = Math.ceil((((tmp - yearStart) / 86400000) + 1) / 7);
  return tmp.getUTCFullYear() + '-W' + String(week).padStart(2, '0');
}

function buildWeeks(startIso, endIso) {
  const start = utcDate(startIso);
  const end = utcDate(endIso);
  const weeks = [];
  let cursor = mondayOf(start);
  while (cursor <= end) {
    const isoEnd = addUtcDays(cursor, 6);
    const periodStart = cursor < start ? start : cursor;
    const periodEnd = isoEnd > end ? end : isoEnd;
    if (periodEnd >= start) {
      weeks.push({
        id: isoWeekId(periodStart),
        label: formatRange(periodStart, periodEnd),
        start: isoFromUtc(periodStart),
        end: isoFromUtc(periodEnd),
        partial: periodStart > cursor || periodEnd < isoEnd,
      });
    }
    cursor = addUtcDays(cursor, 7);
  }
  return weeks;
}

function emptyCounts() {
  return { created: 0, escape_defect: 0, support_request: 0, done: 0, open: 0, zendesk: 0 };
}

function bump(bucket, issue) {
  bucket.created += 1;
  if (issue.type === 'Escape Defect') bucket.escape_defect += 1;
  else bucket.support_request += 1;
  if (issue.is_done) bucket.done += 1;
  else bucket.open += 1;
  bucket.zendesk += issue.zendesk_count || 0;
}

function weekFor(weeks, createdDate) {
  for (const week of weeks) {
    if (week.start <= createdDate && createdDate <= week.end) return week;
  }
  return weeks[weeks.length - 1];
}

function mapRawIssue(raw, projectsByKey, weeks, createdFrom) {
  const fields = raw.fields || {};
  const project = fields.project || {};
  const projectKey = project.key;
  const meta = projectsByKey[projectKey];
  if (!meta) return null;
  const createdRaw = fields.created || '';
  const createdDate = createdRaw.slice(0, 10);
  if (!createdDate || createdDate < createdFrom) return null;
  let zd = fields.customfield_11201 || 0;
  zd = parseInt(zd, 10);
  if (!Number.isFinite(zd)) zd = 0;
  const status = fields.status || {};
  const statusCat = ((status.statusCategory || {}).name) || '';
  const week = weekFor(weeks, createdDate);
  return {
    key: raw.key,
    url: 'https://securly.atlassian.net/browse/' + raw.key,
    summary: fields.summary || '',
    type: (fields.issuetype || {}).name || '',
    priority: (fields.priority || {}).name || null,
    zendesk_count: zd,
    status: status.name || '',
    status_category: statusCat,
    resolution: null,
    assignee: (fields.assignee && fields.assignee.displayName) || 'Unassigned',
    reporter: '—',
    project_key: projectKey,
    project_name: meta.name,
    project_label: meta.label,
    created: createdRaw,
    created_date: createdDate,
    resolved: fields.resolutiondate || null,
    resolved_date: fields.resolutiondate ? String(fields.resolutiondate).slice(0, 10) : null,
    created_week: {
      id: week.id,
      label: week.label,
      start: week.start,
      end: week.end,
      partial: week.partial,
    },
    is_done: statusCat === 'Done',
  };
}

function assembleFromJira(rawIssues, base) {
  const createdFrom = (base.filters && base.filters.created_from) || '2026-08-01';
  const fromLabel = (base.filters && base.filters.created_from_label) || '1 Aug 2026';
  const now = new Date();
  const snapshot = isoFromUtc(new Date(Date.UTC(now.getUTCFullYear(), now.getUTCMonth(), now.getUTCDate())));
  const weeks = buildWeeks(createdFrom, snapshot);
  const projects = base.projects || [];
  const projectsByKey = {};
  for (const p of projects) projectsByKey[p.key] = p;
  const issues = [];
  const seen = {};
  for (const raw of rawIssues) {
    const issue = mapRawIssue(raw, projectsByKey, weeks, createdFrom);
    if (!issue || seen[issue.key]) continue;
    seen[issue.key] = true;
    issues.push(issue);
  }
  issues.sort((a, b) => (a.created + a.key).localeCompare(b.created + b.key));

  const productKpis = projects.map((proj) => {
    const bucket = emptyCounts();
    for (const issue of issues) {
      if (issue.project_key === proj.key) bump(bucket, issue);
    }
    return {
      ...proj,
      ...bucket,
      done_pct: bucket.created ? Math.round(100 * bucket.done / bucket.created) : 0,
      not_done_pct: bucket.created ? Math.round(100 * bucket.open / bucket.created) : 0,
    };
  });
  productKpis.sort((a, b) => a.label.localeCompare(b.label, undefined, { sensitivity: 'base' }));

  const weekly = weeks.map((week) => {
    const by_project = {};
    for (const p of projects) by_project[p.key] = emptyCounts();
    const totals = emptyCounts();
    for (const issue of issues) {
      if ((issue.created_week || {}).id !== week.id) continue;
      bump(by_project[issue.project_key], issue);
      bump(totals, issue);
    }
    return { ...week, by_project, totals };
  });

  const kpis = emptyCounts();
  for (const issue of issues) bump(kpis, issue);
  const ranked = [...productKpis].sort((a, b) => b.created - a.created || a.label.localeCompare(b.label));
  const top = ranked.filter((p) => p.created > 0).slice(0, 5);
  const zero = productKpis.filter((p) => p.created === 0).map((p) => p.label).sort();
  const topTxt = top.map((p) => p.label + ' ' + p.created).join(', ');
  let headline = kpis.created + ' Zendesk-linked tickets created since ' + fromLabel
    + ' (' + kpis.escape_defect + ' Escape Defect, ' + kpis.support_request + ' Support Request). '
    + kpis.done + ' Done (statusCategory = Done) vs ' + kpis.open + ' not Done (statusCategory != Done). '
    + 'Highest intake: ' + topTxt + '.';
  if (zero.length) headline += ' No matching tickets yet: ' + zero.join(', ') + '.';

  const generated = now.toISOString().replace(/\.\d{3}Z$/, 'Z');
  return {
    ...base,
    generated_at: generated,
    snapshot_date: snapshot,
    live: true,
    product_kpis: productKpis,
    weekly,
    created_issues: issues,
    headline,
    kpis: {
      created: kpis.created,
      created_escape_defect: kpis.escape_defect,
      created_support_request: kpis.support_request,
      created_done: kpis.done,
      created_open: kpis.open,
      done_pct: kpis.created ? Math.round(100 * kpis.done / kpis.created) : 0,
      not_done_pct: kpis.created ? Math.round(100 * kpis.open / kpis.created) : 0,
    },
  };
}

async function fetchJiraIssues(email, token) {
  const headers = {
    Accept: 'application/json',
    'Content-Type': 'application/json',
    Authorization: 'Basic ' + btoa(email + ':' + token),
  };
  const issues = [];
  let next = null;
  for (let i = 0; i < 20; i++) {
    const body = {
      jql: DATA.jql.created,
      maxResults: 100,
      fields: ISSUE_FIELDS,
    };
    if (next) body.nextPageToken = next;
    const r = await fetch(JIRA_SEARCH, {
      method: 'POST',
      headers,
      body: JSON.stringify(body),
      cache: 'no-store',
      credentials: 'omit',
    });
    if (!r.ok) {
      const text = await r.text();
      throw new Error('Jira HTTP ' + r.status + (text ? ': ' + text.slice(0, 180) : ''));
    }
    const page = await r.json();
    issues.push(...(page.issues || []));
    next = page.nextPageToken;
    if (page.isLast || !next) break;
  }
  return issues;
}

function syncJiraButton() {
  const btn = $('jiraToggle');
  if (!btn) return;
  const creds = getJiraCreds();
  btn.textContent = creds ? 'Jira connected' : 'Connect Jira';
  btn.setAttribute('aria-pressed', creds ? 'true' : 'false');
}

function bindJiraPanel() {
  const panel = $('jiraPanel');
  const toggle = $('jiraToggle');
  if (!panel || !toggle) return;
  const creds = getJiraCreds();
  if (creds) $('jiraEmail').value = creds.email;
  syncJiraButton();
  toggle.addEventListener('click', () => {
    panel.classList.toggle('open');
  });
  $('jiraSave').addEventListener('click', async () => {
    const email = $('jiraEmail').value.trim();
    const token = $('jiraToken').value.trim();
    const msg = $('jiraMsg');
    if (!email || !token) {
      msg.textContent = 'Email and API token are required.';
      return;
    }
    setJiraCreds(email, token);
    $('jiraToken').value = '';
    msg.textContent = 'Querying Jira…';
    syncJiraButton();
    setLiveStatus('refreshing from Jira…', '');
    try {
      await refreshDashboard();
      paint();
      msg.textContent = 'Connected. Counts refresh from Jira on every page load.';
      panel.classList.remove('open');
    } catch (e) {
      msg.textContent = e.message || String(e);
      setLiveStatus('Jira connect failed · ' + (e.message || e), 'stale');
    }
  });
  $('jiraClear').addEventListener('click', () => {
    clearJiraCreds();
    $('jiraToken').value = '';
    $('jiraMsg').textContent = 'Disconnected. Reload uses the last snapshot until you connect again.';
    syncJiraButton();
  });
}

async function refreshDashboard() {
  const creds = getJiraCreds();
  if (creds) {
    const raw = await fetchJiraIssues(creds.email, creds.token);
    DATA = assembleFromJira(raw, DATA);
    DATA._fromLiveApi = true;
    return 'jira';
  }
  return loadLive();
}
