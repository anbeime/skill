import assert from "node:assert/strict";
import { execFile } from "node:child_process";
import { createServer } from "node:http";
import { promisify } from "node:util";
import { fileURLToPath } from "node:url";
import test from "node:test";

const execute = promisify(execFile);
const drive = fileURLToPath(new URL("drive.mjs", import.meta.url));

test("drive waits for a slow page to finish loading before running actions", async () => {
  const server = createServer((request, response) => {
    if (request.url === "/slow.js") {
      setTimeout(() => {
        response.setHeader("content-type", "text/javascript");
        response.end("window.slowScriptRan = true");
      }, 2500);
    } else {
      response.setHeader("content-type", "text/html");
      response.end('<!doctype html><div class="iso-plate">Figure</div><script src="/slow.js"></script>');
    }
  });
  await new Promise((done) => server.listen(0, "127.0.0.1", done));
  try {
    const { port } = server.address();
    const actions = JSON.stringify([["eval", "document.readyState + ' ' + Boolean(window.slowScriptRan)"]]);
    const result = await execute(process.execPath, [drive, `http://127.0.0.1:${port}/`, actions], { timeout: 30000 });
    assert.match(result.stdout, /eval: "complete true"/);
  } finally {
    server.close();
  }
});
