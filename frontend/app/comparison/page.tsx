"use client";

import { useEffect, useMemo, useState } from "react";
import Link from "next/link";
import { useRouter } from "next/navigation";
import { PageHeader } from "@/components/layout/PageHeader";
import { JourneyGate } from "@/components/layout/JourneyGate";
import { CandidateComparisonPanel } from "@/components/comparison/CandidateComparisonPanel";
import { TradeoffSummary } from "@/components/comparison/TradeoffSummary";
import { StatusBadge } from "@/components/ui/StatusBadge";
import { useReviewState } from "@/lib/reviewState";

type JsonRecord = Record<string, unknown>;

function isRecord(value: unknown): value is JsonRecord {
  return Boolean(value) && typeof value === "object" && !Array.isArray(value);
}

function textValue(value: unknown, fallback = "n/a") {
  return typeof value === "string" && value.trim() ? value : fallback;
}

function errorTextFromResponse(value: unknown) {
  if (!isRecord(value)) return "Comparison failed.";
  const message = textValue(value.error, "Comparison failed.");
  const details = value.details;
  if (typeof details === "string" && details.trim()) return `${message} ${details}`;
  if (Array.isArray(details)) {
    const safeDetails = details
      .map((item) => (typeof item === "string" ? item : ""))
      .filter(Boolean)
      .join(" ");
    return safeDetails ? `${message} ${safeDetails}` : message;
  }
  return message;
}

function EmptyState({
  title,
  description,
  href = "/hypothesis",
  action = "Back to Hypothesis"
}: {
  title: string;
  description: string;
  href?: string;
  action?: string;
}) {
  return (
    <section className="pmri-card rounded-3xl p-6">
      <p className="text-lg font-semibold text-pmri-text">{title}</p>
      <p className="mt-2 max-w-2xl text-sm leading-6 text-pmri-muted">{description}</p>
      <Link
        href={href}
        className="pmri-focus mt-5 inline-flex rounded-full border border-pmri-blue/50 bg-pmri-blue px-5 py-2.5 text-sm font-semibold text-white shadow-decision transition hover:bg-pmri-blueSoft"
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
    && candidateGeneration?.status === "completed"
    && candidateGeneration.canCompare
  );

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
      setComparisonError("Comparison failed. No verdict or report was created.");
    } finally {
      setIsComparing(false);
    }
  }

  if (!hydrated) return null;

  return (
    <JourneyGate stepId="comparison">
      <div>
        <PageHeader
          kicker="Step 05 / Comparison"
          title="Current vs candidate comparison"
          description="The page uses the active review only: one generated diagnostic candidate versus the submitted current portfolio."
        >
          <StatusBadge tone={comparisonMatchesCandidate ? "green" : "amber"}>
            {comparisonMatchesCandidate ? "Active comparison" : "Comparison required"}
          </StatusBadge>
        </PageHeader>

        {!canRunComparison && !comparisonMatchesCandidate ? (
          <EmptyState
            title="Generate one compare-ready candidate first."
            description="Comparison is available only after the Hypothesis page creates one backend candidate with a matching active review id. Demo comparison JSON is not shown here."
          />
        ) : null}

        {canRunComparison && !comparisonMatchesCandidate ? (
          <section className="pmri-card rounded-3xl p-6">
            <div className="flex flex-col gap-4 md:flex-row md:items-start md:justify-between">
              <div>
                <p className="text-xs font-semibold uppercase tracking-[0.16em] text-pmri-gold">Ready for Block 8</p>
                <h2 className="mt-2 text-xl font-semibold text-pmri-text">Run current-vs-candidate comparison</h2>
                <p className="mt-3 max-w-3xl text-sm leading-6 text-pmri-muted">
                  Candidate <span className="font-semibold text-pmri-text2">{candidateId}</span> is compare-ready. This step writes comparison evidence only; it does not create a verdict, recommendation, or trade instruction.
                </p>
              </div>
              <StatusBadge tone="gold">Diagnostic comparison</StatusBadge>
            </div>
            <button
              type="button"
              disabled={isComparing}
              onClick={handleRunComparison}
              className={`mt-6 rounded-full border px-5 py-3 text-sm font-semibold transition ${
                isComparing
                  ? "cursor-not-allowed border-white/10 bg-white/10 text-pmri-muted"
                  : "pmri-focus border-pmri-blue/50 bg-pmri-blue text-white shadow-decision hover:bg-pmri-blueSoft"
              }`}
            >
              {isComparing ? "Running comparison..." : "Run comparison"}
            </button>
            {comparisonError ? (
              <p className="mt-4 rounded-xl border border-pmri-red/35 bg-pmri-red/10 p-3 text-sm leading-6 text-pmri-red">
                {comparisonError}
              </p>
            ) : null}
          </section>
        ) : null}

        {comparisonMatchesCandidate && comparison ? (
          <div className="space-y-6">
            <TradeoffSummary
              improved={comparison.improved}
              worsened={[...comparison.worsened, ...tradeoffDetail]}
              unclear={comparison.unclear}
              evidenceQuality={comparison.evidenceQuality}
              boundary={comparison.candidateBoundary}
            />
            <CandidateComparisonPanel {...comparison} />
            <section className="grid gap-4 lg:grid-cols-3">
              <article className="rounded-2xl border border-pmri-border bg-white/[0.025] p-4">
                <StatusBadge tone="blue">Turnover / cost</StatusBadge>
                <p className="mt-3 text-sm leading-6 text-pmri-text2">{comparison.turnover}</p>
                <p className="mt-2 text-sm leading-6 text-pmri-muted">{comparison.estimatedCost}</p>
              </article>
              <article className="rounded-2xl border border-pmri-border bg-white/[0.025] p-4">
                <StatusBadge tone="amber">Decision review gate</StatusBadge>
                <p className="mt-3 text-sm leading-6 text-pmri-text2">{comparison.materiality}</p>
              </article>
              <article className="rounded-2xl border border-pmri-border bg-white/[0.025] p-4">
                <StatusBadge tone="slate">Warnings</StatusBadge>
                <ul className="mt-3 space-y-2 text-sm leading-6 text-pmri-muted">
                  {(comparison.warnings.length ? comparison.warnings : ["No backend warnings were returned."]).map((item) => (
                    <li key={item}>• {item}</li>
                  ))}
                </ul>
              </article>
            </section>
            <div className="rounded-2xl border border-pmri-border bg-white/[0.025] p-4">
              <p className="mb-3 text-sm leading-6 text-pmri-muted">
                Continue only after reviewing the trade-offs. The next step evaluates action/no-action; this page does not choose a winner.
              </p>
              <button
                type="button"
                className="pmri-focus rounded-full border border-pmri-blue/50 bg-pmri-blue px-5 py-2.5 text-sm font-semibold text-white shadow-decision transition hover:bg-pmri-blueSoft"
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
    </JourneyGate>
  );
}
