const assert = require('node:assert/strict');
const test = require('node:test');
const { refreshDashboard, connectWithToken, getJiraCreds } = require('./jira-live.js');

const RAW_ISSUE = {
  key: 'FILTER-1',
  fields: {
    project: { key: 'FILTER' },
    created: '2026-11-01T00:00:00.000+0000',
    summary: 'Session ticket',
    status: { name: 'Open', statusCategory: { name: 'To Do' } },
    issuetype: { name: 'Support Request' },
    customfield_11201: 1,
  },
};

function memoryStorage(initial) {
  const store = { ...initial };
  return {
    getItem(key) {
      return Object.prototype.hasOwnProperty.call(store, key) ? store[key] : null;
    },
    setItem(key, value) { store[key] = String(value); },
    removeItem(key) { delete store[key]; },
  };
}

function jsonResponse(body, status) {
  return {
    ok: status == null || (status >= 200 && status < 300),
    status: status || 200,
    json: async () => body,
    text: async () => JSON.stringify(body),
  };
}

function baseData() {
  return {
    filters: { created_from: '2026-08-01', created_from_label: '1 Aug 2026' },
    projects: [{ key: 'FILTER', name: 'product_FILTER', label: 'Filter' }],
    jql: { created: 'project = FILTER' },
    kpis: { created: 141 },
    live: false,
  };
}

test('a rejected saved token still refreshes from the Atlassian session', async () => {
  const calls = [];
  global.localStorage = memoryStorage({
    'zd-jira-email': 'pm@securly.com',
    'zd-jira-token': 'classic-token',
  });
  global.DATA = baseData();
  let snapshotLoads = 0;
  global.loadLive = async () => {
    snapshotLoads += 1;
    return 'snapshot';
  };
  global.fetch = async (url, opts = {}) => {
    calls.push({ url: String(url), credentials: opts.credentials });
    if (String(url).includes('/myself')) return jsonResponse({ accountId: 'abc' });
    if (opts.credentials === 'omit') return jsonResponse({ message: 'Unauthorized' }, 401);
    return jsonResponse({ issues: [RAW_ISSUE], isLast: true });
  };

  const source = await refreshDashboard();

  assert.equal(source, 'session');
  assert.equal(snapshotLoads, 0);
  assert.equal(global.DATA._liveSource, 'session');
  assert.equal(global.DATA.created_issues.length, 1);
  assert.equal(global.DATA.created_issues[0].key, 'FILTER-1');
  assert.ok(calls.some((call) => call.credentials === 'include' && call.url.includes('search/jql')));
});

test('a working token is used and the session is not consulted', async () => {
  const calls = [];
  global.localStorage = memoryStorage({
    'zd-jira-email': 'pm@securly.com',
    'zd-jira-token': 'scoped-token',
  });
  global.DATA = baseData();
  global.loadLive = async () => {
    throw new Error('snapshot should not load');
  };
  global.fetch = async (url, opts = {}) => {
    calls.push({ url: String(url), credentials: opts.credentials });
    return jsonResponse({ issues: [RAW_ISSUE], isLast: true });
  };

  const source = await refreshDashboard();

  assert.equal(source, 'token');
  assert.equal(global.DATA._liveSource, 'token');
  assert.equal(calls.length, 1);
  assert.equal(calls[0].credentials, 'omit');
});

test('Connect Jira does not keep a token that Jira rejected', async () => {
  global.localStorage = memoryStorage({
    'zd-jira-email': 'pm@securly.com',
    'zd-jira-token': 'previous-good-token',
  });
  global.DATA = baseData();
  global.fetch = async (url, opts = {}) => {
    if (opts.credentials === 'omit') return jsonResponse({ message: 'Unauthorized' }, 401);
    return jsonResponse({ accountId: 'abc' });
  };

  await assert.rejects(
    () => connectWithToken('pm@securly.com', 'new-classic-token'),
    /401|scoped token/i,
  );
  const creds = getJiraCreds();
  assert.equal(creds.email, 'pm@securly.com');
  assert.equal(creds.token, 'previous-good-token');
});

test('a failed first connect leaves no token saved', async () => {
  global.localStorage = memoryStorage();
  global.DATA = baseData();
  global.fetch = async (url, opts = {}) => {
    if (opts.credentials === 'omit') return jsonResponse({ message: 'Unauthorized' }, 401);
    return jsonResponse({ accountId: 'abc' });
  };

  await assert.rejects(() => connectWithToken('pm@securly.com', 'classic-token'));
  assert.equal(getJiraCreds(), null);
});
