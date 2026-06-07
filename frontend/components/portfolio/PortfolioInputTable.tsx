"use client";

import { useMemo, useState } from "react";
import type { Holding } from "@/lib/types";
import { StatusBadge } from "@/components/ui/StatusBadge";

type PortfolioInputTableProps = {
  investorCurrency: string;
  holdings: Holding[];
};

type EditableHolding = Holding & {
  id: string;
  weightInput: string;
};

type Instrument = {
  ticker: string;
  instrument: string;
  kind: "fund" | "cash";
};

const currencies = ["USD", "EUR", "GBP", "CHF", "CAD", "AUD"];
const WEIGHT_TOLERANCE = 0.01;

const instrumentUniverse: Instrument[] = [
  { ticker: "SPY", instrument: "SPDR S&P 500 ETF", kind: "fund" },
  { ticker: "QQQ", instrument: "Invesco QQQ Trust", kind: "fund" },
  { ticker: "BND", instrument: "Vanguard Total Bond Market ETF", kind: "fund" },
  { ticker: "TLT", instrument: "iShares 20+ Year Treasury Bond ETF", kind: "fund" },
  { ticker: "GLD", instrument: "SPDR Gold Shares", kind: "fund" },
  { ticker: "VOO", instrument: "Vanguard S&P 500 ETF", kind: "fund" },
  { ticker: "VTI", instrument: "Vanguard Total Stock Market ETF", kind: "fund" },
  { ticker: "CASH_USD", instrument: "Cash USD", kind: "cash" },
  { ticker: "CASH_EUR", instrument: "Cash EUR", kind: "cash" }
];

const instrumentByTicker = new Map(instrumentUniverse.map((item) => [item.ticker, item]));

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

function normalizeTicker(value: string) {
  return value.trim().toUpperCase();
}

function parseWeightInput(value: string) {
  if (value.trim() === "") return null;
  const parsed = Number(value);
  return Number.isFinite(parsed) ? parsed : null;
}

function formatWeight(value: number) {
  return Number.isFinite(value) ? value.toFixed(2).replace(/\.?0+$/, "") : "0";
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

function formatDelta(value: number) {
  return formatWeight(Math.max(0, value));
}

function isCashRow(row: EditableHolding) {
  return instrumentByTicker.get(normalizeTicker(row.ticker))?.kind === "cash";
}

function cashRulePasses(rows: EditableHolding[]) {
  return rows.every((row) => {
    const instrumentMentionsCash = row.instrument.trim().toLowerCase().includes("cash");
    return !instrumentMentionsCash || isCashRow(row);
  });
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

function getCashTicker(currency: string) {
  return currency === "EUR" ? "CASH_EUR" : "CASH_USD";
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

export function PortfolioInputTable({ investorCurrency, holdings }: PortfolioInputTableProps) {
  const [currency, setCurrency] = useState(investorCurrency || "");
  const [rows, setRows] = useState<EditableHolding[]>(() => holdings.map(toEditableHolding));

  const totalWeight = useMemo(
    () => rows.reduce((sum, row) => sum + parsedWeightOrZero(row), 0),
    [rows]
  );

  const duplicateTickerSet = useMemo(() => duplicateTickers(rows), [rows]);
  const hasDuplicateTickers = duplicateTickerSet.size > 0;

  const validation = useMemo(() => {
    const currencySelected = currency.trim().length > 0;
    const validRows = rows.filter((row) => isKnownInstrument(row) && isValidWeight(row));
    const enoughHoldings = validRows.length >= 2;
    const weightsAddTo100 = Math.abs(totalWeight - 100) <= WEIGHT_TOLERANCE;
    const cashSeparate = cashRulePasses(rows);
    const instrumentsComplete = rows.every(isKnownInstrument);
    const weightsComplete = rows.every(isValidWeight);
    const allocationStatus = totalWeight < 100 - WEIGHT_TOLERANCE
      ? {
          title: "Incomplete allocation",
          message: `You still need to allocate ${formatDelta(100 - totalWeight)}%.`
        }
      : totalWeight > 100 + WEIGHT_TOLERANCE
        ? {
            title: "Allocation exceeds 100%",
            message: `Reduce total weight by ${formatDelta(totalWeight - 100)}%.`
          }
        : {
            title: "Ready for diagnosis",
            message: "Portfolio weights add up to 100%."
          };

    const blockingReasons = [
      !currencySelected ? "Select an investor currency." : null,
      rows.length < 2 ? "Add at least 2 portfolio rows." : null,
      !enoughHoldings ? "Portfolio must have at least 2 valid rows with selected instruments and weights above 0." : null,
      !instrumentsComplete ? "Select an instrument for every row." : null,
      !weightsComplete ? "Enter a weight greater than 0 for every row." : null,
      !weightsAddTo100 ? allocationStatus.message : null,
      !cashSeparate ? "Cash must be selected as a dedicated cash instrument." : null
    ].filter((reason): reason is string => Boolean(reason));

    return {
      currencySelected,
      enoughHoldings,
      weightsAddTo100,
      cashSeparate,
      instrumentsComplete,
      weightsComplete,
      allocationStatus,
      blockingReasons,
      ready: currencySelected && enoughHoldings && weightsAddTo100 && cashSeparate && instrumentsComplete && weightsComplete
    };
  }, [currency, rows, totalWeight]);

  const updateTicker = (id: string, value: string) => {
    const ticker = normalizeTicker(value);
    const selectedInstrument = instrumentByTicker.get(ticker);

    setRows((currentRows) => currentRows.map((row) => {
      if (row.id !== id) return row;
      return {
        ...row,
        ticker,
        instrument: selectedInstrument?.instrument ?? ""
      };
    }));
  };

  const updateWeight = (id: string, value: string) => {
    setRows((currentRows) => currentRows.map((row) => (
      row.id === id ? { ...row, weightInput: value, weight: parseWeightInput(value) ?? Number.NaN } : row
    )));
  };

  const addHolding = () => {
    setRows((currentRows) => [
      ...currentRows,
      { id: `holding-${Date.now()}`, ticker: "", instrument: "", weight: Number.NaN, weightInput: "" }
    ]);
  };

  const addCashPosition = () => {
    const ticker = getCashTicker(currency);
    const cashInstrument = instrumentByTicker.get(ticker);

    setRows((currentRows) => [
      ...currentRows,
      {
        id: `cash-${Date.now()}`,
        ticker,
        instrument: cashInstrument?.instrument ?? "Cash position",
        weight: Number.NaN,
        weightInput: ""
      }
    ]);
  };

  const removeRow = (id: string) => {
    setRows((currentRows) => currentRows.filter((row) => row.id !== id));
  };

  const checklist = [
    { label: "Investor currency selected", passed: validation.currencySelected },
    { label: "Portfolio has at least 2 valid rows", passed: validation.enoughHoldings },
    { label: "Every row has a selected instrument", passed: validation.instrumentsComplete },
    { label: "Every row has a weight greater than 0", passed: validation.weightsComplete },
    { label: "Weights add up to 100%", passed: validation.weightsAddTo100 },
    { label: "Cash is entered as a separate position, if used", passed: validation.cashSeparate }
  ];

  return (
    <section className="pmri-card overflow-hidden rounded-2xl">
      <div className="border-b border-pmri-border/80 p-5 md:p-6">
        <div className="flex flex-col gap-4 lg:flex-row lg:items-start lg:justify-between">
          <div className="max-w-2xl">
            <p className="text-xs font-semibold uppercase tracking-[0.16em] text-pmri-gold">Current allocation only</p>
            <p className="mt-2 text-sm leading-6 text-pmri-text2">
              These weights are the subject of diagnosis, not a recommendation or target portfolio.
            </p>
          </div>

          <label className="min-w-[240px]">
            <span className="block text-xs font-medium text-pmri-muted">Investor currency</span>
            <select
              className="pmri-focus mt-2 w-full rounded-lg border border-pmri-border bg-pmri-secondary px-3 py-2 text-sm font-semibold text-pmri-text"
              value={currency}
              onChange={(event) => setCurrency(event.target.value)}
              title="Used for reporting, benchmark defaults, and cash treatment."
            >
              <option value="">Select currency</option>
              {currencies.map((item) => <option key={item} value={item}>{item}</option>)}
            </select>
            <span className="mt-1 block text-xs leading-5 text-pmri-muted">
              Used for reporting, benchmark defaults, and cash treatment.
            </span>
          </label>
        </div>
      </div>

      <div className="p-5 md:p-6">
        <div className="flex flex-col gap-3 md:flex-row md:items-center md:justify-between">
          <div>
            <h2 className="text-xl font-semibold text-pmri-text">Holdings and weights</h2>
            <p className="mt-1 text-sm text-pmri-muted">What portfolio are we diagnosing?</p>
          </div>
          <div className="flex flex-wrap gap-2">
            <button
              type="button"
              onClick={addHolding}
              className="pmri-focus rounded-full border border-pmri-blue/40 bg-pmri-blue/10 px-4 py-2 text-sm font-semibold text-pmri-blueSoft transition hover:bg-pmri-blue/15"
            >
              Add holding
            </button>
            <button
              type="button"
              onClick={addCashPosition}
              title="Cash is treated as a real portfolio position. It is not replaced by a proxy asset."
              className="pmri-focus rounded-full border border-pmri-gold/40 bg-pmri-gold/10 px-4 py-2 text-sm font-semibold text-pmri-gold transition hover:bg-pmri-gold/15"
            >
              Add cash position
            </button>
          </div>
        </div>

        <p className="mt-3 text-xs leading-5 text-pmri-muted">
          Cash is treated as a real portfolio position. It is not replaced by a proxy asset.
        </p>

        <div className="mt-5 overflow-x-auto rounded-xl border border-pmri-border">
          <table className="w-full min-w-[760px] border-collapse text-left text-sm">
            <thead className="bg-pmri-secondary/80 text-xs uppercase tracking-[0.12em] text-pmri-muted">
              <tr>
                <th scope="col" className="px-4 py-3">Ticker / Cash</th>
                <th scope="col" className="px-4 py-3">Instrument</th>
                <th scope="col" className="px-4 py-3 text-right">Weight %</th>
                <th scope="col" className="px-4 py-3 text-right">Actions</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-pmri-border/80">
              {rows.map((row) => {
                const ticker = normalizeTicker(row.ticker);
                const tickerMissing = ticker.length === 0;
                const instrumentMissing = !isKnownInstrument(row);
                const duplicateTicker = ticker.length > 0 && duplicateTickerSet.has(ticker);
                const inputId = `instrument-${row.id}`;

                return (
                  <tr key={row.id} className="bg-white/[0.015] transition hover:bg-white/[0.04]">
                    <td className="px-4 py-4 align-top">
                      <input
                        className={`pmri-focus w-full rounded-lg border bg-pmri-secondary px-3 py-2 font-semibold uppercase text-pmri-text placeholder:text-pmri-muted/70 ${instrumentMissing ? "border-pmri-risk/70" : duplicateTicker ? "border-pmri-amber/70" : "border-pmri-border"}`}
                        value={row.ticker}
                        list={inputId}
                        placeholder="Search ticker or name"
                        onChange={(event) => updateTicker(row.id, event.target.value)}
                        aria-invalid={instrumentMissing}
                      />
                      <datalist id={inputId}>
                        {instrumentUniverse.map((item) => (
                          <option key={item.ticker} value={item.ticker}>{item.instrument}</option>
                        ))}
                      </datalist>
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
                      <div className="rounded-lg border border-pmri-border bg-white/[0.025] px-3 py-2 text-pmri-text2">
                        {row.instrument || "Choose an instrument from the list"}
                      </div>
                    </td>
                    <td className="px-4 py-4 text-right align-top">
                      <input
                        className="pmri-focus data-figure ml-auto w-28 rounded-lg border border-pmri-border bg-pmri-secondary px-3 py-2 text-right font-semibold text-pmri-text"
                        type="number"
                        inputMode="decimal"
                        min="0.01"
                        max="100"
                        step="0.1"
                        value={row.weightInput}
                        onChange={(event) => updateWeight(row.id, event.target.value)}
                        aria-invalid={!isValidWeight(row)}
                      />
                      {!isValidWeight(row) ? (
                        <p className="mt-2 text-xs leading-5 text-pmri-risk">Enter a valid weight greater than 0.</p>
                      ) : null}
                    </td>
                    <td className="px-4 py-4 text-right align-top">
                      <button
                        type="button"
                        onClick={() => removeRow(row.id)}
                        className="pmri-focus rounded-full border border-pmri-border bg-white/[0.03] px-3 py-2 text-xs font-semibold text-pmri-text2 transition hover:border-pmri-risk/50 hover:text-pmri-risk"
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
          <section className="rounded-2xl border border-pmri-border bg-white/[0.025] p-5">
            <div className="flex flex-col gap-3 sm:flex-row sm:items-start sm:justify-between">
              <div>
                <h3 className="text-lg font-semibold text-pmri-text">Before diagnosis</h3>
                <p className="mt-1 text-sm leading-6 text-pmri-muted">{validation.allocationStatus.message}</p>
              </div>
              <div className="flex items-center gap-3">
                <StatusBadge tone={validation.ready ? "green" : "amber"}>
                  {validation.allocationStatus.title}
                </StatusBadge>
                <span className={`data-figure text-xl font-semibold ${validation.weightsAddTo100 ? "text-pmri-positive" : "text-pmri-amber"}`}>
                  {formatWeight(totalWeight)}%
                </span>
              </div>
            </div>

            {!validation.ready && validation.blockingReasons.length > 0 ? (
              <ul className="mt-4 list-disc space-y-1 pl-5 text-sm leading-6 text-pmri-text2">
                {validation.blockingReasons.map((reason) => (
                  <li key={reason}>{reason}</li>
                ))}
              </ul>
            ) : null}

            <ul className="mt-4 grid gap-3 sm:grid-cols-2">
              {checklist.map((item) => (
                <li key={item.label} className="flex items-center gap-3 text-sm text-pmri-text2">
                  <span className={`flex h-6 w-6 items-center justify-center rounded-full border text-xs font-bold ${item.passed ? "border-pmri-positive/40 bg-pmri-positive/10 text-pmri-positive" : "border-pmri-amber/40 bg-pmri-amber/10 text-pmri-amber"}`}>
                    {item.passed ? "✓" : "•"}
                  </span>
                  {item.label}
                </li>
              ))}
            </ul>
          </section>

          <div className="lg:max-w-xs">
            <button
              type="button"
              disabled={!validation.ready}
              className="pmri-focus w-full rounded-full border border-pmri-blue/50 bg-pmri-blue px-6 py-3 text-sm font-semibold text-white shadow-decision transition hover:bg-pmri-blueSoft disabled:cursor-not-allowed disabled:border-pmri-border disabled:bg-white/[0.05] disabled:text-pmri-muted disabled:shadow-none"
            >
              Run portfolio diagnosis
            </button>
            <p className="mt-3 text-sm leading-6 text-pmri-muted">
              Next: Portfolio X-Ray will analyze allocation, concentration, factor exposure, risk contribution, and stress vulnerabilities.
            </p>
          </div>
        </div>
      </div>
    </section>
  );
}
