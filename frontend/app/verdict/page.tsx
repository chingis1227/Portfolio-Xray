"use client";

import { useEffect, useMemo, useState } from "react";
import Link from "next/link";
import { useRouter } from "next/navigation";
import { PageHeader } from "@/components/layout/PageHeader";
import { SiteExplanationHierarchy } from "@/components/explanation/SiteExplanationHierarchy";
import { ClientFitContextCard } from "@/components/client-fit/ClientFitContextCard";
import { VerdictPanel } from "@/components/verdict/VerdictPanel";
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
  if (!isRecord(value)) return "Verdict unavailable. A valid comparison is required before a decision-support verdict can be formed.";
  const message = textValue(value.error, "Verdict unavailable.");
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

function EmptyState({
  title,
  description,
  href = "/hypothesis",
  action = "Return to Hypothesis Builder",
  why,
  nextStep,
  decisionBoundary,
  details
}: {
  title: string;
  description: string;
  href?: string;
  action?: string;
  why?: string;
  nextStep?: string;
  decisionBoundary?: string;
  details?: string[];
}) {
  return (
    <section className="pmri-card rounded-3xl p-6">
      <p className="pmri-heading-section text-lg text-pmri-text">{title}</p>
      <p className="mt-2 max-w-2xl text-sm leading-7 text-pmri-muted">{description}</p>
      {why ? (
        <p className="mt-4 max-w-3xl text-sm leading-7 text-pmri-text2">
          <span className="font-medium text-pmri-text">Why:</span> {why}
        </p>
      ) : null}
      {details?.length ? (
        <div className="mt-5 rounded-2xl border border-pmri-border/45 bg-white/[0.026] p-4">
          <p className="pmri-label">What we know</p>
          <ul className="mt-3 space-y-2 text-sm leading-6 text-pmri-text2">
            {details.map((item) => <li key={item}>• {item}</li>)}
          </ul>
        </div>
      ) : null}
      {nextStep ? (
        <p className="mt-4 max-w-3xl text-sm leading-7 text-pmri-text2">
          <span className="font-medium text-pmri-text">Next step:</span> {nextStep}
        </p>
      ) : null}
      {decisionBoundary ? (
        <p className="mt-4 max-w-3xl rounded-xl border border-pmri-border/70 bg-white/[0.035] p-3 text-sm leading-6 text-pmri-text2">
          <span className="font-medium text-pmri-text">Decision boundary:</span> {decisionBoundary}
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

function statusKey(value: unknown) {
  return String(value ?? "")
    .trim()
    .toLowerCase()
    .replace(/[^a-z0-9]+/g, "_")
    .replace(/^_+|_+$/g, "");
}

function isEvidenceInsufficientVerdict(verdict: NonNullable<ReturnType<typeof useReviewState>["activeReview"]>["verdictResult"] | undefined) {
  if (!verdict) return false;
  return [
    verdict.verdictId,
    verdict.state,
    verdict.decisionStatus,
    verdict.headline,
    verdict.evidenceQuality
  ].some((value) => statusKey(value).includes("evidence_insufficient"));
}

function isCandidateFailedVerdict(verdict: NonNullable<ReturnType<typeof useReviewState>["activeReview"]>["verdictResult"] | undefined) {
  if (!verdict) return false;
  return [
    verdict.verdictId,
    verdict.state,
    verdict.decisionStatus,
    verdict.headline
  ].some((value) => {
    const key = statusKey(value);
    return key.includes("candidate_failed") || key.includes("infeasible");
  });
}

function isFailedCandidateGeneration(status: unknown) {
  const key = statusKey(status);
  return key.includes("failed") || key.includes("infeasible") || key.includes("blocked");
}

function confidenceTone(value: string) {
  const key = statusKey(value);
  return key === "low" || key.includes("insufficient") ? "amber" : "blue";
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
  const candidateDisplayName = formatUnknownValue(comparison?.candidateName ?? candidateId, "generated diagnostic candidate");
  const comparisonMatchesCandidate = Boolean(
    comparison
    && selectedCardId
    && candidateId
    && comparison.selectedCardId === selectedCardId
    && comparison.candidateId === candidateId
  );
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
    && comparisonMatchesCandidate
    && activeReview?.comparisonReady
  );
  const evidenceInsufficient = verdictMatchesCandidate && isEvidenceInsufficientVerdict(verdict);
  const candidateFailed = verdictMatchesCandidate && isCandidateFailedVerdict(verdict);
  const staleVerdictIgnored = Boolean(verdict && selectedCardId && candidateId && !verdictMatchesCandidate);
  const staleComparisonIgnored = Boolean(comparison && selectedCardId && candidateId && !comparisonMatchesCandidate);
  const generationFailed = isFailedCandidateGeneration(candidateGeneration?.status);
  const siteExplanation = activeReview?.reviewSummary?.siteExplanation;
  const clientFitForStage = verdict?.clientFit ?? comparison?.clientFit ?? activeReview?.reviewSummary?.clientFit;

  useEffect(() => {
    setVerdictError(undefined);
  }, [reviewId, selectedCardId, candidateId]);

  const limitationRows = useMemo(() => {
    if (!verdictMatchesCandidate || !verdict) return [];
    return verdict.limitations.length ? verdict.limitations : ["No confidence limitations were returned."];
  }, [verdict, verdictMatchesCandidate]);

  const evidenceInsufficientDetails = useMemo(() => {
    if (!verdictMatchesCandidate || !verdict) return [];
    return [
      ...verdict.keyEvidence,
      ...verdict.limitations
    ]
      .map((item) => normalizeDisplaySentence(item))
      .filter(Boolean)
      .slice(0, 5);
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
      setVerdictError("Verdict unavailable. A valid comparison is required before a decision-support verdict can be formed.");
    } finally {
      setIsRunningVerdict(false);
    }
  }

  if (!hydrated) return null;

  return (
    <div>
        <PageHeader
          kicker="Step 07 / Verdict"
          title="Decision verdict"
          description="The verdict evaluates one generated diagnostic candidate against the active comparison evidence. No-trade and evidence-insufficient are normal outcomes."
        >
          <StatusBadge tone={verdictMatchesCandidate ? (evidenceInsufficient ? "amber" : "green") : "amber"}>
            {verdictMatchesCandidate ? (evidenceInsufficient ? "Evidence insufficient" : "Active verdict") : "Verdict required"}
          </StatusBadge>
        </PageHeader>
        <SiteExplanationHierarchy
          bundle={siteExplanation}
          screen="verdict"
          fallbackTitle="Verdict explanation"
        />

        {staleVerdictIgnored ? (
          <section className="mb-6 rounded-2xl border border-pmri-amber/35 bg-pmri-amber/10 p-4">
            <StatusBadge tone="amber">Previous verdict ignored</StatusBadge>
            <p className="mt-3 max-w-3xl text-sm leading-7 text-pmri-text2">
              A prior verdict does not match the active candidate test. Generate a new verdict only after the active comparison is current.
            </p>
          </section>
        ) : null}

        {generationFailed && !verdictMatchesCandidate ? (
          <EmptyState
            title="Candidate test could not be used"
            description="The selected candidate attempt failed or was infeasible, so Portfolio MRI cannot form an evidence-supported verdict from it."
            why="A verdict needs a feasible candidate and current comparison evidence. Failed or infeasible tests are treated as evidence-insufficient outcomes, not as recommendations."
            nextStep="Return to Hypothesis Builder and test another diagnostic path."
            decisionBoundary="No portfolio action is implied."
          />
        ) : null}

        {staleComparisonIgnored && !canRunVerdict && !verdictMatchesCandidate && !generationFailed ? (
          <EmptyState
            title="Previous comparison ignored"
            description="The saved comparison does not match the active candidate test, so no verdict is shown from it."
            why="Verdict evidence must belong to the same active review, selected test path, generated candidate, and comparison."
            nextStep="Return to Comparison and regenerate evidence for the active candidate."
            href="/comparison"
            action="Return to Comparison"
            decisionBoundary="Portfolio MRI will not create a fake verdict from outdated evidence."
          />
        ) : null}

        {!canRunVerdict && !verdictMatchesCandidate ? (
          !generationFailed && !staleComparisonIgnored ? (
          <EmptyState
            title="Verdict unavailable"
            description="A valid Current vs Candidate Comparison is required before a decision-support verdict can be formed."
            why="Portfolio MRI cannot determine whether changing the portfolio improves the diagnosed weakness without a valid candidate comparison."
            nextStep={candidateGeneration ? "Return to Comparison and complete a valid same-candidate comparison." : "Return to Hypothesis Builder and generate a valid candidate."}
            href={candidateGeneration ? "/comparison" : "/hypothesis"}
            action={candidateGeneration ? "Return to Comparison" : "Return to Hypothesis Builder"}
            decisionBoundary="No verdict is shown until current comparison evidence exists."
          />
          ) : null
        ) : null}

        {canRunVerdict && !verdictMatchesCandidate ? (
          <section className="pmri-card rounded-3xl p-6">
            <div className="flex flex-col gap-4 md:flex-row md:items-start md:justify-between">
              <div>
                <p className="pmri-label">Ready for verdict</p>
                <h2 className="mt-2 pmri-heading-section text-xl text-pmri-text">Generate decision-support verdict</h2>
                <p className="mt-3 max-w-3xl text-sm leading-7 text-pmri-muted">
                  The <span className="font-medium text-pmri-text2">{candidateDisplayName}</span> has active comparison evidence. This step creates decision-support evidence only; it does not create a rebalance instruction.
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

        {candidateFailed && verdict ? (
          <div className="space-y-6">
            <EmptyState
              title="Candidate failed or infeasible"
              description="The selected candidate test did not produce usable comparison evidence."
              why="A failed or infeasible candidate can explain why no action/no-action verdict is supported, but it is not a reason to change the portfolio."
              nextStep="Test another diagnostic hypothesis or keep the current portfolio under monitoring."
              decisionBoundary="This is a blocked evidence state, not a trade instruction."
              details={evidenceInsufficientDetails.length ? evidenceInsufficientDetails : ["The verdict did not return enough evidence to support action review."]}
            />
          </div>
        ) : null}

        {evidenceInsufficient && !candidateFailed && verdict ? (
          <div className="space-y-6">
            <EmptyState
              title="Evidence insufficient"
              description="Do not make a portfolio decision from this evidence yet."
              why="The candidate comparison is incomplete or degraded. Portfolio MRI cannot determine whether the candidate improves the diagnosed weakness."
              nextStep="Generate a valid candidate, test another hypothesis, or keep the current portfolio under monitoring."
              decisionBoundary="This is not a trade instruction or rebalance recommendation."
              details={evidenceInsufficientDetails.length ? evidenceInsufficientDetails : ["The verdict did not return enough evidence to support an action/no-action decision."]}
            />
            <section className="grid gap-4 lg:grid-cols-2">
              <article className="rounded-2xl border border-pmri-border bg-white/[0.025] p-4">
                <StatusBadge tone="amber">Evidence quality</StatusBadge>
                <p className="mt-3 text-sm leading-7 text-pmri-text2">Confidence: {formatUnknownValue(verdict.confidence, "Unknown")}</p>
                <p className="mt-2 text-sm leading-7 text-pmri-muted">Verdict state: {formatUnknownValue(verdict.state, "Evidence insufficient")}</p>
              </article>
              <article className="rounded-2xl border border-pmri-border bg-white/[0.025] p-4">
                <StatusBadge tone="blue">Monitoring path</StatusBadge>
                <p className="mt-3 text-sm leading-7 text-pmri-text2">{normalizeDisplaySentence(verdict.monitoringTrigger, "Keep monitoring until stronger comparison evidence is available.")}</p>
              </article>
            </section>
          </div>
        ) : null}

        {verdictMatchesCandidate && verdict && !evidenceInsufficient && !candidateFailed ? (
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
            <ClientFitContextCard
              clientFit={clientFitForStage}
              title="Client Fit is one input to the verdict"
              description="The verdict combines Client Fit, objective diagnosis, comparison evidence, and confidence limitations without letting any single green profile result override a material issue."
              structuralIssueNote="Client Fit pass plus a material diagnosis issue should still lead to monitor, review, or test-candidate framing rather than an automatic no-action conclusion."
            />
            <section className="grid gap-4 lg:grid-cols-3">
              <article className="rounded-2xl border border-pmri-border bg-white/[0.025] p-4">
                <StatusBadge tone="slate">Action framing</StatusBadge>
                <p className="mt-3 text-sm leading-7 text-pmri-text2">{verdict.actionFraming}</p>
              </article>
              <article className="rounded-2xl border border-pmri-border bg-white/[0.025] p-4">
                <StatusBadge tone={confidenceTone(verdict.confidence)}>Evidence quality</StatusBadge>
                <p className="mt-3 text-sm leading-7 text-pmri-text2">Confidence: {formatUnknownValue(verdict.confidence, "Unknown")}</p>
                <p className="mt-2 text-sm leading-7 text-pmri-muted">Verdict state: {formatUnknownValue(verdict.state, "Decision-support verdict")}</p>
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
  );
}
