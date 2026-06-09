"use client";

import { useEffect, useMemo, useRef, useState } from "react";
import { createPortal } from "react-dom";
import { useRouter } from "next/navigation";
import type { Holding } from "@/lib/types";
import { StatusBadge } from "@/components/ui/StatusBadge";
import { instrumentByTicker, instrumentUniverse, type Instrument } from "@/data/instrumentUniverse";
import { useReviewState, type ReviewHolding, type ReviewResult } from "@/lib/reviewState";

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
  return Number.isFinite(value) ? value.toFixed(2).replace(/\.?0+$/, "") : "0";
}

function formatTotalWeight(value: number) {
  return Math.abs(value - 100) <= WEIGHT_TOLERANCE ? "100" : formatWeight(value);
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
  onSelect,
  onClearSelection
}: {
  row: EditableHolding;
  duplicateTicker: boolean;
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

  return (
    <div className="relative">
      <input
        ref={inputRef}
        className={`pmri-focus w-full rounded-xl border bg-pmri-secondary/80 px-3 py-2.5 text-sm font-medium text-pmri-text placeholder:text-pmri-muted/70 ${instrumentMissing ? "border-pmri-risk/55" : duplicateTicker ? "border-pmri-amber/55" : "border-pmri-border/55"}`}
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
        aria-invalid={instrumentMissing}
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
  const { activeReview, hydrated, savePortfolioInput, submitPortfolioInput, recordReviewError } = useReviewState();
  const [currency, setCurrency] = useState(investorCurrency || "");
  const [rows, setRows] = useState<EditableHolding[]>(() => holdings.map(toEditableHolding));
  const [isRunningDiagnosis, setIsRunningDiagnosis] = useState(false);
  const [diagnosisError, setDiagnosisError] = useState<string | null>(null);
  const [recoverReviewId, setRecoverReviewId] = useState("");
  const [isRecoveringReview, setIsRecoveringReview] = useState(false);
  const [recoveryError, setRecoveryError] = useState<string | null>(null);
  const inputInitialized = useRef(false);
  const inputEdited = useRef(false);

  useEffect(() => {
    if (!hydrated || inputInitialized.current) return;

    if (activeReview?.holdings.length) {
      setCurrency(activeReview.investorCurrency);
      setRows(activeReview.holdings.map(reviewHoldingToEditable));
    }
    inputInitialized.current = true;
  }, [activeReview, hydrated]);

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
  const instrumentsComplete = rows.length > 0 && rows.every(isKnownInstrument);
  const weightsComplete = rows.length > 0 && rows.every(isValidWeight);
  const weightsAddTo100 = Math.abs(totalWeight - 100) <= WEIGHT_TOLERANCE;

  const validationSummary: ValidationSummary = useMemo(() => {
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
        text: `${rows.length} holdings · 100% allocated`,
      tone: "green"
    };
  }, [instrumentsComplete, rows.length, totalWeight, weightsComplete]);

  const ready = instrumentsComplete && weightsComplete && weightsAddTo100;

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
    setRows((currentRows) => [
      ...currentRows,
      { id: `holding-${Date.now()}`, ticker: "", instrument: "", weight: Number.NaN, weightInput: "" }
    ]);
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
          holdings: reviewHoldings.map(reviewHoldingToPayload)
        })
      });

      const result = await response.json() as ReviewResult & { error?: string; details?: unknown };

      if (!response.ok || result.status !== "completed") {
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

      submitPortfolioInput({
        investorCurrency: currency || "USD",
        holdings: reviewHoldings,
        reviewResult: result
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

  const recoverActiveReview = async () => {
    const reviewId = recoverReviewId.trim();
    if (!reviewId || isRecoveringReview) return;

    setRecoveryError(null);
    setIsRecoveringReview(true);

    try {
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
      if (!recoveredHoldings.length) {
        throw new Error("Review recovery found the run, but portfolio_input.holdings could not be restored.");
      }

      const recoveredCurrency = currencyFromRecoveredReview(result.review_result);
      inputEdited.current = false;
      setCurrency(recoveredCurrency);
      setRows(recoveredHoldings.map(reviewHoldingToEditable));
      submitPortfolioInput({
        investorCurrency: recoveredCurrency,
        holdings: recoveredHoldings,
        reviewResult: result.review_result
      });
      router.push("/diagnosis");
    } catch (error) {
      setRecoveryError(error instanceof Error ? error.message : "Review recovery failed.");
    } finally {
      setIsRecoveringReview(false);
    }
  };

  return (
    <div className="space-y-5">
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
            <p className="mt-1 text-sm text-pmri-muted">What portfolio are we diagnosing?</p>
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
              {rows.map((row) => {
                const ticker = normalizeTicker(row.ticker);
                const tickerMissing = ticker.length === 0;
                const instrumentMissing = !isKnownInstrument(row);
                const duplicateTicker = ticker.length > 0 && duplicateTickerSet.has(ticker);

                return (
                  <tr key={row.id} className="transition hover:bg-white/[0.026]">
                    <td className="px-4 py-4 align-top">
                      <InstrumentCombobox
                        row={row}
                        duplicateTicker={duplicateTicker}
                        onSelect={(instrument) => updateInstrument(row.id, instrument)}
                        onClearSelection={() => updateInstrument(row.id, null)}
                      />
                      {instrumentMissing ? (
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
                      {!isValidWeight(row) ? (
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

        <div className="mt-5 grid gap-5 lg:grid-cols-[1fr_auto] lg:items-start">
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

          <div className="lg:max-w-xs">
            <button
              type="button"
              disabled={!ready || isRunningDiagnosis}
              onClick={runPortfolioDiagnosis}
              className="pmri-focus pmri-primary-action flex w-full items-center justify-center gap-2 rounded-full px-5 py-3 text-sm font-semibold shadow-decision transition disabled:cursor-not-allowed disabled:border-white/10 disabled:bg-white/10 disabled:text-pmri-muted disabled:shadow-none"
            >
              {isRunningDiagnosis ? (
                <>
                  <span className="pmri-spinner" aria-hidden="true" />
                  Building evidence pack...
                </>
              ) : "Run diagnosis"}
            </button>
            {diagnosisError ? (
              <p className="mt-3 rounded-xl border border-pmri-risk/35 bg-pmri-risk/10 px-4 py-3 text-sm leading-6 text-pmri-risk">
                {diagnosisError}
              </p>
            ) : null}
            {isRunningDiagnosis ? (
              <p className="mt-3 rounded-xl border border-pmri-blue/25 bg-pmri-blue/10 px-4 py-3 text-xs leading-5 text-pmri-blueSoft">
                Building the portfolio evidence pack. No candidate or trade action is created at this step.
              </p>
            ) : null}
            <p className="mt-3 text-sm leading-6 text-pmri-muted">
              Next: Portfolio X-Ray will review allocation, concentration, and stress vulnerabilities.
            </p>
          </div>
        </div>
      </div>
    </section>
    <details className="hidden">
      <summary className="pmri-focus cursor-pointer list-none text-sm font-medium text-pmri-text2 transition hover:text-pmri-text">
        Advanced: recover an existing review
      </summary>
      <div className="mt-5 grid gap-5 lg:grid-cols-[minmax(0,1fr)_360px] lg:items-start">
        <div>
          <p className="pmri-label">Optional recovery</p>
          <h2 className="pmri-heading-section mt-2 text-lg text-pmri-text">Reload an existing review by ID</h2>
          <p className="mt-2 text-sm leading-6 text-pmri-muted">
            Use this after a page refresh or browser restart. Recovery restores the current portfolio diagnosis for that review ID.
            Candidate, comparison, verdict, and report steps must be reviewed again.
          </p>
          <p className="mt-2 text-xs leading-5 text-pmri-muted">
            Saved browser state keeps only a compact summary, not the full evidence package.
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
