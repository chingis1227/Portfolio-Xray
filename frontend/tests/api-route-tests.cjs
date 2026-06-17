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
const comparisonGenerateRoutePath = path.resolve(frontendRoot, "app", "api", "portfolio", "comparison", "generate", "route.ts");
const diagnoseRoutePath = path.resolve(frontendRoot, "app", "api", "portfolio", "diagnose", "route.ts");
const reportGenerateRoutePath = path.resolve(frontendRoot, "app", "api", "portfolio", "report", "generate", "route.ts");
const verdictGenerateRoutePath = path.resolve(frontendRoot, "app", "api", "portfolio", "verdict", "generate", "route.ts");
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
const candidateGenerationReadinessPath = path.resolve(frontendRoot, "lib", "review", "candidateGenerationReadiness.ts");
const journeyPath = path.resolve(frontendRoot, "lib", "journey.ts");
const clientFitContextCardPath = path.resolve(frontendRoot, "components", "client-fit", "ClientFitContextCard.tsx");
const clientFitScreenPath = path.resolve(frontendRoot, "components", "client-fit", "ClientFitScreen.tsx");
const clientFitPresentationPath = path.resolve(frontendRoot, "lib", "clientFitPresentation.ts");
const siteExplanationHierarchyPath = path.resolve(frontendRoot, "components", "explanation", "SiteExplanationHierarchy.tsx");
const diagnosisPagePath = path.resolve(frontendRoot, "app", "diagnosis", "page.tsx");
const diagnosisScreenPath = path.resolve(frontendRoot, "components", "diagnosis", "DiagnosisScreen.tsx");
const diagnosisDisplayModelPath = path.resolve(frontendRoot, "lib", "diagnosisDisplayModel.ts");
const diagnosisSummaryPanelPath = path.resolve(frontendRoot, "components", "diagnosis", "DiagnosisSummaryPanel.tsx");
const stressStoryModelPath = path.resolve(frontendRoot, "components", "evidence", "stressStoryModel.ts");
const stressLabModelPath = path.resolve(frontendRoot, "components", "evidence", "stressLabModel.ts");
const evidenceScreenPath = path.resolve(frontendRoot, "components", "evidence", "EvidenceScreen.tsx");
const stressTestLabPath = path.resolve(frontendRoot, "components", "evidence", "StressTestLab.tsx");
const hypothesisScreenPath = path.resolve(frontendRoot, "components", "hypothesis", "HypothesisScreen.tsx");
const comparisonScreenPath = path.resolve(frontendRoot, "components", "comparison", "ComparisonScreen.tsx");
const verdictScreenPath = path.resolve(frontendRoot, "components", "verdict", "VerdictScreen.tsx");
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
      jsx: ts.JsxEmit.ReactJSX,
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
      const tsPath = fs.existsSync(`${aliasedPath}.ts`) ? `${aliasedPath}.ts` : fs.existsSync(`${aliasedPath}.tsx`) ? `${aliasedPath}.tsx` : aliasedPath;
      return loadTsModule(tsPath, { readFileImpl, moduleCache });
    }
    if (specifier.startsWith(".")) {
      const relativePath = path.resolve(path.dirname(resolvedPath), specifier);
      const tsPath = fs.existsSync(`${relativePath}.ts`) ? `${relativePath}.ts` : fs.existsSync(`${relativePath}.tsx`) ? `${relativePath}.tsx` : relativePath;
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

function fastApiCandidateEnvelope(overrides = {}) {
  return fastApiEnvelope({
    schema_version: "candidate_generation_v1",
    review_id: "frontend_review_candidate",
    stage: "candidate",
    status: "ok",
    lineage: {
      review_id: "frontend_review_candidate",
      selected_card_id: "card_equal_weight",
      builder_setup_id: "builder_setup_equal_weight",
      candidate_id: "equal_weight"
    },
    data: {
      candidate: {
        candidate_id: "equal_weight",
        method_label: "Equal Weight",
        generation_status: "generated",
        weight_summary: { VOO: 0.5, BND: 0.5 }
      },
      hypothesis: {
        hypothesis: "Test whether equal weighting reduces concentration.",
        success_criteria: ["Reduce top holding concentration."],
        tradeoff_to_watch: "Return drag.",
        decision_boundary: "Decision Verdict decides; this is not a recommendation."
      },
      next_allowed_actions: ["run_comparison"]
    },
    evidence: {
      source_artifacts: [
        { kind: "candidate_generation", ref: "runs/frontend_review_candidate/candidate_generation.json", scope: "run_local", raw_path_exposed: false }
      ],
      data_quality: "ok",
      confidence: "medium"
    },
    ...overrides
  });
}

function completedClientFit(overrides = {}) {
  return {
    preset_id: "balanced",
    source: "questionnaire",
    source_quality: "medium",
    source_quality_reason: "Questionnaire confirmed.",
    horizon_years: 7,
    target_return_range: { min: 0.05, max: 0.07 },
    target_vol_range: { min: 0.07, max: 0.10 },
    target_max_drawdown_pct: -0.20,
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

test("builder prepare route rejects FastAPI selected-card lineage mismatch before trusting setup", async () => {
  const route = loadRoute();

  await withMockFetch(async () => Response.json(fastApiEnvelope({
    review_id: "frontend_review_builder_lineage",
    lineage: {
      review_id: "frontend_review_builder_lineage",
      selected_card_id: "stale_card",
      builder_setup_id: "candidate_setup_stale"
    },
    data: {
      candidate_generation_allowed: true,
      builder_setup: {
        builder_setup_id: "candidate_setup_stale",
        selected_card_id: "stale_card",
        method_id: "equal_weight"
      }
    }
  })), async () => {
    const result = await responseJson(await route.POST(makeJsonRequest({
      review_id: "frontend_review_builder_lineage",
      selected_card_id: "card_equal_weight"
    })));

    assert.equal(result.status, 409);
    assert.equal(result.body.stage, "builder_setup");
    assert.equal(result.body.review_id, "frontend_review_builder_lineage");
    assert.equal(result.body.selected_card_id, "card_equal_weight");
    assert.equal(result.body.portfolio_alternatives_builder, undefined);
    assert.equal(result.body.fastapi_envelope, undefined);
  });
});

test("builder prepare route rejects stale builder setup body even when lineage ids look valid", async () => {
  const route = loadRoute();

  await withMockFetch(async () => Response.json(fastApiEnvelope({
    review_id: "frontend_review_builder_body_lineage",
    lineage: {
      review_id: "frontend_review_builder_body_lineage",
      selected_card_id: "card_min_cvar",
      builder_setup_id: "builder_setup_active"
    },
    data: {
      candidate_generation_allowed: true,
      builder_setup: {
        builder_setup_id: "builder_setup_stale",
        selected_card_id: "stale_card",
        method_id: "equal_weight"
      }
    }
  })), async () => {
    const result = await responseJson(await route.POST(makeJsonRequest({
      review_id: "frontend_review_builder_body_lineage",
      selected_card_id: "card_min_cvar"
    })));

    assert.equal(result.status, 409);
    assert.equal(result.body.stage, "builder_setup");
    assert.deepEqual(result.body.details, [
      "data.builder_setup.selected_card_id expected card_min_cvar but received stale_card.",
      "data.builder_setup.builder_setup_id expected builder_setup_active but received builder_setup_stale."
    ]);
    assert.equal(result.body.portfolio_alternatives_builder, undefined);
  });
});

test("builder prepare public envelope keeps Client Fit context out of optimizer parameters and constraints", async () => {
  const route = loadRoute();
  const clientFitCriteria = {
    client_fit_status: "watch",
    target_rows: [{ usage: "display_test_criterion", dimension_label: "Worst stress loss limit" }]
  };

  await withMockFetch(async () => Response.json(fastApiEnvelope({
    review_id: "frontend_review_builder_client_fit",
    lineage: {
      review_id: "frontend_review_builder_client_fit",
      selected_card_id: "card_min_cvar",
      builder_setup_id: "builder_setup_min_cvar"
    },
    data: {
      candidate_generation_allowed: true,
      builder_setup: {
        builder_setup_id: "builder_setup_min_cvar",
        selected_card_id: "card_min_cvar",
        method_id: "minimum_cvar",
        generation_readiness: "ready",
        success_criteria: [
          "Lower worst stress loss.",
          "Compare worst stress loss against the stated maximum temporary loss."
        ],
        client_fit_context: { client_fit_status: "watch", profile_label: "Balanced" },
        client_fit_test_criteria: clientFitCriteria,
        client_fit_optimizer_boundary: "Client Fit criteria are display test criteria, not optimizer constraints.",
        parameters: {
          method_id: "minimum_cvar",
          client_fit_test_criteria: clientFitCriteria
        },
        constraints: {
          target_vol_range: { min: 0.07, max: 0.1 },
          client_fit_test_criteria: clientFitCriteria
        }
      }
    }
  })), async () => {
    const result = await responseJson(await route.POST(makeJsonRequest({
      review_id: "frontend_review_builder_client_fit",
      selected_card_id: "card_min_cvar"
    })));

    assert.equal(result.status, 200);
    const prefill = result.body.portfolio_alternatives_builder.builder_prefill;
    const setup = result.body.portfolio_alternatives_builder.candidate_setup;
    assert.deepEqual(prefill.client_fit_test_criteria, clientFitCriteria);
    assert.match(prefill.client_fit_optimizer_boundary, /not optimizer constraints/i);
    assert.deepEqual(setup.client_fit_test_criteria, clientFitCriteria);
    assert.match(setup.client_fit_optimizer_boundary, /not optimizer constraints/i);
    assert.equal(setup.parameters.client_fit_test_criteria, undefined);
    assert.equal(setup.parameters.target_vol_range, undefined);
    assert.equal(setup.constraints.client_fit_test_criteria, undefined);
    assert.equal(setup.constraints.target_vol_range, undefined);
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
        ],
        client_fit: completedClientFit()
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
        client_fit: completedClientFit(),
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

  const clientFit = completedClientFit();

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

test("diagnosis route maps sample mode to deterministic staged demo QA mode", async () => {
  const calls = [];
  const route = loadRoute({ routePath: diagnoseRoutePath });

  await withMockFetch(async (url, options) => {
    calls.push({ url, options });
    return Response.json({
      api_version: "v1",
      schema_version: "review_started_v1",
      review_id: "frontend_review_demo_mode",
      stage: "diagnosis",
      status: "running",
      current_stage: "input",
      mode: "demo_qa",
      warnings: [],
      safe_error: null
    });
  }, async () => {
    const result = await responseJson(await route.POST(makeJsonRequest({
      investor_currency: "USD",
      mode: "sample_demo",
      holdings: [
        { type: "instrument", ticker: "SPY", weight: 70 },
        { type: "cash", currency: "USD", weight: 30 }
      ],
      client_fit: completedClientFit()
    }, "http://localhost/api/portfolio/diagnose")));

    assert.equal(result.status, 200);
    assert.equal(result.body.review_id, "frontend_review_demo_mode");
    assert.equal(result.body.mode, "demo_qa");
    assert.equal(calls.length, 1);
    assert.deepEqual(JSON.parse(calls[0].options.body).options, {
      mode: "diagnosis_only",
      output_profile: "site_api",
      sample_mode: true
    });
  });
});

test("diagnosis route accepts EUR portfolio input and tolerance-safe weights", async () => {
  const calls = [];
  const route = loadRoute({ routePath: diagnoseRoutePath });

  await withMockFetch(async (url, options) => {
    calls.push({ url, options });
    return Response.json({
      api_version: "v1",
      schema_version: "review_started_v1",
      review_id: "frontend_review_eur",
      stage: "diagnosis",
      status: "running",
      current_stage: "input",
      mode: "live",
      warnings: [],
      safe_error: null
    });
  }, async () => {
    const result = await responseJson(await route.POST(makeJsonRequest({
      investor_currency: "EUR",
      holdings: [
        { type: "instrument", ticker: "SPY", weight: 33.33 },
        { type: "instrument", ticker: "BND", weight: 33.33 },
        { type: "cash", currency: "EUR", weight: 33.34 }
      ],
      client_fit: completedClientFit()
    }, "http://localhost/api/portfolio/diagnose")));

    assert.equal(result.status, 200);
    assert.equal(result.body.review_id, "frontend_review_eur");
    assert.equal(calls.length, 1);
    assert.deepEqual(JSON.parse(calls[0].options.body).portfolio, {
      investor_currency: "EUR",
      holdings: [
        { type: "instrument", ticker: "SPY", weight_pct: 33.33 },
        { type: "instrument", ticker: "BND", weight_pct: 33.33 },
        { type: "cash", currency: "EUR", weight_pct: 33.34 }
      ]
    });
  });
});

[
  {
    name: "lower tolerance boundary",
    reviewId: "frontend_review_weight_9999",
    holdings: [
      { type: "instrument", ticker: "SPY", weight: 70 },
      { type: "cash", currency: "USD", weight: 29.99 }
    ],
    expectedHoldings: [
      { type: "instrument", ticker: "SPY", weight_pct: 70 },
      { type: "cash", currency: "USD", weight_pct: 29.99 }
    ]
  },
  {
    name: "upper tolerance boundary",
    reviewId: "frontend_review_weight_10001",
    holdings: [
      { type: "instrument", ticker: "SPY", weight: 70 },
      { type: "cash", currency: "USD", weight: 30.01 }
    ],
    expectedHoldings: [
      { type: "instrument", ticker: "SPY", weight_pct: 70 },
      { type: "cash", currency: "USD", weight_pct: 30.01 }
    ]
  }
].forEach(({ name, reviewId, holdings, expectedHoldings }) => {
  test(`diagnosis route accepts ${name} without normalizing weights`, async () => {
    const calls = [];
    const route = loadRoute({ routePath: diagnoseRoutePath });

    await withMockFetch(async (url, options) => {
      calls.push({ url, options });
      return Response.json({
        api_version: "v1",
        schema_version: "review_started_v1",
        review_id: reviewId,
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
        holdings,
        client_fit: completedClientFit()
      }, "http://localhost/api/portfolio/diagnose")));

      assert.equal(result.status, 200);
      assert.equal(result.body.review_id, reviewId);
      assert.equal(calls.length, 1);
      assert.deepEqual(JSON.parse(calls[0].options.body).portfolio.holdings, expectedHoldings);
    });
  });
});

const validDiagnosisPayload = () => ({
  investor_currency: "USD",
  holdings: [
    { type: "instrument", ticker: "SPY", weight: 70 },
    { type: "cash", currency: "USD", weight: 30 }
  ],
  client_fit: completedClientFit()
});

[
  {
    name: "missing investor currency",
    payload: { ...validDiagnosisPayload(), investor_currency: "" },
    expectedDetails: ["investor_currency is required."]
  },
  {
    name: "unsupported investor currency",
    payload: { ...validDiagnosisPayload(), investor_currency: "GBP" },
    expectedDetails: ["investor_currency must be USD or EUR."]
  },
  {
    name: "invalid cash currency",
    payload: {
      ...validDiagnosisPayload(),
      holdings: [
        { type: "instrument", ticker: "SPY", weight: 70 },
        { type: "cash", currency: "GBP", weight: 30 }
      ]
    },
    expectedDetails: ["holding[1] cash currency must be USD or EUR."]
  },
  {
    name: "weights below tolerance",
    payload: {
      ...validDiagnosisPayload(),
      holdings: [
        { type: "instrument", ticker: "SPY", weight: 70 },
        { type: "cash", currency: "USD", weight: 29.98 }
      ]
    },
    expectedDetails: ["Total weight must equal 100 within 0.01; got 99.98."]
  },
  {
    name: "weights above tolerance",
    payload: {
      ...validDiagnosisPayload(),
      holdings: [
        { type: "instrument", ticker: "SPY", weight: 70 },
        { type: "cash", currency: "USD", weight: 30.02 }
      ]
    },
    expectedDetails: ["Total weight must equal 100 within 0.01; got 100.02."]
  },
  {
    name: "duplicate instrument tickers",
    payload: {
      ...validDiagnosisPayload(),
      holdings: [
        { type: "instrument", ticker: "SPY", weight: 50 },
        { type: "instrument", ticker: "spy", weight: 50 }
      ]
    },
    expectedDetails: ["holding[1] duplicates ticker SPY."]
  },
  {
    name: "duplicate cash currencies",
    payload: {
      ...validDiagnosisPayload(),
      holdings: [
        { type: "cash", currency: "USD", weight: 40 },
        { type: "cash", currency: "usd", weight: 60 }
      ]
    },
    expectedDetails: ["holding[1] duplicates cash currency USD."]
  },
  {
    name: "missing Client Fit",
    payload: (() => {
      const payload = validDiagnosisPayload();
      delete payload.client_fit;
      return payload;
    })(),
    expectedDetails: ["client_fit is required for web diagnosis."]
  },
  {
    name: "missing Client Fit source",
    payload: { ...validDiagnosisPayload(), client_fit: completedClientFit({ source: "missing" }) },
    expectedDetails: [
      "The web diagnosis requires a completed Client Fit profile."
    ]
  },
  {
    name: "missing Client Fit quality",
    payload: { ...validDiagnosisPayload(), client_fit: completedClientFit({ source_quality: "missing" }) },
    expectedDetails: [
      "The web diagnosis requires a completed Client Fit profile."
    ]
  }
].forEach(({ name, payload, expectedDetails }) => {
  test(`diagnosis route rejects ${name} before calling FastAPI`, async () => {
    const route = loadRoute({ routePath: diagnoseRoutePath });

    await withMockFetch(async () => {
      throw new Error("fetch was not expected");
    }, async () => {
      const result = await responseJson(await route.POST(makeJsonRequest(payload, "http://localhost/api/portfolio/diagnose")));

      assert.equal(result.status, 400);
      assert.equal(result.body.status, "failed");
      assert.equal(result.body.error, "Portfolio input validation failed.");
      for (const expectedDetail of expectedDetails) {
        assert.ok(
          result.body.details.includes(expectedDetail),
          `Expected details to include "${expectedDetail}", got ${JSON.stringify(result.body.details)}`
        );
      }
    });
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
      ],
      client_fit: completedClientFit()
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
    assert.equal(result.body.status, "partial");
    assert.equal(result.body.current_stage, "candidate");
    assert.equal(result.body.mode, "live");
    assert.equal(result.body.stages.input.status, "completed");
    assert.equal(result.body.stages.xray.artifact_refs[0], "analysis_subject/portfolio_xray.json");
    assert.equal(result.body.artifacts.portfolio_xray, "analysis_subject/portfolio_xray.json");
    assert.equal(result.body.provider_status.source, "live_provider");
    assert.equal(calls.length, 1);
    assert.match(calls[0].url, /\/api\/v1\/reviews\/frontend_review_status\/status$/);
    assert.equal(calls[0].options.method, "GET");
    assertSignedFastApiHeaders(calls[0].options);
  });
});

test("staged review status route rejects FastAPI status from a different review", async () => {
  const route = loadRoute({ routePath: reviewStatusRoutePath });

  await withMockFetch(async (url, options) => {
    assert.match(url, /\/api\/v1\/reviews\/frontend_review_status_a\/status$/);
    assert.equal(options.method, "GET");
    return Response.json({
      api_version: "v1",
      schema_version: "review_state_v1",
      review_id: "frontend_review_status_b",
      stage: "diagnosis",
      status: "running",
      current_stage: "data_load",
      mode: "live",
      stages: {},
      artifacts: {},
      provider_status: { source: "live_provider", freshness: "pending", message: "Live mode uses the normal market-data provider path." },
      warnings: [],
      safe_error: null,
      created_at: null,
      updated_at: null
    });
  }, async () => {
    const result = await responseJson(await route.GET(new Request("http://localhost/api/portfolio/review/status?reviewId=frontend_review_status_a")));

    assert.equal(result.status, 409);
    assert.equal(result.body.status, "failed");
    assert.equal(result.body.stage, "staged_review_status");
    assert.match(result.body.error, /lineage did not match/);
    assert.match(result.body.details.join(" "), /review_id mismatch/);
    assert.equal(result.body.review_id, "frontend_review_status_a");
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

test("Portfolio Input keeps Run diagnosis disabled until validation and Client Fit are ready", () => {
  const source = fs.readFileSync(portfolioInputTablePath, "utf8");

  assert.match(source, /const WEIGHT_TOLERANCE = 0\.01/);
  assert.match(source, /const MIN_VALID_HOLDINGS = 2/);
  assert.match(source, /const clientProfileReady = Boolean\(activeReview\?\.clientFitProfile\)/);
  assert.match(source, /validHoldingCount >= MIN_VALID_HOLDINGS/);
  assert.match(source, /weightsAddTo100/);
  assert.match(source, /clientProfileReady/);
  assert.match(source, /disabled=\{!ready \|\| isRunningDiagnosis\}/);
  assert.doesNotMatch(source, /SPY:40|QQQ:20|BND:20|GLD:10/);
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
  const hypothesisScreen = fs.readFileSync(hypothesisScreenPath, "utf8");
  const comparisonScreen = fs.readFileSync(comparisonScreenPath, "utf8");
  const verdictScreen = fs.readFileSync(verdictScreenPath, "utf8");
  const combined = [clientFitCard, hypothesisScreen, comparisonScreen, verdictScreen].join("\n");

  assert.match(hypothesisScreen, /ClientFitContextCard/);
  assert.match(comparisonScreen, /ClientFitContextCard/);
  assert.match(verdictScreen, /ClientFitContextCard/);
  assert.match(combined, /Client Fit pass does not clear concentration, stress, drawdown, or other structural issues/);
  assert.match(combined, /Separate from diagnosis/);
  assert.match(combined, /does not clear a material issue|does not clear concentration|does not clear.*structural/i);

  const forbiddenAdvice = /\b(suitable|approved|buy|must rebalance|best portfolio)\b/i;
  assert.doesNotMatch(combined, forbiddenAdvice);
  assert.doesNotMatch(combined, /\bsell\b/i);
});

test("Client Fit screen is a required non-binding step before Hypothesis", () => {
  const source = fs.readFileSync(clientFitScreenPath, "utf8");

  assert.match(source, /activeReview\?\.runStatus === "completed"/);
  assert.match(source, /activeReview\.evidenceReady/);
  assert.match(source, /hasSummary\(summary\)/);
  assert.match(source, /isMissingProfile\(summary\)/);
  assert.match(source, /Backend-compatible runs can preserve a missing-profile state/);
  assert.match(source, /the normal web journey uses your profile before testing a hypothesis/);
  assert.match(source, /href="\/hypothesis"/);
  assert.match(source, /!\s*missingProfile\s*\?\s*\(/);
  assert.doesNotMatch(source, /href="\/comparison"|href="\/verdict"|href="\/report"/);
  assert.doesNotMatch(source, /suitability approved|suitable|approved portfolio|trade now|must rebalance|best portfolio|optimizer mandate/i);
});

test("backend-compatible not_provided Client Fit does not unlock Hypothesis in the web journey", () => {
  const reviewState = loadTsModule(reviewStatePath);
  const { buildHypothesisScreenModel } = loadTsModule(hypothesisScreenModelPath);
  const source = fs.readFileSync(reviewStatePath, "utf8");
  const review = mockHypothesisReview([{
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
  }], {
    clientFit: {
      status_label: "Client Fit not provided",
      status_tone: "amber",
      main_explanation: "Profile missing.",
      decision_boundary: "Complete Client Fit before testing a hypothesis."
    }
  });
  const model = buildHypothesisScreenModel({ activeReview: review });

  assert.equal(reviewState.hasProvidedClientFitSummary(undefined), false);
  assert.equal(reviewState.hasProvidedClientFitSummary({ status_label: "Client Fit not provided" }), false);
  assert.equal(reviewState.hasProvidedClientFitSummary({ status_label: "Profile missing: not provided" }), false);
  assert.equal(reviewState.hasProvidedClientFitSummary({ status_label: "Within stated Client Fit profile" }), true);
  assert.match(source, /clientFitReady:\s*hasProvidedClientFitSummary\(activeReview\?\.reviewSummary\?\.clientFit\)/);
  assert.equal(model.pageState, "locked");
  assert.equal(model.action.state, "blocked");
  assert.match(model.action.disabledReason, /Complete Client Fit/i);
});

test("sample Hypothesis review includes provided Client Fit context before Builder unlocks", () => {
  const source = fs.readFileSync(hypothesisScreenPath, "utf8");
  const { buildHypothesisScreenModel } = loadTsModule(hypothesisScreenModelPath);
  const sampleLikeReview = mockHypothesisReview([{
    card_id: "sample_improve_crisis_resilience",
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
  }]);
  const model = buildHypothesisScreenModel({ activeReview: sampleLikeReview });

  assert.match(source, /Sample Client Fit context is available for the demo journey/);
  assert.match(source, /Client Fit is non-binding context and does not approve a rebalance/);
  assert.equal(model.pageState, "ready");
  assert.equal(model.action.state, "generate");
});

test("Comparison and Verdict prefer stage-scoped Client Fit context over older review summaries", () => {
  const comparisonScreen = fs.readFileSync(comparisonScreenPath, "utf8");
  const verdictScreen = fs.readFileSync(verdictScreenPath, "utf8");

  assert.match(comparisonScreen, /const clientFitForStage = comparison\?\.clientFit \?\? activeReview\?\.reviewSummary\?\.clientFit/);
  assert.match(verdictScreen, /const clientFitForStage = verdict\?\.clientFit \?\? comparison\?\.clientFit \?\? activeReview\?\.reviewSummary\?\.clientFit/);
  assert.match(comparisonScreen, /<ClientFitContextCard[\s\S]*clientFit={clientFitForStage}/);
  assert.match(verdictScreen, /<ClientFitContextCard[\s\S]*clientFit={clientFitForStage}/);
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
      clientFit: extra.clientFit ?? {
        status_label: "Within stated Client Fit profile",
        status_tone: "green",
        main_explanation: "Client Fit context is available.",
        decision_boundary: "Client Fit is non-binding context."
      },
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

test("Hypothesis screen model defaults to one actionable Launchpad card and blocks monitor paths", () => {
  const { buildHypothesisScreenModel } = loadTsModule(hypothesisScreenModelPath);
  const actionable = {
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
  };
  const monitor = {
    card_id: "launchpad_02_evidence_insufficient_monitor",
    title: "Monitor data quality",
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
  };

  const defaultModel = buildHypothesisScreenModel({ activeReview: mockHypothesisReview([monitor, actionable]) });
  const monitorModel = buildHypothesisScreenModel({
    activeReview: mockHypothesisReview([monitor, actionable]),
    selectedCardId: monitor.card_id
  });

  assert.equal(defaultModel.defaultSelectedCardId, actionable.card_id);
  assert.equal(defaultModel.primaryTest.cardId, actionable.card_id);
  assert.equal(defaultModel.primaryTest.canGenerate, true);
  assert.equal(defaultModel.monitorOrDataTests[0].cardId, monitor.card_id);
  assert.equal(monitorModel.primaryTest.cardId, monitor.card_id);
  assert.equal(monitorModel.primaryTest.canGenerate, false);
  assert.equal(monitorModel.action.state, "blocked");
  assert.match(monitorModel.action.disabledReason, /monitoring or data review/i);
});

test("Hypothesis Builder defaults are not derived from Client Fit profile constraints", () => {
  const source = fs.readFileSync(hypothesisScreenPath, "utf8");
  const resetBuilderDefaults = /setBuilderSettings\(DEFAULT_BUILDER_SETTINGS\)/;

  assert.doesNotMatch(source, /CLIENT_FIT_TO_BUILDER_PRESET|builderSettingsForClientFit/);
  assert.doesNotMatch(source, /clientFitProfile\?\.preset_id[\s\S]{0,240}constraintPreset/);
  assert.doesNotMatch(source, /reviewSummary\?\.clientFit\?\.profile_label[\s\S]{0,240}constraintPreset/);
  assert.match(source, resetBuilderDefaults);
  assert.match(source, /ClientFitContextCard/);
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

test("Client Fit pass presentation remains contextual and does not approve inaction", () => {
  const presenter = loadTsModule(clientFitPresentationPath);
  const display = presenter.buildClientFitPresentation({
    status_label: "Within stated Client Fit profile",
    status_tone: "green",
    profile_label: "balanced",
    source_quality_label: "high",
    main_explanation: "Client Fit status is fit.",
    decision_boundary: "Client Fit is non-binding context; keep diagnosis and stress evidence separate.",
    next_best_test: "No action needed because this is a safe portfolio approved for best portfolio status.",
    target_rows: [
      {
        dimension_label: "Return target",
        portfolio_value_label: "6.1%",
        target_or_limit_label: "5.0% to 7.0%",
        status_label: "Within stated Client Fit profile",
        status_tone: "green",
        explanation: "Return evidence sits inside the stated range; do not treat it as suitable or approved."
      },
      {
        dimension_label: "Worst stress loss limit",
        portfolio_value_label: "-12.0%",
        target_or_limit_label: "Limit: -18.0%",
        status_label: "Within stated Client Fit profile",
        status_tone: "green",
        explanation: "Stress loss is within the stated temporary loss limit; this is not a trade now signal."
      }
    ]
  }, {
    schema_version: "site_explanation_bundle_v1",
    screens: {
      client_fit: {
        executive: [{
          id: "client_fit.unsafe",
          level: "executive",
          text: "Suitability approved and no action needed.",
          tone: "neutral",
          evidence_status: "available",
          claim_type: "boundary_note",
          source_refs: []
        }],
        evidence: [],
        technical: []
      }
    }
  });
  const serialized = JSON.stringify(display);

  assert.equal(display.statusLabel, "Within your profile");
  assert.match(display.summary, /Keep the diagnosis and stress evidence separate/i);
  assert.match(display.boundaryNote, /non-binding context/i);
  assert.match(display.nextBestTest, /test one candidate only if the diagnosis evidence justifies a comparison/i);
  assert.ok(display.allRows.every((row) => !/suitable|approved|trade now/i.test(row.explanation)));
  assert.ok(display.technicalDetails.every((detail) => !/suitability|approved|no action needed/i.test(detail)));
  assert.ok(display.technicalDetails.includes("Client Fit is separate from Diagnostic Quality and Decision Verdict."));
  assert.doesNotMatch(serialized, /suitability|suitable|approved|safe portfolio|no action needed|trade now|must rebalance|best portfolio|optimizer mandate/i);
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

test("diagnosis display model keeps adversarial optimizer and advice wording out of the primary answer", () => {
  const diagnosisDisplay = loadTsModule(diagnosisDisplayModelPath);
  const model = diagnosisDisplay.buildDiagnosisDisplayModel({
    headline: "Portfolio Health Score says the optimizer should rebalance now.",
    evidenceQuality: "Strong evidence",
    nextStep: "Review supporting evidence before testing one candidate hypothesis.",
    boundaryNote: "Diagnosis is decision-support evidence only.",
    drivers: [
      "Optimizer driver says trade now.",
      "Portfolio Health Score driver says must rebalance.",
      "Scorecard driver says approved portfolio."
    ],
    metrics: [
      { label: "VaR 95", value: "-1.20%", detail: "Advanced tail metric", tone: "blue" },
      { label: "Sharpe", value: "0.42", detail: "Advanced efficiency metric", tone: "blue" }
    ],
    xraySummary: {
      snapshotCards: [
        { label: "Top 3 concentration", value: "68.00%", detail: "Capital in largest three holdings", tone: "red" },
        { label: "Dominant exposure", value: "Equity", detail: "72.00%", tone: "amber" },
        { label: "Max drawdown", value: "-24.00%", detail: "Recovered within sample", tone: "red" },
        { label: "Worst pre-stress weakness", value: "Equity sell-off risk", detail: "Score 78/100", tone: "red" }
      ],
      riskProfile: {
        insight: "Current portfolio risk profile evidence is available.",
        metrics: [
          { label: "CAGR", value: "6.40%", detail: "Primary diagnostic window", tone: "blue" },
          { label: "Max drawdown", value: "-24.00%", detail: "Recovered within sample", tone: "red" },
          { label: "Time to recovery", value: "13.00 months", detail: "Recovered within sample", tone: "slate" },
          { label: "VaR 95", value: "-1.20%", detail: "Advanced tail metric", tone: "blue" },
          { label: "Sharpe", value: "0.42", detail: "Advanced efficiency metric", tone: "blue" }
        ],
        keyFacts: []
      },
      unavailableNotes: []
    },
    siteExplanation: {
      schema_version: "site_explanation_bundle_v1",
      warnings: [],
      screens: {
        diagnosis: {
          executive: [{ id: "e", level: "executive", text: "Raw executive says rebalance now from optimizer.", tone: "risk", evidence_status: "available", claim_type: "material_claim", source_refs: [] }],
          evidence: [{ id: "v", level: "evidence", text: "Raw evidence references portfolio_xray.json and trade now.", tone: "risk", evidence_status: "available", claim_type: "material_claim", source_refs: [] }],
          technical: []
        }
      }
    }
  });

  const publicSurface = JSON.stringify({
    mainFinding: model.mainFinding,
    whyItMatters: model.whyItMatters,
    primaryEvidence: model.primaryEvidence,
    whatMatters: model.whatMatters,
    behaviorSnapshot: model.behaviorSnapshot,
    technicalEvidence: model.technicalEvidence
  });

  assert.match(model.mainFinding, /equity-led/i);
  assert.match(model.whyItMatters, /equity sell-off risk/i);
  assert.match(publicSurface, /Top 3 = 68%|Top 3 holdings: 68%/);
  assert.match(publicSurface, /Dominant exposure: Equity 72%|Main exposure/);
  assert.equal(model.primaryEvidence.length, 3);
  assert.ok(model.whatMatters.length <= 4);
  assert.ok(model.behaviorSnapshot.length <= 3);
  assert.ok(model.advancedMetrics.some((metric) => metric.label === "VaR 95"));
  assert.ok(model.advancedMetrics.some((metric) => metric.label === "Sharpe"));
  assert.deepEqual(model.technicalEvidence, []);
  assert.doesNotMatch(publicSurface, /optimizer|Portfolio Health Score|scorecard|rebalance now|must rebalance|trade now|approved portfolio|portfolio_xray\.json/i);
});

test("Diagnosis page uses the compact display model instead of the standalone explanation wall", () => {
  const diagnosisPage = fs.readFileSync(diagnosisPagePath, "utf8");
  const diagnosisScreen = fs.readFileSync(diagnosisScreenPath, "utf8");
  const diagnosisPanel = fs.readFileSync(diagnosisSummaryPanelPath, "utf8");

  assert.doesNotMatch(diagnosisPage, /SiteExplanationHierarchy/);
  assert.match(diagnosisScreen, /siteExplanation/);
  assert.match(diagnosisPanel, /buildDiagnosisDisplayModel/);
  assert.match(diagnosisPanel, /VerdictHero/);
  assert.match(diagnosisPanel, /EvidenceSummary/);
  assert.match(diagnosisPanel, /MetricMatrix/);
  assert.match(diagnosisPanel, /<details id="advanced-diagnostics"/);
  assert.match(diagnosisPanel, /Advanced diagnostics and technical evidence/);
  assert.match(diagnosisPanel, /Full portfolio x-ray detail/);
  assert.match(diagnosisPanel, /Historical diagnostic window/);
  assert.match(diagnosisPanel, /href="\/evidence"/);
  assert.match(diagnosisPanel, /href="\/hypothesis"/);
  assert.doesNotMatch(diagnosisPanel, /href="\/verdict"|href="\/report"/);
  assert.doesNotMatch(diagnosisPanel, /sourceArtifacts|rejectedAlternatives|rationaleRefs/);
  assert.doesNotMatch(diagnosisPanel, /Evidence available/);
  assert.doesNotMatch(diagnosisPanel, /Rolling charts are not shown/);
  assert.doesNotMatch(diagnosisPanel, /must rebalance|trade now|Portfolio Health Score|Robustness Scorecard|optimizer/i);
});

test("review state builds Diagnosis from compact summaries, then FastAPI envelope, then raw artifacts", () => {
  const reviewState = loadTsModule(reviewStatePath);
  const compactDiagnosis = {
    status: "Diagnosis ready",
    headline: "Compact saved summary wins.",
    evidenceQuality: "Strong evidence",
    nextStep: "Continue from compact review state.",
    boundaryNote: "Compact summary only.",
    drivers: ["Compact saved driver."],
    metrics: [],
    sourceArtifacts: [],
    rejectedAlternatives: [],
    rationaleRefs: []
  };
  const rawOutputs = {
    portfolio_xray: {
      block_2_1_asset_allocation: {
        actual_economic_exposure_summary: { headline: "Raw artifact allocation headline." },
        portfolio_composition_snapshot: {
          top1_holding: { ticker: "SPY", weight_pct: 0.52 },
          dominant_asset_class: { name: "equity", weight_pct: 0.72 },
          dominant_main_risk_factor: { name: "equity", weight_pct: 0.72 }
        }
      },
      block_2_2_portfolio_metrics: {
        portfolio_behavior_snapshot: { headline: "Raw artifact behavior headline.", overall_behavior_label: "Concentrated growth" },
        return_risk_metrics: { portfolio_cagr: 0.064, vol_annual: 0.18, sharpe: 0.42 },
        drawdown_diagnostics: { max_drawdown: -0.24 }
      },
      block_2_6_portfolio_weakness_map: {
        risk_types: [{ risk_title: "Equity sell-off risk", score_0_100: 78, severity: "high", short_diagnosis: "Equity sell-off risk dominates." }]
      }
    },
    stress_report: {
      stress_conclusions: { overall_confidence: "high" }
    }
  };
  const fastApiReviewResult = {
    status: "completed",
    outputs: rawOutputs,
    fastapi_envelope: {
      data: {
        diagnosis: {
          headline: "FastAPI bounded diagnosis wins.",
          confidence: "high",
          selected_diagnosis_role: "primary",
          next_diagnostic_step: "Review supporting evidence before testing one candidate hypothesis.",
          recommendation_boundary: "Diagnosis is decision-support evidence only.",
          root_cause_narrative: {
            statement: "FastAPI bounded diagnosis wins.",
            label: "Concentration"
          },
          diagnosis_evidence_items: [{ interpretation: "Bounded FastAPI evidence." }],
          evidence_chain: ["Bounded chain item."]
        }
      }
    }
  };

  const compactResult = reviewState.buildDiagnosisFromReview({
    investorCurrency: "USD",
    holdings: [],
    reviewSummary: { diagnosis: compactDiagnosis },
    reviewResult: fastApiReviewResult
  });
  const fastApiResult = reviewState.buildDiagnosisFromReview({
    investorCurrency: "USD",
    holdings: [],
    reviewResult: fastApiReviewResult
  });
  const rawResult = reviewState.buildDiagnosisFromReview({
    investorCurrency: "USD",
    holdings: [],
    reviewResult: {
      status: "completed",
      outputs: rawOutputs
    }
  });

  assert.equal(compactResult.headline, "Compact saved summary wins.");
  assert.equal(fastApiResult.headline, "FastAPI bounded diagnosis wins.");
  assert.match(rawResult.headline, /main pre-stress weakness to review is Equity Sell-Off Risk/i);
  assert.deepEqual(rawResult.sourceArtifacts, ["portfolio_xray.json", "stress_report.json"]);
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

test("stress lab adapter maps raw stress_report outputs into user-facing current-portfolio evidence", () => {
  const stressLabModel = loadTsModule(stressLabModelPath);
  const model = stressLabModel.buildStressLabModelFromOutputs({
    stress_report: {
      stress_results_v1: {
        envelope: {
          worst_synthetic: { scenario_id: "equity_shock" },
          worst_historical: { episode: "dotcom" }
        },
        synthetic_scenarios: [
          {
            scenario_id: "equity_shock",
            availability: "available",
            portfolio_loss_pct: -0.183,
            loss_contribution: {
              pnl_by_asset_pct: { SPY: -0.121, QQQ: -0.044, BND: -0.018, Cash: 0.004 },
              assets_hurt: [
                { ticker: "SPY", pnl_pct: -0.121 },
                { ticker: "QQQ", pnl_pct: -0.044 }
              ],
              assets_helped: [{ ticker: "Cash", pnl_pct: 0.004 }]
            },
            factor_attribution: {
              pnl_by_factor_pct: { beta_eq: -0.14, beta_credit: -0.02 }
            },
            synthetic_assumptions: { beta_confidence: "high" }
          },
          {
            scenario_id: "credit_shock",
            availability: "available",
            portfolio_loss_pct: -0.061,
            pnl_by_asset_pct: { BND: -0.036, SPY: -0.021 }
          }
        ],
        historical_episodes: [
          {
            episode: "2022",
            availability: "available",
            max_dd: -0.119,
            data_quality: "usable_with_gaps",
            loss_contribution: { pnl_by_asset_pct: { BND: -0.052, QQQ: -0.031, Cash: 0.002 } }
          }
        ]
      },
      hedge_gap_analysis_v1: {
        summary: {
          main_hedge_gap: {
            risk_type: "equity_crash_protection",
            linked_scenario_id: "equity_shock",
            protection_status: "weak_protection",
            offset_coverage_ratio: 0.03
          }
        },
        by_risk_type: [{
          risk_type: "equity_crash_protection",
          linked_scenario_id: "equity_shock",
          protection_status: "weak_protection",
          gross_loss_from_assets_hurt: 0.183,
          positive_contribution_from_assets_helped: 0.004,
          offset_coverage_ratio: 0.03,
          assets_hurt: [{ ticker: "SPY", pnl_pct: -0.121 }],
          assets_helped: [{ ticker: "Cash", pnl_pct: 0.004 }]
        }]
      },
      current_portfolio_stress_scorecard_v1: {
        block_status: "partial",
        stress_coverage: {
          n_synthetic_available: 2,
          n_synthetic_total: 8,
          n_historical_available: 1,
          n_historical_total: 5
        },
        stress_diagnosis: {
          diagnosis_confidence: "medium",
          diagnostic_code: "DIAG_loss_ok",
          raw_status: "pass"
        },
        pre_stress_confirmation_summary: {
          weakness_map: {
            confirmation_rows: [{
              linked_scenario_id: "equity_shock",
              confirmation_status: "confirmed",
              protection_status: "weak_protection",
              offset_coverage_ratio: 0.03,
              portfolio_loss_pct: -0.183
            }]
          }
        }
      }
    }
  });

  assert.ok(model);
  assert.equal(model.selectedScenarioId, "equity_shock");
  const equityShock = model.syntheticScenarios.find((scenario) => scenario.id === "equity_shock");
  const dotcom = model.historicalScenarios.find((scenario) => scenario.id === "dotcom");
  assert.equal(equityShock?.displayName, "Equity sell-off");
  assert.equal(equityShock?.assetsHurt[0].ticker, "SPY");
  assert.equal(model.hedgeGap.displayName, "Equity sell-off protection");
  assert.equal(dotcom?.availability, "unavailable");
  assert.equal(dotcom?.dataNote, "Replay limited");
  assert.equal(dotcom?.interpretation, "Dot-com replay is limited for the current portfolio.");
  assert.match(model.limitations.headline, /Historical replay is limited/i);
  assert.match(JSON.stringify(model.scorecard), /Historical replay limited|Equity sell-off/);
  assert.doesNotMatch(JSON.stringify(model), /DIAG_|loss_ok|raw_status|stress_report\.json|field_path|source_refs|artifact/i);
});

test("Evidence screen contract keeps Stress Lab between diagnosis and Client Fit", () => {
  const evidenceScreen = fs.readFileSync(evidenceScreenPath, "utf8");
  const stressTestLab = fs.readFileSync(stressTestLabPath, "utf8");

  assert.match(evidenceScreen, /activeReview\?\.submitted/);
  assert.match(evidenceScreen, /activeReview\.runMode === "real_run"/);
  assert.match(evidenceScreen, /activeReview\.runStatus === "completed"/);
  assert.match(evidenceScreen, /searchParams\.get\("sample"\) === "1"/);
  assert.match(evidenceScreen, /ensureStressLabModel\(sampleStressLabData\)/);
  assert.match(evidenceScreen, /href="\/client-fit"/);
  assert.doesNotMatch(evidenceScreen, /href="\/hypothesis"|href="\/comparison"|href="\/verdict"|href="\/report"/);
  assert.match(evidenceScreen, /Complete Portfolio Input first to unlock Stress Test Lab/);
  assert.match(evidenceScreen, /Full Stress Test Lab detail is not available/);
  assert.match(stressTestLab, /Stress Test Lab turns scenario evidence into one current-portfolio answer first/);
  assert.match(stressTestLab, /technical drill-downs remain below as secondary details/);
  assert.doesNotMatch(stressTestLab, /raw technical panels|must rebalance|trade now|Portfolio Health Score|optimizer/i);
});

function unsafeEvidenceExplanationBundle() {
  return {
    schema_version: "site_explanation_bundle_v1",
    warnings: ["missing_source:stress_report"],
    screens: {
      evidence: {
        executive: [{
          id: "evidence.executive",
          level: "executive",
          text: "Stress evidence says trade now from stress_report.json.",
          tone: "risk",
          evidence_status: "available",
          claim_type: "material_claim",
          source_refs: [{ artifact: "stress_report.json", field_path: "stress_results_v1.envelope" }]
        }],
        evidence: [{
          id: "evidence.detail",
          level: "evidence",
          text: "Worst stress loss comes from source_refs and artifact fields.",
          tone: "risk",
          evidence_status: "available",
          claim_type: "material_claim",
          source_refs: [{ artifact: "portfolio_xray.json", field_path: "block_2_6" }]
        }],
        technical: []
      }
    }
  };
}

test("stress story counts evidence trace without copying trace text into the primary summary", () => {
  const storyModel = loadTsModule(stressStoryModelPath);
  const sample = readJsonFixture(path.resolve(frontendRoot, "data", "demo", "stress-lab.json"));
  const story = storyModel.buildStressStoryViewModel(sample, unsafeEvidenceExplanationBundle());

  const serialized = JSON.stringify(story);
  assert.ok(story.evidenceTraceCount > 0);
  assert.match(story.answer, /current portfolio/i);
  assert.match(story.whatThisMeans, /does not create a rebalance verdict/i);
  assert.doesNotMatch(serialized, /stress_report\.json|portfolio_xray\.json|field_path|source_refs|artifact|trade now|must rebalance|buy|sell|suitability approved/i);
});

test("site explanation presenter sanitizes unsafe public Evidence trace text while keeping provenance developer-only", () => {
  const presenter = loadTsModule(siteExplanationPresenterPath);
  const display = presenter.buildPublicSiteExplanationDisplayModel(unsafeEvidenceExplanationBundle(), "evidence", "Stress evidence trace");
  const developerDisplay = presenter.buildPublicSiteExplanationDisplayModel(
    unsafeEvidenceExplanationBundle(),
    "evidence",
    "Stress evidence trace",
    { includeDeveloperProvenance: true }
  );
  const serialized = JSON.stringify(display);

  assert.ok(display);
  assert.equal(display.title, "Stress evidence trace");
  assert.ok(display.executiveItems.length > 0);
  assert.match(display.executiveItems[0].text, /developer provenance stays separate/i);
  assert.doesNotMatch(serialized, /stress_report\.json|portfolio_xray\.json|field_path|source_refs|artifact|trade now|must rebalance|buy|sell|suitability approved/i);
  assert.equal(display.developerProvenance, undefined);
  assert.ok(developerDisplay.developerProvenance);
  assert.deepEqual(developerDisplay.developerProvenance.items[0].sourceRefs, [
    "stress_report.json:stress_results_v1.envelope"
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

test("review recovery route drops downstream artifact payloads from recovered active state", async () => {
  const route = loadRoute({ routePath: reviewRecoverRoutePath });

  await withMockFetch(async () => Response.json(fastApiEnvelope({
    review_id: "frontend_review_recover_stale_downstream",
    stage: "recovery",
    lineage: { review_id: "frontend_review_recover_stale_downstream" },
    data: {
      review_summary: {
        investor_currency: "USD"
      },
      artifact_payloads: {
        portfolio_xray: { schema_version: "portfolio_xray_v2", current_portfolio_only: true },
        stress_report: { schema_version: "stress_report_v1" },
        problem_classification: { primary_diagnosis: "Concentration" },
        candidate_launchpad: { cards: [{ card_id: "card_equal_weight" }] },
        portfolio_alternatives_builder: {
          selected_card_id: "card_equal_weight",
          candidate_setup: { candidate_setup_id: "candidate_setup_card_equal_weight" }
        },
        candidate_generation: { candidate_id: "stale_candidate" },
        current_vs_candidate: { candidate_id: "stale_candidate" },
        decision_verdict: { verdict_id: "stale_verdict" },
        report: { report_id: "stale_report" }
      },
      artifact_refs: [
        { kind: "portfolio_xray", ref: "runs/frontend_review_recover_stale_downstream/analysis_subject/portfolio_xray.json", scope: "analysis_subject", raw_path_exposed: false },
        { kind: "candidate_generation", ref: "runs/frontend_review_recover_stale_downstream/candidate_generation.json", scope: "run", raw_path_exposed: false },
        { kind: "current_vs_candidate", ref: "runs/frontend_review_recover_stale_downstream/current_vs_candidate.json", scope: "run", raw_path_exposed: false },
        { kind: "decision_verdict", ref: "runs/frontend_review_recover_stale_downstream/decision_verdict.json", scope: "run", raw_path_exposed: false },
        { kind: "report", ref: "runs/frontend_review_recover_stale_downstream/report.json", scope: "run", raw_path_exposed: false }
      ],
      downstream_artifacts_restored_as_active: false,
      restored_active_stages: ["diagnosis", "evidence", "hypothesis_setup"]
    },
    evidence: {
      source_artifacts: [
        { kind: "portfolio_xray", ref: "runs/frontend_review_recover_stale_downstream/analysis_subject/portfolio_xray.json", scope: "analysis_subject", raw_path_exposed: false },
        { kind: "current_vs_candidate", ref: "runs/frontend_review_recover_stale_downstream/current_vs_candidate.json", scope: "run", raw_path_exposed: false }
      ],
      data_quality: "ok",
      confidence: "medium"
    }
  })), async () => {
    const result = await responseJson(await route.POST(makeJsonRequest({
      review_id: "frontend_review_recover_stale_downstream"
    })));

    assert.equal(result.status, 200);
    assert.equal(result.body.recovery.downstream_artifacts_restored_as_active, false);
    assert.deepEqual(result.body.recovery.restored_active_stages, ["diagnosis", "evidence", "hypothesis_setup"]);
    assert.deepEqual(Object.keys(result.body.fastapi_envelope.data.artifact_payloads).sort(), [
      "candidate_launchpad",
      "portfolio_alternatives_builder",
      "portfolio_xray",
      "problem_classification",
      "stress_report"
    ]);
    assert.deepEqual(result.body.fastapi_envelope.data.artifact_refs.map((ref) => ref.kind), [
      "portfolio_xray"
    ]);
    assert.deepEqual(result.body.fastapi_envelope.evidence.source_artifacts.map((ref) => ref.kind), [
      "portfolio_xray"
    ]);
    assert.deepEqual(Object.keys(result.body.review_result.outputs).sort(), [
      "candidate_launchpad",
      "portfolio_alternatives_builder",
      "portfolio_xray",
      "problem_classification",
      "stress_report"
    ]);
    assert.deepEqual(Object.keys(result.body.review_result.paths).sort(), [
      "portfolio_xray"
    ]);
    assert.equal(result.body.review_result.outputs.candidate_generation, undefined);
    assert.equal(result.body.review_result.outputs.current_vs_candidate, undefined);
    assert.equal(result.body.review_result.outputs.decision_verdict, undefined);
    assert.equal(result.body.review_result.outputs.report, undefined);
    assert.equal(result.body.fastapi_envelope.data.artifact_payloads.candidate_generation, undefined);
    assert.equal(result.body.fastapi_envelope.data.artifact_payloads.current_vs_candidate, undefined);
    assert.equal(result.body.fastapi_envelope.data.artifact_payloads.decision_verdict, undefined);
    assert.equal(result.body.fastapi_envelope.data.artifact_payloads.report, undefined);
    assert.equal(result.body.review_result.fastapi_envelope.data.artifact_payloads.candidate_generation, undefined);
    assert.equal(result.body.review_result.fastapi_envelope.data.artifact_payloads.current_vs_candidate, undefined);
    assert.equal(result.body.review_result.fastapi_envelope.data.artifact_payloads.decision_verdict, undefined);
    assert.equal(result.body.review_result.fastapi_envelope.data.artifact_payloads.report, undefined);
    assert.deepEqual(result.body.review_result.fastapi_envelope.data.artifact_refs.map((ref) => ref.kind), [
      "portfolio_xray"
    ]);
    assert.deepEqual(result.body.review_result.fastapi_envelope.evidence.source_artifacts.map((ref) => ref.kind), [
      "portfolio_xray"
    ]);
    assert.equal(result.body.review_result.paths.candidate_generation, undefined);
    assert.equal(result.body.review_result.paths.current_vs_candidate, undefined);
    assert.equal(result.body.review_result.paths.decision_verdict, undefined);
    assert.equal(result.body.review_result.paths.report, undefined);
  });
});

test("review recovery route rejects FastAPI recovery lineage from a different review before restoring state", async () => {
  const route = loadRoute({ routePath: reviewRecoverRoutePath });

  await withMockFetch(async (url, options) => {
    assert.match(url, /\/api\/v1\/reviews\/frontend_review_recover_a$/);
    assert.equal(options.method, "GET");
    return Response.json(fastApiEnvelope({
      review_id: "frontend_review_recover_b",
      stage: "recovery",
      lineage: { review_id: "frontend_review_recover_b" },
      data: {
        review_summary: { investor_currency: "USD" },
        artifact_payloads: {
          portfolio_xray: { schema_version: "portfolio_xray_v2" }
        }
      }
    }));
  }, async () => {
    const result = await responseJson(await route.GET(new Request("http://localhost/api/portfolio/review/recover?review_id=frontend_review_recover_a")));

    assert.equal(result.status, 409);
    assert.equal(result.body.status, "failed");
    assert.equal(result.body.stage, "review_recovery");
    assert.match(result.body.error, /lineage did not match/);
    assert.match(result.body.details.join(" "), /review_id mismatch/);
    assert.equal(result.body.review_result, undefined);
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

test("candidate route maps a compare-ready FastAPI candidate envelope without unsafe paths", async () => {
  const route = loadRoute({ routePath: candidateGenerateRoutePath });

  await withMockFetch(async (url, options) => {
    assertSignedFastApiHeaders(options);
    assert.match(url, /\/api\/v1\/reviews\/frontend_review_candidate\/candidate$/);
    assert.equal(options.method, "POST");
    assert.deepEqual(JSON.parse(options.body), {
      builder_setup_id: "builder_setup_equal_weight"
    });
    return Response.json(fastApiCandidateEnvelope());
  }, async () => {
    const result = await responseJson(await route.POST(makeJsonRequest({
      review_id: "frontend_review_candidate",
      selected_card_id: "card_equal_weight",
      builder_setup_id: "builder_setup_equal_weight"
    }, "http://localhost/api/portfolio/candidate/generate")));

    assert.equal(result.status, 200);
    assert.equal(result.body.status, "completed");
    assert.equal(result.body.stage, "candidate_generation");
    assert.equal(result.body.review_id, "frontend_review_candidate");
    assert.equal(result.body.selected_card_id, "card_equal_weight");
    assert.equal(result.body.builder_setup_id, "builder_setup_equal_weight");
    assert.equal(result.body.candidate_id, "equal_weight");
    assert.equal(result.body.generation_status, "generated");
    assert.equal(result.body.can_compare, true);
    assert.equal(result.body.candidate_generation.candidate.candidate_id, "equal_weight");
    assert.deepEqual(result.body.candidate_generation.candidate.weights, { VOO: 0.5, BND: 0.5 });
    assert.equal(result.body.candidate_generation.handoff_to_comparison.can_compare, true);
    assert.doesNotMatch(JSON.stringify(result.body), /[A-Z]:[\\/]/);
    assert.doesNotMatch(JSON.stringify(result.body), /Traceback|portfolio_weights\.yml/);
  });
});

test("candidate route prepares Builder first when setup id is missing", async () => {
  const route = loadRoute({ routePath: candidateGenerateRoutePath });
  const calls = [];

  await withMockFetch(async (url, options) => {
    const requestUrl = String(url);
    calls.push(requestUrl);
    assertSignedFastApiHeaders(options);
    if (requestUrl.endsWith("/api/v1/reviews/frontend_review_candidate/builder")) {
      assert.equal(options.method, "POST");
      const builderBody = JSON.parse(options.body);
      assert.equal(builderBody.selected_card_id, "card_equal_weight");
      assert.equal(builderBody.overrides.method_id, "equal_weight");
      return Response.json(fastApiEnvelope({
        review_id: "frontend_review_candidate",
        stage: "builder",
        lineage: {
          review_id: "frontend_review_candidate",
          selected_card_id: "card_equal_weight",
          builder_setup_id: "builder_setup_equal_weight"
        },
        data: { candidate_generation_allowed: true }
      }));
    }
    assert.match(requestUrl, /\/api\/v1\/reviews\/frontend_review_candidate\/candidate$/);
    assert.deepEqual(JSON.parse(options.body), {
      builder_setup_id: "builder_setup_equal_weight"
    });
    return Response.json(fastApiCandidateEnvelope());
  }, async () => {
    const result = await responseJson(await route.POST(makeJsonRequest({
      review_id: "frontend_review_candidate",
      selected_card_id: "card_equal_weight",
      overrides: { method_id: "equal_weight" }
    }, "http://localhost/api/portfolio/candidate/generate")));

    assert.equal(result.status, 200);
    assert.equal(result.body.status, "completed");
    assert.equal(result.body.builder_setup_id, "builder_setup_equal_weight");
    assert.equal(result.body.can_compare, true);
    assert.equal(calls.length, 2);
    assert.match(calls[0], /\/builder$/);
    assert.match(calls[1], /\/candidate$/);
  });
});

test("candidate route blocks stale Builder lineage before calling candidate generation", async () => {
  const route = loadRoute({ routePath: candidateGenerateRoutePath });
  let callCount = 0;

  await withMockFetch(async (url, options) => {
    callCount += 1;
    assert.match(url, /\/api\/v1\/reviews\/frontend_review_candidate\/builder$/);
    assert.equal(options.method, "POST");
    return Response.json(fastApiEnvelope({
      review_id: "frontend_review_candidate",
      stage: "builder",
      lineage: {
        review_id: "frontend_review_candidate",
        selected_card_id: "stale_card",
        builder_setup_id: "builder_setup_stale"
      },
      data: { candidate_generation_allowed: true }
    }));
  }, async () => {
    const result = await responseJson(await route.POST(makeJsonRequest({
      review_id: "frontend_review_candidate",
      selected_card_id: "card_equal_weight",
      method_id: "equal_weight"
    }, "http://localhost/api/portfolio/candidate/generate")));

    assert.equal(callCount, 1);
    assert.equal(result.status, 409);
    assert.equal(result.body.status, "failed");
    assert.equal(result.body.stage, "candidate_generation");
    assert.match(result.body.details.join(" "), /selected_card_id mismatch/);
    assert.equal(result.body.candidate_generation, undefined);
  });
});

test("candidate route keeps blocked candidate attempts from unlocking Comparison", async () => {
  const route = loadRoute({ routePath: candidateGenerateRoutePath });

  await withMockFetch(async (url, options) => {
    assert.match(url, /\/api\/v1\/reviews\/frontend_review_candidate\/candidate$/);
    assert.equal(options.method, "POST");
    return Response.json(fastApiCandidateEnvelope({
      status: "blocked",
      data: {
        candidate: {
          candidate_id: "equal_weight",
          method_label: "Equal Weight",
          generation_status: "blocked"
        },
        hypothesis: {
          hypothesis: "Test whether equal weighting reduces concentration.",
          success_criteria: ["Reduce top holding concentration."]
        },
        next_allowed_actions: ["select_another_card"]
      },
      safe_error: {
        code: "candidate_generation_blocked",
        message: "Candidate generation did not produce compare-ready weights.",
        user_action: "return_to_hypothesis",
        retryable: false
      }
    }));
  }, async () => {
    const result = await responseJson(await route.POST(makeJsonRequest({
      review_id: "frontend_review_candidate",
      selected_card_id: "card_equal_weight",
      builder_setup_id: "builder_setup_equal_weight"
    }, "http://localhost/api/portfolio/candidate/generate")));

    assert.equal(result.status, 200);
    assert.equal(result.body.status, "blocked");
    assert.equal(result.body.stage, "candidate_generation");
    assert.equal(result.body.can_compare, false);
    assert.equal(result.body.candidate_generation.handoff_to_comparison.can_compare, false);
    assert.equal(result.body.candidate_generation.candidate.status, "blocked");
  });
});

test("candidate route does not trust run_comparison when generation status is not generated", async () => {
  const route = loadRoute({ routePath: candidateGenerateRoutePath });

  await withMockFetch(async (url, options) => {
    assert.match(String(url), /\/api\/v1\/reviews\/frontend_review_candidate\/candidate$/);
    assert.equal(options.method, "POST");
    return Response.json(fastApiCandidateEnvelope({
      status: "ok",
      data: {
        candidate: {
          candidate_id: "equal_weight",
          method_label: "Equal Weight",
          generation_status: "blocked"
        },
        hypothesis: {
          hypothesis: "Test whether equal weighting reduces concentration.",
          success_criteria: ["Reduce top holding concentration."]
        },
        next_allowed_actions: ["run_comparison"]
      }
    }));
  }, async () => {
    const result = await responseJson(await route.POST(makeJsonRequest({
      review_id: "frontend_review_candidate",
      selected_card_id: "card_equal_weight",
      builder_setup_id: "builder_setup_equal_weight"
    }, "http://localhost/api/portfolio/candidate/generate")));

    assert.equal(result.status, 200);
    assert.equal(result.body.status, "blocked");
    assert.equal(result.body.can_compare, false);
    assert.equal(result.body.generation_status, "blocked");
    assert.equal(result.body.candidate_generation.handoff_to_comparison.can_compare, false);
  });
});

test("candidate generation readiness requires completed, generated, compare-ready state", () => {
  const { isCompareReadyCandidateGeneration } = loadTsModule(candidateGenerationReadinessPath);

  assert.equal(isCompareReadyCandidateGeneration({
    status: "completed",
    generationStatus: "generated",
    canCompare: true
  }), true);
  assert.equal(isCompareReadyCandidateGeneration({
    status: "completed",
    generationStatus: "blocked",
    canCompare: true
  }), false);
  assert.equal(isCompareReadyCandidateGeneration({
    status: "completed",
    generationStatus: "generated",
    canCompare: false
  }), false);
  assert.equal(isCompareReadyCandidateGeneration({
    status: "blocked",
    generationStatus: "generated",
    canCompare: true
  }), false);
  assert.equal(isCompareReadyCandidateGeneration(undefined), false);
});

test("comparison route rejects FastAPI lineage for a different candidate before trusting comparison evidence", async () => {
  const route = loadRoute({ routePath: comparisonGenerateRoutePath });

  await withMockFetch(async (url, options) => {
    assert.match(url, /\/api\/v1\/reviews\/frontend_review_lineage\/comparison$/);
    assert.equal(options.method, "POST");
    assert.deepEqual(JSON.parse(options.body), {
      candidate_id: "equal_weight"
    });
    return Response.json(fastApiEnvelope({
      review_id: "frontend_review_lineage",
      stage: "comparison",
      lineage: {
        review_id: "frontend_review_lineage",
        selected_card_id: "card_equal_weight",
        candidate_id: "stale_candidate",
        comparison_id: "current_vs_candidate:stale_candidate"
      },
      data: {
        comparison: {
          candidate_label: "Stale Candidate",
          success_criteria_result: "passed"
        }
      }
    }));
  }, async () => {
    const result = await responseJson(await route.POST(makeJsonRequest({
      review_id: "frontend_review_lineage",
      selected_card_id: "card_equal_weight",
      candidate_id: "equal_weight"
    }, "http://localhost/api/portfolio/comparison/generate")));

    assert.equal(result.status, 409);
    assert.equal(result.body.status, "failed");
    assert.equal(result.body.stage, "current_vs_candidate");
    assert.match(result.body.error, /lineage did not match/);
    assert.match(result.body.details.join(" "), /candidate_id mismatch/);
    assert.equal(result.body.current_vs_candidate, undefined);
    assert.equal(result.body.fastapi_envelope, undefined);
  });
});

test("verdict route rejects FastAPI lineage for a different comparison before trusting verdict evidence", async () => {
  const route = loadRoute({ routePath: verdictGenerateRoutePath });

  await withMockFetch(async (url, options) => {
    assert.match(url, /\/api\/v1\/reviews\/frontend_review_lineage\/verdict$/);
    assert.equal(options.method, "POST");
    assert.deepEqual(JSON.parse(options.body), {
      comparison_id: "current_vs_candidate:equal_weight"
    });
    return Response.json(fastApiEnvelope({
      review_id: "frontend_review_lineage",
      stage: "verdict",
      lineage: {
        review_id: "frontend_review_lineage",
        selected_card_id: "card_equal_weight",
        candidate_id: "equal_weight",
        comparison_id: "current_vs_candidate:stale_candidate",
        verdict_id: "rebalance_to_selected_candidate"
      },
      data: {
        verdict: {
          verdict_id: "rebalance_to_selected_candidate",
          verdict: "rebalance_review"
        }
      }
    }));
  }, async () => {
    const result = await responseJson(await route.POST(makeJsonRequest({
      review_id: "frontend_review_lineage",
      selected_card_id: "card_equal_weight",
      candidate_id: "equal_weight",
      comparison_id: "current_vs_candidate:equal_weight"
    }, "http://localhost/api/portfolio/verdict/generate")));

    assert.equal(result.status, 409);
    assert.equal(result.body.status, "failed");
    assert.equal(result.body.stage, "decision_verdict");
    assert.match(result.body.error, /lineage did not match/);
    assert.match(result.body.details.join(" "), /comparison_id mismatch/);
    assert.equal(result.body.decision_verdict, undefined);
    assert.equal(result.body.fastapi_envelope, undefined);
  });
});

test("report route rejects FastAPI lineage for a different verdict before building report display model", async () => {
  const route = loadRoute({ routePath: reportGenerateRoutePath });

  await withMockFetch(async (url, options) => {
    assert.match(url, /\/api\/v1\/reviews\/frontend_review_lineage\/report$/);
    assert.equal(options.method, "POST");
    assert.deepEqual(JSON.parse(options.body), {
      verdict_id: "no_material_rebalance_recommended"
    });
    return Response.json(fastApiReportEnvelope({
      review_id: "frontend_review_lineage",
      lineage: {
        review_id: "frontend_review_lineage",
        selected_card_id: "card_equal_weight",
        candidate_id: "equal_weight",
        comparison_id: "current_vs_candidate:equal_weight",
        verdict_id: "stale_verdict"
      }
    }));
  }, async () => {
    const result = await responseJson(await route.POST(makeJsonRequest({
      review_id: "frontend_review_lineage",
      selected_card_id: "card_equal_weight",
      candidate_id: "equal_weight",
      comparison_id: "current_vs_candidate:equal_weight",
      verdict_id: "no_material_rebalance_recommended"
    }, "http://localhost/api/portfolio/report/generate")));

    assert.equal(result.status, 409);
    assert.equal(result.body.status, "failed");
    assert.equal(result.body.stage, "report_commentary");
    assert.match(result.body.error, /lineage did not match/);
    assert.match(result.body.details.join(" "), /verdict_id mismatch/);
    assert.equal(result.body.report_display_model, undefined);
    assert.equal(result.body.fastapi_envelope, undefined);
  });
});

test("report route rejects FastAPI lineage for a different comparison when comparison id is supplied", async () => {
  const route = loadRoute({ routePath: reportGenerateRoutePath });

  await withMockFetch(async () => Response.json(fastApiReportEnvelope({
    review_id: "frontend_review_lineage",
    lineage: {
      review_id: "frontend_review_lineage",
      selected_card_id: "card_equal_weight",
      candidate_id: "equal_weight",
      comparison_id: "current_vs_candidate:stale_candidate",
      verdict_id: "no_material_rebalance_recommended"
    }
  })), async () => {
    const result = await responseJson(await route.POST(makeJsonRequest({
      review_id: "frontend_review_lineage",
      selected_card_id: "card_equal_weight",
      candidate_id: "equal_weight",
      comparison_id: "current_vs_candidate:equal_weight",
      verdict_id: "no_material_rebalance_recommended"
    }, "http://localhost/api/portfolio/report/generate")));

    assert.equal(result.status, 409);
    assert.equal(result.body.stage, "report_commentary");
    assert.match(result.body.details.join(" "), /comparison_id mismatch/);
    assert.equal(result.body.report_display_model, undefined);
  });
});

test("Hypothesis probes backend review status before Builder and Candidate generation", () => {
  const source = fs.readFileSync(hypothesisScreenPath, "utf8");
  const probeIndex = source.indexOf("probeLiveReviewLineage(reviewId)");
  const builderIndex = source.indexOf('fetch("/api/portfolio/builder/prepare"');
  const candidateIndex = source.indexOf('fetch("/api/portfolio/candidate/generate"');

  assert.ok(probeIndex > 0, "Hypothesis should probe live backend lineage before downstream actions.");
  assert.ok(builderIndex > probeIndex, "Builder prepare must happen after the status probe.");
  assert.ok(candidateIndex > builderIndex, "Candidate generation must happen after Builder prepare.");
  assert.match(source, /Run a new diagnosis before generating a candidate/);
  assert.match(source, /markLiveLineageUnavailable\(message\)/);
});

test("downstream active state is cleared when upstream Builder or candidate evidence changes", () => {
  const reviewStateSource = fs.readFileSync(reviewStatePath, "utf8");
  const hypothesisSource = fs.readFileSync(hypothesisScreenPath, "utf8");

  const builderSection = reviewStateSource.slice(
    reviewStateSource.indexOf("const recordBuilderSetup"),
    reviewStateSource.indexOf("const clearDownstreamReviewState")
  );
  assert.match(builderSection, /candidateGeneration: undefined/);
  assert.match(builderSection, /comparisonResult: undefined/);
  assert.match(builderSection, /verdictResult: undefined/);
  assert.match(builderSection, /reportResult: undefined/);
  assert.match(builderSection, /candidateReady: false/);
  assert.match(builderSection, /comparisonReady: false/);
  assert.match(builderSection, /verdictReady: false/);

  const candidateSection = reviewStateSource.slice(
    reviewStateSource.indexOf("const recordCandidateGeneration"),
    reviewStateSource.indexOf("const recordComparisonResult")
  );
  assert.match(candidateSection, /candidateReady: isCompareReadyCandidateGeneration\(summary\)/);
  assert.match(candidateSection, /comparisonResult: undefined/);
  assert.match(candidateSection, /verdictResult: undefined/);
  assert.match(candidateSection, /reportResult: undefined/);
  assert.match(candidateSection, /comparisonReady: false/);
  assert.match(candidateSection, /verdictReady: false/);

  const comparisonSection = reviewStateSource.slice(
    reviewStateSource.indexOf("const recordComparisonResult"),
    reviewStateSource.indexOf("const recordVerdictResult")
  );
  assert.match(comparisonSection, /verdictResult: undefined/);
  assert.match(comparisonSection, /reportResult: undefined/);
  assert.match(comparisonSection, /verdictReady: false/);

  const verdictSection = reviewStateSource.slice(
    reviewStateSource.indexOf("const recordVerdictResult"),
    reviewStateSource.indexOf("const recordReportResult")
  );
  assert.match(verdictSection, /reportResult: undefined/);

  const hypothesisResetSection = hypothesisSource.slice(
    hypothesisSource.indexOf("const key = ["),
    hypothesisSource.indexOf("function handleSelectCard")
  );
  assert.match(hypothesisResetSection, /builderSettingsKey\(builderSettings\)/);
  assert.match(hypothesisResetSection, /clearDownstreamReviewState\(\)/);
});

test("candidate generation hands off weights to Comparison instead of rendering them in Hypothesis", () => {
  const hypothesisSource = fs.readFileSync(hypothesisScreenPath, "utf8");
  const hypothesisModelSource = fs.readFileSync(hypothesisScreenModelPath, "utf8");
  const comparisonSource = fs.readFileSync(comparisonScreenPath, "utf8");

  assert.match(hypothesisSource, /router\.push\("\/comparison"\)/);
  assert.match(hypothesisSource, /router\.push\("\/hypothesis\?sample=1&generated=1"\)/);
  assert.doesNotMatch(hypothesisSource, /router\.push\("\/comparison\?sample=1"\)/);
  assert.match(hypothesisModelSource, /Continue to Comparison/);
  assert.match(hypothesisModelSource, /Select one diagnosis-led test candidate before Current vs Candidate Comparison/);
  assert.doesNotMatch(hypothesisSource, /View weights/);
  assert.match(comparisonSource, /Current portfolio vs/);
  assert.match(comparisonSource, /AllocationList/);
  assert.match(comparisonSource, /weightUnit="percent"/);
  assert.match(comparisonSource, /weightUnit="fraction"/);
  assert.match(comparisonSource, /Retry comparison/);
  assert.match(comparisonSource, /candidateGeneration\?\.generatedAt/);
  assert.match(comparisonSource, /void handleRunComparison\(\)/);
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
