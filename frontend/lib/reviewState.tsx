"use client";

import { createContext, useCallback, useContext, useEffect, useMemo, useRef, useState, type ReactNode } from "react";
import type { ComparisonMetric, EvidenceItem, Metric, SiteExplanationBundle, SiteExplanationScreen, SiteExplanationTextItem, StatusTone } from "@/lib/types";
import type { JourneyFlags } from "@/lib/journey";
import type {
  CandidateResponse,
  ClientFitInput,
  ClientFitDisplaySummary,
  ComparisonResponse,
  CreateReviewResponse,
  DiagnosisSummary as FastApiDiagnosisSummary,
  DownstreamEvidenceChainContext,
  StagedProviderStatus,
  StagedReviewStartedResponse,
  StagedReviewStatusResponse,
  StagedSafeError,
  StagedStageState,
  VerdictResponse
} from "@/lib/generated/api-types";
import { evidenceQualityLabel, formatUnknownValue, normalizeDisplaySentence } from "@/lib/displayLabels";
import { instrumentByTicker } from "@/data/instrumentUniverse";
import { buildStressLabModelFromOutputs } from "@/components/evidence/stressLabModel";
import type { StressLabModel } from "@/components/evidence/stressLabTypes";
import { stagedSafeErrorMessage } from "@/lib/review/stagedSafeError";
import { isCompareReadyCandidateGeneration } from "@/lib/review/candidateGenerationReadiness";
import { buildClientFitProfileFromOnboarding, hasCompletedOnboarding, readOnboardingState } from "@/lib/onboarding";
import { useSupabaseAuth } from "@/lib/supabase/auth";
import { persistCompactStageSummariesForReview, persistDiagnosisSummaryForReview, persistStagedProgressForReview, useSupabasePersistence, type SavedReviewRecord } from "@/lib/supabase/persistence";

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
export type ReviewRunStatus = "draft" | "running" | "completed" | "failed";

export type StagedReviewProgress = {
  schemaVersion: "review_state_v1" | "review_started_v1";
  reviewId: string;
  status: "pending" | "running" | "completed" | "partial" | "blocked" | "failed";
  currentStage: string;
  mode: "demo_qa" | "live";
  stages: Record<string, StagedStageState>;
  providerStatus?: StagedProviderStatus;
  safeError?: StagedSafeError | null;
  updatedAt?: string | null;
  warnings: string[];
};

export type ReviewErrorState = {
  message: string;
  details?: string;
  occurredAt: string;
};

export type CandidateGenerationSummary = {
  reviewId?: string;
  status: string;
  stage: "candidate_generation";
  selectedCardId: string;
  candidateId: string;
  methodLabel?: string;
  hypothesis?: string;
  successCriteria?: string[];
  tradeoffToWatch?: string;
  decisionBoundary?: string;
  generationStatus: string;
  canCompare: boolean;
  path?: string;
  weights: Array<{ ticker: string; weight: number }>;
  generatedAt: string;
};

export type EvidenceChainContextSummary = {
  selectedDiagnosisId?: string;
  selectedDiagnosisLabel?: string;
  selectedDiagnosisRole?: string;
  diagnosisStatement?: string;
  testedHypothesis?: string;
  successCriteria: string[];
  tradeoffToWatch?: string;
  candidateBoundary?: string;
  recommendationBoundary?: string;
  sourceArtifacts: string[];
};

export type ComparisonResultSummary = {
  reviewId?: string;
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
  evidenceChainContext?: EvidenceChainContextSummary;
  clientFit?: ClientFitDisplaySummary;
  path?: string;
  generatedAt: string;
};

export type VerdictResultSummary = {
  reviewId?: string;
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
  evidenceUsed: string[];
  whatWouldChangeVerdict: string[];
  evidenceChainContext?: EvidenceChainContextSummary;
  clientFit?: ClientFitDisplaySummary;
  path?: string;
  generatedAt: string;
};

export type ReportResultSummary = {
  reviewId?: string;
  status: string;
  stage: "report";
  selectedCardId: string;
  candidateId: string;
  title: string;
  subtitle: string;
  sections: { title: string; body: string }[];
  evidenceUsed: string[];
  unavailableEvidence: string[];
  nextObservation: string;
  boundaryNote: string;
  warnings: string[];
  clientFit?: ClientFitDisplaySummary;
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

export type XRayBreakdownItem = {
  name: string;
  weightPct: number;
};

export type XRayBreakdown = {
  title: string;
  items: XRayBreakdownItem[];
};

export type XRayFlag = {
  label: string;
  severity: string;
  message: string;
};

export type XRayHoldingRow = {
  holding: string;
  weightPct: number;
  assetClass: string;
  riskRole: string;
  mainRiskFactor: string;
};

export type XRayFactor = {
  factor: string;
  beta?: number;
  contributionPct?: number;
  confidence: string;
  interpretation: string;
};

export type XRayHiddenRiskAlert = {
  id: string;
  title: string;
  level: string;
  score?: number;
  diagnosis: string;
  evidence: string[];
  linkedAssets: string[];
  nextTests: string[];
  confidence?: string;
};

export type XRayRiskContribution = {
  name: string;
  weightPct?: number;
  riskContributionPct?: number;
  gapPp?: number;
};

export type XRayWeaknessTile = {
  id: string;
  title: string;
  severity: string;
  score?: number;
  diagnosis: string;
  evidence: string[];
  linkedAssets: string[];
  nextTests: string[];
  confidence?: string;
};

export type XRaySummary = {
  snapshotCards: Metric[];
  composition: {
    insight: string;
    keyFacts: string[];
    breakdowns: XRayBreakdown[];
    flags: XRayFlag[];
    holdings?: XRayHoldingRow[];
  };
  riskProfile: {
    insight: string;
    metrics: Metric[];
    keyFacts: string[];
  };
  factors: {
    insight: string;
    topFactors: XRayFactor[];
    factorCards: XRayFactor[];
    caveat?: string;
  };
  hiddenRisks: {
    insight: string;
    alerts: XRayHiddenRiskAlert[];
  };
  riskBudget: {
    insight: string;
    topContributor?: XRayRiskContribution;
    top3Share?: number;
    contributors: XRayRiskContribution[];
    riskOverweight: XRayRiskContribution[];
    riskUnderweight: XRayRiskContribution[];
    buckets: XRayRiskContribution[];
  };
  weaknessMap: {
    insight: string;
    tiles: XRayWeaknessTile[];
  };
  unavailableNotes: string[];
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
  builder_setup_id?: string;
  builder_prefill: {
    goal?: string;
    suggested_method?: string;
    mode?: string;
    constraint_preset?: string;
    max_asset_weight?: number | string;
    min_asset_weight?: number | string;
  };
  candidate_setup: {
    candidate_setup_id?: string;
    validation_status?: string;
    can_generate_candidate: boolean;
    mode?: string;
    constraint_preset?: string;
    max_asset_weight?: number | string;
    min_asset_weight?: number | string;
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
  xraySummary?: XRaySummary;
  evidence?: EvidenceSummary;
  clientFit?: ClientFitDisplaySummary;
  stressLabModel?: StressLabModel;
  siteExplanation?: SiteExplanationBundle;
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
  clientFitProfile?: ClientFitInput;
  cloudPortfolio?: {
    id: string;
    name: string;
    versionId?: string;
    versionNumber?: number;
  };
  portfolioVersionId?: string;
  portfolioVersionNumber?: number;
  readOnlyHistory?: boolean;
  lineageAvailable?: boolean;
  reviewId?: string;
  reviewResult?: ReviewResult;
  reviewSummary?: ReviewSummary;
  stagedProgress?: StagedReviewProgress;
  builderSetup?: BuilderSetupSummary;
  candidateGeneration?: CandidateGenerationSummary;
  comparisonResult?: ComparisonResultSummary;
  verdictResult?: VerdictResultSummary;
  reportResult?: ReportResultSummary;
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
  selectedDiagnosisRole?: string;
  sourceArtifacts: string[];
  rejectedAlternatives: string[];
  rationaleRefs: string[];
};

type ReviewStateContextValue = {
  activeReview: ActiveReviewState | null;
  hydrated: boolean;
  saveClientFitProfile: (profile: ClientFitInput) => void;
  savePortfolioInput: (input: Pick<ActiveReviewState, "investorCurrency" | "holdings">) => void;
  submitPortfolioInput: (input: Pick<ActiveReviewState, "investorCurrency" | "holdings" | "reviewResult">) => void;
  startStagedReview: (input: Pick<ActiveReviewState, "investorCurrency" | "holdings"> & { started: StagedReviewStartedResponse }) => void;
  recordStagedProgress: (progress: StagedReviewStatusResponse) => void;
  recordReviewError: (input: Pick<ActiveReviewState, "investorCurrency" | "holdings"> & { message: string; details?: string }) => void;
  linkCloudPortfolio: (portfolio: ActiveReviewState["cloudPortfolio"]) => void;
  loadCloudPortfolioInput: (input: { portfolioId: string; name: string; investorCurrency: string; holdings: ReviewHolding[]; versionId?: string; versionNumber?: number }) => void;
  recordBuilderSetup: (result: unknown) => void;
  clearDownstreamReviewState: () => void;
  recordCandidateGeneration: (result: unknown) => void;
  recordComparisonResult: (result: unknown) => void;
  recordVerdictResult: (result: unknown) => void;
  recordReportResult: (result: unknown) => void;
  hydrateCloudReview: (savedReview: SavedReviewRecord) => void;
  markLiveLineageUnavailable: (message?: string) => void;
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
const LEGACY_DEMO_PORTFOLIO_SIGNATURES = new Set([
  "BND:20|CASH_USD:10|GLD:10|QQQ:20|SPY:40",
  "BND:10|CASH_USD:10|GLD:15|QQQ:25|SPY:40"
]);

function nowIso() {
  return new Date().toISOString();
}

function isRecord(value: unknown): value is Record<string, unknown> {
  return Boolean(value) && typeof value === "object" && !Array.isArray(value);
}

function holdingsSignature(holdings: ReviewHolding[]) {
  return holdings
    .map((holding) => `${holding.ticker}:${holding.weight}`)
    .sort()
    .join("|");
}

function isLegacyUnsubmittedDemoPortfolio(value: ActiveReviewState) {
  return value.runMode === "sample_demo"
    && value.runStatus === "draft"
    && !value.submitted
    && !value.reviewId
    && !value.reviewSummary
    && !value.cloudPortfolio
    && LEGACY_DEMO_PORTFOLIO_SIGNATURES.has(holdingsSignature(value.holdings));
}

function isJsonValue(value: unknown): value is JsonValue {
  if (value === null) return true;
  if (["boolean", "number", "string"].includes(typeof value)) return true;
  if (Array.isArray(value)) return value.every(isJsonValue);
  if (isRecord(value)) return Object.values(value).every(isJsonValue);
  return false;
}

function cleanSiteExplanationScreen(value: unknown): SiteExplanationScreen | undefined {
  if (!isRecord(value)) return undefined;
  const normalizeItems = (items: unknown, level: "executive" | "evidence" | "technical"): SiteExplanationTextItem[] => (
    Array.isArray(items)
      ? items.filter(isRecord).map((item) => ({
        id: textValue(item.id, `${level}.item`),
        level,
        text: normalizeDisplaySentence(item.text, ""),
        tone: (["neutral", "caution", "risk", "positive"].includes(String(item.tone)) ? item.tone : "neutral") as SiteExplanationTextItem["tone"],
        evidence_status: (["available", "limited", "missing", "preliminary"].includes(String(item.evidence_status)) ? item.evidence_status : "limited") as SiteExplanationTextItem["evidence_status"],
        claim_type: (["material_claim", "boundary_note", "empty_state"].includes(String(item.claim_type)) ? item.claim_type : "boundary_note") as SiteExplanationTextItem["claim_type"],
        source_refs: Array.isArray(item.source_refs)
          ? item.source_refs.filter(isRecord).map((ref) => ({
            artifact: textValue(ref.artifact, ""),
            field_path: textValue(ref.field_path, "")
          })).filter((ref) => ref.artifact && ref.field_path)
          : []
      })).filter((item) => item.text)
      : []
  );
  return {
    executive: normalizeItems(value.executive, "executive"),
    evidence: normalizeItems(value.evidence, "evidence"),
    technical: normalizeItems(value.technical, "technical")
  };
}

export function cleanSiteExplanationBundle(value: unknown): SiteExplanationBundle | undefined {
  if (!isRecord(value) || value.schema_version !== "site_explanation_bundle_v1") return undefined;
  const screensRaw = getRecord(value.screens);
  const screens = Object.fromEntries(
    Object.entries(screensRaw)
      .map(([screen, screenValue]) => [screen, cleanSiteExplanationScreen(screenValue)])
      .filter((entry): entry is [string, SiteExplanationScreen] => Boolean(entry[1]))
  );
  return {
    schema_version: "site_explanation_bundle_v1",
    review_id: typeof value.review_id === "string" ? value.review_id : undefined,
    screens,
    warnings: stringArray(value.warnings)
  };
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
    reviewId: typeof value.reviewId === "string" ? value.reviewId : undefined,
    status: typeof value.status === "string" ? value.status : "unknown",
    stage: "candidate_generation",
    selectedCardId: typeof value.selectedCardId === "string" ? value.selectedCardId : "",
    candidateId: typeof value.candidateId === "string" ? value.candidateId : "",
    methodLabel: typeof value.methodLabel === "string" ? value.methodLabel : undefined,
    hypothesis: typeof value.hypothesis === "string" ? value.hypothesis : undefined,
    successCriteria: stringArray(value.successCriteria).map((item) => normalizeDisplaySentence(item)),
    tradeoffToWatch: typeof value.tradeoffToWatch === "string" ? normalizeDisplaySentence(value.tradeoffToWatch) : undefined,
    decisionBoundary: typeof value.decisionBoundary === "string" ? normalizeDisplaySentence(value.decisionBoundary) : undefined,
    generationStatus: typeof value.generationStatus === "string" ? value.generationStatus : "unknown",
    canCompare: Boolean(value.canCompare),
    path: typeof value.path === "string" ? value.path : undefined,
    weights,
    generatedAt: typeof value.generatedAt === "string" ? value.generatedAt : nowIso()
  };
}

function cleanEvidenceChainContextSummary(value: unknown): EvidenceChainContextSummary | undefined {
  if (!isRecord(value)) return undefined;
  const sourceArtifacts = stringArray(value.sourceArtifacts ?? value.source_artifacts)
    .map((item) => formatUnknownValue(item))
    .filter(Boolean);
  const successCriteria = stringArray(value.successCriteria ?? value.success_criteria)
    .map((item) => normalizeDisplaySentence(item))
    .filter(Boolean);
  const summary: EvidenceChainContextSummary = {
    selectedDiagnosisId: firstText(value.selectedDiagnosisId, value.selected_diagnosis_id),
    selectedDiagnosisLabel: firstText(value.selectedDiagnosisLabel, value.selected_diagnosis_label) ? formatUnknownValue(firstText(value.selectedDiagnosisLabel, value.selected_diagnosis_label)) : undefined,
    selectedDiagnosisRole: firstText(value.selectedDiagnosisRole, value.selected_diagnosis_role) ? formatUnknownValue(firstText(value.selectedDiagnosisRole, value.selected_diagnosis_role)) : undefined,
    diagnosisStatement: firstText(value.diagnosisStatement, value.diagnosis_statement) ? normalizeDisplaySentence(firstText(value.diagnosisStatement, value.diagnosis_statement)) : undefined,
    testedHypothesis: firstText(value.testedHypothesis, value.tested_hypothesis) ? normalizeDisplaySentence(firstText(value.testedHypothesis, value.tested_hypothesis)) : undefined,
    successCriteria,
    tradeoffToWatch: firstText(value.tradeoffToWatch, value.tradeoff_to_watch) ? normalizeDisplaySentence(firstText(value.tradeoffToWatch, value.tradeoff_to_watch)) : undefined,
    candidateBoundary: firstText(value.candidateBoundary, value.candidate_boundary) ? normalizeDisplaySentence(firstText(value.candidateBoundary, value.candidate_boundary)) : undefined,
    recommendationBoundary: firstText(value.recommendationBoundary, value.recommendation_boundary) ? normalizeDisplaySentence(firstText(value.recommendationBoundary, value.recommendation_boundary)) : undefined,
    sourceArtifacts
  };
  return Object.values(summary).some((item) => Array.isArray(item) ? item.length : Boolean(item)) ? summary : undefined;
}

function cleanClientFitDisplaySummary(value: unknown): ClientFitDisplaySummary | undefined {
  if (!isRecord(value)) return undefined;
  const tone = value.status_tone === "green" || value.status_tone === "amber" || value.status_tone === "red"
    ? value.status_tone
    : "amber";
  const targetRows = Array.isArray(value.target_rows)
    ? value.target_rows.filter(isRecord).map((row) => {
      const rowTone: "green" | "amber" | "red" = row.status_tone === "green" || row.status_tone === "amber" || row.status_tone === "red" ? row.status_tone : "amber";
      return {
        dimension_label: textValue(row.dimension_label, "Client Fit check"),
        portfolio_value_label: firstText(row.portfolio_value_label) ?? null,
        target_or_limit_label: firstText(row.target_or_limit_label) ?? null,
        status_label: textValue(row.status_label, "Client Fit not evaluated"),
        status_tone: rowTone,
        explanation: firstText(row.explanation) ? normalizeDisplaySentence(firstText(row.explanation)) : null
      };
    })
    : [];
  return {
    status_label: textValue(value.status_label, "Client Fit not provided"),
    status_tone: tone,
    profile_label: firstText(value.profile_label) ?? null,
    source_quality_label: firstText(value.source_quality_label) ?? null,
    target_rows: targetRows.slice(0, 6),
    main_explanation: firstText(value.main_explanation) ? normalizeDisplaySentence(firstText(value.main_explanation)) : null,
    decision_boundary: normalizeDisplaySentence(value.decision_boundary, "Client Fit is non-binding decision support."),
    next_best_test: firstText(value.next_best_test) ? normalizeDisplaySentence(firstText(value.next_best_test)) : null
  };
}

function cleanClientFitProfileInput(value: unknown): ClientFitInput | undefined {
  if (!isRecord(value)) return undefined;
  const source = ["questionnaire", "preset_override", "manual_override", "imported", "missing"].includes(String(value.source))
    ? String(value.source) as ClientFitInput["source"]
    : undefined;
  const sourceQuality = ["high", "medium", "low", "missing"].includes(String(value.source_quality))
    ? String(value.source_quality) as ClientFitInput["source_quality"]
    : undefined;
  if (!source || !sourceQuality || source === "missing" || sourceQuality === "missing") return undefined;

  const presetId = ["ultra_conservative", "conservative", "balanced", "growth", "aggressive"].includes(String(value.preset_id))
    ? String(value.preset_id) as NonNullable<ClientFitInput["preset_id"]>
    : null;
  const rangeInput = (raw: unknown) => {
    if (!isRecord(raw)) return undefined;
    const min = numericValue(raw.min);
    const max = numericValue(raw.max);
    if (min === null || max === null || min < 0 || max > 1 || min >= max) return undefined;
    return { min, max };
  };
  const targetReturnRange = rangeInput(value.target_return_range);
  const targetVolRange = rangeInput(value.target_vol_range);
  const drawdown = numericValue(value.target_max_drawdown_pct);
  const horizonYears = numericValue(value.horizon_years);
  if (!presetId && (!targetReturnRange || !targetVolRange || drawdown === null || !(horizonYears !== null && horizonYears > 0))) {
    return undefined;
  }

  return {
    preset_id: presetId,
    source,
    source_quality: sourceQuality,
    source_quality_reason: firstText(value.source_quality_reason) ?? null,
    horizon_years: horizonYears !== null && horizonYears > 0 ? horizonYears : null,
    target_return_range: targetReturnRange ?? null,
    target_vol_range: targetVolRange ?? null,
    target_max_drawdown_pct: drawdown !== null && drawdown <= 0 && drawdown >= -1 ? drawdown : null
  };
}

export function hasProvidedClientFitSummary(value: ClientFitDisplaySummary | undefined) {
  if (!value) return false;
  const label = (value.status_label ?? "").trim().toLowerCase();
  return Boolean(label && !label.includes("not provided"));
}

function cleanComparisonResultSummary(value: unknown): ComparisonResultSummary | undefined {
  if (!isRecord(value)) return undefined;
  if (value.stage !== "current_vs_candidate") return undefined;
  const metrics = Array.isArray(value.metrics)
    ? value.metrics.filter(isRecord).map((item) => ({
      metric: textValue(item.metric, "Metric"),
      current: formatUnknownValue(item.current),
      candidate: formatUnknownValue(item.candidate),
      direction: formatUnknownValue(item.direction, "Unclear"),
      tradeoff: normalizeDisplaySentence(item.tradeoff, "Evidence only; no action implied."),
      tone: statusToneValue(item.tone)
    }))
    : [];
  return {
    reviewId: typeof value.reviewId === "string" ? value.reviewId : undefined,
    status: textValue(value.status, "unknown"),
    stage: "current_vs_candidate",
    selectedCardId: textValue(value.selectedCardId, ""),
    candidateId: textValue(value.candidateId, ""),
    comparisonStatus: formatUnknownValue(value.comparisonStatus, "Unknown"),
    viewMode: formatUnknownValue(value.viewMode, "Unknown"),
    candidateName: formatUnknownValue(value.candidateName, "Generated diagnostic candidate"),
    candidateBoundary: normalizeDisplaySentence(value.candidateBoundary, "Diagnostic comparison only. It does not decide whether to change the portfolio or create a rebalance instruction."),
    evidenceQuality: formatUnknownValue(value.evidenceQuality, "Evidence status unavailable"),
    summary: normalizeDisplaySentence(value.summary, "Current and candidate portfolios were compared for this review."),
    metrics,
    improved: stringArray(value.improved),
    worsened: stringArray(value.worsened),
    neutral: stringArray(value.neutral),
    unclear: stringArray(value.unclear),
    turnover: formatUnknownValue(value.turnover, "Turnover unavailable"),
    estimatedCost: formatUnknownValue(value.estimatedCost, "Estimated cost unavailable"),
    materiality: formatUnknownValue(value.materiality, "Materiality not evaluated"),
    warnings: stringArray(value.warnings).map((item) => normalizeDisplaySentence(item)),
    evidenceChainContext: cleanEvidenceChainContextSummary(value.evidenceChainContext),
    clientFit: cleanClientFitDisplaySummary(value.clientFit),
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
      value: formatUnknownValue(item.value),
      detail: typeof item.detail === "string" ? normalizeDisplaySentence(item.detail) : undefined,
      tone: statusToneValue(item.tone),
      delta: typeof item.delta === "string" ? item.delta : undefined
    }))
    : [];
  return {
    reviewId: typeof value.reviewId === "string" ? value.reviewId : undefined,
    status: textValue(value.status, "unknown"),
    stage: "decision_verdict",
    selectedCardId: textValue(value.selectedCardId, ""),
    candidateId: textValue(value.candidateId, ""),
    verdictId: textValue(value.verdictId, "unknown"),
    decisionStatus: formatUnknownValue(value.decisionStatus, "Unknown"),
    confidence: formatUnknownValue(value.confidence, "Unknown"),
    state: formatUnknownValue(value.state, "Decision-support verdict"),
    headline: normalizeDisplaySentence(value.headline, "Decision verdict generated."),
    explanation: normalizeDisplaySentence(value.explanation, "The active review produced a decision-support verdict."),
    evidenceQuality: formatUnknownValue(value.evidenceQuality, "Evidence status unavailable"),
    boundaryNote: normalizeDisplaySentence(value.boundaryNote, "Decision-support only. This is not a trade instruction or rebalance recommendation."),
    keyEvidence: stringArray(value.keyEvidence).map((item) => normalizeDisplaySentence(item)),
    monitoringTrigger: normalizeDisplaySentence(value.monitoringTrigger, "Monitor changes in comparison evidence before revisiting the verdict."),
    metrics,
    actionFraming: normalizeDisplaySentence(value.actionFraming, "Review the verdict as decision-support evidence only."),
    limitations: stringArray(value.limitations).map((item) => normalizeDisplaySentence(item)),
    evidenceUsed: stringArray(value.evidenceUsed).map((item) => normalizeDisplaySentence(item)),
    whatWouldChangeVerdict: stringArray(value.whatWouldChangeVerdict).map((item) => normalizeDisplaySentence(item)),
    evidenceChainContext: cleanEvidenceChainContextSummary(value.evidenceChainContext),
    clientFit: cleanClientFitDisplaySummary(value.clientFit),
    path: typeof value.path === "string" ? value.path : undefined,
    generatedAt: textValue(value.generatedAt, nowIso())
  };
}

function cleanReportResultSummary(value: unknown): ReportResultSummary | undefined {
  if (!isRecord(value)) return undefined;
  if (value.stage !== "report") return undefined;
  const sections = Array.isArray(value.sections)
    ? value.sections.filter(isRecord).map((section) => ({
      title: textValue(section.title, "Evidence"),
      body: normalizeDisplaySentence(section.body, "")
    })).filter((section) => section.body)
    : [];
  return {
    reviewId: typeof value.reviewId === "string" ? value.reviewId : undefined,
    status: textValue(value.status, "unknown"),
    stage: "report",
    selectedCardId: textValue(value.selectedCardId, ""),
    candidateId: textValue(value.candidateId, ""),
    title: textValue(value.title, "Grounded client-ready report summary"),
    subtitle: normalizeDisplaySentence(value.subtitle, "Active review report preview grounded in available evidence."),
    sections,
    evidenceUsed: stringArray(value.evidenceUsed).map((item) => normalizeDisplaySentence(item)),
    unavailableEvidence: stringArray(value.unavailableEvidence).map((item) => normalizeDisplaySentence(item)),
    nextObservation: normalizeDisplaySentence(value.nextObservation, "Retest if diagnosis, comparison, or verdict evidence changes."),
    boundaryNote: normalizeDisplaySentence(value.boundaryNote, "Decision-support only."),
    warnings: stringArray(value.warnings).map((item) => normalizeDisplaySentence(item)),
    clientFit: cleanClientFitDisplaySummary(value.clientFit),
    generatedAt: textValue(value.generatedAt, nowIso())
  };
}

function comparisonResultCanGenerateVerdict(value: ComparisonResultSummary | undefined) {
  if (!value) return false;
  const status = value.comparisonStatus.trim().toLowerCase().replace(/[^a-z0-9]+/g, "_");
  if (status !== "available") return false;
  return value.status.trim().toLowerCase().replace(/[^a-z0-9]+/g, "_") === "completed";
}

const STAGED_STAGE_NAMES = [
  "input",
  "data_load",
  "xray",
  "stress",
  "client_fit",
  "problem_classification",
  "launchpad_builder",
  "candidate",
  "comparison",
  "verdict",
  "report"
] as const;

function isStagedStageReady(progress: StagedReviewProgress | undefined, stage: string) {
  const status = progress?.stages?.[stage]?.status;
  return status === "completed" || status === "partial";
}

export function diagnosisStageChainReady(progress: Pick<StagedReviewStatusResponse, "stages"> | StagedReviewProgress | null | undefined) {
  const stageReady = (stage: string) => {
    const status = progress?.stages?.[stage]?.status;
    return status === "completed" || status === "partial";
  };
  return stageReady("xray")
    && stageReady("stress")
    && stageReady("problem_classification")
    && stageReady("launchpad_builder");
}

function cleanStageRow(value: unknown): StagedStageState {
  const row = isRecord(value) ? value : {};
  const status = typeof row.status === "string" && ["pending", "running", "completed", "partial", "blocked", "failed", "skipped"].includes(row.status)
    ? row.status as StagedStageState["status"]
    : "pending";
  return {
    status,
    started_at: typeof row.started_at === "string" ? row.started_at : null,
    completed_at: typeof row.completed_at === "string" ? row.completed_at : null,
    artifact_refs: Array.isArray(row.artifact_refs)
      ? row.artifact_refs.filter((item): item is string => typeof item === "string")
      : []
  };
}

function compactStagedProgressFromStarted(started: StagedReviewStartedResponse): StagedReviewProgress {
  const stages = Object.fromEntries(STAGED_STAGE_NAMES.map((stage) => [
    stage,
    cleanStageRow({ status: stage === started.current_stage ? started.status : "pending" })
  ])) as Record<string, StagedStageState>;

  return {
    schemaVersion: started.schema_version ?? "review_started_v1",
    reviewId: started.review_id,
    status: started.status,
    currentStage: started.current_stage,
    mode: started.mode,
    stages,
    safeError: started.safe_error ?? null,
    warnings: started.warnings ?? [],
    updatedAt: nowIso()
  };
}

function compactStagedProgressFromStatus(status: StagedReviewStatusResponse): StagedReviewProgress {
  const sourceStages = isRecord(status.stages) ? status.stages : {};
  const stages = Object.fromEntries(STAGED_STAGE_NAMES.map((stage) => [
    stage,
    cleanStageRow(sourceStages[stage])
  ])) as Record<string, StagedStageState>;

  return {
    schemaVersion: status.schema_version ?? "review_state_v1",
    reviewId: status.review_id,
    status: status.status,
    currentStage: status.current_stage,
    mode: status.mode,
    stages,
    providerStatus: status.provider_status,
    safeError: status.safe_error ?? null,
    updatedAt: status.updated_at ?? nowIso(),
    warnings: status.warnings ?? []
  };
}

function cleanStagedReviewProgress(value: unknown): StagedReviewProgress | undefined {
  if (!isRecord(value)) return undefined;
  const reviewId = typeof value.reviewId === "string" ? value.reviewId : "";
  if (!reviewId) return undefined;
  const status = typeof value.status === "string" && ["pending", "running", "completed", "partial", "blocked", "failed"].includes(value.status)
    ? value.status as StagedReviewProgress["status"]
    : "running";
  const mode = value.mode === "demo_qa" ? "demo_qa" : "live";
  const sourceStages = isRecord(value.stages) ? value.stages : {};
  const stages = Object.fromEntries(STAGED_STAGE_NAMES.map((stage) => [
    stage,
    cleanStageRow(sourceStages[stage])
  ])) as Record<string, StagedStageState>;
  return {
    schemaVersion: value.schemaVersion === "review_started_v1" ? "review_started_v1" : "review_state_v1",
    reviewId,
    status,
    currentStage: typeof value.currentStage === "string" ? value.currentStage : "input",
    mode,
    stages,
    providerStatus: isRecord(value.providerStatus) ? value.providerStatus as StagedProviderStatus : undefined,
    safeError: isRecord(value.safeError) ? value.safeError as StagedSafeError : null,
    updatedAt: typeof value.updatedAt === "string" ? value.updatedAt : null,
    warnings: stringArray(value.warnings)
  };
}

function advanceStagedProgress(
  progress: StagedReviewProgress | undefined,
  completedStage: string,
  nextStage: string,
  status: StagedReviewProgress["status"] = "partial"
): StagedReviewProgress | undefined {
  if (!progress) return undefined;
  return {
    ...progress,
    schemaVersion: "review_state_v1",
    status,
    currentStage: nextStage,
    stages: {
      ...progress.stages,
      [completedStage]: cleanStageRow({
        ...progress.stages[completedStage],
        status: "completed",
        completed_at: nowIso()
      })
    },
    safeError: null,
    updatedAt: nowIso()
  };
}

function cleanReviewState(value: ActiveReviewState): ActiveReviewState {
  const reviewResult = cleanReviewResult(value.reviewResult);
  const reviewSummary = cleanReviewSummary(value.reviewSummary);
  const clientFitProfile = cleanClientFitProfileInput(value.clientFitProfile);
  const stagedProgress = cleanStagedReviewProgress(value.stagedProgress);
  const runStatus: ReviewRunStatus = value.runStatus === "failed" || stagedProgress?.status === "failed"
    ? "failed"
    : isCompletedReviewResult(reviewResult) || reviewSummary?.status === "completed"
      ? "completed"
      : value.runStatus === "running" || stagedProgress?.status === "running"
        ? "running"
        : "draft";
  const builderSetup = compactBuilderSetup(value.builderSetup) ?? reviewSummary?.builderSetup;
  const candidateGenerationRaw = cleanCandidateGenerationSummary(value.candidateGeneration);
  const candidateMatchesBuilder = Boolean(
    candidateGenerationRaw
    && (!builderSetup || candidateGenerationRaw.selectedCardId === builderSetup.selected_card_id)
  );
  const candidateGeneration = candidateMatchesBuilder ? candidateGenerationRaw : undefined;
  const comparisonResult = cleanComparisonResultSummary(value.comparisonResult);
  const verdictResult = cleanVerdictResultSummary(value.verdictResult);
  const reportResult = cleanReportResultSummary(value.reportResult);
  const effectiveReviewId = typeof value.reviewId === "string" ? value.reviewId : reviewSummary?.reviewId ?? reviewResult?.review_id;
  const hasCompletedReviewResult = runStatus === "completed" && Boolean(reviewResult || reviewSummary);
  const readOnlyHistory = Boolean(value.readOnlyHistory || (hasCompletedReviewResult && !value.lineageAvailable));
  const hasLiveLineage = Boolean(value.lineageAvailable && !readOnlyHistory);
  const candidateMatchesReview = Boolean(
    candidateGeneration
    && (!hasLiveLineage || (candidateGeneration.reviewId && effectiveReviewId && candidateGeneration.reviewId === effectiveReviewId))
  );
  const comparisonMatchesCandidate = Boolean(
    comparisonResult
    && candidateGeneration
    && candidateMatchesReview
    && (!hasLiveLineage || (comparisonResult.reviewId && effectiveReviewId && comparisonResult.reviewId === effectiveReviewId))
    && comparisonResult.selectedCardId === candidateGeneration.selectedCardId
    && comparisonResult.candidateId === candidateGeneration.candidateId
  );
  const verdictMatchesCandidate = Boolean(
    verdictResult
    && candidateGeneration
    && comparisonMatchesCandidate
    && (!hasLiveLineage || (verdictResult.reviewId && effectiveReviewId && verdictResult.reviewId === effectiveReviewId))
    && verdictResult.selectedCardId === candidateGeneration.selectedCardId
    && verdictResult.candidateId === candidateGeneration.candidateId
  );
  const reportMatchesCandidate = Boolean(
    reportResult
    && candidateGeneration
    && verdictMatchesCandidate
    && (!hasLiveLineage || (reportResult.reviewId && effectiveReviewId && reportResult.reviewId === effectiveReviewId))
    && reportResult.selectedCardId === candidateGeneration.selectedCardId
    && reportResult.candidateId === candidateGeneration.candidateId
  );

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
    clientFitProfile,
    cloudPortfolio: value.cloudPortfolio?.id && value.cloudPortfolio?.name
      ? {
        id: value.cloudPortfolio.id,
        name: value.cloudPortfolio.name,
        versionId: typeof value.cloudPortfolio.versionId === "string" ? value.cloudPortfolio.versionId : undefined,
        versionNumber: typeof value.cloudPortfolio.versionNumber === "number" ? value.cloudPortfolio.versionNumber : undefined
      }
      : undefined,
    portfolioVersionId: typeof value.portfolioVersionId === "string"
      ? value.portfolioVersionId
      : typeof value.cloudPortfolio?.versionId === "string"
        ? value.cloudPortfolio.versionId
        : undefined,
    portfolioVersionNumber: typeof value.portfolioVersionNumber === "number"
      ? value.portfolioVersionNumber
      : typeof value.cloudPortfolio?.versionNumber === "number"
        ? value.cloudPortfolio.versionNumber
        : undefined,
    readOnlyHistory,
    lineageAvailable: Boolean(value.lineageAvailable && !readOnlyHistory),
    submitted: Boolean(value.submitted),
    reviewId: effectiveReviewId,
    reviewResult,
    reviewSummary,
    stagedProgress,
    builderSetup,
    candidateGeneration: candidateMatchesReview ? candidateGeneration : undefined,
    comparisonResult: comparisonMatchesCandidate ? comparisonResult : undefined,
    verdictResult: verdictMatchesCandidate ? verdictResult : undefined,
    reportResult: reportMatchesCandidate ? reportResult : undefined,
    runMode: value.runMode === "real_run" ? "real_run" : "sample_demo",
    runStatus,
    reviewError: value.reviewError?.message ? value.reviewError : undefined,
    diagnosisReady: Boolean(value.diagnosisReady && (hasCompletedReviewResult || isStagedStageReady(stagedProgress, "xray"))),
    evidenceReady: Boolean((value.evidenceReady ?? value.diagnosisReady) && (hasCompletedReviewResult || isStagedStageReady(stagedProgress, "stress"))),
    improvementPathsReady: Boolean((value.improvementPathsReady ?? value.diagnosisReady) && (hasCompletedReviewResult || isStagedStageReady(stagedProgress, "launchpad_builder"))),
    candidateReady: Boolean(hasLiveLineage && value.candidateReady && candidateMatchesReview && isCompareReadyCandidateGeneration(candidateGeneration)),
    comparisonReady: Boolean(hasLiveLineage && value.comparisonReady && comparisonMatchesCandidate && comparisonResultCanGenerateVerdict(comparisonResult)),
    verdictReady: Boolean(hasLiveLineage && value.verdictReady && verdictMatchesCandidate),
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

    const clean = cleanReviewState({
      ...parsed,
      reviewResult: undefined
    } as ActiveReviewState);
    if (isLegacyUnsubmittedDemoPortfolio(clean)) {
      return {
        ...clean,
        holdings: [],
        updatedAt: nowIso()
      };
    }

    return clean;
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
  const { enabled: cloudEnabled, status: authStatus, user } = useSupabaseAuth();
  const {
    setNotice: setCloudNotice,
    savedReviews,
    workspaceState,
    workspaceLoading,
    reviewsLoading,
    ensurePortfolioVersion
  } = useSupabasePersistence();
  const lastPersistedDiagnosisKeyRef = useRef<string | null>(null);
  const lastPersistedStagedKeyRef = useRef<string | null>(null);
  const lastHydratedWorkspaceKeyRef = useRef<string | null>(null);
  const lastEnsuredDraftVersionKeyRef = useRef<string | null>(null);

  useEffect(() => {
    setActiveReview(readStoredReview());
    setHydrated(true);
  }, []);

  useEffect(() => {
    if (!hydrated) return;
    writeStoredReview(activeReview);
  }, [activeReview, hydrated]);

  useEffect(() => {
    if (!hydrated || activeReview?.clientFitProfile || !hasCompletedOnboarding()) return;
    const profile = cleanClientFitProfileInput(buildClientFitProfileFromOnboarding(readOnboardingState()));
    if (!profile) return;
    setActiveReview((current) => ({
      ...current,
      investorCurrency: current?.investorCurrency || "USD",
      holdings: current?.holdings ?? [],
      clientFitProfile: profile,
      runMode: current?.runMode ?? "sample_demo",
      runStatus: current?.runStatus ?? "draft",
      submitted: current?.submitted ?? false,
      diagnosisReady: current?.diagnosisReady ?? false,
      evidenceReady: current?.evidenceReady ?? false,
      improvementPathsReady: current?.improvementPathsReady ?? false,
      candidateReady: current?.candidateReady ?? false,
      comparisonReady: current?.comparisonReady ?? false,
      verdictReady: current?.verdictReady ?? false,
      updatedAt: new Date().toISOString()
    }));
  }, [activeReview?.clientFitProfile, hydrated]);

  const saveClientFitProfile = useCallback((profile: ClientFitInput) => {
    const cleaned = cleanClientFitProfileInput(profile);
    if (!cleaned) return;
    setActiveReview((current) => ({
      investorCurrency: current?.investorCurrency || "USD",
      holdings: current?.holdings ?? [],
      clientFitProfile: cleaned,
      cloudPortfolio: current?.cloudPortfolio,
      portfolioVersionId: current?.portfolioVersionId,
      portfolioVersionNumber: current?.portfolioVersionNumber,
      readOnlyHistory: false,
      lineageAvailable: false,
      reviewId: undefined,
      reviewResult: undefined,
      reviewSummary: undefined,
      builderSetup: undefined,
      candidateGeneration: undefined,
      comparisonResult: undefined,
      verdictResult: undefined,
      reportResult: undefined,
      runMode: "sample_demo",
      runStatus: "draft",
      reviewError: undefined,
      submitted: false,
      diagnosisReady: false,
      evidenceReady: false,
      improvementPathsReady: false,
      candidateReady: false,
      comparisonReady: false,
      verdictReady: false,
      updatedAt: nowIso()
    }));
  }, []);

  const savePortfolioInput = useCallback((input: Pick<ActiveReviewState, "investorCurrency" | "holdings">) => {
    setActiveReview((current) => ({
      investorCurrency: input.investorCurrency || "USD",
      holdings: input.holdings,
      clientFitProfile: current?.clientFitProfile,
      cloudPortfolio: current?.cloudPortfolio
        ? {
          id: current.cloudPortfolio.id,
          name: current.cloudPortfolio.name
        }
        : undefined,
      portfolioVersionId: undefined,
      portfolioVersionNumber: undefined,
      readOnlyHistory: false,
      lineageAvailable: false,
      reviewId: undefined,
      reviewResult: undefined,
      reviewSummary: undefined,
      builderSetup: undefined,
      candidateGeneration: undefined,
      comparisonResult: undefined,
      verdictResult: undefined,
      reportResult: undefined,
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

    setActiveReview((current) => ({
      investorCurrency: input.investorCurrency || "USD",
      holdings: input.holdings,
      clientFitProfile: current?.clientFitProfile,
      cloudPortfolio: current?.cloudPortfolio,
      portfolioVersionId: current?.portfolioVersionId ?? current?.cloudPortfolio?.versionId,
      portfolioVersionNumber: current?.portfolioVersionNumber ?? current?.cloudPortfolio?.versionNumber,
      readOnlyHistory: false,
      lineageAvailable: hasCompletedReviewResult,
      reviewId,
      reviewResult,
      reviewSummary,
      stagedProgress: current?.stagedProgress,
      builderSetup: reviewSummary?.builderSetup,
      candidateGeneration: undefined,
      comparisonResult: undefined,
      verdictResult: undefined,
      reportResult: undefined,
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
    }));
  }, []);

  const startStagedReview = useCallback((input: Pick<ActiveReviewState, "investorCurrency" | "holdings"> & { started: StagedReviewStartedResponse }) => {
    const progress = compactStagedProgressFromStarted(input.started);
    setActiveReview((current) => ({
      investorCurrency: input.investorCurrency || "USD",
      holdings: input.holdings,
      clientFitProfile: current?.clientFitProfile,
      cloudPortfolio: current?.cloudPortfolio,
      portfolioVersionId: current?.portfolioVersionId ?? current?.cloudPortfolio?.versionId,
      portfolioVersionNumber: current?.portfolioVersionNumber ?? current?.cloudPortfolio?.versionNumber,
      readOnlyHistory: false,
      lineageAvailable: true,
      reviewId: progress.reviewId,
      reviewResult: undefined,
      reviewSummary: undefined,
      stagedProgress: progress,
      builderSetup: undefined,
      candidateGeneration: undefined,
      comparisonResult: undefined,
      verdictResult: undefined,
      reportResult: undefined,
      runMode: "real_run",
      runStatus: progress.status === "failed" ? "failed" : "running",
      reviewError: progress.safeError ? {
        message: stagedSafeErrorMessage(progress.safeError),
        occurredAt: nowIso()
      } : undefined,
      submitted: true,
      diagnosisReady: isStagedStageReady(progress, "xray"),
      evidenceReady: isStagedStageReady(progress, "stress"),
      improvementPathsReady: isStagedStageReady(progress, "launchpad_builder"),
      candidateReady: false,
      comparisonReady: false,
      verdictReady: false,
      updatedAt: nowIso()
    }));
  }, []);

  const recordStagedProgress = useCallback((status: StagedReviewStatusResponse) => {
    const progress = compactStagedProgressFromStatus(status);
    setActiveReview((current) => current ? {
      ...current,
      reviewId: progress.reviewId,
      stagedProgress: progress,
      readOnlyHistory: false,
      lineageAvailable: true,
      runMode: "real_run",
      runStatus: progress.status === "failed" ? "failed" : current.runStatus === "completed" ? "completed" : "running",
      reviewError: progress.safeError ? {
        message: stagedSafeErrorMessage(progress.safeError),
        occurredAt: nowIso()
      } : current.reviewError,
      submitted: true,
      diagnosisReady: current.diagnosisReady || isStagedStageReady(progress, "xray"),
      evidenceReady: current.evidenceReady || isStagedStageReady(progress, "stress"),
      improvementPathsReady: current.improvementPathsReady || isStagedStageReady(progress, "launchpad_builder"),
      candidateReady: current.candidateReady || isStagedStageReady(progress, "candidate"),
      comparisonReady: current.comparisonReady || isStagedStageReady(progress, "comparison"),
      verdictReady: current.verdictReady || isStagedStageReady(progress, "verdict"),
      updatedAt: nowIso()
    } : {
      investorCurrency: "USD",
      holdings: [],
      readOnlyHistory: false,
      lineageAvailable: true,
      reviewId: progress.reviewId,
      stagedProgress: progress,
      runMode: "real_run",
      runStatus: progress.status === "failed" ? "failed" : "running",
      reviewError: progress.safeError ? {
        message: stagedSafeErrorMessage(progress.safeError),
        occurredAt: nowIso()
      } : undefined,
      submitted: true,
      diagnosisReady: isStagedStageReady(progress, "xray"),
      evidenceReady: isStagedStageReady(progress, "stress"),
      improvementPathsReady: isStagedStageReady(progress, "launchpad_builder"),
      candidateReady: isStagedStageReady(progress, "candidate"),
      comparisonReady: isStagedStageReady(progress, "comparison"),
      verdictReady: isStagedStageReady(progress, "verdict"),
      updatedAt: nowIso()
    });
  }, []);

  const recordReviewError = useCallback((input: Pick<ActiveReviewState, "investorCurrency" | "holdings"> & { message: string; details?: string }) => {
    setActiveReview((current) => ({
      investorCurrency: input.investorCurrency || "USD",
      holdings: input.holdings,
      clientFitProfile: current?.clientFitProfile,
      cloudPortfolio: current?.cloudPortfolio,
      portfolioVersionId: current?.portfolioVersionId ?? current?.cloudPortfolio?.versionId,
      portfolioVersionNumber: current?.portfolioVersionNumber ?? current?.cloudPortfolio?.versionNumber,
      readOnlyHistory: false,
      lineageAvailable: false,
      reviewId: undefined,
      reviewResult: undefined,
      reviewSummary: undefined,
      builderSetup: undefined,
      candidateGeneration: undefined,
      comparisonResult: undefined,
      verdictResult: undefined,
      reportResult: undefined,
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
    }));
  }, []);

  const linkCloudPortfolio = useCallback((portfolio: ActiveReviewState["cloudPortfolio"]) => {
    setActiveReview((current) => current ? {
      ...current,
      cloudPortfolio: portfolio ?? undefined,
      portfolioVersionId: portfolio?.versionId ?? current.portfolioVersionId,
      portfolioVersionNumber: portfolio?.versionNumber ?? current.portfolioVersionNumber,
      updatedAt: nowIso()
    } : current);
  }, []);

  const loadCloudPortfolioInput = useCallback((input: { portfolioId: string; name: string; investorCurrency: string; holdings: ReviewHolding[]; versionId?: string; versionNumber?: number }) => {
    setActiveReview((current) => ({
      investorCurrency: input.investorCurrency || "USD",
      holdings: input.holdings,
      clientFitProfile: current?.clientFitProfile,
      cloudPortfolio: {
        id: input.portfolioId,
        name: input.name,
        versionId: input.versionId,
        versionNumber: input.versionNumber
      },
      portfolioVersionId: input.versionId,
      portfolioVersionNumber: input.versionNumber,
      readOnlyHistory: false,
      lineageAvailable: false,
      reviewId: undefined,
      reviewResult: undefined,
      reviewSummary: undefined,
      builderSetup: undefined,
      candidateGeneration: undefined,
      comparisonResult: undefined,
      verdictResult: undefined,
      reportResult: undefined,
      runMode: "sample_demo",
      runStatus: "draft",
      reviewError: undefined,
      submitted: false,
      diagnosisReady: false,
      evidenceReady: false,
      improvementPathsReady: false,
      candidateReady: false,
      comparisonReady: false,
      verdictReady: false,
      updatedAt: nowIso()
    }));
  }, []);


  const hydrateCloudReview = useCallback((savedReview: SavedReviewRecord) => {
    const diagnosisStage = getRecord(savedReview.stages.diagnosis);
    const builderStage = getRecord(savedReview.stages.builder);
    const candidateStage = getRecord(savedReview.stages.candidate);
    const comparisonStage = getRecord(savedReview.stages.comparison);
    const verdictStage = getRecord(savedReview.stages.verdict);
    const reportStage = getRecord(savedReview.stages.report);
    const portfolio = savedReview.portfolioSnapshot;
    const compact = savedReview.compactSummary;
    const stagedProgress = cleanStagedReviewProgress(compact.stagedProgress);
    if (savedReview.status === "draft" || savedReview.mode === "draft" || compact.reviewKind === "draft") {
      setActiveReview(cleanReviewState({
        investorCurrency: portfolio.investorCurrency ?? (typeof compact.investorCurrency === "string" ? compact.investorCurrency : "USD"),
        holdings: portfolio.holdings ?? [],
        clientFitProfile: undefined,
        cloudPortfolio: savedReview.portfolioId && typeof compact.activeCloudPortfolioName === "string" ? {
          id: savedReview.portfolioId,
          name: compact.activeCloudPortfolioName,
          versionId: savedReview.portfolioVersionId,
          versionNumber: typeof compact.activeCloudPortfolioVersionNumber === "number" ? compact.activeCloudPortfolioVersionNumber : undefined
        } : undefined,
        portfolioVersionId: savedReview.portfolioVersionId,
        portfolioVersionNumber: typeof compact.activeCloudPortfolioVersionNumber === "number" ? compact.activeCloudPortfolioVersionNumber : undefined,
        readOnlyHistory: false,
        lineageAvailable: false,
        reviewId: undefined,
        reviewResult: undefined,
        reviewSummary: undefined,
        stagedProgress: undefined,
        builderSetup: undefined,
        candidateGeneration: undefined,
        comparisonResult: undefined,
        verdictResult: undefined,
        reportResult: undefined,
        runMode: "sample_demo",
        runStatus: "draft",
        reviewError: undefined,
        submitted: false,
        diagnosisReady: false,
        evidenceReady: false,
        improvementPathsReady: false,
        candidateReady: false,
        comparisonReady: false,
        verdictReady: false,
        updatedAt: savedReview.updatedAt ?? nowIso()
      }));
      return;
    }
    if (!isRecord(diagnosisStage.diagnosis) && stagedProgress) {
      setActiveReview(cleanReviewState({
        investorCurrency: portfolio.investorCurrency ?? (typeof compact.investorCurrency === "string" ? compact.investorCurrency : "USD"),
        holdings: portfolio.holdings ?? [],
        clientFitProfile: undefined,
        cloudPortfolio: savedReview.portfolioId && typeof compact.activeCloudPortfolioName === "string" ? {
          id: savedReview.portfolioId,
          name: compact.activeCloudPortfolioName,
          versionId: savedReview.portfolioVersionId,
          versionNumber: typeof compact.activeCloudPortfolioVersionNumber === "number" ? compact.activeCloudPortfolioVersionNumber : undefined
        } : undefined,
        portfolioVersionId: savedReview.portfolioVersionId,
        portfolioVersionNumber: typeof compact.activeCloudPortfolioVersionNumber === "number" ? compact.activeCloudPortfolioVersionNumber : undefined,
        readOnlyHistory: true,
        lineageAvailable: false,
        reviewId: savedReview.reviewId,
        reviewResult: undefined,
        reviewSummary: undefined,
        stagedProgress,
        builderSetup: undefined,
        candidateGeneration: undefined,
        comparisonResult: undefined,
        verdictResult: undefined,
        reportResult: undefined,
        runMode: "real_run",
        runStatus: stagedProgress.status === "failed" ? "failed" : stagedProgress.status === "completed" ? "completed" : "running",
        reviewError: stagedProgress.safeError ? {
          message: stagedSafeErrorMessage(stagedProgress.safeError),
          occurredAt: savedReview.updatedAt ?? nowIso()
        } : undefined,
        submitted: true,
        diagnosisReady: isStagedStageReady(stagedProgress, "xray"),
        evidenceReady: isStagedStageReady(stagedProgress, "stress"),
        improvementPathsReady: isStagedStageReady(stagedProgress, "launchpad_builder"),
        candidateReady: false,
        comparisonReady: false,
        verdictReady: false,
        updatedAt: savedReview.updatedAt ?? nowIso()
      }));
      return;
    }
    const diagnosis = getRecord(diagnosisStage.diagnosis);
    const summaryGeneratedAt = typeof compact.generatedAt === "string" ? compact.generatedAt : savedReview.completedAt ?? savedReview.updatedAt ?? nowIso();
    const reviewSummary: ReviewSummary = {
      version: 1,
      source: savedReview.mode === "real_run" ? "real_run" : "real_run",
      status: savedReview.status === "failed" ? "failed" : "completed",
      reviewId: savedReview.reviewId,
      generatedAt: summaryGeneratedAt,
      investorCurrency: portfolio.investorCurrency ?? (typeof compact.investorCurrency === "string" ? compact.investorCurrency : "USD"),
      holdingsCount: typeof compact.holdingsCount === "number" ? compact.holdingsCount : portfolio.holdings?.length ?? 0,
      totalWeight: typeof compact.totalWeight === "number" ? compact.totalWeight : (portfolio.holdings ?? []).reduce((sum, holding) => sum + holding.weight, 0),
      cashWeight: typeof compact.cashWeight === "number" ? compact.cashWeight : (portfolio.holdings ?? []).filter((holding) => holding.type === "cash").reduce((sum, holding) => sum + holding.weight, 0),
      rawOutputKeys: stringArray(diagnosisStage.artifactRefs),
      outputPaths: {},
      diagnosis: {
        status: textValue(diagnosis.status, textValue(compact.diagnosisStatus, "Diagnosis saved")),
        headline: normalizeDisplaySentence(diagnosis.headline, textValue(compact.diagnosisHeadline, "Saved diagnosis summary recovered from cloud.")),
        evidenceQuality: formatUnknownValue(diagnosis.evidenceQuality, textValue(compact.evidenceQuality, "Evidence status unavailable")),
        nextStep: normalizeDisplaySentence(diagnosis.nextStep, "Continue from the saved compact review state."),
        boundaryNote: normalizeDisplaySentence(diagnosis.boundaryNote, "Recovered cloud state is compact app data, not full generated evidence."),
        drivers: stringArray(diagnosis.drivers),
        metrics: Array.isArray(diagnosis.metrics) ? diagnosis.metrics.filter(isRecord).map((metric) => ({
          label: textValue(metric.label, "Metric"),
          value: formatUnknownValue(metric.value),
          detail: typeof metric.detail === "string" ? metric.detail : undefined,
          tone: statusToneValue(metric.tone)
        })) : [],
        selectedDiagnosisRole: typeof diagnosis.selectedDiagnosisRole === "string" ? diagnosis.selectedDiagnosisRole : undefined,
        sourceArtifacts: stringArray(diagnosis.sourceArtifacts),
        rejectedAlternatives: stringArray(diagnosis.rejectedAlternatives),
        rationaleRefs: stringArray(diagnosis.rationaleRefs)
      },
      evidence: undefined,
      clientFit: cleanClientFitDisplaySummary(savedReview.clientFit) ?? cleanClientFitDisplaySummary(compact.clientFit),
      primaryProblem: typeof compact.primaryProblem === "string" ? compact.primaryProblem : undefined,
      problemSeverity: typeof compact.problemSeverity === "string" ? compact.problemSeverity : undefined,
      problemConfidence: typeof compact.problemConfidence === "string" ? compact.problemConfidence : undefined,
      suggestedActionPaths: stringArray(compact.suggestedActionPaths),
      launchpadCardsCount: typeof compact.launchpadCardsCount === "number" ? compact.launchpadCardsCount : 0,
      launchpadCards: [],
      builderSetup: compactBuilderSetup(getRecord(builderStage.builderSetup)),
      recommendedFirstTest: typeof compact.recommendedFirstTest === "string" ? compact.recommendedFirstTest : undefined,
      candidateLaunchpadAvailable: Boolean(compact.candidateLaunchpadAvailable),
      problemClassificationAvailable: Boolean(compact.problemClassificationAvailable),
      storage: {
        summaryBytes: estimateJsonBytes(compact),
        rawBytes: 0,
        rawPersisted: false,
        rawAccessStrategy: "Recovered from compact Supabase app-data summaries; full generated artifacts remain local/run-scoped."
      }
    };
    const candidateGeneration = cleanCandidateGenerationSummary({
      ...getRecord(candidateStage.candidate),
      reviewId: savedReview.reviewId
    });
    const comparisonResult = cleanComparisonResultSummary({
      ...getRecord(comparisonStage.comparison),
      reviewId: savedReview.reviewId
    });
    const verdictResult = cleanVerdictResultSummary({
      ...getRecord(verdictStage.verdict),
      reviewId: savedReview.reviewId
    });
    const reportResult = cleanReportResultSummary({
      ...getRecord(reportStage.report),
      reviewId: savedReview.reviewId
    });
    setActiveReview(cleanReviewState({
      investorCurrency: reviewSummary.investorCurrency,
      holdings: portfolio.holdings ?? [],
      clientFitProfile: undefined,
      cloudPortfolio: savedReview.portfolioId && typeof compact.activeCloudPortfolioName === "string" ? {
        id: savedReview.portfolioId,
        name: compact.activeCloudPortfolioName,
        versionId: savedReview.portfolioVersionId,
        versionNumber: typeof compact.activeCloudPortfolioVersionNumber === "number" ? compact.activeCloudPortfolioVersionNumber : undefined
      } : undefined,
      portfolioVersionId: savedReview.portfolioVersionId,
      portfolioVersionNumber: typeof compact.activeCloudPortfolioVersionNumber === "number" ? compact.activeCloudPortfolioVersionNumber : undefined,
      readOnlyHistory: true,
      lineageAvailable: false,
      reviewId: savedReview.reviewId,
      reviewResult: undefined,
      reviewSummary,
      stagedProgress,
      builderSetup: reviewSummary.builderSetup,
      candidateGeneration,
      comparisonResult,
      verdictResult,
      reportResult,
      runMode: "real_run",
      runStatus: reviewSummary.status,
      reviewError: undefined,
      submitted: true,
      diagnosisReady: true,
      evidenceReady: true,
      improvementPathsReady: true,
      candidateReady: false,
      comparisonReady: false,
      verdictReady: false,
      updatedAt: savedReview.updatedAt ?? nowIso()
    }));
  }, []);

  const markLiveLineageUnavailable = useCallback((message?: string) => {
    setActiveReview((current) => current ? {
      ...current,
      readOnlyHistory: true,
      lineageAvailable: false,
      candidateGeneration: undefined,
      comparisonResult: undefined,
      verdictResult: undefined,
      reportResult: undefined,
      candidateReady: false,
      comparisonReady: false,
      verdictReady: false,
      reviewError: message ? {
        message,
        occurredAt: nowIso()
      } : current.reviewError,
      updatedAt: nowIso()
    } : current);
  }, []);

  useEffect(() => {
    if (!hydrated || !cloudEnabled || authStatus !== "signed_in" || !user?.id) return;
    if (workspaceLoading || reviewsLoading) return;
    if (!workspaceState?.activeReviewRowId && !workspaceState?.lastOpenedReviewRowId) return;

    const reviewRowId = workspaceState.activeReviewRowId ?? workspaceState.lastOpenedReviewRowId;
    const savedReview = savedReviews.find((review) => review.id === reviewRowId);
    if (!savedReview) return;

    const workspaceKey = [
      user.id,
      reviewRowId,
      workspaceState.activePortfolioId ?? "no_portfolio",
      workspaceState.activePortfolioVersionId ?? "no_version",
      savedReview.updatedAt ?? "no_review_update",
      workspaceState.updatedAt ?? "no_workspace_update"
    ].join(":");
    if (lastHydratedWorkspaceKeyRef.current === workspaceKey) return;

    const localUpdatedAt = activeReview?.updatedAt ? Date.parse(activeReview.updatedAt) : 0;
    const cloudUpdatedAt = Date.parse(savedReview.updatedAt ?? workspaceState.updatedAt ?? "0");
    const cloudHasActiveWorkspace = Boolean(workspaceState.activeReviewRowId || workspaceState.activePortfolioVersionId);
    if (activeReview?.reviewId && activeReview.reviewId !== savedReview.reviewId && !cloudHasActiveWorkspace && localUpdatedAt > cloudUpdatedAt) {
      return;
    }

    lastHydratedWorkspaceKeyRef.current = workspaceKey;
    hydrateCloudReview(savedReview);
  }, [activeReview?.reviewId, activeReview?.updatedAt, authStatus, cloudEnabled, hydrateCloudReview, hydrated, reviewsLoading, savedReviews, user?.id, workspaceLoading, workspaceState]);


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
      reportResult: undefined,
      candidateReady: false,
      comparisonReady: false,
      verdictReady: false,
      updatedAt: nowIso()
    } : current);
  }, []);

  const clearDownstreamReviewState = useCallback(() => {
    setActiveReview((current) => current ? {
      ...current,
      candidateGeneration: undefined,
      comparisonResult: undefined,
      verdictResult: undefined,
      reportResult: undefined,
      candidateReady: false,
      comparisonReady: false,
      verdictReady: false,
      updatedAt: nowIso()
    } : current);
  }, []);

  const markCandidateReady = useCallback(() => {
    setActiveReview((current) => current ? {
      ...current,
      candidateReady: Boolean(current.lineageAvailable && !current.readOnlyHistory && isCompareReadyCandidateGeneration(current.candidateGeneration)),
      comparisonReady: false,
      verdictReady: false,
      updatedAt: nowIso()
    } : current);
  }, []);

  const recordCandidateGeneration = useCallback((result: unknown) => {
    const resultRecord = getRecord(result);
    const apiEnvelope = fastApiEnvelopeRecord(resultRecord) as CandidateResponse | Record<string, unknown>;
    const apiData = getRecord(apiEnvelope.data);
    const apiCandidate = getRecord(apiData.candidate);
    const apiHypothesis = getRecord(apiData.hypothesis);
    const candidateGeneration = getRecord(resultRecord.candidate_generation);
    const candidate = getRecord(candidateGeneration.candidate);
    const weightsRecord = getRecord(apiCandidate.weight_summary ?? candidate.weights);
    const weights = Object.entries(weightsRecord)
      .filter((entry): entry is [string, number] => typeof entry[1] === "number" && Number.isFinite(entry[1]))
      .map(([ticker, weight]) => ({ ticker, weight }));
    const status = textValue(resultRecord.status, "unknown");
    const nextAllowedActions = stringArray(apiData.next_allowed_actions);
    const generationStatus = textValue(apiCandidate.generation_status, textValue(resultRecord.generation_status, textValue(candidateGeneration.generation_status, "unknown")));
    const summary: CandidateGenerationSummary = {
      reviewId: firstText(resultRecord.review_id),
      status,
      stage: "candidate_generation",
      selectedCardId: textValue(resultRecord.selected_card_id, ""),
      candidateId: textValue(apiCandidate.candidate_id, textValue(resultRecord.candidate_id, textValue(candidate.candidate_id, ""))),
      methodLabel: firstText(apiCandidate.method_label) ? formatUnknownValue(firstText(apiCandidate.method_label)) : undefined,
      hypothesis: firstText(apiHypothesis.hypothesis) ? normalizeDisplaySentence(firstText(apiHypothesis.hypothesis)) : undefined,
      successCriteria: stringArray(apiHypothesis.success_criteria).map((item) => normalizeDisplaySentence(item)),
      tradeoffToWatch: firstText(apiHypothesis.tradeoff_to_watch) ? normalizeDisplaySentence(firstText(apiHypothesis.tradeoff_to_watch)) : undefined,
      decisionBoundary: firstText(apiHypothesis.decision_boundary) ? normalizeDisplaySentence(firstText(apiHypothesis.decision_boundary)) : undefined,
      generationStatus,
      canCompare: nextAllowedActions.includes("run_comparison") || Boolean(resultRecord.can_compare),
      path: typeof resultRecord.path === "string" ? resultRecord.path : undefined,
      weights,
      generatedAt: nowIso()
    };

    setActiveReview((current) => current ? {
      ...current,
      readOnlyHistory: false,
      lineageAvailable: true,
      candidateGeneration: {
        ...summary,
        reviewId: summary.reviewId ?? current.reviewId
      },
      candidateReady: isCompareReadyCandidateGeneration(summary),
      stagedProgress: isCompareReadyCandidateGeneration(summary)
        ? advanceStagedProgress(current.stagedProgress, "candidate", "comparison")
        : current.stagedProgress,
      comparisonResult: undefined,
      verdictResult: undefined,
      reportResult: undefined,
      comparisonReady: false,
      verdictReady: false,
      updatedAt: nowIso()
    } : current);
  }, []);

  const recordComparisonResult = useCallback((result: unknown) => {
    const resultRecord = getRecord(result);
    const apiEnvelope = fastApiEnvelopeRecord(resultRecord) as ComparisonResponse | Record<string, unknown>;
    const apiData = getRecord(apiEnvelope.data);
    const apiComparison = getRecord(apiData.comparison);
    const evidenceContext = fastApiEvidenceChainContext(resultRecord);
    const apiClientFit = cleanClientFitDisplaySummary(apiData.client_fit);
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
    const siteExplanation = cleanSiteExplanationBundle(resultRecord.site_explanation_bundle);
    const successCriteriaStatus = formatUnknownValue(apiComparison.success_criteria_result, "Unknown");
    const materialityStatus = formatUnknownValue(apiComparison.materiality, "Unknown");
    const summary: ComparisonResultSummary = {
      reviewId: firstText(resultRecord.review_id),
      status,
      stage: "current_vs_candidate",
      selectedCardId: textValue(resultRecord.selected_card_id, ""),
      candidateId: textValue(resultRecord.candidate_id, textValue(row.candidate_id, textValue(apiComparison.comparison_id, "").replace(/^current_vs_candidate:/, ""))),
      comparisonStatus: Object.keys(apiComparison).length ? "available" : comparisonStatus,
      viewMode: formatUnknownValue(resultRecord.view_mode ?? currentVsCandidate.view_mode, "Unknown"),
      candidateName: formatUnknownValue(apiComparison.candidate_label ?? row.display_name ?? row.candidate_id, "Generated diagnostic candidate"),
      candidateBoundary: normalizeDisplaySentence(evidenceContext?.candidateBoundary, "Diagnostic comparison only. It does not decide whether to change the portfolio or create a rebalance instruction."),
      evidenceQuality: Object.keys(apiComparison).length ? "FastAPI display comparison evidence" : comparisonStatus === "available" ? "Active comparison evidence" : formatUnknownValue(comparisonStatus, "Evidence status unavailable"),
      summary: evidenceContext?.testedHypothesis
        ? `Tested hypothesis: ${evidenceContext.testedHypothesis} Success criteria: ${successCriteriaStatus}. Materiality: ${materialityStatus}.`
        : comparisonSummaryText({ row, materiality, successCriteria }),
      metrics: dimensionsToMetrics(dimensions),
      improved: compactDimensionList(apiComparison.what_improved ?? row.what_improved, "No available comparison metric showed a clear improvement."),
      worsened: compactDimensionList(apiComparison.what_worsened ?? row.what_worsened, "No available comparison metric showed a clear worsening."),
      neutral: compactDimensionList(apiComparison.what_stayed_similar ?? row.what_stayed_similar, "No neutral metrics were reported."),
      unclear: stringArray(apiComparison.unavailable_metrics).length ? stringArray(apiComparison.unavailable_metrics).map((item) => normalizeDisplaySentence(item)) : unclearList(row, currentVsCandidate),
      turnover: turnoverText(turnoverRequired),
      estimatedCost: estimatedCostText(practicality, transactionCost),
      materiality: Object.keys(apiComparison).length ? `Decision review materiality: ${materialityStatus}.` : materialityText(materiality),
      warnings: [
        ...fastApiWarnings(resultRecord),
        ...stringArray(currentVsCandidate.warnings).map((item) => normalizeDisplaySentence(item))
      ],
      evidenceChainContext: evidenceContext,
      clientFit: apiClientFit,
      path: typeof paths.current_vs_candidate === "string" ? paths.current_vs_candidate : undefined,
      generatedAt: nowIso()
    };

    setActiveReview((current) => current ? {
      ...current,
      reviewResult: current.reviewResult && isRecord(current.reviewResult.outputs) ? {
        ...current.reviewResult,
        outputs: {
          ...current.reviewResult.outputs,
          candidate_comparison: resultRecord.candidate_comparison as JsonValue,
          current_vs_candidate: resultRecord.current_vs_candidate as JsonValue,
          site_explanation_bundle: resultRecord.site_explanation_bundle as JsonValue
        }
      } : current.reviewResult,
      reviewSummary: current.reviewSummary && siteExplanation ? {
        ...current.reviewSummary,
        siteExplanation
      } : current.reviewSummary,
      readOnlyHistory: false,
      lineageAvailable: true,
      comparisonResult: {
        ...summary,
        reviewId: summary.reviewId ?? current.reviewId
      },
      stagedProgress: status === "completed" && comparisonResultCanGenerateVerdict(summary)
        ? advanceStagedProgress(current.stagedProgress, "comparison", "verdict")
        : current.stagedProgress,
      verdictResult: undefined,
      reportResult: undefined,
      candidateReady: true,
      comparisonReady: status === "completed" && comparisonResultCanGenerateVerdict(summary),
      verdictReady: false,
      updatedAt: nowIso()
    } : current);
  }, []);

  const markComparisonReady = useCallback(() => {
    setActiveReview((current) => current ? {
      ...current,
      candidateReady: Boolean(current.lineageAvailable && !current.readOnlyHistory && isCompareReadyCandidateGeneration(current.candidateGeneration)),
      comparisonReady: Boolean(current.lineageAvailable && !current.readOnlyHistory && current.comparisonResult),
      verdictReady: false,
      updatedAt: nowIso()
    } : current);
  }, []);

  const markVerdictReady = useCallback(() => {
    setActiveReview((current) => current ? {
      ...current,
      candidateReady: Boolean(current.lineageAvailable && !current.readOnlyHistory && isCompareReadyCandidateGeneration(current.candidateGeneration)),
      comparisonReady: Boolean(current.lineageAvailable && !current.readOnlyHistory && current.comparisonResult),
      verdictReady: Boolean(current.lineageAvailable && !current.readOnlyHistory && current.verdictResult),
      updatedAt: nowIso()
    } : current);
  }, []);

  const recordVerdictResult = useCallback((result: unknown) => {
    const resultRecord = getRecord(result);
    const apiEnvelope = fastApiEnvelopeRecord(resultRecord) as VerdictResponse | Record<string, unknown>;
    const apiData = getRecord(apiEnvelope.data);
    const apiVerdict = getRecord(apiData.verdict);
    const evidenceContext = fastApiEvidenceChainContext(resultRecord);
    const apiClientFit = cleanClientFitDisplaySummary(apiData.client_fit);
    const verdict = getRecord(resultRecord.decision_verdict);
    const evidence = getRecord(verdict.evidence_summary);
    const noTrade = getRecord(verdict.no_trade);
    const materiality = getRecord(evidence.materiality_for_decision_review);
    const success = getRecord(evidence.success_criteria_result);
    const practicality = getRecord(evidence.practicality);
    const status = textValue(resultRecord.status, "unknown");
    const verdictId = textValue(apiVerdict.verdict_id, textValue(resultRecord.verdict_id, textValue(verdict.verdict_id, "unknown")));
    const decisionStatus = textValue(apiVerdict.verdict, textValue(resultRecord.selection_decision_status, textValue(verdict.selection_decision_status, "unknown")));
    const confidence = textValue(apiVerdict.confidence, textValue(resultRecord.confidence, textValue(verdict.confidence, "unknown")));
    const candidateId = textValue(resultRecord.candidate_id, textValue(verdict.reviewed_candidate_id, textValue(verdict.selected_candidate_id, "")));
    const siteExplanation = cleanSiteExplanationBundle(resultRecord.site_explanation_bundle);
    const apiRationale = stringArray(apiVerdict.rationale).map((item) => normalizeDisplaySentence(item));
    const apiEvidenceUsed = stringArray(apiVerdict.evidence_used).map((item) => normalizeDisplaySentence(item));
    const apiLimitations = stringArray(apiVerdict.limitations).map((item) => normalizeDisplaySentence(item));
    const whatWouldChange = stringArray(apiVerdict.what_would_change_verdict).map((item) => normalizeDisplaySentence(item));

    const summary: VerdictResultSummary = {
      reviewId: firstText(resultRecord.review_id),
      status,
      stage: "decision_verdict",
      selectedCardId: textValue(resultRecord.selected_card_id, ""),
      candidateId,
      verdictId,
      decisionStatus: formatUnknownValue(decisionStatus, "Unknown"),
      confidence: formatUnknownValue(confidence, "Unknown"),
      state: safeVerdictState(verdictId, decisionStatus),
      headline: safeVerdictHeadline(verdictId),
      explanation: safeVerdictExplanation(verdictId, apiRationale[0] ?? textValue(verdict.rationale_summary, "")),
      evidenceQuality: `Verdict evidence - ${formatUnknownValue(confidence, "Unknown")} confidence`,
      boundaryNote: normalizeDisplaySentence(evidenceContext?.recommendationBoundary, "Decision-support only. This is not a trade instruction or rebalance recommendation."),
      keyEvidence: apiEvidenceUsed.length ? apiEvidenceUsed : verdictEvidenceList({
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
          detail: formatUnknownValue(decisionStatus, "Unknown"),
          tone: verdictTone(verdictId)
        },
        {
          label: "No-trade",
          value: noTrade.applies === true ? "Applies" : noTrade.evaluated === true ? "Evaluated" : "Not evaluated",
          detail: "Decision-support evidence",
          tone: noTrade.applies === true ? "green" : noTrade.evaluated === true ? "blue" : "slate"
        },
        {
          label: "Confidence",
          value: formatUnknownValue(confidence, "Unknown"),
          detail: `${stringArray(verdict.confidence_limitations).length} limitation(s)`,
          tone: confidence === "low" ? "amber" : "blue"
        }
      ],
      actionFraming: safeActionFraming(verdictId),
      limitations: apiLimitations.length ? apiLimitations : stringArray(verdict.confidence_limitations).map((item) => normalizeDisplaySentence(item)),
      evidenceUsed: apiEvidenceUsed,
      whatWouldChangeVerdict: whatWouldChange,
      evidenceChainContext: evidenceContext,
      clientFit: apiClientFit,
      path: typeof resultRecord.path === "string" ? resultRecord.path : undefined,
      generatedAt: nowIso()
    };

    setActiveReview((current) => current ? {
      ...current,
      reviewResult: current.reviewResult && isRecord(current.reviewResult.outputs) ? {
        ...current.reviewResult,
        outputs: {
          ...current.reviewResult.outputs,
          decision_verdict: resultRecord.decision_verdict as JsonValue,
          site_explanation_bundle: resultRecord.site_explanation_bundle as JsonValue
        }
      } : current.reviewResult,
      reviewSummary: current.reviewSummary && siteExplanation ? {
        ...current.reviewSummary,
        siteExplanation
      } : current.reviewSummary,
      readOnlyHistory: false,
      lineageAvailable: true,
      verdictResult: {
        ...summary,
        reviewId: summary.reviewId ?? current.reviewId
      },
      stagedProgress: status === "completed"
        ? advanceStagedProgress(current.stagedProgress, "verdict", "report")
        : current.stagedProgress,
      reportResult: undefined,
      candidateReady: true,
      comparisonReady: Boolean(current.comparisonReady),
      verdictReady: status === "completed",
      updatedAt: nowIso()
    } : current);
  }, []);

  const recordReportResult = useCallback((result: unknown) => {
    const resultRecord = getRecord(result);
    const display = getRecord(resultRecord.report_display_model);
    const currentReview = activeReview;
    const selectedCardId = currentReview?.candidateGeneration?.selectedCardId ?? textValue(resultRecord.selected_card_id, "");
    const candidateId = currentReview?.candidateGeneration?.candidateId ?? textValue(resultRecord.candidate_id, "");
    const summary = cleanReportResultSummary({
      reviewId: textValue(resultRecord.review_id, currentReview?.reviewId ?? ""),
      status: textValue(resultRecord.status, "unknown"),
      stage: "report",
      selectedCardId,
      candidateId,
      title: display.title,
      subtitle: display.subtitle,
      sections: display.sections,
      evidenceUsed: display.evidenceUsed,
      unavailableEvidence: display.unavailableEvidence,
      nextObservation: display.nextObservation,
      boundaryNote: display.boundaryNote,
      warnings: display.warnings,
      clientFit: display.clientFit,
      generatedAt: display.generatedAt ?? nowIso()
    });
    if (!summary) return;
    setActiveReview((current) => current ? {
      ...current,
      readOnlyHistory: false,
      lineageAvailable: true,
      reportResult: {
        ...summary,
        reviewId: summary.reviewId ?? current.reviewId
      },
      stagedProgress: summary.status === "completed"
        ? advanceStagedProgress(current.stagedProgress, "report", "report", "completed")
        : current.stagedProgress,
      updatedAt: nowIso()
    } : current);
  }, [activeReview]);

  const clearActiveReview = useCallback(() => setActiveReview(null), []);

  useEffect(() => {
    if (!hydrated || !cloudEnabled || authStatus !== "signed_in" || !user?.id) return;
    if (!activeReview?.cloudPortfolio?.id || activeReview.portfolioVersionId || !activeReview.holdings.length) return;
    if (activeReview.reviewId || activeReview.runStatus !== "draft") return;
    const portfolioId = activeReview.cloudPortfolio.id;
    const portfolioName = activeReview.cloudPortfolio.name;

    const draftKey = [
      user.id,
      portfolioId,
      activeReview.investorCurrency,
      holdingsSignature(activeReview.holdings)
    ].join(":");
    if (lastEnsuredDraftVersionKeyRef.current === draftKey) return;
    lastEnsuredDraftVersionKeyRef.current = draftKey;

    let cancelled = false;
    void (async () => {
      const version = await ensurePortfolioVersion({
        portfolioId,
        portfolioName,
        investorCurrency: activeReview.investorCurrency,
        holdings: activeReview.holdings,
        sourceKind: "draft"
      });
      if (cancelled || !version) return;
      setActiveReview((current) => {
        if (!current?.cloudPortfolio || current.reviewId || current.portfolioVersionId) return current;
        if (current.cloudPortfolio.id !== portfolioId) return current;
        return {
          ...current,
          cloudPortfolio: {
            ...current.cloudPortfolio,
            versionId: version.id,
            versionNumber: version.versionNumber
          },
          portfolioVersionId: version.id,
          portfolioVersionNumber: version.versionNumber,
          readOnlyHistory: false,
          lineageAvailable: false,
          updatedAt: nowIso()
        };
      });
    })();
    return () => {
      cancelled = true;
    };
  }, [activeReview, authStatus, cloudEnabled, ensurePortfolioVersion, hydrated, user?.id]);

  useEffect(() => {
    if (!hydrated || !cloudEnabled || authStatus !== "signed_in" || !user?.id) return;
    if (!activeReview?.reviewId || !activeReview.stagedProgress) return;

    const progress = activeReview.stagedProgress;
    const stageStatuses = Object.entries(progress.stages)
      .map(([stage, row]) => `${stage}:${row.status ?? "pending"}`)
      .join("|");
    const persistenceKey = [
      user.id,
      activeReview.reviewId,
      progress.status,
      progress.currentStage,
      progress.updatedAt ?? activeReview.updatedAt,
      stageStatuses
    ].join(":");
    if (lastPersistedStagedKeyRef.current === persistenceKey) return;
    lastPersistedStagedKeyRef.current = persistenceKey;
    let cancelled = false;
    void (async () => {
      try {
        const result = await persistStagedProgressForReview(user.id, activeReview);
        if (!cancelled && result.skipped.length) {
          setCloudNotice("warning", `Skipped oversized staged cloud summary: ${result.skipped.map((item) => `${item.stage} (${item.summarySizeBytes} bytes)`).join(", ")}. Local progress is unchanged.`);
        }
      } catch (error) {
        if (!cancelled) {
          lastPersistedStagedKeyRef.current = null;
          const message = error instanceof Error ? error.message : "Unknown cloud persistence error.";
          setCloudNotice("warning", `Staged progress stayed local, but cloud progress sync failed. ${message}`);
        }
      }
    })();
    return () => {
      cancelled = true;
    };
  }, [activeReview, authStatus, cloudEnabled, hydrated, setCloudNotice, user?.id]);

  useEffect(() => {
    if (!hydrated || !cloudEnabled || authStatus !== "signed_in" || !user?.id) return;
    if (!activeReview?.reviewId || !activeReview.reviewSummary || !activeReview.diagnosisReady) return;

    const persistenceKey = `${user.id}:${activeReview.reviewId}:${activeReview.reviewSummary.generatedAt}:${activeReview.cloudPortfolio?.id ?? "no_portfolio"}`;
    if (lastPersistedDiagnosisKeyRef.current === persistenceKey) return;
    lastPersistedDiagnosisKeyRef.current = persistenceKey;
    let cancelled = false;
    void (async () => {
      try {
        await persistDiagnosisSummaryForReview(user.id, activeReview);
        if (!cancelled) {
          setCloudNotice("info", `Diagnosis summary for ${activeReview.reviewId} was saved to optional cloud history.`);
        }
      } catch (error) {
        if (!cancelled) {
          lastPersistedDiagnosisKeyRef.current = null;
          const message = error instanceof Error ? error.message : "Unknown cloud persistence error.";
          setCloudNotice("warning", `Diagnosis stayed local, but cloud review sync failed. ${message}`);
        }
      }
    })();

    return () => {
      cancelled = true;
    };
  }, [activeReview, authStatus, cloudEnabled, hydrated, setCloudNotice, user?.id]);

  const lastPersistedStagesKeyRef = useRef<string | null>(null);

  useEffect(() => {
    if (!hydrated || !cloudEnabled || authStatus !== "signed_in" || !user?.id) return;
    if (!activeReview?.reviewId || !activeReview.reviewSummary || !activeReview.diagnosisReady) return;
    const stageKey = [
      user.id,
      activeReview.reviewId,
      activeReview.builderSetup?.selected_card_id ?? "no_builder",
      activeReview.candidateGeneration?.generatedAt ?? "no_candidate",
      activeReview.comparisonResult?.generatedAt ?? "no_comparison",
      activeReview.verdictResult?.generatedAt ?? "no_verdict",
      activeReview.reportResult?.generatedAt ?? "no_report"
    ].join(":");
    if (lastPersistedStagesKeyRef.current === stageKey) return;
    if (!activeReview.builderSetup && !activeReview.candidateGeneration && !activeReview.comparisonResult && !activeReview.verdictResult && !activeReview.reportResult) return;
    lastPersistedStagesKeyRef.current = stageKey;
    let cancelled = false;
    void (async () => {
      try {
        const result = await persistCompactStageSummariesForReview(user.id, activeReview);
        if (!cancelled && result.persisted.length) {
          setCloudNotice("info", `Saved compact cloud stage summaries: ${result.persisted.join(", ")}.`);
        }
        if (!cancelled && result.skipped.length) {
          setCloudNotice("warning", `Skipped oversized cloud stage summary: ${result.skipped.map((item) => `${item.stage} (${item.summarySizeBytes} bytes)`).join(", ")}. Local state is unchanged.`);
        }
      } catch (error) {
        if (!cancelled) {
          lastPersistedStagesKeyRef.current = null;
          const detail = error instanceof Error ? ` ${error.message}` : "";
          setCloudNotice("warning", `We could not save your latest workspace update. Your current review is still available on this device.${detail}`);
        }
      }
    })();
    return () => {
      cancelled = true;
    };
  }, [activeReview, authStatus, cloudEnabled, hydrated, setCloudNotice, user?.id]);

  const journeyFlags = useMemo<JourneyFlags>(() => ({
    clientProfileCompleted: Boolean(activeReview?.clientFitProfile || hasProvidedClientFitSummary(activeReview?.reviewSummary?.clientFit)),
    inputCompleted: Boolean(activeReview?.submitted),
    diagnosisGenerated: Boolean(activeReview?.diagnosisReady),
    evidenceGenerated: Boolean(activeReview?.evidenceReady),
    clientFitReady: hasProvidedClientFitSummary(activeReview?.reviewSummary?.clientFit),
    improvementPathsAvailable: Boolean(activeReview?.improvementPathsReady),
    candidateReady: Boolean(activeReview?.candidateReady),
    comparisonReady: Boolean(activeReview?.comparisonReady),
    verdictReady: Boolean(activeReview?.verdictReady)
  }), [activeReview]);

  const value = useMemo<ReviewStateContextValue>(() => ({
    activeReview,
    hydrated,
    saveClientFitProfile,
    savePortfolioInput,
    submitPortfolioInput,
    startStagedReview,
    recordStagedProgress,
    recordReviewError,
    linkCloudPortfolio,
    loadCloudPortfolioInput,
    recordBuilderSetup,
    clearDownstreamReviewState,
    recordCandidateGeneration,
    recordComparisonResult,
    recordVerdictResult,
    recordReportResult,
    hydrateCloudReview,
    markLiveLineageUnavailable,
    markCandidateReady,
    markComparisonReady,
    markVerdictReady,
    clearActiveReview,
    journeyFlags
  }), [activeReview, clearActiveReview, clearDownstreamReviewState, hydrated, journeyFlags, linkCloudPortfolio, loadCloudPortfolioInput, markCandidateReady, markComparisonReady, markLiveLineageUnavailable, markVerdictReady, recordBuilderSetup, recordCandidateGeneration, recordComparisonResult, recordReportResult, recordReviewError, recordStagedProgress, recordVerdictResult, saveClientFitProfile, savePortfolioInput, startStagedReview, submitPortfolioInput]);

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
  return `${value.toFixed(2).replace(/\?.0+$/, "")}%`;
}

function formatDecimalPercent(value: unknown) {
  return typeof value === "number" && Number.isFinite(value) ? formatPercent(value * 100) : "n/a";
}

function formatRawPercent(value: unknown) {
  return typeof value === "number" && Number.isFinite(value) ? formatPercent(value) : "n/a";
}

function formatFlexiblePercent(value: unknown) {
  if (typeof value !== "number" || !Number.isFinite(value)) return "n/a";
  return Math.abs(value) <= 1 ? formatDecimalPercent(value) : formatRawPercent(value);
}

function compactNumber(value: unknown) {
  return typeof value === "number" && Number.isFinite(value) ? value.toFixed(2) : "n/a";
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

function toneForSeverity(value: unknown): StatusTone {
  const normalized = textValue(value, "").toLowerCase();
  if (normalized === "high") return "red";
  if (normalized === "medium" || normalized === "moderate") return "amber";
  if (normalized === "low") return "blue";
  if (normalized === "ok" || normalized === "available") return "green";
  return "slate";
}

function displayLabel(value: unknown, fallback = "Unavailable") {
  return formatUnknownValue(value, fallback);
}

function statusKey(value: unknown) {
  return String(value ?? "")
    .trim()
    .toLowerCase()
    .replace(/[^a-z0-9]+/g, "_")
    .replace(/^_+|_+$/g, "");
}

function dominantExposureNameForHeadline(dominantRiskFactor: Record<string, unknown>, dominantAssetClass: Record<string, unknown>) {
  return displayLabel(dominantRiskFactor.name, displayLabel(dominantAssetClass.name, "the current exposure mix")).toLowerCase();
}

function verdictTone(verdictId: string): StatusTone {
  const key = statusKey(verdictId);
  if (key === "keep_current" || key.includes("no_trade") || key === "no_material_rebalance_recommended") return "green";
  if (verdictId === "evidence_insufficient" || verdictId === "candidate_failed_or_infeasible") return "amber";
  if (verdictId === "test_another_candidate_or_review_evidence") return "blue";
  return "gold";
}

function safeVerdictState(verdictId: string, decisionStatus: string) {
  const verdictKey = statusKey(verdictId);
  const decisionKey = statusKey(decisionStatus);
  if (verdictKey === "keep_current" || verdictKey.includes("no_trade")) return "Keep current";
  if (verdictKey === "no_material_rebalance_recommended") return "No material rebalance";
  if (verdictKey === "evidence_insufficient" || decisionKey === "evidence_insufficient") return "Evidence insufficient";
  if (verdictKey === "candidate_failed_or_infeasible") return "Candidate failed or infeasible";
  if (verdictKey === "test_another_candidate_or_review_evidence") return "Test another hypothesis";
  if (decisionKey === "selected_candidate" || verdictKey.includes("rebalance")) return "Rebalance review";
  return "Evidence insufficient";
}

function safeVerdictHeadline(verdictId: string) {
  const verdictKey = statusKey(verdictId);
  if (verdictKey === "keep_current" || verdictKey.includes("no_trade") || verdictKey === "no_material_rebalance_recommended") return "Keep the current portfolio under review.";
  if (verdictKey === "evidence_insufficient") return "Do not make a decision from this evidence yet.";
  if (verdictKey === "candidate_failed_or_infeasible") return "The candidate test did not produce usable comparison evidence.";
  if (verdictKey === "test_another_candidate_or_review_evidence") return "The evidence is mixed; test another diagnostic hypothesis.";
  return "Rebalance review is supported by material evidence.";
}

function safeVerdictExplanation(verdictId: string, rationale: string) {
  const suffix = rationale ? ` Rationale: ${rationale}` : "";
  const verdictKey = statusKey(verdictId);
  if (verdictKey === "keep_current" || verdictKey.includes("no_trade") || verdictKey === "no_material_rebalance_recommended") {
    return `The current evidence supports no material change. Continue monitoring instead of treating the candidate as an instruction.${suffix}`;
  }
  if (verdictKey === "evidence_insufficient") {
    return `Do not make a portfolio decision from this evidence yet. The candidate comparison is incomplete or degraded, so Portfolio MRI cannot determine whether the candidate improves the diagnosed weakness.${suffix}`;
  }
  if (verdictKey === "candidate_failed_or_infeasible") {
    return `The generated candidate failed or was infeasible, so it cannot support a portfolio action review.${suffix}`;
  }
  if (verdictKey === "test_another_candidate_or_review_evidence") {
    return `The comparison does not support a clear action/no-action decision. Review evidence or test another diagnostic hypothesis.${suffix}`;
  }
  return `The selected candidate is material enough for human decision review, but this UI does not create a trade instruction or rebalance recommendation.${suffix}`;
}

function safeActionFraming(verdictId: string) {
  const verdictKey = statusKey(verdictId);
  if (verdictKey === "keep_current" || verdictKey.includes("no_trade") || verdictKey === "no_material_rebalance_recommended") return "Action framing: no material change; keep monitoring the current portfolio.";
  if (verdictKey === "evidence_insufficient") return "Action framing: generate a valid candidate, test another hypothesis, or keep the current portfolio under monitoring.";
  if (verdictKey === "candidate_failed_or_infeasible") return "Action framing: discard this failed test and choose another diagnostic hypothesis if needed.";
  if (verdictKey === "test_another_candidate_or_review_evidence") return "Action framing: review trade-offs or test another diagnostic hypothesis; no action is implied.";
  return "Action framing: review the rebalance option with its documented trade-offs; no trade instruction is created.";
}

function verdictEvidenceList({
  materiality,
  success,
  noTrade,
  limitations
}: {
  materiality: Record<string, unknown>;
  success: Record<string, unknown>;
  noTrade: Record<string, unknown>;
  limitations: unknown;
}) {
  const rows = [
    `Decision materiality: ${formatUnknownValue(materiality.status, "Not evaluated")} (${normalizeDisplaySentence(materiality.reason, "No reason supplied")}).`,
    `Success criteria: ${formatUnknownValue(success.overall_status, "Not evaluated")}.`,
    `No-trade gate: ${noTrade.applies === true ? "applies" : noTrade.evaluated === true ? "evaluated" : "not evaluated"}.`
  ];
  const firstLimit = stringArray(limitations)[0];
  if (firstLimit) rows.push(`Main confidence limitation: ${normalizeDisplaySentence(firstLimit)}.`);
  return rows;
}

function verdictMonitoringTrigger(verdictId: string, limitations: unknown) {
  const firstLimit = stringArray(limitations)[0];
  if (verdictId === "evidence_insufficient") return firstLimit ? `Re-run the verdict after resolving: ${normalizeDisplaySentence(firstLimit)}.` : "Re-run after missing evidence is available.";
  if (verdictId === "candidate_failed_or_infeasible") return "Re-run only after selecting a different feasible diagnostic candidate.";
  if (verdictId === "no_material_rebalance_recommended") return "Revisit if comparison materiality, turnover, or stress evidence changes materially.";
  return "Revisit before any implementation decision if trade-offs, costs, or risk evidence changes.";
}

function formatSignedDelta(value: unknown, field?: string) {
  if (typeof value !== "number" || !Number.isFinite(value)) return "Delta unavailable";
  const sign = value > 0 ? "+" : "";
  if (field && percentLikeField(field)) return `${sign}${formatDecimalPercent(value)}`;
  return `${sign}${value.toFixed(3).replace(/\?.0+$/, "")}`;
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
  if (typeof value !== "number" || !Number.isFinite(value)) return "Evidence unavailable";
  if (field && percentLikeField(field)) return formatDecimalPercent(value);
  return value.toFixed(3).replace(/\?.0+$/, "");
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
      metric: formatUnknownValue(dimension.label ?? field, "Metric"),
      current: formatComparisonValue(dimension.baseline_value, field),
      candidate: formatComparisonValue(dimension.candidate_value, field),
      direction: status === "available" ? directionLabel(direction) : "Unclear",
      tradeoff: status === "available"
        ? formatSignedDelta(dimension.delta, field)
        : formatUnknownValue(dimension.unavailable_reason, "Metric unavailable"),
      tone: status === "available" ? toneFromDirection(direction) : "slate"
    };
  });
}

function compactDimensionList(value: unknown, fallback: string) {
  const rows = getArray(value)
    .map(getRecord)
    .map((item) => {
      const label = formatUnknownValue(item.label ?? item.field, "");
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
    .map((item) => `${formatUnknownValue(item.label ?? item.field, "Metric")}: ${formatUnknownValue(item.unavailable_reason, "Unavailable")}.`);
  const warnings = stringArray(currentVsCandidate.warnings).map((item) => `Warning: ${normalizeDisplaySentence(item)}.`);
  const result = [...unavailable, ...warnings].filter(Boolean).slice(0, 4);
  return result.length ? result : ["Suitability and mandate fit remain outside this comparison step."];
}

function turnoverText(turnoverRequired: Record<string, unknown>) {
  const status = textValue(turnoverRequired.status, "unavailable");
  const turnover = turnoverRequired.turnover_half_sum_pct;
  if (status === "available" && typeof turnover === "number" && Number.isFinite(turnover)) {
    return `${formatDecimalPercent(turnover)} half-sum turnover required.`;
  }
  return `Turnover evidence ${formatUnknownValue(status, "Unavailable")}.`;
}

function estimatedCostText(practicality: Record<string, unknown>, transactionCost: Record<string, unknown>) {
  const estimated = practicality.estimated_transaction_cost_pct;
  const bps = transactionCost.transaction_cost_bps;
  if (typeof estimated === "number" && Number.isFinite(estimated)) {
    const assumption = typeof bps === "number" && Number.isFinite(bps) ? ` using ${bps} bps assumption` : "";
    return `${formatDecimalPercent(estimated)} estimated transaction cost${assumption}.`;
  }
  return "Estimated transaction cost evidence unavailable.";
}

function materialityText(materiality: Record<string, unknown>) {
  return `${formatUnknownValue(materiality.status, "Not evaluated")}: ${normalizeDisplaySentence(materiality.reason, "No reason supplied")}.`;
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
    `Comparison found ${improvedCount} improved, ${worsenedCount} worsened, and ${neutralCount} neutral metric groups.`,
    `Success criteria: ${formatUnknownValue(successCriteria.overall_status, "Not evaluated")}.`,
    `Decision review materiality: ${formatUnknownValue(materiality.status, "Not evaluated")}.`
  ].join(" ");
}

function fastApiEnvelopeRecord(value: unknown): Record<string, unknown> {
  return getRecord(getRecord(value).fastapi_envelope);
}

function fastApiDataRecord(value: unknown): Record<string, unknown> {
  return getRecord(fastApiEnvelopeRecord(value).data);
}

function fastApiStatus(value: unknown, fallback = "completed") {
  return textValue(fastApiEnvelopeRecord(value).status, fallback);
}

function fastApiWarnings(value: unknown) {
  return stringArray(fastApiEnvelopeRecord(value).warnings).map((item) => normalizeDisplaySentence(item));
}

function fastApiEvidenceChainContext(value: unknown): EvidenceChainContextSummary | undefined {
  const context = getRecord(fastApiDataRecord(value).evidence_chain_context) as DownstreamEvidenceChainContext | Record<string, unknown>;
  return cleanEvidenceChainContextSummary(context);
}

function diagnosisFromFastApiEnvelope(envelope: CreateReviewResponse | Record<string, unknown> | unknown): DiagnosisState | null {
  const data = getRecord(getRecord(envelope).data);
  const diagnosis = getRecord(data.diagnosis) as FastApiDiagnosisSummary | Record<string, unknown>;
  if (!Object.keys(diagnosis).length) return null;

  const rootCause = getRecord(diagnosis.root_cause_narrative);
  const evidenceItems = getArray(diagnosis.diagnosis_evidence_items).map(getRecord);
  const traces = getArray(diagnosis.metric_to_diagnosis_trace).map(getRecord);
  const rejected = getArray(diagnosis.rejected_alternatives).map(getRecord);
  const rationale = getArray(diagnosis.professional_rationale_refs).map(getRecord);
  const evidenceChain = stringArray(diagnosis.evidence_chain);
  const headline = firstText(rootCause.statement, diagnosis.headline, rootCause.label, diagnosis.primary_diagnosis);
  const drivers = [
    ...evidenceItems.map((item) => firstText(item.interpretation, item.why_relevant, item.signal)),
    ...evidenceChain,
    ...traces.map((trace) => firstText(trace.interpretation, trace.contribution, trace.metric_or_signal))
  ]
    .filter((item): item is string => Boolean(item))
    .map((item) => normalizeDisplaySentence(item))
    .slice(0, 5);
  const rejectedAlternatives = rejected
    .map((item) => {
      const label = firstText(item.label, item.problem_id, "Alternative diagnosis");
      const reason = firstText(item.reason, item.reason_code);
      return reason ? `${formatUnknownValue(label)}: ${normalizeDisplaySentence(reason)}` : formatUnknownValue(label);
    })
    .filter(Boolean)
    .slice(0, 5);
  const rationaleRefs = rationale
    .map((item) => firstText(item.rationale, item.reason, item.source, item.ref_id))
    .filter((item): item is string => Boolean(item))
    .map((item) => normalizeDisplaySentence(item))
    .slice(0, 5);

  return {
    status: "Diagnosis ready",
    headline: normalizeDisplaySentence(headline, "Portfolio diagnosis completed for the submitted current portfolio."),
    evidenceQuality: evidenceQualityLabel(diagnosis.confidence ?? "unknown"),
    nextStep: normalizeDisplaySentence(diagnosis.next_diagnostic_step, "Review supporting evidence before testing one candidate hypothesis."),
    boundaryNote: normalizeDisplaySentence(diagnosis.recommendation_boundary, "Diagnosis is decision-support evidence only. It is not a rebalance recommendation or trade instruction."),
    drivers: drivers.length ? drivers : ["FastAPI returned a bounded diagnosis display summary for the active review."],
    metrics: [
      {
        label: "Selected diagnosis",
        value: formatUnknownValue(rootCause.label ?? diagnosis.primary_diagnosis, "Current portfolio diagnosis"),
        detail: formatUnknownValue(diagnosis.selected_diagnosis_role ?? rootCause.diagnosis_role, "Diagnostic role"),
        tone: "blue"
      },
      {
        label: "Evidence items",
        value: String(evidenceItems.length || evidenceChain.length),
        detail: "Bounded diagnosis display evidence",
        tone: evidenceItems.length || evidenceChain.length ? "blue" : "slate"
      },
      {
        label: "Rejected alternatives",
        value: String(rejected.length),
        detail: "Alternative diagnoses considered",
        tone: rejected.length ? "amber" : "slate"
      }
    ],
    selectedDiagnosisRole: firstText(diagnosis.selected_diagnosis_role, rootCause.diagnosis_role) ? formatUnknownValue(firstText(diagnosis.selected_diagnosis_role, rootCause.diagnosis_role)) : undefined,
    sourceArtifacts: stringArray(diagnosis.source_artifacts).map((item) => formatUnknownValue(item)),
    rejectedAlternatives,
    rationaleRefs
  };
}

function buildDiagnosisFromRealResult(review: ActiveReviewState): DiagnosisState | null {
  if (isCompletedReviewResult(review.reviewResult)) {
    const fastApiDiagnosis = diagnosisFromFastApiEnvelope(fastApiEnvelopeRecord(review.reviewResult));
    if (fastApiDiagnosis) return fastApiDiagnosis;
  }
  return buildDiagnosisFromRawArtifacts(review);
}

function buildDiagnosisFromRawArtifacts(review: ActiveReviewState): DiagnosisState | null {
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
  const topHolding = getRecord(composition.top1_holding);
  const dominantAssetClass = getRecord(composition.dominant_asset_class);
  const dominantRiskFactor = getRecord(composition.dominant_main_risk_factor);
  const riskTypes = getArray(weaknessMap.risk_types)
    .map(getRecord)
    .filter((item) => typeof item.risk_title === "string")
    .sort((a, b) => (Number(b.score_0_100) || 0) - (Number(a.score_0_100) || 0));

  const primaryRisk = riskTypes[0];
  const allocationHeadline = textValue(getRecord(allocation.actual_economic_exposure_summary).headline, "");
  const xrayHeadline = primaryRisk
    ? `Current portfolio is most exposed to ${dominantExposureNameForHeadline(dominantRiskFactor, dominantAssetClass)}; the main pre-stress weakness to review is ${displayLabel(primaryRisk.risk_title ?? primaryRisk.risk_type)}.`
    : textValue(allocationHeadline, textValue(behavior.headline, "Portfolio Diagnosis completed for the submitted current portfolio."));
  const primaryRiskScore = numericValue(primaryRisk?.score_0_100);

  const drivers = [
    topHolding.ticker
      ? `${String(topHolding.ticker)} is the largest holding at ${formatRawPercent(topHolding.weight_pct)}.`
      : "Portfolio Diagnosis returned the current allocation snapshot.",
    dominantAssetClass.name
      ? `Dominant asset class: ${displayLabel(dominantAssetClass.name)} at ${formatRawPercent(dominantAssetClass.weight_pct)}.`
      : allocationHeadline || "Asset allocation diagnostics are available from Portfolio Diagnosis.",
    primaryRisk
      ? textValue(primaryRisk.short_diagnosis, `${String(primaryRisk.risk_title)} is the top pre-stress weakness.`)
      : textValue(behavior.headline, "Portfolio behavior metrics are available for review.")
  ];

  return {
    status: "Diagnosis ready",
    headline: xrayHeadline,
    evidenceQuality: evidenceQualityLabel(stressConclusions.overall_confidence ?? "Partial"),
    nextStep: "Review supporting evidence before testing one candidate hypothesis.",
    boundaryNote: "Diagnosis is based on Portfolio Diagnosis evidence for the submitted current portfolio. It frames potential weaknesses before any candidate test.",
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
        label: "Primary weakness",
        value: primaryRisk ? displayLabel(primaryRisk.risk_title ?? primaryRisk.risk_type) : "n/a",
        detail: primaryRiskScore !== null ? `Score ${primaryRiskScore}/100` : "Pre-stress signal unavailable",
        tone: toneForSeverity(primaryRisk?.severity)
      }
    ],
    sourceArtifacts: ["portfolio_xray.json", "stress_report.json"],
    rejectedAlternatives: [],
    rationaleRefs: []
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
    .map((item) => item ? formatUnknownValue(item) : item)
    .filter((item): item is string => Boolean(item))
    .slice(0, 3);

  return {
    primaryProblem: formatUnknownValue(firstText(
      primaryProblem.label_en,
      primaryProblem.problem_id,
      primaryDiagnosis.label_en,
      rootCause.label_en,
      rootCause.problem_id
    ), ""),
    problemSeverity: formatUnknownValue(firstText(primaryProblem.severity, problem.materiality), ""),
    problemConfidence: formatUnknownValue(firstText(primaryProblem.confidence, primaryDiagnosis.confidence, problem.confidence), ""),
    suggestedActionPaths: suggestedActions.length
      ? suggestedActions
      : [
        firstText(primaryProblem.suggested_action_path_id),
        ...getArray(primaryProblem.secondary_action_path_ids).filter((item): item is string => typeof item === "string" && Boolean(item.trim()))
      ].filter((item): item is string => Boolean(item)).map((item) => formatUnknownValue(item)).slice(0, 3)
  };
}

function compactProblemFieldsFromFastApi(diagnosisValue: unknown) {
  const diagnosis = getRecord(diagnosisValue);
  if (!Object.keys(diagnosis).length) return undefined;
  const rootCause = getRecord(diagnosis.root_cause_narrative);
  const suggestedAction = firstText(diagnosis.next_diagnostic_step, diagnosis.recommendation_boundary);
  return {
    primaryProblem: formatUnknownValue(firstText(
      rootCause.label,
      diagnosis.headline,
      diagnosis.primary_diagnosis
    ), ""),
    problemSeverity: formatUnknownValue(firstText(rootCause.diagnosis_role, diagnosis.selected_diagnosis_role), ""),
    problemConfidence: formatUnknownValue(firstText(diagnosis.confidence), ""),
    suggestedActionPaths: [suggestedAction]
      .filter((item): item is string => Boolean(item))
      .map((item) => normalizeDisplaySentence(item))
      .slice(0, 3)
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
    recommendedFirstTest: formatUnknownValue(firstText(
      firstCard.title,
      firstCard.goal,
      defaultMethod,
      launchpad.launchpad_outcome
    ), "")
  };
}

function compactLaunchpadCard(card: Record<string, unknown>): LaunchpadCardSummary {
  return {
    card_id: textValue(card.card_id, textValue(card.title, "launchpad_card")),
    title: formatUnknownValue(card.title, "Hypothesis test"),
    goal: firstText(card.goal) ? normalizeDisplaySentence(firstText(card.goal)) : undefined,
    hypothesis_to_test: firstText(card.hypothesis_to_test, card.what_this_tests_en) ? normalizeDisplaySentence(firstText(card.hypothesis_to_test, card.what_this_tests_en)) : undefined,
    card_type: firstText(card.card_type) ? formatUnknownValue(firstText(card.card_type)) : undefined,
    source_problem_label: firstText(card.source_problem_label) ? formatUnknownValue(firstText(card.source_problem_label)) : undefined,
    suggested_methods: getArray(card.suggested_methods).map(getRecord).slice(0, 4).map((method, index) => ({
      candidate_method_id: formatUnknownValue(method.candidate_method_id, `Method ${index + 1}`),
      method_role: firstText(method.method_role) ? formatUnknownValue(firstText(method.method_role)) : undefined,
      why_this_method: firstText(method.why_this_method) ? normalizeDisplaySentence(firstText(method.why_this_method)) : undefined
    })),
    default_method: firstText(card.default_method) ? formatUnknownValue(firstText(card.default_method)) : undefined,
    success_criteria: stringArray(card.success_criteria).slice(0, 6).map((item) => normalizeDisplaySentence(item)),
    tradeoff_to_watch: firstText(card.tradeoff_to_watch, card.expected_tradeoff_to_check_en) ? normalizeDisplaySentence(firstText(card.tradeoff_to_watch, card.expected_tradeoff_to_check_en)) : undefined,
    when_to_skip: firstText(card.when_to_skip) ? normalizeDisplaySentence(firstText(card.when_to_skip)) : undefined,
    decision_boundary: firstText(card.decision_boundary) ? normalizeDisplaySentence(firstText(card.decision_boundary)) : undefined,
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
  const parameters = getRecord(candidateSetup.parameters);
  const constraints = getRecord(candidateSetup.constraints);
  const mode = firstText(builderPrefill.mode, candidateSetup.mode, parameters.mode, constraints.mode);
  const constraintPreset = firstText(builderPrefill.constraint_preset, candidateSetup.constraint_preset, parameters.constraint_preset, constraints.constraint_preset);
  const maxAssetWeight = typeof builderPrefill.max_asset_weight === "number" || typeof builderPrefill.max_asset_weight === "string"
    ? builderPrefill.max_asset_weight
    : typeof candidateSetup.max_asset_weight === "number" || typeof candidateSetup.max_asset_weight === "string"
      ? candidateSetup.max_asset_weight
      : typeof parameters.max_asset_weight === "number" || typeof parameters.max_asset_weight === "string"
        ? parameters.max_asset_weight
        : typeof constraints.max_asset_weight === "number" || typeof constraints.max_asset_weight === "string"
          ? constraints.max_asset_weight
          : undefined;
  const minAssetWeight = typeof builderPrefill.min_asset_weight === "number" || typeof builderPrefill.min_asset_weight === "string"
    ? builderPrefill.min_asset_weight
    : typeof candidateSetup.min_asset_weight === "number" || typeof candidateSetup.min_asset_weight === "string"
      ? candidateSetup.min_asset_weight
      : typeof parameters.min_asset_weight === "number" || typeof parameters.min_asset_weight === "string"
        ? parameters.min_asset_weight
        : typeof constraints.min_asset_weight === "number" || typeof constraints.min_asset_weight === "string"
          ? constraints.min_asset_weight
          : undefined;
  return {
    selected_card_id: selectedCardId,
    can_generate_candidate: builder.can_generate_candidate === true || candidateSetup.can_generate_candidate === true,
    builder_setup_id: firstText(builder.builder_setup_id, candidateSetup.candidate_setup_id, candidateSetup.setup_id),
    builder_prefill: {
      goal: firstText(builderPrefill.goal),
      suggested_method: firstText(builderPrefill.suggested_method) ? formatUnknownValue(firstText(builderPrefill.suggested_method)) : undefined,
      mode: mode ? formatUnknownValue(mode) : undefined,
      constraint_preset: constraintPreset ? formatUnknownValue(constraintPreset) : undefined,
      max_asset_weight: maxAssetWeight,
      min_asset_weight: minAssetWeight
    },
    candidate_setup: {
      candidate_setup_id: firstText(candidateSetup.candidate_setup_id, candidateSetup.setup_id),
      validation_status: firstText(candidateSetup.validation_status) ? formatUnknownValue(firstText(candidateSetup.validation_status)) : undefined,
      can_generate_candidate: candidateSetup.can_generate_candidate === true,
      mode: mode ? formatUnknownValue(mode) : undefined,
      constraint_preset: constraintPreset ? formatUnknownValue(constraintPreset) : undefined,
      max_asset_weight: maxAssetWeight,
      min_asset_weight: minAssetWeight
    }
  };
}

const FACTOR_LABELS: Record<string, string> = {
  beta_eq: "Equity",
  beta_rr: "Interest-rate sensitivity",
  beta_inf: "Inflation",
  beta_credit: "Credit",
  beta_usd: "USD",
  beta_cmd: "Commodity",
  beta_vix: "Volatility",
  beta_us_growth: "Growth / risk assets"
};

const FACTOR_TO_BETA: Record<string, string> = {
  equity: "beta_eq",
  real_rates: "beta_rr",
  inflation: "beta_inf",
  credit: "beta_credit",
  USD: "beta_usd",
  commodity: "beta_cmd",
  VIX_volatility: "beta_vix",
  us_growth: "beta_us_growth"
};

const HIDDEN_ALERT_TITLES: Record<string, string> = {
  hidden_equity_beta: "Hidden Equity Beta",
  duration_concentration: "Duration Concentration",
  credit_liquidity_risk: "Credit / Liquidity Risk",
  correlation_concentration: "Correlation Concentration",
  weak_hedge_behavior: "Weak Hedge Behavior",
  tail_risk: "Tail Risk"
};

const HIDDEN_ALERT_ORDER = [
  "hidden_equity_beta",
  "duration_concentration",
  "credit_liquidity_risk",
  "correlation_concentration",
  "weak_hedge_behavior",
  "tail_risk"
];

const WEAKNESS_TITLES: Record<string, string> = {
  equity_shock: "Equity sell-off",
  rates_shock: "Interest-rate shock",
  inflation_stagflation: "Inflation / stagflation",
  credit_shock: "Credit shock",
  liquidity_shock: "Liquidity shock",
  usd_shock: "USD shock",
  commodity_shock: "Commodity shock",
  recession_severe: "Severe recession"
};

const WEAKNESS_ORDER = [
  "equity_shock",
  "rates_shock",
  "inflation_stagflation",
  "credit_shock",
  "liquidity_shock",
  "usd_shock",
  "commodity_shock",
  "recession_severe"
];

function compactBreakdown(title: string, value: unknown): XRayBreakdown | null {
  const items = getArray(value)
    .map(getRecord)
    .map((item) => ({
      name: textValue(item.name, ""),
      weightPct: numericValue(item.weight_pct) ?? Number.NaN
    }))
    .filter((item) => item.name && Number.isFinite(item.weightPct))
    .slice(0, 6);
  return items.length ? { title, items } : null;
}

function formatObservedPercent(value: unknown) {
  const numeric = numericValue(value);
  if (numeric === null) return "Unavailable";
  return Math.abs(numeric) <= 1 ? formatDecimalPercent(numeric) : formatRawPercent(numeric);
}

function flagLabel(flag: Record<string, unknown>) {
  const flagId = textValue(flag.flag_id, "");
  const label = displayLabel(flag.label, "");

  if (flagId === "top_holding_concentration") return "Top holding concentration";
  if (flagId === "top3_concentration") return "Top 3 concentration";
  if (flagId === "single_asset_class_dominance") return `${label || "Asset class"} concentration`;
  if (flagId === "single_main_risk_factor_dominance") return `${label || "Main risk factor"} risk factor concentration`;
  if (flagId === "single_region_dominance") return `${label || "Region"} region concentration`;
  if (flagId === "single_currency_dominance") return `${label || "Currency"} currency concentration`;
  if (flag.duplicate_group_id) return "Duplicate exposure concentration";

  return displayLabel(flag.label ?? flag.flag_id ?? flag.metric, "Concentration signal");
}

function flagMessage(flag: Record<string, unknown>) {
  const observed = flag.observed ?? flag.combined_weight_pct ?? flag.combined_weight;
  const threshold = flag.threshold;
  const observedText = formatObservedPercent(observed);
  const thresholdText = formatObservedPercent(threshold);
  const severity = displayLabel(flag.severity, "diagnostic").toLowerCase();

  if (observedText !== "Unavailable" && thresholdText !== "Unavailable") {
    return `${flagLabel(flag)}: ${observedText}. Above ${severity} diagnostic threshold of ${thresholdText}.`;
  }

  return textValue(flag.message, "Concentration evidence is available for review.");
}

function flagDedupeKey(flag: Record<string, unknown>) {
  return textValue(flag.flag_id, textValue(flag.duplicate_group_id, textValue(flag.metric, flagLabel(flag)))).toLowerCase();
}

function severityRank(value: unknown) {
  const normalized = textValue(value, "").toLowerCase();
  if (normalized.includes("high")) return 3;
  if (normalized.includes("medium") || normalized.includes("moderate")) return 2;
  if (normalized.includes("low")) return 1;
  return 0;
}

function compactFlags(...sources: unknown[]) {
  const deduped = new Map<string, XRayFlag>();

  sources
    .flatMap((source) => getArray(source).map(getRecord))
    .forEach((flag) => {
      const next = {
        label: flagLabel(flag),
        severity: displayLabel(flag.severity, "Unavailable"),
        message: flagMessage(flag)
      };
      const key = flagDedupeKey(flag);
      const current = deduped.get(key);
      if (!current || severityRank(next.severity) >= severityRank(current.severity)) {
        deduped.set(key, next);
      }
    });

  return Array.from(deduped.values()).slice(0, 6);
}

function evidenceLines(value: unknown, limit = 3) {
  return getArray(value)
    .map(getRecord)
    .map((item) => {
      const interpretation = firstText(item.interpretation, item.why_status, item.reason);
      const metric = displayLabel(item.metric, "");
      const itemValue = item.value === null || item.value === undefined
        ? ""
        : typeof item.value === "number"
          ? ` (${Math.abs(item.value) <= 1 ? formatDecimalPercent(item.value) : compactNumber(item.value)})`
          : ` (${String(item.value)})`;
      return interpretation ?? (metric ? `${metric}${itemValue}.` : "");
    })
    .filter(Boolean)
    .slice(0, limit);
}

function linkedAssetLabels(value: unknown) {
  return getArray(value)
    .map(getRecord)
    .map((asset) => {
      const ticker = textValue(asset.ticker, "");
      const weight = asset.weight_pct;
      return ticker ? `${ticker}${weight === undefined ? "" : ` ${formatFlexiblePercent(weight)}`}` : "";
    })
    .filter(Boolean)
    .slice(0, 3);
}

function holdingClassifications(holding: ReviewHolding): Omit<XRayHoldingRow, "holding" | "weightPct"> {
  const ticker = holding.ticker.toUpperCase();
  const instrument = instrumentByTicker.get(ticker);
  const terms = new Set((instrument?.searchTerms ?? []).map((term) => term.toLowerCase()));
  const sleeve = instrument?.sleeve ?? (holding.type === "cash" ? "cash" : "other");

  if (holding.type === "cash" || sleeve === "cash") {
    return {
      assetClass: "Cash",
      riskRole: "Liquidity reserve",
      mainRiskFactor: "Cash"
    };
  }

  if (sleeve === "fixed_income") {
    return {
      assetClass: "Fixed income",
      riskRole: terms.has("risk_on") || terms.has("credit") ? "Income / credit" : "Defensive",
      mainRiskFactor: terms.has("credit") ? "Credit" : "Interest-rate sensitivity"
    };
  }

  if (sleeve === "equity") {
    return {
      assetClass: "Equity",
      riskRole: "Growth / risk assets",
      mainRiskFactor: "Equity"
    };
  }

  if (sleeve === "gold" || sleeve === "commodity") {
    return {
      assetClass: "Commodity",
      riskRole: "Inflation hedge",
      mainRiskFactor: "Commodity"
    };
  }

  if (sleeve === "multi_asset") {
    return {
      assetClass: "Multi-asset",
      riskRole: terms.has("risk_on") ? "Growth / risk assets" : "Diversifier",
      mainRiskFactor: terms.has("us_growth") ? "Growth / risk assets" : "Multi-factor"
    };
  }

  return {
    assetClass: "Other",
    riskRole: "Review needed",
    mainRiskFactor: "Unavailable"
  };
}

function compactHoldingRows(holdings: ReviewHolding[]): XRayHoldingRow[] {
  return holdings
    .map((holding) => ({
      holding: holding.type === "cash" ? `Cash ${holding.currency || "USD"}` : holding.ticker.toUpperCase(),
      weightPct: holding.weight,
      ...holdingClassifications(holding)
    }))
    .sort((a, b) => b.weightPct - a.weightPct);
}

function nextTests(value: unknown) {
  return getArray(value)
    .filter((item): item is string => typeof item === "string" && Boolean(item.trim()))
    .map((item) => displayLabel(item))
    .slice(0, 3);
}

function riskContributionRow(value: unknown): XRayRiskContribution | null {
  const row = getRecord(value);
  const name = firstText(row.ticker, row.bucket, row.name);
  if (!name) return null;
  return {
    name,
    weightPct: numericValue(row.weight_pct) ?? undefined,
    riskContributionPct: numericValue(row.rc_pct ?? row.risk_contribution_pct) ?? undefined,
    gapPp: numericValue(row.weight_vs_risk_gap_pp ?? row.gap_pp) ?? undefined
  };
}

function compactRiskRows(value: unknown, limit = 5) {
  return getArray(value)
    .map(riskContributionRow)
    .filter((item): item is XRayRiskContribution => Boolean(item))
    .slice(0, limit);
}

function compactMetric(label: string, value: string, detail?: string, tone: StatusTone = "slate"): Metric {
  return { label, value, detail, tone };
}

function compactXRaySummary({
  activeReview,
  outputs
}: {
  activeReview: ActiveReviewState;
  outputs: Record<string, unknown>;
}): XRaySummary | undefined {
  const xray = getRecord(outputs.portfolio_xray);
  if (!Object.keys(xray).length) return undefined;

  const allocation = getRecord(xray.block_2_1_asset_allocation);
  const metricsBlock = getRecord(xray.block_2_2_portfolio_metrics);
  const factorsBlock = getRecord(xray.block_2_3_factor_exposure);
  const hiddenBlock = getRecord(xray.block_2_4_hidden_exposure);
  const riskBudgetBlock = getRecord(xray.block_2_5_risk_budget_view);
  const weaknessBlock = getRecord(xray.block_2_6_portfolio_weakness_map);

  const composition = getRecord(allocation.portfolio_composition_snapshot);
  const allocationBreakdown = getRecord(allocation.capital_allocation_breakdown);
  const behavior = getRecord(metricsBlock.portfolio_behavior_snapshot);
  const returnRisk = getRecord(metricsBlock.return_risk_metrics);
  const drawdown = getRecord(metricsBlock.drawdown_diagnostics);
  const tailRisk = getRecord(metricsBlock.tail_risk_diagnostics);
  const benchmark = getRecord(metricsBlock.benchmark_dependence);
  const rolling = getRecord(getRecord(metricsBlock.rolling_diagnostics).core_view);
  const metricsMetadata = getRecord(metricsBlock.metadata);
  const factorSummary = getRecord(factorsBlock.factor_exposure_summary);
  const factorBetas = getRecord(factorsBlock.factor_beta_snapshot);
  const factorSignal = getRecord(factorsBlock.factor_signal_confidence);
  const factorVariance = getRecord(getRecord(factorsBlock.factor_variance_contribution).contributions);
  const topHolding = getRecord(composition.top1_holding);
  const dominantAssetClass = getRecord(composition.dominant_asset_class);
  const dominantRiskRole = getRecord(composition.dominant_risk_role);
  const dominantRiskFactor = getRecord(composition.dominant_main_risk_factor);
  const dominantRegion = getRecord(composition.dominant_region);
  const dominantCurrency = getRecord(composition.dominant_currency);
  const topRiskContributor = riskContributionRow(riskBudgetBlock.top1_rc_asset);
  const riskTypes = getArray(weaknessBlock.risk_types).map(getRecord);
  const primaryWeakness = [...riskTypes]
    .filter((risk) => textValue(risk.risk_type, ""))
    .sort((a, b) => (numericValue(b.score_0_100) ?? -1) - (numericValue(a.score_0_100) ?? -1))[0];

  const holdingsCount = numericValue(composition.total_holdings) ?? activeReview.reviewSummary?.holdingsCount ?? activeReview.holdings.length;
  const top3Weight = numericValue(composition.top3_weight_pct);
  const dominantExposure = textValue(dominantRiskFactor.name, textValue(dominantAssetClass.name, "Unavailable"));
  const dominantExposureWeight = dominantRiskFactor.weight_pct ?? dominantAssetClass.weight_pct;
  const dominantRiskFactorMetric = numericValue(dominantExposureWeight);
  const primaryWeaknessScore = numericValue(primaryWeakness?.score_0_100);

  const snapshotCards = [
    compactMetric("Total holdings", String(holdingsCount), "Current portfolio review", "blue"),
    compactMetric(
      "Top holding",
      topHolding.ticker ? `${textValue(topHolding.ticker)} ${formatRawPercent(topHolding.weight_pct)}` : "n/a",
      "Largest capital position",
      numericValue(topHolding.weight_pct) !== null && (numericValue(topHolding.weight_pct) ?? 0) >= 30 ? "red" : numericValue(topHolding.weight_pct) !== null && (numericValue(topHolding.weight_pct) ?? 0) >= 20 ? "amber" : "blue"
    ),
    compactMetric(
      "Top 3 concentration",
      top3Weight !== null ? formatRawPercent(top3Weight) : "n/a",
      "Capital in largest three holdings",
      top3Weight !== null && top3Weight >= 65 ? "red" : top3Weight !== null && top3Weight >= 50 ? "amber" : "blue"
    ),
    compactMetric(
      "Dominant exposure",
      displayLabel(dominantExposure),
      formatFlexiblePercent(dominantExposureWeight),
      dominantRiskFactorMetric !== null && dominantRiskFactorMetric >= 50 ? "amber" : "blue"
    ),
    compactMetric(
      "Max drawdown",
      formatDecimalPercent(drawdown.max_drawdown),
      textValue(behavior.overall_behavior_label, "Portfolio behavior"),
      toneForLoss(drawdown.max_drawdown)
    ),
    compactMetric(
      "Worst pre-stress weakness",
      primaryWeakness ? displayLabel(primaryWeakness.risk_title ?? primaryWeakness.risk_type) : "n/a",
      primaryWeaknessScore !== null ? `Score ${primaryWeaknessScore}/100` : "Insufficient evidence",
      toneForSeverity(primaryWeakness?.severity)
    )
  ];

  const breakdowns = [
    compactBreakdown("Asset class", allocationBreakdown.by_asset_class),
    compactBreakdown("Main risk factor", allocationBreakdown.by_main_risk_factor),
    compactBreakdown("Risk role", allocationBreakdown.by_risk_role),
    compactBreakdown("Region", allocationBreakdown.by_region),
    compactBreakdown("Currency", allocationBreakdown.by_currency)
  ].filter((item): item is XRayBreakdown => Boolean(item));

  const compositionKeyFacts = [
    `Top holding: ${topHolding.ticker ? `${textValue(topHolding.ticker)} at ${formatRawPercent(topHolding.weight_pct)}` : "unavailable"}.`,
    `Top 3 concentration: ${top3Weight !== null ? formatRawPercent(top3Weight) : "unavailable"}.`,
    `Dominant asset class: ${dominantAssetClass.name ? `${displayLabel(dominantAssetClass.name)} at ${formatFlexiblePercent(dominantAssetClass.weight_pct)}` : "unavailable"}.`,
    `Dominant risk role: ${dominantRiskRole.name ? `${displayLabel(dominantRiskRole.name)} at ${formatFlexiblePercent(dominantRiskRole.weight_pct)}` : "unavailable"}.`,
    `Dominant region / currency: ${dominantRegion.name ? `${displayLabel(dominantRegion.name)} ${formatFlexiblePercent(dominantRegion.weight_pct)}` : "region unavailable"}; ${dominantCurrency.name ? `${displayLabel(dominantCurrency.name)} ${formatFlexiblePercent(dominantCurrency.weight_pct)}` : "currency unavailable"}.`
  ];

  const rollingFacts = [
    getRecord(rolling.rolling_volatility_12m).latest !== undefined
      ? `Latest rolling volatility: ${formatDecimalPercent(getRecord(rolling.rolling_volatility_12m).latest)}.`
      : "",
    getRecord(rolling.rolling_sharpe_36m).latest !== undefined
      ? `Latest rolling Sharpe: ${compactNumber(getRecord(rolling.rolling_sharpe_36m).latest)}.`
      : "",
    getRecord(rolling.rolling_beta_or_correlation).latest_beta !== undefined
      ? `Latest rolling beta: ${compactNumber(getRecord(rolling.rolling_beta_or_correlation).latest_beta)}.`
      : ""
  ].filter(Boolean);

  const riskProfileFacts = [
    `Realized CAGR ${formatDecimalPercent(returnRisk.portfolio_cagr)} with annualized volatility ${formatDecimalPercent(returnRisk.vol_annual)} over the primary window.`,
    `Sharpe ratio ${compactNumber(returnRisk.sharpe)}; Sortino ${compactNumber(returnRisk.sortino)}.`,
    `Maximum drawdown ${formatDecimalPercent(drawdown.max_drawdown)}${drawdown.recovered === true ? "; deepest episode recovered within sample" : ""}.`,
    ...rollingFacts
  ].filter((fact) => !fact.includes("n/a")).slice(0, 5);

  const riskMetrics = [
    compactMetric("CAGR", formatDecimalPercent(returnRisk.portfolio_cagr), "Primary diagnostic window", "blue"),
    compactMetric("Annual volatility", formatDecimalPercent(returnRisk.vol_annual), "Realized portfolio volatility", "blue"),
    ...(numericValue(metricsMetadata.vol_of_vol) !== null
      ? [compactMetric("Vol of vol", formatDecimalPercent(metricsMetadata.vol_of_vol), "Rolling volatility stability", "slate")]
      : []),
    compactMetric("Max drawdown", formatDecimalPercent(drawdown.max_drawdown), drawdown.recovered === true ? "Deepest episode recovered within sample" : "Recovery evidence unavailable", toneForLoss(drawdown.max_drawdown)),
    ...(numericValue(drawdown.ttr_months) !== null
      ? [compactMetric("Time to recovery", `${compactNumber(drawdown.ttr_months)} months`, drawdown.recovered === true ? "Recovered within sample" : "Recovery not observed", "slate")]
      : []),
    ...(numericValue(drawdown.pct_time_underwater) !== null
      ? [compactMetric("Time underwater", formatDecimalPercent(drawdown.pct_time_underwater), "Share of diagnostic window below prior high", "slate")]
      : []),
    ...(numericValue(drawdown.count_drawdowns_gt_10) !== null
      ? [compactMetric("Drawdowns >10%", String(drawdown.count_drawdowns_gt_10), "Count in diagnostic window", "slate")]
      : []),
    compactMetric("VaR 95", formatDecimalPercent(tailRisk.var_95), "Daily historical tail metric", toneForLoss(tailRisk.var_95)),
    compactMetric("ES 95", formatDecimalPercent(tailRisk.es_95), "Daily historical expected shortfall", toneForLoss(tailRisk.es_95)),
    ...(numericValue(returnRisk.skewness) !== null
      ? [compactMetric("Skewness", compactNumber(returnRisk.skewness), "Return asymmetry", "slate")]
      : []),
    ...(numericValue(returnRisk.kurtosis) !== null
      ? [compactMetric("Kurtosis", compactNumber(returnRisk.kurtosis), "Tail thickness", "slate")]
      : []),
    compactMetric("Beta", compactNumber(benchmark.beta_portfolio), textValue(benchmark.benchmark_ticker, "Benchmark dependence"), numericValue(benchmark.beta_portfolio) !== null && (numericValue(benchmark.beta_portfolio) ?? 0) >= 0.9 ? "amber" : "blue"),
    compactMetric("Downside beta", compactNumber(benchmark.downside_beta), "Sensitivity in down markets", numericValue(benchmark.downside_beta) !== null && (numericValue(benchmark.downside_beta) ?? 0) >= 0.9 ? "amber" : "blue"),
    ...(numericValue(benchmark.upside_beta) !== null
      ? [compactMetric("Upside beta", compactNumber(benchmark.upside_beta), "Sensitivity in up markets", "slate")]
      : []),
    ...(numericValue(benchmark.corr_base) !== null
      ? [compactMetric("Benchmark correlation", compactNumber(benchmark.corr_base), textValue(benchmark.benchmark_ticker, "Benchmark"), "slate")]
      : []),
    compactMetric("Sharpe", compactNumber(returnRisk.sharpe), "Total-volatility efficiency", "blue"),
    compactMetric("Sortino", compactNumber(returnRisk.sortino), "Downside-adjusted efficiency", "blue"),
    ...(numericValue(returnRisk.treynor) !== null
      ? [compactMetric("Treynor", compactNumber(returnRisk.treynor), "Beta-adjusted efficiency", "slate")]
      : [])
  ].filter((metric) => metric.value !== "n/a");

  const factorCards = Object.entries(FACTOR_LABELS).map(([betaName, factor]) => {
    const confidenceRecord = getRecord(factorSignal[betaName]);
    const factorKey = Object.entries(FACTOR_TO_BETA).find(([, beta]) => beta === betaName)?.[0];
    return {
      factor,
      beta: numericValue(factorBetas[betaName]) ?? undefined,
      contributionPct: factorKey ? numericValue(factorVariance[factorKey]) ?? undefined : undefined,
      confidence: displayLabel(confidenceRecord.signal_confidence ?? confidenceRecord.status, numericValue(factorBetas[betaName]) === null ? "Unavailable" : "Visible"),
      interpretation: textValue(confidenceRecord.confidence_reason, `${factor} factor sensitivity ${numericValue(factorBetas[betaName]) === null ? "is unavailable" : "is visible"} in the current evidence.`)
    };
  });

  const rankedFactors = getArray(factorsBlock.factor_risk_ranking)
    .map(getRecord)
    .map((item) => ({
      factor: displayLabel(item.factor, "Factor"),
      beta: numericValue(item.beta) ?? undefined,
      contributionPct: numericValue(item.contribution) ?? undefined,
      confidence: displayLabel(item.confidence, "Evidence"),
      interpretation: textValue(item.interpretation, "Factor sensitivity is visible in the current evidence.")
    }))
    .filter((item) => item.factor)
    .slice(0, 3);

  const hiddenAlerts: XRayHiddenRiskAlert[] = HIDDEN_ALERT_ORDER.map((id): XRayHiddenRiskAlert | null => {
    const alert = getRecord(getRecord(hiddenBlock.alerts)[id]);
    if (!Object.keys(alert).length) {
      return null;
    }
    return {
      id,
      title: HIDDEN_ALERT_TITLES[id],
      level: displayLabel(alert.status, "Unavailable"),
      score: numericValue(alert.score) ?? undefined,
      diagnosis: textValue(alert.explanation, textValue(alert.why_it_matters, "Hidden risk signal is present.")),
      evidence: evidenceLines(alert.evidence, 3),
      linkedAssets: linkedAssetLabels(alert.contributing_assets ?? alert.linked_assets),
      nextTests: nextTests(alert.next_tests),
      confidence: displayLabel(alert.confidence, "Evidence")
    };
  }).filter((alert): alert is XRayHiddenRiskAlert => Boolean(alert));

  const weaknessById = new Map(riskTypes.map((risk) => [textValue(risk.risk_type, ""), risk]));
  const weaknessTiles: XRayWeaknessTile[] = WEAKNESS_ORDER.map((id): XRayWeaknessTile | null => {
    const risk = weaknessById.get(id);
    if (!risk) {
      return null;
    }
    return {
      id,
      title: WEAKNESS_TITLES[id],
      severity: displayLabel(risk.severity, "Unavailable"),
      score: numericValue(risk.score_0_100) ?? undefined,
      diagnosis: textValue(risk.short_diagnosis, textValue(risk.why_status, "Potential weakness signal is present.")),
      evidence: stringArray(risk.key_evidence).slice(0, 3).length
        ? stringArray(risk.key_evidence).slice(0, 3)
        : evidenceLines(risk.evidence, 3),
      linkedAssets: linkedAssetLabels(risk.linked_assets),
      nextTests: nextTests(risk.next_tests),
      confidence: displayLabel(risk.confidence, "Evidence")
    };
  }).filter((tile): tile is XRayWeaknessTile => Boolean(tile));

  const unavailableNotes = [
    ...stringArray(allocation.data_quality_warnings),
    ...stringArray(metricsBlock.data_quality_warnings),
    ...stringArray(factorsBlock.data_quality_warnings),
    ...stringArray(hiddenBlock.data_quality_warnings),
    ...stringArray(riskBudgetBlock.data_quality_warnings),
    ...stringArray(weaknessBlock.data_quality_warnings)
  ].slice(0, 4);

  return {
    snapshotCards,
    composition: {
      insight: textValue(getRecord(allocation.actual_economic_exposure_summary).headline, "Portfolio composition evidence is available for the submitted current portfolio."),
      keyFacts: compositionKeyFacts,
      breakdowns,
      flags: compactFlags(allocation.concentration_flags, allocation.duplicate_exposure_flags),
      holdings: compactHoldingRows(activeReview.holdings)
    },
    riskProfile: {
      insight: numericValue(returnRisk.portfolio_cagr) !== null || numericValue(drawdown.max_drawdown) !== null
        ? `The portfolio delivered ${formatDecimalPercent(returnRisk.portfolio_cagr)} CAGR with a ${formatDecimalPercent(drawdown.max_drawdown)} maximum drawdown over the primary diagnostic window.`
        : textValue(behavior.headline, "Risk profile evidence is available for the submitted current portfolio."),
      metrics: riskMetrics,
      keyFacts: riskProfileFacts.length ? riskProfileFacts : stringArray(behavior.key_points).slice(0, 5)
    },
    factors: {
      insight: textValue(factorSummary.diagnostic_interpretation, textValue(factorSummary.client_summary, "Factor sensitivity evidence is available when factor data is sufficient.")),
      topFactors: rankedFactors.length ? rankedFactors : factorCards.filter((factor) => factor.beta !== undefined).slice(0, 3),
      factorCards,
      caveat: firstText(factorSummary.main_caveat)
    },
    hiddenRisks: {
      insight: textValue(hiddenBlock.summary, "Hidden risk alerts are preliminary diagnosis signals before stress confirmation."),
      alerts: hiddenAlerts
    },
    riskBudget: {
      insight: textValue(riskBudgetBlock.summary, "Risk budget evidence shows which assets contribute more or less risk than their capital weight."),
      topContributor: topRiskContributor ?? undefined,
      top3Share: numericValue(riskBudgetBlock.top3_rc_share) ?? undefined,
      contributors: compactRiskRows(riskBudgetBlock.top3_rc_assets, 3),
      riskOverweight: compactRiskRows(riskBudgetBlock.top_risk_overweight_assets, 3),
      riskUnderweight: compactRiskRows(riskBudgetBlock.top_risk_underweight_assets, 3),
      buckets: compactRiskRows(riskBudgetBlock.risk_budget_bucket_contribution, 5)
    },
    weaknessMap: {
      insight: textValue(weaknessBlock.summary, "Portfolio Weakness Map is a pre-stress hypothesis map, not scenario P&L."),
      tiles: weaknessTiles
    },
    unavailableNotes
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
      type: "Diagnosis",
      title: "Portfolio composition",
      status: `${holdingsCount} holdings`,
      summary: topHolding.ticker
        ? `Largest holding is ${textValue(topHolding.ticker)} at ${formatRawPercent(topHolding.weight_pct)}.`
        : "Portfolio composition was returned for the current portfolio.",
      source: "Portfolio Diagnosis",
      tone: "blue"
    },
    {
      type: "Diagnosis",
      title: "Dominant exposure",
      status: `${dominantExposureName} · ${dominantExposureWeight}`,
      summary: `The current portfolio is most exposed to ${dominantExposureName}.`,
      source: "Portfolio Diagnosis",
      tone: numericValue(dominantRiskFactor.weight_pct ?? dominantAssetClass.weight_pct) !== null && (numericValue(dominantRiskFactor.weight_pct ?? dominantAssetClass.weight_pct) ?? 0) >= 50 ? "amber" : "blue"
    },
    {
      type: "Diagnosis",
      title: "Top risk contributors",
      status: topRiskContributor.ticker ? `${textValue(topRiskContributor.ticker)} leads risk` : "Not available",
      summary: riskContributorText,
      source: "Portfolio Diagnosis",
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
      type: "Diagnosis",
      title: "Primary weakness",
      status: `${textValue(riskTypes[0].severity, "Risk")} · score ${textValue(String(riskTypes[0].score_0_100 ?? "n/a"))}`,
      summary: textValue(riskTypes[0].short_diagnosis, textValue(riskTypes[0].risk_title, "Primary weakness returned by Portfolio Diagnosis.")),
      source: "Portfolio Diagnosis",
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
    quality: evidenceQualityLabel(stressConclusions.overall_confidence ?? "partial"),
    boundaryNote: "Evidence is diagnostic and comes from Portfolio Diagnosis plus Stress Test Lab for the submitted current portfolio.",
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
        detail: "Portfolio Diagnosis drawdown",
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
    evidenceQuality: "Moderate evidence",
    nextStep: "Review supporting evidence before testing one candidate hypothesis.",
    boundaryNote: "Compact summary is available; the full evidence package is not stored in browser storage.",
    drivers: ["Review completed for the submitted portfolio."],
    metrics: [],
    sourceArtifacts: [],
    rejectedAlternatives: [],
    rationaleRefs: []
  };

  const outputs = getRecord(reviewResult.outputs);
  const fastApiData = fastApiDataRecord(reviewResult);
  const problemClassification = outputs.problem_classification;
  const candidateLaunchpad = outputs.candidate_launchpad;
  const portfolioAlternativesBuilder = outputs.portfolio_alternatives_builder;
  const siteExplanation = cleanSiteExplanationBundle(outputs.site_explanation_bundle);
  const compactProblem = compactProblemFieldsFromFastApi(fastApiData.diagnosis) ?? compactProblemFields(problemClassification);
  const compactLaunchpad = compactLaunchpadFields(candidateLaunchpad);
  const clientFit = cleanClientFitDisplaySummary(fastApiData.client_fit);
  const rawBytes = estimateJsonBytes(reviewResult);
  const activeReviewForCompaction: ActiveReviewState = {
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
  };
  const xraySummary = compactXRaySummary({
    activeReview: activeReviewForCompaction,
    outputs
  });
  const evidence = compactEvidenceFields({
    activeReview: activeReviewForCompaction,
    outputs
  });
  const stressLabModel = buildStressLabModelFromOutputs(outputs);
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
    xraySummary,
    evidence,
    clientFit,
    stressLabModel: stressLabModel ?? undefined,
    siteExplanation,
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
      rawAccessStrategy: "Use reviewId for future retrieval; browser storage keeps only compact summaries."
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
    evidenceQuality: "Limited evidence",
    nextStep: "Review evidence before testing any candidate hypothesis.",
    boundaryNote: "Diagnosis reflects the portfolio currently entered on the input screen.",
    drivers,
    metrics: [
      { label: "Equity sleeve", value: formatPercent(equityWeight), detail: equityLabels.length ? equityLabels.join(" + ") : "No equity sleeve", tone: metricTone(equityWeight, 50) },
      { label: "Fixed income", value: formatPercent(fixedIncomeWeight), detail: fixedIncomeLabels.length ? fixedIncomeLabels.join(" + ") : "No bond sleeve", tone: metricTone(fixedIncomeWeight, 35) },
      { label: "Liquidity sleeve", value: formatPercent(cashWeight), detail: cashDetail, tone: cashWeight > 0 ? "blue" : "slate" }
    ],
    sourceArtifacts: [],
    rejectedAlternatives: [],
    rationaleRefs: []
  };
}
