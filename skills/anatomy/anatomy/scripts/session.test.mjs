import assert from "node:assert/strict";
import { mkdirSync, mkdtempSync, writeFileSync } from "node:fs";
import { tmpdir } from "node:os";
import { join } from "node:path";
import { test } from "node:test";
import { describe, fromThisSession, measure, parseMinutes, parseTokens } from "./session.mjs";

const at = (minute) => new Date(Date.UTC(2026, 9, 12, 10, 0) + minute * 60000).toISOString();
const user = (minute, text) => ({ type: "user", timestamp: at(minute), message: { role: "user", content: text } });
const reply = (minute, id, input, output, extra = {}) => ({ type: "assistant", timestamp: at(minute), message: { id, usage: { input_tokens: input, cache_creation_input_tokens: 1000, cache_read_input_tokens: 999999, output_tokens: output } }, ...extra });
const lines = (entries) => entries.map((entry) => JSON.stringify(entry)).join("\n") + "\n";

function session() {
  const root = mkdtempSync(join(tmpdir(), "session-"));
  const id = "0123abcd-0000-0000-0000-000000000000";
  mkdirSync(join(root, "-work", id, "subagents"), { recursive: true });
  writeFileSync(join(root, "-work", `${id}.jsonl`), lines([
    user(0, "fix the readme"),
    reply(1, "m0", 50, 50),
    user(5, "/anatomy explain how a token bucket works, interactive"),
    reply(6, "m1", 100, 200),
    reply(6, "m1", 100, 400),
    reply(8, "m2", 10, 20),
    reply(70, "m3", 10, 20),
    user(80, "publish this figure to the community gallery"),
    reply(81, "m4", 5000, 5000),
  ]));
  writeFileSync(join(root, "-work", id, "subagents", "agent-1.jsonl"), lines([reply(7, "s1", 300, 300, { isSidechain: true, agentId: "a1" })]));
  return { root, id };
}

test("time and tokens cover the figure's request up to the publish request", () => {
  const { root, id } = session();
  const result = fromThisSession({ prompt: "/anatomy explain how a token bucket works, interactive", env: { CLAUDE_CODE_SESSION_ID: id }, root });
  assert.equal(result.tokens, 1100 + 400 + 1030 + 1030 + 1600);
  assert.equal(result.minutes, 3 + 10);
  assert.equal(result.from, at(5));
  assert.equal(result.to, at(80));
});

test("no session, no numbers", () => {
  assert.equal(fromThisSession({ env: {} }), null);
  assert.equal(measure([]), null);
});

test("hand-given values are read like the gallery reads them", () => {
  assert.equal(parseMinutes("1h30m"), 90);
  assert.equal(parseMinutes("45"), 45);
  assert.equal(parseMinutes("soon"), undefined);
  assert.equal(parseTokens("1.2M"), 1200000);
  assert.equal(parseTokens("450k"), 450000);
  assert.equal(parseTokens("lots"), undefined);
  assert.equal(describe({ minutes: 95, tokens: 1240000 }), "about 1 h 35 min and 1.2M tokens");
});
