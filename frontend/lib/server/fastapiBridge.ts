import { NextResponse } from "next/server";
import type { ReportResponse, StagedReviewStatusResponse } from "@/lib/generated/api-types";
import { legacyErrorFromFastApi, scrubForClient } from "@/lib/server/fastapi/errors";

const FASTAPI_TIMEOUT_MS = 15 * 60 * 1000;
const WEIGHT_TOLERANCE = 0.01;
const WEIGHT_TOLERANCE_EPSILON = 1e-9;

const path = {
  basename(value: string) {
    return value.split(/[\\/]/).pop() || "";
  },
  resolve(...parts: string[]) {
    return parts.filter(Boolean).join("/");
  },
  relative(..._parts: string[]) {
    return "";
  },
  isAbsolute(value: string) {
    return /^([A-Za-z]:)?[\\/]/.test(value);
  }
};

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
  sample_mode: boolean;
};

export type StageRequest = {
  review_id?: unknown;
  selected_card_id?: unknown;
  builder_setup_id?: unknown;
  candidate_id?: unknown;
  comparison_id?: unknown;
  verdict_id?: unknown;
  overrides?: unknown;
};

type FastApiCallResult = {
  ok: boolean;
  status: number;
  body: unknown;
};

class PortfolioApiAuthError extends Error {
  status: number;

  constructor(message: string, status = 401) {
    super(message);
    this.name = "PortfolioApiAuthError";
    this.status = status;
  }
}

type ExpectedFastApiLineage = {
  reviewId?: string;
  selectedCardId?: string;
  builderSetupId?: string;
  candidateId?: string;
  comparisonId?: string;
  verdictId?: string;
};

function fastApiBaseUrl() {
  return (
    process.env.PMRI_FASTAPI_BASE_URL
    || process.env.FASTAPI_BASE_URL
    || "http://127.0.0.1:8000"
  ).replace(/\/+$/, "");
}

function envText(name: string) {
  const value = process.env[name];
  return typeof value === "string" && value.trim() ? value.trim() : "";
}

function isProductionRuntime() {
  return ["production"].includes(
    (envText("NODE_ENV") || envText("ENVIRONMENT")).toLowerCase()
  );
}

function portfolioApiDevBypassEnabled() {
  return envText("PMRI_PORTFOLIO_API_AUTH_MODE") === "dev_bypass" && !isProductionRuntime();
}

function internalAuthSecret() {
  return envText("PMRI_FASTAPI_INTERNAL_SECRET") || envText("PMRI_INTERNAL_AUTH_SECRET");
}

function hexFromBytes(bytes: Uint8Array) {
  return Array.from(bytes)
    .map((byte) => byte.toString(16).padStart(2, "0"))
    .join("");
}

async function hmacSha256Hex(secret: string, message: string) {
  const encoder = new TextEncoder();
  const key = await crypto.subtle.importKey(
    "raw",
    encoder.encode(secret),
    { name: "HMAC", hash: "SHA-256" },
    false,
    ["sign"]
  );
  const signature = await crypto.subtle.sign("HMAC", key, encoder.encode(message));
  return hexFromBytes(new Uint8Array(signature));
}

async function portfolioApiUserId() {
  if (portfolioApiDevBypassEnabled()) {
    return envText("PMRI_PORTFOLIO_API_DEV_USER_ID") || "local-dev-user";
  }

  if (envText("NEXT_PUBLIC_PMRI_SUPABASE_ENABLED") === "true") {
    const { createSupabaseServerClient } = await import("@/lib/supabase/server");
    const supabase = await createSupabaseServerClient();
    if (!supabase) {
      throw new PortfolioApiAuthError("Portfolio API authentication is not configured.");
    }
    const { data, error } = await supabase.auth.getUser();
    const userId = data?.user?.id;
    if (error || !userId) {
      throw new PortfolioApiAuthError("Sign in before starting or reading a portfolio review.");
    }
    return userId;
  }

  throw new PortfolioApiAuthError(
    "Portfolio API authentication is required. For local-only demos, set PMRI_PORTFOLIO_API_AUTH_MODE=dev_bypass outside production."
  );
}

async function internalAuthHeaders() {
  const userId = await portfolioApiUserId();
  const secret = internalAuthSecret();
  if (!secret) {
    throw new PortfolioApiAuthError("FastAPI internal auth secret is not configured.", 500);
  }
  const timestamp = String(Date.now());
  const signature = await hmacSha256Hex(secret, `${userId}.${timestamp}`);
  return {
    "X-PMRI-User-Id": userId,
    "X-PMRI-Auth-Timestamp": timestamp,
    "X-PMRI-Internal-Signature": signature
  };
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
  if (value === undefined || value === null) {
    return { clientFitErrors: ["client_fit is required for web diagnosis."] };
  }
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
    const authHeaders = await internalAuthHeaders();
    const headers = body === undefined
      ? authHeaders
      : { ...authHeaders, "Content-Type": "application/json" };
    const response = await fetch(url, {
      method,
      headers,
      body: body === undefined ? undefined : JSON.stringify(body),
      cache: "no-store",
      signal: controller.signal
    });
    const responseText = await response.text();
    const parsed = responseText ? parseJsonWithNonFinite(responseText) : null;
    return { ok: response.ok, status: response.status, body: parsed };
  } catch (error) {
    if (error instanceof PortfolioApiAuthError) {
      return {
        ok: false,
        status: error.status,
        body: {
          safe_error: {
            message: error.message,
            details: []
          }
        }
      };
    }
    const unavailable = error instanceof Error && error.name === "AbortError"
      ? "FastAPI backend request timed out."
      : isProductionRuntime()
        ? "Portfolio MRI supporting data is temporarily unavailable. Please retry in a minute; the analysis backend may be restarting."
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
  const holdingKeys = new Set<string>();
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
      const holdingKey = `instrument:${ticker}`;
      if (holdingKeys.has(holdingKey)) {
        errors.push(`holding[${index}] duplicates ticker ${ticker}.`);
        return;
      }
      holdingKeys.add(holdingKey);
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
      const holdingKey = `cash:${currency}`;
      if (holdingKeys.has(holdingKey)) {
        errors.push(`holding[${index}] duplicates cash currency ${currency}.`);
        return;
      }
      holdingKeys.add(holdingKey);
      holdings.push({ type: "cash", currency, weight });
      return;
    }

    errors.push(`holding[${index}].type must be "instrument" or "cash".`);
  });

  if (Math.abs(totalWeight - 100) - WEIGHT_TOLERANCE > WEIGHT_TOLERANCE_EPSILON) {
    errors.push(`Total weight must equal 100 within ${WEIGHT_TOLERANCE}; got ${totalWeight}.`);
  }

  if (errors.length) return { errors };
  const { clientFit, clientFitErrors } = validateClientFitPayload(body.client_fit);
  errors.push(...clientFitErrors);
  if (errors.length) return { errors };
  const requestedMode = typeof body.mode === "string" ? body.mode.trim().toLowerCase() : "";
  const sampleMode = ["demo_qa", "sample", "sample_demo"].includes(requestedMode);
  return {
    payload: {
      investor_currency: investorCurrency,
      holdings,
      client_fit: clientFit,
      sample_mode: sampleMode
    },
    errors
  };
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
      sample_mode: payload.sample_mode
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

function artifactPath(reviewId: string, relativePath: string) {
  return `runs/${reviewId}/${relativePath.replaceAll("\\", "/")}`;
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
    ["builder_setup_id", expected.builderSetupId],
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

function fastApiData(body: unknown) {
  const envelope = isRecord(body) ? body : {};
  return isRecord(envelope.data) ? envelope.data : {};
}

function fastApiLineage(body: unknown) {
  const envelope = isRecord(body) ? body : {};
  return isRecord(envelope.lineage) ? envelope.lineage : {};
}

function stageBodyText(body: StageRequest, key: keyof StageRequest) {
  return typeof body[key] === "string" ? String(body[key]).trim() : "";
}

function builderOverridesFromStageRequest(body: StageRequest) {
  const raw = isRecord(body.overrides) ? body.overrides : {};
  const methodId = textValue(raw.method_id);
  const mode = textValue(raw.mode);
  const constraintPreset = textValue(raw.constraint_preset);
  const minAssetWeight = numberValue(raw.min_asset_weight);
  const maxAssetWeight = numberValue(raw.max_asset_weight);
  const overrides: Record<string, unknown> = {};
  if (methodId) overrides.method_id = methodId;
  if (mode) overrides.mode = mode;
  if (constraintPreset) overrides.constraint_preset = constraintPreset;
  if (minAssetWeight !== null) overrides.min_asset_weight = minAssetWeight;
  if (maxAssetWeight !== null) overrides.max_asset_weight = maxAssetWeight;
  return overrides;
}

function sourceArtifactPath(body: unknown, kind: string, fallback: string) {
  const envelope = isRecord(body) ? body : {};
  const evidence = isRecord(envelope.evidence) ? envelope.evidence : {};
  const refs = Array.isArray(evidence.source_artifacts) ? evidence.source_artifacts : [];
  for (const item of refs) {
    const ref = isRecord(item) ? item : {};
    if (textValue(ref.kind) === kind) return textValue(ref.ref, fallback);
  }
  return fallback;
}

function publicBuilderDocumentFromFastApi(body: unknown, selectedCardId: string) {
  const data = fastApiData(body);
  const setup = isRecord(data.builder_setup) ? data.builder_setup : {};
  const setupId = textValue(setup.builder_setup_id);
  const methodId = textValue(setup.method_id);
  const mode = textValue(setup.mode) || null;
  const constraintPreset = textValue(setup.constraint_preset) || null;
  const minAssetWeight = numberValue(setup.min_asset_weight);
  const maxAssetWeight = numberValue(setup.max_asset_weight);
  const canGenerate = data.candidate_generation_allowed === true;
  const clientFitContext = isRecord(setup.client_fit_context) ? setup.client_fit_context : undefined;
  const clientFitTestCriteria = isRecord(setup.client_fit_test_criteria) ? setup.client_fit_test_criteria : undefined;
  const clientFitOptimizerBoundary = textValue(setup.client_fit_optimizer_boundary) || null;
  return {
    selected_card_id: textValue(setup.selected_card_id, selectedCardId),
    can_generate_candidate: canGenerate,
    builder_prefill: {
      source_card_id: textValue(setup.selected_card_id, selectedCardId),
      suggested_method: methodId || null,
      constraint_preset: constraintPreset,
      min_asset_weight: minAssetWeight,
      max_asset_weight: maxAssetWeight,
      success_criteria: stringArray(setup.success_criteria),
      tradeoff_to_watch: textValue(setup.tradeoff_to_watch) || null,
      decision_boundary: textValue(setup.decision_boundary) || null,
      client_fit_context: clientFitContext,
      client_fit_test_criteria: clientFitTestCriteria,
      client_fit_optimizer_boundary: clientFitOptimizerBoundary
    },
    candidate_setup: {
      candidate_setup_id: setupId,
      source_card_id: textValue(setup.selected_card_id, selectedCardId),
      selected_method: methodId || null,
      validation_status: canGenerate ? "valid" : "blocked",
      can_generate_candidate: canGenerate,
      success_criteria: stringArray(setup.success_criteria),
      tradeoff_to_watch: textValue(setup.tradeoff_to_watch) || null,
      decision_boundary: textValue(setup.decision_boundary) || null,
      client_fit_context: clientFitContext,
      client_fit_test_criteria: clientFitTestCriteria,
      client_fit_optimizer_boundary: clientFitOptimizerBoundary,
      parameters: {
        mode,
        constraint_preset: constraintPreset,
        min_asset_weight: minAssetWeight,
        max_asset_weight: maxAssetWeight
      },
      constraints: {
        mode,
        constraint_preset: constraintPreset,
        min_asset_weight: minAssetWeight,
        max_asset_weight: maxAssetWeight
      }
    }
  };
}

function stagedRouteVersionMismatchResponse(status: number) {
  return NextResponse.json({
    status: "failed",
    error: "Frontend/backend version mismatch: FastAPI does not expose POST /api/v1/reviews/staged. Restart the FastAPI backend and Next.js frontend so both use the same route contract.",
    details: []
  }, { status: status === 404 || status === 405 ? 502 : status });
}

function publicCandidateGenerationFromFastApi(body: unknown, selectedCardId: string) {
  const data = fastApiData(body);
  const candidate = isRecord(data.candidate) ? data.candidate : {};
  const hypothesis = isRecord(data.hypothesis) ? data.hypothesis : {};
  const lineage = fastApiLineage(body);
  const candidateId = textValue(lineage.candidate_id, textValue(candidate.candidate_id));
  const generationStatus = textValue(candidate.generation_status, "unknown");
  return {
    selected_card_id: textValue(lineage.selected_card_id, selectedCardId),
    generation_status: generationStatus,
    candidate: {
      candidate_id: candidateId,
      source_card_id: textValue(lineage.selected_card_id, selectedCardId),
      candidate_name: textValue(candidate.method_label, candidateId),
      method: textValue(candidate.method_label),
      generation_status: generationStatus,
      weights: isRecord(candidate.weight_summary) ? candidate.weight_summary : {},
      status: generationStatus,
      hypothesis_to_test: textValue(hypothesis.hypothesis),
      success_criteria: stringArray(hypothesis.success_criteria),
      tradeoff_to_watch: textValue(hypothesis.tradeoff_to_watch),
      decision_boundary: textValue(hypothesis.decision_boundary)
    },
    handoff_to_comparison: {
      candidate_id: candidateId,
      can_compare: generationStatus === "generated" && stringArray(data.next_allowed_actions).includes("run_comparison")
    }
  };
}

function publicCurrentVsCandidateFromFastApi(body: unknown, candidateId: string) {
  const data = fastApiData(body);
  const comparison = isRecord(data.comparison) ? data.comparison : {};
  const currentVsCandidate = isRecord(data.current_vs_candidate) ? data.current_vs_candidate : {};
  if (Array.isArray(currentVsCandidate.comparisons)) {
    return currentVsCandidate;
  }
  const context = isRecord(data.evidence_chain_context) ? data.evidence_chain_context : {};
  const resolvedCandidateId = candidateId || textValue(fastApiLineage(body).candidate_id);
  return {
    comparison_status: textValue(comparison.candidate_label) ? "available" : "partial",
    view_mode: "current_vs_candidate",
    selected_candidate_ids: resolvedCandidateId ? [resolvedCandidateId] : [],
    baseline: {
      display_name: textValue(comparison.current_label, "Current portfolio")
    },
    comparisons: [
      {
        candidate_id: resolvedCandidateId,
        display_name: textValue(comparison.candidate_label, resolvedCandidateId),
        candidate_label: textValue(comparison.candidate_label, resolvedCandidateId),
        hypothesis_to_test: textValue(context.tested_hypothesis),
        success_criteria_result: {
          overall_status: textValue(comparison.success_criteria_result, "unknown")
        },
        what_improved: stringArray(comparison.what_improved),
        what_worsened: stringArray(comparison.what_worsened),
        what_stayed_similar: stringArray(comparison.what_stayed_similar),
        unavailable_metrics: stringArray(comparison.unavailable_metrics).map((field) => ({ field })),
        materiality_for_decision_review: {
          status: textValue(comparison.materiality, "unknown")
        },
        source_artifacts: stringArray(context.source_artifacts)
      }
    ],
    warnings: stringArray((isRecord(body) ? body : {}).warnings)
  };
}

function publicDecisionVerdictFromFastApi(body: unknown) {
  const data = fastApiData(body);
  const verdict = isRecord(data.verdict) ? data.verdict : {};
  const lineage = fastApiLineage(body);
  return {
    verdict_id: textValue(lineage.verdict_id, textValue(verdict.verdict_id, "unknown")),
    reviewed_candidate_id: textValue(lineage.candidate_id),
    selection_decision_status: textValue(verdict.verdict, "unknown"),
    confidence: textValue(verdict.confidence, "unknown"),
    rationale_summary: stringArray(verdict.rationale)[0] || "",
    confidence_limitations: stringArray(verdict.limitations),
    what_would_change_verdict: stringArray(verdict.what_would_change_verdict),
    evidence_summary: {
      improvements: stringArray(verdict.evidence_used)
    },
    warnings: stringArray((isRecord(body) ? body : {}).warnings)
  };
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
    portfolio_xray: "Portfolio Diagnosis",
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

  const api = await callFastApi("POST", "/api/v1/reviews/staged", fastApiCreateReviewBody(payload));
  if (!api.ok) {
    if (api.status === 404 || api.status === 405) {
      return stagedRouteVersionMismatchResponse(api.status);
    }
    return NextResponse.json(legacyErrorFromFastApi(api.body, "Portfolio diagnosis failed."), { status: api.status });
  }

  const envelope = isRecord(api.body) ? api.body : {};
  const reviewId = textValue(envelope.review_id);
  if (!reviewId) return jsonError("FastAPI diagnosis did not return a review id.", 500);
  const reviewValidation = validateReviewId(reviewId);
  if (reviewValidation.errors.length) {
    return jsonError("FastAPI diagnosis returned an invalid review id.", 500, reviewValidation.errors);
  }

  return NextResponse.json(api.body);
}

export async function stagedReviewStatusViaFastApi(reviewIdInput: unknown) {
  const { reviewId, errors } = validateReviewId(reviewIdInput);
  if (errors.length) return jsonError("Staged review status request validation failed.", 400, errors);

  const api = await callFastApi("GET", `/api/v1/reviews/${encodeURIComponent(reviewId)}/status`);
  if (!api.ok) {
    return NextResponse.json(legacyErrorFromFastApi(api.body, "Staged review status failed."), { status: api.status });
  }

  const envelope: Partial<StagedReviewStatusResponse> = isRecord(api.body) ? api.body as StagedReviewStatusResponse : {};
  if (envelope.review_id && envelope.review_id !== reviewId) {
    return fastApiLineageMismatchResponse("staged_review_status", { reviewId }, [
      `review_id mismatch: expected ${reviewId}; FastAPI returned ${envelope.review_id}.`
    ]);
  }
  return NextResponse.json(api.body);
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

function sanitizeRecoveryEnvelope(value: unknown) {
  if (!isRecord(value)) return value;
  const recoverableKeys = [
    "portfolio_xray",
    "stress_report",
    "run_metadata",
    "output_manifest",
    "problem_classification",
    "candidate_launchpad",
    "portfolio_alternatives_builder",
    "ai_commentary_context",
    "site_explanation_bundle"
  ];
  const data = isRecord(value.data) ? value.data : {};
  const artifactPayloads = isRecord(data.artifact_payloads) ? data.artifact_payloads : {};
  const allowedArtifactPayloads = Object.fromEntries(
    Object.entries(artifactPayloads).filter(([key]) => recoverableKeys.includes(key))
  );
  const sanitizedData: Record<string, unknown> = {
    ...data,
    artifact_payloads: allowedArtifactPayloads
  };
  if (Array.isArray(data.artifact_refs)) {
    sanitizedData.artifact_refs = data.artifact_refs.filter((item) => (
      isRecord(item) && recoverableKeys.includes(textValue(item.kind))
    ));
  }

  const evidence = isRecord(value.evidence) ? value.evidence : undefined;
  const sanitizedEvidence = evidence && Array.isArray(evidence.source_artifacts)
    ? {
      ...evidence,
      source_artifacts: evidence.source_artifacts.filter((item) => (
        isRecord(item) && recoverableKeys.includes(textValue(item.kind))
      ))
    }
    : value.evidence;

  return {
    ...value,
    data: sanitizedData,
    evidence: sanitizedEvidence
  };
}

function artifactRefsToPathMap(refs: unknown) {
  const pathEntries = Array.isArray(refs)
    ? refs
      .map((item): [string, string] | null => {
        const ref = isRecord(item) ? item : {};
        const kind = textValue(ref.kind);
        const value = textValue(ref.ref);
        return kind && value ? [kind, value] : null;
      })
      .filter((item): item is [string, string] => Boolean(item))
    : [];
  return Object.fromEntries(pathEntries);
}

function recoveredLaunchpadOutput(launchpadValue: unknown) {
  const launchpad = Array.isArray(launchpadValue)
    ? (isRecord(launchpadValue[0]) ? launchpadValue[0] : {})
    : (isRecord(launchpadValue) ? launchpadValue : {});
  const cardId = textValue(launchpad.card_id);
  if (!cardId) return undefined;
  return {
    cards: [
      {
        card_id: cardId,
        title: textValue(launchpad.title, "Test candidate"),
        default_method: textValue(launchpad.method_id),
        generates_portfolio: launchpad.generation_allowed === true,
        is_rebalance_recommendation: launchpad.is_rebalance_recommendation === true
      }
    ]
  };
}

function recoveredBuilderOutput(launchpadValue: unknown) {
  const launchpad = Array.isArray(launchpadValue)
    ? (isRecord(launchpadValue[0]) ? launchpadValue[0] : {})
    : (isRecord(launchpadValue) ? launchpadValue : {});
  const selectedCardId = textValue(launchpad.card_id);
  if (!selectedCardId) return undefined;
  const methodId = textValue(launchpad.method_id);
  const canGenerate = launchpad.generation_allowed === true;
  return {
    selected_card_id: selectedCardId,
    can_generate_candidate: canGenerate,
    builder_prefill: {
      suggested_method: methodId || null
    },
    candidate_setup: {
      source_card_id: selectedCardId,
      candidate_setup_id: methodId ? `fastapi_recovered:${methodId}` : `fastapi_recovered:${selectedCardId}`,
      validation_status: canGenerate ? "valid" : "blocked",
      can_generate_candidate: canGenerate
    }
  };
}

function recoveredReviewResultFromFastApi(body: unknown, reviewId: string) {
  const envelope = isRecord(body) ? body : {};
  const data = isRecord(envelope.data) ? envelope.data : {};
  const evidence = isRecord(envelope.evidence) ? envelope.evidence : {};
  const summary = isRecord(data.review_summary) ? data.review_summary : {};
  const launchpadOutput = recoveredLaunchpadOutput(data.launchpad);
  const builderOutput = recoveredBuilderOutput(data.launchpad);
  const artifactPayloads = isRecord(data.artifact_payloads) ? data.artifact_payloads : {};
  const outputs = Object.fromEntries(
    Object.entries({
      ...artifactPayloads,
      problem_classification: artifactPayloads.problem_classification ?? data.diagnosis,
      candidate_launchpad: artifactPayloads.candidate_launchpad ?? launchpadOutput,
      portfolio_alternatives_builder: artifactPayloads.portfolio_alternatives_builder ?? builderOutput
    }).filter(([, value]) => value !== undefined && value !== null)
  );
  const paths = artifactRefsToPathMap(data.artifact_refs ?? evidence.source_artifacts);

  return sanitizeRecoveredReviewResult({
    review_id: reviewId,
    status: "completed",
    portfolio_input: {
      investor_currency: textValue(summary.investor_currency, "USD"),
      holdings: []
    },
    paths,
    outputs,
    fastapi_envelope: body
  }, reviewId);
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

  const sanitizedEnvelope = sanitizeRecoveryEnvelope(api.body);
  const sanitized = recoveredReviewResultFromFastApi(sanitizedEnvelope, reviewId);
  if (!sanitized) return jsonError("FastAPI did not return recoverable review data for this review_id.", 409);
  return NextResponse.json({
    status: "completed",
    stage: "review_recovery",
    review_id: reviewId,
    fastapi_envelope: sanitizedEnvelope,
    recovery: {
      source: "fastapi_v1_review_recovery",
      restored_active_stages: ["diagnosis", "evidence", "hypothesis_setup"],
      downstream_artifacts_restored_as_active: false,
      note: "Candidate, comparison, verdict, and report artifacts are not restored as active state during recovery."
    },
    review_result: sanitized
  });
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
    overrides: builderOverridesFromStageRequest(body)
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
  const builderData = fastApiData(api.body);
  const builderSetup: Record<string, unknown> = isRecord(builderData.builder_setup) ? builderData.builder_setup : {};
  const setupSelectedCardId = textValue(builderSetup.selected_card_id);
  const lineageBuilderSetupId = textValue(fastApiLineage(api.body).builder_setup_id);
  const setupBuilderSetupId = textValue(builderSetup.builder_setup_id);
  const builderSetupErrors: string[] = [];
  if (setupSelectedCardId && setupSelectedCardId !== selectedCardId) {
    builderSetupErrors.push(`data.builder_setup.selected_card_id expected ${selectedCardId} but received ${setupSelectedCardId}.`);
  }
  if (lineageBuilderSetupId && setupBuilderSetupId && setupBuilderSetupId !== lineageBuilderSetupId) {
    builderSetupErrors.push(`data.builder_setup.builder_setup_id expected ${lineageBuilderSetupId} but received ${setupBuilderSetupId}.`);
  }
  if (builderSetupErrors.length) {
    return fastApiLineageMismatchResponse("builder_setup", { reviewId, selectedCardId }, builderSetupErrors);
  }

  return NextResponse.json({
    review_id: reviewId,
    status: "completed",
    stage: "builder_setup",
    selected_card_id: selectedCardId,
    builder_setup_id: textValue(fastApiLineage(api.body).builder_setup_id, textValue(fastApiData(api.body).builder_setup_id)),
    fastapi_envelope: api.body,
    can_generate_candidate: fastApiData(api.body).candidate_generation_allowed === true,
    path: sourceArtifactPath(api.body, "portfolio_alternatives_builder", artifactPath(reviewId, "analysis_subject/portfolio_alternatives_builder.json")),
    portfolio_alternatives_builder: publicBuilderDocumentFromFastApi(api.body, selectedCardId)
  });
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

  let builderSetupId = stageBodyText(body, "builder_setup_id");

  if (!builderSetupId) {
    const builderApi = await callFastApi("POST", `/api/v1/reviews/${encodeURIComponent(reviewId)}/builder`, {
      selected_card_id: selectedCardId,
      overrides: builderOverridesFromStageRequest(body)
    });
    if (!builderApi.ok) {
      const legacyError = legacyErrorFromFastApi(builderApi.body, "Candidate generation requires a prepared Builder setup for this review.");
      const status = JSON.stringify(builderApi.body).includes("Selected Launchpad card was not found") ? 409 : builderApi.status;
      return NextResponse.json({
        ...legacyError,
        stage: "candidate_generation",
        review_id: reviewId,
        selected_card_id: selectedCardId
      }, { status });
    }
    const builderLineageErrors = fastApiLineageErrors(builderApi.body, { reviewId, selectedCardId });
    if (builderLineageErrors.length) {
      return fastApiLineageMismatchResponse("candidate_generation", { reviewId, selectedCardId }, builderLineageErrors);
    }
    builderSetupId = textValue(fastApiLineage(builderApi.body).builder_setup_id);
  }
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
  const candidateLineageErrors = fastApiLineageErrors(api.body, { reviewId, selectedCardId, builderSetupId });
  if (candidateLineageErrors.length) {
    return fastApiLineageMismatchResponse("candidate_generation", { reviewId, selectedCardId }, candidateLineageErrors);
  }

  const candidateGeneration = publicCandidateGenerationFromFastApi(api.body, selectedCardId);
  const candidate: Record<string, unknown> = isRecord(candidateGeneration.candidate) ? candidateGeneration.candidate : {};
  const canCompare = isRecord(candidateGeneration.handoff_to_comparison) && candidateGeneration.handoff_to_comparison.can_compare === true;
  return NextResponse.json({
    review_id: reviewId,
    status: canCompare ? "completed" : "blocked",
    stage: "candidate_generation",
    selected_card_id: textValue(fastApiLineage(api.body).selected_card_id, selectedCardId),
    builder_setup_id: builderSetupId,
    candidate_id: textValue(fastApiLineage(api.body).candidate_id, textValue(candidate.candidate_id)),
    fastapi_envelope: api.body,
    generation_status: textValue(candidate.generation_status, "unknown"),
    can_compare: canCompare,
    path: sourceArtifactPath(api.body, "candidate_generation", artifactPath(reviewId, "candidate_generation.json")),
    candidate_generation: candidateGeneration
  });
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

  const candidateId = stageBodyText(body, "candidate_id");
  if (!candidateId) return jsonError("Comparison requires a generated candidate id.", 400);

  const api = await callFastApi("POST", `/api/v1/reviews/${encodeURIComponent(reviewId)}/comparison`, {
    candidate_id: candidateId
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
    candidateId
  });
  if (comparisonLineageErrors.length) {
    return fastApiLineageMismatchResponse("current_vs_candidate", {
      reviewId,
      selectedCardId,
      candidateId
    }, comparisonLineageErrors);
  }

  const comparisonId = textValue(fastApiLineage(api.body).comparison_id, `current_vs_candidate:${candidateId}`);
  const paths = {
    candidate_comparison: sourceArtifactPath(api.body, "candidate_comparison", artifactPath(reviewId, "candidate_comparison.json")),
    current_vs_candidate: sourceArtifactPath(api.body, "current_vs_candidate", artifactPath(reviewId, "current_vs_candidate.json")),
    site_explanation_bundle: sourceArtifactPath(api.body, "site_explanation_bundle", artifactPath(reviewId, "site_explanation_bundle.json"))
  };
  return NextResponse.json({
    review_id: reviewId,
    status: "completed",
    stage: "current_vs_candidate",
    selected_card_id: textValue(fastApiLineage(api.body).selected_card_id, selectedCardId),
    candidate_id: textValue(fastApiLineage(api.body).candidate_id, candidateId),
    comparison_id: comparisonId,
    fastapi_envelope: api.body,
    paths,
    current_vs_candidate: publicCurrentVsCandidateFromFastApi(api.body, candidateId)
  });
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

  const candidateId = stageBodyText(body, "candidate_id");
  const comparisonId = stageBodyText(body, "comparison_id") || (candidateId ? `current_vs_candidate:${candidateId}` : "");
  if (!comparisonId) return jsonError("Decision verdict requires a comparison id.", 400);

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
    candidateId,
    comparisonId
  });
  if (verdictLineageErrors.length) {
    return fastApiLineageMismatchResponse("decision_verdict", {
      reviewId,
      selectedCardId,
      candidateId,
      comparisonId
    }, verdictLineageErrors);
  }

  const decisionVerdict = publicDecisionVerdictFromFastApi(api.body);
  return NextResponse.json({
    review_id: reviewId,
    status: "completed",
    stage: "decision_verdict",
    selected_card_id: textValue(fastApiLineage(api.body).selected_card_id, selectedCardId),
    candidate_id: textValue(fastApiLineage(api.body).candidate_id, candidateId),
    comparison_id: textValue(fastApiLineage(api.body).comparison_id, comparisonId),
    fastapi_envelope: api.body,
    verdict_id: textValue(fastApiLineage(api.body).verdict_id, textValue(decisionVerdict.verdict_id, "unknown")),
    selection_decision_status: textValue(decisionVerdict.selection_decision_status, "unknown"),
    confidence: textValue(decisionVerdict.confidence, "unknown"),
    path: sourceArtifactPath(api.body, "decision_verdict", artifactPath(reviewId, "decision_verdict.json")),
    decision_verdict: decisionVerdict
  });
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

  const candidateId = stageBodyText(body, "candidate_id");
  const comparisonId = stageBodyText(body, "comparison_id");
  const verdictId = stageBodyText(body, "verdict_id");
  if (!verdictId) return jsonError("Report commentary requires a verdict id.", 400);

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
    candidateId,
    comparisonId,
    verdictId
  });
  if (reportLineageErrors.length) {
    return fastApiLineageMismatchResponse("report_commentary", {
      reviewId,
      selectedCardId,
      candidateId,
      verdictId
    }, reportLineageErrors);
  }

  return NextResponse.json({
    review_id: reviewId,
    status: "completed",
    stage: "report_commentary",
    selected_card_id: textValue(fastApiLineage(api.body).selected_card_id, selectedCardId),
    candidate_id: textValue(fastApiLineage(api.body).candidate_id, candidateId),
    comparison_id: textValue(fastApiLineage(api.body).comparison_id, comparisonId),
    verdict_id: textValue(fastApiLineage(api.body).verdict_id, verdictId),
    fastapi_envelope: api.body,
    report_display_model: reportDisplayModelFromFastApi(isRecord(api.body) ? api.body : {}),
    path: sourceArtifactPath(api.body, "ai_commentary_context", artifactPath(reviewId, "ai_commentary_context.json"))
  });
}
