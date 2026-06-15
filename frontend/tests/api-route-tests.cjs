const assert = require("node:assert/strict");
const nodeCrypto = require("node:crypto");
const fs = require("node:fs");
const path = require("node:path");
const test = require("node:test");
const ts = require("typescript");

if (!globalThis.crypto?.subtle) {
  globalThis.crypto = nodeCrypto.webcrypto;
}

const frontendRoot = path.resolve(__dirname, "..");
const builderPrepareRoutePath = path.resolve(frontendRoot, "app", "api", "portfolio", "builder", "prepare", "route.ts");
const candidateGenerateRoutePath = path.resolve(frontendRoot, "app", "api", "portfolio", "candidate", "generate", "route.ts");
const diagnoseRoutePath = path.resolve(frontendRoot, "app", "api", "portfolio", "diagnose", "route.ts");
const reportGenerateRoutePath = path.resolve(frontendRoot, "app", "api", "portfolio", "report", "generate", "route.ts");
const reviewRecoverRoutePath = path.resolve(frontendRoot, "app", "api", "portfolio", "review", "recover", "route.ts");
const reviewStatusRoutePath = path.resolve(frontendRoot, "app", "api", "portfolio", "review", "status", "route.ts");
const supabasePersistencePath = path.resolve(frontendRoot, "lib", "supabase", "persistence.tsx");
const supabaseSchemaPath = path.resolve(frontendRoot, "..", "docs", "supabase", "supabase_free_schema.sql");
const supabaseAuthCallbackPath = path.resolve(frontendRoot, "app", "auth", "callback", "route.ts");
const sidebarPath = path.resolve(frontendRoot, "components", "layout", "Sidebar.tsx");
const portfolioInputTablePath = path.resolve(frontendRoot, "components", "portfolio", "PortfolioInputTable.tsx");
const reviewStatePath = path.resolve(frontendRoot, "lib", "reviewState.tsx");
const stagedSafeErrorPath = path.resolve(frontendRoot, "lib", "review", "stagedSafeError.ts");
const fastApiErrorsPath = path.resolve(frontendRoot, "lib", "server", "fastapi", "errors.ts");
const journeyPath = path.resolve(frontendRoot, "lib", "journey.ts");
const clientFitContextCardPath = path.resolve(frontendRoot, "components", "client-fit", "ClientFitContextCard.tsx");
const clientFitPresentationPath = path.resolve(frontendRoot, "lib", "clientFitPresentation.ts");
const siteExplanationHierarchyPath = path.resolve(frontendRoot, "components", "explanation", "SiteExplanationHierarchy.tsx");
const diagnosisPagePath = path.resolve(frontendRoot, "app", "diagnosis", "page.tsx");
const diagnosisDisplayModelPath = path.resolve(frontendRoot, "lib", "diagnosisDisplayModel.ts");
const diagnosisSummaryPanelPath = path.resolve(frontendRoot, "components", "diagnosis", "DiagnosisSummaryPanel.tsx");
const stressStoryModelPath = path.resolve(frontendRoot, "components", "evidence", "stressStoryModel.ts");
const hypothesisPagePath = path.resolve(frontendRoot, "app", "hypothesis", "page.tsx");
const comparisonPagePath = path.resolve(frontendRoot, "app", "comparison", "page.tsx");
const verdictPagePath = path.resolve(frontendRoot, "app", "verdict", "page.tsx");
const siteExplanationPresenterPath = path.resolve(frontendRoot, "lib", "siteExplanationPresenter.ts");
const hypothesisScreenModelPath = path.resolve(frontendRoot, "lib", "hypothesis", "hypothesisScreenModel.ts");

function makeJsonRequest(body, url = "http://localhost/api/portfolio/builder/prepare") {
  return new Request(url, {
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

function loadTsModule(filePath, { readFileImpl, moduleCache = new Map() } = {}) {
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
      return loadTsModule(tsPath, { readFileImpl, moduleCache });
    }
    if (specifier.startsWith(".")) {
      const relativePath = path.resolve(path.dirname(resolvedPath), specifier);
      const tsPath = fs.existsSync(`${relativePath}.ts`) ? `${relativePath}.ts` : relativePath;
      return loadTsModule(tsPath, { readFileImpl, moduleCache });
    }
    return require(specifier);
  };

  Function("require", "exports", "module", compiled)(sandboxRequire, exports, module);
  return module.exports;
}

function readJsonFixture(filePath) {
  return JSON.parse(fs.readFileSync(filePath, "utf8").replace(/^\uFEFF/, ""));
}

function loadRoute({ routePath = builderPrepareRoutePath, readFileImpl } = {}) {
  return loadTsModule(routePath, { readFileImpl });
}

async function responseJson(response) {
  return { status: response.status, body: await response.json() };
}

async function withMockFetch(mockFetch, callback) {
  const original = globalThis.fetch;
  const originalPortfolioAuthMode = process.env.PMRI_PORTFOLIO_API_AUTH_MODE;
  const originalPortfolioDevUserId = process.env.PMRI_PORTFOLIO_API_DEV_USER_ID;
  const originalInternalSecret = process.env.PMRI_FASTAPI_INTERNAL_SECRET;
  process.env.PMRI_PORTFOLIO_API_AUTH_MODE = "dev_bypass";
  process.env.PMRI_PORTFOLIO_API_DEV_USER_ID = "frontend-route-test-user";
  process.env.PMRI_FASTAPI_INTERNAL_SECRET = "frontend-route-test-secret";
  globalThis.fetch = mockFetch;
  try {
    return await callback();
  } finally {
    globalThis.fetch = original;
    if (originalPortfolioAuthMode === undefined) delete process.env.PMRI_PORTFOLIO_API_AUTH_MODE;
    else process.env.PMRI_PORTFOLIO_API_AUTH_MODE = originalPortfolioAuthMode;
    if (originalPortfolioDevUserId === undefined) delete process.env.PMRI_PORTFOLIO_API_DEV_USER_ID;
    else process.env.PMRI_PORTFOLIO_API_DEV_USER_ID = originalPortfolioDevUserId;
    if (originalInternalSecret === undefined) delete process.env.PMRI_FASTAPI_INTERNAL_SECRET;
    else process.env.PMRI_FASTAPI_INTERNAL_SECRET = originalInternalSecret;
  }
}

function assertSignedFastApiHeaders(options) {
  const userId = options.headers["X-PMRI-User-Id"];
  const timestamp = options.headers["X-PMRI-Auth-Timestamp"];
  const signature = options.headers["X-PMRI-Internal-Signature"];
  assert.equal(userId, "frontend-route-test-user");
  assert.match(timestamp, /^\d+$/);
  assert.match(signature, /^[a-f0-9]{64}$/);
  assert.equal(
    signature,
    nodeCrypto
      .createHmac("sha256", "frontend-route-test-secret")
      .update(`${userId}.${timestamp}`)
      .digest("hex")
  );
}

function fastApiEnvelope(overrides = {}) {
  return {
    api_version: "v1",
    schema_version: "builder_setup_v1",
    review_id: "frontend_review_ok",
    stage: "builder",
    status: "ok",
    lineage: { review_id: "frontend_review_ok" },
    data: { candidate_generation_allowed: true },
    warnings: [],
    safe_error: null,
    evidence: { source_artifacts: [], data_quality: "ok", confidence: "medium" },
    ...overrides
  };
}

function fastApiReportEnvelope(overrides = {}) {
  return fastApiEnvelope({
    schema_version: "report_grounding_v1",
    stage: "report",
    data: {
      report_preview: {
        executive_summary: "Current evidence supports a grounded decision-support preview.",
        current_portfolio_diagnosis: "Diagnosis summary from the public API.",
        stress_evidence: ["Stress evidence line."],
        tested_hypothesis: "Equal Weight diagnostic test.",
        candidate_boundary: "Candidate is a test, not a recommendation.",
        comparison_tradeoffs: ["Risk concentration improved; turnover should be reviewed."],
        verdict_explanation: "No material rebalance is recommended from this evidence.",
        evidence_limitations: ["Historical replay is partial."],
        monitoring_note: "Retest when comparison evidence changes."
      },
      grounding: {
        source_refs: [
          { kind: "portfolio_xray", ref: "logical://portfolio_xray", scope: "logical", raw_path_exposed: false },
          { kind: "decision_verdict", ref: "logical://decision_verdict", scope: "logical", raw_path_exposed: false }
        ],
        unavailable_sections: []
      },
      evidence_chain_context: {
        diagnosis_statement: "Concentration is the selected root-cause diagnosis.",
        tested_hypothesis: "Equal Weight diagnostic test.",
        candidate_boundary: "Candidate is a test, not a recommendation.",
        recommendation_boundary: "Decision-support only from FastAPI context.",
        source_artifacts: ["problem_classification.json", "current_vs_candidate.json"]
      },
      llm_generated: false
    },
    warnings: [],
    ...overrides
  });
}

test("builder prepare route rejects invalid JSON before calling FastAPI", async () => {
  const route = loadRoute();

  await withMockFetch(async () => {
    throw new Error("fetch was not expected");
  }, async () => {
    const result = await responseJson(await route.POST(makeInvalidJsonRequest()));
    assert.equal(result.status, 400);
    assert.equal(result.body.status, "failed");
    assert.equal(result.body.error, "Request body must be valid JSON.");
  });
});

test("builder prepare route validates review id format and missing selected card", async () => {
  const route = loadRoute();

  await withMockFetch(async () => {
    throw new Error("fetch was not expected");
  }, async () => {
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
});

test("builder prepare route proxies to FastAPI and scrubs safe backend errors", async () => {
  const route = loadRoute();
  const calls = [];
  const root = path.resolve(process.cwd(), "..");
  const localPath = path.join(root, "scripts", "run_review_from_payload.py");

  await withMockFetch(async (url, options) => {
    calls.push({ url, options });
    return Response.json({
      safe_error: {
        message: `Cannot prepare builder at ${localPath}`,
        details: [`Traceback (most recent call last):\n  File "${localPath}", line 10, in <module>\nRuntimeError: boom`]
      }
    }, { status: 500 });
  }, async () => {
    const result = await responseJson(await route.POST(makeJsonRequest({
      review_id: "frontend_review_123",
      selected_card_id: "card_equal_weight"
    })));

    assert.equal(result.status, 500);
    assert.equal(result.body.status, "failed");
    assert.equal(result.body.stage, "builder_setup");
    assert.equal(result.body.review_id, "frontend_review_123");
    assert.equal(result.body.selected_card_id, "card_equal_weight");
    assert.equal(calls.length, 1);
    assert.match(calls[0].url, /\/api\/v1\/reviews\/frontend_review_123\/builder$/);
    assert.equal(calls[0].options.method, "POST");
    assertSignedFastApiHeaders(calls[0].options);
    assert.equal(calls[0].options.headers["Content-Type"], "application/json");
    assert.deepEqual(JSON.parse(calls[0].options.body), {
      selected_card_id: "card_equal_weight",
      overrides: {}
    });
    const serialized = JSON.stringify(result.body);
    assert.doesNotMatch(serialized, /Traceback \(most recent call last\):/);
    assert.doesNotMatch(serialized, /run_review_from_payload\.py/);
    assert.doesNotMatch(serialized, /D:[\\/]/);
    assert.match(serialized, /\[path\]|\[project\]|Backend failure details were captured safely/);
  });
});

test("builder prepare route returns legacy-compatible setup after FastAPI success", async () => {
  const route = loadRoute();

  await withMockFetch(async () => Response.json(fastApiEnvelope({
    lineage: {
      review_id: "frontend_review_ok",
      selected_card_id: "card_equal_weight",
      builder_setup_id: "candidate_setup_card_equal_weight"
    },
    data: {
      candidate_generation_allowed: true,
      builder_setup: {
        builder_setup_id: "candidate_setup_card_equal_weight",
        selected_card_id: "card_equal_weight",
        method_id: "equal_weight",
        generation_readiness: "ready"
      },
      next_allowed_actions: ["generate_candidate"]
    },
    evidence: {
      source_artifacts: [{
        kind: "portfolio_alternatives_builder",
        ref: "runs/frontend_review_ok/analysis_subject/portfolio_alternatives_builder.json",
        scope: "analysis_subject",
        raw_path_exposed: false
      }],
      data_quality: "ok",
      confidence: "medium"
    }
  })), async () => {
    const result = await responseJson(await route.POST(makeJsonRequest({
      review_id: "frontend_review_ok",
      selected_card_id: "card_equal_weight"
    })));

    assert.equal(result.status, 200);
    assert.equal(result.body.status, "completed");
    assert.equal(result.body.stage, "builder_setup");
    assert.equal(result.body.can_generate_candidate, true);
    assert.equal(result.body.path, "runs/frontend_review_ok/analysis_subject/portfolio_alternatives_builder.json");
    assert.equal(result.body.portfolio_alternatives_builder.candidate_setup.candidate_setup_id, "candidate_setup_card_equal_weight");
  });
});

test("staged safe error formatter includes code, stage, and retry guidance", () => {
  const { stagedSafeErrorMessage } = loadTsModule(stagedSafeErrorPath);

  const message = stagedSafeErrorMessage({
    message: "Market data provider failed during data loading.",
    code: "DATA_PROVIDER_FAILED",
    stage: "data_load",
    retryable: true
  });

  assert.equal(
    message,
    "Market data provider failed during data loading. Code: DATA_PROVIDER_FAILED Stage: data_load You can retry after checking that the backend/frontend servers are freshly restarted."
  );
});

test("FastAPI legacy error mapper scrubs unsafe backend details", () => {
  const { legacyErrorFromFastApi } = loadTsModule(fastApiErrorsPath);

  const result = legacyErrorFromFastApi({
    safe_error: {
      message: "Backend run failed.",
      details: [
        "Traceback (most recent call last):\n  File \"D:\\repo\\scripts\\run_review_from_payload.py\", line 10, in run\nValueError: boom",
        "/Users/alice/project/run_review_from_payload.py failed"
      ]
    }
  }, "Fallback failure.");

  assert.equal(result.status, "failed");
  assert.equal(result.error, "Backend run failed.");
  assert.deepEqual(result.details, [
    "Backend failure details were captured safely.",
    "[path] failed"
  ]);
});

test("diagnosis route maps instrument and cash rows into the staged FastAPI create-review contract", async () => {
  const calls = [];
  const route = loadRoute({ routePath: diagnoseRoutePath });
  const originalPmriBaseUrl = process.env.PMRI_FASTAPI_BASE_URL;
  const originalFastApiBaseUrl = process.env.FASTAPI_BASE_URL;
  delete process.env.PMRI_FASTAPI_BASE_URL;
  process.env.FASTAPI_BASE_URL = "http://fastapi.test:53265/";

  try {
    await withMockFetch(async (url, options) => {
      calls.push({ url, options });
      return Response.json({
        api_version: "v1",
        schema_version: "review_started_v1",
        review_id: "frontend_review_cash",
        stage: "diagnosis",
        status: "running",
        current_stage: "input",
        mode: "live",
        warnings: [],
        safe_error: null
      });
    }, async () => {
      const result = await responseJson(await route.POST(makeJsonRequest({
        investor_currency: "USD",
        holdings: [
          { type: "instrument", ticker: "SPY", weight: 80 },
          { type: "cash", currency: "USD", weight: 20 }
        ]
      }, "http://localhost/api/portfolio/diagnose")));

      assert.equal(result.status, 200);
      assert.equal(result.body.review_id, "frontend_review_cash");
      assert.equal(result.body.schema_version, "review_started_v1");
      assert.equal(calls.length, 1);
      assert.equal(calls[0].url, "http://fastapi.test:53265/api/v1/reviews/staged");
      assertSignedFastApiHeaders(calls[0].options);
      assert.deepEqual(JSON.parse(calls[0].options.body), {
        portfolio: {
          investor_currency: "USD",
          holdings: [
            { type: "instrument", ticker: "SPY", weight_pct: 80 },
            { type: "cash", currency: "USD", weight_pct: 20 }
          ]
        },
        options: {
          mode: "diagnosis_only",
          output_profile: "site_api",
          sample_mode: false
        }
      });
    });
  } finally {
    if (originalPmriBaseUrl === undefined) delete process.env.PMRI_FASTAPI_BASE_URL;
    else process.env.PMRI_FASTAPI_BASE_URL = originalPmriBaseUrl;
    if (originalFastApiBaseUrl === undefined) delete process.env.FASTAPI_BASE_URL;
    else process.env.FASTAPI_BASE_URL = originalFastApiBaseUrl;
  }
});

test("diagnosis route forwards completed Client Fit profile into the staged FastAPI create-review contract", async () => {
  const calls = [];
  const route = loadRoute({ routePath: diagnoseRoutePath });

  const clientFit = {
    preset_id: "balanced",
    source: "questionnaire",
    source_quality: "medium",
    source_quality_reason: "Questionnaire confirmed.",
    horizon_years: 7,
    target_return_range: { min: 0.05, max: 0.07 },
    target_vol_range: { min: 0.07, max: 0.10 },
    target_max_drawdown_pct: -0.20
  };

  await withMockFetch(async (url, options) => {
    calls.push({ url, options });
    return Response.json({
      api_version: "v1",
      schema_version: "review_started_v1",
      review_id: "frontend_review_client_fit",
      stage: "diagnosis",
      status: "running",
      current_stage: "input",
      mode: "live",
      warnings: [],
      safe_error: null
    });
  }, async () => {
    const result = await responseJson(await route.POST(makeJsonRequest({
      investor_currency: "USD",
      holdings: [
        { type: "instrument", ticker: "SPY", weight: 80 },
        { type: "cash", currency: "USD", weight: 20 }
      ],
      client_fit: clientFit
    }, "http://localhost/api/portfolio/diagnose")));

    assert.equal(result.status, 200);
    const body = JSON.parse(calls[0].options.body);
    assert.deepEqual(body.client_fit, clientFit);
    assert.equal(body.options.mode, "diagnosis_only");
    assert.match(calls[0].url, /\/api\/v1\/reviews\/staged$/);
  });
});

test("diagnosis route reports frontend backend version mismatch when staged FastAPI route is missing", async () => {
  const route = loadRoute({ routePath: diagnoseRoutePath });

  await withMockFetch(async () => Response.json({
    detail: "Method Not Allowed"
  }, { status: 405 }), async () => {
    const result = await responseJson(await route.POST(makeJsonRequest({
      investor_currency: "USD",
      holdings: [
        { type: "instrument", ticker: "SPY", weight: 80 },
        { type: "cash", currency: "USD", weight: 20 }
      ]
    }, "http://localhost/api/portfolio/diagnose")));

    assert.equal(result.status, 502);
    assert.equal(result.body.status, "failed");
    assert.match(result.body.error, /Frontend\/backend version mismatch/);
    assert.match(result.body.error, /POST \/api\/v1\/reviews\/staged/);
    assert.match(result.body.error, /Restart the FastAPI backend and Next\.js frontend/);
  });
});

test("staged review status route proxies to the FastAPI status endpoint", async () => {
  const calls = [];
  const route = loadRoute({ routePath: reviewStatusRoutePath });

  await withMockFetch(async (url, options) => {
    calls.push({ url, options });
    return Response.json({
      api_version: "v1",
      schema_version: "review_state_v1",
      review_id: "frontend_review_status",
      stage: "diagnosis",
      status: "partial",
      current_stage: "candidate",
      mode: "live",
      stages: {
        input: { status: "completed", started_at: "2026-06-14T00:00:00Z", completed_at: "2026-06-14T00:00:01Z", artifact_refs: ["payload.json"] },
        xray: { status: "completed", started_at: null, completed_at: null, artifact_refs: ["analysis_subject/portfolio_xray.json"] }
      },
      artifacts: { portfolio_xray: "analysis_subject/portfolio_xray.json" },
      provider_status: { source: "live_provider", freshness: "current", message: "Live mode uses the normal market-data provider path." },
      warnings: [],
      safe_error: null,
      created_at: "2026-06-14T00:00:00Z",
      updated_at: "2026-06-14T00:00:02Z"
    });
  }, async () => {
    const result = await responseJson(await route.GET(new Request("http://localhost/api/portfolio/review/status?reviewId=frontend_review_status")));

    assert.equal(result.status, 200);
    assert.equal(result.body.schema_version, "review_state_v1");
    assert.equal(result.body.review_id, "frontend_review_status");
    assert.equal(calls.length, 1);
    assert.match(calls[0].url, /\/api\/v1\/reviews\/frontend_review_status\/status$/);
    assert.equal(calls[0].options.method, "GET");
    assertSignedFastApiHeaders(calls[0].options);
  });
});

test("portfolio API routes reject browser review calls without Supabase auth or explicit local dev bypass", async () => {
  const route = loadRoute({ routePath: reviewStatusRoutePath });
  const originalPortfolioAuthMode = process.env.PMRI_PORTFOLIO_API_AUTH_MODE;
  const originalSupabaseEnabled = process.env.NEXT_PUBLIC_PMRI_SUPABASE_ENABLED;
  const originalInternalSecret = process.env.PMRI_FASTAPI_INTERNAL_SECRET;
  delete process.env.PMRI_PORTFOLIO_API_AUTH_MODE;
  delete process.env.NEXT_PUBLIC_PMRI_SUPABASE_ENABLED;
  process.env.PMRI_FASTAPI_INTERNAL_SECRET = "frontend-route-test-secret";

  try {
    await withMockFetch(async () => {
      throw new Error("fetch was not expected before authentication succeeds");
    }, async () => {
      delete process.env.PMRI_PORTFOLIO_API_AUTH_MODE;
      const result = await responseJson(await route.GET(new Request("http://localhost/api/portfolio/review/status?reviewId=frontend_review_status")));

      assert.equal(result.status, 401);
      assert.equal(result.body.status, "failed");
      assert.match(result.body.error, /Portfolio API authentication is required/);
    });
  } finally {
    if (originalPortfolioAuthMode === undefined) delete process.env.PMRI_PORTFOLIO_API_AUTH_MODE;
    else process.env.PMRI_PORTFOLIO_API_AUTH_MODE = originalPortfolioAuthMode;
    if (originalSupabaseEnabled === undefined) delete process.env.NEXT_PUBLIC_PMRI_SUPABASE_ENABLED;
    else process.env.NEXT_PUBLIC_PMRI_SUPABASE_ENABLED = originalSupabaseEnabled;
    if (originalInternalSecret === undefined) delete process.env.PMRI_FASTAPI_INTERNAL_SECRET;
    else process.env.PMRI_FASTAPI_INTERNAL_SECRET = originalInternalSecret;
  }
});

test("Portfolio Input resumes in-flight staged reviews after browser refresh", () => {
  const source = fs.readFileSync(portfolioInputTablePath, "utf8");

  assert.match(source, /stagedResumeRef/);
  assert.match(source, /pollStagedDiagnosis\(reviewId\)/);
  assert.match(source, /recoverCompletedDiagnosis\(\s*reviewId,/);
  assert.match(source, /safe to refresh/);
  assert.match(source, /Data freshness:/);
  assert.match(source, /stagedStatusLabel/);
  assert.doesNotMatch(source, /Staged diagnosis running/);
  assert.doesNotMatch(source, /Demo \/ QA/);
});

test("Portfolio Input does not keep showing diagnosis loading after the diagnosis chain is ready", () => {
  const source = fs.readFileSync(portfolioInputTablePath, "utf8");

  assert.match(source, /diagnosisStageChainReady\(stagedProgress\)/);
  assert.match(source, /isRunningDiagnosis\s*&&\s*!diagnosisChainIsReady/);
  assert.doesNotMatch(source, /\|\|\s*stagedProgress\.status\s*===\s*"partial"\s*\)\s*\)\s*;/);
});

test("active review state advances downstream staged progress after explicit stage actions", () => {
  const source = fs.readFileSync(reviewStatePath, "utf8");

  assert.match(source, /function advanceStagedProgress/);
  assert.match(source, /advanceStagedProgress\(current\.stagedProgress, "candidate", "comparison"\)/);
  assert.match(source, /advanceStagedProgress\(current\.stagedProgress, "comparison", "verdict"\)/);
  assert.match(source, /advanceStagedProgress\(current\.stagedProgress, "verdict", "report"\)/);
  assert.match(source, /advanceStagedProgress\(current\.stagedProgress, "report", "report", "completed"\)/);
  assert.match(source, /candidateReady: current\.candidateReady \|\| isStagedStageReady\(progress, "candidate"\)/);
  assert.match(source, /comparisonReady: current\.comparisonReady \|\| isStagedStageReady\(progress, "comparison"\)/);
  assert.match(source, /verdictReady: current\.verdictReady \|\| isStagedStageReady\(progress, "verdict"\)/);
});

test("active review state exposes a shared diagnosis chain helper and can downgrade stale live lineage", () => {
  const source = fs.readFileSync(reviewStatePath, "utf8");

  assert.match(source, /export function diagnosisStageChainReady/);
  assert.match(source, /stageReady\("xray"\)/);
  assert.match(source, /stageReady\("stress"\)/);
  assert.match(source, /stageReady\("problem_classification"\)/);
  assert.match(source, /stageReady\("launchpad_builder"\)/);
  assert.match(source, /markLiveLineageUnavailable/);
  assert.match(source, /readOnlyHistory:\s*true/);
  assert.match(source, /lineageAvailable:\s*false/);
});

test("Supabase staged persistence keeps canonical stage names and strips raw artifact references", () => {
  const persistenceSource = fs.readFileSync(supabasePersistencePath, "utf8");
  const schemaSource = fs.readFileSync(supabaseSchemaPath, "utf8");
  const callbackSource = fs.readFileSync(supabaseAuthCallbackPath, "utf8");
  const sidebarSource = fs.readFileSync(sidebarPath, "utf8");

  for (const stage of ["input", "data_load", "xray", "stress", "client_fit", "problem_classification", "launchpad_builder"]) {
    assert.match(schemaSource, new RegExp(`'${stage}'`), `schema should allow staged progress row ${stage}`);
    assert.match(persistenceSource, new RegExp(`"${stage}"`), `frontend persistence should know staged progress row ${stage}`);
  }

  assert.match(persistenceSource, /function compactCloudValue/);
  assert.match(persistenceSource, /isCloudForbiddenKey/);
  assert.match(persistenceSource, /isUnsafeCloudString/);
  assert.match(persistenceSource, /persistStagedProgressForReview/);
  assert.match(persistenceSource, /compactCloudRecord\(summary\)/);
  assert.match(persistenceSource, /WorkspaceStateRecord/);
  assert.match(persistenceSource, /ensurePortfolioVersionForUser/);
  assert.match(persistenceSource, /upsertDraftReviewForPortfolioVersion/);
  assert.match(persistenceSource, /Diagnosis is not run automatically/);
  assert.match(persistenceSource, /portfolio_version_id/);
  assert.match(persistenceSource, /workspace_state/);
  assert.match(persistenceSource, /readOnlyHistory/);
  assert.match(persistenceSource, /lineageAvailable/);
  assert.match(persistenceSource, /archived_at/);
  assert.match(persistenceSource, /\.update\(\{ archived_at: nowIso\(\) \}\)/);
  assert.match(fs.readFileSync(reviewStatePath, "utf8"), /lastHydratedWorkspaceKeyRef/);
  assert.match(fs.readFileSync(reviewStatePath, "utf8"), /lastEnsuredDraftVersionKeyRef/);
  assert.match(fs.readFileSync(reviewStatePath, "utf8"), /readOnlyHistory:\s*true/);
  assert.match(fs.readFileSync(reviewStatePath, "utf8"), /lineageAvailable:\s*false/);
  assert.match(fs.readFileSync(reviewStatePath, "utf8"), /portfolioVersionId: savedReview\.portfolioVersionId/);
  assert.match(callbackSource, /url\.pathname = "\/onboarding\/sign-in"/);
  assert.doesNotMatch(persistenceSource, /artifactRefs:\s*reviewSummary\.rawOutputKeys/);
  assert.doesNotMatch(persistenceSource, /summary:\s*activeReview\.verdictResult/);
});

test("Supabase compact reviews do not claim live run-local lineage without a backend probe", () => {
  const persistenceSource = fs.readFileSync(supabasePersistencePath, "utf8");
  const reviewStateSource = fs.readFileSync(reviewStatePath, "utf8");

  assert.match(persistenceSource, /const lineageAvailable = false/);
  assert.match(reviewStateSource, /readOnlyHistory:\s*true/);
  assert.match(reviewStateSource, /lineageAvailable:\s*false/);
});

test("journey route order requires Client Fit before Hypothesis", () => {
  const journey = loadTsModule(journeyPath);
  assert.deepEqual(journey.journeySteps.map((step) => step.href), [
    "/portfolio-input",
    "/diagnosis",
    "/evidence",
    "/client-fit",
    "/hypothesis",
    "/comparison",
    "/verdict",
    "/report"
  ]);
  assert.equal(journey.isStepUnlocked("portfolio-input", journey.emptyJourneyFlags), true);
  assert.equal(journey.isStepUnlocked("hypothesis", {
    ...journey.emptyJourneyFlags,
    clientProfileCompleted: true,
    inputCompleted: true,
    diagnosisGenerated: true,
    evidenceGenerated: true,
    improvementPathsAvailable: true,
    clientFitReady: false
  }), false);
  assert.equal(journey.isStepUnlocked("hypothesis", {
    ...journey.emptyJourneyFlags,
    clientProfileCompleted: true,
    inputCompleted: true,
    diagnosisGenerated: true,
    evidenceGenerated: true,
    improvementPathsAvailable: true,
    clientFitReady: true
  }), true);
});

test("Hypothesis, Comparison, and Verdict keep Client Fit separate from structural diagnosis", () => {
  const clientFitCard = fs.readFileSync(clientFitContextCardPath, "utf8");
  const hypothesisPage = fs.readFileSync(hypothesisPagePath, "utf8");
  const comparisonPage = fs.readFileSync(comparisonPagePath, "utf8");
  const verdictPage = fs.readFileSync(verdictPagePath, "utf8");
  const combined = [clientFitCard, hypothesisPage, comparisonPage, verdictPage].join("\n");

  assert.match(hypothesisPage, /ClientFitContextCard/);
  assert.match(comparisonPage, /ClientFitContextCard/);
  assert.match(verdictPage, /ClientFitContextCard/);
  assert.match(combined, /Client Fit pass does not clear concentration, stress, drawdown, or other structural issues/);
  assert.match(combined, /Separate from diagnosis/);
  assert.match(combined, /does not clear a material issue|does not clear concentration|does not clear.*structural/i);

  const forbiddenAdvice = /\b(suitable|approved|buy|must rebalance|best portfolio)\b/i;
  assert.doesNotMatch(combined, forbiddenAdvice);
  assert.doesNotMatch(combined, /\bsell\b/i);
});

function mockHypothesisReview(cards, extra = {}) {
  return {
    investorCurrency: "USD",
    holdings: [],
    lineageAvailable: extra.lineageAvailable ?? true,
    readOnlyHistory: extra.readOnlyHistory ?? false,
    reviewId: "frontend_review_adapter",
    runMode: "real_run",
    runStatus: "completed",
    submitted: true,
    diagnosisReady: true,
    evidenceReady: true,
    improvementPathsReady: true,
    candidateReady: false,
    comparisonReady: false,
    verdictReady: false,
    updatedAt: "2026-06-15T00:00:00.000Z",
    reviewSummary: {
      version: 1,
      source: "real_run",
      status: "completed",
      reviewId: "frontend_review_adapter",
      generatedAt: "2026-06-15T00:00:00.000Z",
      investorCurrency: "USD",
      holdingsCount: 3,
      totalWeight: 100,
      cashWeight: 0,
      rawOutputKeys: [],
      outputPaths: {},
      diagnosis: {
        status: "Diagnosis ready",
        headline: "Weak crisis resilience is the primary diagnosis.",
        evidenceQuality: "Moderate evidence",
        nextStep: "Improve Crisis Resilience",
        boundaryNote: "Diagnostic only.",
        drivers: [],
        metrics: [],
        sourceArtifacts: [],
        rejectedAlternatives: [],
        rationaleRefs: []
      },
      primaryProblem: "Weak crisis resilience",
      problemSeverity: "High",
      problemConfidence: "High",
      suggestedActionPaths: ["Improve Crisis Resilience"],
      launchpadCardsCount: cards.length,
      launchpadCards: cards,
      recommendedFirstTest: "Improve Crisis Resilience",
      candidateLaunchpadAvailable: true,
      problemClassificationAvailable: true,
      clientFit: extra.clientFit,
      storage: {
        summaryBytes: 0,
        rawBytes: 0,
        rawPersisted: false,
        rawAccessStrategy: "test"
      }
    },
    ...extra
  };
}

test("Hypothesis screen model selects primary Launchpad card without text-guessing", () => {
  const { buildHypothesisScreenModel } = loadTsModule(hypothesisScreenModelPath);
  const cards = [
    {
      card_id: "launchpad_01_improve_crisis_resilience",
      title: "Improve Crisis Resilience",
      goal: "Improve crisis resilience",
      hypothesis_to_test: "Test whether crisis resilience improves.",
      card_type: "targeted_hypothesis_test",
      source_problem_label: "Weak crisis resilience",
      suggested_methods: [{ candidate_method_id: "minimum_cvar", method_role: "targeted_hypothesis" }],
      default_method: "minimum_cvar",
      success_criteria: ["Lower worst stress loss."],
      tradeoff_to_watch: "Lower tail loss vs lower expected return.",
      decision_boundary: "This is not a rebalance recommendation.",
      is_rebalance_recommendation: false,
      generates_portfolio: false
    },
    {
      card_id: "launchpad_02_reduce_credit_liquidity_risk",
      title: "Reduce Credit / Liquidity Risk",
      goal: "Reduce credit / liquidity risk",
      hypothesis_to_test: "Test whether credit risk improves.",
      card_type: "targeted_hypothesis_test",
      source_problem_label: "Credit / liquidity fragility",
      suggested_methods: [{ candidate_method_id: "minimum_variance", method_role: "targeted_hypothesis" }],
      default_method: "minimum_variance",
      success_criteria: ["Lower credit shock loss."],
      decision_boundary: "This is not a rebalance recommendation.",
      is_rebalance_recommendation: false,
      generates_portfolio: false
    }
  ];

  const model = buildHypothesisScreenModel({ activeReview: mockHypothesisReview(cards) });

  assert.equal(model.primaryTest.title, "Improve Crisis Resilience");
  assert.equal(model.primaryTest.selectedMethodLabel, "Minimum CVaR");
  assert.equal(model.defaultSelectedCardId, "launchpad_01_improve_crisis_resilience");
  assert.equal(model.alternativeTests.length, 1);
});

test("Hypothesis screen model blocks data-quality paths and keeps Client Fit contextual", () => {
  const { buildHypothesisScreenModel, sanitizeHypothesisError } = loadTsModule(hypothesisScreenModelPath);
  const cards = [{
    card_id: "launchpad_01_evidence_insufficient_do_not_act_yet",
    title: "Review Data Quality",
    goal: "Do not act yet",
    hypothesis_to_test: "Resolve data quality before testing candidates.",
    card_type: "monitor_or_data_step",
    source_problem_label: "Evidence quality requires review",
    suggested_methods: [],
    default_method: undefined,
    success_criteria: ["Resolve data-quality blockers."],
    decision_boundary: "This is not a rebalance recommendation.",
    is_rebalance_recommendation: false,
    generates_portfolio: false
  }];
  const clientFit = {
    status_label: "Outside stated Client Fit limits",
    status_tone: "red",
    main_explanation: "Return target gap is outside the stated range.",
    decision_boundary: "Client Fit is non-binding context."
  };

  const model = buildHypothesisScreenModel({ activeReview: mockHypothesisReview(cards, { clientFit }) });
  const sanitized = sanitizeHypothesisError("FastAPI backend is unavailable. Start it with uvicorn src.api.app:app --host 127.0.0.1 --port 8000.");

  assert.equal(model.primaryTest.canGenerate, false);
  assert.equal(model.action.state, "blocked");
  assert.equal(model.clientFitContext.statusLabel, "Outside stated Client Fit limits");
  assert.match(model.clientFitContext.boundary, /Client Fit/i);
  assert.match(sanitized.userError, /Supporting data service is unavailable/);
  assert.doesNotMatch(sanitized.userError, /uvicorn|127\.0\.0\.1|FastAPI/);
  assert.match(sanitized.developerError, /uvicorn/);
});

test("site explanation presenter strips raw provenance from the public display model", () => {
  const presenter = loadTsModule(siteExplanationPresenterPath);
  const rawBundle = {
    schema_version: "site_explanation_bundle_v1",
    screens: {
      diagnosis: {
        executive: [{
          id: "diagnosis.executive.primary",
          level: "executive",
          text: "The current diagnosis is supported by available evidence.",
          tone: "neutral",
          evidence_status: "available",
          claim_type: "material_claim",
          source_refs: [{ artifact: "problem_classification.json", field_path: "root_cause.statement" }]
        }],
        evidence: [{
          id: "diagnosis.evidence.primary",
          level: "evidence",
          text: "Material contradictions were detected across the diagnostic evidence.",
          tone: "caution",
          evidence_status: "limited",
          claim_type: "material_claim",
          source_refs: [{ artifact: "portfolio_xray.json", field_path: "block_2_6_portfolio_weakness_map.risk_types" }]
        }],
        technical: [{
          id: "diagnosis.technical.primary",
          level: "technical",
          text: "Some method detail is available for review.",
          tone: "neutral",
          evidence_status: "preliminary",
          claim_type: "boundary_note",
          source_refs: [{ artifact: "stress_report.json", field_path: "stress_results_v1.worst_synthetic" }]
        }]
      }
    }
  };

  const display = presenter.buildPublicSiteExplanationDisplayModel(rawBundle, "diagnosis", "Diagnosis explanation");
  assert.ok(display);
  assert.equal(display.title, "Diagnosis explanation");
  assert.equal(display.executiveItems[0].evidenceLabel, "Evidence available");
  assert.equal(display.evidenceItems[0].evidenceLabel, "Limited evidence");
  assert.equal(display.technicalItems[0].evidenceLabel, "Preliminary evidence");

  const serializedDisplay = JSON.stringify(display);
  assert.doesNotMatch(serializedDisplay, /site_explanation_bundle_v1/);
  assert.doesNotMatch(serializedDisplay, /portfolio_xray\.json/);
  assert.doesNotMatch(serializedDisplay, /problem_classification\.json/);
  assert.doesNotMatch(serializedDisplay, /stress_report\.json/);
  assert.doesNotMatch(serializedDisplay, /field_path|source_refs|artifact/);
  assert.doesNotMatch(serializedDisplay, /"available"|"limited"|"missing"|"preliminary"/);
});

test("Client Fit presentation maps technical API labels into concise user-facing copy", () => {
  const presenter = loadTsModule(clientFitPresentationPath);
  const display = presenter.buildClientFitPresentation({
    status_label: "Outside stated Client Fit limits",
    status_tone: "red",
    profile_label: "ultra_conservative",
    source_quality_label: "high",
    main_explanation: "Client Fit status is breach.",
    decision_boundary: "Client Fit is non-binding decision support.",
    next_best_test: "Review the hypothesis page.",
    target_rows: [
      {
        dimension_label: "Return target",
        portfolio_value_label: "7.8%",
        target_or_limit_label: "2.0% to 4.0%",
        status_label: "Client Fit watch",
        status_tone: "amber",
        explanation: "Return target gap is outside the stated range but not a risk-limit breach."
      },
      {
        dimension_label: "Worst stress loss limit",
        portfolio_value_label: "-26.1%",
        target_or_limit_label: "Limit: -10.0%",
        status_label: "Outside stated Client Fit limits",
        status_tone: "red",
        explanation: "Worst stress loss is worse than the stated drawdown limit."
      },
      {
        dimension_label: "Volatility comfort range",
        portfolio_value_label: "10.8%",
        target_or_limit_label: "2.0% to 5.0%",
        status_label: "Outside stated Client Fit limits",
        status_tone: "red",
        explanation: "Volatility is above the stated comfort range."
      }
    ]
  }, {
    schema_version: "site_explanation_bundle_v1",
    screens: {
      client_fit: {
        executive: [{
          id: "client_fit.executive.status_boundary",
          level: "executive",
          text: "Client Fit status is breach; diagnostic quality status is material issue.",
          tone: "risk",
          evidence_status: "available",
          claim_type: "material_claim",
          source_refs: [{ artifact: "client_fit_check.json", field_path: "client_fit_status" }]
        }],
        evidence: [{
          id: "client_fit.evidence.primary",
          level: "evidence",
          text: "Worst stress loss vs limit: portfolio evidence is breach.",
          tone: "risk",
          evidence_status: "available",
          claim_type: "material_claim",
          source_refs: [{ artifact: "client_fit_check.json", field_path: "checks[0]" }]
        }],
        technical: []
      }
    }
  });

  assert.equal(display.statusLabel, "Outside your profile");
  assert.equal(display.profileLabel, "Very cautious");
  assert.equal(display.primaryReasons[0].label, "Stress loss");
  assert.equal(display.primaryReasons[0].status, "Outside");

  const serialized = JSON.stringify(display);
  assert.doesNotMatch(serialized, /ultra_conservative/);
  assert.doesNotMatch(serialized, /Evidence available/);
  assert.doesNotMatch(serialized, /client_fit_check\.json/);
});

test("site explanation presenter exposes raw provenance only when explicitly requested", () => {
  const presenter = loadTsModule(siteExplanationPresenterPath);
  const rawBundle = {
    schema_version: "site_explanation_bundle_v1",
    review_id: "frontend_review_debug",
    warnings: ["missing_source:stress_report"],
    screens: {
      diagnosis: {
        executive: [{
          id: "diagnosis.executive.primary",
          level: "executive",
          text: "The current diagnosis is supported by available evidence.",
          tone: "neutral",
          evidence_status: "available",
          claim_type: "material_claim",
          source_refs: [{ artifact: "problem_classification.json", field_path: "root_cause.statement" }]
        }],
        evidence: [],
        technical: []
      }
    }
  };

  const defaultDisplay = presenter.buildPublicSiteExplanationDisplayModel(rawBundle, "diagnosis", "Diagnosis explanation");
  assert.ok(defaultDisplay);
  assert.equal(defaultDisplay.developerProvenance, undefined);
  assert.doesNotMatch(JSON.stringify(defaultDisplay), /problem_classification\.json|site_explanation_bundle_v1|sourceRefs/);

  const developerDisplay = presenter.buildPublicSiteExplanationDisplayModel(rawBundle, "diagnosis", "Diagnosis explanation", {
    includeDeveloperProvenance: true
  });
  assert.ok(developerDisplay.developerProvenance);
  assert.equal(developerDisplay.developerProvenance.schemaVersion, "site_explanation_bundle_v1");
  assert.equal(developerDisplay.developerProvenance.reviewId, "frontend_review_debug");
  assert.deepEqual(developerDisplay.developerProvenance.warnings, ["missing_source:stress_report"]);
  assert.deepEqual(developerDisplay.developerProvenance.items[0].sourceRefs, [
    "problem_classification.json:root_cause.statement"
  ]);
});

test("diagnosis display model keeps the public Diagnosis screen compact", () => {
  const diagnosisDisplay = loadTsModule(diagnosisDisplayModelPath);
  const model = diagnosisDisplay.buildDiagnosisDisplayModel({
    headline: "Fallback diagnosis headline.",
    evidenceQuality: "Strong evidence",
    nextStep: "Review supporting evidence before testing one candidate hypothesis.",
    boundaryNote: "Diagnosis is decision-support evidence only.",
    drivers: [
      "Driver one should be visible.",
      "Driver two should be trimmed by stronger facts.",
      "Driver three should be trimmed by stronger facts."
    ],
    metrics: [],
    xraySummary: {
      snapshotCards: [
        { label: "Top 3 concentration", value: "60.00%", detail: "Capital in largest three holdings", tone: "amber" },
        { label: "Dominant exposure", value: "Equity", detail: "60.00%", tone: "amber" },
        { label: "Max drawdown", value: "-20.20%", detail: "Recovered within sample", tone: "red" },
        { label: "Worst pre-stress weakness", value: "Equity sell-off risk", detail: "Score 55/100", tone: "amber" }
      ],
      riskProfile: {
        insight: "Risk profile evidence is available.",
        metrics: [
          { label: "CAGR", value: "7.80%", detail: "Primary diagnostic window", tone: "blue" },
          { label: "Max drawdown", value: "-20.20%", detail: "Recovered within sample", tone: "red" },
          { label: "Time to recovery", value: "11.00 months", detail: "Recovered within sample", tone: "slate" },
          { label: "Beta", value: "0.61", detail: "SPY", tone: "blue" },
          { label: "VaR 95", value: "-1.00%", detail: "Daily historical tail metric", tone: "blue" },
          { label: "Sharpe", value: "0.54", detail: "Total-volatility efficiency", tone: "blue" },
          { label: "Treynor", value: "n/a", detail: "Unavailable", tone: "slate" }
        ],
        keyFacts: []
      },
      unavailableNotes: ["Rolling chart not shown.", "Factor names normalized for product contract."]
    },
    siteExplanation: {
      schema_version: "site_explanation_bundle_v1",
      warnings: ["missing_source:stress_report"],
      screens: {
        diagnosis: {
          executive: [{ id: "e", level: "executive", text: "Executive explanation.", tone: "neutral", evidence_status: "available", claim_type: "material_claim", source_refs: [] }],
          evidence: [{ id: "v", level: "evidence", text: "Evidence explanation.", tone: "neutral", evidence_status: "available", claim_type: "material_claim", source_refs: [] }],
          technical: [{ id: "t", level: "technical", text: "Technical explanation.", tone: "neutral", evidence_status: "preliminary", claim_type: "boundary_note", source_refs: [] }]
        }
      }
    }
  });

  assert.equal(model.primaryEvidence.length, 3);
  assert.equal(model.whatMatters.length, 4);
  assert.equal(model.behaviorSnapshot.length, 3);
  assert.match(model.mainFinding, /equity-led/i);
  assert.match(JSON.stringify(model.primaryEvidence), /60%/);
  assert.doesNotMatch(JSON.stringify(model.primaryEvidence), /60\.00%|7\.80%|11\.00 months/);
  assert.ok(model.advancedMetrics.some((metric) => metric.label === "VaR 95"));
  assert.ok(model.advancedMetrics.some((metric) => metric.label === "Sharpe"));
  assert.ok(!model.advancedMetrics.some((metric) => metric.label === "Treynor"));
  assert.deepEqual(model.limitations, ["Missing source:stress evidence"]);
});

test("Diagnosis page uses the compact display model instead of the standalone explanation wall", () => {
  const diagnosisPage = fs.readFileSync(diagnosisPagePath, "utf8");
  const diagnosisPanel = fs.readFileSync(diagnosisSummaryPanelPath, "utf8");

  assert.doesNotMatch(diagnosisPage, /SiteExplanationHierarchy/);
  assert.match(diagnosisPage, /siteExplanation/);
  assert.match(diagnosisPanel, /buildDiagnosisDisplayModel/);
  assert.match(diagnosisPanel, /Advanced diagnostics and technical evidence/);
  assert.match(diagnosisPanel, /How the current portfolio behaved historically/);
  assert.doesNotMatch(diagnosisPanel, /Evidence available/);
  assert.doesNotMatch(diagnosisPanel, /Rolling charts are not shown/);
});

test("stress story presenter keeps the primary Stress Lab surface compact", () => {
  const storyModel = loadTsModule(stressStoryModelPath);
  const sample = readJsonFixture(path.resolve(frontendRoot, "data", "demo", "stress-lab.json"));
  const story = storyModel.buildStressStoryViewModel(sample);
  const limits = storyModel.assertPublicStressStoryLimits(story);

  assert.equal(story.state, "material_vulnerability");
  assert.equal(limits.hasSingleAnswer, true);
  assert.equal(limits.factCountOk, true);
  assert.equal(limits.metricCountOk, true);
  assert.equal(limits.noRawTerms, true);
  assert.ok(story.facts.length <= 3);
  assert.ok(story.metrics.length <= 4);
  assert.match(story.answer, /current portfolio/i);
  assert.doesNotMatch(JSON.stringify(story), /Evidence available|stress_report\.json|field_path|must rebalance|trade now/i);
});

test("stress story presenter handles limited and acceptable stress states", () => {
  const storyModel = loadTsModule(stressStoryModelPath);
  const sample = readJsonFixture(path.resolve(frontendRoot, "data", "demo", "stress-lab.json"));
  const limited = JSON.parse(JSON.stringify(sample));
  limited.syntheticScenarios = limited.syntheticScenarios.map((scenario) => ({
    ...scenario,
    availability: "unavailable",
    portfolioLossPct: null
  }));
  limited.historicalScenarios = limited.historicalScenarios.map((scenario) => ({
    ...scenario,
    availability: "unavailable",
    drawdownPct: null,
    portfolioLossPct: null
  }));
  limited.limitations.evidenceQualityLabel = "Insufficient data";
  limited.limitations.evidenceTone = "slate";

  const limitedStory = storyModel.buildStressStoryViewModel(limited);
  assert.equal(limitedStory.state, "evidence_limited");
  assert.equal(storyModel.assertPublicStressStoryLimits(limitedStory).noRawTerms, true);

  const acceptable = JSON.parse(JSON.stringify(sample));
  acceptable.syntheticScenarios = acceptable.syntheticScenarios.map((scenario, index) => ({
    ...scenario,
    portfolioLossPct: index === 0 ? -0.025 : -0.01,
    severityTone: "slate",
    severityLabel: "Less damaging",
    isWorst: index === 0
  }));
  acceptable.hedgeGap.offsetCoverageRatio = 0.45;
  acceptable.hedgeGap.statusLabel = "Partial offset";
  acceptable.hedgeGap.statusTone = "amber";
  acceptable.limitations.evidenceQualityLabel = "Strong evidence";
  acceptable.limitations.evidenceTone = "green";

  const acceptableStory = storyModel.buildStressStoryViewModel(acceptable);
  assert.equal(acceptableStory.state, "stress_acceptable");
  assert.ok(acceptableStory.facts.length <= 3);
  assert.ok(acceptableStory.metrics.length <= 4);
});

test("SiteExplanationHierarchy renders public explanation data instead of raw provenance", () => {
  const source = fs.readFileSync(siteExplanationHierarchyPath, "utf8");

  assert.match(source, /buildPublicSiteExplanationDisplayModel/);
  assert.match(source, /Decision evidence/);
  assert.match(source, /showDeveloperProvenance = false/);
  assert.match(source, /Developer provenance/);
  assert.doesNotMatch(source, /Source:/);
  assert.doesNotMatch(source, /site_explanation_bundle_v1/);
  assert.doesNotMatch(source, /ref\.artifact|ref\.field_path/);
  assert.doesNotMatch(source, /source_refs\.map/);
});

test("public journey pages do not opt into developer provenance by default", () => {
  const publicPagePaths = [
    path.resolve(frontendRoot, "app", "diagnosis", "page.tsx"),
    path.resolve(frontendRoot, "app", "evidence", "page.tsx"),
    path.resolve(frontendRoot, "app", "client-fit", "page.tsx"),
    path.resolve(frontendRoot, "app", "hypothesis", "page.tsx"),
    path.resolve(frontendRoot, "app", "comparison", "page.tsx"),
    path.resolve(frontendRoot, "app", "verdict", "page.tsx"),
    path.resolve(frontendRoot, "app", "report", "page.tsx")
  ];

  for (const publicPagePath of publicPagePaths) {
    const source = fs.readFileSync(publicPagePath, "utf8");
    assert.doesNotMatch(source, /showDeveloperProvenance\s*=\s*{?\s*true\s*}?/, `${publicPagePath} must not expose developer provenance`);
  }
});

test("review recovery route validates review id and path separators", async () => {
  const route = loadRoute({ routePath: reviewRecoverRoutePath });

  await withMockFetch(async () => {
    throw new Error("fetch was not expected");
  }, async () => {
    const result = await responseJson(await route.GET(new Request("http://localhost/api/portfolio/review/recover?review_id=../bad")));

    assert.equal(result.status, 400);
    assert.equal(result.body.status, "failed");
    assert.equal(result.body.error, "Review recovery request validation failed.");
    assert.deepEqual(result.body.details, [
      "review_id must be a frontend_review_* id.",
      "review_id must not contain path separators."
    ]);
  });
});

test("review recovery route uses FastAPI readiness and returns only safe run-local diagnosis artifacts", async () => {
  const route = loadRoute({ routePath: reviewRecoverRoutePath });

  await withMockFetch(async (url, options) => {
    assert.match(url, /\/api\/v1\/reviews\/frontend_review_recover_ok$/);
    assert.equal(options.method, "GET");
    return Response.json(fastApiEnvelope({
      review_id: "frontend_review_recover_ok",
      stage: "recovery",
      lineage: { review_id: "frontend_review_recover_ok" },
      data: {
        review_summary: {
          investor_currency: "USD"
        },
        diagnosis: {
          primary_diagnosis: "Concentration",
          headline: "Concentration deserves a diagnostic test."
        },
        launchpad: [{
          card_id: "card_ok",
          title: "Equal Weight reference test",
          method_id: "equal_weight",
          generation_allowed: true,
          is_rebalance_recommendation: false
        }],
        next_allowed_actions: ["prepare_builder"],
        artifact_refs: [
          { kind: "problem_classification", ref: "runs/frontend_review_recover_ok/analysis_subject/problem_classification.json", scope: "analysis_subject", raw_path_exposed: false },
          { kind: "portfolio_alternatives_builder", ref: "runs/frontend_review_recover_ok/analysis_subject/portfolio_alternatives_builder.json", scope: "analysis_subject", raw_path_exposed: false }
        ],
        downstream_artifacts_restored_as_active: false,
        restored_active_stages: ["diagnosis", "evidence", "hypothesis_setup"]
      },
      evidence: {
        source_artifacts: [
          { kind: "problem_classification", ref: "runs/frontend_review_recover_ok/analysis_subject/problem_classification.json", scope: "analysis_subject", raw_path_exposed: false }
        ],
        data_quality: "ok",
        confidence: "medium"
      }
    }));
  }, async () => {
    const result = await responseJson(await route.POST(makeJsonRequest({ review_id: "frontend_review_recover_ok" })));

    assert.equal(result.status, 200);
    assert.equal(result.body.status, "completed");
    assert.equal(result.body.stage, "review_recovery");
    assert.equal(result.body.recovery.source, "fastapi_v1_review_recovery");
    assert.equal(result.body.recovery.downstream_artifacts_restored_as_active, false);
    assert.deepEqual(result.body.recovery.restored_active_stages, ["diagnosis", "evidence", "hypothesis_setup"]);
    assert.equal(result.body.review_result.status, "completed");
    assert.equal(result.body.review_result.outputs.portfolio_alternatives_builder.selected_card_id, "card_ok");
    assert.equal(result.body.review_result.outputs.candidate_generation, undefined);
    assert.equal(result.body.review_result.outputs.current_vs_candidate, undefined);
    assert.equal(result.body.review_result.outputs.decision_verdict, undefined);
    assert.equal(result.body.review_result.paths.current_vs_candidate, undefined);
  });
});

test("candidate route rejects FastAPI lineage from a different active review before trusting downstream artifacts", async () => {
  const route = loadRoute({ routePath: candidateGenerateRoutePath });

  await withMockFetch(async (url, options) => {
    assert.match(url, /\/api\/v1\/reviews\/frontend_review_user_a\/candidate$/);
    assert.equal(options.method, "POST");
    assert.deepEqual(JSON.parse(options.body), {
      builder_setup_id: "candidate_setup_card_equal_weight"
    });
    return Response.json(fastApiEnvelope({
      review_id: "frontend_review_user_b",
      stage: "candidate",
      lineage: {
        review_id: "frontend_review_user_b",
        selected_card_id: "card_equal_weight"
      }
    }));
  }, async () => {
    const result = await responseJson(await route.POST(makeJsonRequest({
      review_id: "frontend_review_user_a",
      selected_card_id: "card_equal_weight",
      builder_setup_id: "candidate_setup_card_equal_weight"
    }, "http://localhost/api/portfolio/candidate/generate")));

    assert.equal(result.status, 409);
    assert.equal(result.body.status, "failed");
    assert.equal(result.body.stage, "candidate_generation");
    assert.match(result.body.error, /lineage did not match/);
    assert.match(result.body.details.join(" "), /review_id mismatch/);
  });
});

test("Hypothesis probes backend review status before Builder and Candidate generation", () => {
  const source = fs.readFileSync(hypothesisPagePath, "utf8");
  const probeIndex = source.indexOf("probeLiveReviewLineage(reviewId)");
  const builderIndex = source.indexOf('fetch("/api/portfolio/builder/prepare"');
  const candidateIndex = source.indexOf('fetch("/api/portfolio/candidate/generate"');

  assert.ok(probeIndex > 0, "Hypothesis should probe live backend lineage before downstream actions.");
  assert.ok(builderIndex > probeIndex, "Builder prepare must happen after the status probe.");
  assert.ok(candidateIndex > builderIndex, "Candidate generation must happen after Builder prepare.");
  assert.match(source, /Run a new diagnosis before generating a candidate/);
  assert.match(source, /markLiveLineageUnavailable\(message\)/);
});

test("report route returns a display model from the FastAPI public envelope", async () => {
  const route = loadRoute({ routePath: reportGenerateRoutePath });

  await withMockFetch(async (url, options) => {
    assert.match(url, /\/api\/v1\/reviews\/frontend_review_report_ok\/report$/);
    assert.equal(options.method, "POST");
    assert.deepEqual(JSON.parse(options.body), {
      verdict_id: "no_material_rebalance_recommended"
    });
    return Response.json(fastApiReportEnvelope({
      review_id: "frontend_review_report_ok",
      lineage: {
        review_id: "frontend_review_report_ok",
        selected_card_id: "card_equal_weight",
        candidate_id: "equal_weight",
        verdict_id: "no_material_rebalance_recommended"
      }
    }));
  }, async () => {
    const result = await responseJson(await route.POST(makeJsonRequest({
      review_id: "frontend_review_report_ok",
      selected_card_id: "card_equal_weight",
      candidate_id: "equal_weight",
      verdict_id: "no_material_rebalance_recommended"
    }, "http://localhost/api/portfolio/report/generate")));

    assert.equal(result.status, 200);
    assert.equal(result.body.status, "completed");
    assert.equal(result.body.stage, "report_commentary");
    assert.equal(result.body.report_display_model.title, "Grounded client-ready report summary");
    assert.match(result.body.report_display_model.sections.map((section) => section.body).join(" "), /Diagnosis summary from the public API/);
    assert.deepEqual(result.body.report_display_model.evidenceUsed.slice(0, 2), [
      "Portfolio Diagnosis",
      "decision evidence"
    ]);
    assert.match(result.body.report_display_model.boundaryNote, /Decision-support only from FastAPI context/);
    assert.ok(result.body.report_display_model.evidenceUsed.includes("main diagnosis"));
    assert.ok(result.body.report_display_model.evidenceUsed.includes("comparison evidence"));
    assert.equal(result.body.fastapi_envelope.data.llm_generated, false);
  });
});
