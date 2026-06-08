const assert = require("node:assert/strict");
const { execFileSync } = require("node:child_process");
const { spawn } = require("node:child_process");
const fs = require("node:fs");
const path = require("node:path");
const test = require("node:test");

const frontendRoot = path.resolve(__dirname, "..");
const nextCli = path.join(frontendRoot, "node_modules", "next", "dist", "bin", "next");
const smokePort = Number(process.env.FRONTEND_SMOKE_PORT || 3217);
const smokeHost = "127.0.0.1";
const baseUrl = `http://${smokeHost}:${smokePort}`;

function sleep(ms) {
  return new Promise((resolve) => setTimeout(resolve, ms));
}

async function fetchWithTimeout(url, timeoutMs = 2000) {
  const controller = new AbortController();
  const timer = setTimeout(() => controller.abort(), timeoutMs);
  try {
    return await fetch(url, { signal: controller.signal });
  } finally {
    clearTimeout(timer);
  }
}

async function waitForServer(url, child, outputLines) {
  const deadline = Date.now() + 30000;
  while (Date.now() < deadline) {
    assert.equal(child.exitCode, null, `Next dev server exited early:\n${outputLines.join("")}`);
    try {
      const response = await fetchWithTimeout(url, 1500);
      if (response.ok) {
        return;
      }
    } catch (_error) {
      // Keep polling until Next finishes compiling the first route.
    }
    await sleep(500);
  }
  throw new Error(`Timed out waiting for ${url}.\n${outputLines.join("")}`);
}

function stopServer(child) {
  if (child.exitCode !== null) {
    return;
  }

  if (process.platform === "win32") {
    try {
      execFileSync("taskkill", ["/pid", String(child.pid), "/T", "/F"], { stdio: "ignore" });
      return;
    } catch (_error) {
      // Fall through to the portable kill below.
    }
  }

  child.kill("SIGTERM");
}

test("frontend static journey pages respond on a local Next server", { timeout: 45000 }, async () => {
  assert.ok(fs.existsSync(nextCli), `Next CLI not found at ${nextCli}; run npm install first.`);

  const outputLines = [];
  const child = spawn(process.execPath, [nextCli, "dev", "--hostname", smokeHost, "--port", String(smokePort)], {
    cwd: frontendRoot,
    env: { ...process.env, BROWSER: "none" },
    stdio: ["ignore", "pipe", "pipe"]
  });

  child.stdout.on("data", (chunk) => outputLines.push(chunk.toString()));
  child.stderr.on("data", (chunk) => outputLines.push(chunk.toString()));

  try {
    await waitForServer(`${baseUrl}/portfolio-input`, child, outputLines);

    const pages = [
      ["/portfolio-input", /Portfolio Input|Run diagnosis/i],
      ["/diagnosis", /Diagnosis|Portfolio/i],
      ["/evidence", /Evidence|X-Ray/i],
      ["/hypothesis", /Hypothesis|Builder/i],
      ["/comparison", /Comparison|Current/i],
      ["/verdict", /Verdict|Decision/i],
      ["/report", /Report|Commentary/i]
    ];

    for (const [route, expectedText] of pages) {
      const response = await fetchWithTimeout(`${baseUrl}${route}`, 5000);
      assert.equal(response.status, 200, `${route} should render successfully`);
      const html = await response.text();
      assert.match(html, expectedText, `${route} should include expected stage text`);
    }
  } finally {
    stopServer(child);
  }
});
