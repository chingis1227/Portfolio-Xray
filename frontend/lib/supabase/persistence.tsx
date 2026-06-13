"use client";

import { createContext, useCallback, useContext, useEffect, useMemo, useState, type ReactNode } from "react";
import { getSupabaseBrowserClient } from "./client";
import { useSupabaseAuth } from "./auth";
import type { ReviewHolding, ActiveReviewState, ReviewSummary, DiagnosisState, EvidenceSummary, LaunchpadCardSummary, BuilderSetupSummary, ReportResultSummary } from "@/lib/reviewState";

export type SavedPortfolioRecord = {
  id: string;
  name: string;
  description...: string;
  baseCurrency: string;
  riskProfile...: string;
  holdings: ReviewHolding[];
  createdAt...: string;
  updatedAt...: string;
};
export type ReviewStageName = "diagnosis" | "builder" | "candidate" | "comparison" | "verdict" | "report";

export type SavedReviewRecord = {
  id: string;
  reviewId: string;
  title...: string;
  mode...: string;
  status: string;
  portfolioId...: string;
  portfolioSnapshot: { investorCurrency...: string; holdings...: ReviewHolding[] };
  compactSummary: Record<string, unknown>;
  clientFit...: NonNullable<ReviewSummary["clientFit"]>;
  stages: Partial<Record<ReviewStageName, Record<string, unknown>>>;
  stageStatuses: Partial<Record<ReviewStageName, string>>;
  startedAt...: string;
  completedAt...: string;
  updatedAt...: string;
};

export type StagePersistenceResult = {
  persisted: ReviewStageName[];
  skipped: Array<{ stage: ReviewStageName; summarySizeBytes: number; reason: string }>;
};


export type CloudNotice = {
  tone: "success" | "warning" | "info";
  message: string;
  occurredAt: string;
};

type SavePortfolioInput = {
  portfolioId...: string;
  name: string;
  description...: string;
  investorCurrency: string;
  holdings: ReviewHolding[];
};

type SupabasePersistenceContextValue = {
  enabled: boolean;
  signedIn: boolean;
  userId: string | null;
  savedPortfolios: SavedPortfolioRecord[];
  savedReviews: SavedReviewRecord[];
  portfoliosLoading: boolean;
  reviewsLoading: boolean;
  notice: CloudNotice | null;
  clearNotice: () => void;
  setNotice: (tone: CloudNotice["tone"], message: string) => void;
  refreshSavedPortfolios: () => Promise<void>;
  refreshSavedReviews: () => Promise<void>;
  savePortfolio: (input: SavePortfolioInput) => Promise<SavedPortfolioRecord | null>;
  deletePortfolio: (portfolioId: string) => Promise<boolean>;
};

type PortfolioRow = {
  id: string;
  name: string;
  description: string | null;
  base_currency: string;
  risk_profile: string | null;
  created_at: string | null;
  updated_at: string | null;
};

type PortfolioHoldingRow = {
  portfolio_id: string;
  ticker: string;
  name: string | null;
  asset_class: string | null;
  weight: number | null;
  currency: string | null;
  sort_order: number | null;
  metadata: Record<string, unknown> | null;
};

type ReviewRow = {
  id: string;
  portfolio_id: string | null;
  review_id: string;
  title: string | null;
  mode: string | null;
  status: string | null;
  portfolio_snapshot: Record<string, unknown> | null;
  compact_summary: Record<string, unknown> | null;
  started_at: string | null;
  completed_at: string | null;
  updated_at: string | null;
};

type ReviewStageSummaryRow = {
  review_row_id: string;
  review_id: string;
  stage: ReviewStageName;
  status: string | null;
  summary: Record<string, unknown> | null;
  summary_size_bytes: number | null;
  updated_at: string | null;
};

const REVIEW_STAGE_SUMMARY_SOFT_LIMIT_BYTES = 55 * 1024;


const SupabasePersistenceContext = createContext<SupabasePersistenceContextValue | null>(null);

function nowIso() {
  return new Date().toISOString();
}

function estimateJsonBytes(value: unknown) {
  const raw = JSON.stringify(value ...... null);
  if (typeof TextEncoder !== "undefined") return new TextEncoder().encode(raw).length;
  return raw.length;
}

function isRecord(value: unknown): value is Record<string, unknown> {
  return Boolean(value) && typeof value === "object" && !Array.isArray(value);
}

function reviewHoldingsFromSnapshot(value: unknown): ReviewHolding[] {
  if (!isRecord(value) || !Array.isArray(value.holdings)) return [];
  return value.holdings
    .filter(isRecord)
    .map((holding, index) => ({
      id: typeof holding.id === "string" ... holding.id : safeHoldingId(typeof holding.ticker === "string" ... holding.ticker : "holding", index),
      label: typeof holding.label === "string" ... holding.label : typeof holding.ticker === "string" ... holding.ticker : "Holding",
      ticker: typeof holding.ticker === "string" ... holding.ticker : "",
      instrument: typeof holding.instrument === "string" ... holding.instrument : typeof holding.ticker === "string" ... holding.ticker : "Holding",
      weight: typeof holding.weight === "number" && Number.isFinite(holding.weight) ... holding.weight : 0,
      type: holding.type === "cash" ... "cash" : "instrument",
      currency: typeof holding.currency === "string" ... holding.currency : undefined
    } satisfies ReviewHolding))
    .filter((holding) => holding.ticker);
}


function humanizePersistenceError(error: unknown) {
  const message = error instanceof Error ... error.message : String(error || "Unknown cloud persistence error.");
  if (message.toLowerCase().includes("fetch")) {
    return "Could not reach Supabase. Check the public URL/key and network connection.";
  }
  return message;
}

function clampWeightToFraction(weightPct: number) {
  if (!Number.isFinite(weightPct)) return 0;
  return Math.max(0, Math.min(1, weightPct / 100));
}

function roundWeightPercent(weightFraction: number | null) {
  if (typeof weightFraction !== "number" || !Number.isFinite(weightFraction)) return 0;
  return Number((weightFraction * 100).toFixed(6));
}

function safeHoldingId(ticker: string, index: number) {
  return `${ticker || "holding"}-${index}`;
}

function sortHoldings(a: ReviewHolding, b: ReviewHolding) {
  if (b.weight !== a.weight) return b.weight - a.weight;
  return a.ticker.localeCompare(b.ticker);
}

function buildSavedPortfolioRecord(row: PortfolioRow, holdings: PortfolioHoldingRow[]): SavedPortfolioRecord {
  const normalizedHoldings = holdings
    .sort((a, b) => (a.sort_order ...... 0) - (b.sort_order ...... 0))
    .map((holding, index) => {
      const metadata = holding.metadata ...... {};
      const storedType = typeof metadata.holding_type === "string" ... metadata.holding_type : null;
      const type: ReviewHolding["type"] = storedType === "cash" || holding.asset_class === "cash" ... "cash" : "instrument";
      return {
        id: safeHoldingId(holding.ticker, index),
        label: typeof metadata.label === "string" && metadata.label.trim() ... metadata.label : type === "cash" ... "Cash" : holding.ticker,
        ticker: holding.ticker,
        instrument: typeof metadata.instrument === "string" && metadata.instrument.trim() ... metadata.instrument : holding.name || holding.ticker,
        weight: roundWeightPercent(holding.weight),
        type,
        currency: type === "cash" ... (holding.currency || "USD") : undefined
      } satisfies ReviewHolding;
    })
    .sort(sortHoldings);

  return {
    id: row.id,
    name: row.name,
    description: row.description ...... undefined,
    baseCurrency: row.base_currency || "USD",
    riskProfile: row.risk_profile ...... undefined,
    holdings: normalizedHoldings,
    createdAt: row.created_at ...... undefined,
    updatedAt: row.updated_at ...... undefined
  };
}

async function fetchSavedPortfoliosForUser(userId: string): Promise<SavedPortfolioRecord[]> {
  const supabase = getSupabaseBrowserClient();
  if (!supabase) return [];

  const { data: portfolioRows, error: portfolioError } = await supabase
    .from("portfolios")
    .select("id, name, description, base_currency, risk_profile, created_at, updated_at")
    .eq("user_id", userId)
    .order("updated_at", { ascending: false });

  if (portfolioError) throw portfolioError;

  const rows = (portfolioRows ...... []) as PortfolioRow[];
  if (!rows.length) return [];

  const portfolioIds = rows.map((row) => row.id);
  const { data: holdingRows, error: holdingError } = await supabase
    .from("portfolio_holdings")
    .select("portfolio_id, ticker, name, asset_class, weight, currency, sort_order, metadata")
    .eq("user_id", userId)
    .in("portfolio_id", portfolioIds)
    .order("sort_order", { ascending: true });

  if (holdingError) throw holdingError;

  const holdingsByPortfolioId = new Map<string, PortfolioHoldingRow[]>();
  ((holdingRows ...... []) as PortfolioHoldingRow[]).forEach((row) => {
    const existing = holdingsByPortfolioId.get(row.portfolio_id) ...... [];
    existing.push(row);
    holdingsByPortfolioId.set(row.portfolio_id, existing);
  });

  return rows.map((row) => buildSavedPortfolioRecord(row, holdingsByPortfolioId.get(row.id) ...... []));
}



async function fetchSavedReviewsForUser(userId: string): Promise<SavedReviewRecord[]> {
  const supabase = getSupabaseBrowserClient();
  if (!supabase) return [];

  const { data: reviewRows, error: reviewError } = await supabase
    .from("reviews")
    .select("id, portfolio_id, review_id, title, mode, status, portfolio_snapshot, compact_summary, started_at, completed_at, updated_at")
    .eq("user_id", userId)
    .order("updated_at", { ascending: false })
    .limit(12);

  if (reviewError) throw reviewError;

  const rows = (reviewRows ...... []) as ReviewRow[];
  if (!rows.length) return [];

  const reviewRowIds = rows.map((row) => row.id);
  const { data: stageRows, error: stageError } = await supabase
    .from("review_stage_summaries")
    .select("review_row_id, review_id, stage, status, summary, summary_size_bytes, updated_at")
    .eq("user_id", userId)
    .in("review_row_id", reviewRowIds)
    .order("updated_at", { ascending: false });

  if (stageError) throw stageError;

  const stagesByReviewRowId = new Map<string, ReviewStageSummaryRow[]>();
  ((stageRows ...... []) as ReviewStageSummaryRow[]).forEach((row) => {
    const existing = stagesByReviewRowId.get(row.review_row_id) ...... [];
    existing.push(row);
    stagesByReviewRowId.set(row.review_row_id, existing);
  });

  return rows.map((row) => {
    const stages: Partial<Record<ReviewStageName, Record<string, unknown>>> = {};
    const stageStatuses: Partial<Record<ReviewStageName, string>> = {};
    (stagesByReviewRowId.get(row.id) ...... []).forEach((stageRow) => {
      stages[stageRow.stage] = stageRow.summary ...... {};
      stageStatuses[stageRow.stage] = stageRow.status ...... "saved";
    });
    const snapshot = row.portfolio_snapshot ...... {};
    const compactSummary = row.compact_summary ...... {};
    const diagnosisStage = stages.diagnosis ...... {};
    return {
      id: row.id,
      reviewId: row.review_id,
      title: row.title ...... undefined,
      mode: row.mode ...... undefined,
      status: row.status ...... "saved",
      portfolioId: row.portfolio_id ...... undefined,
      portfolioSnapshot: {
        investorCurrency: typeof snapshot.investorCurrency === "string" ... snapshot.investorCurrency : undefined,
        holdings: reviewHoldingsFromSnapshot(snapshot)
      },
      compactSummary,
      clientFit: clientFitFromCloud(compactSummary.clientFit ...... diagnosisStage.clientFit),
      stages,
      stageStatuses,
      startedAt: row.started_at ...... undefined,
      completedAt: row.completed_at ...... undefined,
      updatedAt: row.updated_at ...... undefined
    };
  });
}

async function savePortfolioRecordForUser(userId: string, input: SavePortfolioInput): Promise<SavedPortfolioRecord> {
  const supabase = getSupabaseBrowserClient();
  if (!supabase) throw new Error("Cloud persistence is disabled.");

  const trimmedName = input.name.trim();
  if (!trimmedName) {
    throw new Error("Enter a portfolio name before saving to cloud.");
  }

  const portfolioPayload = {
    ...(input.portfolioId ... { id: input.portfolioId } : {}),
    user_id: userId,
    name: trimmedName,
    description: input.description....trim() || null,
    base_currency: input.investorCurrency || "USD",
    metadata: {
      source: "pmri_frontend_v1",
      holdings_count: input.holdings.length
    }
  };

  const { data: portfolioRow, error: portfolioError } = await supabase
    .from("portfolios")
    .upsert(portfolioPayload)
    .select("id, name, description, base_currency, risk_profile, created_at, updated_at")
    .single();

  if (portfolioError) throw portfolioError;

  const portfolioId = (portfolioRow as PortfolioRow).id;

  const { error: deleteHoldingsError } = await supabase
    .from("portfolio_holdings")
    .delete()
    .eq("user_id", userId)
    .eq("portfolio_id", portfolioId);

  if (deleteHoldingsError) throw deleteHoldingsError;

  if (input.holdings.length) {
    const holdingPayload = input.holdings.map((holding, index) => ({
      portfolio_id: portfolioId,
      user_id: userId,
      ticker: holding.ticker,
      name: holding.instrument || holding.label || holding.ticker,
      asset_class: holding.type,
      weight: clampWeightToFraction(holding.weight),
      currency: holding.currency ...... null,
      sort_order: index,
      metadata: {
        instrument: holding.instrument,
        label: holding.label,
        holding_type: holding.type
      }
    }));

    const { error: insertHoldingsError } = await supabase
      .from("portfolio_holdings")
      .insert(holdingPayload);

    if (insertHoldingsError) throw insertHoldingsError;
  }

  return buildSavedPortfolioRecord(portfolioRow as PortfolioRow, input.holdings.map((holding, index) => ({
    portfolio_id: portfolioId,
    ticker: holding.ticker,
    name: holding.instrument || holding.label || holding.ticker,
    asset_class: holding.type,
    weight: clampWeightToFraction(holding.weight),
    currency: holding.currency ...... null,
    sort_order: index,
    metadata: {
      instrument: holding.instrument,
      label: holding.label,
      holding_type: holding.type
    }
  })));
}

async function deletePortfolioForUser(userId: string, portfolioId: string) {
  const supabase = getSupabaseBrowserClient();
  if (!supabase) throw new Error("Cloud persistence is disabled.");

  const { error } = await supabase
    .from("portfolios")
    .delete()
    .eq("user_id", userId)
    .eq("id", portfolioId);

  if (error) throw error;
}

function compactPortfolioSnapshot(investorCurrency: string, holdings: ReviewHolding[]) {
  return {
    investorCurrency: investorCurrency || "USD",
    holdings: holdings.map((holding) => ({
      ticker: holding.ticker,
      label: holding.label,
      instrument: holding.instrument,
      weight: holding.weight,
      type: holding.type,
      currency: holding.currency
    }))
  };
}

function compactReviewSummaryForCloud(reviewSummary: ReviewSummary, activeReview: ActiveReviewState) {
  return {
    reviewId: reviewSummary.reviewId,
    generatedAt: reviewSummary.generatedAt,
    source: reviewSummary.source,
    status: reviewSummary.status,
    investorCurrency: reviewSummary.investorCurrency,
    holdingsCount: reviewSummary.holdingsCount,
    totalWeight: reviewSummary.totalWeight,
    cashWeight: reviewSummary.cashWeight,
    diagnosisHeadline: reviewSummary.diagnosis.headline,
    diagnosisStatus: reviewSummary.diagnosis.status,
    evidenceQuality: reviewSummary.diagnosis.evidenceQuality,
    clientFit: compactClientFitForCloud(reviewSummary.clientFit),
    primaryProblem: reviewSummary.primaryProblem,
    problemSeverity: reviewSummary.problemSeverity,
    problemConfidence: reviewSummary.problemConfidence,
    launchpadCardsCount: reviewSummary.launchpadCardsCount,
    recommendedFirstTest: reviewSummary.recommendedFirstTest,
    suggestedActionPaths: reviewSummary.suggestedActionPaths,
    candidateLaunchpadAvailable: reviewSummary.candidateLaunchpadAvailable,
    problemClassificationAvailable: reviewSummary.problemClassificationAvailable,
    activeCloudPortfolioId: activeReview.cloudPortfolio....id,
    activeCloudPortfolioName: activeReview.cloudPortfolio....name
  };
}

function clientFitFromCloud(value: unknown): NonNullable<ReviewSummary["clientFit"]> | undefined {
  if (!isRecord(value)) return undefined;
  const rawRows = Array.isArray(value.targetRows) ... value.targetRows : Array.isArray(value.target_rows) ... value.target_rows : [];
  const statusTone = value.statusTone === "green" || value.statusTone === "amber" || value.statusTone === "red"
    ... value.statusTone
    : value.status_tone === "green" || value.status_tone === "amber" || value.status_tone === "red"
      ... value.status_tone
      : "amber";
  return {
    status_label: typeof value.statusLabel === "string" ... value.statusLabel : typeof value.status_label === "string" ... value.status_label : "Client Fit not provided",
    status_tone: statusTone,
    profile_label: typeof value.profileLabel === "string" ... value.profileLabel : typeof value.profile_label === "string" ... value.profile_label : null,
    source_quality_label: typeof value.sourceQualityLabel === "string" ... value.sourceQualityLabel : typeof value.source_quality_label === "string" ... value.source_quality_label : null,
    main_explanation: typeof value.mainExplanation === "string" ... value.mainExplanation : typeof value.main_explanation === "string" ... value.main_explanation : null,
    decision_boundary: typeof value.decisionBoundary === "string" ... value.decisionBoundary : typeof value.decision_boundary === "string" ... value.decision_boundary : "Client Fit is non-binding decision support.",
    next_best_test: typeof value.nextBestTest === "string" ... value.nextBestTest : typeof value.next_best_test === "string" ... value.next_best_test : null,
    target_rows: rawRows.filter(isRecord).slice(0, 6).map((row) => ({
      dimension_label: typeof row.dimensionLabel === "string" ... row.dimensionLabel : typeof row.dimension_label === "string" ... row.dimension_label : "Client Fit check",
      portfolio_value_label: typeof row.portfolioValueLabel === "string" ... row.portfolioValueLabel : typeof row.portfolio_value_label === "string" ... row.portfolio_value_label : null,
      target_or_limit_label: typeof row.targetOrLimitLabel === "string" ... row.targetOrLimitLabel : typeof row.target_or_limit_label === "string" ... row.target_or_limit_label : null,
      status_label: typeof row.statusLabel === "string" ... row.statusLabel : typeof row.status_label === "string" ... row.status_label : "Not evaluated",
      status_tone: row.statusTone === "green" || row.statusTone === "amber" || row.statusTone === "red"
        ... row.statusTone
        : row.status_tone === "green" || row.status_tone === "amber" || row.status_tone === "red"
          ... row.status_tone
          : "amber",
      explanation: typeof row.explanation === "string" ... row.explanation : null
    }))
  };
}

function compactClientFitForCloud(clientFit: ReviewSummary["clientFit"] | ComparisonResultSummaryClientFit | undefined) {
  if (!clientFit) return undefined;
  return {
    statusLabel: clientFit.status_label,
    statusTone: clientFit.status_tone,
    profileLabel: clientFit.profile_label ...... undefined,
    sourceQualityLabel: clientFit.source_quality_label ...... undefined,
    mainExplanation: clientFit.main_explanation ...... undefined,
    decisionBoundary: clientFit.decision_boundary,
    nextBestTest: clientFit.next_best_test ...... undefined,
    targetRows: (clientFit.target_rows ...... []).slice(0, 6).map((row) => ({
      dimensionLabel: row.dimension_label,
      portfolioValueLabel: row.portfolio_value_label ...... undefined,
      targetOrLimitLabel: row.target_or_limit_label ...... undefined,
      statusLabel: row.status_label,
      statusTone: row.status_tone,
      explanation: row.explanation ...... undefined
    }))
  };
}

type ComparisonResultSummaryClientFit = NonNullable<ActiveReviewState["comparisonResult"]>["clientFit"];

function compactEvidenceForCloud(evidence: EvidenceSummary | undefined) {
  if (!evidence) return undefined;
  return {
    headline: evidence.headline,
    quality: evidence.quality,
    boundaryNote: evidence.boundaryNote,
    items: evidence.items.slice(0, 6),
    metrics: evidence.metrics.slice(0, 6)
  };
}

function compactLaunchpadCardsForCloud(cards: LaunchpadCardSummary[]) {
  return cards.slice(0, 6).map((card) => ({
    card_id: card.card_id,
    title: card.title,
    goal: card.goal,
    hypothesis_to_test: card.hypothesis_to_test,
    source_problem_label: card.source_problem_label,
    default_method: card.default_method,
    success_criteria: card.success_criteria,
    tradeoff_to_watch: card.tradeoff_to_watch,
    decision_boundary: card.decision_boundary,
    generates_portfolio: card.generates_portfolio
  }));
}

function compactBuilderSetupForCloud(builderSetup: BuilderSetupSummary | undefined) {
  if (!builderSetup) return undefined;
  return {
    selected_card_id: builderSetup.selected_card_id,
    can_generate_candidate: builderSetup.can_generate_candidate,
    builder_prefill: builderSetup.builder_prefill,
    candidate_setup: builderSetup.candidate_setup
  };
}

function compactDiagnosisForCloud(diagnosis: DiagnosisState) {
  return {
    status: diagnosis.status,
    headline: diagnosis.headline,
    evidenceQuality: diagnosis.evidenceQuality,
    nextStep: diagnosis.nextStep,
    boundaryNote: diagnosis.boundaryNote,
    drivers: diagnosis.drivers,
    metrics: diagnosis.metrics,
    selectedDiagnosisRole: diagnosis.selectedDiagnosisRole,
    sourceArtifacts: diagnosis.sourceArtifacts,
    rejectedAlternatives: diagnosis.rejectedAlternatives,
    rationaleRefs: diagnosis.rationaleRefs
  };
}

function buildDiagnosisStageSummary(activeReview: ActiveReviewState) {
  const reviewSummary = activeReview.reviewSummary;
  if (!reviewSummary) return null;

  return {
    stage: "diagnosis",
    status: "completed",
    reviewId: activeReview.reviewId,
    generatedAt: reviewSummary.generatedAt,
    portfolio: {
      investorCurrency: reviewSummary.investorCurrency,
      holdingsCount: reviewSummary.holdingsCount,
      totalWeight: reviewSummary.totalWeight,
      cashWeight: reviewSummary.cashWeight
    },
    clientFit: compactClientFitForCloud(reviewSummary.clientFit),
    diagnosis: compactDiagnosisForCloud(reviewSummary.diagnosis),
    evidence: compactEvidenceForCloud(reviewSummary.evidence),
    primaryProblem: reviewSummary.primaryProblem,
    problemSeverity: reviewSummary.problemSeverity,
    problemConfidence: reviewSummary.problemConfidence,
    recommendedFirstTest: reviewSummary.recommendedFirstTest,
    suggestedActionPaths: reviewSummary.suggestedActionPaths,
    launchpadCardsCount: reviewSummary.launchpadCardsCount,
    launchpadCards: compactLaunchpadCardsForCloud(reviewSummary.launchpadCards),
    builderSetup: compactBuilderSetupForCloud(reviewSummary.builderSetup),
    artifactRefs: reviewSummary.rawOutputKeys
  };
}

async function upsertReviewRowForUser(userId: string, activeReview: ActiveReviewState) {
  const supabase = getSupabaseBrowserClient();
  if (!supabase) throw new Error("Cloud persistence is disabled.");
  if (!activeReview.reviewId || !activeReview.reviewSummary) {
    throw new Error("No completed diagnosis review is available for cloud persistence.");
  }

  const reviewSummary = activeReview.reviewSummary;
  const compactSummary = compactReviewSummaryForCloud(reviewSummary, activeReview);
  const portfolioSnapshot = compactPortfolioSnapshot(activeReview.investorCurrency, activeReview.holdings);
  const reviewPayload = {
    user_id: userId,
    portfolio_id: activeReview.cloudPortfolio....id ...... null,
    review_id: activeReview.reviewId,
    title: activeReview.cloudPortfolio....name
      ... `${activeReview.cloudPortfolio.name} diagnosis`
      : `Portfolio MRI diagnosis ${activeReview.reviewId}`,
    mode: activeReview.runMode,
    status: activeReview.runStatus,
    portfolio_snapshot: portfolioSnapshot,
    compact_summary: compactSummary,
    started_at: reviewSummary.generatedAt,
    completed_at: reviewSummary.generatedAt
  };

  const { data: reviewRow, error: reviewError } = await supabase
    .from("reviews")
    .upsert(reviewPayload, { onConflict: "user_id,review_id" })
    .select("id")
    .single();

  if (reviewError) throw reviewError;
  return (reviewRow as { id: string }).id;
}

async function upsertStageSummaryForReview({
  userId,
  reviewRowId,
  reviewId,
  stage,
  status,
  summary
}: {
  userId: string;
  reviewRowId: string;
  reviewId: string;
  stage: ReviewStageName;
  status: string;
  summary: Record<string, unknown>;
}): Promise<{ persisted: true; summarySizeBytes: number } | { persisted: false; summarySizeBytes: number; reason: string }> {
  const summarySizeBytes = estimateJsonBytes(summary);
  if (summarySizeBytes > REVIEW_STAGE_SUMMARY_SOFT_LIMIT_BYTES) {
    return {
      persisted: false,
      summarySizeBytes,
      reason: `Compact ${stage} summary is ${summarySizeBytes} bytes, above the 55 KB cloud soft limit.`
    };
  }

  const supabase = getSupabaseBrowserClient();
  if (!supabase) throw new Error("Cloud persistence is disabled.");

  const { error: stageError } = await supabase
    .from("review_stage_summaries")
    .upsert({
      review_row_id: reviewRowId,
      user_id: userId,
      review_id: reviewId,
      stage,
      status,
      summary,
      summary_size_bytes: summarySizeBytes
    }, { onConflict: "review_row_id,stage" });

  if (stageError) throw stageError;
  return { persisted: true, summarySizeBytes };
}

function buildBuilderStageSummary(activeReview: ActiveReviewState) {
  if (!activeReview.builderSetup) return null;
  return {
    stage: "builder",
    status: "completed",
    reviewId: activeReview.reviewId,
    generatedAt: activeReview.updatedAt,
    builderSetup: compactBuilderSetupForCloud(activeReview.builderSetup),
    selectedCardId: activeReview.builderSetup.selected_card_id,
    canGenerateCandidate: activeReview.builderSetup.can_generate_candidate
  };
}

function buildCandidateStageSummary(activeReview: ActiveReviewState) {
  if (!activeReview.candidateGeneration) return null;
  return {
    stage: "candidate",
    status: activeReview.candidateGeneration.status,
    reviewId: activeReview.reviewId,
    candidate: activeReview.candidateGeneration,
    selectedCardId: activeReview.candidateGeneration.selectedCardId,
    candidateId: activeReview.candidateGeneration.candidateId
  };
}

function buildComparisonStageSummary(activeReview: ActiveReviewState) {
  if (!activeReview.comparisonResult) return null;
  return {
    stage: "comparison",
    status: activeReview.comparisonResult.status,
    reviewId: activeReview.reviewId,
    comparison: activeReview.comparisonResult,
    clientFit: compactClientFitForCloud(activeReview.comparisonResult.clientFit ...... activeReview.reviewSummary....clientFit),
    selectedCardId: activeReview.comparisonResult.selectedCardId,
    candidateId: activeReview.comparisonResult.candidateId
  };
}

function buildVerdictStageSummary(activeReview: ActiveReviewState) {
  if (!activeReview.verdictResult) return null;
  return {
    stage: "verdict",
    status: activeReview.verdictResult.status,
    reviewId: activeReview.reviewId,
    verdict: activeReview.verdictResult,
    clientFit: compactClientFitForCloud(activeReview.verdictResult.clientFit ...... activeReview.reviewSummary....clientFit),
    selectedCardId: activeReview.verdictResult.selectedCardId,
    candidateId: activeReview.verdictResult.candidateId
  };
}

function buildReportStageSummary(activeReview: ActiveReviewState) {
  if (!activeReview.reportResult) return null;
  return {
    stage: "report",
    status: activeReview.reportResult.status,
    reviewId: activeReview.reviewId,
    report: activeReview.reportResult,
    clientFit: compactClientFitForCloud(activeReview.reportResult.clientFit ...... activeReview.reviewSummary....clientFit),
    selectedCardId: activeReview.reportResult.selectedCardId,
    candidateId: activeReview.reportResult.candidateId
  };
}

export async function persistDiagnosisSummaryForReview(userId: string, activeReview: ActiveReviewState) {
  if (!activeReview.reviewId || !activeReview.reviewSummary) {
    throw new Error("No completed diagnosis review is available for cloud persistence.");
  }
  const reviewRowId = await upsertReviewRowForUser(userId, activeReview);
  const stageSummary = buildDiagnosisStageSummary(activeReview);
  if (!stageSummary) throw new Error("Diagnosis summary is unavailable for cloud persistence.");
  const result = await upsertStageSummaryForReview({
    userId,
    reviewRowId,
    reviewId: activeReview.reviewId,
    stage: "diagnosis",
    status: "completed",
    summary: stageSummary
  });
  if (!result.persisted) throw new Error(result.reason);
}

export async function persistCompactStageSummariesForReview(userId: string, activeReview: ActiveReviewState): Promise<StagePersistenceResult> {
  if (!activeReview.reviewId || !activeReview.reviewSummary) {
    throw new Error("No active review is available for cloud stage persistence.");
  }

  const reviewRowId = await upsertReviewRowForUser(userId, activeReview);
  const candidates: Array<{ stage: ReviewStageName; status: string; summary: Record<string, unknown> | null }> = [
    { stage: "builder", status: activeReview.builderSetup ... "completed" : "missing", summary: buildBuilderStageSummary(activeReview) },
    { stage: "candidate", status: activeReview.candidateGeneration....status ...... "missing", summary: buildCandidateStageSummary(activeReview) },
    { stage: "comparison", status: activeReview.comparisonResult....status ...... "missing", summary: buildComparisonStageSummary(activeReview) },
    { stage: "verdict", status: activeReview.verdictResult....status ...... "missing", summary: buildVerdictStageSummary(activeReview) },
    { stage: "report", status: activeReview.reportResult....status ...... "missing", summary: buildReportStageSummary(activeReview) }
  ];

  const persisted: ReviewStageName[] = [];
  const skipped: StagePersistenceResult["skipped"] = [];

  for (const item of candidates) {
    if (!item.summary) continue;
    const result = await upsertStageSummaryForReview({
      userId,
      reviewRowId,
      reviewId: activeReview.reviewId,
      stage: item.stage,
      status: item.status,
      summary: item.summary
    });
    if (result.persisted) persisted.push(item.stage);
    else skipped.push({ stage: item.stage, summarySizeBytes: result.summarySizeBytes, reason: result.reason });
  }

  if (activeReview.verdictResult) {
    const supabase = getSupabaseBrowserClient();
    if (!supabase) throw new Error("Cloud persistence is disabled.");
    const confidenceNumber = Number.parseFloat(activeReview.verdictResult.confidence);
    const { error } = await supabase
      .from("verdicts")
      .upsert({
        review_row_id: reviewRowId,
        user_id: userId,
        review_id: activeReview.reviewId,
        verdict: activeReview.verdictResult.decisionStatus,
        confidence: Number.isFinite(confidenceNumber) ... confidenceNumber : null,
        rationale: activeReview.verdictResult.explanation,
        summary: activeReview.verdictResult,
        limitations: activeReview.verdictResult.limitations
      }, { onConflict: "review_row_id" });
    if (error) throw error;
  }

  return { persisted, skipped };
}

export function SupabasePersistenceProvider({ children }: { children: ReactNode }) {
  const { enabled, status, user } = useSupabaseAuth();
  const [savedPortfolios, setSavedPortfolios] = useState<SavedPortfolioRecord[]>([]);
  const [savedReviews, setSavedReviews] = useState<SavedReviewRecord[]>([]);
  const [portfoliosLoading, setPortfoliosLoading] = useState(false);
  const [reviewsLoading, setReviewsLoading] = useState(false);
  const [notice, setNoticeState] = useState<CloudNotice | null>(null);
  const signedIn = enabled && status === "signed_in" && Boolean(user....id);

  const setNotice = useCallback((tone: CloudNotice["tone"], message: string) => {
    setNoticeState({
      tone,
      message,
      occurredAt: nowIso()
    });
  }, []);

  const clearNotice = useCallback(() => {
    setNoticeState(null);
  }, []);

  const refreshSavedPortfolios = useCallback(async () => {
    if (!signedIn || !user....id) {
      setSavedPortfolios([]);
      return;
    }

    setPortfoliosLoading(true);
    try {
      const portfolios = await fetchSavedPortfoliosForUser(user.id);
      setSavedPortfolios(portfolios);
    } catch (error) {
      setNotice("warning", `Could not load saved portfolios. ${humanizePersistenceError(error)}`);
    } finally {
      setPortfoliosLoading(false);
    }
  }, [setNotice, signedIn, user....id]);

  const refreshSavedReviews = useCallback(async () => {
    if (!signedIn || !user....id) {
      setSavedReviews([]);
      return;
    }

    setReviewsLoading(true);
    try {
      const reviews = await fetchSavedReviewsForUser(user.id);
      setSavedReviews(reviews);
    } catch (error) {
      setNotice("warning", `Could not load saved reviews. ${humanizePersistenceError(error)}`);
    } finally {
      setReviewsLoading(false);
    }
  }, [setNotice, signedIn, user....id]);

  const savePortfolio = useCallback(async (input: SavePortfolioInput) => {
    if (!signedIn || !user....id) {
      setNotice("warning", "Sign in first to save portfolios to cloud.");
      return null;
    }

    try {
      const saved = await savePortfolioRecordForUser(user.id, input);
      const portfolios = await fetchSavedPortfoliosForUser(user.id);
      setSavedPortfolios(portfolios);
      setNotice("success", `Saved "${saved.name}" to optional cloud storage.`);
      return saved;
    } catch (error) {
      setNotice("warning", `Cloud portfolio save failed. ${humanizePersistenceError(error)}`);
      return null;
    }
  }, [setNotice, signedIn, user....id]);

  const deletePortfolio = useCallback(async (portfolioId: string) => {
    if (!signedIn || !user....id) {
      setNotice("warning", "Sign in first to delete saved cloud portfolios.");
      return false;
    }

    try {
      const portfolioName = savedPortfolios.find((item) => item.id === portfolioId)....name;
      await deletePortfolioForUser(user.id, portfolioId);
      const portfolios = await fetchSavedPortfoliosForUser(user.id);
      setSavedPortfolios(portfolios);
      setNotice("success", portfolioName ... `Deleted "${portfolioName}" from cloud storage.` : "Deleted saved cloud portfolio.");
      return true;
    } catch (error) {
      setNotice("warning", `Cloud portfolio delete failed. ${humanizePersistenceError(error)}`);
      return false;
    }
  }, [savedPortfolios, setNotice, signedIn, user....id]);

  useEffect(() => {
    if (!signedIn || !user....id) {
      setSavedPortfolios([]);
      setSavedReviews([]);
      setPortfoliosLoading(false);
      setReviewsLoading(false);
      return;
    }
    void refreshSavedPortfolios();
    void refreshSavedReviews();
  }, [refreshSavedPortfolios, refreshSavedReviews, signedIn, user....id]);

  const value = useMemo<SupabasePersistenceContextValue>(() => ({
    enabled,
    signedIn,
    userId: user....id ...... null,
    savedPortfolios,
    savedReviews,
    portfoliosLoading,
    reviewsLoading,
    notice,
    clearNotice,
    setNotice,
    refreshSavedPortfolios,
    refreshSavedReviews,
    savePortfolio,
    deletePortfolio
  }), [clearNotice, deletePortfolio, enabled, notice, portfoliosLoading, refreshSavedPortfolios, refreshSavedReviews, reviewsLoading, savePortfolio, savedPortfolios, savedReviews, setNotice, signedIn, user....id]);

  return <SupabasePersistenceContext.Provider value={value}>{children}</SupabasePersistenceContext.Provider>;
}

export function useSupabasePersistence() {
  const context = useContext(SupabasePersistenceContext);
  if (!context) {
    throw new Error("useSupabasePersistence must be used within SupabasePersistenceProvider");
  }
  return context;
}
