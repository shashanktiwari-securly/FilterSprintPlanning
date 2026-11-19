const assert = require('node:assert/strict');
const fs = require('node:fs');
const path = require('node:path');
const test = require('node:test');
const vm = require('node:vm');

function loadLive() {
  const context = {
    console,
    TextEncoder,
    URLSearchParams,
    AbortController,
    setTimeout,
    clearTimeout,
    fetch() {
      throw new Error('unexpected fetch');
    },
    btoa(value) {
      return Buffer.from(value, 'binary').toString('base64');
    },
    localStorage: {
      getItem() { return null; },
      setItem() {},
      removeItem() {},
    },
    DATA: {},
  };
  vm.createContext(context);
  vm.runInContext(
    fs.readFileSync(path.join(__dirname, 'jira-live.js'), 'utf8'),
    context,
  );
  return context;
}

function baseData() {
  return {
    filters: { created_from: '2026-08-01', created_from_label: '1 Aug 2026' },
    projects: [{ key: 'FILTER', name: 'product_FILTER', label: 'Filter' }],
    jql: { created: 'project = FILTER' },
    kpis: { created: 0 },
    live: false,
  };
}

function issue(key, categoryKey, categoryName) {
  return {
    key,
    fields: {
      project: { key: 'FILTER' },
      created: '2026-11-02T15:00:00.000+0800',
      summary: key,
      status: { name: categoryName, statusCategory: { key: categoryKey, name: categoryName } },
      issuetype: { name: 'Escape Defect' },
      customfield_11201: 1,
    },
  };
}

test('a translated Done category still counts as Done', () => {
  const live = loadLive();
  const done = issue('FILTER-9', 'done', '完成');
  const open = issue('FILTER-10', 'indeterminate', '进行中');
  const data = live.assembleFromJira([done, open], baseData());

  assert.equal(data.created_issues.length, 2);
  assert.equal(data.created_issues.find((row) => row.key === 'FILTER-9').is_done, true);
  assert.equal(data.created_issues.find((row) => row.key === 'FILTER-9').status_category, 'Done');
  assert.equal(data.created_issues.find((row) => row.key === 'FILTER-10').is_done, false);
  assert.equal(data.created_issues.find((row) => row.key === 'FILTER-10').status_category, 'In Progress');
  assert.equal(data.kpis.created, 2);
  assert.equal(data.kpis.created_done, 1);
  assert.equal(data.kpis.created_open, 1);
  assert.equal(data.product_kpis[0].done, 1);
  assert.equal(data.product_kpis[0].open, 1);
  const week = data.weekly.find((row) => row.totals.created === 2);
  assert.ok(week);
  assert.equal(week.totals.done, 1);
  assert.equal(week.totals.open, 1);
});

test('an English category name still counts when the key is absent', () => {
  const live = loadLive();
  const raw = issue('FILTER-11', '', 'Done');
  delete raw.fields.status.statusCategory.key;
  const data = live.assembleFromJira([raw], baseData());
  assert.equal(data.kpis.created_done, 1);
  assert.equal(data.created_issues[0].status_category, 'Done');
});
