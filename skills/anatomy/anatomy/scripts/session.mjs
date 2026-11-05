import { existsSync, readdirSync, readFileSync, statSync } from "node:fs";
import { homedir } from "node:os";
import { join } from "node:path";

export const IDLE_CAP = 10 * 60 * 1000;

export function parseMinutes(text) {
  const value = String(text ?? "").trim().toLowerCase();
  if (!value) return null;
  if (/^\d+$/.test(value)) return Number(value);
  const match = value.match(/^(?:(\d+(?:[.,]\d+)?)\s*(?:h|hr|hrs|hours?))?\s*(?:(\d+)\s*(?:m|min|mins|minutes?))?$/);
  if (!match || (!match[1] && !match[2])) return undefined;
  return Math.round(Number((match[1] ?? "0").replace(",", ".")) * 60 + Number(match[2] ?? 0)) || undefined;
}

export function parseTokens(text) {
  const value = String(text ?? "").trim().toLowerCase().replace(/[\s,_]/g, "").replace(/tokens?$/, "");
  if (!value) return null;
  const match = value.match(/^(\d+(?:\.\d+)?)([km]?)$/);
  if (!match) return undefined;
  const tokens = Math.round(Number(match[1]) * (match[2] === "m" ? 1e6 : match[2] === "k" ? 1e3 : 1));
  return tokens >= 1 && tokens <= 1e10 ? tokens : undefined;
}

function walk(dir, out = []) {
  for (const name of existsSync(dir) ? readdirSync(dir) : []) {
    const full = join(dir, name);
    if (statSync(full).isDirectory()) walk(full, out);
    else if (name.endsWith(".jsonl")) out.push(full);
  }
  return out;
}

export function sessionFiles(sessionId, root = join(homedir(), ".claude", "projects")) {
  if (!sessionId || !/^[0-9a-f-]{8,64}$/i.test(sessionId) || !existsSync(root)) return [];
  for (const project of readdirSync(root)) {
    const main = join(root, project, `${sessionId}.jsonl`);
    if (existsSync(main)) return [main, ...walk(join(root, project, sessionId))];
  }
  return [];
}

function entriesOf(file) {
  const out = [];
  for (const line of readFileSync(file, "utf8").split("\n")) {
    if (!line.trim()) continue;
    try {
      const entry = JSON.parse(line);
      if (entry && typeof entry.timestamp === "string") out.push(entry);
    } catch {}
  }
  return out;
}

const textOf = (entry) => {
  const content = entry.message?.content;
  if (typeof content === "string") return content;
  if (Array.isArray(content)) return content.filter((part) => part?.type === "text").map((part) => part.text).join("\n");
  return "";
};

const squash = (text) => text.toLowerCase().replace(/\s+/g, " ").trim();

export function measure(files, { prompt = "" } = {}) {
  if (!files.length) return null;
  const [main, ...side] = files;
  const mainEntries = entriesOf(main).sort((a, b) => a.timestamp.localeCompare(b.timestamp));
  const asks = mainEntries.filter((entry) => entry.type === "user" && !entry.isSidechain && textOf(entry));
  const head = squash(prompt).slice(0, 48);
  const start =
    (head && asks.find((entry) => squash(textOf(entry)).includes(head))) ??
    asks.find((entry) => /\/anatomy\b|\banatomy\b/i.test(textOf(entry))) ??
    mainEntries[0];
  if (!start) return null;
  const end = asks.find((entry) => entry.timestamp > start.timestamp && /\bpublish\b/i.test(textOf(entry)) && /\b(community|gallery)\b/i.test(textOf(entry)));
  const from = start.timestamp;
  const to = end?.timestamp ?? "￿";
  const inWindow = (entry) => entry.timestamp >= from && entry.timestamp < to;

  const all = [...mainEntries, ...side.flatMap(entriesOf)].filter(inWindow);
  const times = [...new Set(all.map((entry) => Date.parse(entry.timestamp)).filter(Number.isFinite))].sort((a, b) => a - b);
  let active = 0;
  for (let i = 1; i < times.length; i++) active += Math.min(times[i] - times[i - 1], IDLE_CAP);

  const perMessage = new Map();
  for (const entry of all) {
    const usage = entry.type === "assistant" ? entry.message?.usage : null;
    if (!usage) continue;
    const key = `${entry.sessionId ?? ""}:${entry.agentId ?? ""}:${entry.message?.id ?? entry.uuid}`;
    const spent = (usage.input_tokens ?? 0) + (usage.cache_creation_input_tokens ?? 0) + (usage.output_tokens ?? 0);
    perMessage.set(key, Math.max(perMessage.get(key) ?? 0, spent));
  }
  const tokens = [...perMessage.values()].reduce((sum, spent) => sum + spent, 0);
  if (!tokens) return null;
  const last = end?.timestamp ?? (times.length ? new Date(times.at(-1)).toISOString() : from);
  return { minutes: Math.max(1, Math.round(active / 60000)), tokens, from, to: last };
}

export function fromThisSession({ prompt, env = process.env, root } = {}) {
  return measure(sessionFiles(env.CLAUDE_CODE_SESSION_ID, root), { prompt });
}

export function describe({ minutes, tokens }) {
  const time = minutes < 60 ? `${minutes} min` : `${Math.floor(minutes / 60)} h${minutes % 60 ? ` ${minutes % 60} min` : ""}`;
  const count = tokens >= 1e6 ? `${(tokens / 1e6).toFixed(1).replace(/\.0$/, "")}M` : tokens >= 1e3 ? `${Math.round(tokens / 1e3)}k` : String(tokens);
  return `about ${time} and ${count} tokens`;
}
