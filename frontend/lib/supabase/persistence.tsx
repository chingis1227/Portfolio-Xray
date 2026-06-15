"use client";

import { createContext, useCallback, useContext, useEffect, useMemo, useState, type ReactNode } from "react";
import { getSupabaseBrowserClient } from "./client";
import { useSupabaseAuth } from "./auth";
import type { ReviewHolding, ActiveReviewState, ReviewSummary, DiagnosisState, EvidenceSummary, LaunchpadCardSummary, BuilderSetupSummary, ReportResultSummary } from "@/lib/reviewState";

export type SavedPortfolioRecord = {
  id: string;
  name: string;
  description?: string;
  baseCurrency: string;
  riskProfile?: string;
  holdings: ReviewHolding[];
  archivedAt?: string;
  latestVersionId?: string;
  versionNumber?: number;
  createdAt?: string;
  updatedAt?: string;
};
export type ReviewStageName =
  | "diagnosis"
  | "builder"
  | "input"
  | "data_load"
  | "xray"
  | "stress"
  | "client_fit"
  | "problem_classification"
  | "launchpad_builder"
  | "candidate"
  | "comparison"
  | "verdict"
  | "report";

export type SavedReviewRecord = {
  id: string;
  reviewId: string;
  title?: string;
  mode?: string;
  status: string;
  portfolioId?: string;
  portfolioVersionId?: string;
  archivedAt?: string;
  readOnlyHistory: boolean;
  lineageAvailable: boolean;
  portfolioSnapshot: { investorCurrency?: string; holdings?: ReviewHolding[] };
  compactSummary: Record<string, unknown>;
  clientFit?: NonNullable<ReviewSummary["clientFit"]>;
  stages: Partial<Record<ReviewStageName, Record<string, unknown>>>;
  stageStatuses: Partial<Record<ReviewStageName, string>>;
  startedAt?: string;
  completedAt?: string;
  updatedAt?: string;
};

export type WorkspaceStateRecord = {
  userId: string;
  activePortfolioId?: string;
  activePortfolioVersionId?: string;
  activeReviewRowId?: string;
  lastOpenedReviewRowId?: string;
  metadata: Record<string, unknown>;
  createdAt?: string;
  updatedAt?: string;
};

export type PortfolioVersionRecord = {
  id: string;
  portfolioId: string;
  userId: string;
  versionNumber: number;
  baseCurrency: string;
  holdingsSnapshot: ReviewHolding[];
  inputFingerprint?: string;
  sourceKind: string;
  sourceReviewId?: string;
  createdAt?: string;
  updatedAt?: string;
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
  portfolioId?: string;
  name: string;
  description?: string;
  investorCurrency: string;
  holdings: ReviewHolding[];
};

type SupabasePersistenceContextValue = {
  enabled: boolean;
  signedIn: boolean;
  userId: string | null;
  savedPortfolios: SavedPortfolioRecord[];
  savedReviews: SavedReviewRecord[];
  workspaceState: WorkspaceStateRecord | null;
  portfoliosLoading: boolean;
  reviewsLoading: boolean;
  workspaceLoading: boolean;
  notice: CloudNotice | null;
  clearNotice: () => void;
  setNotice: (tone: CloudNotice["tone"], message: string) => void;
  refreshSavedPortfolios: () => Promise<void>;
  refreshSavedReviews: () => Promise<void>;
  refreshWorkspaceState: () => Promise<void>;
  savePortfolio: (input: SavePortfolioInput) => Promise<SavedPortfolioRecord | null>;
  ensurePortfolioVersion: (input: { portfolioId: string; portfolioName?: string; investorCurrency: string; holdings: ReviewHolding[]; sourceKind?: string; sourceReviewId?: string }) => Promise<PortfolioVersionRecord | null>;
  deletePortfolio: (portfolioId: string) => Promise<boolean>;
  archiveReview: (reviewRowId: string) => Promise<boolean>;
};

type PortfolioRow = {
  id: string;
  name: string;
  description: string | null;
  base_currency: string;
  risk_profile: string | null;
  archived_at: string | null;
  created_at: string | null;
  updated_at: string | null;
};

type PortfolioVersionRow = {
  id: string;
  portfolio_id: string;
  user_id: string;
  version_number: number;
  base_currency: string;
  holdings_snapshot: unknown;
  input_fingerprint: string | null;
  source_kind: string | null;
  source_review_id: string | null;
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
  portfolio_version_id: string | null;
  archived_at: string | null;
  portfolio_snapshot: Record<string, unknown> | null;
  compact_summary: Record<string, unknown> | null;
  started_at: string | null;
  completed_at: string | null;
  updated_at: string | null;
};

type WorkspaceStateRow = {
  user_id: string;
  active_portfolio_id: string | null;
  active_portfolio_version_id: string | null;
  active_review_row_id: string | null;
  last_opened_review_row_id: string | null;
  metadata: Record<string, unknown> | null;
  created_at: string | null;
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
const STAGED_REVIEW_STAGE_NAMES: ReviewStageName[] = [
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
];


const SupabasePersistenceContext = createContext<SupabasePersistenceContextValue | null>(null);

function nowIso() {
  return new Date().toISOString();
}

function estimateJsonBytes(value: unknown) {
  const raw = JSON.stringify(value ?? null);
  if (typeof TextEncoder !== "undefined") return new TextEncoder().encode(raw).length;
  return raw.length;
}

function isRecord(value: unknown): value is Record<string, unknown> {
  return Boolean(value) && typeof value === "object" && !Array.isArray(value);
}

function isCloudForbiddenKey(key: string) {
  const normalized = key.replace(/[_-]/g, "").toLowerCase();
  return normalized === "path"
    || normalized === "paths"
    || normalized === "outputpaths"
    || normalized === "artifactrefs"
    || normalized === "artifactref"
    || normalized === "sourceartifacts"
    || normalized === "rawoutputkeys"
    || normalized === "rawaccessstrategy"
    || normalized === "sourcerefs"
    || normalized.includes("localpath")
    || normalized.endsWith("path");
}

function isUnsafeCloudString(value: string) {
  return /[A-Za-z]:[\\/]/.test(value)
    || /(^|[\\/])(runs|cache|Main portfolio|pdf files|pdf_md_sources|results_csv)([\\/]|$)/i.test(value)
    || /frontend_review_[^/\\\s]+[\\/]/i.test(value)
    || /\b(portfolio_xray|stress_report|client_fit_check|review_state|run_result|review_result|candidate_generation|current_vs_candidate|decision_verdict)\.json\b/i.test(value)
    || /\.(pdf|csv|parquet|png|html|txt)\b/i.test(value);
}

function compactCloudValue(value: unknown): unknown {
  if (typeof value === "string") {
    return isUnsafeCloudString(value) ? undefined : value;
  }
  if (Array.isArray(value)) {
    return value
      .map((item) => compactCloudValue(item))
      .filter((item) => item !== undefined);
  }
  if (!isRecord(value)) return value;

  const compact: Record<string, unknown> = {};
  Object.entries(value).forEach(([key, item]) => {
    if (isCloudForbiddenKey(key)) return;
    const cleaned = compactCloudValue(item);
    if (cleaned !== undefined) compact[key] = cleaned;
  });
  return compact;
}

function compactCloudRecord(value: Record<string, unknown>) {
  const compact = compactCloudValue(value);
  return isRecord(compact) ? compact : {};
}

function normalizedHoldingsSnapshot(holdings: ReviewHolding[]) {
  return holdings
    .map((holding) => ({
      ticker: holding.ticker.trim().toUpperCase(),
      label: holding.label,
      instrument: holding.instrument,
      weight: Number.isFinite(holding.weight) ? Number(holding.weight.toFixed(6)) : 0,
      type: holding.type,
      currency: holding.currency
    }))
    .filter((holding) => holding.ticker)
    .sort((a, b) => a.ticker.localeCompare(b.ticker) || a.weight - b.weight);
}

function portfolioInputFingerprint(investorCurrency: string, holdings: ReviewHolding[]) {
  return JSON.stringify({
    schema: "pmri_portfolio_input_fingerprint_v1",
    investorCurrency: (investorCurrency || "USD").trim().toUpperCase(),
    holdings: normalizedHoldingsSnapshot(holdings).map((holding) => ({
      ticker: holding.ticker,
      weight: holding.weight,
      type: holding.type,
      currency: holding.currency ?? null
    }))
  });
}

function reviewHoldingsFromSnapshot(value: unknown): ReviewHolding[] {
  if (!isRecord(value) || !Array.isArray(value.holdings)) return [];
  return value.holdings
    .filter(isRecord)
    .map((holding, index) => ({
      id: typeof holding.id === "string" ? holding.id : safeHoldingId(typeof holding.ticker === "string" ? holding.ticker : "holding", index),
      label: typeof holding.label === "string" ? holding.label : typeof holding.ticker === "string" ? holding.ticker : "Holding",
      ticker: typeof holding.ticker === "string" ? holding.ticker : "",
      instrument: typeof holding.instrument === "string" ? holding.instrument : typeof holding.ticker === "string" ? holding.ticker : "Holding",
      weight: typeof holding.weight === "number" && Number.isFinite(holding.weight) ? holding.weight : 0,
      type: holding.type === "cash" ? "cash" : "instrument",
      currency: typeof holding.currency === "string" ? holding.currency : undefined
    } satisfies ReviewHolding))
    .filter((holding) => holding.ticker);
}

function holdingsFromVersionSnapshot(value: unknown): ReviewHolding[] {
  if (!Array.isArray(value)) return [];
  return value
    .filter(isRecord)
    .map((holding, index) => ({
      id: typeof holding.id === "string" ? holding.id : safeHoldingId(typeof holding.ticker === "string" ? holding.ticker : "holding", index),
      label: typeof holding.label === "string" ? holding.label : typeof holding.ticker === "string" ? holding.ticker : "Holding",
      ticker: typeof holding.ticker === "string" ? holding.ticker : "",
      instrument: typeof holding.instrument === "string" ? holding.instrument : typeof holding.ticker === "string" ? holding.ticker : "Holding",
      weight: typeof holding.weight === "number" && Number.isFinite(holding.weight) ? holding.weight : 0,
      type: holding.type === "cash" ? "cash" : "instrument",
      currency: typeof holding.currency === "string" ? holding.currency : undefined
    } satisfies ReviewHolding))
    .filter((holding) => holding.ticker);
}


function humanizePersistenceError(error: unknown) {
  const rawMessage = error instanceof Error
    ? error.message
    : isRecord(error) && typeof error.message === "string"
      ? error.message
      : isRecord(error) && typeof error.details === "string"
        ? error.details
        : typeof error === "string"
          ? error
          : "";
  const message = rawMessage.trim();
  if (!message || message === "[object Object]") {
    return "Saved workspace data is temporarily unavailable. You can continue locally or try again.";
  }
  if (message.toLowerCase().includes("fetch")) {
    return "Could not reach the saved workspace service. Check your connection and try again.";
  }
  return message
    .replace(/Supabase/gi, "saved workspace service")
    .replace(/cloud persistence/gi, "workspace saving")
    .replace(/cloud/gi, "workspace");
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

function buildSavedPortfolioRecord(row: PortfolioRow, holdings: PortfolioHoldingRow[], latestVersion?: PortfolioVersionRow): SavedPortfolioRecord {
  const normalizedHoldings = holdings
    .sort((a, b) => (a.sort_order ?? 0) - (b.sort_order ?? 0))
    .map((holding, index) => {
      const metadata = holding.metadata ?? {};
      const storedType = typeof metadata.holding_type === "string" ? metadata.holding_type : null;
      const type: ReviewHolding["type"] = storedType === "cash" || holding.asset_class === "cash" ? "cash" : "instrument";
      return {
        id: safeHoldingId(holding.ticker, index),
        label: typeof metadata.label === "string" && metadata.label.trim() ? metadata.label : type === "cash" ? "Cash" : holding.ticker,
        ticker: holding.ticker,
        instrument: typeof metadata.instrument === "string" && metadata.instrument.trim() ? metadata.instrument : holding.name || holding.ticker,
        weight: roundWeightPercent(holding.weight),
        type,
        currency: type === "cash" ? (holding.currency || "USD") : undefined
      } satisfies ReviewHolding;
    })
    .sort(sortHoldings);

  return {
    id: row.id,
    name: row.name,
    description: row.description ?? undefined,
    baseCurrency: row.base_currency || "USD",
    riskProfile: row.risk_profile ?? undefined,
    holdings: normalizedHoldings,
    archivedAt: row.archived_at ?? undefined,
    latestVersionId: latestVersion?.id,
    versionNumber: latestVersion?.version_number,
    createdAt: row.created_at ?? undefined,
    updatedAt: row.updated_at ?? undefined
  };
}

async function fetchSavedPortfoliosForUser(userId: string): Promise<SavedPortfolioRecord[]> {
  const supabase = getSupabaseBrowserClient();
  if (!supabase) return [];

  const { data: portfolioRows, error: portfolioError } = await supabase
    .from("portfolios")
    .select("id, name, description, base_currency, risk_profile, archived_at, created_at, updated_at")
    .eq("user_id", userId)
    .is("archived_at", null)
    .order("updated_at", { ascending: false });

  if (portfolioError) throw portfolioError;

  const rows = (portfolioRows ?? []) as PortfolioRow[];
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
  ((holdingRows ?? []) as PortfolioHoldingRow[]).forEach((row) => {
    const existing = holdingsByPortfolioId.get(row.portfolio_id) ?? [];
    existing.push(row);
    holdingsByPortfolioId.set(row.portfolio_id, existing);
  });

  const { data: versionRows, error: versionError } = await supabase
    .from("portfolio_versions")
    .select("id, portfolio_id, user_id, version_number, base_currency, holdings_snapshot, input_fingerprint, source_kind, source_review_id, created_at, updated_at")
    .eq("user_id", userId)
    .in("portfolio_id", portfolioIds)
    .order("version_number", { ascending: false });

  if (versionError) throw versionError;

  const latestVersionByPortfolioId = new Map<string, PortfolioVersionRow>();
  ((versionRows ?? []) as PortfolioVersionRow[]).forEach((row) => {
    if (!latestVersionByPortfolioId.has(row.portfolio_id)) {
      latestVersionByPortfolioId.set(row.portfolio_id, row);
    }
  });

  return rows.map((row) => buildSavedPortfolioRecord(row, holdingsByPortfolioId.get(row.id) ?? [], latestVersionByPortfolioId.get(row.id)));
}



async function fetchSavedReviewsForUser(userId: string): Promise<SavedReviewRecord[]> {
  const supabase = getSupabaseBrowserClient();
  if (!supabase) return [];

  const { data: reviewRows, error: reviewError } = await supabase
    .from("reviews")
    .select("id, portfolio_id, portfolio_version_id, archived_at, review_id, title, mode, status, portfolio_snapshot, compact_summary, started_at, completed_at, updated_at")
    .eq("user_id", userId)
    .is("archived_at", null)
    .order("updated_at", { ascending: false })
    .limit(12);

  if (reviewError) throw reviewError;

  const rows = (reviewRows ?? []) as ReviewRow[];
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
  ((stageRows ?? []) as ReviewStageSummaryRow[]).forEach((row) => {
    const existing = stagesByReviewRowId.get(row.review_row_id) ?? [];
    existing.push(row);
    stagesByReviewRowId.set(row.review_row_id, existing);
  });

  return rows.map((row) => {
    const stages: Partial<Record<ReviewStageName, Record<string, unknown>>> = {};
    const stageStatuses: Partial<Record<ReviewStageName, string>> = {};
    (stagesByReviewRowId.get(row.id) ?? []).forEach((stageRow) => {
      stages[stageRow.stage] = stageRow.summary ?? {};
      stageStatuses[stageRow.stage] = stageRow.status ?? "saved";
    });
    const snapshot = row.portfolio_snapshot ?? {};
    const compactSummary = row.compact_summary ?? {};
    const diagnosisStage = stages.diagnosis ?? {};
    const lineageAvailable = false;
    return {
      id: row.id,
      reviewId: row.review_id,
      title: row.title ?? undefined,
      mode: row.mode ?? undefined,
      status: row.status ?? "saved",
      portfolioId: row.portfolio_id ?? undefined,
      portfolioVersionId: row.portfolio_version_id ?? undefined,
      archivedAt: row.archived_at ?? undefined,
      readOnlyHistory: !lineageAvailable,
      lineageAvailable,
      portfolioSnapshot: {
        investorCurrency: typeof snapshot.investorCurrency === "string" ? snapshot.investorCurrency : undefined,
        holdings: reviewHoldingsFromSnapshot(snapshot)
      },
      compactSummary,
      clientFit: clientFitFromCloud(compactSummary.clientFit ?? diagnosisStage.clientFit),
      stages,
      stageStatuses,
      startedAt: row.started_at ?? undefined,
      completedAt: row.completed_at ?? undefined,
      updatedAt: row.updated_at ?? undefined
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
    ...(input.portfolioId ? { id: input.portfolioId } : {}),
    user_id: userId,
    name: trimmedName,
    description: input.description?.trim() || null,
    base_currency: input.investorCurrency || "USD",
    metadata: {
      source: "pmri_frontend_v1",
      holdings_count: input.holdings.length
    }
  };

  const { data: portfolioRow, error: portfolioError } = await supabase
    .from("portfolios")
    .upsert(portfolioPayload)
    .select("id, name, description, base_currency, risk_profile, archived_at, created_at, updated_at")
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
      currency: holding.currency ?? null,
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

  const version = await ensurePortfolioVersionForUser(userId, {
    portfolioId,
    investorCurrency: input.investorCurrency,
    holdings: input.holdings,
    sourceKind: "manual"
  });

  return buildSavedPortfolioRecord(portfolioRow as PortfolioRow, input.holdings.map((holding, index) => ({
    portfolio_id: portfolioId,
    ticker: holding.ticker,
    name: holding.instrument || holding.label || holding.ticker,
    asset_class: holding.type,
    weight: clampWeightToFraction(holding.weight),
    currency: holding.currency ?? null,
    sort_order: index,
    metadata: {
      instrument: holding.instrument,
      label: holding.label,
      holding_type: holding.type
    }
  })), {
    id: version.id,
    portfolio_id: version.portfolioId,
    user_id: version.userId,
    version_number: version.versionNumber,
    base_currency: version.baseCurrency,
    holdings_snapshot: version.holdingsSnapshot,
    input_fingerprint: version.inputFingerprint ?? null,
    source_kind: version.sourceKind,
    source_review_id: version.sourceReviewId ?? null,
    created_at: version.createdAt ?? null,
    updated_at: version.updatedAt ?? null
  });
}

async function deletePortfolioForUser(userId: string, portfolioId: string) {
  const supabase = getSupabaseBrowserClient();
  if (!supabase) throw new Error("Cloud persistence is disabled.");

  const { error } = await supabase
    .from("portfolios")
    .update({ archived_at: nowIso() })
    .eq("user_id", userId)
    .eq("id", portfolioId);

  if (error) throw error;
}

async function archiveReviewForUser(userId: string, reviewRowId: string) {
  const supabase = getSupabaseBrowserClient();
  if (!supabase) throw new Error("Cloud persistence is disabled.");

  const { error } = await supabase
    .from("reviews")
    .update({ archived_at: nowIso() })
    .eq("user_id", userId)
    .eq("id", reviewRowId);

  if (error) throw error;
}

function buildPortfolioVersionRecord(row: PortfolioVersionRow): PortfolioVersionRecord {
  return {
    id: row.id,
    portfolioId: row.portfolio_id,
    userId: row.user_id,
    versionNumber: row.version_number,
    baseCurrency: row.base_currency || "USD",
    holdingsSnapshot: holdingsFromVersionSnapshot(row.holdings_snapshot),
    inputFingerprint: row.input_fingerprint ?? undefined,
    sourceKind: row.source_kind || "manual",
    sourceReviewId: row.source_review_id ?? undefined,
    createdAt: row.created_at ?? undefined,
    updatedAt: row.updated_at ?? undefined
  };
}

async function ensurePortfolioVersionForUser(
  userId: string,
  input: { portfolioId: string; investorCurrency: string; holdings: ReviewHolding[]; sourceKind?: string; sourceReviewId?: string }
): Promise<PortfolioVersionRecord> {
  const supabase = getSupabaseBrowserClient();
  if (!supabase) throw new Error("Cloud persistence is disabled.");

  const fingerprint = portfolioInputFingerprint(input.investorCurrency, input.holdings);
  const { data: existingRows, error: existingError } = await supabase
    .from("portfolio_versions")
    .select("id, portfolio_id, user_id, version_number, base_currency, holdings_snapshot, input_fingerprint, source_kind, source_review_id, created_at, updated_at")
    .eq("user_id", userId)
    .eq("portfolio_id", input.portfolioId)
    .eq("input_fingerprint", fingerprint)
    .limit(1);

  if (existingError) throw existingError;
  const existing = ((existingRows ?? []) as PortfolioVersionRow[])[0];
  if (existing) return buildPortfolioVersionRecord(existing);

  const { data: latestRows, error: latestError } = await supabase
    .from("portfolio_versions")
    .select("version_number")
    .eq("user_id", userId)
    .eq("portfolio_id", input.portfolioId)
    .order("version_number", { ascending: false })
    .limit(1);

  if (latestError) throw latestError;
  const latestNumber = ((latestRows ?? []) as Array<{ version_number: number }>)[0]?.version_number ?? 0;

  const { data: insertedRow, error: insertError } = await supabase
    .from("portfolio_versions")
    .insert({
      user_id: userId,
      portfolio_id: input.portfolioId,
      version_number: latestNumber + 1,
      base_currency: input.investorCurrency || "USD",
      holdings_snapshot: normalizedHoldingsSnapshot(input.holdings),
      input_fingerprint: fingerprint,
      source_kind: input.sourceKind || "manual",
      source_review_id: input.sourceReviewId ?? null
    })
    .select("id, portfolio_id, user_id, version_number, base_currency, holdings_snapshot, input_fingerprint, source_kind, source_review_id, created_at, updated_at")
    .single();

  if (insertError) throw insertError;
  return buildPortfolioVersionRecord(insertedRow as PortfolioVersionRow);
}

function buildWorkspaceStateRecord(row: WorkspaceStateRow): WorkspaceStateRecord {
  return {
    userId: row.user_id,
    activePortfolioId: row.active_portfolio_id ?? undefined,
    activePortfolioVersionId: row.active_portfolio_version_id ?? undefined,
    activeReviewRowId: row.active_review_row_id ?? undefined,
    lastOpenedReviewRowId: row.last_opened_review_row_id ?? undefined,
    metadata: row.metadata ?? {},
    createdAt: row.created_at ?? undefined,
    updatedAt: row.updated_at ?? undefined
  };
}

async function fetchWorkspaceStateForUser(userId: string): Promise<WorkspaceStateRecord | null> {
  const supabase = getSupabaseBrowserClient();
  if (!supabase) return null;

  const { data, error } = await supabase
    .from("workspace_state")
    .select("user_id, active_portfolio_id, active_portfolio_version_id, active_review_row_id, last_opened_review_row_id, metadata, created_at, updated_at")
    .eq("user_id", userId)
    .maybeSingle();

  if (error) throw error;
  return data ? buildWorkspaceStateRecord(data as WorkspaceStateRow) : null;
}

async function upsertWorkspaceStateForUser(userId: string, patch: Partial<WorkspaceStateRecord>): Promise<WorkspaceStateRecord> {
  const supabase = getSupabaseBrowserClient();
  if (!supabase) throw new Error("Cloud persistence is disabled.");

  const payload = {
    user_id: userId,
    active_portfolio_id: patch.activePortfolioId ?? null,
    active_portfolio_version_id: patch.activePortfolioVersionId ?? null,
    active_review_row_id: patch.activeReviewRowId ?? null,
    last_opened_review_row_id: patch.lastOpenedReviewRowId ?? patch.activeReviewRowId ?? null,
    metadata: compactCloudRecord(patch.metadata ?? {})
  };

  const { data, error } = await supabase
    .from("workspace_state")
    .upsert(payload, { onConflict: "user_id" })
    .select("user_id, active_portfolio_id, active_portfolio_version_id, active_review_row_id, last_opened_review_row_id, metadata, created_at, updated_at")
    .single();

  if (error) throw error;
  return buildWorkspaceStateRecord(data as WorkspaceStateRow);
}

async function upsertDraftReviewForPortfolioVersion(
  userId: string,
  input: { portfolioId: string; portfolioName?: string; investorCurrency: string; holdings: ReviewHolding[] },
  version: PortfolioVersionRecord
) {
  const supabase = getSupabaseBrowserClient();
  if (!supabase) throw new Error("Cloud persistence is disabled.");

  const draftReviewId = `draft_${version.id.replace(/-/g, "")}`;
  const compactSummary = compactCloudRecord({
    reviewKind: "draft",
    status: "draft",
    investorCurrency: input.investorCurrency,
    holdingsCount: input.holdings.length,
    activeCloudPortfolioId: input.portfolioId,
    activeCloudPortfolioName: input.portfolioName,
    activeCloudPortfolioVersionId: version.id,
    activeCloudPortfolioVersionNumber: version.versionNumber,
    readOnlyHistory: false,
    lineageAvailable: false,
    note: "Draft review created from changed portfolio input. Diagnosis is not run automatically."
  });

  const { data: reviewRow, error } = await supabase
    .from("reviews")
    .upsert({
      user_id: userId,
      portfolio_id: input.portfolioId,
      portfolio_version_id: version.id,
      review_id: draftReviewId,
      title: input.portfolioName ? `${input.portfolioName} draft` : "Portfolio MRI draft review",
      mode: "draft",
      status: "draft",
      portfolio_snapshot: compactPortfolioSnapshot(input.investorCurrency, input.holdings),
      compact_summary: compactSummary,
      started_at: null,
      completed_at: null
    }, { onConflict: "user_id,review_id" })
    .select("id")
    .single();

  if (error) throw error;
  return {
    reviewRowId: (reviewRow as { id: string }).id,
    draftReviewId
  };
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
    activeCloudPortfolioId: activeReview.cloudPortfolio?.id,
    activeCloudPortfolioName: activeReview.cloudPortfolio?.name,
    activeCloudPortfolioVersionId: activeReview.portfolioVersionId ?? activeReview.cloudPortfolio?.versionId,
    activeCloudPortfolioVersionNumber: activeReview.portfolioVersionNumber ?? activeReview.cloudPortfolio?.versionNumber,
    lineageAvailable: Boolean(activeReview.lineageAvailable),
    readOnlyHistory: Boolean(activeReview.readOnlyHistory)
  };
}

function clientFitFromCloud(value: unknown): NonNullable<ReviewSummary["clientFit"]> | undefined {
  if (!isRecord(value)) return undefined;
  const rawRows = Array.isArray(value.targetRows) ? value.targetRows : Array.isArray(value.target_rows) ? value.target_rows : [];
  const statusTone = value.statusTone === "green" || value.statusTone === "amber" || value.statusTone === "red"
    ? value.statusTone
    : value.status_tone === "green" || value.status_tone === "amber" || value.status_tone === "red"
      ? value.status_tone
      : "amber";
  return {
    status_label: typeof value.statusLabel === "string" ? value.statusLabel : typeof value.status_label === "string" ? value.status_label : "Client Fit not provided",
    status_tone: statusTone,
    profile_label: typeof value.profileLabel === "string" ? value.profileLabel : typeof value.profile_label === "string" ? value.profile_label : null,
    source_quality_label: typeof value.sourceQualityLabel === "string" ? value.sourceQualityLabel : typeof value.source_quality_label === "string" ? value.source_quality_label : null,
    main_explanation: typeof value.mainExplanation === "string" ? value.mainExplanation : typeof value.main_explanation === "string" ? value.main_explanation : null,
    decision_boundary: typeof value.decisionBoundary === "string" ? value.decisionBoundary : typeof value.decision_boundary === "string" ? value.decision_boundary : "Client Fit is non-binding decision support.",
    next_best_test: typeof value.nextBestTest === "string" ? value.nextBestTest : typeof value.next_best_test === "string" ? value.next_best_test : null,
    target_rows: rawRows.filter(isRecord).slice(0, 6).map((row) => ({
      dimension_label: typeof row.dimensionLabel === "string" ? row.dimensionLabel : typeof row.dimension_label === "string" ? row.dimension_label : "Client Fit check",
      portfolio_value_label: typeof row.portfolioValueLabel === "string" ? row.portfolioValueLabel : typeof row.portfolio_value_label === "string" ? row.portfolio_value_label : null,
      target_or_limit_label: typeof row.targetOrLimitLabel === "string" ? row.targetOrLimitLabel : typeof row.target_or_limit_label === "string" ? row.target_or_limit_label : null,
      status_label: typeof row.statusLabel === "string" ? row.statusLabel : typeof row.status_label === "string" ? row.status_label : "Not evaluated",
      status_tone: row.statusTone === "green" || row.statusTone === "amber" || row.statusTone === "red"
        ? row.statusTone
        : row.status_tone === "green" || row.status_tone === "amber" || row.status_tone === "red"
          ? row.status_tone
          : "amber",
      explanation: typeof row.explanation === "string" ? row.explanation : null
    }))
  };
}

function compactClientFitForCloud(clientFit: ReviewSummary["clientFit"] | ComparisonResultSummaryClientFit | undefined) {
  if (!clientFit) return undefined;
  return {
    statusLabel: clientFit.status_label,
    statusTone: clientFit.status_tone,
    profileLabel: clientFit.profile_label ?? undefined,
    sourceQualityLabel: clientFit.source_quality_label ?? undefined,
    mainExplanation: clientFit.main_explanation ?? undefined,
    decisionBoundary: clientFit.decision_boundary,
    nextBestTest: clientFit.next_best_test ?? undefined,
    targetRows: (clientFit.target_rows ?? []).slice(0, 6).map((row) => ({
      dimensionLabel: row.dimension_label,
      portfolioValueLabel: row.portfolio_value_label ?? undefined,
      targetOrLimitLabel: row.target_or_limit_label ?? undefined,
      statusLabel: row.status_label,
      statusTone: row.status_tone,
      explanation: row.explanation ?? undefined
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
    builderSetup: compactBuilderSetupForCloud(reviewSummary.builderSetup)
  };
}

async function upsertReviewRowForUser(userId: string, activeReview: ActiveReviewState) {
  const supabase = getSupabaseBrowserClient();
  if (!supabase) throw new Error("Cloud persistence is disabled.");
  if (!activeReview.reviewId || !activeReview.reviewSummary) {
    throw new Error("No completed diagnosis review is available for cloud persistence.");
  }

  const reviewSummary = activeReview.reviewSummary;
  const compactSummary = compactCloudRecord(compactReviewSummaryForCloud(reviewSummary, activeReview));
  const portfolioSnapshot = compactPortfolioSnapshot(activeReview.investorCurrency, activeReview.holdings);
  const portfolioVersion = activeReview.cloudPortfolio?.id
    ? await ensurePortfolioVersionForUser(userId, {
      portfolioId: activeReview.cloudPortfolio.id,
      investorCurrency: activeReview.investorCurrency,
      holdings: activeReview.holdings,
      sourceKind: "review",
      sourceReviewId: activeReview.reviewId
    })
    : null;
  const reviewPayload = {
    user_id: userId,
    portfolio_id: activeReview.cloudPortfolio?.id ?? null,
    portfolio_version_id: portfolioVersion?.id ?? activeReview.cloudPortfolio?.versionId ?? null,
    review_id: activeReview.reviewId,
    title: activeReview.cloudPortfolio?.name
      ? `${activeReview.cloudPortfolio.name} diagnosis`
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
  const reviewRowId = (reviewRow as { id: string }).id;
  if (activeReview.cloudPortfolio?.id) {
    await upsertWorkspaceStateForUser(userId, {
      activePortfolioId: activeReview.cloudPortfolio.id,
      activePortfolioVersionId: portfolioVersion?.id ?? activeReview.cloudPortfolio.versionId,
      activeReviewRowId: reviewRowId,
      lastOpenedReviewRowId: reviewRowId,
      metadata: {
        source: "diagnosis_sync",
        reviewId: activeReview.reviewId,
        updatedAt: nowIso()
      }
    });
  }
  return reviewRowId;
}

function stagedStageStatusesForCloud(activeReview: ActiveReviewState) {
  const progress = activeReview.stagedProgress;
  if (!progress) return {};
  return Object.fromEntries(STAGED_REVIEW_STAGE_NAMES.map((stage) => [
    stage,
    progress.stages[stage]?.status ?? "pending"
  ]));
}

function compactStagedProgressForCloud(activeReview: ActiveReviewState) {
  const progress = activeReview.stagedProgress;
  if (!progress) return undefined;
  return compactCloudRecord({
    schemaVersion: progress.schemaVersion,
    reviewId: progress.reviewId,
    status: progress.status,
    currentStage: progress.currentStage,
    mode: progress.mode,
    stageStatuses: stagedStageStatusesForCloud(activeReview),
    providerStatus: progress.providerStatus,
    safeError: progress.safeError,
    warnings: progress.warnings,
    updatedAt: progress.updatedAt
  });
}

function buildStagedReviewCompactSummary(activeReview: ActiveReviewState) {
  const stagedProgress = compactStagedProgressForCloud(activeReview);
  const reviewSummary = activeReview.reviewSummary;
  return compactCloudRecord({
    reviewId: activeReview.reviewId,
    status: activeReview.stagedProgress?.status ?? activeReview.runStatus,
    mode: activeReview.stagedProgress?.mode ?? activeReview.runMode,
    currentStage: activeReview.stagedProgress?.currentStage,
    investorCurrency: activeReview.investorCurrency,
    holdingsCount: activeReview.holdings.length,
    totalWeight: activeReview.holdings.reduce((sum, holding) => sum + holding.weight, 0),
    cashWeight: activeReview.holdings.filter((holding) => holding.type === "cash").reduce((sum, holding) => sum + holding.weight, 0),
    diagnosisHeadline: reviewSummary?.diagnosis.headline,
    diagnosisStatus: reviewSummary?.diagnosis.status,
    evidenceQuality: reviewSummary?.diagnosis.evidenceQuality,
    clientFit: compactClientFitForCloud(reviewSummary?.clientFit),
    primaryProblem: reviewSummary?.primaryProblem,
    problemSeverity: reviewSummary?.problemSeverity,
    problemConfidence: reviewSummary?.problemConfidence,
    launchpadCardsCount: reviewSummary?.launchpadCardsCount,
    recommendedFirstTest: reviewSummary?.recommendedFirstTest,
    suggestedActionPaths: reviewSummary?.suggestedActionPaths,
    candidateLaunchpadAvailable: reviewSummary?.candidateLaunchpadAvailable,
    problemClassificationAvailable: reviewSummary?.problemClassificationAvailable,
    activeCloudPortfolioId: activeReview.cloudPortfolio?.id,
    activeCloudPortfolioName: activeReview.cloudPortfolio?.name,
    activeCloudPortfolioVersionId: activeReview.portfolioVersionId ?? activeReview.cloudPortfolio?.versionId,
    activeCloudPortfolioVersionNumber: activeReview.portfolioVersionNumber ?? activeReview.cloudPortfolio?.versionNumber,
    lineageAvailable: Boolean(activeReview.lineageAvailable),
    readOnlyHistory: Boolean(activeReview.readOnlyHistory),
    stagedProgress
  });
}

async function upsertStagedReviewRowForUser(userId: string, activeReview: ActiveReviewState) {
  const supabase = getSupabaseBrowserClient();
  if (!supabase) throw new Error("Cloud persistence is disabled.");
  if (!activeReview.reviewId || !activeReview.stagedProgress) {
    throw new Error("No staged review progress is available for cloud persistence.");
  }

  const progress = activeReview.stagedProgress;
  const compactSummary = buildStagedReviewCompactSummary(activeReview);
  const portfolioSnapshot = compactPortfolioSnapshot(activeReview.investorCurrency, activeReview.holdings);
  const portfolioVersion = activeReview.cloudPortfolio?.id
    ? await ensurePortfolioVersionForUser(userId, {
      portfolioId: activeReview.cloudPortfolio.id,
      investorCurrency: activeReview.investorCurrency,
      holdings: activeReview.holdings,
      sourceKind: "draft",
      sourceReviewId: activeReview.reviewId
    })
    : null;
  const completedAt = progress.status === "completed" || progress.status === "failed"
    ? progress.updatedAt ?? nowIso()
    : null;
  const reviewPayload = {
    user_id: userId,
    portfolio_id: activeReview.cloudPortfolio?.id ?? null,
    portfolio_version_id: portfolioVersion?.id ?? activeReview.cloudPortfolio?.versionId ?? null,
    review_id: activeReview.reviewId,
    title: activeReview.cloudPortfolio?.name
      ? `${activeReview.cloudPortfolio.name} staged review`
      : `Portfolio MRI staged review ${activeReview.reviewId}`,
    mode: progress.mode,
    status: progress.status,
    portfolio_snapshot: portfolioSnapshot,
    compact_summary: compactSummary,
    started_at: progress.updatedAt ?? activeReview.updatedAt,
    completed_at: completedAt
  };

  const { data: reviewRow, error: reviewError } = await supabase
    .from("reviews")
    .upsert(reviewPayload, { onConflict: "user_id,review_id" })
    .select("id")
    .single();

  if (reviewError) throw reviewError;
  const reviewRowId = (reviewRow as { id: string }).id;
  if (activeReview.cloudPortfolio?.id) {
    await upsertWorkspaceStateForUser(userId, {
      activePortfolioId: activeReview.cloudPortfolio.id,
      activePortfolioVersionId: portfolioVersion?.id ?? activeReview.cloudPortfolio.versionId,
      activeReviewRowId: reviewRowId,
      lastOpenedReviewRowId: reviewRowId,
      metadata: {
        source: "staged_progress_sync",
        reviewId: activeReview.reviewId,
        updatedAt: nowIso()
      }
    });
  }
  return reviewRowId;
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
  const cloudSummary = compactCloudRecord(summary);
  const summarySizeBytes = estimateJsonBytes(cloudSummary);
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
      summary: cloudSummary,
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
    clientFit: compactClientFitForCloud(activeReview.comparisonResult.clientFit ?? activeReview.reviewSummary?.clientFit),
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
    clientFit: compactClientFitForCloud(activeReview.verdictResult.clientFit ?? activeReview.reviewSummary?.clientFit),
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
    clientFit: compactClientFitForCloud(activeReview.reportResult.clientFit ?? activeReview.reviewSummary?.clientFit),
    selectedCardId: activeReview.reportResult.selectedCardId,
    candidateId: activeReview.reportResult.candidateId
  };
}

function buildStagedStageSummary(activeReview: ActiveReviewState, stage: ReviewStageName) {
  const progress = activeReview.stagedProgress;
  const row = progress?.stages[stage];
  if (!progress || !row) return null;
  return {
    stage,
    status: row.status ?? "pending",
    reviewId: progress.reviewId,
    currentStage: progress.currentStage,
    mode: progress.mode,
    startedAt: row.started_at,
    completedAt: row.completed_at,
    providerStatus: progress.providerStatus,
    safeError: progress.safeError?.stage === stage ? progress.safeError : undefined,
    warnings: progress.warnings,
    updatedAt: progress.updatedAt
  };
}

export async function persistStagedProgressForReview(userId: string, activeReview: ActiveReviewState): Promise<StagePersistenceResult> {
  if (!activeReview.reviewId || !activeReview.stagedProgress) {
    throw new Error("No staged review progress is available for cloud persistence.");
  }

  const reviewRowId = await upsertStagedReviewRowForUser(userId, activeReview);
  const persisted: ReviewStageName[] = [];
  const skipped: StagePersistenceResult["skipped"] = [];

  for (const stage of STAGED_REVIEW_STAGE_NAMES) {
    const status = activeReview.stagedProgress.stages[stage]?.status ?? "pending";
    if (status === "pending") continue;
    const summary = buildStagedStageSummary(activeReview, stage);
    if (!summary) continue;
    const result = await upsertStageSummaryForReview({
      userId,
      reviewRowId,
      reviewId: activeReview.reviewId,
      stage,
      status,
      summary
    });
    if (result.persisted) persisted.push(stage);
    else skipped.push({ stage, summarySizeBytes: result.summarySizeBytes, reason: result.reason });
  }

  return { persisted, skipped };
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
    { stage: "builder", status: activeReview.builderSetup ? "completed" : "missing", summary: buildBuilderStageSummary(activeReview) },
    { stage: "candidate", status: activeReview.candidateGeneration?.status ?? "missing", summary: buildCandidateStageSummary(activeReview) },
    { stage: "comparison", status: activeReview.comparisonResult?.status ?? "missing", summary: buildComparisonStageSummary(activeReview) },
    { stage: "verdict", status: activeReview.verdictResult?.status ?? "missing", summary: buildVerdictStageSummary(activeReview) },
    { stage: "report", status: activeReview.reportResult?.status ?? "missing", summary: buildReportStageSummary(activeReview) }
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
        confidence: Number.isFinite(confidenceNumber) ? confidenceNumber : null,
        rationale: activeReview.verdictResult.explanation,
        summary: compactCloudRecord(activeReview.verdictResult),
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
  const [workspaceState, setWorkspaceState] = useState<WorkspaceStateRecord | null>(null);
  const [portfoliosLoading, setPortfoliosLoading] = useState(false);
  const [reviewsLoading, setReviewsLoading] = useState(false);
  const [workspaceLoading, setWorkspaceLoading] = useState(false);
  const [notice, setNoticeState] = useState<CloudNotice | null>(null);
  const signedIn = enabled && status === "signed_in" && Boolean(user?.id);

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
    if (!signedIn || !user?.id) {
      setSavedPortfolios([]);
      return;
    }

    setPortfoliosLoading(true);
    try {
      const portfolios = await fetchSavedPortfoliosForUser(user.id);
      setSavedPortfolios(portfolios);
    } catch (error) {
      console.warn("Could not load saved portfolios.", humanizePersistenceError(error));
    } finally {
      setPortfoliosLoading(false);
    }
  }, [setNotice, signedIn, user?.id]);

  const refreshSavedReviews = useCallback(async () => {
    if (!signedIn || !user?.id) {
      setSavedReviews([]);
      return;
    }

    setReviewsLoading(true);
    try {
      const reviews = await fetchSavedReviewsForUser(user.id);
      setSavedReviews(reviews);
    } catch (error) {
      console.warn("Could not load saved reviews.", humanizePersistenceError(error));
    } finally {
      setReviewsLoading(false);
    }
  }, [setNotice, signedIn, user?.id]);

  const refreshWorkspaceState = useCallback(async () => {
    if (!signedIn || !user?.id) {
      setWorkspaceState(null);
      return;
    }

    setWorkspaceLoading(true);
    try {
      const workspace = await fetchWorkspaceStateForUser(user.id);
      setWorkspaceState(workspace);
    } catch (error) {
      console.warn("Could not load the latest workspace.", humanizePersistenceError(error));
    } finally {
      setWorkspaceLoading(false);
    }
  }, [setNotice, signedIn, user?.id]);

  const savePortfolio = useCallback(async (input: SavePortfolioInput) => {
    if (!signedIn || !user?.id) {
      setNotice("warning", "Sign in first to save portfolios to your workspace.");
      return null;
    }

    try {
      const saved = await savePortfolioRecordForUser(user.id, input);
      const portfolios = await fetchSavedPortfoliosForUser(user.id);
      setSavedPortfolios(portfolios);
      const workspace = await upsertWorkspaceStateForUser(user.id, {
        activePortfolioId: saved.id,
        activePortfolioVersionId: saved.latestVersionId,
        activeReviewRowId: workspaceState?.activeReviewRowId,
        lastOpenedReviewRowId: workspaceState?.lastOpenedReviewRowId,
        metadata: {
          source: "portfolio_save",
          updatedAt: nowIso()
        }
      });
      setWorkspaceState(workspace);
      setNotice("success", `Saved "${saved.name}" to your workspace.`);
      return saved;
    } catch (error) {
      setNotice("warning", `We could not save this portfolio. ${humanizePersistenceError(error)}`);
      return null;
    }
  }, [setNotice, signedIn, user?.id, workspaceState?.activeReviewRowId, workspaceState?.lastOpenedReviewRowId]);

  const ensurePortfolioVersion = useCallback(async (input: { portfolioId: string; portfolioName?: string; investorCurrency: string; holdings: ReviewHolding[]; sourceKind?: string; sourceReviewId?: string }) => {
    if (!signedIn || !user?.id) {
      setNotice("warning", "Sign in first to save portfolio changes to your workspace.");
      return null;
    }

    try {
      const version = await ensurePortfolioVersionForUser(user.id, input);
      const draftReview = input.sourceKind === "draft"
        ? await upsertDraftReviewForPortfolioVersion(user.id, input, version)
        : null;
      const workspace = await upsertWorkspaceStateForUser(user.id, {
        activePortfolioId: input.portfolioId,
        activePortfolioVersionId: version.id,
        activeReviewRowId: draftReview?.reviewRowId ?? workspaceState?.activeReviewRowId,
        lastOpenedReviewRowId: draftReview?.reviewRowId ?? workspaceState?.lastOpenedReviewRowId,
        metadata: {
          source: input.sourceKind || "manual",
          draftReviewId: draftReview?.draftReviewId,
          updatedAt: nowIso()
        }
      });
      setWorkspaceState(workspace);
      const portfolios = await fetchSavedPortfoliosForUser(user.id);
      setSavedPortfolios(portfolios);
      if (draftReview) {
        const reviews = await fetchSavedReviewsForUser(user.id);
        setSavedReviews(reviews);
      }
      return version;
    } catch (error) {
      setNotice("warning", `We could not save this portfolio version. ${humanizePersistenceError(error)}`);
      return null;
    }
  }, [setNotice, signedIn, user?.id, workspaceState?.activeReviewRowId, workspaceState?.lastOpenedReviewRowId]);

  const deletePortfolio = useCallback(async (portfolioId: string) => {
    if (!signedIn || !user?.id) {
      setNotice("warning", "Sign in first to archive saved portfolios.");
      return false;
    }

    try {
      const portfolioName = savedPortfolios.find((item) => item.id === portfolioId)?.name;
      await deletePortfolioForUser(user.id, portfolioId);
      const portfolios = await fetchSavedPortfoliosForUser(user.id);
      setSavedPortfolios(portfolios);
      if (workspaceState?.activePortfolioId === portfolioId) {
        const workspace = await upsertWorkspaceStateForUser(user.id, {
          activePortfolioId: undefined,
          activePortfolioVersionId: undefined,
          activeReviewRowId: workspaceState.activeReviewRowId,
          lastOpenedReviewRowId: workspaceState.lastOpenedReviewRowId,
          metadata: {
            source: "portfolio_archive",
            updatedAt: nowIso()
          }
        });
        setWorkspaceState(workspace);
      }
      setNotice("success", portfolioName ? `Archived "${portfolioName}".` : "Archived saved portfolio.");
      return true;
    } catch (error) {
      setNotice("warning", `We could not archive this portfolio. ${humanizePersistenceError(error)}`);
      return false;
    }
  }, [savedPortfolios, setNotice, signedIn, user?.id, workspaceState?.activePortfolioId, workspaceState?.activeReviewRowId, workspaceState?.lastOpenedReviewRowId]);

  const archiveReview = useCallback(async (reviewRowId: string) => {
    if (!signedIn || !user?.id) {
      setNotice("warning", "Sign in first to archive saved reviews.");
      return false;
    }

    try {
      const review = savedReviews.find((item) => item.id === reviewRowId);
      await archiveReviewForUser(user.id, reviewRowId);
      const reviews = await fetchSavedReviewsForUser(user.id);
      setSavedReviews(reviews);
      if (workspaceState?.activeReviewRowId === reviewRowId || workspaceState?.lastOpenedReviewRowId === reviewRowId) {
        const workspace = await upsertWorkspaceStateForUser(user.id, {
          activePortfolioId: workspaceState.activePortfolioId,
          activePortfolioVersionId: workspaceState.activePortfolioVersionId,
          activeReviewRowId: workspaceState.activeReviewRowId === reviewRowId ? undefined : workspaceState.activeReviewRowId,
          lastOpenedReviewRowId: workspaceState.lastOpenedReviewRowId === reviewRowId ? undefined : workspaceState.lastOpenedReviewRowId,
          metadata: {
            source: "review_archive",
            updatedAt: nowIso()
          }
        });
        setWorkspaceState(workspace);
      }
      setNotice("success", review?.title ? `Archived "${review.title}".` : "Archived saved review.");
      return true;
    } catch (error) {
      setNotice("warning", `We could not archive this review. ${humanizePersistenceError(error)}`);
      return false;
    }
  }, [savedReviews, setNotice, signedIn, user?.id, workspaceState]);

  useEffect(() => {
    if (!signedIn || !user?.id) {
      setSavedPortfolios([]);
      setSavedReviews([]);
      setWorkspaceState(null);
      setPortfoliosLoading(false);
      setReviewsLoading(false);
      setWorkspaceLoading(false);
      return;
    }
    void refreshSavedPortfolios();
    void refreshSavedReviews();
    void refreshWorkspaceState();
  }, [refreshSavedPortfolios, refreshSavedReviews, refreshWorkspaceState, signedIn, user?.id]);

  const value = useMemo<SupabasePersistenceContextValue>(() => ({
    enabled,
    signedIn,
    userId: user?.id ?? null,
    savedPortfolios,
    savedReviews,
    workspaceState,
    portfoliosLoading,
    reviewsLoading,
    workspaceLoading,
    notice,
    clearNotice,
    setNotice,
    refreshSavedPortfolios,
    refreshSavedReviews,
    refreshWorkspaceState,
    savePortfolio,
    ensurePortfolioVersion,
    deletePortfolio,
    archiveReview
  }), [archiveReview, clearNotice, deletePortfolio, enabled, ensurePortfolioVersion, notice, portfoliosLoading, refreshSavedPortfolios, refreshSavedReviews, refreshWorkspaceState, reviewsLoading, savePortfolio, savedPortfolios, savedReviews, setNotice, signedIn, user?.id, workspaceLoading, workspaceState]);

  return <SupabasePersistenceContext.Provider value={value}>{children}</SupabasePersistenceContext.Provider>;
}

export function useSupabasePersistence() {
  const context = useContext(SupabasePersistenceContext);
  if (!context) {
    throw new Error("useSupabasePersistence must be used within SupabasePersistenceProvider");
  }
  return context;
}
