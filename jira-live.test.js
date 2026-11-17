const assert = require('node:assert/strict');
const test = require('node:test');
const { jiraRequestHeaders } = require('./jira-live.js');

test('session search does not send Authorization: undefined', () => {
  const headers = jiraRequestHeaders({
    Accept: 'application/json',
    'Content-Type': 'application/json',
  });
  const sent = new Headers(headers);
  assert.equal(sent.get('authorization'), null);
  assert.equal(sent.get('accept'), 'application/json');
});

test('token search keeps the Authorization header', () => {
  const headers = jiraRequestHeaders({
    Accept: 'application/json',
    Authorization: 'Bearer scoped-token',
  });
  const sent = new Headers(headers);
  assert.equal(sent.get('authorization'), 'Bearer scoped-token');
});
