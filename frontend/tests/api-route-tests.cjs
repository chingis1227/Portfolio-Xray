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
const journeyPath = path.resolve(frontendRoot, "lib", "journey.ts");
const clientFitContextCardPath = path.resolve(frontendRoot, "components", "client-fit", "ClientFitContextCard.tsx");
const hypothesisPagePath = path.resolve(frontendRoot, "app", "hypothesis", "page.tsx");
const comparisonPagePath = path.resolve(frontendRoot, "app", "comparison", "page.tsx");
const verdictPagePath = path.resolve(frontendRoot, "app", "verdict", "page.tsx");

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
      const tsPath = fs.existsSync(`${aliasedPath}.ts`) ... `${aliasedPath}.ts` : aliasedPath;
      return loadTsModule(tsPath, { readFileImpl, moduleCache });
    }
    if (specifier.startsWith(".")) {
      const relativePath = path.resolve(path.dirname(resolvedPath), specifier);
      const tsPath = fs.existsSync(`${relativePath}.ts`) ... `${relativePath}.ts` : relativePath;
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
  const root = path.resolve(process.cwd(), "..");
  const expectedPath = path.join(root, "runs", "frontend_review_ok", "analysis_subject", "portfolio_alternatives_builder.json");
  const route = loadRoute({
    async readFileImpl(filePath, encoding) {
      assert.equal(filePath, expectedPath);
      assert.equal(encoding, "utf8");
      return JSON.stringify({
        selected_card_id: "card_equal_weight",
        can_generate_candidate: true,
        builder_prefill: { suggested_method: "equal_weight" },
        candidate_setup: { candidate_setup_id: "candidate_setup_card_equal_weight", can_generate_candidate: true }
      });
    }
  });

  await withMockFetch(async () => Response.json(fastApiEnvelope()), async () => {
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

test("diagnosis route maps instrument and cash rows into the FastAPI create-review contract", async () => {
  const root = path.resolve(process.cwd(), "..");
  const expectedPath = path.join(root, "runs", "frontend_review_cash", "review_result.json");
  const calls = [];
  const route = loadRoute({
    routePath: diagnoseRoutePath,
    async readFileImpl(filePath, encoding) {
      assert.equal(filePath, expectedPath);
      assert.equal(encoding, "utf8");
      return JSON.stringify({
        review_id: "frontend_review_cash",
        status: "completed",
        portfolio_input: { investor_currency: "USD", holdings: [] },
        outputs: {}
      });
    }
  });

  await withMockFetch(async (url, options) => {
    calls.push({ url, options });
    return Response.json(fastApiEnvelope({ review_id: "frontend_review_cash", lineage: { review_id: "frontend_review_cash" } }));
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
    assert.equal(calls.length, 1);
    assert.match(calls[0].url, /\/api\/v1\/reviews$/);
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
});

test("diagnosis route forwards completed Client Fit profile into the FastAPI create-review contract", async () => {
  const root = path.resolve(process.cwd(), "..");
  const expectedPath = path.join(root, "runs", "frontend_review_client_fit", "review_result.json");
  const calls = [];
  const route = loadRoute({
    routePath: diagnoseRoutePath,
    async readFileImpl(filePath, encoding) {
      assert.equal(filePath, expectedPath);
      assert.equal(encoding, "utf8");
      return JSON.stringify({
        review_id: "frontend_review_client_fit",
        status: "completed",
        portfolio_input: { investor_currency: "USD", holdings: [] },
        outputs: {}
      });
    }
  });

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
    return Response.json(fastApiEnvelope({ review_id: "frontend_review_client_fit", lineage: { review_id: "frontend_review_client_fit" } }));
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
  });
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

test("review recovery route validates review id and path separators", async () => {
  const route = loadRoute({ routePath: reviewRecoverRoutePath });

  await withMockFetch(async () => {
    throw new Error("fetch was not expected");
  }, async () => {
    const result = await responseJson(await route.GET(new Request("http://localhost/api/portfolio/review/recover...review_id=../bad")));

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

  await withMockFetch(async (url, options) => {
    assert.match(url, /\/api\/v1\/reviews\/frontend_review_recover_ok$/);
    assert.equal(options.method, "GET");
    return Response.json(fastApiEnvelope({
      review_id: "frontend_review_recover_ok",
      stage: "recovery",
      lineage: { review_id: "frontend_review_recover_ok" }
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
    assert.equal(result.body.review_result.outputs.portfolio_xray.version, "portfolio_xray_v2");
    assert.equal(result.body.review_result.outputs.portfolio_alternatives_builder.selected_card_id, "card_ok");
    assert.equal(result.body.review_result.outputs.candidate_generation, undefined);
    assert.equal(result.body.review_result.outputs.current_vs_candidate, undefined);
    assert.equal(result.body.review_result.outputs.decision_verdict, undefined);
    assert.equal(result.body.review_result.paths.current_vs_candidate, undefined);
  });
});

test("candidate route rejects FastAPI lineage from a different active review before trusting downstream artifacts", async () => {
  const root = path.resolve(process.cwd(), "..");
  const builderPath = path.join(root, "runs", "frontend_review_user_a", "analysis_subject", "portfolio_alternatives_builder.json");
  const candidatePath = path.join(root, "runs", "frontend_review_user_a", "candidate_generation.json");
  const reads = [];
  const route = loadRoute({
    routePath: candidateGenerateRoutePath,
    async readFileImpl(filePath, encoding) {
      reads.push(filePath);
      assert.equal(encoding, "utf8");
      if (filePath === builderPath) {
        return JSON.stringify({
          selected_card_id: "card_equal_weight",
          builder_prefill: { source_card_id: "card_equal_weight" },
          candidate_setup: {
            candidate_setup_id: "candidate_setup_card_equal_weight",
            source_card_id: "card_equal_weight"
          }
        });
      }
      if (filePath === candidatePath) {
        throw new Error("candidate_generation.json must not be trusted after a FastAPI lineage mismatch");
      }
      throw new Error(`unexpected read ${filePath}`);
    }
  });

  await withMockFetch(async (url, options) => {
    assert.match(url, /\/api\/v1\/reviews\/frontend_review_user_a\/candidate$/);
    assert.equal(options.method, "POST");
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
      selected_card_id: "card_equal_weight"
    }, "http://localhost/api/portfolio/candidate/generate")));

    assert.equal(result.status, 409);
    assert.equal(result.body.status, "failed");
    assert.equal(result.body.stage, "candidate_generation");
    assert.match(result.body.error, /lineage did not match/);
    assert.match(result.body.details.join(" "), /review_id mismatch/);
    assert.deepEqual(reads, [builderPath]);
  });
});

test("report route returns a display model from the FastAPI public envelope", async () => {
  const root = path.resolve(process.cwd(), "..");
  const files = {
    [path.join(root, "runs", "frontend_review_report_ok", "candidate_generation.json")]: {
      selected_card_id: "card_equal_weight",
      candidate: { candidate_id: "equal_weight" },
      handoff_to_comparison: { candidate_id: "equal_weight", can_compare: true }
    },
    [path.join(root, "runs", "frontend_review_report_ok", "decision_verdict.json")]: {
      verdict_id: "no_material_rebalance_recommended"
    },
    [path.join(root, "runs", "frontend_review_report_ok", "ai_commentary_context.json")]: {
      client_explanation_draft: { sentences: [] }
    }
  };
  const route = loadRoute({
    routePath: reportGenerateRoutePath,
    async readFileImpl(filePath, encoding) {
      assert.equal(encoding, "utf8");
      assert.ok(Object.prototype.hasOwnProperty.call(files, filePath), `unexpected read ${filePath}`);
      return JSON.stringify(files[filePath]);
    }
  });

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
      selected_card_id: "card_equal_weight"
    }, "http://localhost/api/portfolio/report/generate")));

    assert.equal(result.status, 200);
    assert.equal(result.body.status, "completed");
    assert.equal(result.body.stage, "report_commentary");
    assert.equal(result.body.report_display_model.title, "Grounded client-ready report summary");
    assert.match(result.body.report_display_model.sections.map((section) => section.body).join(" "), /Diagnosis summary from the public API/);
    assert.deepEqual(result.body.report_display_model.evidenceUsed.slice(0, 2), [
      "Portfolio X-Ray diagnosis",
      "decision evidence"
    ]);
    assert.match(result.body.report_display_model.boundaryNote, /Decision-support only from FastAPI context/);
    assert.ok(result.body.report_display_model.evidenceUsed.includes("main diagnosis"));
    assert.ok(result.body.report_display_model.evidenceUsed.includes("comparison evidence"));
    assert.equal(result.body.fastapi_envelope.data.llm_generated, false);
  });
});
