"use client";

import { createContext, useCallback, useContext, useEffect, useMemo, useState, type ReactNode } from "react";
import type { ComparisonMetric, EvidenceItem, Metric, StatusTone } from "@/lib/types";
import type { JourneyFlags } from "@/lib/journey";
import { instrumentByTicker } from "@/data/instrumentUniverse";

export type ReviewHolding = {
  id: string;
  label: string;
  ticker: string;
  instrument: string;
  weight: number;
  type: "instrument" | "cash";
  currency?: string;
};

type JsonValue = null | boolean | number | string | JsonValue[] | { [key: string]: JsonValue };

export type ReviewResult = {
  review_id?: string;
  status?: string;
  portfolio_input?: JsonValue;
  paths?: JsonValue;
  outputs?: Record<string, JsonValue>;
  error?: string;
  details?: JsonValue;
  [key: string]: JsonValue | undefined;
};

export type ReviewRunMode = "sample_demo" | "real_run";
export type ReviewRunStatus = "draft" | "completed" | "failed";

export type ReviewErrorState = {
  message: string;
  details?: string;
  occurredAt: string;
};

export type CandidateGenerationSummary = {
  status: string;
  stage: "candidate_generation";
  selectedCardId: string;
  candidateId: string;
  generationStatus: string;
  canCompare: boolean;
  path?: string;
  weights: Array<{ ticker: string; weight: number }>;
  generatedAt: string;
};

export type ComparisonResultSummary = {
  status: string;
  stage: "current_vs_candidate";
  selectedCardId: string;
  candidateId: string;
  comparisonStatus: string;
  viewMode: string;
  candidateName: string;
  candidateBoundary: string;
  evidenceQuality: string;
  summary: string;
  metrics: ComparisonMetric[];
  improved: string[];
  worsened: string[];
  neutral: string[];
  unclear: string[];
  turnover: string;
  estimatedCost: string;
  materiality: string;
  warnings: string[];
  path?: string;
  generatedAt: string;
};

export type VerdictResultSummary = {
  status: string;
  stage: "decision_verdict";
  selectedCardId: string;
  candidateId: string;
  verdictId: string;
  decisionStatus: string;
  confidence: string;
  state: string;
  headline: string;
  explanation: string;
  evidenceQuality: string;
  boundaryNote: string;
  keyEvidence: string[];
  monitoringTrigger: string;
  metrics: Metric[];
  actionFraming: string;
  limitations: string[];
  path?: string;
  generatedAt: string;
};

export type ReviewStorageInfo = {
  summaryBytes: number;
  rawBytes: number;
  rawPersisted: false;
  rawAccessStrategy: string;
};

export type EvidenceSummary = {
  headline: string;
  quality: string;
  boundaryNote: string;
  items: EvidenceItem[];
  metrics: Metric[];
};

export type LaunchpadCardSummary = {
  card_id: string;
  title: string;
  goal?: string;
  hypothesis_to_test?: string;
  card_type?: string;
  source_problem_label?: string;
  suggested_methods: Array<{
    candidate_method_id: string;
    method_role?: string;
    why_this_method?: string;
  }>;
  default_method?: string;
  success_criteria: string[];
  tradeoff_to_watch?: string;
  when_to_skip?: string;
  decision_boundary?: string;
  is_rebalance_recommendation: boolean;
  generates_portfolio: boolean;
};

export type BuilderSetupSummary = {
  selected_card_id: string;
  can_generate_candidate: boolean;
  builder_prefill: {
    goal?: string;
    suggested_method?: string;
    constraint_preset?: string;
    max_asset_weight?: number | string;
    min_asset_weight?: number | string;
  };
  candidate_setup: {
    validation_status?: string;
    can_generate_candidate: boolean;
  };
};

export type ReviewSummary = {
  version: 1;
  source: ReviewRunMode;
  status: ReviewRunStatus;
  reviewId?: string;
  generatedAt: string;
  investorCurrency: string;
  holdingsCount: number;
  totalWeight: number;
  cashWeight: number;
  rawOutputKeys: string[];
  outputPaths: Record<string, string>;
  diagnosis: DiagnosisState;
  evidence?: EvidenceSummary;
  primaryProblem?: string;
  problemSeverity?: string;
  problemConfidence?: string;
  suggestedActionPaths: string[];
  launchpadCardsCount: number;
  launchpadCards: LaunchpadCardSummary[];
  builderSetup?: BuilderSetupSummary;
  recommendedFirstTest?: string;
  candidateLaunchpadAvailable: boolean;
  problemClassificationAvailable: boolean;
  storage: ReviewStorageInfo;
};

export type ActiveReviewState = {
  investorCurrency: string;
  holdings: ReviewHolding[];
  reviewId?: string;
  reviewResult?: ReviewResult;
  reviewSummary?: ReviewSummary;
  builderSetup?: BuilderSetupSummary;
  candidateGeneration?: CandidateGenerationSummary;
  comparisonResult?: ComparisonResultSummary;
  verdictResult?: VerdictResultSummary;
  runMode: ReviewRunMode;
  runStatus: ReviewRunStatus;
  reviewError?: ReviewErrorState;
  submitted: boolean;
  diagnosisReady: boolean;
  evidenceReady: boolean;
  improvementPathsReady: boolean;
  candidateReady: boolean;
  comparisonReady: boolean;
  verdictReady: boolean;
  updatedAt: string;
};

export type DiagnosisState = {
  status: string;
  headline: string;
  evidenceQuality: string;
  nextStep: string;
  boundaryNote: string;
  drivers: string[];
  metrics: Metric[];
};

type ReviewStateContextValue = {
  activeReview: ActiveReviewState | null;
  hydrated: boolean;
  savePortfolioInput: (input: Pick<ActiveReviewState, "investorCurrency" | "holdings">) => void;
  submitPortfolioInput: (input: Pick<ActiveReviewState, "investorCurrency" | "holdings" | "reviewResult">) => void;
  recordReviewError: (input: Pick<ActiveReviewState, "investorCurrency" | "holdings"> & { message: string; details?: string }) => void;
  recordBuilderSetup: (result: unknown) => void;
  recordCandidateGeneration: (result: unknown) => void;
  recordComparisonResult: (result: unknown) => void;
  recordVerdictResult: (result: unknown) => void;
  markCandidateReady: () => void;
  markComparisonReady: () => void;
  markVerdictReady: () => void;
  clearActiveReview: () => void;
  journeyFlags: JourneyFlags;
};

const ACTIVE_REVIEW_STORAGE_KEY = "pmri.activeReview.v2";
const LEGACY_ACTIVE_REVIEW_STORAGE_KEY = "pmri.activeReview.v1";
const RAW_REVIEW_STORAGE_PREFIX = "pmri.reviewResult."; // legacy cleanup only; raw review JSON is no longer persisted.
const ReviewStateContext = createContext<ReviewStateContextValue | null>(null);

function nowIso() {
  return new Date().toISOString();
}

function isRecord(value: unknown): value is Record<string, unknown> {
  return Boolean(value) && typeof value === "object" && !Array.isArray(value);
}

function isJsonValue(value: unknown): value is JsonValue {
  if (value === null) return true;
  if (["boolean", "number", "string"].includes(typeof value)) return true;
  if (Array.isArray(value)) return value.every(isJsonValue);
  if (isRecord(value)) return Object.values(value).every(isJsonValue);
  return false;
}

function cleanReviewResult(value: unknown): ReviewResult | undefined {
  if (!isRecord(value) || !isJsonValue(value)) return undefined;
  return value as ReviewResult;
}

function isCompletedReviewResult(value: unknown): value is ReviewResult {
  const result = cleanReviewResult(value);
  return Boolean(result?.status === "completed" && isRecord(result.outputs));
}

function estimateJsonBytes(value: unknown) {
  const raw = JSON.stringify(value ?? null);
  if (typeof TextEncoder !== "undefined") return new TextEncoder().encode(raw).length;
  return raw.length;
}

function cleanReviewSummary(value: unknown): ReviewSummary | undefined {
  if (!isRecord(value)) return undefined;
  if (value.version !== 1) return undefined;
  if (value.source !== "real_run" && value.source !== "sample_demo") return undefined;
  if (value.status !== "draft" && value.status !== "completed" && value.status !== "failed") return undefined;
  if (!isRecord(value.diagnosis)) return undefined;
  return value as ReviewSummary;
}

function cleanCandidateGenerationSummary(value: unknown): CandidateGenerationSummary | undefined {
  if (!isRecord(value)) return undefined;
  if (value.stage !== "candidate_generation") return undefined;
  const weights = Array.isArray(value.weights)
    ? value.weights
      .filter(isRecord)
      .map((item) => ({
        ticker: typeof item.ticker === "string" ? item.ticker : "",
        weight: typeof item.weight === "number" && Number.isFinite(item.weight) ? item.weight : Number.NaN
      }))
      .filter((item) => item.ticker && Number.isFinite(item.weight))
    : [];
  return {
    status: typeof value.status === "string" ? value.status : "unknown",
    stage: "candidate_generation",
    selectedCardId: typeof value.selectedCardId === "string" ? value.selectedCardId : "",
    candidateId: typeof value.candidateId === "string" ? value.candidateId : "",
    generationStatus: typeof value.generationStatus === "string" ? value.generationStatus : "unknown",
    canCompare: Boolean(value.canCompare),
    path: typeof value.path === "string" ? value.path : undefined,
    weights,
    generatedAt: typeof value.generatedAt === "string" ? value.generatedAt : nowIso()
  };
}

function cleanComparisonResultSummary(value: unknown): ComparisonResultSummary | undefined {
  if (!isRecord(value)) return undefined;
  if (value.stage !== "current_vs_candidate") return undefined;
  const metrics = Array.isArray(value.metrics)
    ? value.metrics.filter(isRecord).map((item) => ({
      metric: textValue(item.metric, "Metric"),
      current: textValue(item.current, "n/a"),
      candidate: textValue(item.candidate, "n/a"),
      direction: textValue(item.direction, "unclear"),
      tradeoff: textValue(item.tradeoff, "Evidence only; no action implied."),
      tone: statusToneValue(item.tone)
    }))
    : [];
  return {
    status: textValue(value.status, "unknown"),
    stage: "current_vs_candidate",
    selectedCardId: textValue(value.selectedCardId, ""),
    candidateId: textValue(value.candidateId, ""),
    comparisonStatus: textValue(value.comparisonStatus, "unknown"),
    viewMode: textValue(value.viewMode, "unknown"),
    candidateName: textValue(value.candidateName, "Generated diagnostic candidate"),
    candidateBoundary: textValue(value.candidateBoundary, "Diagnostic comparison only. This is not a recommendation or trade instruction."),
    evidenceQuality: textValue(value.evidenceQuality, "Evidence status unavailable"),
    summary: textValue(value.summary, "Current and candidate portfolios were compared by the backend."),
    metrics,
    improved: stringArray(value.improved),
    worsened: stringArray(value.worsened),
    neutral: stringArray(value.neutral),
    unclear: stringArray(value.unclear),
    turnover: textValue(value.turnover, "Turnover unavailable"),
    estimatedCost: textValue(value.estimatedCost, "Estimated cost unavailable"),
    materiality: textValue(value.materiality, "Materiality not evaluated"),
    warnings: stringArray(value.warnings),
    path: typeof value.path === "string" ? value.path : undefined,
    generatedAt: textValue(value.generatedAt, nowIso())
  };
}

function cleanVerdictResultSummary(value: unknown): VerdictResultSummary | undefined {
  if (!isRecord(value)) return undefined;
  if (value.stage !== "decision_verdict") return undefined;
  const metrics = Array.isArray(value.metrics)
    ? value.metrics.filter(isRecord).map((item) => ({
      label: textValue(item.label, "Metric"),
      value: textValue(item.value, "n/a"),
      detail: typeof item.detail === "string" ? item.detail : undefined,
      tone: statusToneValue(item.tone),
      delta: typeof item.delta === "string" ? item.delta : undefined
    }))
    : [];
  return {
    status: textValue(value.status, "unknown"),
    stage: "decision_verdict",
    selectedCardId: textValue(value.selectedCardId, ""),
    candidateId: textValue(value.candidateId, ""),
    verdictId: textValue(value.verdictId, "unknown"),
    decisionStatus: textValue(value.decisionStatus, "unknown"),
    confidence: textValue(value.confidence, "unknown"),
    state: textValue(value.state, "Decision-support verdict"),
    headline: textValue(value.headline, "Decision verdict generated."),
    explanation: textValue(value.explanation, "The backend generated a decision-support verdict for the active review."),
    evidenceQuality: textValue(value.evidenceQuality, "Evidence status unavailable"),
    boundaryNote: textValue(value.boundaryNote, "Decision-support only. This is not a recommendation or trade instruction."),
    keyEvidence: stringArray(value.keyEvidence),
    monitoringTrigger: textValue(value.monitoringTrigger, "Monitor changes in comparison evidence before revisiting the verdict."),
    metrics,
    actionFraming: textValue(value.actionFraming, "Review the verdict as decision-support evidence only."),
    limitations: stringArray(value.limitations),
    path: typeof value.path === "string" ? value.path : undefined,
    generatedAt: textValue(value.generatedAt, nowIso())
  };
}

function cleanReviewState(value: ActiveReviewState): ActiveReviewState {
  const reviewResult = cleanReviewResult(value.reviewResult);
  const reviewSummary = cleanReviewSummary(value.reviewSummary);
  const runStatus: ReviewRunStatus = value.runStatus === "failed" ? "failed" : isCompletedReviewResult(reviewResult) || reviewSummary?.status === "completed" ? "completed" : "draft";
  const builderSetup = compactBuilderSetup(value.builderSetup) ?? reviewSummary?.builderSetup;
  const candidateGenerationRaw = cleanCandidateGenerationSummary(value.candidateGeneration);
  const candidateMatchesBuilder = Boolean(
    candidateGenerationRaw
    && (!builderSetup || candidateGenerationRaw.selectedCardId === builderSetup.selected_card_id)
  );
  const candidateGeneration = candidateMatchesBuilder ? candidateGenerationRaw : undefined;
  const comparisonResult = cleanComparisonResultSummary(value.comparisonResult);
  const verdictResult = cleanVerdictResultSummary(value.verdictResult);
  const comparisonMatchesCandidate = Boolean(
    comparisonResult
    && candidateGeneration
    && comparisonResult.selectedCardId === candidateGeneration.selectedCardId
    && comparisonResult.candidateId === candidateGeneration.candidateId
  );
  const verdictMatchesCandidate = Boolean(
    verdictResult
    && candidateGeneration
    && verdictResult.selectedCardId === candidateGeneration.selectedCardId
    && verdictResult.candidateId === candidateGeneration.candidateId
  );
  const hasCompletedReviewResult = runStatus === "completed" && Boolean(reviewResult || reviewSummary);

  return {
    investorCurrency: value.investorCurrency || "USD",
    holdings: Array.isArray(value.holdings)
      ? value.holdings
        .filter((holding) => holding.id && holding.ticker && Number.isFinite(holding.weight))
        .map((holding) => ({
          id: holding.id,
          label: holding.label || holding.ticker,
          ticker: holding.ticker,
          instrument: holding.instrument,
          weight: holding.weight,
          type: holding.type === "cash" ? "cash" : "instrument",
          currency: holding.currency
        }))
      : [],
    submitted: Boolean(value.submitted),
    reviewId: typeof value.reviewId === "string" ? value.reviewId : reviewSummary?.reviewId ?? reviewResult?.review_id,
    reviewResult,
    reviewSummary,
    builderSetup,
    candidateGeneration,
    comparisonResult: comparisonMatchesCandidate ? comparisonResult : undefined,
    verdictResult: verdictMatchesCandidate ? verdictResult : undefined,
    runMode: value.runMode === "real_run" ? "real_run" : "sample_demo",
    runStatus,
    reviewError: value.reviewError?.message ? value.reviewError : undefined,
    diagnosisReady: Boolean(value.diagnosisReady && hasCompletedReviewResult),
    evidenceReady: Boolean((value.evidenceReady ?? value.diagnosisReady) && hasCompletedReviewResult),
    improvementPathsReady: Boolean((value.improvementPathsReady ?? value.diagnosisReady) && hasCompletedReviewResult),
    candidateReady: Boolean(value.candidateReady && candidateGeneration),
    comparisonReady: Boolean(value.comparisonReady && comparisonMatchesCandidate),
    verdictReady: Boolean(value.verdictReady && verdictMatchesCandidate),
    updatedAt: value.updatedAt || nowIso()
  };
}

function readStoredReview(): ActiveReviewState | null {
  if (typeof window === "undefined") return null;

  try {
    const raw = window.localStorage.getItem(ACTIVE_REVIEW_STORAGE_KEY)
      ?? window.localStorage.getItem(LEGACY_ACTIVE_REVIEW_STORAGE_KEY);
    if (!raw) return null;

    const parsed = JSON.parse(raw) as ActiveReviewState;
    removeStoredRawReviews();

    return cleanReviewState({
      ...parsed,
      reviewResult: undefined
    } as ActiveReviewState);
  } catch {
    return null;
  }
}

function removeStoredRawReviews(exceptKey?: string) {
  if (typeof window === "undefined") return;

  Object.keys(window.localStorage)
    .filter((key) => key.startsWith(RAW_REVIEW_STORAGE_PREFIX) && key !== exceptKey)
    .forEach((key) => window.localStorage.removeItem(key));
}

function writeStoredReview(value: ActiveReviewState | null) {
  if (typeof window === "undefined") return;

  if (!value) {
    window.localStorage.removeItem(ACTIVE_REVIEW_STORAGE_KEY);
    window.localStorage.removeItem(LEGACY_ACTIVE_REVIEW_STORAGE_KEY);
    removeStoredRawReviews();
    return;
  }

  const clean = cleanReviewState(value);
  removeStoredRawReviews();

  const compactState = {
    ...clean,
    reviewResult: undefined
  } satisfies ActiveReviewState;

  window.localStorage.setItem(ACTIVE_REVIEW_STORAGE_KEY, JSON.stringify(compactState));
}

export function ReviewStateProvider({ children }: { children: ReactNode }) {
  const [activeReview, setActiveReview] = useState<ActiveReviewState | null>(null);
  const [hydrated, setHydrated] = useState(false);

  useEffect(() => {
    setActiveReview(readStoredReview());
    setHydrated(true);
  }, []);

  useEffect(() => {
    if (!hydrated) return;
    writeStoredReview(activeReview);
  }, [activeReview, hydrated]);

  const savePortfolioInput = useCallback((input: Pick<ActiveReviewState, "investorCurrency" | "holdings">) => {
    setActiveReview((current) => ({
      investorCurrency: input.investorCurrency || "USD",
      holdings: input.holdings,
      reviewId: undefined,
      reviewResult: undefined,
      reviewSummary: undefined,
      builderSetup: undefined,
      candidateGeneration: undefined,
      comparisonResult: undefined,
      verdictResult: undefined,
      runMode: "sample_demo",
      runStatus: "draft",
      reviewError: undefined,
      submitted: current?.submitted ?? false,
      diagnosisReady: false,
      evidenceReady: false,
      improvementPathsReady: false,
      candidateReady: false,
      comparisonReady: false,
      verdictReady: false,
      updatedAt: nowIso()
    }));
  }, []);

  const submitPortfolioInput = useCallback((input: Pick<ActiveReviewState, "investorCurrency" | "holdings" | "reviewResult">) => {
    const reviewResult = cleanReviewResult(input.reviewResult);
    const hasCompletedReviewResult = isCompletedReviewResult(reviewResult);
    const failedReviewResult = reviewResult as ReviewResult | undefined;
    const reviewId = reviewResult?.review_id;

    const reviewSummary = hasCompletedReviewResult
      ? buildCompactReviewSummary({
        investorCurrency: input.investorCurrency || "USD",
        holdings: input.holdings,
        reviewResult
      })
      : undefined;

    setActiveReview({
      investorCurrency: input.investorCurrency || "USD",
      holdings: input.holdings,
      reviewId,
      reviewResult,
      reviewSummary,
      builderSetup: reviewSummary?.builderSetup,
      candidateGeneration: undefined,
      comparisonResult: undefined,
      verdictResult: undefined,
      runMode: "real_run",
      runStatus: hasCompletedReviewResult ? "completed" : "failed",
      reviewError: hasCompletedReviewResult ? undefined : {
        message: failedReviewResult?.error || "Portfolio diagnosis failed.",
        details: typeof failedReviewResult?.details === "string" ? failedReviewResult.details : undefined,
        occurredAt: nowIso()
      },
      submitted: true,
      diagnosisReady: hasCompletedReviewResult,
      evidenceReady: hasCompletedReviewResult,
      improvementPathsReady: hasCompletedReviewResult,
      candidateReady: false,
      comparisonReady: false,
      verdictReady: false,
      updatedAt: nowIso()
    });
  }, []);

  const recordReviewError = useCallback((input: Pick<ActiveReviewState, "investorCurrency" | "holdings"> & { message: string; details?: string }) => {
    setActiveReview({
      investorCurrency: input.investorCurrency || "USD",
      holdings: input.holdings,
      reviewId: undefined,
      reviewResult: undefined,
      reviewSummary: undefined,
      builderSetup: undefined,
      candidateGeneration: undefined,
      comparisonResult: undefined,
      verdictResult: undefined,
      runMode: "real_run",
      runStatus: "failed",
      reviewError: {
        message: input.message,
        details: input.details,
        occurredAt: nowIso()
      },
      submitted: true,
      diagnosisReady: false,
      evidenceReady: false,
      improvementPathsReady: false,
      candidateReady: false,
      comparisonReady: false,
      verdictReady: false,
      updatedAt: nowIso()
    });
  }, []);


  const recordBuilderSetup = useCallback((result: unknown) => {
    const resultRecord = getRecord(result);
    const setup = compactBuilderSetup(resultRecord.portfolio_alternatives_builder);
    const selectedCardId = textValue(resultRecord.selected_card_id, setup?.selected_card_id ?? "");
    const summary = setup
      ? {
        ...setup,
        selected_card_id: selectedCardId || setup.selected_card_id,
        can_generate_candidate: resultRecord.can_generate_candidate === true || setup.can_generate_candidate
      }
      : undefined;

    if (!summary) return;

    setActiveReview((current) => current ? {
      ...current,
      builderSetup: summary,
      reviewSummary: current.reviewSummary ? {
        ...current.reviewSummary,
        builderSetup: summary
      } : current.reviewSummary,
      reviewResult: current.reviewResult && isRecord(current.reviewResult.outputs) ? {
        ...current.reviewResult,
        outputs: {
          ...current.reviewResult.outputs,
          portfolio_alternatives_builder: resultRecord.portfolio_alternatives_builder as JsonValue
        }
      } : current.reviewResult,
      candidateGeneration: undefined,
      comparisonResult: undefined,
      verdictResult: undefined,
      candidateReady: false,
      comparisonReady: false,
      verdictReady: false,
      updatedAt: nowIso()
    } : current);
  }, []);

  const markCandidateReady = useCallback(() => {
    setActiveReview((current) => current ? {
      ...current,
      candidateReady: true,
      comparisonReady: false,
      verdictReady: false,
      updatedAt: nowIso()
    } : current);
  }, []);

  const recordCandidateGeneration = useCallback((result: unknown) => {
    const resultRecord = getRecord(result);
    const candidateGeneration = getRecord(resultRecord.candidate_generation);
    const candidate = getRecord(candidateGeneration.candidate);
    const weightsRecord = getRecord(candidate.weights);
    const weights = Object.entries(weightsRecord)
      .filter((entry): entry is [string, number] => typeof entry[1] === "number" && Number.isFinite(entry[1]))
      .map(([ticker, weight]) => ({ ticker, weight }));
    const status = textValue(resultRecord.status, "unknown");
    const summary: CandidateGenerationSummary = {
      status,
      stage: "candidate_generation",
      selectedCardId: textValue(resultRecord.selected_card_id, ""),
      candidateId: textValue(resultRecord.candidate_id, textValue(candidate.candidate_id, "")),
      generationStatus: textValue(resultRecord.generation_status, textValue(candidateGeneration.generation_status, "unknown")),
      canCompare: Boolean(resultRecord.can_compare),
      path: typeof resultRecord.path === "string" ? resultRecord.path : undefined,
      weights,
      generatedAt: nowIso()
    };

    setActiveReview((current) => current ? {
      ...current,
      candidateGeneration: summary,
      candidateReady: status === "completed",
      comparisonResult: undefined,
      verdictResult: undefined,
      comparisonReady: false,
      verdictReady: false,
      updatedAt: nowIso()
    } : current);
  }, []);

  const recordComparisonResult = useCallback((result: unknown) => {
    const resultRecord = getRecord(result);
    const currentVsCandidate = getRecord(resultRecord.current_vs_candidate);
    const comparisons = getArray(currentVsCandidate.comparisons).map(getRecord);
    const row = comparisons[0] ?? {};
    const dimensions = getArray(row.dimensions).map(getRecord);
    const practicality = getRecord(row.practicality);
    const turnoverRequired = getRecord(practicality.turnover_required);
    const transactionCost = getRecord(practicality.transaction_cost_assumption);
    const materiality = getRecord(row.materiality_for_decision_review);
    const successCriteria = getRecord(row.success_criteria_result);
    const paths = getRecord(resultRecord.paths);
    const status = textValue(resultRecord.status, "unknown");
    const comparisonStatus = textValue(resultRecord.comparison_status, textValue(currentVsCandidate.comparison_status, "unknown"));
    const summary: ComparisonResultSummary = {
      status,
      stage: "current_vs_candidate",
      selectedCardId: textValue(resultRecord.selected_card_id, ""),
      candidateId: textValue(resultRecord.candidate_id, textValue(row.candidate_id, "")),
      comparisonStatus,
      viewMode: textValue(resultRecord.view_mode, textValue(currentVsCandidate.view_mode, "unknown")),
      candidateName: textValue(row.display_name, textValue(row.candidate_id, "Generated diagnostic candidate")),
      candidateBoundary: "Diagnostic comparison only. This is not a recommendation, winner selection, or trade instruction.",
      evidenceQuality: comparisonStatus === "available" ? "Active backend comparison" : comparisonStatus.replaceAll("_", " "),
      summary: comparisonSummaryText({ row, materiality, successCriteria }),
      metrics: dimensionsToMetrics(dimensions),
      improved: compactDimensionList(row.what_improved, "No clear improvement was found in available comparison metrics."),
      worsened: compactDimensionList(row.what_worsened, "No clear worsening was found in available comparison metrics."),
      neutral: compactDimensionList(row.what_stayed_similar, "No neutral metrics were reported."),
      unclear: unclearList(row, currentVsCandidate),
      turnover: turnoverText(turnoverRequired),
      estimatedCost: estimatedCostText(practicality, transactionCost),
      materiality: materialityText(materiality),
      warnings: stringArray(currentVsCandidate.warnings),
      path: typeof paths.current_vs_candidate === "string" ? paths.current_vs_candidate : undefined,
      generatedAt: nowIso()
    };

    setActiveReview((current) => current ? {
      ...current,
      comparisonResult: summary,
      verdictResult: undefined,
      candidateReady: true,
      comparisonReady: status === "completed" && comparisonStatus === "available",
      verdictReady: false,
      updatedAt: nowIso()
    } : current);
  }, []);

  const markComparisonReady = useCallback(() => {
    setActiveReview((current) => current ? {
      ...current,
      candidateReady: true,
      comparisonReady: true,
      verdictReady: false,
      updatedAt: nowIso()
    } : current);
  }, []);

  const markVerdictReady = useCallback(() => {
    setActiveReview((current) => current ? {
      ...current,
      candidateReady: true,
      comparisonReady: true,
      verdictReady: true,
      updatedAt: nowIso()
    } : current);
  }, []);

  const recordVerdictResult = useCallback((result: unknown) => {
    const resultRecord = getRecord(result);
    const verdict = getRecord(resultRecord.decision_verdict);
    const evidence = getRecord(verdict.evidence_summary);
    const noTrade = getRecord(verdict.no_trade);
    const source = getRecord(noTrade.source);
    const materiality = getRecord(evidence.materiality_for_decision_review);
    const success = getRecord(evidence.success_criteria_result);
    const practicality = getRecord(evidence.practicality);
    const status = textValue(resultRecord.status, "unknown");
    const verdictId = textValue(resultRecord.verdict_id, textValue(verdict.verdict_id, "unknown"));
    const decisionStatus = textValue(resultRecord.selection_decision_status, textValue(verdict.selection_decision_status, "unknown"));
    const confidence = textValue(resultRecord.confidence, textValue(verdict.confidence, "unknown"));
    const candidateId = textValue(resultRecord.candidate_id, textValue(verdict.reviewed_candidate_id, textValue(verdict.selected_candidate_id, "")));

    const summary: VerdictResultSummary = {
      status,
      stage: "decision_verdict",
      selectedCardId: textValue(resultRecord.selected_card_id, ""),
      candidateId,
      verdictId,
      decisionStatus,
      confidence,
      state: safeVerdictState(verdictId, decisionStatus),
      headline: safeVerdictHeadline(verdictId, candidateId),
      explanation: safeVerdictExplanation(verdictId, textValue(verdict.rationale_summary, "")),
      evidenceQuality: `Backend verdict · ${confidence} confidence`,
      boundaryNote: "Decision-support only. This page does not recommend trades, execute trades, or identify a best portfolio.",
      keyEvidence: verdictEvidenceList({
        evidence,
        materiality,
        success,
        noTrade,
        limitations: verdict.confidence_limitations
      }),
      monitoringTrigger: verdictMonitoringTrigger(verdictId, verdict.confidence_limitations),
      metrics: [
        {
          label: "Verdict status",
          value: safeVerdictState(verdictId, decisionStatus),
          detail: decisionStatus.replaceAll("_", " "),
          tone: verdictTone(verdictId)
        },
        {
          label: "No-trade",
          value: noTrade.applies === true ? "Applies" : noTrade.evaluated === true ? "Evaluated" : "Not evaluated",
          detail: textValue(getRecord(source).reason_id, "Backend Block 9 evidence"),
          tone: noTrade.applies === true ? "green" : noTrade.evaluated === true ? "blue" : "slate"
        },
        {
          label: "Confidence",
          value: confidence,
          detail: `${stringArray(verdict.confidence_limitations).length} limitation(s)`,
          tone: confidence === "low" ? "amber" : "blue"
        }
      ],
      actionFraming: safeActionFraming(verdictId, candidateId),
      limitations: stringArray(verdict.confidence_limitations),
      path: typeof resultRecord.path === "string" ? resultRecord.path : undefined,
      generatedAt: nowIso()
    };

    setActiveReview((current) => current ? {
      ...current,
      verdictResult: summary,
      candidateReady: true,
      comparisonReady: true,
      verdictReady: status === "completed",
      updatedAt: nowIso()
    } : current);
  }, []);

  const clearActiveReview = useCallback(() => setActiveReview(null), []);

  const journeyFlags = useMemo<JourneyFlags>(() => ({
    inputCompleted: Boolean(activeReview?.submitted),
    diagnosisGenerated: Boolean(activeReview?.diagnosisReady),
    evidenceGenerated: Boolean(activeReview?.evidenceReady),
    improvementPathsAvailable: Boolean(activeReview?.improvementPathsReady),
    candidateReady: Boolean(activeReview?.candidateReady),
    comparisonReady: Boolean(activeReview?.comparisonReady),
    verdictReady: Boolean(activeReview?.verdictReady)
  }), [activeReview]);

  const value = useMemo<ReviewStateContextValue>(() => ({
    activeReview,
    hydrated,
    savePortfolioInput,
    submitPortfolioInput,
    recordReviewError,
    recordBuilderSetup,
    recordCandidateGeneration,
    recordComparisonResult,
    recordVerdictResult,
    markCandidateReady,
    markComparisonReady,
    markVerdictReady,
    clearActiveReview,
    journeyFlags
  }), [activeReview, clearActiveReview, hydrated, journeyFlags, markCandidateReady, markComparisonReady, markVerdictReady, recordBuilderSetup, recordCandidateGeneration, recordComparisonResult, recordReviewError, recordVerdictResult, savePortfolioInput, submitPortfolioInput]);

  return <ReviewStateContext.Provider value={value}>{children}</ReviewStateContext.Provider>;
}

export function useReviewState() {
  const value = useContext(ReviewStateContext);
  if (!value) {
    throw new Error("useReviewState must be used within ReviewStateProvider");
  }
  return value;
}

function formatPercent(value: number) {
  return `${value.toFixed(2).replace(/\.?0+$/, "")}%`;
}

function formatDecimalPercent(value: unknown) {
  return typeof value === "number" && Number.isFinite(value) ? formatPercent(value * 100) : "n/a";
}

function formatRawPercent(value: unknown) {
  return typeof value === "number" && Number.isFinite(value) ? formatPercent(value) : "n/a";
}

function getRecord(value: unknown): Record<string, unknown> {
  return isRecord(value) ? value : {};
}

function getArray(value: unknown): unknown[] {
  return Array.isArray(value) ? value : [];
}

function textValue(value: unknown, fallback = "n/a") {
  return typeof value === "string" && value.trim() ? value : fallback;
}

function stringArray(value: unknown): string[] {
  return Array.isArray(value)
    ? value.map((item) => (typeof item === "string" ? item.trim() : "")).filter(Boolean)
    : [];
}

function numericValue(value: unknown): number | null {
  return typeof value === "number" && Number.isFinite(value) ? value : null;
}

function firstStringFromArrays(...sources: unknown[]) {
  for (const source of sources) {
    const first = stringArray(source)[0];
    if (first) return first;
  }
  return null;
}

function statusToneValue(value: unknown): StatusTone {
  return value === "blue" || value === "gold" || value === "green" || value === "amber" || value === "red" || value === "slate"
    ? value
    : "slate";
}

function toneForLoss(value: unknown): StatusTone {
  const parsed = numericValue(value);
  if (parsed === null) return "slate";
  if (parsed <= -0.12) return "red";
  if (parsed <= -0.06) return "amber";
  return "blue";
}

function verdictTone(verdictId: string): StatusTone {
  if (verdictId === "no_material_rebalance_recommended") return "green";
  if (verdictId === "evidence_insufficient" || verdictId === "candidate_failed_or_infeasible") return "amber";
  if (verdictId === "test_another_candidate_or_review_evidence") return "blue";
  return "gold";
}

function safeVerdictState(verdictId: string, decisionStatus: string) {
  if (verdictId === "no_material_rebalance_recommended") return "No-trade is supported by current evidence";
  if (verdictId === "evidence_insufficient") return "Evidence insufficient";
  if (verdictId === "candidate_failed_or_infeasible") return "Candidate failed or infeasible";
  if (verdictId === "test_another_candidate_or_review_evidence") return "Test another hypothesis or review evidence";
  if (decisionStatus === "selected_candidate") return "Candidate is material enough for decision review";
  return decisionStatus.replaceAll("_", " ");
}

function safeVerdictHeadline(verdictId: string, candidateId: string) {
  const candidate = candidateId || "selected candidate";
  if (verdictId === "no_material_rebalance_recommended") return "Keep the current portfolio under review.";
  if (verdictId === "evidence_insufficient") return "Do not make a decision from this evidence yet.";
  if (verdictId === "candidate_failed_or_infeasible") return "The candidate test did not produce actionable comparison evidence.";
  if (verdictId === "test_another_candidate_or_review_evidence") return "The evidence is mixed; test another diagnostic hypothesis.";
  return `${candidate} passed the materiality review gate.`;
}

function safeVerdictExplanation(verdictId: string, rationale: string) {
  const suffix = rationale ? ` Backend rationale: ${rationale}` : "";
  if (verdictId === "no_material_rebalance_recommended") {
    return `The current evidence supports no material change. Continue monitoring instead of treating the candidate as an instruction.${suffix}`;
  }
  if (verdictId === "evidence_insufficient") {
    return `The backend found missing or degraded evidence, so the verdict stays evidence-insufficient.${suffix}`;
  }
  if (verdictId === "candidate_failed_or_infeasible") {
    return `The generated candidate failed or was infeasible, so it cannot become an action verdict.${suffix}`;
  }
  if (verdictId === "test_another_candidate_or_review_evidence") {
    return `The comparison does not support a clear action/no-action decision. Review evidence or test another candidate.${suffix}`;
  }
  return `The selected candidate is material enough for human decision review, but this UI does not create a trade or implementation instruction.${suffix}`;
}

function safeActionFraming(verdictId: string, candidateId: string) {
  if (verdictId === "no_material_rebalance_recommended") return "Action framing: no material change; keep monitoring the current portfolio.";
  if (verdictId === "evidence_insufficient") return "Action framing: collect or repair evidence before making a decision.";
  if (verdictId === "candidate_failed_or_infeasible") return "Action framing: discard this failed test and choose another diagnostic hypothesis if needed.";
  if (verdictId === "test_another_candidate_or_review_evidence") return "Action framing: review trade-offs or test another candidate; no action is implied.";
  return `Action framing: review ${candidateId || "the selected candidate"} with its documented trade-offs; no trade instruction is created.`;
}

function verdictEvidenceList({
  evidence,
  materiality,
  success,
  noTrade,
  limitations
}: {
  evidence: Record<string, unknown>;
  materiality: Record<string, unknown>;
  success: Record<string, unknown>;
  noTrade: Record<string, unknown>;
  limitations: unknown;
}) {
  const rows = [
    `Generation status: ${textValue(evidence.generation_status, "unknown").replaceAll("_", " ")}.`,
    `Decision materiality: ${textValue(materiality.status, "not evaluated").replaceAll("_", " ")} (${textValue(materiality.reason, "no reason supplied")}).`,
    `Success criteria: ${textValue(success.overall_status, "not evaluated").replaceAll("_", " ")}.`,
    `No-trade gate: ${noTrade.applies === true ? "applies" : noTrade.evaluated === true ? "evaluated" : "not evaluated"}.`
  ];
  const firstLimit = stringArray(limitations)[0];
  if (firstLimit) rows.push(`Main confidence limitation: ${firstLimit}.`);
  return rows;
}

function verdictMonitoringTrigger(verdictId: string, limitations: unknown) {
  const firstLimit = stringArray(limitations)[0];
  if (verdictId === "evidence_insufficient") return firstLimit ? `Re-run the verdict after resolving: ${firstLimit}.` : "Re-run after missing evidence is available.";
  if (verdictId === "candidate_failed_or_infeasible") return "Re-run only after selecting a different feasible diagnostic candidate.";
  if (verdictId === "no_material_rebalance_recommended") return "Revisit if comparison materiality, turnover, or stress evidence changes materially.";
  return "Revisit before any implementation decision if trade-offs, costs, or risk evidence changes.";
}

function formatSignedDelta(value: unknown, field?: string) {
  if (typeof value !== "number" || !Number.isFinite(value)) return "Delta n/a";
  const sign = value > 0 ? "+" : "";
  if (field && percentLikeField(field)) return `${sign}${formatDecimalPercent(value)}`;
  return `${sign}${value.toFixed(3).replace(/\.?0+$/, "")}`;
}

function percentLikeField(field: string) {
  return [
    "cagr",
    "vol_annual",
    "max_drawdown",
    "worst_stress_loss",
    "weight_",
    "rc_"
  ].some((prefix) => field === prefix || field.startsWith(prefix));
}

function formatComparisonValue(value: unknown, field?: string) {
  if (typeof value !== "number" || !Number.isFinite(value)) return "n/a";
  if (field && percentLikeField(field)) return formatDecimalPercent(value);
  return value.toFixed(3).replace(/\.?0+$/, "");
}

function toneFromDirection(direction: string): StatusTone {
  if (direction === "improved") return "green";
  if (direction === "worse") return "amber";
  if (direction === "flat") return "slate";
  return "slate";
}

function directionLabel(direction: string) {
  if (direction === "improved") return "Improved";
  if (direction === "worse") return "Worsened";
  if (direction === "flat") return "Neutral";
  return "Unclear";
}

function dimensionsToMetrics(dimensions: Record<string, unknown>[]): ComparisonMetric[] {
  return dimensions.slice(0, 10).map((dimension) => {
    const field = textValue(dimension.field, "");
    const direction = textValue(dimension.direction, "unknown");
    const status = textValue(dimension.status, "unavailable");
    return {
      metric: textValue(dimension.label, field || "Metric"),
      current: formatComparisonValue(dimension.baseline_value, field),
      candidate: formatComparisonValue(dimension.candidate_value, field),
      direction: status === "available" ? directionLabel(direction) : "Unclear",
      tradeoff: status === "available"
        ? formatSignedDelta(dimension.delta, field)
        : textValue(dimension.unavailable_reason, "Metric unavailable"),
      tone: status === "available" ? toneFromDirection(direction) : "slate"
    };
  });
}

function compactDimensionList(value: unknown, fallback: string) {
  const rows = getArray(value)
    .map(getRecord)
    .map((item) => {
      const label = textValue(item.label, textValue(item.field, ""));
      const direction = textValue(item.direction, "changed");
      const delta = formatSignedDelta(item.delta, textValue(item.field, ""));
      return label ? `${label}: ${directionLabel(direction).toLowerCase()} (${delta}).` : "";
    })
    .filter(Boolean);
  return rows.length ? rows : [fallback];
}

function unclearList(row: Record<string, unknown>, currentVsCandidate: Record<string, unknown>) {
  const unavailable = getArray(getRecord(row.tradeoff_summary).unavailable_metrics)
    .map(getRecord)
    .map((item) => `${textValue(item.label, textValue(item.field, "Metric"))}: ${textValue(item.unavailable_reason, "unavailable")}.`);
  const warnings = stringArray(currentVsCandidate.warnings).map((item) => `Warning: ${item}.`);
  const result = [...unavailable, ...warnings].filter(Boolean).slice(0, 4);
  return result.length ? result : ["Suitability and mandate fit remain outside this comparison step."];
}

function turnoverText(turnoverRequired: Record<string, unknown>) {
  const status = textValue(turnoverRequired.status, "unavailable");
  const turnover = turnoverRequired.turnover_half_sum_pct;
  if (status === "available" && typeof turnover === "number" && Number.isFinite(turnover)) {
    return `${formatDecimalPercent(turnover)} half-sum turnover required.`;
  }
  return `Turnover ${status.replaceAll("_", " ")}.`;
}

function estimatedCostText(practicality: Record<string, unknown>, transactionCost: Record<string, unknown>) {
  const estimated = practicality.estimated_transaction_cost_pct;
  const bps = transactionCost.transaction_cost_bps;
  if (typeof estimated === "number" && Number.isFinite(estimated)) {
    const assumption = typeof bps === "number" && Number.isFinite(bps) ? ` using ${bps} bps assumption` : "";
    return `${formatDecimalPercent(estimated)} estimated transaction cost${assumption}.`;
  }
  return "Estimated transaction cost unavailable.";
}

function materialityText(materiality: Record<string, unknown>) {
  return `${textValue(materiality.status, "not evaluated").replaceAll("_", " ")}: ${textValue(materiality.reason, "no reason supplied")}.`;
}

function comparisonSummaryText({
  row,
  materiality,
  successCriteria
}: {
  row: Record<string, unknown>;
  materiality: Record<string, unknown>;
  successCriteria: Record<string, unknown>;
}) {
  const improvedCount = getArray(row.what_improved).length;
  const worsenedCount = getArray(row.what_worsened).length;
  const neutralCount = getArray(row.what_stayed_similar).length;
  return [
    `Backend comparison found ${improvedCount} improved, ${worsenedCount} worsened, and ${neutralCount} neutral metric groups.`,
    `Success criteria: ${textValue(successCriteria.overall_status, "not evaluated").replaceAll("_", " ")}.`,
    `Decision review materiality: ${textValue(materiality.status, "not evaluated").replaceAll("_", " ")}.`
  ].join(" ");
}

function buildDiagnosisFromRealResult(review: ActiveReviewState): DiagnosisState | null {
  if (!isCompletedReviewResult(review.reviewResult)) return null;

  const outputs = getRecord(review.reviewResult.outputs);
  const xray = getRecord(outputs.portfolio_xray);
  const stress = getRecord(outputs.stress_report);
  const allocation = getRecord(xray.block_2_1_asset_allocation);
  const metricsBlock = getRecord(xray.block_2_2_portfolio_metrics);
  const weaknessMap = getRecord(xray.block_2_6_portfolio_weakness_map);
  const composition = getRecord(allocation.portfolio_composition_snapshot);
  const behavior = getRecord(metricsBlock.portfolio_behavior_snapshot);
  const returnRisk = getRecord(metricsBlock.return_risk_metrics);
  const drawdown = getRecord(metricsBlock.drawdown_diagnostics);
  const stressConclusions = getRecord(stress.stress_conclusions);
  const worstScenario = getRecord(stressConclusions.worst_synthetic_scenario);
  const topHolding = getRecord(composition.top1_holding);
  const dominantAssetClass = getRecord(composition.dominant_asset_class);
  const riskTypes = getArray(weaknessMap.risk_types)
    .map(getRecord)
    .filter((item) => typeof item.risk_title === "string")
    .sort((a, b) => (Number(b.score_0_100) || 0) - (Number(a.score_0_100) || 0));

  const primaryRisk = riskTypes[0];
  const xrayHeadline = textValue(behavior.headline, "Portfolio X-Ray completed for the submitted current portfolio.");
  const allocationHeadline = textValue(getRecord(allocation.actual_economic_exposure_summary).headline, "");
  const stressStatus = textValue(stress.status, "unknown");
  const worstScenarioId = textValue(worstScenario.scenario_id, "n/a");
  const worstScenarioLoss = formatDecimalPercent(worstScenario.portfolio_pnl_pct);

  const drivers = [
    topHolding.ticker
      ? `${String(topHolding.ticker)} is the largest holding at ${formatRawPercent(topHolding.weight_pct)}.`
      : "Portfolio X-Ray returned the current allocation snapshot.",
    dominantAssetClass.name
      ? `Dominant asset class: ${String(dominantAssetClass.name)} at ${formatRawPercent(dominantAssetClass.weight_pct)}.`
      : allocationHeadline || "Asset allocation diagnostics are available from Portfolio X-Ray.",
    primaryRisk
      ? textValue(primaryRisk.short_diagnosis, `${String(primaryRisk.risk_title)} is the top pre-stress weakness.`)
      : `Stress status is ${stressStatus}; worst synthetic scenario is ${worstScenarioId} (${worstScenarioLoss}).`
  ];

  return {
    status: "Diagnosis ready",
    headline: xrayHeadline,
    evidenceQuality: `Real backend review · ${textValue(stressConclusions.overall_confidence, "confidence n/a")} stress confidence`,
    nextStep: "Review Evidence before testing one candidate hypothesis.",
    boundaryNote: "Diagnosis is rendered from the returned portfolio_xray and stress_report for the submitted portfolio.",
    drivers,
    metrics: [
      {
        label: "CAGR / Volatility",
        value: `${formatDecimalPercent(returnRisk.portfolio_cagr)} / ${formatDecimalPercent(returnRisk.vol_annual)}`,
        detail: `Sharpe ${typeof returnRisk.sharpe === "number" ? returnRisk.sharpe.toFixed(2) : "n/a"}`,
        tone: "blue"
      },
      {
        label: "Max drawdown",
        value: formatDecimalPercent(drawdown.max_drawdown),
        detail: textValue(behavior.overall_behavior_label, "Portfolio behavior"),
        tone: "amber"
      },
      {
        label: "Worst stress",
        value: worstScenarioLoss,
        detail: worstScenarioId,
        tone: stressStatus === "fail" ? "red" : stressStatus === "warning" ? "amber" : "blue"
      }
    ]
  };
}

function stringPathMap(value: unknown): Record<string, string> {
  const record = getRecord(value);
  return Object.fromEntries(
    Object.entries(record).filter(([, item]) => typeof item === "string") as Array<[string, string]>
  );
}

function firstText(...values: unknown[]) {
  for (const value of values) {
    if (typeof value === "string" && value.trim()) return value;
  }
  return undefined;
}

function compactProblemFields(problemClassification: unknown) {
  const problem = getRecord(problemClassification);
  const primaryProblem = getRecord(problem.primary_problem);
  const primaryDiagnosis = getRecord(problem.primary_diagnosis);
  const rootCause = getRecord(primaryDiagnosis.root_cause);
  const suggestedActions = getArray(problem.suggested_actions)
    .map(getRecord)
    .map((action) => firstText(action.label_en, action.action_path_id))
    .filter((item): item is string => Boolean(item))
    .slice(0, 3);

  return {
    primaryProblem: firstText(
      primaryProblem.label_en,
      primaryProblem.problem_id,
      primaryDiagnosis.label_en,
      rootCause.label_en,
      rootCause.problem_id
    ),
    problemSeverity: firstText(primaryProblem.severity, problem.materiality),
    problemConfidence: firstText(primaryProblem.confidence, primaryDiagnosis.confidence, problem.confidence),
    suggestedActionPaths: suggestedActions.length
      ? suggestedActions
      : [
        firstText(primaryProblem.suggested_action_path_id),
        ...getArray(primaryProblem.secondary_action_path_ids).filter((item): item is string => typeof item === "string" && Boolean(item.trim()))
      ].filter((item): item is string => Boolean(item)).slice(0, 3)
  };
}


function compactLaunchpadFields(candidateLaunchpad: unknown) {
  const launchpad = getRecord(candidateLaunchpad);
  const cards = getArray(launchpad.cards).map(getRecord);
  const firstCard = cards[0];
  const defaultMethod = firstText(firstCard.default_method);

  return {
    launchpadCardsCount: cards.length,
    launchpadCards: cards.slice(0, 8).map(compactLaunchpadCard),
    recommendedFirstTest: firstText(
      firstCard.title,
      firstCard.goal,
      defaultMethod,
      launchpad.launchpad_outcome
    )
  };
}

function compactLaunchpadCard(card: Record<string, unknown>): LaunchpadCardSummary {
  return {
    card_id: textValue(card.card_id, textValue(card.title, "launchpad_card")),
    title: textValue(card.title, "Candidate Launchpad card"),
    goal: firstText(card.goal),
    hypothesis_to_test: firstText(card.hypothesis_to_test, card.what_this_tests_en),
    card_type: firstText(card.card_type),
    source_problem_label: firstText(card.source_problem_label),
    suggested_methods: getArray(card.suggested_methods).map(getRecord).slice(0, 4).map((method, index) => ({
      candidate_method_id: textValue(method.candidate_method_id, `method_${index + 1}`),
      method_role: firstText(method.method_role),
      why_this_method: firstText(method.why_this_method)
    })),
    default_method: firstText(card.default_method),
    success_criteria: stringArray(card.success_criteria).slice(0, 6),
    tradeoff_to_watch: firstText(card.tradeoff_to_watch, card.expected_tradeoff_to_check_en),
    when_to_skip: firstText(card.when_to_skip),
    decision_boundary: firstText(card.decision_boundary),
    is_rebalance_recommendation: card.is_rebalance_recommendation === true,
    generates_portfolio: card.generates_portfolio === true
  };
}

function compactBuilderSetup(value: unknown): BuilderSetupSummary | undefined {
  const builder = getRecord(value);
  const selectedCardId = firstText(builder.selected_card_id);
  if (!selectedCardId) return undefined;
  const builderPrefill = getRecord(builder.builder_prefill);
  const candidateSetup = getRecord(builder.candidate_setup);
  return {
    selected_card_id: selectedCardId,
    can_generate_candidate: builder.can_generate_candidate === true || candidateSetup.can_generate_candidate === true,
    builder_prefill: {
      goal: firstText(builderPrefill.goal),
      suggested_method: firstText(builderPrefill.suggested_method),
      constraint_preset: firstText(builderPrefill.constraint_preset),
      max_asset_weight: typeof builderPrefill.max_asset_weight === "number" || typeof builderPrefill.max_asset_weight === "string" ? builderPrefill.max_asset_weight : undefined,
      min_asset_weight: typeof builderPrefill.min_asset_weight === "number" || typeof builderPrefill.min_asset_weight === "string" ? builderPrefill.min_asset_weight : undefined
    },
    candidate_setup: {
      validation_status: firstText(candidateSetup.validation_status),
      can_generate_candidate: candidateSetup.can_generate_candidate === true
    }
  };
}

function compactEvidenceFields({
  activeReview,
  outputs
}: {
  activeReview: ActiveReviewState;
  outputs: Record<string, unknown>;
}): EvidenceSummary | undefined {
  const xray = getRecord(outputs.portfolio_xray);
  const stress = getRecord(outputs.stress_report);
  if (!Object.keys(xray).length || !Object.keys(stress).length) return undefined;

  const allocation = getRecord(xray.block_2_1_asset_allocation);
  const composition = getRecord(allocation.portfolio_composition_snapshot);
  const riskBudget = getRecord(xray.block_2_5_risk_budget_view);
  const metricsBlock = getRecord(xray.block_2_2_portfolio_metrics);
  const drawdown = getRecord(metricsBlock.drawdown_diagnostics);
  const weaknessMap = getRecord(xray.block_2_6_portfolio_weakness_map);
  const stressConclusions = getRecord(stress.stress_conclusions);
  const worstScenario = getRecord(stressConclusions.worst_synthetic_scenario);
  const hedgeSummary = getRecord(getRecord(stress.hedge_gap_analysis_v1).summary);
  const mainHedgeGap = getRecord(hedgeSummary.main_hedge_gap);
  const dominantAssetClass = getRecord(composition.dominant_asset_class);
  const dominantRiskFactor = getRecord(composition.dominant_main_risk_factor);
  const topHolding = getRecord(composition.top1_holding);
  const topRiskContributors = getArray(riskBudget.top3_rc_assets).map(getRecord).slice(0, 3);
  const topRiskContributor = getRecord(riskBudget.top1_rc_asset);
  const riskTypes = getArray(weaknessMap.risk_types)
    .map(getRecord)
    .filter((item) => Boolean(textValue(item.risk_title, "") || textValue(item.risk_type, "")))
    .sort((a, b) => (numericValue(b.score_0_100) ?? 0) - (numericValue(a.score_0_100) ?? 0));
  const dataWarning = firstStringFromArrays(
    allocation.data_quality_warnings,
    metricsBlock.data_quality_warnings,
    weaknessMap.data_quality_warnings,
    stressConclusions.data_quality_warnings,
    hedgeSummary.data_quality_warnings
  );

  const holdingsCount = numericValue(composition.total_holdings) ?? activeReview.reviewSummary?.holdingsCount ?? activeReview.holdings.length;
  const dominantExposureName = textValue(dominantRiskFactor.name, textValue(dominantAssetClass.name, "Dominant exposure"));
  const dominantExposureWeight = formatRawPercent(dominantRiskFactor.weight_pct ?? dominantAssetClass.weight_pct);
  const worstScenarioId = textValue(worstScenario.scenario_id ?? stress.failed_scenario, "Worst stress scenario");
  const worstStressLoss = worstScenario.portfolio_pnl_pct ?? stress.worst_scenario_loss_pct;
  const hedgeCoverage = mainHedgeGap.offset_coverage_ratio ?? hedgeSummary.main_hedge_gap_offset_coverage_ratio;
  const hedgeArea = textValue(mainHedgeGap.protection_type ?? hedgeSummary.weakest_protection_area, "hedge gap");
  const riskContributorText = topRiskContributors.length
    ? topRiskContributors.map((item) => `${textValue(item.ticker, "Asset")} ${formatRawPercent(item.rc_pct ?? item.risk_contribution_pct)}`).join(" · ")
    : "Top risk contributors were not returned.";

  const items: EvidenceItem[] = [
    {
      type: "X-Ray",
      title: "Portfolio composition",
      status: `${holdingsCount} holdings`,
      summary: topHolding.ticker
        ? `Largest holding is ${textValue(topHolding.ticker)} at ${formatRawPercent(topHolding.weight_pct)}.`
        : "Portfolio composition was returned for the current portfolio.",
      source: "Portfolio X-Ray",
      tone: "blue"
    },
    {
      type: "X-Ray",
      title: "Dominant exposure",
      status: `${dominantExposureName} · ${dominantExposureWeight}`,
      summary: `The current portfolio is most exposed to ${dominantExposureName}.`,
      source: "Portfolio X-Ray",
      tone: numericValue(dominantRiskFactor.weight_pct ?? dominantAssetClass.weight_pct) !== null && (numericValue(dominantRiskFactor.weight_pct ?? dominantAssetClass.weight_pct) ?? 0) >= 50 ? "amber" : "blue"
    },
    {
      type: "X-Ray",
      title: "Top risk contributors",
      status: topRiskContributor.ticker ? `${textValue(topRiskContributor.ticker)} leads risk` : "Not available",
      summary: riskContributorText,
      source: "Portfolio X-Ray",
      tone: topRiskContributors.length ? "amber" : "slate"
    },
    {
      type: "Stress",
      title: "Worst stress scenario",
      status: worstScenarioId,
      summary: `Estimated portfolio loss: ${formatDecimalPercent(worstStressLoss)}.`,
      source: "Stress Test Lab",
      tone: toneForLoss(worstStressLoss)
    },
    {
      type: "Stress",
      title: "Hedge / offset coverage",
      status: hedgeCoverage !== undefined ? `${formatDecimalPercent(hedgeCoverage)} offset coverage` : "Not available",
      summary: hedgeCoverage !== undefined
        ? `Weakest protection area: ${hedgeArea}.`
        : "Stress result did not return hedge or offset coverage.",
      source: "Stress Test Lab",
      tone: hedgeCoverage !== undefined ? ((numericValue(hedgeCoverage) ?? 0) < 0.25 ? "amber" : "blue") : "slate"
    }
  ];

  if (riskTypes[0]) {
    items.splice(3, 0, {
      type: "X-Ray",
      title: "Primary weakness",
      status: `${textValue(riskTypes[0].severity, "Risk")} · score ${textValue(String(riskTypes[0].score_0_100 ?? "n/a"))}`,
      summary: textValue(riskTypes[0].short_diagnosis, textValue(riskTypes[0].risk_title, "Primary weakness returned by X-Ray.")),
      source: "Portfolio X-Ray",
      tone: (numericValue(riskTypes[0].score_0_100) ?? 0) >= 70 ? "red" : "amber"
    });
  }

  if (dataWarning) {
    items.push({
      type: "Data quality",
      title: "Data quality warning",
      status: "Review with caution",
      summary: dataWarning,
      source: "Input and diagnostic data checks",
      tone: "amber"
    });
  }

  return {
    headline: "Evidence is based on the latest completed real review.",
    quality: `Real run · ${textValue(stressConclusions.overall_confidence, "confidence n/a")} stress confidence`,
    boundaryNote: "Evidence is diagnostic and comes from Portfolio X-Ray plus Stress Test Lab for the submitted current portfolio.",
    metrics: [
      {
        label: "Holdings",
        value: String(holdingsCount),
        detail: topHolding.ticker ? `Largest: ${textValue(topHolding.ticker)} ${formatRawPercent(topHolding.weight_pct)}` : "Current portfolio",
        tone: "blue"
      },
      {
        label: "Dominant exposure",
        value: dominantExposureName,
        detail: dominantExposureWeight,
        tone: "amber"
      },
      {
        label: "Worst stress loss",
        value: formatDecimalPercent(worstStressLoss),
        detail: worstScenarioId,
        tone: toneForLoss(worstStressLoss)
      },
      {
        label: "Max drawdown",
        value: formatDecimalPercent(drawdown.max_drawdown),
        detail: "Portfolio X-Ray drawdown",
        tone: toneForLoss(drawdown.max_drawdown)
      },
      {
        label: "Offset coverage",
        value: hedgeCoverage !== undefined ? formatDecimalPercent(hedgeCoverage) : "n/a",
        detail: hedgeArea,
        tone: hedgeCoverage !== undefined ? "amber" : "slate"
      }
    ],
    items
  };
}

export function buildCompactReviewSummary({
  investorCurrency,
  holdings,
  reviewResult
}: {
  investorCurrency: string;
  holdings: ReviewHolding[];
  reviewResult: ReviewResult;
}): ReviewSummary {
  const diagnosis = buildDiagnosisFromRealResult({
    investorCurrency,
    holdings,
    reviewId: reviewResult.review_id,
    reviewResult,
    verdictResult: undefined,
    runMode: "real_run",
    runStatus: "completed",
    submitted: true,
    diagnosisReady: true,
    evidenceReady: true,
    improvementPathsReady: true,
    candidateReady: false,
    comparisonReady: false,
    verdictReady: false,
    updatedAt: nowIso()
  }) ?? {
    status: "Diagnosis ready",
    headline: "Portfolio diagnosis completed.",
    evidenceQuality: "Real backend review",
    nextStep: "Review Evidence before testing one candidate hypothesis.",
    boundaryNote: "Compact summary is available; full raw outputs are not persisted in browser storage.",
    drivers: ["Backend review completed for the submitted portfolio."],
    metrics: []
  };

  const outputs = getRecord(reviewResult.outputs);
  const problemClassification = outputs.problem_classification;
  const candidateLaunchpad = outputs.candidate_launchpad;
  const portfolioAlternativesBuilder = outputs.portfolio_alternatives_builder;
  const compactProblem = compactProblemFields(problemClassification);
  const compactLaunchpad = compactLaunchpadFields(candidateLaunchpad);
  const rawBytes = estimateJsonBytes(reviewResult);
  const evidence = compactEvidenceFields({
    activeReview: {
      investorCurrency,
      holdings,
      reviewId: reviewResult.review_id,
      reviewResult,
      verdictResult: undefined,
      runMode: "real_run",
      runStatus: "completed",
      submitted: true,
      diagnosisReady: true,
      evidenceReady: true,
      improvementPathsReady: true,
      candidateReady: false,
      comparisonReady: false,
      verdictReady: false,
      updatedAt: nowIso()
    },
    outputs
  });
  const summaryWithoutStorage = {
    version: 1 as const,
    source: "real_run" as const,
    status: "completed" as const,
    reviewId: reviewResult.review_id,
    generatedAt: nowIso(),
    investorCurrency,
    holdingsCount: holdings.length,
    totalWeight: holdings.reduce((sum, holding) => sum + holding.weight, 0),
    cashWeight: holdings.filter((holding) => holding.type === "cash").reduce((sum, holding) => sum + holding.weight, 0),
    rawOutputKeys: Object.keys(outputs),
    outputPaths: stringPathMap(reviewResult.paths),
    diagnosis,
    evidence,
    primaryProblem: compactProblem.primaryProblem,
    problemSeverity: compactProblem.problemSeverity,
    problemConfidence: compactProblem.problemConfidence,
    suggestedActionPaths: compactProblem.suggestedActionPaths,
    launchpadCardsCount: compactLaunchpad.launchpadCardsCount,
    launchpadCards: compactLaunchpad.launchpadCards,
    builderSetup: compactBuilderSetup(portfolioAlternativesBuilder),
    recommendedFirstTest: compactLaunchpad.recommendedFirstTest,
    candidateLaunchpadAvailable: isRecord(candidateLaunchpad),
    problemClassificationAvailable: isRecord(problemClassification)
  };

  const summaryBytes = estimateJsonBytes(summaryWithoutStorage);

  return {
    ...summaryWithoutStorage,
    storage: {
      summaryBytes,
      rawBytes,
      rawPersisted: false,
      rawAccessStrategy: "Use reviewId and backend run artifacts for future retrieval; browser localStorage keeps only compact summaries."
    }
  };
}

function sumBySleeve(holdings: ReviewHolding[], sleeve: string) {
  return holdings.reduce((sum, holding) => {
    const instrument = instrumentByTicker.get(holding.ticker);
    return instrument?.sleeve === sleeve ? sum + holding.weight : sum;
  }, 0);
}

function labelsBySleeve(holdings: ReviewHolding[], sleeve: string) {
  return holdings
    .filter((holding) => instrumentByTicker.get(holding.ticker)?.sleeve === sleeve)
    .map((holding) => holding.type === "cash" ? "Cash" : holding.label);
}

function metricTone(value: number, warningLevel: number): StatusTone {
  return value >= warningLevel ? "amber" : "blue";
}

export function buildDiagnosisFromReview(review: ActiveReviewState): DiagnosisState {
  if (review.reviewSummary?.diagnosis) return review.reviewSummary.diagnosis;

  const realDiagnosis = buildDiagnosisFromRealResult(review);
  if (realDiagnosis) return realDiagnosis;

  const holdings = review.holdings;
  const equityWeight = sumBySleeve(holdings, "equity");
  const fixedIncomeWeight = sumBySleeve(holdings, "fixed_income");
  const goldWeight = sumBySleeve(holdings, "gold");
  const cashWeight = sumBySleeve(holdings, "cash");
  const topHolding = [...holdings].sort((a, b) => b.weight - a.weight)[0];
  const equityLabels = labelsBySleeve(holdings, "equity");
  const fixedIncomeLabels = labelsBySleeve(holdings, "fixed_income");
  const cashDetail = cashWeight > 0 ? `${review.investorCurrency || "USD"} cash included` : "No cash position";

  const headline = equityWeight >= 50
    ? "Equity exposure is the main driver of the current portfolio risk story."
    : fixedIncomeWeight >= 35
      ? "Rate-sensitive fixed income is a major part of the current portfolio risk story."
      : "The current portfolio has a more balanced risk mix, with no single sleeve fully dominant.";

  const drivers = [
    topHolding
      ? `${topHolding.label} is the largest position at ${formatPercent(topHolding.weight)}.`
      : "No portfolio positions are available for diagnosis.",
    equityWeight > 0
      ? `Equity sleeve is ${formatPercent(equityWeight)}${equityLabels.length ? ` through ${equityLabels.join(" + ")}` : ""}.`
      : "There is no dedicated equity sleeve in the current input.",
    fixedIncomeWeight > 0
      ? `Fixed-income sleeve is ${formatPercent(fixedIncomeWeight)}${fixedIncomeLabels.length ? ` through ${fixedIncomeLabels.join(" + ")}` : ""}.`
      : goldWeight > 0
        ? `Gold sleeve is ${formatPercent(goldWeight)} and may behave differently from equity and bonds.`
        : cashWeight > 0
          ? `Liquidity sleeve is ${formatPercent(cashWeight)}.`
          : "No cash position is currently entered."
  ];

  return {
    status: "Diagnosis ready",
    headline,
    evidenceQuality: "Input-based review",
    nextStep: "Review evidence before testing any candidate hypothesis.",
    boundaryNote: "Diagnosis reflects the portfolio currently entered on the input screen.",
    drivers,
    metrics: [
      { label: "Equity sleeve", value: formatPercent(equityWeight), detail: equityLabels.length ? equityLabels.join(" + ") : "No equity sleeve", tone: metricTone(equityWeight, 50) },
      { label: "Fixed income", value: formatPercent(fixedIncomeWeight), detail: fixedIncomeLabels.length ? fixedIncomeLabels.join(" + ") : "No bond sleeve", tone: metricTone(fixedIncomeWeight, 35) },
      { label: "Liquidity sleeve", value: formatPercent(cashWeight), detail: cashDetail, tone: cashWeight > 0 ? "blue" : "slate" }
    ]
  };
}
