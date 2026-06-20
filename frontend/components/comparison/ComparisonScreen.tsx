"use client";

import { useEffect, useMemo, useRef, useState } from "react";
import Link from "next/link";
import { useRouter } from "next/navigation";
import { SiteExplanationHierarchy } from "@/components/explanation/SiteExplanationHierarchy";
import { ClientFitContextCard } from "@/components/client-fit/ClientFitContextCard";
import { ActiveDiagnosticTestContext } from "@/components/ui/ActiveDiagnosticTestContext";
import { StatusBadge } from "@/components/ui/StatusBadge";
import { VerdictHero } from "@/components/ui/VerdictHero";
import { EvidenceSummary } from "@/components/ui/EvidenceSummary";
import { CaseFileTopCards } from "@/components/ui/CaseFileCards";
import { ComparisonMetricMatrix } from "@/components/ui/MetricMatrix";
import { formatUnknownValue, normalizeDisplaySentence } from "@/lib/displayLabels";
import { deriveComparisonPublicSummary } from "@/lib/comparisonPresentation";
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

function formatWeight(value: number, unit: "percent" | "fraction") {
  const normalized = unit === "fraction" ? value * 100 : value;
  return `${normalized.toFixed(2).replace(/\.?0+$/, "")}%`;
}

function AllocationList({
  title,
  subtitle,
  weightUnit,
  items
}: {
  title: string;
  subtitle: string;
  weightUnit: "percent" | "fraction";
  items: Array<{ ticker: string; weight: number }>;
}) {
  return (
    <article className="rounded-2xl border border-pmri-border bg-white/[0.025] p-4">
      <p className="pmri-label">{subtitle}</p>
      <h2 className="mt-2 pmri-heading-section text-lg text-pmri-text">{title}</h2>
      {items.length ? (
        <ul className="mt-4 grid gap-2">
          {items.map((item) => (
            <li key={item.ticker} className="flex items-center justify-between rounded-xl bg-white/[0.04] px-3 py-2 text-sm">
              <span className="font-medium text-pmri-text">{item.ticker}</span>
              <span className="text-pmri-text2">{formatWeight(item.weight, weightUnit)}</span>
            </li>
          ))}
        </ul>
      ) : (
        <p className="mt-4 text-sm leading-6 text-pmri-muted">Weights are unavailable for this portfolio.</p>
      )}
    </article>
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
  if (candidateNotComparable) reasons.add("The generated test candidate is not compare-ready for this review.");
  if (!candidateNotComparable) reasons.add("Test candidate metrics are unavailable");
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
            {missing.map((item) => <li key={item}>- {item}</li>)}
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

export function ComparisonScreen() {
  const router = useRouter();
  const { activeReview, hydrated, markComparisonReady, recordComparisonResult } = useReviewState();
  const [isComparing, setIsComparing] = useState(false);
  const [comparisonError, setComparisonError] = useState<string | undefined>();
  const autoComparisonKeyRef = useRef<string | null>(null);

  const reviewId = activeReview?.reviewId ?? activeReview?.reviewSummary?.reviewId ?? activeReview?.reviewResult?.review_id;
  const candidateGeneration = activeReview?.candidateGeneration;
  const selectedCardId = candidateGeneration?.selectedCardId;
  const candidateId = candidateGeneration?.candidateId;
  const comparison = activeReview?.comparisonResult;
  const hasLiveLineage = Boolean(activeReview?.lineageAvailable && !activeReview?.readOnlyHistory);
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
    && hasLiveLineage
    && candidateGeneration?.status === "completed"
    && candidateGeneration.canCompare
  );
  const validComparisonAvailable = comparisonMatchesCandidate && comparisonIsAvailable(comparison);
  const canGenerateEvidenceVerdict = hasLiveLineage && comparisonMatchesCandidate && comparisonCanGenerateVerdict(comparison);
  const displayableMetrics = useMemo(
    () => comparison?.metrics.filter(isDisplayableMetric) ?? [],
    [comparison]
  );
  const comparisonForDisplay = comparison && displayableMetrics.length
    ? { ...comparison, metrics: displayableMetrics }
    : comparison;
  const siteExplanation = activeReview?.reviewSummary?.siteExplanation;
  const clientFitForStage = comparison?.clientFit ?? activeReview?.reviewSummary?.clientFit;
  const currentWeights = (activeReview?.holdings ?? []).map((holding) => ({
    ticker: holding.ticker,
    weight: holding.weight
  }));
  const candidateWeights = candidateGeneration?.weights ?? [];

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
          selected_card_id: selectedCardId,
          candidate_id: candidateId
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

  useEffect(() => {
    if (!canRunComparison || comparisonMatchesCandidate || comparisonError || isComparing) return;
    const autoKey = [reviewId, selectedCardId, candidateId, candidateGeneration?.generatedAt ?? "no_generation_time"].join("|");
    if (autoComparisonKeyRef.current === autoKey) return;
    autoComparisonKeyRef.current = autoKey;
    void handleRunComparison();
  }, [canRunComparison, candidateGeneration?.generatedAt, candidateId, comparisonError, comparisonMatchesCandidate, isComparing, reviewId, selectedCardId]);

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
  const comparisonPublicSummary = validComparisonForDisplay
    ? deriveComparisonPublicSummary({
      improved: validComparisonForDisplay.improved,
      worsened: validComparisonForDisplay.worsened,
      evidenceQuality: validComparisonForDisplay.evidenceQuality,
      metrics: validComparisonForDisplay.metrics,
      materiality: validComparisonForDisplay.materiality
    })
    : undefined;

  const comparisonAvailabilityTitle = showCandidateNotComparableState
    ? "Test candidate cannot be compared yet"
    : "Comparison metrics unavailable";
  const comparisonAvailabilityDescription = showCandidateNotComparableState
    ? "A diagnostic test candidate was generated, but it is not ready for a trade-off comparison."
    : "The test candidate exists, but Portfolio MRI does not have enough current metrics to compare it against the current portfolio.";

  return (
    <div>
      <div className="mb-6 space-y-5">
        <VerdictHero
          stepContext="Step 6 of 8 - Comparison"
          headline={validComparisonAvailable ? "Diagnostic test changes the evidence, with trade-offs" : "Current vs diagnostic test evidence is required"}
          interpretation="This page compares the current portfolio with one generated diagnostic test candidate and highlights the main trade-offs."
          facts={[
            { label: "Current portfolio", value: currentWeights.length ? `${currentWeights.length} holdings` : "Input not ready" },
            { label: "Test candidate", value: candidateGeneration?.methodLabel ?? "Candidate not generated" }
          ]}
        />
        {validComparisonForDisplay ? (
          <CaseFileTopCards
            cards={[
              {
                eyebrow: "What improved",
                title: comparisonPublicSummary?.improved ?? "No material improvement returned",
                value: validComparisonForDisplay.metrics.find((metric) => metric.tone === "blue")?.direction,
                description: "This is the strongest improvement signal to carry into the verdict step.",
                tone: "blue"
              },
              {
                eyebrow: "What worsened",
                title: comparisonPublicSummary?.worsened ?? "No material worsening returned",
                value: tradeoffDetail[0] ?? validComparisonForDisplay.materiality,
                description: "This is the main cost or trade-off that could make an improvement less useful.",
                tone: validComparisonForDisplay.worsened.length ? "amber" : "slate"
              },
              {
                eyebrow: "Is the trade-off meaningful?",
                title: validComparisonForDisplay.materiality || "Materiality needs review",
                value: validComparisonForDisplay.evidenceQuality,
                description: "Comparison evidence is not a winner; it tells the verdict step whether the improvement is large enough to matter.",
                tone: /limited|insufficient|partial/i.test(validComparisonForDisplay.evidenceQuality) ? "amber" : "slate"
              }
            ]}
          />
        ) : null}
        {validComparisonForDisplay ? (
          <EvidenceSummary
            title="Comparison evidence summary"
            description="Only material comparison facts are promoted before the matrix."
            emptyMessage="Comparison evidence is not ready; generate one test candidate and complete a same-candidate comparison first."
            items={[
              { label: "Improved", value: comparisonPublicSummary?.improved ?? "No material improvement returned" },
              { label: "Trade-off", value: comparisonPublicSummary?.worsened ?? comparisonPublicSummary?.materiality ?? "No main trade-off returned", tone: validComparisonForDisplay.worsened.length ? "amber" : "slate" },
              { label: "Evidence quality", value: validComparisonForDisplay.evidenceQuality, tone: /limited|insufficient|partial/i.test(validComparisonForDisplay.evidenceQuality) ? "amber" : "slate" }
            ]}
          />
        ) : null}
      </div>

      <div className="mb-6">
        <ActiveDiagnosticTestContext
          testName={candidateGeneration?.methodLabel ?? "Diagnostic test candidate not generated"}
          purpose="Comparison checks whether the generated test candidate changes the current portfolio evidence enough to support a cautious verdict."
          candidateName={candidateGeneration?.methodLabel}
          evidenceQuality={validComparisonAvailable ? "Trade-off evidence ready" : "Trade-off evidence not ready"}
          limitation="Comparison is trade-off evidence only. It is not a final verdict or trade instruction."
          tone={validComparisonAvailable ? "blue" : "amber"}
        />
      </div>

      {validComparisonAvailable ? (
        <SiteExplanationHierarchy bundle={siteExplanation} screen="comparison" fallbackTitle="Comparison explanation" />
      ) : null}

      {activeReview?.readOnlyHistory ? (
        <section className="mb-6 rounded-2xl border border-pmri-border/45 bg-white/[0.026] p-4">
          <StatusBadge tone="slate">Historical</StatusBadge>
          <p className="mt-3 max-w-3xl text-sm leading-7 text-pmri-text2">
            This is compact review history. Same-run evidence is not recoverable from this compact snapshot, so Portfolio MRI will not reuse this comparison to create a new verdict.
          </p>
        </section>
      ) : null}

      {hasGeneratedCandidate ? (
        <section className="mb-6 pmri-card rounded-3xl p-6">
          <div className="flex flex-col gap-3 md:flex-row md:items-start md:justify-between">
            <div>
              <p className="pmri-label">Generated diagnostic test candidate</p>
              <h2 className="mt-2 pmri-heading-section text-xl text-pmri-text">
                Current portfolio vs {candidateGeneration?.methodLabel ?? "generated test candidate"}
              </h2>
              <p className="mt-3 max-w-3xl text-sm leading-7 text-pmri-muted">
                These are the two portfolios being compared.
              </p>
            </div>
            <StatusBadge tone={isComparing ? "blue" : validComparisonAvailable ? "blue" : "amber"}>
              {isComparing ? "Comparison running" : validComparisonAvailable ? "Comparison available" : "Preparing comparison"}
            </StatusBadge>
          </div>
        </section>
      ) : null}

      {showCandidateMissingState ? (
        <EmptyState
          title="Generate a diagnostic test candidate first"
          description="Portfolio MRI needs one generated diagnostic test candidate before it can compare trade-offs against the current portfolio."
          nextStep="Return to Hypothesis Builder and generate a diagnostic test candidate."
        />
      ) : null}

      {showMetricsUnavailableState ? (
        <section className="pmri-card rounded-3xl p-6">
          <p className="pmri-heading-section text-lg text-pmri-text">{comparisonAvailabilityTitle}</p>
          <p className="mt-2 max-w-2xl text-sm leading-7 text-pmri-muted">{comparisonAvailabilityDescription}</p>
          <div className="mt-5 rounded-2xl border border-pmri-border/45 bg-white/[0.026] p-4">
            <p className="pmri-label">What is missing</p>
            <ul className="mt-3 space-y-2 text-sm leading-6 text-pmri-text2">
              {comparisonMissingReasons({ comparison, comparisonError, candidateNotComparable: showCandidateNotComparableState }).map((item) => <li key={item}>- {item}</li>)}
            </ul>
          </div>
          <p className="mt-4 max-w-2xl text-sm leading-7 text-pmri-text2">
            <span className="font-medium text-pmri-text">Next step:</span>{" "}
            {canGenerateEvidenceVerdict
              ? "Generate an evidence-insufficient verdict, or return to Hypothesis Builder to test another setup."
              : "Regenerate the test candidate, adjust setup, or resolve data quality."}
          </p>
          <div className="mt-5 flex flex-wrap gap-3">
            {comparisonError && canRunComparison ? (
              <button
                type="button"
                disabled={isComparing}
                className={`rounded-full border px-5 py-2.5 text-sm font-medium transition ${
                  isComparing
                    ? "cursor-not-allowed border-white/10 bg-white/10 text-pmri-muted"
                    : "pmri-focus border-pmri-blue/50 bg-pmri-blue text-pmri-bg shadow-decision hover:bg-pmri-blueSoft"
                }`}
                onClick={handleRunComparison}
              >
                {isComparing ? "Retrying comparison..." : "Retry comparison"}
              </button>
            ) : null}
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
            <Link href="/hypothesis" className="pmri-focus inline-flex rounded-full border border-pmri-border bg-white/[0.035] px-5 py-2.5 text-sm font-medium text-pmri-text transition hover:border-pmri-blue/60">
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
                The generated diagnostic test candidate is compare-ready. This step creates the comparison evidence.
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
            {isComparing ? "Comparing test candidate..." : "Compare test candidate"}
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
          <ComparisonMetricMatrix
            groups={[
              {
                title: "Risk improvement",
                rows: validComparisonForDisplay.metrics
                  .filter((metric) => metric.tone === "blue" || /improv|lower|reduce|better/i.test(metric.direction))
                  .map((metric) => ({ metric: metric.metric, currentPortfolio: metric.current, candidatePortfolio: metric.candidate, change: metric.direction, interpretation: metric.tradeoff, material: true }))
              },
              {
                title: "Trade-offs",
                rows: [
                  ...validComparisonForDisplay.metrics.filter((metric) => metric.tone === "amber" || metric.tone === "red" || /worsen|cost|turnover|higher/i.test(metric.direction)).map((metric) => ({ metric: metric.metric, currentPortfolio: metric.current, candidatePortfolio: metric.candidate, change: metric.direction, status: metric.tone === "red" || metric.tone === "amber" ? { label: metric.direction, tone: metric.tone } : undefined, interpretation: metric.tradeoff, material: true })),
                  { metric: "Turnover", currentPortfolio: "Current allocation", candidatePortfolio: candidateGeneration?.methodLabel ?? "Test candidate", change: validComparisonForDisplay.turnover, interpretation: validComparisonForDisplay.estimatedCost }
                ]
              },
              {
                title: "Fit impact",
                rows: [{ metric: "Client Fit context", currentPortfolio: clientFitForStage?.status_label ?? "Unavailable", candidatePortfolio: "Test impact", change: "Limited", interpretation: "Profile context for the comparison." }]
              },
              {
                title: "Evidence quality",
                rows: [
                  { metric: "Evidence quality", currentPortfolio: validComparisonForDisplay.evidenceQuality, candidatePortfolio: validComparisonForDisplay.materiality, change: validComparisonForDisplay.warnings.length ? "Limited" : "Available", status: validComparisonForDisplay.warnings.length ? { label: "Limited", tone: "amber" } : undefined, interpretation: validComparisonForDisplay.summary, material: Boolean(validComparisonForDisplay.warnings.length) }
                ]
              }
            ].map((group) => ({ ...group, rows: group.rows.length ? group.rows : [{ metric: "No material row", currentPortfolio: "Unavailable", candidatePortfolio: "Unavailable", change: "Unavailable", interpretation: "No material evidence was returned for this group." }] }))}
          />
          <ClientFitContextCard
            clientFit={clientFitForStage}
            title="Current vs diagnostic test vs Client Fit"
            description="This comparison can show whether the diagnostic test candidate changes profile-fit evidence."
            structuralIssueNote="Compare the diagnostic test candidate against both diagnosis evidence and profile targets."
            compact
          />
          <details className="pmri-card rounded-3xl p-5 md:p-6">
            <summary className="cursor-pointer list-none">
              <p className="pmri-label">Secondary detail</p>
              <h2 className="pmri-heading-section mt-2 text-xl text-pmri-text">Allocations, warnings, and technical comparison notes</h2>
            </summary>
            <div className="mt-5 grid gap-4 lg:grid-cols-2">
              <AllocationList title="Current portfolio" subtitle="Input allocation" weightUnit="percent" items={currentWeights} />
              <AllocationList title={candidateGeneration?.methodLabel ?? "Generated test candidate"} subtitle="Test candidate allocation" weightUnit="fraction" items={candidateWeights} />
            </div>
            <ul className="mt-5 space-y-2 text-sm leading-7 text-pmri-muted">
              {(validComparisonForDisplay.warnings.length ? validComparisonForDisplay.warnings : ["No additional comparison warnings are available."]).map((item) => <li key={item}>- {item}</li>)}
            </ul>
          </details>
          <div className="rounded-2xl border border-pmri-border bg-white/[0.025] p-4">
            <p className="mb-3 text-sm leading-7 text-pmri-muted">
              Continue after reviewing the trade-offs. The next step evaluates the evidence.
            </p>
            {hasLiveLineage ? (
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
          </div>
        </div>
      ) : null}
    </div>
  );
}
