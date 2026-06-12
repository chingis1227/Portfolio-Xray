const assert = require('node:assert/strict');
const { execFileSync, spawn } = require('node:child_process');
const fs = require('node:fs');
const net = require('node:net');
const path = require('node:path');
const { createRequire } = require('node:module');

const repoRoot = path.resolve(__dirname, '..');
const frontendRoot = path.join(repoRoot, 'frontend');
const outputRoot = path.join(repoRoot, 'output', 'playwright', `vertical-qa-${new Date().toISOString().replace(/[:.]/g, '-')}`);
const host = '127.0.0.1';
const startupTimeoutMs = Number(process.env.PMRI_QA_STARTUP_TIMEOUT_MS || 120000);
const requestTimeoutMs = Number(process.env.PMRI_QA_REQUEST_TIMEOUT_MS || 15 * 60 * 1000);
const scenarioLimitArgIndex = process.argv.indexOf('--scenario-limit');
const scenarioLimit = scenarioLimitArgIndex >= 0 ? Number(process.argv[scenarioLimitArgIndex + 1]) : 3;
const headless = !process.argv.includes('--headed');
const keepServers = process.argv.includes('--keep-servers');

const scenarios = [
  {
    id: 'concentrated_growth_cash',
    expectedDifferent: true,
    portfolio: {
      investor_currency: 'USD',
      holdings: [
        { type: 'instrument', ticker: 'QQQ', weight: 70 },
        { type: 'instrument', ticker: 'VOO', weight: 20 },
        { type: 'cash', currency: 'USD', weight: 10 }
      ]
    }
  },
  {
    id: 'weak_crisis_resilience_live',
    expectedDifferent: true,
    portfolio: {
      investor_currency: 'USD',
      holdings: [
        { type: 'instrument', ticker: 'MTUM', weight: 25 },
        { type: 'instrument', ticker: 'COPX', weight: 15 },
        { type: 'instrument', ticker: 'ETHA', weight: 10 },
        { type: 'instrument', ticker: 'GLD', weight: 10 },
        { type: 'cash', currency: 'USD', weight: 10 },
        { type: 'instrument', ticker: 'USO', weight: 8 },
        { type: 'instrument', ticker: 'META', weight: 14 },
        { type: 'instrument', ticker: 'IDEV', weight: 8 }
      ]
    }
  },
  {
    id: 'balanced_reference',
    expectedDifferent: true,
    portfolio: {
      investor_currency: 'USD',
      holdings: [
        { type: 'instrument', ticker: 'VOO', weight: 50 },
        { type: 'instrument', ticker: 'BND', weight: 30 },
        { type: 'instrument', ticker: 'GLD', weight: 20 }
      ]
    }
  }
].slice(0, Number.isFinite(scenarioLimit) && scenarioLimit > 0 ? scenarioLimit : 3);

function sleep(ms) {
  return new Promise((resolve) => setTimeout(resolve, ms));
}

function outputTail(lines, maxLines = 100) {
  return lines.join('').split(/\r?\n/).slice(-maxLines).join('\n');
}

function ensureDir(dir) {
  fs.mkdirSync(dir, { recursive: true });
}

function findAvailablePort() {
  return new Promise((resolve, reject) => {
    const server = net.createServer();
    server.once('error', reject);
    server.listen(0, host, () => {
      const address = server.address();
      server.close(() => {
        if (!address || typeof address === 'string') reject(new Error('Could not allocate local port.'));
        else resolve(address.port);
      });
    });
  });
}

async function fetchWithTimeout(url, options = {}, context = url, timeoutMs = requestTimeoutMs) {
  const controller = new AbortController();
  const timer = setTimeout(() => controller.abort(), timeoutMs);
  try {
    const response = await fetch(url, { ...options, signal: controller.signal });
    return response;
  } catch (error) {
    if (error && error.name === 'AbortError') {
      throw new Error(`Timed out after ${timeoutMs}ms while fetching ${context}`);
    }
    throw error;
  } finally {
    clearTimeout(timer);
  }
}

async function waitForHttp(url, child, lines, label) {
  const deadline = Date.now() + startupTimeoutMs;
  while (Date.now() < deadline) {
    assert.equal(child.exitCode, null, `${label} exited early.\n${outputTail(lines)}`);
    try {
      const response = await fetchWithTimeout(url, {}, `${label} readiness`, 5000);
      if (response.ok) return;
    } catch (_error) {
      // Keep polling while the server boots or compiles its first route.
    }
    await sleep(750);
  }
  throw new Error(`Timed out waiting for ${label} at ${url}.\n${outputTail(lines)}`);
}

function stopProcess(child) {
  if (!child || child.exitCode !== null) return;
  if (process.platform === 'win32') {
    try {
      execFileSync('taskkill', ['/pid', String(child.pid), '/T', '/F'], { stdio: 'ignore' });
      return;
    } catch (_error) {}
  }
  child.kill('SIGTERM');
}

function startFastApi(port) {
  const python = fs.existsSync(path.join(repoRoot, '.venv', 'Scripts', 'python.exe'))
    ? path.join(repoRoot, '.venv', 'Scripts', 'python.exe')
    : 'py';
  const args = python === 'py'
    ? ['-3', '-m', 'uvicorn', 'src.api.app:app', '--host', host, '--port', String(port)]
    : ['-m', 'uvicorn', 'src.api.app:app', '--host', host, '--port', String(port)];
  const lines = [];
  const child = spawn(python, args, {
    cwd: repoRoot,
    env: { ...process.env, PYTHONUTF8: '1' },
    stdio: ['ignore', 'pipe', 'pipe']
  });
  child.stdout.on('data', (chunk) => lines.push(chunk.toString()));
  child.stderr.on('data', (chunk) => lines.push(chunk.toString()));
  return { child, lines };
}

function startNext(frontendPort, fastapiPort) {
  const nextCli = path.join(frontendRoot, 'node_modules', 'next', 'dist', 'bin', 'next');
  assert.ok(fs.existsSync(nextCli), `Next CLI not found at ${nextCli}; run npm install in frontend first.`);
  const lines = [];
  const child = spawn(process.execPath, [nextCli, 'dev', '--hostname', host, '--port', String(frontendPort)], {
    cwd: frontendRoot,
    env: {
      ...process.env,
      BROWSER: 'none',
      PMRI_FASTAPI_BASE_URL: `http://${host}:${fastapiPort}`
    },
    stdio: ['ignore', 'pipe', 'pipe']
  });
  child.stdout.on('data', (chunk) => lines.push(chunk.toString()));
  child.stderr.on('data', (chunk) => lines.push(chunk.toString()));
  return { child, lines };
}

function serverDiagnostics(lines) {
  const tail = outputTail(lines, 160);
  const fatalPatterns = [
    /Failed to compile/i,
    /Module not found/i,
    /Cannot find module/i,
    /React Client Manifest/i,
    /ENOENT.*\.next/i,
    /missing.*\.next/i
  ];
  return {
    fatal: fatalPatterns.some((pattern) => pattern.test(tail)),
    tail
  };
}


async function gotoWithRetry(page, url, options = {}, maxAttempts = 3) {
  let lastError = null;
  for (let attempt = 1; attempt <= maxAttempts; attempt += 1) {
    try {
      await page.goto(url, options);
      return attempt;
    } catch (error) {
      lastError = error;
      await sleep(750 * attempt);
    }
  }
  throw lastError;
}

async function browserJson(page, method, url, body) {
  return await page.evaluate(async ({ method, url, body, timeoutMs }) => {
    const controller = new AbortController();
    const timer = setTimeout(() => controller.abort(), timeoutMs);
    try {
      const response = await fetch(url, {
        method,
        headers: body === undefined ? undefined : { 'Content-Type': 'application/json' },
        body: body === undefined ? undefined : JSON.stringify(body),
        signal: controller.signal
      });
      const text = await response.text();
      let parsed = null;
      try { parsed = text ? JSON.parse(text) : null; } catch (_error) { parsed = { rawText: text }; }
      return { ok: response.ok, status: response.status, body: parsed };
    } finally {
      clearTimeout(timer);
    }
  }, { method, url, body, timeoutMs: requestTimeoutMs });
}

function record(value) {
  return value && typeof value === 'object' && !Array.isArray(value) ? value : {};
}

function text(value) {
  return typeof value === 'string' && value.trim() ? value.trim() : '';
}

function findCards(diagnosisBody) {
  const reviewResult = record(diagnosisBody.review_result || diagnosisBody);
  const outputs = record(reviewResult.outputs);
  const launchpad = record(outputs.candidate_launchpad);
  const rawCards = Array.isArray(launchpad.cards) ? launchpad.cards : [];
  return rawCards.filter((item) => item && typeof item === 'object');
}

function chooseCard(cards) {
  return cards.find((card) => {
    const setup = record(card.candidate_setup);
    return card.candidate_generation_allowed === true
      || setup.candidate_generation_allowed === true
      || text(card.default_method)
      || text(setup.selected_method);
  }) || cards[0];
}

function envelope(body) {
  return record(body.fastapi_envelope || body);
}

function lineage(body) {
  return record(envelope(body).lineage);
}

function sourceArtifacts(body) {
  const evidence = record(envelope(body).evidence);
  const refs = Array.isArray(evidence.source_artifacts) ? evidence.source_artifacts : [];
  return refs.map((ref) => text(record(ref).kind)).filter(Boolean);
}

async function capturePageArtifact(page, artifactBase) {
  const screenshotPath = path.join(outputRoot, `${artifactBase}.png`);
  try {
    await page.screenshot({ path: screenshotPath, fullPage: true, timeout: 15000 });
    return { screenshot: screenshotPath, fallback: null };
  } catch (error) {
    const htmlPath = path.join(outputRoot, `${artifactBase}.html`);
    const textPath = path.join(outputRoot, `${artifactBase}.txt`);
    let html = '';
    let bodyText = '';
    try { html = await page.content(); } catch (_contentError) { html = '<!-- page.content unavailable -->'; }
    try { bodyText = await page.locator('body').innerText({ timeout: 5000 }); } catch (_textError) { bodyText = 'body text unavailable'; }
    fs.writeFileSync(htmlPath, html, 'utf8');
    fs.writeFileSync(textPath, `Screenshot failed: ${error && error.message ? error.message : String(error)}\n\n${bodyText}`, 'utf8');
    return { screenshot: null, fallback: { html: htmlPath, text: textPath, error: error && error.message ? error.message : String(error) } };
  }
}

async function diagnoseWithRetry(page, baseUrl, scenario, maxAttempts = 3) {
  let lastResult = null;
  for (let attempt = 1; attempt <= maxAttempts; attempt += 1) {
    const result = await browserJson(page, 'POST', `${baseUrl}/api/portfolio/diagnose`, scenario.portfolio);
    if (result.ok) {
      result.attempt = attempt;
      return result;
    }
    lastResult = result;
    await sleep(1500 * attempt);
  }
  if (lastResult && typeof lastResult === 'object') lastResult.attempt = maxAttempts;
  return lastResult;
}

function assertOk(result, label) {
  assert.equal(result.ok, true, `${label} failed with HTTP ${result.status}: ${JSON.stringify(result.body).slice(0, 2000)}`);
}

async function runScenario(page, baseUrl, scenario, index) {
  await gotoWithRetry(page, `${baseUrl}/portfolio-input`, { waitUntil: 'domcontentloaded' });
  await page.evaluate(() => { localStorage.clear(); sessionStorage.clear(); });
  await capturePageArtifact(page, `${index}-${scenario.id}-input`);

  const diagnosis = await diagnoseWithRetry(page, baseUrl, scenario, 3);
  assertOk(diagnosis, `${scenario.id} diagnosis`);
  const diagnosisLineage = lineage(diagnosis.body);
  const reviewId = text(diagnosis.body.review_id) || text(diagnosisLineage.review_id);
  assert.ok(reviewId.startsWith('frontend_review_'), `${scenario.id} returned invalid reviewId ${reviewId}`);

  const cards = findCards(diagnosis.body);
  assert.ok(cards.length > 0, `${scenario.id} returned no Launchpad cards.`);
  const selectedCard = chooseCard(cards);
  const selectedCardId = text(selectedCard.card_id || selectedCard.id);
  assert.ok(selectedCardId, `${scenario.id} selected card has no id.`);

  const builder = await browserJson(page, 'POST', `${baseUrl}/api/portfolio/builder/prepare`, {
    review_id: reviewId,
    selected_card_id: selectedCardId
  });
  assertOk(builder, `${scenario.id} builder`);

  const candidate = await browserJson(page, 'POST', `${baseUrl}/api/portfolio/candidate/generate`, {
    review_id: reviewId,
    selected_card_id: selectedCardId
  });
  assertOk(candidate, `${scenario.id} candidate`);
  const candidateId = text(candidate.body.candidate_id) || text(lineage(candidate.body).candidate_id);
  assert.ok(candidateId, `${scenario.id} returned no candidate id.`);

  const comparison = await browserJson(page, 'POST', `${baseUrl}/api/portfolio/comparison/generate`, {
    review_id: reviewId,
    selected_card_id: selectedCardId
  });
  assertOk(comparison, `${scenario.id} comparison`);
  const comparisonId = text(lineage(comparison.body).comparison_id) || `current_vs_candidate:${candidateId}`;

  const verdict = await browserJson(page, 'POST', `${baseUrl}/api/portfolio/verdict/generate`, {
    review_id: reviewId,
    selected_card_id: selectedCardId
  });
  assertOk(verdict, `${scenario.id} verdict`);
  const verdictId = text(verdict.body.verdict_id) || text(lineage(verdict.body).verdict_id);
  assert.ok(verdictId, `${scenario.id} returned no verdict id.`);

  const report = await browserJson(page, 'POST', `${baseUrl}/api/portfolio/report/generate`, {
    review_id: reviewId,
    selected_card_id: selectedCardId
  });
  assertOk(report, `${scenario.id} report`);

  const routes = ['diagnosis', 'evidence', 'hypothesis', 'comparison', 'verdict', 'report'];
  const routeChecks = [];
  for (const route of routes) {
    const routeNavigationAttempt = await gotoWithRetry(page, `${baseUrl}/${route}`, { waitUntil: 'domcontentloaded' });
    const bodyText = await page.locator('body').innerText({ timeout: 10000 });
    routeChecks.push({ route, navigationAttempt: routeNavigationAttempt, hasReviewText: bodyText.includes('Portfolio') || bodyText.includes('Diagnosis') || bodyText.includes('Report') });
    await capturePageArtifact(page, `${index}-${scenario.id}-${route}`);
  }

  const staleUnlock = await browserJson(page, 'POST', `${baseUrl}/api/portfolio/candidate/generate`, {
    review_id: reviewId,
    selected_card_id: `${selectedCardId}_stale_probe`
  });
  assert.equal(staleUnlock.ok, false, `${scenario.id} stale selected-card probe unexpectedly succeeded.`);
  assert.equal(staleUnlock.status, 409, `${scenario.id} stale selected-card probe should fail with 409.`);

  const diagnosisEnvelope = envelope(diagnosis.body);
  const diagnosisData = record(diagnosisEnvelope.data);
  const diagnosisSummary = record(diagnosisData.diagnosis);
  const reportEnvelope = envelope(report.body);
  const reportData = record(reportEnvelope.data);

  const summary = {
    scenario_id: scenario.id,
    review_id: reviewId,
    selected_card_id: selectedCardId,
    candidate_id: candidateId,
    comparison_id: comparisonId,
    verdict_id: verdictId,
    diagnosis_primary: text(diagnosisSummary.primary_diagnosis),
    diagnosis_headline: text(diagnosisSummary.headline),
    diagnosis_evidence_count: Array.isArray(diagnosisSummary.diagnosis_evidence_items) ? diagnosisSummary.diagnosis_evidence_items.length : 0,
    diagnosis_attempt: diagnosis.attempt || 1,
    diagnosis_sources: sourceArtifacts(diagnosis.body),
    comparison_sources: sourceArtifacts(comparison.body),
    verdict_sources: sourceArtifacts(verdict.body),
    report_sources: sourceArtifacts(report.body),
    report_has_evidence_chain_context: Boolean(record(reportData.evidence_chain_context).recommendation_boundary || record(reportData.evidence_chain_context).diagnosis_statement),
    stale_probe_status: staleUnlock.status,
    route_checks: routeChecks
  };

  assert.ok(summary.diagnosis_primary || summary.diagnosis_headline, `${scenario.id} lacks diagnosis display summary.`);
  assert.ok(summary.diagnosis_evidence_count > 0 || summary.diagnosis_sources.length > 0, `${scenario.id} lacks source-backed diagnosis evidence.`);
  assert.ok(summary.report_has_evidence_chain_context, `${scenario.id} report lacks downstream evidence-chain context.`);
  assert.ok(summary.verdict_sources.includes('decision_verdict'), `${scenario.id} verdict sources do not include decision_verdict.`);
  return summary;
}

async function main() {
  ensureDir(outputRoot);
  let playwright;
  try {
    playwright = createRequire(path.join(frontendRoot, 'package.json'))('playwright');
  } catch (error) {
    throw new Error('Playwright module is unavailable. Run npm.cmd install in frontend, then: node scripts\\\\qa_browser_vertical.cjs');
  }

  const fastapiPort = await findAvailablePort();
  const frontendPort = await findAvailablePort();
  const fastapi = startFastApi(fastapiPort);
  const next = startNext(frontendPort, fastapiPort);
  const baseUrl = `http://${host}:${frontendPort}`;
  const fastapiUrl = `http://${host}:${fastapiPort}`;
  const report = {
    status: 'started',
    started_at: new Date().toISOString(),
    frontend_url: baseUrl,
    fastapi_url: fastapiUrl,
    output_dir: outputRoot,
    browser_state: 'fresh Playwright context per run; localStorage/sessionStorage cleared before each scenario',
    scenarios: [],
    failures: [],
    server_diagnostics: {}
  };

  try {
    await waitForHttp(`${fastapiUrl}/api/v1/health`, fastapi.child, fastapi.lines, 'FastAPI');
    await waitForHttp(`${baseUrl}/portfolio-input`, next.child, next.lines, 'Next.js');

    const nextDiag = serverDiagnostics(next.lines);
    assert.equal(nextDiag.fatal, false, `Next.js server has compile/.next diagnostics before QA.\n${nextDiag.tail}`);

    const browser = await playwright.chromium.launch({ headless });
    const context = await browser.newContext({ viewport: { width: 1440, height: 1100 } });
    const page = await context.newPage();
    page.setDefaultTimeout(30000);

    try {
      let index = 1;
      for (const scenario of scenarios) {
        const result = await runScenario(page, baseUrl, scenario, index);
        report.scenarios.push(result);
        index += 1;
      }
    } finally {
      await context.close();
      await browser.close();
    }

    const diagnoses = new Set(report.scenarios.map((scenario) => `${scenario.diagnosis_primary}|${scenario.diagnosis_headline}`));
    assert.ok(diagnoses.size >= Math.min(2, report.scenarios.length), 'Multiple scenarios did not produce distinct diagnosis summaries.');
    report.status = 'passed';
  } catch (error) {
    report.status = 'failed';
    report.failures.push(error && error.stack ? error.stack : String(error));
    throw error;
  } finally {
    report.finished_at = new Date().toISOString();
    report.server_diagnostics = {
      next: serverDiagnostics(next.lines),
      fastapi: { tail: outputTail(fastapi.lines, 160) }
    };
    fs.writeFileSync(path.join(outputRoot, 'qa-report.json'), JSON.stringify(report, null, 2), 'utf8');
    fs.writeFileSync(path.join(outputRoot, 'next.log'), next.lines.join(''), 'utf8');
    fs.writeFileSync(path.join(outputRoot, 'fastapi.log'), fastapi.lines.join(''), 'utf8');
    if (!keepServers) {
      stopProcess(next.child);
      stopProcess(fastapi.child);
    }
    console.log(JSON.stringify({ status: report.status, frontend_url: baseUrl, fastapi_url: fastapiUrl, output_dir: outputRoot, scenarios: report.scenarios }, null, 2));
  }
}

main().catch((error) => {
  console.error(error && error.stack ? error.stack : error);
  process.exitCode = 1;
});
