"use client";

import { useEffect, useRef, useState } from "react";
import { DiagnosisSummaryPanel } from "@/components/diagnosis/DiagnosisSummaryPanel";
import { BackToPortfolioInputAction, ErrorState, LoadingState, LockedState, PortfolioInputAction } from "@/components/ui/States";
import { buildDiagnosisFromReview, diagnosisStageChainReady, useReviewState, type ReviewHolding, type ReviewResult, type StagedReviewProgress } from "@/lib/reviewState";
import type { StagedReviewStatusResponse } from "@/lib/generated/api-types";

const STAGED_POLL_INTERVAL_MS = 2000;
const STAGED_RECOVERY_TIMEOUT_MS = 15 * 60 * 1000;

function sleep(ms: number) {
  return new Promise((resolve) => window.setTimeout(resolve, ms));
}

function holdingsFromRecoveredReview(result: ReviewResult | undefined) {
  const portfolioInput = result?.portfolio_input;
  if (!portfolioInput || typeof portfolioInput !== "object" || Array.isArray(portfolioInput)) return [];
  const holdings = (portfolioInput as { holdings?: unknown }).holdings;
  if (!Array.isArray(holdings)) return [];
  return holdings
    .map((item, index): ReviewHolding | null => {
      if (!item || typeof item !== "object" || Array.isArray(item)) return null;
      const row = item as Record<string, unknown>;
      const type = row.type === "cash" ? "cash" : "instrument";
      const ticker = typeof row.ticker === "string"
        ? row.ticker
        : type === "cash" && typeof row.currency === "string"
          ? `Cash ${row.currency.toUpperCase()}`
          : "";
      const weight = typeof row.weight === "number"
        ? row.weight
        : typeof row.config_weight === "number"
          ? row.config_weight * 100
          : Number.NaN;
      if (!ticker || !Number.isFinite(weight)) return null;
      const currency = typeof row.currency === "string" ? row.currency.toUpperCase() : undefined;
      return {
        id: `recovered-${index}-${ticker}`,
        label: ticker,
        ticker,
        instrument: type === "cash" ? `${currency || "USD"} liquidity position` : ticker,
        weight,
        type,
        currency
      };
    })
    .filter((item): item is ReviewHolding => Boolean(item));
}

function currencyFromRecoveredReview(result: ReviewResult | undefined) {
  const portfolioInput = result?.portfolio_input;
  if (!portfolioInput || typeof portfolioInput !== "object" || Array.isArray(portfolioInput)) return "";
  const currency = (portfolioInput as { investor_currency?: unknown }).investor_currency;
  return typeof currency === "string" && currency.trim() ? currency.trim().toUpperCase() : "";
}

function FailedDiagnosisState() {
  return (
    <ErrorState
      title="Diagnosis is taking longer than expected"
      description="Please try again. Your portfolio input is still saved on this device."
      action={<PortfolioInputAction />}
    />
  );
}

function LockedDiagnosisState() {
  return (
    <LockedState
      title="Complete Portfolio Input first to unlock Diagnosis."
      description="Enter the current portfolio and run diagnosis so this page can reflect the active review."
      missing={["Current holdings and weights", "A completed current-portfolio diagnosis run"]}
      action={<PortfolioInputAction />}
    />
  );
}

function RunningDiagnosisState({
  progress: _progress,
  recoveryError: _recoveryError
}: {
  progress: StagedReviewProgress | undefined;
  recoveryError?: string | null;
}) {
  return (
    <LoadingState
      title="Portfolio MRI is preparing your diagnosis."
      description="This usually takes a moment."
      action={<BackToPortfolioInputAction />}
    />
  );
}

export function DiagnosisScreen() {
  const { activeReview, hydrated, recordStagedProgress, submitPortfolioInput } = useReviewState();
  const [recoveryError, setRecoveryError] = useState<string | null>(null);
  const pollingRef = useRef<string | null>(null);
  const reviewId = activeReview?.reviewId;
  const reviewSummaryReady = Boolean(activeReview?.reviewSummary);
  const runStatus = activeReview?.runStatus;
  const activeHoldings = activeReview?.holdings ?? [];
  const activeCurrency = activeReview?.investorCurrency || "USD";

  useEffect(() => {
    if (!hydrated || !reviewId || reviewSummaryReady || runStatus !== "running") {
      return;
    }
    if (pollingRef.current === reviewId) return;
    pollingRef.current = reviewId;
    let cancelled = false;

    const recoverCompletedDiagnosis = async () => {
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
      if (cancelled) return;
      const recoveredHoldings = holdingsFromRecoveredReview(result.review_result);
      const holdings = recoveredHoldings.length ? recoveredHoldings : activeHoldings;
      const investorCurrency = currencyFromRecoveredReview(result.review_result) || activeCurrency;
      submitPortfolioInput({
        investorCurrency,
        holdings,
        reviewResult: result.review_result
      });
    };

    const poll = async () => {
      const startedAt = Date.now();
      setRecoveryError(null);
      try {
        while (!cancelled && Date.now() - startedAt < STAGED_RECOVERY_TIMEOUT_MS) {
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
            throw new Error(safeError?.message || "Portfolio diagnosis failed during staged execution.");
          }
          if (diagnosisStageChainReady(status)) {
            await recoverCompletedDiagnosis();
            return;
          }
          await sleep(STAGED_POLL_INTERVAL_MS);
        }
        if (!cancelled) {
          setRecoveryError("Portfolio diagnosis is still running. Keep this review ID and this page will keep recovery-safe progress locally.");
        }
      } catch (error) {
        if (!cancelled) setRecoveryError(error instanceof Error ? error.message : "Staged diagnosis recovery failed.");
      } finally {
        if (pollingRef.current === reviewId) pollingRef.current = null;
      }
    };

    void poll();

    return () => {
      cancelled = true;
      if (pollingRef.current === reviewId) pollingRef.current = null;
    };
  }, [activeCurrency, activeHoldings, hydrated, recordStagedProgress, reviewId, reviewSummaryReady, runStatus, submitPortfolioInput]);

  const diagnosisReady = Boolean(
    activeReview?.submitted
    && activeReview.diagnosisReady
    && activeReview.runStatus === "completed"
    && activeReview.reviewSummary
  );
  const failedRealRun = Boolean(activeReview?.runMode === "real_run" && activeReview.runStatus === "failed");
  const runningRealRun = Boolean(activeReview?.runMode === "real_run" && activeReview.runStatus === "running" && !diagnosisReady);
  const diagnosis = diagnosisReady && activeReview ? buildDiagnosisFromReview(activeReview) : null;
  const xraySummary = diagnosisReady ? activeReview?.reviewSummary?.xraySummary : undefined;
  const siteExplanation = activeReview?.reviewSummary?.siteExplanation;

  return (
    <div>
      {!hydrated ? null : failedRealRun && activeReview?.reviewError ? (
        <FailedDiagnosisState />
      ) : runningRealRun ? (
        <RunningDiagnosisState progress={activeReview?.stagedProgress} recoveryError={recoveryError} />
      ) : diagnosis ? <DiagnosisSummaryPanel {...diagnosis} xraySummary={xraySummary} siteExplanation={siteExplanation} /> : <LockedDiagnosisState />}
    </div>
  );
}
