"use client";

import { useEffect, useMemo, useState } from "react";
import Link from "next/link";
import { useRouter } from "next/navigation";
import { PageHeader } from "@/components/layout/PageHeader";
import { JourneyGate } from "@/components/layout/JourneyGate";
import { VerdictPanel } from "@/components/verdict/VerdictPanel";
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
  if (!isRecord(value)) return "Decision verdict failed.";
  const message = textValue(value.error, "Decision verdict failed.");
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
  href = "/comparison",
  action = "Back to Comparison"
}: {
  title: string;
  description: string;
  href?: string;
  action?: string;
}) {
  return (
    <section className="pmri-card rounded-3xl p-6">
      <p className="pmri-heading-section text-lg text-pmri-text">{title}</p>
      <p className="mt-2 max-w-2xl text-sm leading-7 text-pmri-muted">{description}</p>
      <Link
        href={href}
        className="pmri-focus mt-5 inline-flex rounded-full border border-pmri-blue/50 bg-pmri-blue px-5 py-2.5 text-sm font-medium text-pmri-bg shadow-decision transition hover:bg-pmri-blueSoft"
      >
        {action}
      </Link>
    </section>
  );
}

export default function VerdictPage() {
  const router = useRouter();
  const { activeReview, hydrated, markVerdictReady, recordVerdictResult } = useReviewState();
  const [isRunningVerdict, setIsRunningVerdict] = useState(false);
  const [verdictError, setVerdictError] = useState<string | undefined>();

  const reviewId = activeReview?.reviewId ?? activeReview?.reviewSummary?.reviewId ?? activeReview?.reviewResult?.review_id;
  const candidateGeneration = activeReview?.candidateGeneration;
  const comparison = activeReview?.comparisonResult;
  const verdict = activeReview?.verdictResult;
  const selectedCardId = candidateGeneration?.selectedCardId;
  const candidateId = candidateGeneration?.candidateId;
  const verdictMatchesCandidate = Boolean(
    verdict
    && selectedCardId
    && candidateId
    && verdict.selectedCardId === selectedCardId
    && verdict.candidateId === candidateId
  );
  const canRunVerdict = Boolean(
    hydrated
    && reviewId
    && selectedCardId
    && candidateGeneration?.status === "completed"
    && comparison?.candidateId === candidateId
    && activeReview?.comparisonReady
  );

  useEffect(() => {
    setVerdictError(undefined);
  }, [reviewId, selectedCardId, candidateId]);

  const limitationRows = useMemo(() => {
    if (!verdictMatchesCandidate || !verdict) return [];
    return verdict.limitations.length ? verdict.limitations : ["No confidence limitations were returned."];
  }, [verdict, verdictMatchesCandidate]);

  async function handleRunVerdict() {
    if (!reviewId || !selectedCardId) return;
    setIsRunningVerdict(true);
    setVerdictError(undefined);

    try {
      const response = await fetch("/api/portfolio/verdict/generate", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          review_id: reviewId,
          selected_card_id: selectedCardId
        })
      });
      const result = await response.json() as unknown;
      if (!response.ok || !isRecord(result) || result.status !== "completed") {
        setVerdictError(errorTextFromResponse(result));
        return;
      }
      recordVerdictResult(result);
    } catch {
      setVerdictError("Decision verdict failed. No report was created.");
    } finally {
      setIsRunningVerdict(false);
    }
  }

  if (!hydrated) return null;

  return (
    <JourneyGate stepId="verdict">
      <div>
        <PageHeader
          kicker="Step 06 / Verdict"
          title="Decision verdict"
          description="The verdict evaluates one generated diagnostic candidate against the active comparison evidence. No-trade and evidence-insufficient are normal outcomes."
        >
          <StatusBadge tone={verdictMatchesCandidate ? "green" : "amber"}>
            {verdictMatchesCandidate ? "Active verdict" : "Verdict required"}
          </StatusBadge>
        </PageHeader>

        {!canRunVerdict && !verdictMatchesCandidate ? (
          <EmptyState
            title="Complete an active comparison first."
            description="The Verdict page uses the active review in the normal flow. It needs one active review, one generated candidate, and one matching current-vs-candidate comparison."
          />
        ) : null}

        {canRunVerdict && !verdictMatchesCandidate ? (
          <section className="pmri-card rounded-3xl p-6">
            <div className="flex flex-col gap-4 md:flex-row md:items-start md:justify-between">
              <div>
                <p className="pmri-label">Ready for verdict</p>
                <h2 className="mt-2 pmri-heading-section text-xl text-pmri-text">Generate decision-support verdict</h2>
                <p className="mt-3 max-w-3xl text-sm leading-7 text-pmri-muted">
                  Candidate <span className="font-medium text-pmri-text2">{candidateId}</span> has active comparison evidence. This step creates verdict evidence only; it does not create an implementation order.
                </p>
              </div>
              <StatusBadge tone="slate">Decision-support only</StatusBadge>
            </div>
            <button
              type="button"
              disabled={isRunningVerdict}
              onClick={handleRunVerdict}
              className={`mt-6 rounded-full border px-5 py-3 text-sm font-medium transition ${
                isRunningVerdict
                  ? "cursor-not-allowed border-white/10 bg-white/10 text-pmri-muted"
                  : "pmri-focus border-pmri-blue/50 bg-pmri-blue text-pmri-bg shadow-decision hover:bg-pmri-blueSoft"
              }`}
            >
              {isRunningVerdict ? "Generating verdict..." : "Generate verdict"}
            </button>
            {verdictError ? (
              <p className="mt-4 rounded-xl border border-pmri-red/35 bg-pmri-red/10 p-3 text-sm leading-6 text-pmri-red">
                {verdictError}
              </p>
            ) : null}
          </section>
        ) : null}

        {verdictMatchesCandidate && verdict ? (
          <div className="space-y-6">
            <VerdictPanel
              state={verdict.state}
              headline={verdict.headline}
              explanation={verdict.explanation}
              evidenceQuality={verdict.evidenceQuality}
              boundaryNote={verdict.boundaryNote}
              keyEvidence={verdict.keyEvidence}
              monitoringTrigger={verdict.monitoringTrigger}
              metrics={verdict.metrics}
            />
            <section className="grid gap-4 lg:grid-cols-3">
              <article className="rounded-2xl border border-pmri-border bg-white/[0.025] p-4">
                <StatusBadge tone="slate">Action framing</StatusBadge>
                <p className="mt-3 text-sm leading-7 text-pmri-text2">{verdict.actionFraming}</p>
              </article>
              <article className="rounded-2xl border border-pmri-border bg-white/[0.025] p-4">
                <StatusBadge tone={verdict.confidence === "low" ? "amber" : "blue"}>Evidence quality</StatusBadge>
                <p className="mt-3 text-sm leading-7 text-pmri-text2">Confidence: {verdict.confidence}</p>
                <p className="mt-2 text-sm leading-7 text-pmri-muted">Decision status: {verdict.decisionStatus.replaceAll("_", " ")}</p>
              </article>
              <article className="rounded-2xl border border-pmri-border bg-white/[0.025] p-4">
                <StatusBadge tone="slate">What would change it</StatusBadge>
                <ul className="mt-3 space-y-2 text-sm leading-7 text-pmri-muted">
                  {limitationRows.map((item) => (
                    <li key={item}>• {item}</li>
                  ))}
                </ul>
              </article>
            </section>
            <div className="rounded-2xl border border-pmri-border bg-white/[0.025] p-4">
              <p className="mb-3 text-sm leading-7 text-pmri-muted">
                Continue to Report only after reviewing the verdict framing. The next page should summarize the evidence; this is still not a trade order.
              </p>
              <button
                type="button"
                className="pmri-focus rounded-full border border-pmri-blue/50 bg-pmri-blue px-5 py-2.5 text-sm font-medium text-pmri-bg shadow-decision transition hover:bg-pmri-blueSoft"
                onClick={() => {
                  markVerdictReady();
                  router.push("/report");
                }}
              >
                Open report
              </button>
            </div>
          </div>
        ) : null}
      </div>
    </JourneyGate>
  );
}
