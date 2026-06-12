"use client";

import { useEffect, useMemo, useState } from "react";
import Link from "next/link";
import { useRouter } from "next/navigation";
import { PageHeader } from "@/components/layout/PageHeader";
import { SiteExplanationHierarchy } from "@/components/explanation/SiteExplanationHierarchy";
import { CandidateComparisonPanel } from "@/components/comparison/CandidateComparisonPanel";
import { TradeoffSummary } from "@/components/comparison/TradeoffSummary";
import { StatusBadge } from "@/components/ui/StatusBadge";
import { formatUnknownValue, normalizeDisplaySentence } from "@/lib/displayLabels";
import { useReviewState } from "@/lib/reviewState";

type JsonRecord = Record<string, unknown>;

function isRecord(value: unknown): value is JsonRecord {
  return Boolean(value) && typeof value === "object" && !Array.isArray(value);
}

function textValue(value: unknown, fallback = "Unavailable") {
  return typeof value === "string" && value.trim() ? formatUnknownValue(value, fallback) : fallback;
}

function errorTextFromResponse(value: unknown) {
  if (!isRecord(value)) return "Comparison failed.";
  const message = textValue(value.error, "Comparison failed.");
  const details = value.details;
  if (typeof details === "string" && details.trim()) return `${message} ${normalizeDisplaySentence(details)}`;
  if (Array.isArray(details)) {
    const safeDetails = details
      .map((item) => (typeof item === "string" ? normalizeDisplaySentence(item) : ""))
      .filter(Boolean)
      .join(" ");
    return safeDetails ? `${message} ${safeDetails}` : message;
  }
  return message;
}

function statusKey(value: unknown) {
  return String(value ?? "")
    .trim()
    .toLowerCase()
    .replace(/[^a-z0-9]+/g, "_")
    .replace(/^_+|_+$/g, "");
}

function isUnavailableDisplay(value: unknown) {
  const key = statusKey(value);
  return !key
    || key === "not_available_yet"
    || key === "not_available"
    || key === "unavailable"
    || key === "evidence_unavailable"
    || key === "candidate_metric_unavailable"
    || key === "metric_unavailable"
    || key === "unclear";
}

function isDisplayableMetric(metric: { current: string; candidate: string; direction: string }) {
  return !isUnavailableDisplay(metric.current)
    && !isUnavailableDisplay(metric.candidate)
    && statusKey(metric.direction) !== "unclear";
}

function comparisonIsAvailable(comparison: NonNullable<ReturnType<typeof useReviewState>["activeReview"]>["comparisonResult"] | undefined) {
  return Boolean(
    comparison
    && statusKey(comparison.status) === "completed"
    && statusKey(comparison.comparisonStatus) === "available"
    && comparison.metrics.some(isDisplayableMetric)
  );
}

function comparisonCanGenerateVerdict(comparison: NonNullable<ReturnType<typeof useReviewState>["activeReview"]>["comparisonResult"] | undefined) {
  return Boolean(
    comparison
    && statusKey(comparison.status) === "completed"
    && statusKey(comparison.comparisonStatus) === "available"
  );
}

function comparisonMissingReasons({
  comparison,
  comparisonError,
  candidateNotComparable
}: {
  comparison: NonNullable<ReturnType<typeof useReviewState>["activeReview"]>["comparisonResult"] | undefined;
  comparisonError?: string;
  candidateNotComparable?: boolean;
}) {
  const reasons = new Set<string>();
  if (candidateNotComparable) reasons.add("The generated candidate is not compare-ready for this review.");
  if (!candidateNotComparable) reasons.add("Candidate metrics are unavailable");
  reasons.add("Trade-off comparison evidence could not be completed");
  if (comparison?.comparisonStatus && statusKey(comparison.comparisonStatus) !== "available") {
    reasons.add(formatUnknownValue(comparison.comparisonStatus, "Comparison unavailable"));
  }
  comparison?.warnings.forEach((item) => reasons.add(normalizeDisplaySentence(item)));
  if (comparisonError) reasons.add(normalizeDisplaySentence(comparisonError));
  return Array.from(reasons).slice(0, 5);
}

function EmptyState({
  title,
  description,
  href = "/hypothesis",
  action = "Return to Hypothesis Builder",
  missing,
  nextStep
}: {
  title: string;
  description: string;
  href?: string;
  action?: string;
  missing?: string[];
  nextStep?: string;
}) {
  return (
    <section className="pmri-card rounded-3xl p-6">
      <p className="pmri-heading-section text-lg text-pmri-text">{title}</p>
      <p className="mt-2 max-w-2xl text-sm leading-7 text-pmri-muted">{description}</p>
      {missing?.length ? (
        <div className="mt-5 rounded-2xl border border-pmri-border/45 bg-white/[0.026] p-4">
          <p className="pmri-label">What is missing</p>
          <ul className="mt-3 space-y-2 text-sm leading-6 text-pmri-text2">
            {missing.map((item) => <li key={item}>• {item}</li>)}
          </ul>
        </div>
      ) : null}
      {nextStep ? (
        <p className="mt-4 max-w-2xl text-sm leading-7 text-pmri-text2">
          <span className="font-medium text-pmri-text">Next step:</span> {nextStep}
        </p>
      ) : null}
      <Link
        href={href}
        className="pmri-focus mt-5 inline-flex rounded-full border border-pmri-blue/50 bg-pmri-blue px-5 py-2.5 text-sm font-medium text-pmri-bg shadow-decision transition hover:bg-pmri-blueSoft"
      >
        {action}
      </Link>
    </section>
  );
}

export default function ComparisonPage() {
  const router = useRouter();
  const { activeReview, hydrated, markComparisonReady, recordComparisonResult } = useReviewState();
  const [isComparing, setIsComparing] = useState(false);
  const [comparisonError, setComparisonError] = useState<string | undefined>();

  const reviewId = activeReview?.reviewId ?? activeReview?.reviewSummary?.reviewId ?? activeReview?.reviewResult?.review_id;
  const candidateGeneration = activeReview?.candidateGeneration;
  const selectedCardId = candidateGeneration?.selectedCardId;
  const candidateId = candidateGeneration?.candidateId;
  const comparison = activeReview?.comparisonResult;
  const hasGeneratedCandidate = Boolean(candidateGeneration?.status === "completed" && candidateId && selectedCardId);
  const comparisonMatchesCandidate = Boolean(
    comparison
    && selectedCardId
    && candidateId
    && comparison.selectedCardId === selectedCardId
    && comparison.candidateId === candidateId
  );
  const canRunComparison = Boolean(
    hydrated
    && reviewId
    && selectedCardId
    && candidateId
    && candidateGeneration?.status === "completed"
    && candidateGeneration.canCompare
  );
  const validComparisonAvailable = comparisonMatchesCandidate && comparisonIsAvailable(comparison);
  const canGenerateEvidenceVerdict = comparisonMatchesCandidate && comparisonCanGenerateVerdict(comparison);
  const displayableMetrics = useMemo(
    () => comparison?.metrics.filter(isDisplayableMetric) ?? [],
    [comparison]
  );
  const comparisonForDisplay = comparison && displayableMetrics.length
    ? { ...comparison, metrics: displayableMetrics }
    : comparison;
  const siteExplanation = activeReview?.reviewSummary?.siteExplanation;

  useEffect(() => {
    setComparisonError(undefined);
  }, [reviewId, selectedCardId, candidateId]);

  const tradeoffDetail = useMemo(() => {
    if (!comparisonMatchesCandidate || !comparison) return [];
    return [
      comparison.turnover,
      comparison.estimatedCost,
      comparison.materiality
    ].filter(Boolean);
  }, [comparison, comparisonMatchesCandidate]);

  async function handleRunComparison() {
    if (!reviewId || !selectedCardId) return;
    setIsComparing(true);
    setComparisonError(undefined);

    try {
      const response = await fetch("/api/portfolio/comparison/generate", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          review_id: reviewId,
          selected_card_id: selectedCardId
        })
      });
      const result = await response.json() as unknown;
      if (!response.ok || !isRecord(result) || result.status !== "completed") {
        setComparisonError(errorTextFromResponse(result));
        return;
      }
      recordComparisonResult(result);
    } catch {
      setComparisonError("Comparison failed. Trade-off evidence was not created.");
    } finally {
      setIsComparing(false);
    }
  }

  if (!hydrated) return null;

  const showCandidateMissingState = !hasGeneratedCandidate;
  const showCandidateNotComparableState = hasGeneratedCandidate && !candidateGeneration?.canCompare;
  const showMetricsUnavailableState = !showCandidateMissingState
    && (showCandidateNotComparableState || Boolean(comparisonError) || (comparisonMatchesCandidate && !validComparisonAvailable));
  const showReadyToCompareState = canRunComparison
    && !comparisonMatchesCandidate
    && !comparisonError
    && !showCandidateMissingState
    && !showCandidateNotComparableState;

  const validComparisonForDisplay = validComparisonAvailable && comparisonForDisplay
    ? comparisonForDisplay
    : undefined;

  const comparisonAvailabilityTitle = showCandidateNotComparableState
    ? "Candidate cannot be compared yet"
    : "Comparison metrics unavailable";
  const comparisonAvailabilityDescription = showCandidateNotComparableState
    ? "A candidate was generated, but it is not ready for a current-vs-candidate trade-off comparison."
    : "The candidate exists, but Portfolio MRI does not have enough current candidate metrics to compare it against the current portfolio.";

  return (
    <div>
        <PageHeader
          kicker="Step 05 / Comparison"
          title="Current vs Candidate Comparison"
          description="This step compares the current portfolio with one generated diagnostic candidate. It does not make a final decision or create a rebalance instruction."
        >
          <StatusBadge tone={validComparisonAvailable ? "green" : "amber"}>
            {validComparisonAvailable ? "Active comparison" : "Comparison required"}
          </StatusBadge>
        </PageHeader>
        <SiteExplanationHierarchy
          bundle={siteExplanation}
          screen="comparison"
          fallbackTitle="Comparison explanation"
        />

        {showCandidateMissingState ? (
          <EmptyState
            title="Generate a test candidate first"
            description="Portfolio MRI needs one generated diagnostic test candidate before it can compare current vs candidate trade-offs."
            nextStep="Return to Hypothesis Builder and generate a candidate."
          />
        ) : null}

        {showMetricsUnavailableState ? (
          <section className="pmri-card rounded-3xl p-6">
            <p className="pmri-heading-section text-lg text-pmri-text">{comparisonAvailabilityTitle}</p>
            <p className="mt-2 max-w-2xl text-sm leading-7 text-pmri-muted">{comparisonAvailabilityDescription}</p>
            <div className="mt-5 rounded-2xl border border-pmri-border/45 bg-white/[0.026] p-4">
              <p className="pmri-label">What is missing</p>
              <ul className="mt-3 space-y-2 text-sm leading-6 text-pmri-text2">
                {comparisonMissingReasons({ comparison, comparisonError, candidateNotComparable: showCandidateNotComparableState }).map((item) => <li key={item}>• {item}</li>)}
              </ul>
            </div>
            <p className="mt-4 max-w-2xl text-sm leading-7 text-pmri-text2">
              <span className="font-medium text-pmri-text">Next step:</span>{" "}
              {canGenerateEvidenceVerdict
                ? "Generate an evidence-insufficient verdict, or return to Hypothesis Builder to test another setup."
                : "Regenerate candidate, adjust setup, or resolve data quality."}
            </p>
            <div className="mt-5 flex flex-wrap gap-3">
              {canGenerateEvidenceVerdict ? (
                <button
                  type="button"
                  className="pmri-focus rounded-full border border-pmri-blue/50 bg-pmri-blue px-5 py-2.5 text-sm font-medium text-pmri-bg shadow-decision transition hover:bg-pmri-blueSoft"
                  onClick={() => {
                    markComparisonReady();
                    router.push("/verdict");
                  }}
                >
                  Continue to verdict
                </button>
              ) : null}
              <Link
                href="/hypothesis"
                className="pmri-focus inline-flex rounded-full border border-pmri-border bg-white/[0.035] px-5 py-2.5 text-sm font-medium text-pmri-text transition hover:border-pmri-blue/60"
              >
                Return to Hypothesis Builder
              </Link>
            </div>
          </section>
        ) : null}

        {showReadyToCompareState ? (
          <section className="pmri-card rounded-3xl p-6">
            <div className="flex flex-col gap-4 md:flex-row md:items-start md:justify-between">
              <div>
                <p className="pmri-label">Ready for comparison</p>
                <h2 className="mt-2 pmri-heading-section text-xl text-pmri-text">Run diagnostic comparison</h2>
                <p className="mt-3 max-w-3xl text-sm leading-7 text-pmri-muted">
                  The generated candidate is compare-ready. This step creates comparison evidence only; it does not decide whether to change the portfolio.
                </p>
              </div>
              <StatusBadge tone="slate">Diagnostic comparison</StatusBadge>
            </div>
            <button
              type="button"
              disabled={isComparing}
              onClick={handleRunComparison}
              className={`mt-6 rounded-full border px-5 py-3 text-sm font-medium transition ${
                isComparing
                  ? "cursor-not-allowed border-white/10 bg-white/10 text-pmri-muted"
                  : "pmri-focus border-pmri-blue/50 bg-pmri-blue text-pmri-bg shadow-decision hover:bg-pmri-blueSoft"
              }`}
            >
              {isComparing ? "Comparing candidate..." : "Compare candidate"}
            </button>
            {comparisonError ? (
              <p className="mt-4 rounded-xl border border-pmri-red/35 bg-pmri-red/10 p-3 text-sm leading-6 text-pmri-red">
                {comparisonError}
              </p>
            ) : null}
          </section>
        ) : null}

        {validComparisonForDisplay ? (
          <div className="space-y-6">
            <TradeoffSummary
              improved={validComparisonForDisplay.improved}
              worsened={validComparisonForDisplay.worsened}
              unclear={validComparisonForDisplay.unclear}
              costs={tradeoffDetail}
              evidenceQuality={validComparisonForDisplay.evidenceQuality}
              boundary={validComparisonForDisplay.candidateBoundary}
            />
            <CandidateComparisonPanel {...validComparisonForDisplay} />
            <section className="grid gap-4 lg:grid-cols-3">
              <article className="rounded-2xl border border-pmri-border bg-white/[0.025] p-4">
                <StatusBadge tone="blue">Turnover / cost</StatusBadge>
                <p className="mt-3 text-sm leading-7 text-pmri-text2">{validComparisonForDisplay.turnover}</p>
                <p className="mt-2 text-sm leading-7 text-pmri-muted">{validComparisonForDisplay.estimatedCost}</p>
              </article>
              <article className="rounded-2xl border border-pmri-border bg-white/[0.025] p-4">
                <StatusBadge tone="amber">Success criteria evaluation</StatusBadge>
                <p className="mt-3 text-sm leading-7 text-pmri-text2">{validComparisonForDisplay.summary}</p>
                <p className="mt-2 text-sm leading-7 text-pmri-muted">{validComparisonForDisplay.materiality}</p>
              </article>
              <article className="rounded-2xl border border-pmri-border bg-white/[0.025] p-4">
                <StatusBadge tone="slate">Warnings</StatusBadge>
                <ul className="mt-3 space-y-2 text-sm leading-7 text-pmri-muted">
                  {(validComparisonForDisplay.warnings.length ? validComparisonForDisplay.warnings : ["No additional comparison warnings are available."]).map((item) => (
                    <li key={item}>• {item}</li>
                  ))}
                </ul>
              </article>
            </section>
            <div className="rounded-2xl border border-pmri-border bg-white/[0.025] p-4">
              <p className="mb-3 text-sm leading-7 text-pmri-muted">
                Continue only after reviewing the trade-offs. The next step evaluates decision-support evidence; this page does not make the final decision.
              </p>
              <button
                type="button"
                className="pmri-focus rounded-full border border-pmri-blue/50 bg-pmri-blue px-5 py-2.5 text-sm font-medium text-pmri-bg shadow-decision transition hover:bg-pmri-blueSoft"
                onClick={() => {
                  markComparisonReady();
                  router.push("/verdict");
                }}
              >
                Continue to verdict
              </button>
            </div>
          </div>
        ) : null}
    </div>
  );
}
