"use client";

import Link from "next/link";
import { useEffect, useRef, useState } from "react";
import { PageHeader } from "@/components/layout/PageHeader";
import { DiagnosisSummaryPanel } from "@/components/diagnosis/DiagnosisSummaryPanel";
import { SiteExplanationHierarchy } from "@/components/explanation/SiteExplanationHierarchy";
import { StatusBadge } from "@/components/ui/StatusBadge";
import { buildDiagnosisFromReview, useReviewState, type ReviewHolding, type ReviewResult, type StagedReviewProgress } from "@/lib/reviewState";
import type { StagedReviewStatusResponse } from "@/lib/generated/api-types";

const STAGED_POLL_INTERVAL_MS = 2000;
const STAGED_RECOVERY_TIMEOUT_MS = 15 * 60 * 1000;

function sleep(ms: number) {
  return new Promise((resolve) => window.setTimeout(resolve, ms));
}

function stageReady(progress: Pick<StagedReviewStatusResponse, "stages"> | StagedReviewProgress | null | undefined, stage: string) {
  const status = progress?.stages?.[stage]?.status;
  return status === "completed" || status === "partial";
}

function diagnosisChainReady(progress: Pick<StagedReviewStatusResponse, "stages"> | StagedReviewProgress) {
  return stageReady(progress, "xray")
    && stageReady(progress, "stress")
    && stageReady(progress, "problem_classification")
    && stageReady(progress, "launchpad_builder");
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

function FailedDiagnosisState({ message, details }: { message: string; details?: string }) {
  return (
    <section className="pmri-card rounded-2xl border-pmri-risk/35 p-6 md:p-8">
      <StatusBadge tone="red">Diagnosis failed</StatusBadge>
      <h2 className="mt-4 pmri-heading-section text-2xl text-pmri-text">
        Portfolio diagnosis could not be completed.
      </h2>
      <p className="mt-3 max-w-2xl text-sm leading-7 text-pmri-text2">{message}</p>
      {details ? (
        <pre className="mt-4 max-h-56 overflow-auto rounded-xl border border-pmri-border bg-pmri-secondary p-4 text-xs leading-5 text-pmri-muted">{details}</pre>
      ) : null}
      <Link
        href="/portfolio-input"
        className="pmri-focus mt-6 inline-flex rounded-full border border-pmri-blue/50 bg-pmri-blue px-5 py-2.5 text-sm font-medium text-pmri-bg transition hover:bg-pmri-blueSoft"
      >
        Back to Portfolio Input
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
  progress,
  recoveryError
}: {
  progress: StagedReviewProgress | undefined;
  recoveryError?: string | null;
}) {
  return (
    <section className="pmri-card rounded-2xl p-6 md:p-8">
      <StatusBadge tone="blue">Diagnosis running</StatusBadge>
      <h2 className="mt-4 pmri-heading-section text-2xl text-pmri-text">
        Portfolio MRI is preparing your diagnosis.
      </h2>
      <p className="mt-3 max-w-2xl text-sm leading-7 text-pmri-muted">
        You can keep this page open or refresh it. The review ID is saved locally and the results
        will appear here when the backend finishes.
      </p>
      <div className="mt-5 rounded-2xl border border-pmri-blue/25 bg-pmri-blue/10 p-4">
        <div className="flex items-center gap-2 text-sm font-semibold leading-5 text-pmri-text">
          <span className="pmri-spinner" aria-hidden="true" />
          Preparing your diagnosis...
        </div>
        <p className="mt-3 max-w-2xl text-xs leading-5 text-pmri-muted">
          Portfolio MRI is reviewing allocation, concentration, risk drivers, and stress vulnerabilities.
          Results will appear automatically when the diagnosis is ready.
        </p>
        {progress?.safeError ? (
          <p className="mt-3 rounded-xl border border-pmri-risk/35 bg-pmri-risk/10 px-3 py-2 text-xs leading-5 text-pmri-risk">
            {progress.safeError.message}
          </p>
        ) : recoveryError ? (
          <p className="mt-3 rounded-xl border border-pmri-risk/35 bg-pmri-risk/10 px-3 py-2 text-xs leading-5 text-pmri-risk">
            {recoveryError}
          </p>
        ) : null}
      </div>
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
          if (diagnosisChainReady(status)) {
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
        description="Current-portfolio review before any candidate test."
      />
      <SiteExplanationHierarchy
        bundle={siteExplanation}
        screen="diagnosis"
        fallbackTitle="Diagnosis explanation"
      />
      {!hydrated ? null : failedRealRun && activeReview?.reviewError ? (
        <FailedDiagnosisState message={activeReview.reviewError.message} details={activeReview.reviewError.details} />
      ) : runningRealRun ? (
        <RunningDiagnosisState progress={activeReview?.stagedProgress} recoveryError={recoveryError} />
      ) : diagnosis ? <DiagnosisSummaryPanel {...diagnosis} xraySummary={xraySummary} /> : <LockedDiagnosisState />}
    </div>
  );
}
