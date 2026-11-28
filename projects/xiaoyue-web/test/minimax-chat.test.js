const assert = require('assert').strict;
const fs = require('fs');
const path = require('path');
const vm = require('vm');
const { createRequire } = require('module');
const axios = require('axios');
const express = require('express');
const {
  MINIMAX_TEXT_MODEL_CONFIG,
  resolveMiniMaxConfig,
  postMiniMaxChatCompletion,
} = require('../lib/minimax-chat');

const root = path.resolve(__dirname, '..');
const originalEnv = { ...process.env };
const originalAdapter = axios.defaults.adapter;
const requests = [];
let checks = 0;

function configure(env = {}) {
  for (const key of Object.keys(process.env)) {
    if (/^(MINIMAX_|ZHIPU_|OPENCLAW_|OPENCODE_|FEISHU_)/.test(key)) delete process.env[key];
  }
  Object.assign(process.env, { MINIMAX_API_KEY: 'fixture-key', OPENCLAW_ENABLED: 'false' }, env);
}

// Load the real entry point and its Express handlers without opening a listener,
// starting background tasks, reading local credentials, or executing commands.
function loadServer(filename) {
  const app = express();
  app.listen = () => {};
  const wrappedExpress = Object.assign(() => app, express);
  const localRequire = createRequire(path.join(root, filename));
  const context = vm.createContext({
    require(name) {
      if (name === 'express') return wrappedExpress;
      if (name === 'dotenv') return { config() {} };
      if (name === 'fs') return {
        existsSync: () => true,
        readFileSync: () => 'You are a fixture assistant.',
      };
      if (name === 'child_process') return {
        exec: () => { throw new Error('Commands are forbidden in tests'); },
        spawn: () => { throw new Error('Commands are forbidden in tests'); },
      };
      return localRequire(name);
    },
    __dirname: root,
    process,
    console: { log() {}, error() {} },
    setTimeout() {},
  });
  vm.runInContext(fs.readFileSync(path.join(root, filename), 'utf8'), context, { filename });
  return { app, context };
}

async function invoke(app, method, route, body = {}) {
  const layer = app._router.stack.find((entry) => entry.route
    && entry.route.path === route && entry.route.methods[method]);
  assert.ok(layer, `${method} ${route} is registered`);
  let response;
  await layer.route.stack[0].handle({ body }, { json(value) { response = value; } });
  assert.ok(response, 'The handler returns a JSON response');
  return response;
}

function checkRequest(request, model, region) {
  assert.equal(request.url, region === 'cn_zh'
    ? 'https://api.minimaxi.com/v1/chat/completions'
    : 'https://api.minimax.io/v1/chat/completions');
  assert.equal(request.payload.model, model);
  // Omission uses the API's adaptive thinking and max effort defaults for Flash.
  for (const field of ['thinking', 'reasoning_effort', 'service_tier', 'reasoning_split']) {
    assert.equal(Object.prototype.hasOwnProperty.call(request.payload, field), false);
  }
  assert.equal(request.payload.messages.at(-1).content, 'Hello');
  checks += 1;
}

async function main() {
  axios.defaults.adapter = async (config) => {
    // This is the real Axios adapter boundary, after JSON serialization.
    assert.equal(typeof config.data, 'string');
    assert.equal(config.method, 'post');
    assert.ok(config.url.endsWith('/chat/completions'), 'Unexpected outbound request');
    assert.ok(config.headers.Authorization === 'Bearer fixture-key', 'Only fixture credentials are allowed');
    requests.push({ url: config.url, payload: JSON.parse(config.data) });
    return { data: { choices: [{ message: { role: 'assistant', content: 'Fixture reply' } }] },
      status: 200, statusText: 'OK', headers: {}, config };
  };

  configure();
  assert.deepEqual(resolveMiniMaxConfig().modelIds, ['MiniMax-M3.1-Flash', 'MiniMax-M3']);
  assert.equal(resolveMiniMaxConfig().modelId, 'MiniMax-M3.1-Flash');
  assert.deepEqual(MINIMAX_TEXT_MODEL_CONFIG.models[0].thinking, ['adaptive']);
  assert.equal(MINIMAX_TEXT_MODEL_CONFIG.models[0].max_output_tokens, 524288);
  assert.equal(MINIMAX_TEXT_MODEL_CONFIG.models[0].pricing_usd_per_million_tokens.cache_read, 0.015);
  assert.deepEqual(MINIMAX_TEXT_MODEL_CONFIG.models[1].thinking, ['adaptive', 'disabled']);
  assert.equal(resolveMiniMaxConfig({ model: 'custom-model' }).modelSpec, undefined);
  assert.equal(resolveMiniMaxConfig({ model: 'constructor' }).modelSpec, undefined);
  checks += 1;

  const scenarios = [
    { expected: 'MiniMax-M3.1-Flash' },
    { model: 'MiniMax-M3', expected: 'MiniMax-M3' },
    { model: 'MiniMax-M2.7', expected: 'MiniMax-M2.7' },
    { model: 'custom-model', expected: 'custom-model' },
    { saved: 'MiniMax-M2.7', expected: 'MiniMax-M2.7' },
    { saved: 'saved-custom', expected: 'saved-custom' },
    { saved: 'MiniMax-M3', model: 'custom-override', expected: 'custom-override' },
  ];
  for (const filename of ['server.js', 'server-openclaw.js', 'server-with-openclaw.js']) {
    for (const region of ['global_en', 'cn_zh']) {
      for (const scenario of scenarios) {
        configure({ MINIMAX_REGION: region, ...(scenario.saved ? { MINIMAX_MODEL: scenario.saved } : {}) });
        const { app } = loadServer(filename);
        const before = requests.length;
        const response = await invoke(app, 'post', '/api/chat', { message: 'Hello', model: scenario.model });
        assert.equal(response.success, true);
        assert.equal(requests.length, before + 1);
        checkRequest(requests.at(-1), scenario.expected, region);
        if (filename !== 'server.js') {
          assert.equal(requests.at(-1).payload.max_tokens,
            scenario.expected === 'MiniMax-M3.1-Flash' ? 16384 : 200);
        }
        const health = await invoke(app, 'get', filename === 'server-openclaw.js' ? '/health' : '/api/health');
        assert.equal(health.model, scenario.saved || 'MiniMax-M3.1-Flash');
        assert.equal(health.region, region);
      }
    }
  }

  configure();
  const { app, context } = loadServer('server-with-openclaw.js');
  const star = await invoke(app, 'post', '/api/starclaw/chat', {
    message: 'Hello', agentId: 'fixture', agentName: 'Fixture', region: 'cn_zh',
  });
  assert.equal(star.success, true);
  checkRequest(requests.at(-1), 'MiniMax-M3.1-Flash', 'cn_zh');
  assert.equal(requests.at(-1).payload.max_tokens, 16384);
  // Invoke the production webhook's chat function; only its external reply is stubbed.
  vm.runInContext('replyFeishuMessage = async () => {}', context);
  await vm.runInContext('handleFeishuMessage("fixture-id", "Hello", "fixture-chat")', context);
  checkRequest(requests.at(-1), 'MiniMax-M3.1-Flash', 'global_en');
  assert.equal(requests.at(-1).payload.max_tokens, 16384);

  const messages = [{ role: 'user', content: [
    { type: 'text', text: 'Describe this' },
    { type: 'image_url', image_url: { url: 'https://example.com/image.png' } },
    { type: 'video_url', video_url: { url: 'mm_file://fixture-video' } },
  ] }];
  await postMiniMaxChatCompletion({ messages, model: 'saved-custom',
    apiBaseUrl: 'https://custom.example/v1', max_tokens: 123, temperature: 0, top_p: 0.7, stream: false });
  assert.equal(requests.at(-1).url, 'https://custom.example/v1/chat/completions');
  assert.deepEqual(requests.at(-1).payload, {
    model: 'saved-custom', messages, max_tokens: 123, temperature: 0, top_p: 0.7, stream: false,
  });
  checks += 1;

  configure({ MINIMAX_API_BASE: 'https://saved.example/v1', MINIMAX_MODEL: 'saved-custom' });
  const customApp = loadServer('server.js').app;
  await invoke(customApp, 'post', '/api/chat', { message: 'Hello' });
  assert.equal(requests.at(-1).url, 'https://saved.example/v1/chat/completions');
  assert.equal(requests.at(-1).payload.model, 'saved-custom');
  checks += 1;

  const beforeNontext = requests.length;
  const image = await invoke(customApp, 'post', '/api/generate-image', { prompt: 'fixture', scene: 'coffee-shop' });
  assert.equal(image.success, true);
  const speech = await invoke(customApp, 'post', '/api/tts', { text: 'Hello' });
  assert.equal(speech.success, true);
  assert.equal(requests.length, beforeNontext);
  checks += 1;

  configure({ MINIMAX_API_KEY: '', ZHIPU_API_KEY: 'unrelated-fixture' });
  assert.equal(resolveMiniMaxConfig().apiKey, '');
  await assert.rejects(postMiniMaxChatCompletion(), { code: 'MINIMAX_API_KEY_MISSING' });
  const missing = await invoke(loadServer('server.js').app, 'post', '/api/chat', { message: 'Hello' });
  assert.equal(missing.success, false);
  assert.equal(requests.length, beforeNontext);
  checks += 1;
  console.log(`Passed ${checks} checks; inspected ${requests.length} serialized Axios requests; no network calls.`);
}

main().catch((error) => {
  console.error(error);
  process.exitCode = 1;
}).finally(() => {
  axios.defaults.adapter = originalAdapter;
  for (const key of Object.keys(process.env)) delete process.env[key];
  Object.assign(process.env, originalEnv);
});
