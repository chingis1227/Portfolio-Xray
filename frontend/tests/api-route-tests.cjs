const assert = require("node:assert/strict");
const { EventEmitter } = require("node:events");
const { PassThrough } = require("node:stream");
const fs = require("node:fs");
const path = require("node:path");
const test = require("node:test");
const ts = require("typescript");

const builderPrepareRoutePath = path.resolve(__dirname, "..", "app", "api", "portfolio", "builder", "prepare", "route.ts");
const reviewRecoverRoutePath = path.resolve(__dirname, "..", "app", "api", "portfolio", "review", "recover", "route.ts");
const frontendRoot = path.resolve(__dirname, "..");

function makeJsonRequest(body) {
  return new Request("http://localhost/api/portfolio/builder/prepare", {
    method: "POST",
    headers: { "content-type": "application/json" },
    body: JSON.stringify(body)
  });
}

function makeInvalidJsonRequest() {
  return new Request("http://localhost/api/portfolio/builder/prepare", {
    method: "POST",
    headers: { "content-type": "application/json" },
    body: "{not-json"
  });
}

class FakeChild extends EventEmitter {
  constructor() {
    super();
    this.stdout = new PassThrough();
    this.stderr = new PassThrough();
    this.killed = false;
  }

  kill() {
    this.killed = true;
    this.emit("close", 124);
  }
}

function loadTsModule(filePath, { spawnImpl, readFileImpl, moduleCache = new Map() } = {}) {
  const resolvedPath = path.resolve(filePath);
  if (moduleCache.has(resolvedPath)) {
    return moduleCache.get(resolvedPath).exports;
  }

  const source = fs.readFileSync(resolvedPath, "utf8");
  const compiled = ts.transpileModule(source, {
    compilerOptions: {
      module: ts.ModuleKind.CommonJS,
      target: ts.ScriptTarget.ES2022,
      esModuleInterop: true
    },
    fileName: resolvedPath
  }).outputText;

  const exports = {};
  const module = { exports };
  moduleCache.set(resolvedPath, module);

  const sandboxRequire = (specifier) => {
    if (specifier === "node:child_process") {
      return { spawn: spawnImpl || (() => { throw new Error("spawn was not expected"); }) };
    }
    if (specifier === "node:fs/promises") {
      return { readFile: readFileImpl || (() => { throw new Error("readFile was not expected"); }) };
    }
    if (specifier === "next/server") {
      return {
        NextResponse: {
          json(payload, init = {}) {
            return Response.json(payload, { status: init.status || 200 });
          }
        }
      };
    }
    if (specifier.startsWith("@/")) {
      const aliasedPath = path.join(frontendRoot, specifier.slice(2));
      const tsPath = fs.existsSync(`${aliasedPath}.ts`) ? `${aliasedPath}.ts` : aliasedPath;
      return loadTsModule(tsPath, { spawnImpl, readFileImpl, moduleCache });
    }
    if (specifier.startsWith(".")) {
      const relativePath = path.resolve(path.dirname(resolvedPath), specifier);
      const tsPath = fs.existsSync(`${relativePath}.ts`) ? `${relativePath}.ts` : relativePath;
      return loadTsModule(tsPath, { spawnImpl, readFileImpl, moduleCache });
    }
    return require(specifier);
  };

  Function("require", "exports", "module", compiled)(sandboxRequire, exports, module);
  return module.exports;
}

function loadRoute({ routePath = builderPrepareRoutePath, spawnImpl, readFileImpl } = {}) {
  return loadTsModule(routePath, { spawnImpl, readFileImpl });
}

async function responseJson(response) {
  return { status: response.status, body: await response.json() };
}

test("builder prepare route rejects invalid JSON before starting bridge", async () => {
  const route = loadRoute();

  const result = await responseJson(await route.POST(makeInvalidJsonRequest()));

  assert.equal(result.status, 400);
  assert.equal(result.body.status, "failed");
  assert.equal(result.body.error, "Request body must be valid JSON.");
});

test("builder prepare route validates review id format and missing selected card", async () => {
  const route = loadRoute();

  const result = await responseJson(await route.POST(makeJsonRequest({ review_id: "../bad" })));

  assert.equal(result.status, 400);
  assert.equal(result.body.status, "failed");
  assert.equal(result.body.error, "Builder setup prepare request validation failed.");
  assert.deepEqual(result.body.details, [
    "selected_card_id is required.",
    "review_id must be a frontend_review_* id.",
    "review_id must not contain path separators."
  ]);
});

test("builder prepare route surfaces a scrubbed backend failure result", async () => {
  const root = path.resolve(process.cwd(), "..");
  const resultPath = path.join(root, "runs", "frontend_review_123", "builder_setup_result.json");
  const localPath = path.join(root, "scripts", "run_review_from_payload.py");
  const child = new FakeChild();
  const spawnCalls = [];
  const route = loadRoute({
    spawnImpl(command, args, options) {
      spawnCalls.push({ command, args, options });
      process.nextTick(() => {
        child.stdout.write(`${resultPath}\n`);
        child.stderr.write(`Traceback (most recent call last):\n  File "${localPath}", line 10, in <module>\nRuntimeError: boom at ${localPath}`);
        child.emit("close", 1);
      });
      return child;
    },
    async readFileImpl(filePath, encoding) {
      assert.equal(filePath, resultPath);
      assert.equal(encoding, "utf8");
      return JSON.stringify({
        status: "failed",
        error: `Cannot prepare builder at ${localPath}`,
        details: `Traceback (most recent call last):\n  File "${localPath}", line 10, in <module>\nRuntimeError: boom at ${localPath}`
      });
    }
  });

  const result = await responseJson(await route.POST(makeJsonRequest({
    review_id: "frontend_review_123",
    selected_card_id: "card_equal_weight"
  })));

  assert.equal(result.status, 500);
  assert.equal(result.body.status, "failed");
  assert.equal(result.body.stage, "builder_setup");
  assert.equal(result.body.review_id, "frontend_review_123");
  assert.equal(result.body.selected_card_id, "card_equal_weight");
  assert.equal(spawnCalls.length, 1);
  assert.equal(spawnCalls[0].command, path.join(root, ".venv", "Scripts", "python.exe"));
  assert.ok(spawnCalls[0].args.includes("--prepare-builder"));
  assert.ok(spawnCalls[0].args.includes("--selected-card-id"));
  const serialized = JSON.stringify(result.body);
  assert.doesNotMatch(serialized, /Traceback \(most recent call last\):/);
  assert.doesNotMatch(serialized, /run_review_from_payload\.py/);
  assert.doesNotMatch(serialized, /D:[\\/]/);
  assert.match(serialized, /\[path\]|\[project\]|Backend failure details were captured safely/);
});

test("builder prepare route returns safe failure when backend returns no result path", async () => {
  const root = path.resolve(process.cwd(), "..");
  const localPath = path.join(root, "scripts", "run_review_from_payload.py");
  const child = new FakeChild();
  const route = loadRoute({
    spawnImpl() {
      process.nextTick(() => {
        child.stderr.write(`Traceback (most recent call last):\n  File "${localPath}", line 5, in <module>\nRuntimeError: missing result`);
        child.emit("close", 1);
      });
      return child;
    }
  });

  const result = await responseJson(await route.POST(makeJsonRequest({
    review_id: "frontend_review_missing_result",
    selected_card_id: "card_equal_weight"
  })));

  assert.equal(result.status, 500);
  assert.equal(result.body.status, "failed");
  assert.equal(result.body.error, "Builder setup prepare did not return a result path.");
  const serialized = JSON.stringify(result.body);
  assert.doesNotMatch(serialized, /Traceback \(most recent call last\):/);
  assert.doesNotMatch(serialized, /run_review_from_payload\.py/);
  assert.doesNotMatch(serialized, /D:[\\/]/);
});

test("builder prepare route passes through successful backend JSON without running live factory", async () => {
  const root = path.resolve(process.cwd(), "..");
  const resultPath = path.join(root, "runs", "frontend_review_ok", "builder_setup_result.json");
  const child = new FakeChild();
  const route = loadRoute({
    spawnImpl() {
      process.nextTick(() => {
        child.stdout.write(`some log\n${resultPath}\n`);
        child.emit("close", 0);
      });
      return child;
    },
    async readFileImpl() {
      return JSON.stringify({
        review_id: "frontend_review_ok",
        status: "completed",
        stage: "builder_setup",
        selected_card_id: "card_equal_weight",
        can_generate_candidate: true,
        portfolio_alternatives_builder: { setup_id: "builder_card_equal_weight" }
      });
    }
  });

  const result = await responseJson(await route.POST(makeJsonRequest({
    review_id: "frontend_review_ok",
    selected_card_id: "card_equal_weight"
  })));

  assert.equal(result.status, 200);
  assert.equal(result.body.status, "completed");
  assert.equal(result.body.stage, "builder_setup");
  assert.equal(result.body.can_generate_candidate, true);
});

test("review recovery route validates review id and path separators", async () => {
  const route = loadRoute({ routePath: reviewRecoverRoutePath });

  const result = await responseJson(await route.GET(new Request("http://localhost/api/portfolio/review/recover?review_id=../bad")));

  assert.equal(result.status, 400);
  assert.equal(result.body.status, "failed");
  assert.equal(result.body.error, "Review recovery request validation failed.");
  assert.deepEqual(result.body.details, [
    "review_id must be a frontend_review_* id.",
    "review_id must not contain path separators."
  ]);
});

test("review recovery route reads only run-local diagnosis artifacts and skips downstream active state", async () => {
  const root = path.resolve(process.cwd(), "..");
  const expectedPath = path.join(root, "runs", "frontend_review_recover_ok", "review_result.json");
  const route = loadRoute({
    routePath: reviewRecoverRoutePath,
    async readFileImpl(filePath, encoding) {
      assert.equal(filePath, expectedPath);
      assert.equal(encoding, "utf8");
      return JSON.stringify({
        review_id: "frontend_review_recover_ok",
        status: "completed",
        portfolio_input: {
          investor_currency: "USD",
          holdings: [
            { type: "instrument", ticker: "SPY", weight: 60 },
            { type: "cash", currency: "USD", weight: 40 }
          ]
        },
        paths: {
          run_dir: "runs/frontend_review_recover_ok",
          portfolio_xray: "runs/frontend_review_recover_ok/analysis_subject/portfolio_xray.json",
          current_vs_candidate: "runs/frontend_review_recover_ok/current_vs_candidate.json"
        },
        outputs: {
          portfolio_xray: { version: "portfolio_xray_v2" },
          stress_report: { stress_conclusions: {} },
          candidate_launchpad: { cards: [] },
          portfolio_alternatives_builder: { selected_card_id: "card_ok" },
          candidate_generation: { stale: true },
          current_vs_candidate: { stale: true },
          decision_verdict: { stale: true }
        }
      });
    }
  });

  const result = await responseJson(await route.POST(makeJsonRequest({ review_id: "frontend_review_recover_ok" })));

  assert.equal(result.status, 200);
  assert.equal(result.body.status, "completed");
  assert.equal(result.body.stage, "review_recovery");
  assert.equal(result.body.recovery.downstream_artifacts_restored_as_active, false);
  assert.deepEqual(result.body.recovery.restored_active_stages, ["diagnosis", "evidence", "hypothesis_setup"]);
  assert.equal(result.body.review_result.status, "completed");
  assert.equal(result.body.review_result.outputs.portfolio_xray.version, "portfolio_xray_v2");
  assert.equal(result.body.review_result.outputs.portfolio_alternatives_builder.selected_card_id, "card_ok");
  assert.equal(result.body.review_result.outputs.candidate_generation, undefined);
  assert.equal(result.body.review_result.outputs.current_vs_candidate, undefined);
  assert.equal(result.body.review_result.outputs.decision_verdict, undefined);
  assert.equal(result.body.review_result.paths.current_vs_candidate, undefined);
});
