"use client";

import { useEffect, useMemo, useRef, useState } from "react";
import { createPortal } from "react-dom";
import { useRouter } from "next/navigation";
import type { Holding } from "@/lib/types";
import { StatusBadge } from "@/components/ui/StatusBadge";
import { instrumentByTicker, instrumentUniverse, type Instrument } from "@/data/instrumentUniverse";
import { diagnosisStageChainReady, useReviewState, type ReviewHolding, type ReviewResult, type StagedReviewProgress } from "@/lib/reviewState";
import type { ClientFitInput, StagedReviewStartedResponse, StagedReviewStatusResponse } from "@/lib/generated/api-types";
import { inferClientFitPresetIdFromTargets } from "@/lib/onboarding";
import { useSupabaseAuth } from "@/lib/supabase/auth";
import { useSupabasePersistence } from "@/lib/supabase/persistence";

type PortfolioInputTableProps = {
  investorCurrency: string;
  holdings: Holding[];
};

type EditableHolding = Holding & {
  id: string;
  weightInput: string;
};

type ValidationSummary = {
  title: string;
  text: string;
  tone: "green" | "amber" | "red";
};

const currencies = ["USD", "EUR"];
const WEIGHT_TOLERANCE = 0.01;
const MIN_VALID_HOLDINGS = 2;
const STAGED_POLL_INTERVAL_MS = 1200;
const STAGED_POLL_TIMEOUT_MS = 10 * 60 * 1000;
const DEFAULT_CLIENT_FIT_PROFILE: ClientFitInput = {
  preset_id: "balanced",
  source: "questionnaire",
  source_quality: "medium",
  source_quality_reason: "Default balanced planning profile prepared before portfolio diagnosis.",
  horizon_years: 7,
  target_return_range: { min: 0.05, max: 0.07 },
  target_vol_range: { min: 0.07, max: 0.10 },
  target_max_drawdown_pct: -0.20
};

function normalizeTicker(value: string) {
  return value.trim().toUpperCase();
}

function isCashTicker(ticker: string) {
  return instrumentByTicker.get(normalizeTicker(ticker))?.kind === "cash";
}


function displayTicker(row: Pick<EditableHolding, "ticker">) {
  return isCashTicker(row.ticker) ? "Cash" : row.ticker;
}

function displayInstrument(row: Pick<EditableHolding, "ticker" | "instrument">) {
  const ticker = normalizeTicker(row.ticker);
  const knownInstrument = instrumentByTicker.get(ticker);

  if (knownInstrument?.kind === "cash") {
    return `${knownInstrument.currency ?? "USD"} liquidity position`;
  }

  return knownInstrument?.instrument ?? row.instrument;
}

function toEditableHolding(holding: Holding, index: number): EditableHolding {
  const ticker = normalizeTicker(holding.ticker);
  const knownInstrument = instrumentByTicker.get(ticker);

  return {
    ...holding,
    ticker,
    instrument: knownInstrument?.instrument ?? holding.instrument,
    weightInput: String(holding.weight),
    id: `${ticker || "row"}-${index}-${Date.now()}`
  };
}

function createBlankHolding(id = `holding-${Date.now()}`): EditableHolding {
  return {
    id,
    ticker: "",
    instrument: "",
    weight: Number.NaN,
    weightInput: ""
  };
}

function reviewHoldingToEditable(holding: ReviewHolding, index: number): EditableHolding {
  return {
    id: holding.id || `${holding.ticker || "row"}-${index}-${Date.now()}`,
    ticker: normalizeTicker(holding.ticker),
    instrument: holding.instrument,
    weight: holding.weight,
    weightInput: String(holding.weight)
  };
}

function parseWeightInput(value: string) {
  const trimmed = value.trim();
  if (trimmed === "") return null;

  const parsed = Number(trimmed.replace(",", "."));
  return Number.isFinite(parsed) && parsed >= 0 ? parsed : null;
}

function cleanWeightInput(value: string) {
  let cleaned = value.replace(/[^\d.,]/g, "");
  const firstSeparator = cleaned.search(/[.,]/);

  if (firstSeparator >= 0) {
    const before = cleaned.slice(0, firstSeparator + 1);
    const after = cleaned.slice(firstSeparator + 1).replace(/[.,]/g, "");
    cleaned = `${before}${after}`;
  }

  return cleaned;
}

function formatWeight(value: number) {
  return Number.isFinite(value) ? value.toFixed(2).replace(/\?.0+$/, "") : "0";
}

function formatTotalWeight(value: number) {
  return Math.abs(value - 100) <= WEIGHT_TOLERANCE ? "100" : formatWeight(value);
}

function sleep(ms: number) {
  return new Promise((resolve) => window.setTimeout(resolve, ms));
}

function stagedStatusLabel(progress: StagedReviewProgress | null | undefined) {
  if (!progress) return "No active staged review";
  const currentStage = progress.currentStage || "input";
  const status = progress.status || "pending";
  return `${currentStage}: ${status}`;
}

function pctRangeLabel(range: { min: number; max: number } | null | undefined) {
  if (!range) return "Not set";
  return `${formatWeight(range.min * 100)}-${formatWeight(range.max * 100)}%`;
}

function drawdownLabel(value: number | null | undefined) {
  return typeof value === "number" && Number.isFinite(value) ? `${formatWeight(value * 100)}%` : "Not set";
}

function pctInputFromDecimal(value: number | null | undefined, fallback: number) {
  const numeric = typeof value === "number" && Number.isFinite(value) ? value : fallback;
  return formatWeight(Math.abs(numeric * 100));
}

function decimalFromPctInput(value: string) {
  const parsed = Number(value.trim().replace(",", "."));
  return Number.isFinite(parsed) ? parsed / 100 : Number.NaN;
}

function profileLabel(value: string | null | undefined) {
  if (!value) return "Custom profile";
  return value.split("_").map((part) => part ? `${part[0].toUpperCase()}${part.slice(1)}` : part).join(" ");
}

function isKnownInstrument(row: EditableHolding) {
  return instrumentByTicker.has(normalizeTicker(row.ticker));
}

function isValidWeight(row: EditableHolding) {
  const parsed = parseWeightInput(row.weightInput);
  return parsed !== null && parsed > 0;
}

function parsedWeightOrZero(row: EditableHolding) {
  const parsed = parseWeightInput(row.weightInput);
  return parsed !== null && parsed > 0 ? parsed : 0;
}

function rowToReviewHolding(row: EditableHolding): ReviewHolding | null {
  const ticker = normalizeTicker(row.ticker);
  const parsedWeight = parseWeightInput(row.weightInput);
  const instrument = instrumentByTicker.get(ticker);

  if (!ticker || parsedWeight === null || !Number.isFinite(parsedWeight)) return null;

  return {
    id: row.id,
    label: instrument?.kind === "cash" ? "Cash" : ticker,
    ticker,
    instrument: displayInstrument(row),
    weight: parsedWeight,
    type: instrument?.kind === "cash" ? "cash" : "instrument",
    currency: instrument?.kind === "cash" ? instrument.currency : undefined
  };
}

function reviewHoldingToPayload(holding: ReviewHolding) {
  if (holding.type === "cash") {
    return {
      type: "cash",
      currency: holding.currency || "USD",
      weight: holding.weight
    };
  }

  return {
    type: "instrument",
    ticker: normalizeTicker(holding.ticker),
    weight: holding.weight
  };
}

function recoveredHoldingToReviewHolding(value: unknown, index: number): ReviewHolding | null {
  if (!value || typeof value !== "object" || Array.isArray(value)) return null;
  const row = value as Record<string, unknown>;
  const weight = typeof row.weight === "number" && Number.isFinite(row.weight) ? row.weight : Number.NaN;
  if (!(weight > 0)) return null;

  if (row.type === "cash") {
    const currency = typeof row.currency === "string" && row.currency.trim() ? row.currency.trim().toUpperCase() : "USD";
    const ticker = getCashTicker(currency);
    const instrument = instrumentByTicker.get(ticker);
    return {
      id: `${ticker}-${index}`,
      label: "Cash",
      ticker,
      instrument: instrument?.instrument ?? `${currency} liquidity position`,
      weight,
      type: "cash",
      currency
    };
  }

  const ticker = typeof row.ticker === "string" ? normalizeTicker(row.ticker) : "";
  if (!ticker) return null;
  const instrument = instrumentByTicker.get(ticker);

  return {
    id: `${ticker}-${index}`,
    label: ticker,
    ticker,
    instrument: instrument?.instrument ?? ticker,
    weight,
    type: "instrument"
  };
}

function holdingsFromRecoveredReview(result: ReviewResult): ReviewHolding[] {
  const portfolioInput = result.portfolio_input;
  if (!portfolioInput || typeof portfolioInput !== "object" || Array.isArray(portfolioInput)) return [];
  const holdings = (portfolioInput as Record<string, unknown>).holdings;
  if (!Array.isArray(holdings)) return [];
  return holdings
    .map(recoveredHoldingToReviewHolding)
    .filter((holding): holding is ReviewHolding => Boolean(holding));
}

function currencyFromRecoveredReview(result: ReviewResult) {
  const portfolioInput = result.portfolio_input;
  if (!portfolioInput || typeof portfolioInput !== "object" || Array.isArray(portfolioInput)) return "USD";
  const currency = (portfolioInput as Record<string, unknown>).investor_currency;
  return typeof currency === "string" && currency.trim() ? currency.trim().toUpperCase() : "USD";
}

function getCashTicker(currency: string) {
  const ticker = `CASH_${currency || "USD"}`;
  return instrumentByTicker.has(ticker) ? ticker : "CASH_USD";
}

function duplicateTickers(rows: EditableHolding[]) {
  const counts = new Map<string, number>();

  rows.forEach((row) => {
    const ticker = normalizeTicker(row.ticker);
    if (!ticker) return;
    counts.set(ticker, (counts.get(ticker) ?? 0) + 1);
  });

  return new Set(Array.from(counts.entries()).filter(([, count]) => count > 1).map(([ticker]) => ticker));
}

function matchesInstrument(item: Instrument, query: string) {
  const normalizedQuery = query.trim().toLowerCase();
  if (!normalizedQuery) return true;

  return [item.ticker, item.instrument, item.currency, ...(item.searchTerms ?? [])]
    .filter(Boolean)
    .some((value) => String(value).toLowerCase().includes(normalizedQuery));
}

function instrumentMatchRank(item: Instrument, query: string) {
  const normalizedQuery = query.trim().toLowerCase();
  if (!normalizedQuery) return item.kind === "cash" ? 0 : item.kind === "fund" ? 1 : 2;

  const ticker = item.ticker.toLowerCase();
  const instrument = item.instrument.toLowerCase();
  if (ticker === normalizedQuery) return 0;
  if (ticker.startsWith(normalizedQuery)) return 1;
  if (instrument.startsWith(normalizedQuery)) return 2;
  if (ticker.includes(normalizedQuery)) return 3;
  if (instrument.includes(normalizedQuery)) return 4;
  return 5;
}

function instrumentKindLabel(item: Instrument) {
  if (item.kind === "cash") return item.currency ?? "Cash";
  if (item.kind === "stock") return "Stock";
  return "ETF";
}

function SimilarExposureWarning({ rows }: { rows: EditableHolding[] }) {
  const tickers = new Set(rows.map((row) => normalizeTicker(row.ticker)));
  const hasSpyAndVoo = tickers.has("SPY") && tickers.has("VOO");

  if (!hasSpyAndVoo) return null;

  return (
    <p className="mt-3 rounded-xl border border-pmri-amber/35 bg-pmri-amber/10 px-4 py-3 text-sm leading-6 text-pmri-text2">
      SPY and VOO are separate tickers, but they may represent very similar U.S. large-cap exposure.
    </p>
  );
}

function InstrumentCombobox({
  row,
  duplicateTicker,
  showValidationError,
  onSelect,
  onClearSelection
}: {
  row: EditableHolding;
  duplicateTicker: boolean;
  showValidationError: boolean;
  onSelect: (instrument: Instrument) => void;
  onClearSelection: () => void;
}) {
  const [query, setQuery] = useState(displayTicker(row));
  const [open, setOpen] = useState(false);
  const [activeIndex, setActiveIndex] = useState(0);
  const [queryEditedSinceOpen, setQueryEditedSinceOpen] = useState(false);
  const closeTimer = useRef<ReturnType<typeof setTimeout> | null>(null);
  const inputRef = useRef<HTMLInputElement | null>(null);
  const [dropdownStyle, setDropdownStyle] = useState<{ left: number; top: number; width: number } | null>(null);

  useEffect(() => {
    if (row.ticker) setQuery(displayTicker(row));
  }, [row.ticker]);

  const effectiveQuery = open && !queryEditedSinceOpen && query === displayTicker(row) ? "" : query;

  const matches = useMemo(() => {
    return instrumentUniverse
      .filter((item) => matchesInstrument(item, effectiveQuery))
      .sort((a, b) => {
        const rankDelta = instrumentMatchRank(a, effectiveQuery) - instrumentMatchRank(b, effectiveQuery);
        if (rankDelta !== 0) return rankDelta;
        return a.ticker.localeCompare(b.ticker);
      });
  }, [effectiveQuery]);

  const updateDropdownPosition = () => {
    const rect = inputRef.current?.getBoundingClientRect();
    if (!rect) return;

    setDropdownStyle({
      left: rect.left,
      top: rect.bottom + 8,
      width: rect.width
    });
  };

  useEffect(() => {
    if (!open) return;

    updateDropdownPosition();
    window.addEventListener("scroll", updateDropdownPosition, true);
    window.addEventListener("resize", updateDropdownPosition);

    return () => {
      window.removeEventListener("scroll", updateDropdownPosition, true);
      window.removeEventListener("resize", updateDropdownPosition);
    };
  }, [open, query]);

  const selectInstrument = (item: Instrument) => {
    if (closeTimer.current) clearTimeout(closeTimer.current);
    onSelect(item);
    setQuery(item.kind === "cash" ? "Cash" : item.ticker);
    setQueryEditedSinceOpen(false);
    setOpen(false);
    setActiveIndex(0);
  };

  const handleQueryChange = (value: string) => {
    setQuery(value);
    setOpen(true);
    setQueryEditedSinceOpen(true);
    setActiveIndex(0);

    const exactTicker = instrumentByTicker.get(normalizeTicker(value));
    if (exactTicker) {
      onSelect(exactTicker);
    } else {
      onClearSelection();
    }
  };

  const instrumentMissing = !isKnownInstrument(row);
  const showMissingState = instrumentMissing && showValidationError;
  const showEmptyGuidance = instrumentMissing && !showValidationError;

  return (
    <div className="relative">
      <input
        ref={inputRef}
        className={`pmri-focus w-full rounded-xl border bg-pmri-secondary/80 px-3 py-2.5 text-sm font-medium text-pmri-text placeholder:text-pmri-muted/70 ${showMissingState ? "border-pmri-risk/55" : duplicateTicker ? "border-pmri-amber/55" : showEmptyGuidance ? "pmri-empty-field" : "border-pmri-border/55"}`}
        value={query}
        placeholder="Search ticker or name"
        onChange={(event) => handleQueryChange(event.target.value)}
        onFocus={() => {
          setOpen(true);
          setQueryEditedSinceOpen(false);
          updateDropdownPosition();
          window.setTimeout(() => inputRef.current?.select(), 0);
        }}
        onBlur={() => {
          closeTimer.current = setTimeout(() => setOpen(false), 120);
        }}
        onKeyDown={(event) => {
          if (!open && ["ArrowDown", "ArrowUp"].includes(event.key)) {
            setOpen(true);
            return;
          }

          if (event.key === "ArrowDown") {
            event.preventDefault();
            setActiveIndex((current) => Math.min(current + 1, Math.max(0, matches.length - 1)));
          }

          if (event.key === "ArrowUp") {
            event.preventDefault();
            setActiveIndex((current) => Math.max(current - 1, 0));
          }

          if (event.key === "Enter" && open && matches[activeIndex]) {
            event.preventDefault();
            selectInstrument(matches[activeIndex]);
          }

          if (event.key === "Escape") {
            setOpen(false);
          }
        }}
        role="combobox"
        aria-expanded={open}
        aria-autocomplete="list"
        aria-invalid={showMissingState}
      />

      {open && dropdownStyle ? createPortal((
        <div
          className="fixed z-50 max-h-80 overflow-y-auto rounded-xl border border-pmri-border/55 bg-pmri-secondary shadow-2xl shadow-black/35"
          style={{ left: dropdownStyle.left, top: dropdownStyle.top, width: dropdownStyle.width }}
        >
          <div className="sticky top-0 z-10 border-b border-pmri-border/50 bg-pmri-secondary/95 px-3 py-2 text-xs text-pmri-text2 backdrop-blur">
            {matches.length} instruments available
          </div>
          {matches.length > 0 ? matches.map((item, index) => (
            <button
              key={item.ticker}
              type="button"
              className={`pmri-focus flex w-full items-start justify-between gap-3 px-3 py-3 text-left text-sm transition ${index === activeIndex ? "bg-pmri-blue/10" : "hover:bg-white/[0.045]"}`}
              onMouseDown={(event) => event.preventDefault()}
              onClick={() => selectInstrument(item)}
            >
              <span>
                <span className="block font-medium text-pmri-text">{item.kind === "cash" ? "Cash" : item.ticker}</span>
                <span className="mt-0.5 block text-xs leading-5 text-pmri-muted">
                  {item.kind === "cash" ? `${item.currency ?? "USD"} liquidity position` : item.instrument}
                </span>
              </span>
              <span className="shrink-0 rounded-full border border-pmri-border/55 px-2 py-0.5 text-xs font-medium tracking-[-0.005em] text-pmri-text2">
                {instrumentKindLabel(item)}
              </span>
            </button>
          )) : (
            <div className="px-3 py-3 text-sm text-pmri-muted">No matching instruments</div>
          )}
        </div>
      ), document.body) : null}
    </div>
  );
}

export function PortfolioInputTable({ investorCurrency, holdings }: PortfolioInputTableProps) {
  const router = useRouter();
  const { activeReview, hydrated, saveClientFitProfile, savePortfolioInput, submitPortfolioInput, startStagedReview, recordStagedProgress, recordReviewError, linkCloudPortfolio, loadCloudPortfolioInput } = useReviewState();
  const { enabled: cloudEnabled, status: authStatus } = useSupabaseAuth();
  const { savedPortfolios, portfoliosLoading, savePortfolio, deletePortfolio } = useSupabasePersistence();
  const [currency, setCurrency] = useState(investorCurrency || "");
  const [rows, setRows] = useState<EditableHolding[]>(() => (
    holdings.length ? holdings.map(toEditableHolding) : [createBlankHolding("starter-0")]
  ));
  const [intakeModalOpen, setIntakeModalOpen] = useState(false);
  const [intakeReturnMin, setIntakeReturnMin] = useState(pctInputFromDecimal(DEFAULT_CLIENT_FIT_PROFILE.target_return_range?.min, 0.05));
  const [intakeReturnMax, setIntakeReturnMax] = useState(pctInputFromDecimal(DEFAULT_CLIENT_FIT_PROFILE.target_return_range?.max, 0.07));
  const [intakeVolMin, setIntakeVolMin] = useState(pctInputFromDecimal(DEFAULT_CLIENT_FIT_PROFILE.target_vol_range?.min, 0.07));
  const [intakeVolMax, setIntakeVolMax] = useState(pctInputFromDecimal(DEFAULT_CLIENT_FIT_PROFILE.target_vol_range?.max, 0.10));
  const [intakeDrawdown, setIntakeDrawdown] = useState(pctInputFromDecimal(DEFAULT_CLIENT_FIT_PROFILE.target_max_drawdown_pct, -0.20));
  const [intakeHorizonYears, setIntakeHorizonYears] = useState(String(DEFAULT_CLIENT_FIT_PROFILE.horizon_years ?? 7));
  const [isRunningDiagnosis, setIsRunningDiagnosis] = useState(false);
  const [diagnosisError, setDiagnosisError] = useState<string | null>(null);
  const [recoverReviewId, setRecoverReviewId] = useState("");
  const [isRecoveringReview, setIsRecoveringReview] = useState(false);
  const [recoveryError, setRecoveryError] = useState<string | null>(null);
  const [cloudPortfolioName, setCloudPortfolioName] = useState("");
  const [cloudPortfolioDescription, setCloudPortfolioDescription] = useState("");
  const [isSavingPortfolio, setIsSavingPortfolio] = useState(false);
  const [activeCloudLoadId, setActiveCloudLoadId] = useState<string | null>(null);
  const [activeCloudDeleteId, setActiveCloudDeleteId] = useState<string | null>(null);
  const inputInitialized = useRef(false);
  const inputEdited = useRef(false);
  const stagedResumeRef = useRef<string | null>(null);

  useEffect(() => {
    if (!hydrated || inputInitialized.current) return;

    if (activeReview?.holdings.length) {
      setCurrency(activeReview.investorCurrency);
      setRows(activeReview.holdings.map(reviewHoldingToEditable));
    }
    inputInitialized.current = true;
  }, [activeReview, hydrated]);

  useEffect(() => {
    if (activeReview?.cloudPortfolio?.name) {
      setCloudPortfolioName(activeReview.cloudPortfolio.name);
      return;
    }
    if (!cloudPortfolioName.trim()) {
      const dateLabel = new Date().toISOString().slice(0, 10);
      setCloudPortfolioName(`Portfolio ${dateLabel}`);
    }
  }, [activeReview?.cloudPortfolio?.name, cloudPortfolioName]);

  useEffect(() => {
    if (!intakeModalOpen) return;
    const profile = activeReview?.clientFitProfile ?? DEFAULT_CLIENT_FIT_PROFILE;
    setIntakeReturnMin(pctInputFromDecimal(profile.target_return_range?.min, DEFAULT_CLIENT_FIT_PROFILE.target_return_range?.min ?? 0.05));
    setIntakeReturnMax(pctInputFromDecimal(profile.target_return_range?.max, DEFAULT_CLIENT_FIT_PROFILE.target_return_range?.max ?? 0.07));
    setIntakeVolMin(pctInputFromDecimal(profile.target_vol_range?.min, DEFAULT_CLIENT_FIT_PROFILE.target_vol_range?.min ?? 0.07));
    setIntakeVolMax(pctInputFromDecimal(profile.target_vol_range?.max, DEFAULT_CLIENT_FIT_PROFILE.target_vol_range?.max ?? 0.10));
    setIntakeDrawdown(pctInputFromDecimal(profile.target_max_drawdown_pct, DEFAULT_CLIENT_FIT_PROFILE.target_max_drawdown_pct ?? -0.20));
    setIntakeHorizonYears(String(profile.horizon_years ?? DEFAULT_CLIENT_FIT_PROFILE.horizon_years ?? 7));
  }, [activeReview?.clientFitProfile, intakeModalOpen]);

  useEffect(() => {
    if (!hydrated || !inputEdited.current) return;

    savePortfolioInput({
      investorCurrency: currency || "USD",
      holdings: rows
        .map(rowToReviewHolding)
        .filter((holding): holding is ReviewHolding => Boolean(holding))
    });
  }, [currency, hydrated, rows, savePortfolioInput]);

  const totalWeight = useMemo(
    () => rows.reduce((sum, row) => sum + parsedWeightOrZero(row), 0),
    [rows]
  );

  const duplicateTickerSet = useMemo(() => duplicateTickers(rows), [rows]);
  const hasDuplicateTickers = duplicateTickerSet.size > 0;
  const validHoldingCount = rows.filter((row) => isKnownInstrument(row) && isValidWeight(row)).length;
  const hasStartedPortfolio = rows.some((row) => normalizeTicker(row.ticker) || row.weightInput.trim());
  const instrumentsComplete = rows.length > 0 && rows.every(isKnownInstrument);
  const weightsComplete = rows.length > 0 && rows.every(isValidWeight);
  const weightsAddTo100 = Math.abs(totalWeight - 100) <= WEIGHT_TOLERANCE;
  const clientProfileReady = Boolean(activeReview?.clientFitProfile);

  const validationSummary: ValidationSummary = useMemo(() => {
    if (!clientProfileReady) {
      return {
        title: "Profile required",
        text: "Complete Client Profile before running the web diagnosis.",
        tone: "amber"
      };
    }

    if (!hasStartedPortfolio) {
      return {
        title: "Add current holdings",
        text: "Start with the assets you already hold. Select a ticker or cash position, then enter its weight.",
        tone: "amber"
      };
    }

    if (!instrumentsComplete) {
      return {
        title: "Select an instrument",
        text: "Choose a ticker or cash position before running diagnosis.",
        tone: "amber"
      };
    }

    if (!weightsComplete) {
      return {
        title: "Check weights",
        text: "Each position needs a weight greater than 0.",
        tone: "red"
      };
    }

    if (validHoldingCount < MIN_VALID_HOLDINGS) {
      return {
        title: "Add one more holding",
        text: `Diagnosis needs at least ${MIN_VALID_HOLDINGS} valid portfolio positions.`,
        tone: "amber"
      };
    }

    if (totalWeight < 100 - WEIGHT_TOLERANCE) {
      return {
        title: "Incomplete allocation",
        text: `You still need to allocate ${formatWeight(100 - totalWeight)}%.`,
        tone: "amber"
      };
    }

    if (totalWeight > 100 + WEIGHT_TOLERANCE) {
      return {
        title: "Allocation exceeds 100%",
        text: `Reduce allocation by ${formatWeight(totalWeight - 100)}%.`,
        tone: "red"
      };
    }

    return {
      title: "Ready for diagnosis",
      text: `${validHoldingCount} holdings · 100% allocated`,
      tone: "green"
    };
  }, [clientProfileReady, hasStartedPortfolio, instrumentsComplete, totalWeight, validHoldingCount, weightsComplete]);

  const ready = validHoldingCount >= MIN_VALID_HOLDINGS && instrumentsComplete && weightsComplete && weightsAddTo100 && clientProfileReady;
  const cloudReady = cloudEnabled && authStatus === "signed_in";
  const intakeValues = useMemo(() => {
    const returnMin = decimalFromPctInput(intakeReturnMin);
    const returnMax = decimalFromPctInput(intakeReturnMax);
    const volMin = decimalFromPctInput(intakeVolMin);
    const volMax = decimalFromPctInput(intakeVolMax);
    const drawdown = -Math.abs(decimalFromPctInput(intakeDrawdown));
    const horizonYears = Number(intakeHorizonYears.trim().replace(",", "."));
    const valid = returnMin >= 0
      && returnMax <= 1
      && returnMin < returnMax
      && volMin >= 0
      && volMax <= 1
      && volMin < volMax
      && drawdown <= 0
      && drawdown >= -1
      && Number.isFinite(horizonYears)
      && horizonYears > 0;
    return { returnMin, returnMax, volMin, volMax, drawdown, horizonYears, valid };
  }, [intakeDrawdown, intakeHorizonYears, intakeReturnMax, intakeReturnMin, intakeVolMax, intakeVolMin]);

  const saveAdjustedIntake = () => {
    if (!intakeValues.valid) return;
    const inferredPresetId = inferClientFitPresetIdFromTargets(intakeValues);
    saveClientFitProfile({
      preset_id: inferredPresetId,
      source: "manual_override",
      source_quality: "high",
      source_quality_reason: `Manual intake targets adjusted from the Portfolio Input screen; preset reclassified as ${profileLabel(inferredPresetId)} from the saved target ranges.`,
      horizon_years: intakeValues.horizonYears,
      target_return_range: { min: intakeValues.returnMin, max: intakeValues.returnMax },
      target_vol_range: { min: intakeValues.volMin, max: intakeValues.volMax },
      target_max_drawdown_pct: intakeValues.drawdown
    });
    setIntakeModalOpen(false);
  };

  const updateInstrument = (id: string, instrument: Instrument | null) => {
    inputEdited.current = true;
    setRows((currentRows) => currentRows.map((row) => {
      if (row.id !== id) return row;
      return {
        ...row,
        ticker: instrument?.ticker ?? "",
        instrument: instrument?.instrument ?? ""
      };
    }));
  };

  const updateWeight = (id: string, value: string) => {
    inputEdited.current = true;
    const cleanedValue = cleanWeightInput(value);
    const parsed = parseWeightInput(cleanedValue);

    setRows((currentRows) => currentRows.map((row) => (
      row.id === id ? { ...row, weightInput: cleanedValue, weight: parsed ?? Number.NaN } : row
    )));
  };

  const addHolding = () => {
    inputEdited.current = true;
    setRows((currentRows) => [...currentRows, createBlankHolding()]);
  };

  const addCashPosition = () => {
    inputEdited.current = true;
    const ticker = getCashTicker(currency);
    const cashInstrument = instrumentByTicker.get(ticker);

    setRows((currentRows) => [
      ...currentRows,
      {
        id: `cash-${Date.now()}`,
        ticker,
        instrument: cashInstrument?.instrument ?? `${currency || "USD"} liquidity position`,
        weight: Number.NaN,
        weightInput: ""
      }
    ]);
  };

  const removeRow = (id: string) => {
    inputEdited.current = true;
    setRows((currentRows) => currentRows.filter((row) => row.id !== id));
  };

  const pollStagedDiagnosis = async (reviewId: string) => {
    const startedAt = Date.now();

    while (Date.now() - startedAt < STAGED_POLL_TIMEOUT_MS) {
      const response = await fetch(`/api/portfolio/review/status?reviewId=${encodeURIComponent(reviewId)}`, {
        method: "GET",
        cache: "no-store"
      });
      const status = await response.json() as StagedReviewStatusResponse & { error?: string; details?: unknown };

      if (!response.ok) {
        const detailText = Array.isArray(status.details)
          ? status.details.filter((item) => typeof item === "string").join(" ")
          : "";
        throw new Error([status.error || "Staged review status failed.", detailText].filter(Boolean).join(" "));
      }

      recordStagedProgress(status);

      if (status.status === "failed" || status.safe_error) {
        const safeError = status.safe_error;
        const safeErrorMessage = safeError
          ? [
            safeError.message,
            safeError.code ? `Code: ${safeError.code}` : "",
            safeError.stage ? `Stage: ${safeError.stage}` : "",
            safeError.retryable ? "Retry after confirming the backend/frontend servers are freshly restarted." : ""
          ].filter(Boolean).join(" ")
          : "Portfolio diagnosis failed during staged execution.";
        throw new Error(safeErrorMessage);
      }

      if (diagnosisStageChainReady(status)) {
        return status;
      }

      await sleep(STAGED_POLL_INTERVAL_MS);
    }

    throw new Error("Portfolio diagnosis is still running. Keep the review ID and retry recovery after the backend finishes.");
  };

  const recoverCompletedDiagnosis = async (reviewId: string, fallbackHoldings: ReviewHolding[], fallbackCurrency: string) => {
    const response = await fetch("/api/portfolio/review/recover", {
      method: "POST",
      headers: {
        "Content-Type": "application/json"
      },
      body: JSON.stringify({ review_id: reviewId })
    });
    const result = await response.json() as { review_result?: ReviewResult; error?: string; details?: unknown };

    if (!response.ok || result.review_result?.status !== "completed") {
      const detailText = Array.isArray(result.details)
        ? result.details.filter((item) => typeof item === "string").join(" ")
        : typeof result.details === "string"
          ? result.details
          : "";
      throw new Error([result.error || "Review recovery failed.", detailText].filter(Boolean).join(" "));
    }

    const recoveredHoldings = holdingsFromRecoveredReview(result.review_result);
    const nextHoldings = recoveredHoldings.length ? recoveredHoldings : fallbackHoldings;
    if (!nextHoldings.length) {
      throw new Error("Review recovery found the run, but portfolio_input.holdings could not be restored.");
    }

    const recoveredCurrency = currencyFromRecoveredReview(result.review_result) || fallbackCurrency;
    inputEdited.current = false;
    setCurrency(recoveredCurrency);
    setRows(nextHoldings.map(reviewHoldingToEditable));
    submitPortfolioInput({
      investorCurrency: recoveredCurrency,
      holdings: nextHoldings,
      reviewResult: result.review_result
    });
  };

  const runPortfolioDiagnosis = async () => {
    if (!ready || isRunningDiagnosis) return;

    const reviewHoldings = rows
      .map(rowToReviewHolding)
      .filter((holding): holding is ReviewHolding => Boolean(holding));

    setDiagnosisError(null);
    setIsRunningDiagnosis(true);

    try {
      const response = await fetch("/api/portfolio/diagnose", {
        method: "POST",
        headers: {
          "Content-Type": "application/json"
        },
        body: JSON.stringify({
          investor_currency: currency || "USD",
          holdings: reviewHoldings.map(reviewHoldingToPayload),
          client_fit: activeReview?.clientFitProfile
        })
      });

      const responseText = await response.text();
      let result: StagedReviewStartedResponse & { error?: string; details?: unknown };
      try {
        result = responseText ? JSON.parse(responseText) as StagedReviewStartedResponse & { error?: string; details?: unknown } : { status: "failed", error: "Portfolio diagnosis failed." } as StagedReviewStartedResponse & { error?: string };
      } catch (_error) {
        result = {
          status: "failed",
          error: response.ok ? "Portfolio diagnosis returned an unreadable response." : `Portfolio diagnosis failed with HTTP ${response.status}.`,
          details: responseText.slice(0, 500)
        } as StagedReviewStartedResponse & { error?: string; details?: unknown };
      }

      if (!response.ok || !result.review_id || result.status === "failed") {
        const detailText = Array.isArray(result.details)
          ? result.details.filter((item) => typeof item === "string").join(" ")
          : typeof result.details === "string"
            ? result.details
            : "";
        const message = [result.error || "Portfolio diagnosis failed.", detailText].filter(Boolean).join(" ");
        recordReviewError({
          investorCurrency: currency || "USD",
          holdings: reviewHoldings,
          message,
          details: detailText
        });
        throw new Error(message);
      }

      startStagedReview({
        investorCurrency: currency || "USD",
        holdings: reviewHoldings,
        started: result
      });
      router.push("/diagnosis");
    } catch (error) {
      const message = error instanceof Error ? error.message : "Portfolio diagnosis failed.";
      setDiagnosisError(message);
      if (reviewHoldings.length) {
        recordReviewError({
          investorCurrency: currency || "USD",
          holdings: reviewHoldings,
          message
        });
      }
    } finally {
      setIsRunningDiagnosis(false);
    }
  };

  const saveCurrentPortfolioToCloud = async () => {
    if (!cloudReady || isSavingPortfolio) return;
    const reviewHoldings = rows
      .map(rowToReviewHolding)
      .filter((holding): holding is ReviewHolding => Boolean(holding));

    if (!reviewHoldings.length) return;

    setIsSavingPortfolio(true);
    try {
      const saved = await savePortfolio({
        portfolioId: activeReview?.cloudPortfolio?.id,
        name: cloudPortfolioName.trim(),
        description: cloudPortfolioDescription.trim(),
        investorCurrency: currency || "USD",
        holdings: reviewHoldings
      });

      if (saved) {
        linkCloudPortfolio({ id: saved.id, name: saved.name });
      }
    } finally {
      setIsSavingPortfolio(false);
    }
  };

  const loadSavedPortfolio = async (portfolioId: string) => {
    const saved = savedPortfolios.find((item) => item.id === portfolioId);
    if (!saved) return;
    setActiveCloudLoadId(portfolioId);
    try {
      inputEdited.current = false;
      setCurrency(saved.baseCurrency || "USD");
      setRows(saved.holdings.map(reviewHoldingToEditable));
      setDiagnosisError(null);
      setRecoveryError(null);
      loadCloudPortfolioInput({
        portfolioId: saved.id,
        name: saved.name,
        investorCurrency: saved.baseCurrency || "USD",
        holdings: saved.holdings
      });
      setCloudPortfolioName(saved.name);
      setCloudPortfolioDescription(saved.description ?? "");
    } finally {
      setActiveCloudLoadId(null);
    }
  };

  const deleteSavedPortfolioFromCloud = async (portfolioId: string) => {
    const saved = savedPortfolios.find((item) => item.id === portfolioId);
    if (!saved) return;
    if (typeof window !== "undefined" && !window.confirm(`Delete "${saved.name}" from optional cloud storage...`)) return;

    setActiveCloudDeleteId(portfolioId);
    try {
      const deleted = await deletePortfolio(portfolioId);
      if (deleted && activeReview?.cloudPortfolio?.id === portfolioId) {
        linkCloudPortfolio(undefined);
      }
    } finally {
      setActiveCloudDeleteId(null);
    }
  };

  const recoverActiveReview = async () => {
    const reviewId = recoverReviewId.trim();
    if (!reviewId || isRecoveringReview) return;

    setRecoveryError(null);
    setIsRecoveringReview(true);

    try {
      await recoverCompletedDiagnosis(reviewId, [], currency || "USD");
      router.push("/diagnosis");
    } catch (error) {
      setRecoveryError(error instanceof Error ? error.message : "Review recovery failed.");
    } finally {
      setIsRecoveringReview(false);
    }
  };

  useEffect(() => {
    if (!hydrated || isRunningDiagnosis || isRecoveringReview) return;
    const review = activeReview;
    const progress = review?.stagedProgress;
    const reviewId = progress?.reviewId;
    if (!reviewId || !review || review.reviewSummary) return;
    if (progress.status !== "running" && progress.status !== "partial") return;
    if (stagedResumeRef.current === reviewId) return;

    let cancelled = false;
    stagedResumeRef.current = reviewId;
    setIsRunningDiagnosis(true);
    setDiagnosisError(null);

    void (async () => {
      try {
        await pollStagedDiagnosis(reviewId);
        if (cancelled) return;
        await recoverCompletedDiagnosis(
          reviewId,
          review.holdings,
          review.investorCurrency || currency || "USD"
        );
        if (!cancelled) router.push("/diagnosis");
      } catch (error) {
        if (!cancelled) {
          setDiagnosisError(error instanceof Error ? error.message : "Staged review recovery failed.");
        }
      } finally {
        if (!cancelled) setIsRunningDiagnosis(false);
      }
    })();

    return () => {
      cancelled = true;
    };
  }, [activeReview, currency, hydrated, isRecoveringReview, isRunningDiagnosis, router]);

  const stagedProgress = activeReview?.stagedProgress;
  const diagnosisChainIsReady = diagnosisStageChainReady(stagedProgress);
  const showStagedProgress = Boolean(stagedProgress && (
    (isRunningDiagnosis && !diagnosisChainIsReady)
    || (!activeReview?.reviewSummary && !diagnosisChainIsReady && (
      stagedProgress.status === "running" || stagedProgress.status === "partial"
    ))
  ));

  return (
    <div className="space-y-5">
    <section className="pmri-card rounded-2xl p-5 md:p-6">
      <div className="flex flex-col gap-4 lg:flex-row lg:items-start lg:justify-between">
        <div>
          <p className="pmri-label">Client Fit profile</p>
          <h2 className="pmri-heading-section mt-2 text-lg text-pmri-text">
            {clientProfileReady ? profileLabel(activeReview?.clientFitProfile?.preset_id) : "Complete Client Profile before diagnosis"}
          </h2>
          <p className="mt-2 max-w-2xl text-sm leading-6 text-pmri-muted">
            The web journey runs diagnosis only after the planning profile is captured. These limits are used as display and hypothesis-test context, not optimizer instructions.
          </p>
          {activeReview?.clientFitProfile ? (
            <div className="mt-4 flex flex-wrap gap-2 text-xs text-pmri-text2">
              <span className="rounded-full border border-pmri-border/55 bg-white/[0.025] px-3 py-1.5">Return {pctRangeLabel(activeReview.clientFitProfile.target_return_range)}</span>
              <span className="rounded-full border border-pmri-border/55 bg-white/[0.025] px-3 py-1.5">Volatility {pctRangeLabel(activeReview.clientFitProfile.target_vol_range)}</span>
              <span className="rounded-full border border-pmri-border/55 bg-white/[0.025] px-3 py-1.5">Temporary loss {drawdownLabel(activeReview.clientFitProfile.target_max_drawdown_pct)}</span>
              <span className="rounded-full border border-pmri-border/55 bg-white/[0.025] px-3 py-1.5">Horizon {activeReview.clientFitProfile.horizon_years ?? "not set"} years</span>
            </div>
          ) : null}
        </div>
        <div className="flex shrink-0 flex-col items-start gap-3 sm:flex-row sm:items-center">
          <StatusBadge tone={clientProfileReady ? "green" : "amber"}>
            {clientProfileReady ? "Profile ready" : "Profile required"}
          </StatusBadge>
          <button
            type="button"
            onClick={() => setIntakeModalOpen(true)}
            className="pmri-focus rounded-full border border-pmri-border/60 bg-white/[0.025] px-4 py-2 text-sm font-medium text-pmri-text2 transition hover:border-pmri-blue/35 hover:text-pmri-text"
          >
            {clientProfileReady ? "Adjust intake" : "Create intake"}
          </button>
        </div>
      </div>
    </section>
    <section className="pmri-card overflow-hidden rounded-2xl">
      <div className="border-b border-pmri-border/45 p-5 md:p-6">
        <div className="flex flex-col gap-4 lg:flex-row lg:items-start lg:justify-between">
          <div className="max-w-2xl">
            <p className="pmri-label">Current allocation only</p>
            <p className="mt-2 text-sm leading-6 text-pmri-text2">
              Enter the portfolio you hold today. The diagnosis checks this allocation before any alternatives are compared.
            </p>
          </div>

          <label className="min-w-[240px]">
            <span className="pmri-label block">Investor currency</span>
            <select
              className="pmri-focus mt-2 w-full rounded-xl border border-pmri-border/55 bg-pmri-secondary/80 px-3 py-2.5 text-sm font-medium text-pmri-text"
              value={currency}
              onChange={(event) => {
                inputEdited.current = true;
                setCurrency(event.target.value);
              }}
            >
              <option value="">Select currency</option>
              {currencies.map((item) => <option key={item} value={item}>{item}</option>)}
            </select>
          </label>
        </div>
      </div>

      <div className="p-5 md:p-6">
        <div className="flex flex-col gap-3 md:flex-row md:items-center md:justify-between">
          <div>
            <h2 className="pmri-heading-section text-xl text-pmri-text">Holdings and weights</h2>
            <p className="mt-1 text-sm text-pmri-muted">
              Add only positions the client already holds. Search by ticker or name, then enter each weight as a percent.
            </p>
          </div>
          <div className="flex flex-wrap gap-2">
            <button
              type="button"
              onClick={addHolding}
              className="pmri-focus rounded-full border border-pmri-blue/22 bg-pmri-blue/[0.055] px-3.5 py-2 text-sm font-medium text-pmri-blueSoft transition hover:bg-pmri-blue/[0.085]"
            >
              Add holding
            </button>
            <button
              type="button"
              onClick={addCashPosition}
              title="Cash is treated as a portfolio position."
              className="pmri-focus rounded-full border border-pmri-border/50 bg-white/[0.025] px-3.5 py-2 text-sm font-medium text-pmri-text2 transition hover:border-pmri-blue/25 hover:bg-white/[0.04]"
            >
              Add cash position
            </button>
          </div>
        </div>

        <p className="mt-3 text-xs leading-5 text-pmri-muted">Cash is treated as a portfolio position.</p>

        <div className="mt-5 overflow-x-auto rounded-2xl border border-pmri-border/45 bg-pmri-secondary/35">
          <table className="w-full min-w-[760px] border-separate border-spacing-0 text-left text-sm">
            <thead className="bg-white/[0.018] text-xs font-medium tracking-[-0.005em] text-pmri-muted">
              <tr>
                <th scope="col" className="px-4 py-3">Ticker / Cash</th>
                <th scope="col" className="px-4 py-3">Instrument</th>
                <th scope="col" className="px-4 py-3 text-right">Weight %</th>
                <th scope="col" className="px-4 py-3 text-right">Actions</th>
              </tr>
            </thead>
            <tbody className="[&_tr+tr_td]:border-t [&_tr+tr_td]:border-pmri-border/35">
              {rows.length === 0 ? (
                <tr>
                  <td colSpan={4} className="px-4 py-8">
                    <div className="rounded-2xl border border-dashed border-pmri-border/60 bg-white/[0.018] p-5 text-center">
                      <h3 className="pmri-heading-section text-base text-pmri-text">No holdings added yet</h3>
                      <p className="mx-auto mt-2 max-w-xl text-sm leading-6 text-pmri-muted">
                        Add at least two current positions before running the diagnosis. Cash can be entered as its own portfolio position.
                      </p>
                      <button
                        type="button"
                        onClick={addHolding}
                        className="pmri-focus mt-4 rounded-full border border-pmri-blue/25 bg-pmri-blue/[0.065] px-4 py-2 text-sm font-medium text-pmri-blueSoft transition hover:bg-pmri-blue/[0.095]"
                      >
                        Add first holding
                      </button>
                    </div>
                  </td>
                </tr>
              ) : rows.map((row) => {
                const ticker = normalizeTicker(row.ticker);
                const tickerMissing = ticker.length === 0;
                const rowStarted = ticker.length > 0 || row.weightInput.trim().length > 0;
                const instrumentMissing = !isKnownInstrument(row);
                const duplicateTicker = ticker.length > 0 && duplicateTickerSet.has(ticker);

                return (
                  <tr key={row.id} className="transition hover:bg-white/[0.026]">
                    <td className="px-4 py-4 align-top">
                      <InstrumentCombobox
                        row={row}
                        duplicateTicker={duplicateTicker}
                        showValidationError={instrumentMissing && rowStarted}
                        onSelect={(instrument) => updateInstrument(row.id, instrument)}
                        onClearSelection={() => updateInstrument(row.id, null)}
                      />
                      {instrumentMissing && rowStarted ? (
                        <p className="mt-2 text-xs leading-5 text-pmri-risk">
                          {tickerMissing ? "Select a ticker or cash position." : "Select an instrument from the list."}
                        </p>
                      ) : null}
                      {duplicateTicker ? (
                        <p className="mt-2 text-xs leading-5 text-pmri-amber">Warning: this exact ticker appears more than once.</p>
                      ) : null}
                    </td>
                    <td className="px-4 py-4 align-top">
                      <div className="rounded-xl border border-pmri-border/45 bg-white/[0.02] px-3 py-2.5 text-sm leading-6 text-pmri-text2">
                        {displayInstrument(row) || "Choose an instrument from the list"}
                      </div>
                    </td>
                    <td className="px-4 py-4 text-right align-top">
                      <input
                        className="pmri-focus data-figure ml-auto w-28 rounded-xl border border-pmri-border/55 bg-pmri-secondary/80 px-3 py-2.5 text-right text-sm font-medium text-pmri-text placeholder:text-pmri-muted/70"
                        type="text"
                        inputMode="decimal"
                        placeholder="0"
                        value={row.weightInput}
                        onChange={(event) => updateWeight(row.id, event.target.value)}
                        aria-invalid={!isValidWeight(row)}
                      />
                      {!isValidWeight(row) && rowStarted ? (
                        <p className="mt-2 text-xs leading-5 text-pmri-risk">Enter a weight greater than 0.</p>
                      ) : null}
                    </td>
                    <td className="px-4 py-4 text-right align-top">
                      <button
                        type="button"
                        onClick={() => removeRow(row.id)}
                        className="pmri-focus rounded-full border border-transparent bg-transparent px-2.5 py-2 text-sm font-medium text-pmri-muted transition hover:bg-pmri-risk/[0.045] hover:text-pmri-risk"
                      >
                        Remove row
                      </button>
                    </td>
                  </tr>
                );
              })}
            </tbody>
          </table>
        </div>

        {hasDuplicateTickers ? (
          <p className="mt-3 rounded-xl border border-pmri-amber/35 bg-pmri-amber/10 px-4 py-3 text-sm leading-6 text-pmri-text2">
            The same ticker appears more than once. Review duplicates before running the diagnosis.
          </p>
        ) : null}
        <SimilarExposureWarning rows={rows} />

        <div className="mt-5 grid gap-5 lg:grid-cols-[1fr_minmax(360px,420px)] lg:items-start">
          <section className="rounded-2xl border border-pmri-border/45 bg-white/[0.022] p-5">
            <div className="flex flex-col gap-3 sm:flex-row sm:items-start sm:justify-between">
              <div>
                <h3 className="pmri-heading-section text-lg text-pmri-text">{validationSummary.title}</h3>
                <p className="mt-1 text-sm leading-6 text-pmri-muted">{validationSummary.text}</p>
              </div>
              <div className="flex items-center gap-3">
                <StatusBadge tone={validationSummary.tone}>{validationSummary.title}</StatusBadge>
                <span className={`data-figure text-xl font-medium ${weightsAddTo100 ? "text-pmri-positive" : totalWeight > 100 ? "text-pmri-risk" : "text-pmri-amber"}`}>
                  {formatTotalWeight(totalWeight)}%
                </span>
              </div>
            </div>
          </section>

          <div>
            <button
              type="button"
              disabled={!ready || isRunningDiagnosis}
              onClick={runPortfolioDiagnosis}
              className="pmri-focus pmri-primary-action flex w-full items-center justify-center gap-2 rounded-full px-5 py-3 text-sm font-semibold shadow-decision transition disabled:cursor-not-allowed disabled:border-white/10 disabled:bg-white/10 disabled:text-pmri-muted disabled:shadow-none"
            >
              {isRunningDiagnosis ? (
                <>
                  <span className="pmri-spinner" aria-hidden="true" />
                  Starting diagnosis...
                </>
              ) : "Run diagnosis"}
            </button>
            {!clientProfileReady ? (
              <p className="mt-3 rounded-xl border border-pmri-amber/35 bg-pmri-amber/10 px-4 py-3 text-sm leading-6 text-pmri-amber">
                Complete Client Profile first. The backend and CLI remain compatible with missing profile data, but this web journey requires it before diagnosis.
              </p>
            ) : null}
            {diagnosisError ? (
              <p className="mt-3 rounded-xl border border-pmri-risk/35 bg-pmri-risk/10 px-4 py-3 text-sm leading-6 text-pmri-risk">
                {diagnosisError}
              </p>
            ) : null}
            {showStagedProgress || isRunningDiagnosis ? (
              <div className="mt-3 rounded-2xl border border-pmri-blue/25 bg-pmri-blue/10 px-4 py-3 text-xs leading-5 text-pmri-blueSoft">
                <p className="flex items-center gap-2 font-medium text-pmri-text">
                  <span className="pmri-spinner" aria-hidden="true" />
                  Reviewing your portfolio&apos;s allocation, concentration, risk drivers, and stress vulnerabilities.
                </p>
                {stagedProgress ? <p className="sr-only">{stagedStatusLabel(stagedProgress)}</p> : null}
                {stagedProgress?.safeError ? (
                  <p className="mt-3 rounded-xl border border-pmri-risk/35 bg-pmri-risk/10 px-3 py-2 text-xs leading-5 text-pmri-risk">
                    {stagedProgress.safeError.message}
                  </p>
                ) : null}
              </div>
            ) : null}
          </div>
        </div>
      </div>
    </section>
    {false ? (
      <section className="pmri-card rounded-2xl p-5 md:p-6">
        <div className="flex flex-col gap-4 lg:flex-row lg:items-start lg:justify-between">
          <div className="max-w-2xl">
            <p className="pmri-label">Optional cloud portfolios</p>
            <h2 className="pmri-heading-section mt-2 text-lg text-pmri-text">Save and reuse current portfolio inputs</h2>
            <p className="mt-2 text-sm leading-6 text-pmri-muted">
              Cloud save is optional. It stores only the current portfolio input and compact metadata, not generated analytics files.
            </p>
          </div>
          <StatusBadge tone={cloudReady ? "green" : "amber"}>
            {cloudReady ? "Signed in" : "Sign in required"}
          </StatusBadge>
        </div>

        {cloudReady ? (
          <div className="mt-5 grid gap-5 xl:grid-cols-[minmax(0,1fr)_minmax(320px,420px)]">
            <div className="rounded-2xl border border-pmri-border/45 bg-white/[0.022] p-4">
              <div className="grid gap-4 md:grid-cols-2">
                <label>
                  <span className="pmri-label block">Portfolio name</span>
                  <input
                    className="pmri-focus mt-2 w-full rounded-xl border border-pmri-border/55 bg-pmri-secondary/80 px-3 py-2.5 text-sm font-medium text-pmri-text placeholder:text-pmri-muted/70"
                    value={cloudPortfolioName}
                    onChange={(event) => setCloudPortfolioName(event.target.value)}
                    placeholder="Balanced portfolio"
                  />
                </label>
                <label>
                  <span className="pmri-label block">Description (optional)</span>
                  <input
                    className="pmri-focus mt-2 w-full rounded-xl border border-pmri-border/55 bg-pmri-secondary/80 px-3 py-2.5 text-sm font-medium text-pmri-text placeholder:text-pmri-muted/70"
                    value={cloudPortfolioDescription}
                    onChange={(event) => setCloudPortfolioDescription(event.target.value)}
                    placeholder="Client sleeve or review note"
                  />
                </label>
              </div>
              <div className="mt-4 flex flex-wrap items-center gap-3">
                <button
                  type="button"
                  disabled={!rows.length || isSavingPortfolio || !cloudPortfolioName.trim()}
                  onClick={saveCurrentPortfolioToCloud}
                  className="pmri-focus rounded-full border border-pmri-blue/30 bg-pmri-blue px-4 py-2.5 text-sm font-semibold text-pmri-bg shadow-decision transition hover:bg-pmri-blueSoft disabled:cursor-not-allowed disabled:border-white/10 disabled:bg-white/10 disabled:text-pmri-muted disabled:shadow-none"
                >
                  {isSavingPortfolio ? "Saving..." : activeReview?.cloudPortfolio?.id ? "Update saved portfolio" : "Save current portfolio"}
                </button>
                {activeReview?.cloudPortfolio?.name ? (
                  <p className="text-xs leading-5 text-pmri-muted">
                    Active cloud portfolio: <span className="font-medium text-pmri-text2">{activeReview?.cloudPortfolio?.name}</span>
                  </p>
                ) : (
                  <p className="text-xs leading-5 text-pmri-muted">Save this input if you want to reload it across browser sessions.</p>
                )}
              </div>
            </div>

            <div className="rounded-2xl border border-pmri-border/45 bg-white/[0.022] p-4">
              <div className="flex items-center justify-between gap-3">
                <div>
                  <p className="pmri-label">Saved portfolios</p>
                  <p className="mt-1 text-xs leading-5 text-pmri-muted">Load, reuse, or delete previously saved portfolio inputs.</p>
                </div>
                <StatusBadge tone="blue">{savedPortfolios.length} saved</StatusBadge>
              </div>

              {portfoliosLoading ? (
                <p className="mt-4 text-sm text-pmri-muted">Loading saved portfolios...</p>
              ) : savedPortfolios.length ? (
                <div className="mt-4 space-y-3">
                  {savedPortfolios.map((portfolio) => (
                    <article key={portfolio.id} className="rounded-2xl border border-pmri-border/40 bg-pmri-secondary/35 p-4">
                      <div className="flex items-start justify-between gap-3">
                        <div className="min-w-0">
                          <h3 className="truncate text-sm font-semibold text-pmri-text">{portfolio.name}</h3>
                          <p className="mt-1 text-xs leading-5 text-pmri-muted">
                            {portfolio.holdings.length} holdings · {portfolio.baseCurrency} base currency
                          </p>
                          {portfolio.description ? (
                            <p className="mt-1 text-xs leading-5 text-pmri-muted">{portfolio.description}</p>
                          ) : null}
                        </div>
                        {activeReview?.cloudPortfolio?.id === portfolio.id ? <StatusBadge tone="green">Active</StatusBadge> : null}
                      </div>
                      <div className="mt-3 flex flex-wrap gap-2">
                        <button
                          type="button"
                          disabled={activeCloudLoadId === portfolio.id}
                          onClick={() => void loadSavedPortfolio(portfolio.id)}
                          className="pmri-focus rounded-full border border-pmri-border/55 px-3.5 py-2 text-xs font-semibold text-pmri-text2 transition hover:border-pmri-border hover:bg-white/[0.04] disabled:cursor-not-allowed disabled:opacity-60"
                        >
                          {activeCloudLoadId === portfolio.id ? "Loading..." : "Load into input"}
                        </button>
                        <button
                          type="button"
                          disabled={activeCloudDeleteId === portfolio.id}
                          onClick={() => void deleteSavedPortfolioFromCloud(portfolio.id)}
                          className="pmri-focus rounded-full border border-pmri-risk/30 px-3.5 py-2 text-xs font-semibold text-pmri-risk transition hover:bg-pmri-risk/[0.08] disabled:cursor-not-allowed disabled:opacity-60"
                        >
                          {activeCloudDeleteId === portfolio.id ? "Deleting..." : "Delete"}
                        </button>
                      </div>
                    </article>
                  ))}
                </div>
              ) : (
                <p className="mt-4 text-sm leading-6 text-pmri-muted">
                  No cloud portfolios saved yet. Save the current input once you want reusable browser-independent storage.
                </p>
              )}
            </div>
          </div>
        ) : (
          <div className="mt-5 rounded-2xl border border-pmri-amber/30 bg-pmri-amber/10 px-4 py-4 text-sm leading-6 text-pmri-text2">
            Sign in with Email OTP from the sidebar to enable optional cloud save/load/delete for portfolio inputs.
            Without sign-in, the normal local browser flow still works.
          </div>
        )}
      </section>
    ) : null}
    {intakeModalOpen && typeof document !== "undefined" ? createPortal((
      <div className="fixed inset-0 z-[90] flex items-center justify-center px-4 py-6" role="dialog" aria-modal="true" aria-labelledby="adjust-intake-title">
        <button
          type="button"
          className="absolute inset-0 bg-black/72 backdrop-blur-sm transition-opacity motion-safe:animate-[pmri-section-reveal_260ms_ease-out]"
          aria-label="Close intake editor"
          onClick={() => setIntakeModalOpen(false)}
        />
        <section className="pmri-card relative z-10 w-full max-w-3xl rounded-[2rem] p-5 shadow-[0_28px_90px_rgba(0,0,0,0.52)] motion-safe:animate-[pmri-section-reveal_320ms_cubic-bezier(0.2,0.8,0.2,1)] md:p-6">
          <div className="flex flex-col gap-4 sm:flex-row sm:items-start sm:justify-between">
            <div>
              <p className="pmri-label text-pmri-blueSoft">Planning targets</p>
              <h2 id="adjust-intake-title" className="pmri-heading-section mt-2 text-2xl text-pmri-text">Adjust intake</h2>
              <p className="mt-2 max-w-2xl text-sm leading-6 text-pmri-muted">
                Change the display targets after the five-question preset. These values are context for diagnosis and later tests, not trade instructions.
              </p>
            </div>
            <button
              type="button"
              onClick={() => setIntakeModalOpen(false)}
              className="pmri-focus rounded-full border border-pmri-border/60 bg-white/[0.025] px-4 py-2 text-sm font-medium text-pmri-text2 transition hover:border-pmri-blue/35 hover:text-pmri-text"
            >
              Close
            </button>
          </div>

          <div className="mt-6 grid gap-4 md:grid-cols-2">
            <label>
              <span className="pmri-label block">Desired return min %</span>
              <input className="pmri-focus mt-2 w-full rounded-2xl border border-pmri-border/55 bg-pmri-secondary/85 px-4 py-3 text-sm text-pmri-text" value={intakeReturnMin} onChange={(event) => setIntakeReturnMin(cleanWeightInput(event.target.value))} />
            </label>
            <label>
              <span className="pmri-label block">Desired return max %</span>
              <input className="pmri-focus mt-2 w-full rounded-2xl border border-pmri-border/55 bg-pmri-secondary/85 px-4 py-3 text-sm text-pmri-text" value={intakeReturnMax} onChange={(event) => setIntakeReturnMax(cleanWeightInput(event.target.value))} />
            </label>
            <label>
              <span className="pmri-label block">Volatility comfort min %</span>
              <input className="pmri-focus mt-2 w-full rounded-2xl border border-pmri-border/55 bg-pmri-secondary/85 px-4 py-3 text-sm text-pmri-text" value={intakeVolMin} onChange={(event) => setIntakeVolMin(cleanWeightInput(event.target.value))} />
            </label>
            <label>
              <span className="pmri-label block">Volatility comfort max %</span>
              <input className="pmri-focus mt-2 w-full rounded-2xl border border-pmri-border/55 bg-pmri-secondary/85 px-4 py-3 text-sm text-pmri-text" value={intakeVolMax} onChange={(event) => setIntakeVolMax(cleanWeightInput(event.target.value))} />
            </label>
            <label>
              <span className="pmri-label block">Maximum temporary loss %</span>
              <input className="pmri-focus mt-2 w-full rounded-2xl border border-pmri-border/55 bg-pmri-secondary/85 px-4 py-3 text-sm text-pmri-text" value={intakeDrawdown} onChange={(event) => setIntakeDrawdown(cleanWeightInput(event.target.value))} />
            </label>
            <label>
              <span className="pmri-label block">Decision horizon years</span>
              <input className="pmri-focus mt-2 w-full rounded-2xl border border-pmri-border/55 bg-pmri-secondary/85 px-4 py-3 text-sm text-pmri-text" value={intakeHorizonYears} onChange={(event) => setIntakeHorizonYears(cleanWeightInput(event.target.value))} />
            </label>
          </div>

          <div className="mt-6 flex flex-col gap-3 rounded-2xl border border-pmri-border/45 bg-white/[0.022] p-4 sm:flex-row sm:items-center sm:justify-between">
            <div>
              <StatusBadge tone={intakeValues.valid ? "green" : "amber"}>{intakeValues.valid ? "Targets ready" : "Check targets"}</StatusBadge>
              <p className="mt-2 text-xs leading-5 text-pmri-muted">
                Ranges must increase, percentages must stay realistic, and horizon must be above zero.
              </p>
            </div>
            <button
              type="button"
              disabled={!intakeValues.valid}
              onClick={saveAdjustedIntake}
              className="pmri-focus pmri-primary-action rounded-full px-5 py-3 text-sm font-semibold transition disabled:cursor-not-allowed disabled:border-white/10 disabled:bg-white/10 disabled:text-pmri-muted"
            >
              Save intake
            </button>
          </div>
        </section>
      </div>
    ), document.body) : null}
    <details className="hidden">
      <summary className="pmri-focus cursor-pointer list-none text-sm font-medium text-pmri-text2 transition hover:text-pmri-text">
        Advanced: recover an existing review
      </summary>
      <div className="mt-5 grid gap-5 lg:grid-cols-[minmax(0,1fr)_360px] lg:items-start">
        <div>
          <p className="pmri-label">Optional recovery</p>
          <h2 className="pmri-heading-section mt-2 text-lg text-pmri-text">Reload an existing review by ID</h2>
          <p className="mt-2 text-sm leading-6 text-pmri-muted">
            Use this after a page refresh or browser restart; staged diagnosis progress is safe to refresh. Recovery restores the current portfolio diagnosis for that review ID.
            Candidate, comparison, verdict, and report steps must be reviewed again.
          </p>
          <p className="mt-2 text-xs leading-5 text-pmri-muted">
            Saved browser state keeps only a compact summary, not the full evidence package.
            Data freshness: recovered compact state is not recalculated automatically.
          </p>
        </div>
        <div>
          <label>
            <span className="pmri-label block">Review ID</span>
            <input
              className="pmri-focus mt-2 w-full rounded-xl border border-pmri-border/55 bg-pmri-secondary/80 px-3 py-2.5 text-sm font-medium text-pmri-text placeholder:text-pmri-muted/70"
              value={recoverReviewId}
              placeholder="frontend_review_..."
              onChange={(event) => setRecoverReviewId(event.target.value)}
            />
          </label>
          <button
            type="button"
            disabled={!recoverReviewId.trim() || isRecoveringReview}
            onClick={recoverActiveReview}
            className="pmri-focus mt-3 flex w-full items-center justify-center gap-2 rounded-full border border-pmri-blue/35 bg-pmri-blue px-5 py-3 text-sm font-semibold text-pmri-bg shadow-decision transition hover:bg-pmri-blueSoft disabled:cursor-not-allowed disabled:border-white/10 disabled:bg-white/10 disabled:text-pmri-muted disabled:shadow-none"
          >
            {isRecoveringReview ? (
              <>
                <span className="pmri-spinner" aria-hidden="true" />
                Recovering review...
              </>
            ) : "Recover active review"}
          </button>
          {recoveryError ? (
            <p className="mt-3 rounded-xl border border-pmri-risk/35 bg-pmri-risk/10 px-4 py-3 text-sm leading-6 text-pmri-risk">
              {recoveryError}
            </p>
          ) : null}
        </div>
      </div>
    </details>
    </div>
  );
}
