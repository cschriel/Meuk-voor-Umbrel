const { test } = require('node:test');
const assert = require('node:assert/strict');
const { route, redact } = require('../../koningkoffie-checkmate/docker-proxy.js.template');
const id = 'a'.repeat(64);

test('allows the exact Checkmate Docker API subset and bounds streaming', () => {
  assert.equal(route('GET', '/_ping').kind, 'ping');
  assert.equal(route('GET', '/v1.45/containers/json?all=true').kind, 'list');
  assert.equal(route('GET', '/containers/' + id + '/json').kind, 'json');
  assert.equal(route('GET', '/containers/' + id + '/stats?stream=true').path, '/containers/' + id + '/stats?stream=false');
  assert.match(route('GET', '/containers/' + id + '/logs?follow=true&tail=all').path, /follow=false.*tail=500/);
});
test('rejects mutations, arbitrary file reads, exec, upgrades and encoded paths', () => {
  for (const method of ['POST', 'PUT', 'DELETE', 'PATCH', 'CONNECT']) assert.equal(route(method, '/containers/json'), null);
  for (const path of ['/containers/create', '/containers/' + id + '/archive?path=/etc/passwd',
    '/exec/id/json', '/images/json', '/containers/' + id + '/export',
    '/containers/../json', '/containers/%2e%2e/json', '//containers/json',
    'http://docker/containers/json', '/v1.45/containers/' + id + '/attach']) assert.equal(route('GET', path), null, path);
});
test('inspection does not disclose container environment credentials', () => {
  const body = redact('json', JSON.stringify({Id: id, Config: { Env: ['PASSWORD=secret'] },
    State: { StartedAt: 'now', Health: { Status: 'healthy', Log: ['secret'] } },
    RestartCount: 1, NetworkSettings: { Ports: {} }, Mounts: []}));
  assert.ok(!body.includes('secret'));
  assert.equal(JSON.parse(body).State.Health.Status, 'healthy');
  const list = redact('list', JSON.stringify([{ Id: id, Names: ['/test'], Command: 'secret', Labels: { password: 'secret' } }]));
  assert.ok(!list.includes('secret'));
});
