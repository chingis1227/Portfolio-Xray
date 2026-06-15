const assert = require("node:assert/strict");
const fs = require("node:fs");
const path = require("node:path");
const test = require("node:test");
const ts = require("typescript");

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
const siteExplanationHierarchyPath = path.resolve(frontendRoot, "components", "explanation", "SiteExplanationHierarchy.tsx");
const hypothesisPagePath = path.resolve(frontendRoot, "app", "hypothesis", "page.tsx");
const comparisonPagePath = path.resolve(frontendRoot, "app", "comparison", "page.tsx");
const verdictPagePath = path.resolve(frontendRoot, "app", "verdict", "page.tsx");
const siteExplanationPresenterPath = path.resolve(frontendRoot, "lib", "siteExplanationPresenter.ts");

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

function loadRoute({ routePath = builderPrepareRoutePath, readFileImpl } = {}) {
  return loadTsModule(routePath, { readFileImpl });
}

async function responseJson(response) {
  return { status: response.status, body: await response.json() };
}

async function withMockFetch(mockFetch, callback) {
  const original = globalThis.fetch;
  globalThis.fetch = mockFetch;
  try {
    return await callback();
  } finally {
    globalThis.fetch = original;
  }
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
  });
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
  assert.match(callbackSource, /url\.pathname = "\/onboarding\/name"/);
  assert.doesNotMatch(persistenceSource, /artifactRefs:\s*reviewSummary\.rawOutputKeys/);
  assert.doesNotMatch(persistenceSource, /summary:\s*activeReview\.verdictResult/);
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
