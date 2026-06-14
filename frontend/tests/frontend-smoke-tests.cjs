const assert = require("node:assert/strict");
const { execFileSync } = require("node:child_process");
const { spawn } = require("node:child_process");
const fs = require("node:fs");
const net = require("node:net");
const path = require("node:path");
const test = require("node:test");

const frontendRoot = path.resolve(__dirname, "..");
const nextCli = path.join(frontendRoot, "node_modules", "next", "dist", "bin", "next");
const smokeHost = "127.0.0.1";
const startupTimeoutMs = 60000;
const startupFetchTimeoutMs = 10000;
const pageFetchTimeoutMs = 15000;

function sleep(ms) {
  return new Promise((resolve) => setTimeout(resolve, ms));
}

async function fetchWithTimeout(url, timeoutMs = 2000, context = url) {
  const controller = new AbortController();
  const timer = setTimeout(() => controller.abort(), timeoutMs);
  try {
    return await fetch(url, { signal: controller.signal });
  } catch (error) {
    if (error && error.name === "AbortError") {
      throw new Error(`Timed out after ${timeoutMs}ms while fetching ${context}`);
    }
    throw error;
  } finally {
    clearTimeout(timer);
  }
}

function outputTail(outputLines, maxLines = 80) {
  return outputLines.join("").split(/\r?\n/).slice(-maxLines).join("\n");
}

function findAvailablePort(preferredPort) {
  return new Promise((resolve, reject) => {
    const server = net.createServer();
    server.once("error", (error) => reject(error));
    server.listen(preferredPort, smokeHost, () => {
      const address = server.address();
      server.close(() => {
        if (!address || typeof address === "string") {
          reject(new Error("Could not resolve an available smoke-test port."));
          return;
        }
        resolve(address.port);
      });
    });
  });
}

async function waitForServer(url, child, outputLines) {
  const deadline = Date.now() + startupTimeoutMs;
  while (Date.now() < deadline) {
    assert.equal(child.exitCode, null, `Next dev server exited early:\n${outputTail(outputLines)}`);
    try {
      const response = await fetchWithTimeout(url, startupFetchTimeoutMs, `server readiness check ${url}`);
      if (response.ok) {
        return;
      }
    } catch (_error) {
      // Keep polling until Next finishes compiling the first route.
    }
    await sleep(500);
  }
  throw new Error(`Timed out after ${startupTimeoutMs}ms waiting for ${url}.\n${outputTail(outputLines)}`);
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

test("frontend static journey pages respond on a local Next server", { timeout: 120000 }, async () => {
  assert.ok(fs.existsSync(nextCli), `Next CLI not found at ${nextCli}; run npm install first.`);

  const smokePort = await findAvailablePort(Number(process.env.FRONTEND_SMOKE_PORT || 0));
  const baseUrl = `http://${smokeHost}:${smokePort}`;
  const outputLines = [];
  const child = spawn(process.execPath, [nextCli, "dev", "--hostname", smokeHost, "--port", String(smokePort)], {
    cwd: frontendRoot,
    env: { ...process.env, BROWSER: "none" },
    stdio: ["ignore", "pipe", "pipe"]
  });

  child.stdout.on("data", (chunk) => outputLines.push(chunk.toString()));
  child.stderr.on("data", (chunk) => outputLines.push(chunk.toString()));

  try {
    await waitForServer(`${baseUrl}/`, child, outputLines);

    const pages = [
      ["/", /Diagnose portfolio risk before you rebalance|Enter Platform/i],
      ["/onboarding/sign-in", /Sign in before opening the diagnostic room|Enter your email/i],
      ["/onboarding/name", /What should we call you|Continue/i],
      ["/onboarding/investor-type", /Five questions before we open the portfolio screen|What your answers do/i],
      ["/onboarding/loading", /Setting up your experience|Opening the decision room/i],
      ["/client-profile", /Manual diagnostic context|Client Fit profile editor/i],
      ["/portfolio-input", /Portfolio Input|Run diagnosis/i],
      ["/diagnosis", /Diagnosis|Portfolio/i],
      ["/evidence", /Stress Test Lab|Diagnosis/i],
      ["/client-fit", /Client Fit|provided profile/i],
      ["/hypothesis", /Hypothesis|Builder/i],
      ["/comparison", /Comparison|Current/i],
      ["/verdict", /Verdict|Decision/i],
      ["/report", /Report|Commentary/i]
    ];

    for (const [route, expectedText] of pages) {
      const response = await fetchWithTimeout(`${baseUrl}${route}`, pageFetchTimeoutMs, route);
      assert.equal(response.status, 200, `${route} should render successfully.\n${outputTail(outputLines)}`);
      const html = await response.text();
      assert.match(html, expectedText, `${route} should include expected stage text`);
    }
  } finally {
    stopServer(child);
  }
});
