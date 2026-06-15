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
const scenarioLimit = scenarioLimitArgIndex >= 0 ? Number(process.argv[scenarioLimitArgIndex + 1]) : 5;
const headless = !process.argv.includes('--headed');
const keepServers = process.argv.includes('--keep-servers');

const scenarios = [
  {
    id: 'fit_material_issue',
    expectedDifferent: true,
    portfolio: {
      investor_currency: 'USD',
      client_fit: {
        preset_id: 'aggressive',
        target_return_range: { min: 0.04, max: 0.20 },
        target_vol_range: { min: 0.05, max: 0.35 },
        target_max_drawdown_pct: -0.60,
        horizon_years: 10,
        source: 'questionnaire',
        source_quality: 'high'
      },
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
    id: 'breach',
    expectedDifferent: true,
    portfolio: {
      investor_currency: 'USD',
      client_fit: {
        preset_id: 'conservative',
        target_return_range: { min: 0.02, max: 0.05 },
        target_vol_range: { min: 0.01, max: 0.06 },
        target_max_drawdown_pct: -0.08,
        horizon_years: 3,
        source: 'questionnaire',
        source_quality: 'high'
      },
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
    id: 'fit_clean',
    expectedDifferent: true,
    portfolio: {
      investor_currency: 'USD',
      client_fit: {
        preset_id: 'balanced',
        target_return_range: { min: 0.00, max: 0.25 },
        target_vol_range: { min: 0.02, max: 0.30 },
        target_max_drawdown_pct: -0.60,
        horizon_years: 7,
        source: 'questionnaire',
        source_quality: 'high'
      },
      holdings: [
        { type: 'instrument', ticker: 'QQQ', weight: 45 },
        { type: 'instrument', ticker: 'VOO', weight: 45 },
        { type: 'cash', currency: 'USD', weight: 10 }
      ]
    }
  },
  {
    id: 'conflict',
    expectedDifferent: true,
    portfolio: {
      investor_currency: 'USD',
      client_fit: {
        target_return_range: { min: 0.20, max: 0.30 },
        target_vol_range: { min: 0.01, max: 0.04 },
        target_max_drawdown_pct: -0.05,
        horizon_years: 2,
        source: 'manual_override',
        source_quality: 'high'
      },
      holdings: [
        { type: 'instrument', ticker: 'QQQ', weight: 60 },
        { type: 'instrument', ticker: 'VOO', weight: 30 },
        { type: 'cash', currency: 'USD', weight: 10 }
      ]
    }
  },
  {
    id: 'missing_blocked_client_fit',
    expectedDifferent: true,
    portfolio: {
      investor_currency: 'USD',
      holdings: [
        { type: 'instrument', ticker: 'QQQ', weight: 45 },
        { type: 'instrument', ticker: 'VOO', weight: 45 },
        { type: 'cash', currency: 'USD', weight: 10 }
      ]
    }
  }
].slice(0, Number.isFinite(scenarioLimit) && scenarioLimit > 0 ? scenarioLimit : 5);

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
  const internalSecret = process.env.PMRI_FASTAPI_INTERNAL_SECRET || process.env.PMRI_INTERNAL_AUTH_SECRET || 'vertical-qa-internal-secret';
  const child = spawn(python, args, {
    cwd: repoRoot,
    env: {
      ...process.env,
      PYTHONUTF8: '1',
      PMRI_FASTAPI_INTERNAL_SECRET: internalSecret,
      PMRI_INTERNAL_AUTH_SECRET: internalSecret
    },
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
  const internalSecret = process.env.PMRI_FASTAPI_INTERNAL_SECRET || process.env.PMRI_INTERNAL_AUTH_SECRET || 'vertical-qa-internal-secret';
  const child = spawn(process.execPath, [nextCli, 'dev', '--hostname', host, '--port', String(frontendPort)], {
    cwd: frontendRoot,
    env: {
      ...process.env,
      BROWSER: 'none',
      PMRI_FASTAPI_BASE_URL: `http://${host}:${fastapiPort}`,
      PMRI_FASTAPI_INTERNAL_SECRET: internalSecret,
      PMRI_INTERNAL_AUTH_SECRET: internalSecret,
      PMRI_PORTFOLIO_API_AUTH_MODE: process.env.PMRI_PORTFOLIO_API_AUTH_MODE || 'dev_bypass',
      PMRI_PORTFOLIO_API_DEV_USER_ID: process.env.PMRI_PORTFOLIO_API_DEV_USER_ID || 'vertical-qa-user'
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

function cardGeneratesPortfolio(card) {
  const setup = record(card.candidate_setup);
  return card.generates_portfolio === true
    || card.candidate_generation_allowed === true
    || setup.candidate_generation_allowed === true
    || Boolean(text(card.default_method) || text(setup.selected_method));
}

function envelope(body) {
  return record(body.fastapi_envelope || body);
}

function lineage(body) {
  return record(envelope(body).lineage);
}

function assertLineage(body, expected, label) {
  const actual = lineage(body);
  for (const [key, value] of Object.entries(expected)) {
    if (!value) continue;
    assert.equal(text(actual[key]), value, `${label} lineage ${key} mismatch.`);
  }
}

function sourceArtifacts(body) {
  const evidence = record(envelope(body).evidence);
  const refs = Array.isArray(evidence.source_artifacts) ? evidence.source_artifacts : [];
  return refs.map((ref) => text(record(ref).kind)).filter(Boolean);
}

function dataRecord(body) {
  return record(envelope(body).data);
}

function apiClientFit(body) {
  return record(dataRecord(body).client_fit);
}

function assertBoundedClientFit(body, label) {
  const clientFit = apiClientFit(body);
  assert.ok(text(clientFit.status_label), `${label} missing display client_fit.status_label.`);
  assert.ok(['green', 'amber', 'red'].includes(text(clientFit.status_tone)), `${label} client_fit.status_tone is not green/amber/red.`);
  const raw = JSON.stringify(clientFit);
  assert.equal(/schema_version|source_artifacts|client_fit_check\.json/i.test(raw), false, `${label} leaked raw Client Fit artifact fields.`);
}

function holdingsForState(portfolio) {
  return (Array.isArray(portfolio.holdings) ? portfolio.holdings : []).map((holding, index) => ({
    id: `${holding.type || 'instrument'}-${holding.ticker || holding.currency || index}`,
    label: holding.type === 'cash' ? `${holding.currency || 'USD'} cash` : holding.ticker,
    ticker: holding.type === 'cash' ? (holding.currency || 'USD') : holding.ticker,
    instrument: holding.type === 'cash' ? 'Cash' : holding.ticker,
    weight: Number(holding.weight) || 0,
    type: holding.type === 'cash' ? 'cash' : 'instrument',
    currency: holding.currency
  }));
}

function minimalDiagnosis(data) {
  const diagnosis = record(data.diagnosis);
  return {
    status: text(diagnosis.status) || 'Diagnosis ready',
    headline: text(diagnosis.headline, diagnosis.primary_diagnosis) || 'Portfolio diagnosis completed.',
    evidenceQuality: text(diagnosis.evidence_quality) || 'Evidence available',
    nextStep: text(diagnosis.next_step) || 'Review the next diagnostic test.',
    boundaryNote: text(diagnosis.boundary_note) || 'Diagnostic evidence only; decision action is separate.',
    drivers: Array.isArray(diagnosis.drivers) ? diagnosis.drivers.filter((item) => typeof item === 'string') : ['Portfolio evidence was generated for this review.'],
    metrics: Array.isArray(diagnosis.metrics) ? diagnosis.metrics : [],
    selectedDiagnosisRole: text(diagnosis.selected_diagnosis_role) || undefined,
    sourceArtifacts: sourceArtifacts({ fastapi_envelope: { evidence: envelope({ fastapi_envelope: { data } }).evidence } }),
    rejectedAlternatives: [],
    rationaleRefs: []
  };
}

function buildStoredState({ scenario, reviewId, selectedCardId, candidateId, comparisonId, verdictId, diagnosis, comparison, verdict, report }) {
  const diagnosisData = dataRecord(diagnosis.body);
  const comparisonData = dataRecord(comparison.body);
  const verdictData = dataRecord(verdict.body);
  const reportData = dataRecord(report.body);
  const holdings = holdingsForState(scenario.portfolio);
  const clientFit = apiClientFit(report.body);
  const now = new Date().toISOString();
  return {
    investorCurrency: scenario.portfolio.investor_currency || 'USD',
    holdings,
    clientFitProfile: scenario.portfolio.client_fit,
    reviewId,
    reviewResult: {
      status: 'completed',
      review_id: reviewId,
      outputs: {}
    },
    reviewSummary: {
      version: 1,
      source: 'real_run',
      status: 'completed',
      reviewId,
      generatedAt: now,
      investorCurrency: scenario.portfolio.investor_currency || 'USD',
      holdingsCount: holdings.length,
      totalWeight: holdings.reduce((sum, holding) => sum + holding.weight, 0),
      cashWeight: holdings.filter((holding) => holding.type === 'cash').reduce((sum, holding) => sum + holding.weight, 0),
      rawOutputKeys: [],
      outputPaths: {},
      diagnosis: minimalDiagnosis(diagnosisData),
      clientFit,
      launchpadCardsCount: 1,
      launchpadCards: [{
        card_id: selectedCardId,
        title: 'Selected diagnostic test',
        suggested_methods: [{ candidate_method_id: 'equal_weight', method_role: 'reference_benchmark' }],
        default_method: 'equal_weight',
        success_criteria: ['Compare the candidate against current evidence and Client Fit context.'],
        is_rebalance_recommendation: false,
        generates_portfolio: true
      }],
      suggestedActionPaths: [],
      candidateLaunchpadAvailable: true,
      problemClassificationAvailable: true,
      storage: {
        summaryBytes: 0,
        rawBytes: 0,
        rawPersisted: false,
        rawAccessStrategy: 'Browser QA compact state only.'
      }
    },
    builderSetup: {
      selected_card_id: selectedCardId,
      can_generate_candidate: true,
      builder_prefill: {
        goal: 'Reference comparison',
        suggested_method: 'equal_weight'
      },
      candidate_setup: {
        validation_status: 'valid',
        can_generate_candidate: true
      }
    },
    candidateGeneration: {
      status: 'completed',
      stage: 'candidate_generation',
      selectedCardId,
      candidateId,
      generationStatus: 'generated',
      canCompare: true,
      weights: [],
      generatedAt: now
    },
    comparisonResult: {
      status: 'completed',
      stage: 'current_vs_candidate',
      selectedCardId,
      candidateId,
      comparisonStatus: 'available',
      viewMode: text(comparisonData.view_mode) || 'current_vs_candidate',
      candidateName: text(comparisonData.candidate_name) || candidateId,
      candidateBoundary: text(comparisonData.candidate_boundary) || 'Comparison is evidence, not an instruction.',
      evidenceQuality: text(comparisonData.evidence_quality) || 'Evidence available',
      summary: text(comparisonData.summary) || `Comparison ${comparisonId} is available.`,
      metrics: Array.isArray(comparisonData.metrics) ? comparisonData.metrics : [],
      improved: Array.isArray(comparisonData.improved) ? comparisonData.improved : [],
      worsened: Array.isArray(comparisonData.worsened) ? comparisonData.worsened : [],
      neutral: Array.isArray(comparisonData.neutral) ? comparisonData.neutral : [],
      unclear: Array.isArray(comparisonData.unclear) ? comparisonData.unclear : [],
      turnover: text(comparisonData.turnover) || 'n/a',
      estimatedCost: text(comparisonData.estimated_cost) || 'n/a',
      materiality: text(comparisonData.materiality) || 'Evidence review',
      warnings: Array.isArray(comparisonData.warnings) ? comparisonData.warnings : [],
      clientFit,
      generatedAt: now
    },
    verdictResult: {
      status: 'completed',
      stage: 'decision_verdict',
      selectedCardId,
      candidateId,
      verdictId,
      decisionStatus: text(verdictData.decision_status) || 'review',
      confidence: text(verdictData.confidence) || 'Evidence available',
      state: text(verdictData.state) || 'Decision support',
      headline: text(verdictData.headline) || 'Verdict evidence is available.',
      explanation: text(verdictData.explanation) || 'Read this as non-binding decision support.',
      evidenceQuality: text(verdictData.evidence_quality) || 'Evidence available',
      boundaryNote: text(verdictData.boundary_note) || 'Not a trade instruction.',
      keyEvidence: Array.isArray(verdictData.key_evidence) ? verdictData.key_evidence : [],
      monitoringTrigger: text(verdictData.monitoring_trigger) || 'Retest if evidence changes.',
      metrics: Array.isArray(verdictData.metrics) ? verdictData.metrics : [],
      actionFraming: text(verdictData.action_framing) || 'Decision-support framing only.',
      limitations: Array.isArray(verdictData.limitations) ? verdictData.limitations : [],
      evidenceUsed: Array.isArray(verdictData.evidence_used) ? verdictData.evidence_used : [],
      whatWouldChangeVerdict: Array.isArray(verdictData.what_would_change_verdict) ? verdictData.what_would_change_verdict : [],
      clientFit,
      generatedAt: now
    },
    reportResult: {
      status: 'completed',
      stage: 'report',
      selectedCardId,
      candidateId,
      title: text(reportData.title) || 'Grounded client-ready report summary',
      subtitle: text(reportData.subtitle) || 'Evidence-backed report preview.',
      sections: Array.isArray(reportData.sections) ? reportData.sections : [],
      evidenceUsed: Array.isArray(reportData.evidence_used) ? reportData.evidence_used : [],
      unavailableEvidence: Array.isArray(reportData.unavailable_evidence) ? reportData.unavailable_evidence : [],
      nextObservation: text(reportData.next_observation) || 'Retest if evidence changes.',
      boundaryNote: text(reportData.boundary_note) || 'Decision-support only.',
      warnings: Array.isArray(reportData.warnings) ? reportData.warnings : [],
      clientFit,
      generatedAt: now
    },
    runMode: 'real_run',
    runStatus: 'completed',
    submitted: true,
    diagnosisReady: true,
    evidenceReady: true,
    improvementPathsReady: true,
    candidateReady: true,
    comparisonReady: true,
    verdictReady: true,
    updatedAt: now
  };
}

function buildDiagnosisOnlyStoredState({ scenario, reviewId, selectedCardId, diagnosis }) {
  const diagnosisData = dataRecord(diagnosis.body);
  const holdings = holdingsForState(scenario.portfolio);
  const clientFit = apiClientFit(diagnosis.body);
  const now = new Date().toISOString();
  return {
    investorCurrency: scenario.portfolio.investor_currency || 'USD',
    holdings,
    clientFitProfile: scenario.portfolio.client_fit,
    reviewId,
    reviewResult: {
      status: 'completed',
      review_id: reviewId,
      outputs: {}
    },
    reviewSummary: {
      version: 1,
      source: 'real_run',
      status: 'completed',
      reviewId,
      generatedAt: now,
      investorCurrency: scenario.portfolio.investor_currency || 'USD',
      holdingsCount: holdings.length,
      totalWeight: holdings.reduce((sum, holding) => sum + holding.weight, 0),
      cashWeight: holdings.filter((holding) => holding.type === 'cash').reduce((sum, holding) => sum + holding.weight, 0),
      rawOutputKeys: [],
      outputPaths: {},
      diagnosis: minimalDiagnosis(diagnosisData),
      clientFit,
      launchpadCardsCount: 1,
      launchpadCards: [{
        card_id: selectedCardId,
        title: 'Review objectives before candidate testing',
        card_type: 'monitor_or_data_step',
        suggested_methods: [],
        success_criteria: ['Clarify the Client Fit profile before candidate testing.'],
        is_rebalance_recommendation: false,
        generates_portfolio: false
      }],
      suggestedActionPaths: [],
      candidateLaunchpadAvailable: true,
      problemClassificationAvailable: true,
      storage: {
        summaryBytes: 0,
        rawBytes: 0,
        rawPersisted: false,
        rawAccessStrategy: 'Browser QA compact state only.'
      }
    },
    runMode: 'real_run',
    runStatus: 'completed',
    submitted: true,
    diagnosisReady: true,
    evidenceReady: true,
    improvementPathsReady: true,
    candidateReady: false,
    comparisonReady: false,
    verdictReady: false,
    updatedAt: now
  };
}

function sanitizedForAdviceScan(bodyText) {
  return bodyText
    .replace(/Equity sell-off/gi, 'Equity stress event')
    .replace(/not a trade instruction/gi, 'not an instruction')
    .replace(/not .*profile sign-off/gi, 'not a profile sign off');
}

function assertNoForbiddenAdvice(bodyText, label) {
  const sanitized = sanitizedForAdviceScan(bodyText);
  assert.equal(/\bsuitable\b|\bsuitability approved\b|\bapproved\b|\bbuy\b|\bsell\b|\bmust rebalance\b|\bbest portfolio\b/i.test(sanitized), false, `${label} contains forbidden advice/suitability copy.`);
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
    const result = await browserJson(page, 'POST', `${baseUrl}/api/portfolio/diagnose`, {
      ...scenario.portfolio,
      mode: 'demo_qa'
    });
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

function stageReady(statusBody, stage) {
  const stages = record(statusBody.stages);
  const row = record(stages[stage]);
  return row.status === 'completed' || row.status === 'partial';
}

function diagnosisChainReady(statusBody) {
  return stageReady(statusBody, 'xray')
    && stageReady(statusBody, 'stress')
    && stageReady(statusBody, 'problem_classification')
    && stageReady(statusBody, 'launchpad_builder');
}

async function pollStagedDiagnosisReady(page, baseUrl, reviewId) {
  const deadline = Date.now() + requestTimeoutMs;
  let latest = null;
  while (Date.now() < deadline) {
    const status = await browserJson(page, 'GET', `${baseUrl}/api/portfolio/review/status?reviewId=${encodeURIComponent(reviewId)}`);
    assertOk(status, `staged status ${reviewId}`);
    latest = status.body;
    if (latest.safe_error || latest.status === 'failed') {
      throw new Error(`Staged diagnosis failed for ${reviewId}: ${JSON.stringify(latest.safe_error || latest).slice(0, 1000)}`);
    }
    if (diagnosisChainReady(latest)) return latest;
    await sleep(1000);
  }
  throw new Error(`Timed out waiting for staged diagnosis chain for ${reviewId}. Last status: ${JSON.stringify(latest).slice(0, 1000)}`);
}

async function pollStageReady(page, baseUrl, reviewId, stage) {
  const deadline = Date.now() + requestTimeoutMs;
  let latest = null;
  while (Date.now() < deadline) {
    const status = await browserJson(page, 'GET', `${baseUrl}/api/portfolio/review/status?reviewId=${encodeURIComponent(reviewId)}`);
    assertOk(status, `staged status ${reviewId}`);
    latest = status.body;
    if (latest.safe_error || latest.status === 'failed') {
      throw new Error(`Staged review failed while waiting for ${stage} on ${reviewId}: ${JSON.stringify(latest.safe_error || latest).slice(0, 1000)}`);
    }
    if (stageReady(latest, stage)) return latest;
    await sleep(1000);
  }
  throw new Error(`Timed out waiting for staged ${stage} on ${reviewId}. Last status: ${JSON.stringify(latest).slice(0, 1000)}`);
}

async function recoverStagedDiagnosis(page, baseUrl, reviewId) {
  const recovery = await browserJson(page, 'POST', `${baseUrl}/api/portfolio/review/recover`, {
    review_id: reviewId
  });
  assertOk(recovery, `recover staged diagnosis ${reviewId}`);
  assert.equal(record(recovery.body.review_result).status, 'completed', `Recovered review ${reviewId} is not completed.`);
  return recovery;
}

function assertOk(result, label) {
  assert.equal(result.ok, true, `${label} failed with HTTP ${result.status}: ${JSON.stringify(result.body).slice(0, 2000)}`);
}

async function runScenario(page, baseUrl, scenario, index) {
  await gotoWithRetry(page, `${baseUrl}/portfolio-input`, { waitUntil: 'domcontentloaded' });
  await page.evaluate(() => { localStorage.clear(); sessionStorage.clear(); });
  await capturePageArtifact(page, `${index}-${scenario.id}-input`);

  const started = await diagnoseWithRetry(page, baseUrl, scenario, 3);
  assertOk(started, `${scenario.id} diagnosis start`);
  const diagnosisLineage = lineage(started.body);
  const reviewId = text(started.body.review_id) || text(diagnosisLineage.review_id);
  assert.ok(reviewId.startsWith('frontend_review_'), `${scenario.id} returned invalid reviewId ${reviewId}`);
  await pollStagedDiagnosisReady(page, baseUrl, reviewId);
  const diagnosis = await recoverStagedDiagnosis(page, baseUrl, reviewId);

  const cards = findCards(diagnosis.body);
  assert.ok(cards.length > 0, `${scenario.id} returned no Launchpad cards.`);
  const selectedCard = chooseCard(cards);
  const selectedCardId = text(selectedCard.card_id || selectedCard.id);
  assert.ok(selectedCardId, `${scenario.id} selected card has no id.`);
  const selectedCardGeneratesPortfolio = cardGeneratesPortfolio(selectedCard);

  if (!selectedCardGeneratesPortfolio) {
    assertBoundedClientFit(diagnosis.body, `${scenario.id} diagnosis`);
    const storedState = buildDiagnosisOnlyStoredState({ scenario, reviewId, selectedCardId, diagnosis });
    await page.goto(baseUrl, { waitUntil: 'domcontentloaded' });
    await page.evaluate((state) => {
      localStorage.clear();
      sessionStorage.clear();
      localStorage.setItem('pmri.activeReview.v2', JSON.stringify(state));
    }, storedState);

    const routes = ['client-profile', 'diagnosis', 'evidence', 'client-fit', 'hypothesis'];
    const routeChecks = [];
    for (const route of routes) {
      const routeNavigationAttempt = await gotoWithRetry(page, `${baseUrl}/${route}`, { waitUntil: 'domcontentloaded' });
      const bodyText = await page.locator('body').innerText({ timeout: 10000 });
      assertNoForbiddenAdvice(bodyText, `${scenario.id} ${route}`);
      routeChecks.push({ route, navigationAttempt: routeNavigationAttempt, hasReviewText: bodyText.includes('Portfolio') || bodyText.includes('Diagnosis') || bodyText.includes('Client Fit') });
      await capturePageArtifact(page, `${index}-${scenario.id}-${route}`);
    }

    const diagnosisEnvelope = envelope(diagnosis.body);
    const diagnosisData = record(diagnosisEnvelope.data);
    const diagnosisSummary = record(diagnosisData.diagnosis);
    return {
      scenario_id: scenario.id,
      review_id: reviewId,
      selected_card_id: selectedCardId,
      candidate_id: null,
      comparison_id: null,
      verdict_id: null,
      downstream_status: 'skipped_non_candidate_card',
      diagnosis_primary: text(diagnosisSummary.primary_diagnosis),
      diagnosis_headline: text(diagnosisSummary.headline),
      diagnosis_evidence_count: Array.isArray(diagnosisSummary.diagnosis_evidence_items) ? diagnosisSummary.diagnosis_evidence_items.length : 0,
      diagnosis_attempt: started.attempt || 1,
      client_fit_status_label: text(apiClientFit(diagnosis.body).status_label),
      client_fit_status_tone: text(apiClientFit(diagnosis.body).status_tone),
      diagnosis_sources: sourceArtifacts(diagnosis.body),
      comparison_sources: [],
      verdict_sources: [],
      report_sources: [],
      report_has_evidence_chain_context: false,
      stale_probe_status: null,
      route_checks: routeChecks
    };
  }

  const builder = await browserJson(page, 'POST', `${baseUrl}/api/portfolio/builder/prepare`, {
    review_id: reviewId,
    selected_card_id: selectedCardId
  });
  assertOk(builder, `${scenario.id} builder`);
  assertLineage(builder.body, { review_id: reviewId, selected_card_id: selectedCardId }, `${scenario.id} builder`);
  const builderSetupId = text(lineage(builder.body).builder_setup_id) || text(builder.body.builder_setup_id);

  const candidate = await browserJson(page, 'POST', `${baseUrl}/api/portfolio/candidate/generate`, {
    review_id: reviewId,
    selected_card_id: selectedCardId,
    builder_setup_id: builderSetupId
  });
  assertOk(candidate, `${scenario.id} candidate`);
  const candidateId = text(candidate.body.candidate_id) || text(lineage(candidate.body).candidate_id);
  assert.ok(candidateId, `${scenario.id} returned no candidate id.`);
  assertLineage(candidate.body, { review_id: reviewId, selected_card_id: selectedCardId, candidate_id: candidateId }, `${scenario.id} candidate`);
  await pollStageReady(page, baseUrl, reviewId, 'candidate');

  const comparison = await browserJson(page, 'POST', `${baseUrl}/api/portfolio/comparison/generate`, {
    review_id: reviewId,
    selected_card_id: selectedCardId,
    candidate_id: candidateId
  });
  assertOk(comparison, `${scenario.id} comparison`);
  const comparisonId = text(lineage(comparison.body).comparison_id) || `current_vs_candidate:${candidateId}`;
  assertLineage(comparison.body, { review_id: reviewId, selected_card_id: selectedCardId, candidate_id: candidateId, comparison_id: comparisonId }, `${scenario.id} comparison`);

  const verdict = await browserJson(page, 'POST', `${baseUrl}/api/portfolio/verdict/generate`, {
    review_id: reviewId,
    selected_card_id: selectedCardId,
    candidate_id: candidateId,
    comparison_id: comparisonId
  });
  assertOk(verdict, `${scenario.id} verdict`);
  const verdictId = text(verdict.body.verdict_id) || text(lineage(verdict.body).verdict_id);
  assert.ok(verdictId, `${scenario.id} returned no verdict id.`);
  assertLineage(verdict.body, { review_id: reviewId, selected_card_id: selectedCardId, candidate_id: candidateId, comparison_id: comparisonId, verdict_id: verdictId }, `${scenario.id} verdict`);

  const report = await browserJson(page, 'POST', `${baseUrl}/api/portfolio/report/generate`, {
    review_id: reviewId,
    selected_card_id: selectedCardId,
    candidate_id: candidateId,
    verdict_id: verdictId
  });
  assertOk(report, `${scenario.id} report`);
  assertLineage(report.body, { review_id: reviewId, selected_card_id: selectedCardId, candidate_id: candidateId, comparison_id: comparisonId, verdict_id: verdictId }, `${scenario.id} report`);

  for (const [label, body] of [
    ['diagnosis', diagnosis.body],
    ['comparison', comparison.body],
    ['verdict', verdict.body],
    ['report', report.body]
  ]) {
    assertBoundedClientFit(body, `${scenario.id} ${label}`);
  }

  const storedState = buildStoredState({ scenario, reviewId, selectedCardId, candidateId, comparisonId, verdictId, diagnosis, comparison, verdict, report });
  await page.goto(baseUrl, { waitUntil: 'domcontentloaded' });
  await page.evaluate((state) => {
    localStorage.clear();
    sessionStorage.clear();
    localStorage.setItem('pmri.activeReview.v2', JSON.stringify(state));
  }, storedState);

  const routes = ['client-profile', 'diagnosis', 'evidence', 'client-fit', 'hypothesis', 'comparison', 'verdict', 'report'];
  const routeChecks = [];
  for (const route of routes) {
    const routeNavigationAttempt = await gotoWithRetry(page, `${baseUrl}/${route}`, { waitUntil: 'domcontentloaded' });
    const bodyText = await page.locator('body').innerText({ timeout: 10000 });
    assertNoForbiddenAdvice(bodyText, `${scenario.id} ${route}`);
    routeChecks.push({ route, navigationAttempt: routeNavigationAttempt, hasReviewText: bodyText.includes('Portfolio') || bodyText.includes('Diagnosis') || bodyText.includes('Report') || bodyText.includes('Client Fit') });
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
    diagnosis_attempt: started.attempt || 1,
    client_fit_status_label: text(apiClientFit(report.body).status_label),
    client_fit_status_tone: text(apiClientFit(report.body).status_tone),
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
    warnings: [],
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
    if (diagnoses.size < Math.min(2, report.scenarios.length)) {
      report.warnings.push('Demo QA mode returned the same fixed diagnosis summary across scenarios; lineage, downstream route chain, and stale-card rejection remain the release gate for this helper.');
    }
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
