import { readFile } from "node:fs/promises";
import path from "node:path";
import { NextResponse } from "next/server";
import type { ReportResponse } from "@/lib/generated/api-types";

const FASTAPI_TIMEOUT_MS = 15 * 60 * 1000;
const WEIGHT_TOLERANCE = 0.01;

export type PortfolioPayload = {
  investor_currency?: unknown;
  holdings?: unknown;
  client_fit?: unknown;
  mode?: unknown;
};

type ValidatedHolding =
  | { type: "instrument"; ticker: string; weight: number }
  | { type: "cash"; currency: string; weight: number };

type ValidatedPayload = {
  investor_currency: string;
  holdings: ValidatedHolding[];
  client_fit?: Record<string, unknown>;
};

export type StageRequest = {
  review_id?: unknown;
  selected_card_id?: unknown;
};

type FastApiCallResult = {
  ok: boolean;
  status: number;
  body: unknown;
};

type ExpectedFastApiLineage = {
  reviewId?: string;
  selectedCardId?: string;
  candidateId?: string;
  comparisonId?: string;
  verdictId?: string;
};

function projectRoot() {
  return path.resolve(process.cwd(), "..");
}

function fastApiBaseUrl() {
  return (process.env.PMRI_FASTAPI_BASE_URL || "http://127.0.0.1:8000").replace(/\/+$/, "");
}

export function jsonError(message: string, status = 400, details: string[] | string = []) {
  return NextResponse.json(
    {
      status: "failed",
      error: message,
      details
    },
    { status }
  );
}

function isRecord(value: unknown): value is Record<string, unknown> {
  return Boolean(value) && typeof value === "object" && !Array.isArray(value);
}

function textValue(value: unknown, fallback = "") {
  return typeof value === "string" && value.trim() ? value.trim() : fallback;
}

function stringArray(value: unknown): string[] {
  return Array.isArray(value)
    ? value.map((item) => (typeof item === "string" ? item.trim() : "")).filter(Boolean)
    : [];
}

function parseJsonWithNonFinite(raw: string) {
  return JSON.parse(
    raw
      .replace(/-Infinity\b/g, "null")
      .replace(/\bNaN\b/g, "null")
      .replace(/\bInfinity\b/g, "null")
  ) as unknown;
}

function scrubForClient(value: string, root = projectRoot()) {
  if (!value) return "";
  return value
    .slice(-4000)
    .replaceAll(root, "[project]")
    .replaceAll(root.replaceAll("\\", "/"), "[project]")
    .replace(/\[project\][\\/][^\s'")<>]+/g, "[path]")
    .replace(/Traceback \(most recent call last\):[\s\S]*/g, "Backend failure details were captured safely.")
    .replace(/File "[^"]+", line \d+(?:, in [^\r\n]+)?/g, "Backend file reference hidden.")
    .replace(/[A-Za-z]:[\\/][^\s'")<>]+/g, "[path]")
    .replace(/\/(?:Users|home|var|tmp|mnt)\/[^\s'")<>]+/g, "[path]")
    .trim();
}

function safeDetails(value: unknown): string[] {
  if (Array.isArray(value)) {
    return value.map((item) => (typeof item === "string" ? scrubForClient(item) : "")).filter(Boolean);
  }
  if (typeof value === "string" && value.trim()) return [scrubForClient(value)];
  return [];
}

function legacyErrorFromFastApi(body: unknown, fallback: string) {
  const envelope = isRecord(body) ? body : {};
  const safeError = isRecord(envelope.safe_error) ? envelope.safe_error : {};
  const message = textValue(safeError.message, textValue(envelope.detail, fallback));
  const details = safeDetails(safeError.details);
  return {
    status: "failed",
    error: scrubForClient(message || fallback),
    details
  };
}

function numberValue(value: unknown) {
  return typeof value === "number" && Number.isFinite(value) ? value : null;
}

function validateClientFitRange(value: unknown, fieldName: string, errors: string[]) {
  if (!isRecord(value)) {
    errors.push(`client_fit.${fieldName} must be an object.`);
    return undefined;
  }
  const min = numberValue(value.min);
  const max = numberValue(value.max);
  if (min === null || max === null || min < 0 || max > 1 || min >= max) {
    errors.push(`client_fit.${fieldName} must satisfy 0 <= min < max <= 1.`);
    return undefined;
  }
  return { min, max };
}

function validateClientFitPayload(value: unknown): { clientFit?: Record<string, unknown>; clientFitErrors: string[] } {
  if (value === undefined || value === null) return { clientFitErrors: [] };
  const clientFitErrors: string[] = [];
  if (!isRecord(value)) return { clientFitErrors: ["client_fit must be an object."] };

  const source = textValue(value.source);
  const sourceQuality = textValue(value.source_quality);
  if (!["questionnaire", "preset_override", "manual_override", "imported", "missing"].includes(source)) {
    clientFitErrors.push("client_fit.source is invalid.");
  }
  if (!["high", "medium", "low", "missing"].includes(sourceQuality)) {
    clientFitErrors.push("client_fit.source_quality is invalid.");
  }
  if (source === "missing" || sourceQuality === "missing") {
    clientFitErrors.push("The web diagnosis requires a completed Client Fit profile.");
  }

  const presetId = textValue(value.preset_id);
  if (presetId && !["ultra_conservative", "conservative", "balanced", "growth", "aggressive"].includes(presetId)) {
    clientFitErrors.push("client_fit.preset_id is invalid.");
  }
  const horizonYears = numberValue(value.horizon_years);
  if (value.horizon_years !== undefined && value.horizon_years !== null && (horizonYears === null || horizonYears <= 0)) {
    clientFitErrors.push("client_fit.horizon_years must be a positive number.");
  }
  const targetReturnRange = value.target_return_range === undefined || value.target_return_range === null
    ? undefined
    : validateClientFitRange(value.target_return_range, "target_return_range", clientFitErrors);
  const targetVolRange = value.target_vol_range === undefined || value.target_vol_range === null
    ? undefined
    : validateClientFitRange(value.target_vol_range, "target_vol_range", clientFitErrors);
  const drawdown = numberValue(value.target_max_drawdown_pct);
  if (value.target_max_drawdown_pct !== undefined && value.target_max_drawdown_pct !== null && (drawdown === null || drawdown < -1 || drawdown > 0)) {
    clientFitErrors.push("client_fit.target_max_drawdown_pct must be a decimal from -1 to 0.");
  }
  if (!presetId && (!targetReturnRange || !targetVolRange || drawdown === null || horizonYears === null || horizonYears <= 0)) {
    clientFitErrors.push("client_fit requires preset_id or complete manual targets.");
  }
  if (clientFitErrors.length) return { clientFitErrors };

  return {
    clientFit: {
      preset_id: presetId || null,
      source,
      source_quality: sourceQuality,
      source_quality_reason: textValue(value.source_quality_reason) || null,
      horizon_years: horizonYears,
      target_return_range: targetReturnRange ?? null,
      target_vol_range: targetVolRange ?? null,
      target_max_drawdown_pct: drawdown
    },
    clientFitErrors
  };
}

async function callFastApi(method: "GET" | "POST", apiPath: string, body?: unknown): Promise<FastApiCallResult> {
  const controller = new AbortController();
  const timeout = setTimeout(() => controller.abort(), FASTAPI_TIMEOUT_MS);
  const url = `${fastApiBaseUrl()}${apiPath}`;
  try {
    const response = await fetch(url, {
      method,
      headers: body === undefined ? undefined : { "Content-Type": "application/json" },
      body: body === undefined ? undefined : JSON.stringify(body),
      signal: controller.signal
    });
    const responseText = await response.text();
    const parsed = responseText ? parseJsonWithNonFinite(responseText) : null;
    return { ok: response.ok, status: response.status, body: parsed };
  } catch (error) {
    const unavailable = error instanceof Error && error.name === "AbortError"
      ? "FastAPI backend request timed out."
      : "FastAPI backend is unavailable. Start it with uvicorn src.api.app:app --host 127.0.0.1 --port 8000.";
    return {
      ok: false,
      status: error instanceof Error && error.name === "AbortError" ? 504 : 503,
      body: {
        safe_error: {
          message: unavailable,
          details: []
        }
      }
    };
  } finally {
    clearTimeout(timeout);
  }
}

function validatePortfolioPayload(body: PortfolioPayload): { payload?: ValidatedPayload; errors: string[] } {
  const errors: string[] = [];
  const investorCurrency = typeof body.investor_currency === "string"
    ? body.investor_currency.trim().toUpperCase()
    : "";

  if (!investorCurrency) errors.push("investor_currency is required.");
  if (investorCurrency && !["USD", "EUR"].includes(investorCurrency)) {
    errors.push("investor_currency must be USD or EUR.");
  }

  if (!Array.isArray(body.holdings)) {
    errors.push("holdings array is required.");
    return { errors };
  }
  if (body.holdings.length < 2) errors.push("At least 2 holdings are required.");

  const holdings: ValidatedHolding[] = [];
  let totalWeight = 0;

  body.holdings.forEach((rawHolding, index) => {
    if (!rawHolding || typeof rawHolding !== "object" || Array.isArray(rawHolding)) {
      errors.push(`holding[${index}] must be an object.`);
      return;
    }
    const row = rawHolding as Record<string, unknown>;
    const weight = typeof row.weight === "number" && Number.isFinite(row.weight) ? row.weight : Number.NaN;
    if (!(weight > 0)) {
      errors.push(`holding[${index}].weight must be greater than 0.`);
      return;
    }
    totalWeight += weight;

    if (row.type === "instrument") {
      const ticker = typeof row.ticker === "string" ? row.ticker.trim().toUpperCase() : "";
      if (!ticker) {
        errors.push(`holding[${index}] instrument row requires ticker.`);
        return;
      }
      holdings.push({ type: "instrument", ticker, weight });
      return;
    }

    if (row.type === "cash") {
      const currency = typeof row.currency === "string" ? row.currency.trim().toUpperCase() : "";
      if (!currency) {
        errors.push(`holding[${index}] cash row requires currency.`);
        return;
      }
      if (!["USD", "EUR"].includes(currency)) {
        errors.push(`holding[${index}] cash currency must be USD or EUR.`);
        return;
      }
      holdings.push({ type: "cash", currency, weight });
      return;
    }

    errors.push(`holding[${index}].type must be "instrument" or "cash".`);
  });

  if (Math.abs(totalWeight - 100) > WEIGHT_TOLERANCE) {
    errors.push(`Total weight must equal 100 within ${WEIGHT_TOLERANCE}; got ${totalWeight}.`);
  }

  if (errors.length) return { errors };
  const { clientFit, clientFitErrors } = validateClientFitPayload(body.client_fit);
  errors.push(...clientFitErrors);
  if (errors.length) return { errors };
  return { payload: { investor_currency: investorCurrency, holdings, client_fit: clientFit }, errors };
}

function fastApiCreateReviewBody(payload: ValidatedPayload) {
  const body: Record<string, unknown> = {
    portfolio: {
      investor_currency: payload.investor_currency,
      holdings: payload.holdings.map((holding) => holding.type === "cash"
        ? { type: "cash", currency: holding.currency, weight_pct: holding.weight }
        : { type: "instrument", ticker: holding.ticker, weight_pct: holding.weight })
    },
    options: {
      mode: "diagnosis_only",
      output_profile: "site_api",
      sample_mode: false
    }
  };
  if (payload.client_fit) body.client_fit = payload.client_fit;
  return body;
}

export function validateStageRequest(body: StageRequest) {
  const reviewId = typeof body.review_id === "string" ? body.review_id.trim() : "";
  const selectedCardId = typeof body.selected_card_id === "string" ? body.selected_card_id.trim() : "";
  const errors: string[] = [];

  if (!reviewId) errors.push("review_id is required.");
  if (!selectedCardId) errors.push("selected_card_id is required.");
  if (reviewId && !reviewId.startsWith("frontend_review_")) errors.push("review_id must be a frontend_review_* id.");
  if (reviewId && path.basename(reviewId) !== reviewId) errors.push("review_id must not contain path separators.");

  return { reviewId, selectedCardId, errors };
}

function validateReviewId(value: unknown) {
  const reviewId = typeof value === "string" ? value.trim() : "";
  const errors: string[] = [];
  if (!reviewId) errors.push("review_id is required.");
  if (reviewId && !reviewId.startsWith("frontend_review_")) errors.push("review_id must be a frontend_review_* id.");
  if (reviewId && path.basename(reviewId) !== reviewId) errors.push("review_id must not contain path separators.");
  return { reviewId, errors };
}

function runDirForReview(reviewId: string) {
  const runsRoot = path.resolve(projectRoot(), "runs");
  const runDir = path.resolve(runsRoot, reviewId);
  const relative = path.relative(runsRoot, runDir);
  if (relative.startsWith("..") || path.isAbsolute(relative)) return null;
  return runDir;
}

async function readRunJson(reviewId: string, relativePath: string): Promise<unknown> {
  const runDir = runDirForReview(reviewId);
  if (!runDir) throw new Error("review_id must stay inside the runs directory.");
  const target = path.resolve(runDir, relativePath);
  const relative = path.relative(runDir, target);
  if (relative.startsWith("..") || path.isAbsolute(relative)) {
    throw new Error("artifact path must stay inside the review run directory.");
  }
  return parseJsonWithNonFinite(await readFile(target, "utf8"));
}

async function readOptionalRunJson(reviewId: string, relativePath: string): Promise<unknown | undefined> {
  try {
    return await readRunJson(reviewId, relativePath);
  } catch {
    return undefined;
  }
}

function artifactPath(reviewId: string, relativePath: string) {
  return `runs/${reviewId}/${relativePath.replaceAll("\\", "/")}`;
}

function selectedBuilderSetupId(builderDocument: unknown) {
  const builder = isRecord(builderDocument) ? builderDocument : {};
  const candidateSetup = isRecord(builder.candidate_setup) ? builder.candidate_setup : {};
  return textValue(candidateSetup.candidate_setup_id, textValue(candidateSetup.setup_id, ""));
}

function selectedCardFromBuilder(builderDocument: unknown) {
  const builder = isRecord(builderDocument) ? builderDocument : {};
  const builderPrefill = isRecord(builder.builder_prefill) ? builder.builder_prefill : {};
  const candidateSetup = isRecord(builder.candidate_setup) ? builder.candidate_setup : {};
  return textValue(builder.selected_card_id, textValue(builderPrefill.source_card_id, textValue(candidateSetup.source_card_id, "")));
}

function lineageMismatchError(stage: string, reviewId: string, selectedCardId: string, actualCardId: string) {
  return NextResponse.json({
    status: "failed",
    stage,
    review_id: reviewId,
    selected_card_id: selectedCardId,
    error: "Selected Launchpad card does not match the active run-local stage artifact.",
    details: [`Expected ${selectedCardId}; found ${actualCardId}. Return to Hypothesis and prepare the selected test again.`]
  }, { status: 409 });
}

function candidateFromGeneration(candidateGeneration: unknown) {
  const generation = isRecord(candidateGeneration) ? candidateGeneration : {};
  const candidate = isRecord(generation.candidate) ? generation.candidate : {};
  const handoff = isRecord(generation.handoff_to_comparison) ? generation.handoff_to_comparison : {};
  return {
    selectedCardId: textValue(generation.selected_card_id, textValue(candidate.source_card_id, textValue(isRecord(generation.source_builder_setup) ? generation.source_builder_setup.source_card_id : undefined, ""))),
    candidateId: textValue(handoff.candidate_id, textValue(candidate.candidate_id, textValue(isRecord(generation.method_availability) ? generation.method_availability.backend_candidate_id : undefined, ""))),
    generationStatus: textValue(generation.generation_status, textValue(candidate.status, "unknown")),
    canCompare: handoff.can_compare === true
  };
}

function verdictIdFromDocument(decisionVerdict: unknown) {
  const verdict = isRecord(decisionVerdict) ? decisionVerdict : {};
  return textValue(verdict.verdict_id, textValue(verdict.decision_verdict_id, "unknown"));
}

function fastApiLineageValue(body: unknown, key: string) {
  const envelope = isRecord(body) ? body : {};
  const lineage = isRecord(envelope.lineage) ? envelope.lineage : {};
  return textValue(lineage[key], textValue(envelope[key], ""));
}

function fastApiLineageErrors(body: unknown, expected: ExpectedFastApiLineage) {
  const checks: Array<[string, string | undefined]> = [
    ["review_id", expected.reviewId],
    ["selected_card_id", expected.selectedCardId],
    ["candidate_id", expected.candidateId],
    ["comparison_id", expected.comparisonId],
    ["verdict_id", expected.verdictId]
  ];
  const errors: string[] = [];
  for (const [key, expectedValue] of checks) {
    if (!expectedValue) continue;
    const actual = fastApiLineageValue(body, key);
    if (actual && actual !== expectedValue) {
      errors.push(`${key} mismatch: expected ${expectedValue}; FastAPI returned ${actual}.`);
    }
  }
  return errors;
}

function fastApiLineageMismatchResponse(stage: string, expected: ExpectedFastApiLineage, details: string[]) {
  return NextResponse.json({
    status: "failed",
    stage,
    review_id: expected.reviewId,
    selected_card_id: expected.selectedCardId,
    candidate_id: expected.candidateId,
    error: "FastAPI response lineage did not match the active frontend review.",
    details: details.map((detail) => scrubForClient(detail))
  }, { status: 409 });
}

function sourceEvidenceLabel(key: string) {
  const normalizedKey = key.replace(/\.json$/i, "");
  const labels: Record<string, string> = {
    portfolio_xray: "Portfolio X-Ray diagnosis",
    stress_report: "Stress Test Lab evidence",
    problem_classification: "main diagnosis",
    candidate_launchpad: "selected test path",
    portfolio_alternatives_builder: "selected test setup",
    candidate_generation: "generated test candidate",
    current_vs_candidate: "comparison evidence",
    decision_verdict: "decision evidence",
    ai_commentary_context: "grounding context",
    site_explanation_bundle: "screen explanation"
  };
  return labels[normalizedKey] || normalizedKey.replaceAll("_", " ");
}

function reportDisplayModelFromFastApi(envelope: ReportResponse | Record<string, unknown>) {
  const data = isRecord(envelope.data) ? envelope.data : {};
  const preview = isRecord(data.report_preview) ? data.report_preview : {};
  const grounding = isRecord(data.grounding) ? data.grounding : {};
  const evidenceChainContext = isRecord(data.evidence_chain_context) ? data.evidence_chain_context : {};
  const sourceRefs = Array.isArray(grounding.source_refs) ? grounding.source_refs.filter(isRecord) : [];
  const sections = [
    { title: "Executive summary", body: textValue(preview.executive_summary, "") },
    { title: "Current portfolio diagnosis", body: textValue(preview.current_portfolio_diagnosis, textValue(evidenceChainContext.diagnosis_statement, "")) },
    ...stringArray(preview.stress_evidence).map((body) => ({ title: "Stress evidence", body })),
    { title: "Tested hypothesis", body: textValue(preview.tested_hypothesis, textValue(evidenceChainContext.tested_hypothesis, "")) },
    { title: "Candidate boundary", body: textValue(preview.candidate_boundary, textValue(evidenceChainContext.candidate_boundary, "")) },
    ...stringArray(preview.comparison_tradeoffs).map((body) => ({ title: "Comparison trade-offs", body })),
    { title: "Decision verdict", body: textValue(preview.verdict_explanation, "") }
  ].filter((section) => section.body);
  const unavailable = stringArray(grounding.unavailable_sections).map(sourceEvidenceLabel);
  const contextSources = stringArray(evidenceChainContext.source_artifacts).map(sourceEvidenceLabel);
  return {
    title: "Grounded client-ready report summary",
    subtitle: "Active review report preview grounded in the current diagnosis, candidate test, comparison, and verdict evidence.",
    sections: sections.length ? sections : [
      {
        title: "Partial explanation",
        body: "Grounded report inputs were available, but no client-readable summary sections were returned."
      }
    ],
    evidenceUsed: sourceRefs
      .map((ref) => sourceEvidenceLabel(textValue(ref.kind, "")))
      .filter(Boolean)
      .concat(contextSources)
      .filter((item, index, items) => item && items.indexOf(item) === index),
    unavailableEvidence: unavailable.length ? unavailable : ["No unsupported sections were added beyond the available review evidence."],
    nextObservation: textValue(preview.monitoring_note, "Retest if diagnosis, comparison, or verdict evidence changes."),
    boundaryNote: textValue(evidenceChainContext.recommendation_boundary, "Decision-support only. This preview explains available evidence and does not provide suitability, tax, or trade advice."),
    warnings: stringArray(envelope.warnings).concat(stringArray(preview.evidence_limitations)),
    clientFit: isRecord(data.client_fit) ? data.client_fit : undefined,
    generatedAt: new Date().toISOString()
  };
}

export async function diagnoseViaFastApi(request: Request) {
  let body: PortfolioPayload;
  try {
    body = await request.json() as PortfolioPayload;
  } catch {
    return jsonError("Request body must be valid JSON.");
  }

  const { payload, errors } = validatePortfolioPayload(body);
  if (!payload) return jsonError("Portfolio input validation failed.", 400, errors);

  const api = await callFastApi("POST", "/api/v1/reviews", fastApiCreateReviewBody(payload));
  if (!api.ok) {
    return NextResponse.json(legacyErrorFromFastApi(api.body, "Portfolio diagnosis failed."), { status: api.status });
  }

  const envelope = isRecord(api.body) ? api.body : {};
  const reviewId = textValue(envelope.review_id, textValue(isRecord(envelope.lineage) ? envelope.lineage.review_id : undefined, ""));
  if (!reviewId) return jsonError("FastAPI diagnosis did not return a review id.", 500);
  const reviewValidation = validateReviewId(reviewId);
  if (reviewValidation.errors.length) {
    return jsonError("FastAPI diagnosis returned an invalid review id.", 500, reviewValidation.errors);
  }

  try {
    const reviewResult = await readRunJson(reviewId, "review_result.json");
    return NextResponse.json(isRecord(reviewResult)
      ? { ...reviewResult, fastapi_envelope: api.body }
      : reviewResult);
  } catch (error) {
    return jsonError("FastAPI diagnosis completed but the run-local review_result.json could not be read.", 500, [
      scrubForClient(error instanceof Error ? error.message : String(error))
    ]);
  }
}

function sanitizeRecoveredReviewResult(value: unknown, reviewId: string) {
  if (!isRecord(value)) return null;
  if (value.review_id !== reviewId || value.status !== "completed") return null;

  const outputs = isRecord(value.outputs) ? value.outputs : {};
  const allowedOutputs = Object.fromEntries(
    Object.entries(outputs).filter(([key]) => [
      "portfolio_xray",
      "stress_report",
      "run_metadata",
      "output_manifest",
      "problem_classification",
      "candidate_launchpad",
      "portfolio_alternatives_builder",
      "ai_commentary_context",
      "site_explanation_bundle"
    ].includes(key))
  );

  const paths = isRecord(value.paths) ? value.paths : {};
  const allowedPaths = Object.fromEntries(
    Object.entries(paths).filter(([key, item]) => (
      typeof item === "string"
      && [
        "run_dir",
        "portfolio_xray",
        "stress_report",
        "run_metadata",
        "output_manifest",
        "problem_classification",
        "candidate_launchpad",
        "portfolio_alternatives_builder",
        "ai_commentary_context",
        "site_explanation_bundle"
      ].includes(key)
    ))
  );

  return {
    ...value,
    paths: allowedPaths,
    outputs: allowedOutputs
  };
}

export async function recoverViaFastApi(reviewIdInput: unknown) {
  const { reviewId, errors } = validateReviewId(reviewIdInput);
  if (errors.length) return jsonError("Review recovery request validation failed.", 400, errors);

  const api = await callFastApi("GET", `/api/v1/reviews/${encodeURIComponent(reviewId)}`);
  if (!api.ok) {
    return NextResponse.json(legacyErrorFromFastApi(api.body, "Review recovery failed."), { status: api.status });
  }
  const recoveryLineageErrors = fastApiLineageErrors(api.body, { reviewId });
  if (recoveryLineageErrors.length) {
    return fastApiLineageMismatchResponse("review_recovery", { reviewId }, recoveryLineageErrors);
  }

  try {
    const reviewResult = await readRunJson(reviewId, "review_result.json");
    const sanitized = sanitizeRecoveredReviewResult(reviewResult, reviewId);
    if (!sanitized) return jsonError("Run-local review_result.json is not a completed matching frontend review.", 409);
    return NextResponse.json({
      status: "completed",
      stage: "review_recovery",
      review_id: reviewId,
      fastapi_envelope: api.body,
      recovery: {
        source: "fastapi_v1_review_recovery",
        restored_active_stages: ["diagnosis", "evidence", "hypothesis_setup"],
        downstream_artifacts_restored_as_active: false,
        note: "Candidate, comparison, verdict, and report artifacts are not restored as active state during recovery."
      },
      review_result: sanitized
    });
  } catch (error) {
    return jsonError("No recoverable run-local review_result.json was found for this review_id.", 404, [
      scrubForClient(error instanceof Error ? error.message : String(error))
    ]);
  }
}

export async function builderViaFastApi(request: Request) {
  let body: StageRequest;
  try {
    body = await request.json() as StageRequest;
  } catch {
    return jsonError("Request body must be valid JSON.");
  }
  const { reviewId, selectedCardId, errors } = validateStageRequest(body);
  if (errors.length) return jsonError("Builder setup prepare request validation failed.", 400, errors);

  const api = await callFastApi("POST", `/api/v1/reviews/${encodeURIComponent(reviewId)}/builder`, {
    selected_card_id: selectedCardId,
    overrides: {}
  });
  if (!api.ok) {
    return NextResponse.json({
      ...legacyErrorFromFastApi(api.body, "Builder setup prepare failed."),
      stage: "builder_setup",
      review_id: reviewId,
      selected_card_id: selectedCardId
    }, { status: api.status });
  }
  const builderLineageErrors = fastApiLineageErrors(api.body, { reviewId, selectedCardId });
  if (builderLineageErrors.length) {
    return fastApiLineageMismatchResponse("builder_setup", { reviewId, selectedCardId }, builderLineageErrors);
  }

  try {
    const builderDocument = await readRunJson(reviewId, "analysis_subject/portfolio_alternatives_builder.json");
    const envelope = isRecord(api.body) ? api.body : {};
    const data = isRecord(envelope.data) ? envelope.data : {};
    return NextResponse.json({
      review_id: reviewId,
      status: "completed",
      stage: "builder_setup",
      selected_card_id: selectedCardId,
      fastapi_envelope: api.body,
      can_generate_candidate: data.candidate_generation_allowed === true,
      path: artifactPath(reviewId, "analysis_subject/portfolio_alternatives_builder.json"),
      portfolio_alternatives_builder: builderDocument
    });
  } catch (error) {
    return jsonError("Builder setup prepare finished but the result could not be read.", 500, [
      scrubForClient(error instanceof Error ? error.message : String(error))
    ]);
  }
}

export async function candidateViaFastApi(request: Request) {
  let body: StageRequest;
  try {
    body = await request.json() as StageRequest;
  } catch {
    return jsonError("Request body must be valid JSON.");
  }
  const { reviewId, selectedCardId, errors } = validateStageRequest(body);
  if (errors.length) return jsonError("Candidate generation request validation failed.", 400, errors);

  let builderDocument: unknown;
  try {
    builderDocument = await readRunJson(reviewId, "analysis_subject/portfolio_alternatives_builder.json");
  } catch (error) {
    return jsonError("Candidate generation requires a prepared Builder setup for this review.", 409, [
      scrubForClient(error instanceof Error ? error.message : String(error))
    ]);
  }
  const builderCardId = selectedCardFromBuilder(builderDocument);
  if (builderCardId && builderCardId !== selectedCardId) {
    return lineageMismatchError("candidate_generation", reviewId, selectedCardId, builderCardId);
  }
  const builderSetupId = selectedBuilderSetupId(builderDocument);
  if (!builderSetupId) return jsonError("Candidate generation requires a Builder setup id.", 409);

  const api = await callFastApi("POST", `/api/v1/reviews/${encodeURIComponent(reviewId)}/candidate`, {
    builder_setup_id: builderSetupId
  });
  if (!api.ok) {
    return NextResponse.json({
      ...legacyErrorFromFastApi(api.body, "Candidate generation failed."),
      stage: "candidate_generation",
      review_id: reviewId,
      selected_card_id: selectedCardId
    }, { status: api.status });
  }
  const candidateLineageErrors = fastApiLineageErrors(api.body, { reviewId, selectedCardId });
  if (candidateLineageErrors.length) {
    return fastApiLineageMismatchResponse("candidate_generation", { reviewId, selectedCardId }, candidateLineageErrors);
  }

  try {
    const candidateGeneration = await readRunJson(reviewId, "candidate_generation.json");
    const candidate = candidateFromGeneration(candidateGeneration);
    return NextResponse.json({
      review_id: reviewId,
      status: "completed",
      stage: "candidate_generation",
      selected_card_id: selectedCardId || candidate.selectedCardId,
      candidate_id: candidate.candidateId,
      fastapi_envelope: api.body,
      generation_status: candidate.generationStatus,
      can_compare: candidate.canCompare,
      path: artifactPath(reviewId, "candidate_generation.json"),
      candidate_generation: candidateGeneration,
      candidate_factory_run: await readOptionalRunJson(reviewId, "candidate_factory_run.json")
    });
  } catch (error) {
    return jsonError("Candidate generation finished but the result could not be read.", 500, [
      scrubForClient(error instanceof Error ? error.message : String(error))
    ]);
  }
}

export async function comparisonViaFastApi(request: Request) {
  let body: StageRequest;
  try {
    body = await request.json() as StageRequest;
  } catch {
    return jsonError("Request body must be valid JSON.");
  }
  const { reviewId, selectedCardId, errors } = validateStageRequest(body);
  if (errors.length) return jsonError("Comparison request validation failed.", 400, errors);

  let candidateGeneration: unknown;
  try {
    candidateGeneration = await readRunJson(reviewId, "candidate_generation.json");
  } catch (error) {
    return jsonError("Comparison requires an active generated candidate for this review.", 409, [
      scrubForClient(error instanceof Error ? error.message : String(error))
    ]);
  }
  const candidate = candidateFromGeneration(candidateGeneration);
  if (candidate.selectedCardId && candidate.selectedCardId !== selectedCardId) {
    return lineageMismatchError("current_vs_candidate", reviewId, selectedCardId, candidate.selectedCardId);
  }
  if (!candidate.candidateId) return jsonError("Comparison requires a generated candidate id.", 409);

  const api = await callFastApi("POST", `/api/v1/reviews/${encodeURIComponent(reviewId)}/comparison`, {
    candidate_id: candidate.candidateId
  });
  if (!api.ok) {
    return NextResponse.json({
      ...legacyErrorFromFastApi(api.body, "Comparison failed."),
      stage: "current_vs_candidate",
      review_id: reviewId,
      selected_card_id: selectedCardId
    }, { status: api.status });
  }
  const comparisonLineageErrors = fastApiLineageErrors(api.body, {
    reviewId,
    selectedCardId,
    candidateId: candidate.candidateId
  });
  if (comparisonLineageErrors.length) {
    return fastApiLineageMismatchResponse("current_vs_candidate", {
      reviewId,
      selectedCardId,
      candidateId: candidate.candidateId
    }, comparisonLineageErrors);
  }

  try {
    const currentVsCandidate = await readRunJson(reviewId, "current_vs_candidate.json");
    const paths = {
      candidate_comparison: artifactPath(reviewId, "candidate_comparison.json"),
      current_vs_candidate: artifactPath(reviewId, "current_vs_candidate.json"),
      site_explanation_bundle: artifactPath(reviewId, "site_explanation_bundle.json")
    };
    return NextResponse.json({
      review_id: reviewId,
      status: "completed",
      stage: "current_vs_candidate",
      selected_card_id: selectedCardId || candidate.selectedCardId,
      candidate_id: candidate.candidateId,
      fastapi_envelope: api.body,
      paths,
      current_vs_candidate: currentVsCandidate,
      candidate_comparison: await readOptionalRunJson(reviewId, "candidate_comparison.json"),
      site_explanation_bundle: await readOptionalRunJson(reviewId, "site_explanation_bundle.json")
    });
  } catch (error) {
    return jsonError("Comparison finished but the result could not be read.", 500, [
      scrubForClient(error instanceof Error ? error.message : String(error))
    ]);
  }
}

export async function verdictViaFastApi(request: Request) {
  let body: StageRequest;
  try {
    body = await request.json() as StageRequest;
  } catch {
    return jsonError("Request body must be valid JSON.");
  }
  const { reviewId, selectedCardId, errors } = validateStageRequest(body);
  if (errors.length) return jsonError("Decision verdict request validation failed.", 400, errors);

  let candidateGeneration: unknown;
  try {
    candidateGeneration = await readRunJson(reviewId, "candidate_generation.json");
  } catch (error) {
    return jsonError("Decision verdict requires an active generated candidate for this review.", 409, [
      scrubForClient(error instanceof Error ? error.message : String(error))
    ]);
  }
  const candidate = candidateFromGeneration(candidateGeneration);
  if (candidate.selectedCardId && candidate.selectedCardId !== selectedCardId) {
    return lineageMismatchError("decision_verdict", reviewId, selectedCardId, candidate.selectedCardId);
  }
  if (!candidate.candidateId) return jsonError("Decision verdict requires a generated candidate id.", 409);
  const comparisonId = `current_vs_candidate:${candidate.candidateId}`;

  const api = await callFastApi("POST", `/api/v1/reviews/${encodeURIComponent(reviewId)}/verdict`, {
    comparison_id: comparisonId
  });
  if (!api.ok) {
    return NextResponse.json({
      ...legacyErrorFromFastApi(api.body, "Decision verdict failed."),
      stage: "decision_verdict",
      review_id: reviewId,
      selected_card_id: selectedCardId
    }, { status: api.status });
  }
  const verdictLineageErrors = fastApiLineageErrors(api.body, {
    reviewId,
    selectedCardId,
    candidateId: candidate.candidateId,
    comparisonId
  });
  if (verdictLineageErrors.length) {
    return fastApiLineageMismatchResponse("decision_verdict", {
      reviewId,
      selectedCardId,
      candidateId: candidate.candidateId,
      comparisonId
    }, verdictLineageErrors);
  }

  try {
    const decisionVerdict = await readRunJson(reviewId, "decision_verdict.json");
    const verdict = isRecord(decisionVerdict) ? decisionVerdict : {};
    return NextResponse.json({
      review_id: reviewId,
      status: "completed",
      stage: "decision_verdict",
      selected_card_id: selectedCardId || candidate.selectedCardId,
      candidate_id: candidate.candidateId,
      fastapi_envelope: api.body,
      verdict_id: verdictIdFromDocument(decisionVerdict),
      selection_decision_status: textValue(verdict.selection_decision_status, textValue(verdict.recommended_action, "unknown")),
      confidence: textValue(verdict.confidence, "unknown"),
      path: artifactPath(reviewId, "decision_verdict.json"),
      decision_verdict: decisionVerdict,
      site_explanation_bundle: await readOptionalRunJson(reviewId, "site_explanation_bundle.json")
    });
  } catch (error) {
    return jsonError("Decision verdict finished but the result could not be read.", 500, [
      scrubForClient(error instanceof Error ? error.message : String(error))
    ]);
  }
}

export async function reportViaFastApi(request: Request) {
  let body: StageRequest;
  try {
    body = await request.json() as StageRequest;
  } catch {
    return jsonError("Request body must be valid JSON.");
  }
  const { reviewId, selectedCardId, errors } = validateStageRequest(body);
  if (errors.length) return jsonError("Report commentary request validation failed.", 400, errors);

  let candidateGeneration: unknown;
  let decisionVerdict: unknown;
  try {
    candidateGeneration = await readRunJson(reviewId, "candidate_generation.json");
    decisionVerdict = await readRunJson(reviewId, "decision_verdict.json");
  } catch (error) {
    return jsonError("Report commentary requires active candidate and verdict evidence for this review.", 409, [
      scrubForClient(error instanceof Error ? error.message : String(error))
    ]);
  }
  const candidate = candidateFromGeneration(candidateGeneration);
  if (candidate.selectedCardId && candidate.selectedCardId !== selectedCardId) {
    return lineageMismatchError("report_commentary", reviewId, selectedCardId, candidate.selectedCardId);
  }
  const verdictId = verdictIdFromDocument(decisionVerdict);

  const api = await callFastApi("POST", `/api/v1/reviews/${encodeURIComponent(reviewId)}/report`, {
    verdict_id: verdictId
  });
  if (!api.ok) {
    return NextResponse.json({
      ...legacyErrorFromFastApi(api.body, "Report commentary failed."),
      stage: "report_commentary",
      review_id: reviewId,
      selected_card_id: selectedCardId
    }, { status: api.status });
  }
  const reportLineageErrors = fastApiLineageErrors(api.body, {
    reviewId,
    selectedCardId,
    candidateId: candidate.candidateId,
    verdictId
  });
  if (reportLineageErrors.length) {
    return fastApiLineageMismatchResponse("report_commentary", {
      reviewId,
      selectedCardId,
      candidateId: candidate.candidateId,
      verdictId
    }, reportLineageErrors);
  }

  try {
    const aiCommentaryContext = await readRunJson(reviewId, "ai_commentary_context.json");
    return NextResponse.json({
      review_id: reviewId,
      status: "completed",
      stage: "report_commentary",
      selected_card_id: selectedCardId || candidate.selectedCardId,
      candidate_id: candidate.candidateId,
      fastapi_envelope: api.body,
      report_display_model: reportDisplayModelFromFastApi(isRecord(api.body) ? api.body : {}),
      path: artifactPath(reviewId, "ai_commentary_context.json"),
      ai_commentary_context: aiCommentaryContext,
      site_explanation_bundle: await readOptionalRunJson(reviewId, "site_explanation_bundle.json")
    });
  } catch (error) {
    return jsonError("Report commentary finished but the result could not be read.", 500, [
      scrubForClient(error instanceof Error ? error.message : String(error))
    ]);
  }
}
