"use client";

import Link from "next/link";
import { useEffect, useRef, useState } from "react";
import { PageHeader } from "@/components/layout/PageHeader";
import { DiagnosisSummaryPanel } from "@/components/diagnosis/DiagnosisSummaryPanel";
import { StatusBadge } from "@/components/ui/StatusBadge";
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
    <section className="pmri-card rounded-2xl border-pmri-risk/35 p-6 md:p-8">
      <StatusBadge tone="amber">Needs retry</StatusBadge>
      <h2 className="mt-4 pmri-heading-section text-2xl text-pmri-text">
        Diagnosis is taking longer than expected
      </h2>
      <p className="mt-3 max-w-2xl text-sm leading-7 text-pmri-text2">
        Please try again. Your portfolio input is still saved on this device.
      </p>
      <Link
        href="/portfolio-input"
        className="pmri-focus mt-6 inline-flex rounded-full border border-pmri-blue/50 bg-pmri-blue px-5 py-2.5 text-sm font-medium text-pmri-bg transition hover:bg-pmri-blueSoft"
      >
        Review portfolio input
      </Link>
    </section>
  );
}

function LockedDiagnosisState() {
  return (
    <section className="pmri-card rounded-2xl p-6 md:p-8">
      <StatusBadge tone="amber">Diagnosis locked</StatusBadge>
      <h2 className="mt-4 pmri-heading-section text-2xl text-pmri-text">
        Complete Portfolio Input first to unlock Diagnosis.
      </h2>
      <p className="mt-3 max-w-2xl text-sm leading-7 text-pmri-muted">
        Enter the current portfolio and run diagnosis so this page can reflect the active review.
      </p>
      <Link
        href="/portfolio-input"
        className="pmri-focus mt-6 inline-flex rounded-full border border-pmri-blue/50 bg-pmri-blue px-5 py-2.5 text-sm font-medium text-pmri-bg transition hover:bg-pmri-blueSoft"
      >
        Go to Portfolio Input
      </Link>
    </section>
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
    <section className="pmri-card rounded-2xl p-6 md:p-8">
      <h2 className="mt-4 pmri-heading-section text-2xl text-pmri-text">
        Portfolio MRI is preparing your diagnosis.
      </h2>
      <p className="mt-3 max-w-2xl text-sm leading-7 text-pmri-muted">
        This usually takes a moment.
      </p>
      <Link
        href="/portfolio-input"
        className="pmri-focus mt-6 inline-flex rounded-full border border-pmri-border/60 px-5 py-2.5 text-sm font-semibold text-pmri-text2 transition hover:border-pmri-blue/40 hover:text-pmri-text"
      >
        Back to Portfolio Input
      </Link>
    </section>
  );
}

export default function DiagnosisPage() {
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
      <PageHeader
        kicker="Step 02 / Portfolio Diagnosis"
        title="Current Portfolio Diagnosis"
        description="Review your current portfolio before testing alternatives."
      />
      {!hydrated ? null : failedRealRun && activeReview?.reviewError ? (
        <FailedDiagnosisState />
      ) : runningRealRun ? (
        <RunningDiagnosisState progress={activeReview?.stagedProgress} recoveryError={recoveryError} />
      ) : diagnosis ? <DiagnosisSummaryPanel {...diagnosis} xraySummary={xraySummary} siteExplanation={siteExplanation} /> : <LockedDiagnosisState />}
    </div>
  );
}
