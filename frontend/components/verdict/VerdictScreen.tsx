"use client";

import { useEffect, useMemo, useState } from "react";
import Link from "next/link";
import { useRouter } from "next/navigation";
import { SiteExplanationHierarchy } from "@/components/explanation/SiteExplanationHierarchy";
import { ClientFitContextCard } from "@/components/client-fit/ClientFitContextCard";
import { ActiveDiagnosticTestContext } from "@/components/ui/ActiveDiagnosticTestContext";
import { StatusBadge } from "@/components/ui/StatusBadge";
import { VerdictHero } from "@/components/ui/VerdictHero";
import { EvidenceSummary } from "@/components/ui/EvidenceSummary";
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
  details
}: {
  title: string;
  description: string;
  href?: string;
  action?: string;
  why?: string;
  nextStep?: string;
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
            {details.map((item) => <li key={item}>- {item}</li>)}
          </ul>
        </div>
      ) : null}
      {nextStep ? (
        <p className="mt-4 max-w-3xl text-sm leading-7 text-pmri-text2">
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

export function VerdictScreen() {
  const router = useRouter();
  const { activeReview, hydrated, markVerdictReady, recordVerdictResult } = useReviewState();
  const [isRunningVerdict, setIsRunningVerdict] = useState(false);
  const [verdictError, setVerdictError] = useState<string | undefined>();

  const reviewId = activeReview?.reviewId ?? activeReview?.reviewSummary?.reviewId ?? activeReview?.reviewResult?.review_id;
  const candidateGeneration = activeReview?.candidateGeneration;
  const comparison = activeReview?.comparisonResult;
  const verdict = activeReview?.verdictResult;
  const hasLiveLineage = Boolean(activeReview?.lineageAvailable && !activeReview?.readOnlyHistory);
  const selectedCardId = candidateGeneration?.selectedCardId;
  const candidateId = candidateGeneration?.candidateId;
  const candidateDisplayName = formatUnknownValue(comparison?.candidateName ?? candidateId, "Diagnostic test not selected");
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
    && hasLiveLineage
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
          selected_card_id: selectedCardId,
          candidate_id: candidateId,
          comparison_id: candidateId ? `current_vs_candidate:${candidateId}` : undefined
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
        <div className="mb-6 space-y-5">
          <VerdictHero
            stepContext="Step 7 of 8 - Verdict"
            headline={verdictMatchesCandidate && verdict ? normalizeDisplaySentence(verdict.headline, "Decision-support verdict is available") : "Decision-support verdict is required"}
            interpretation={verdictMatchesCandidate && verdict ? normalizeDisplaySentence(verdict.explanation, "Review the selected evidence before forming an implementation view.") : "The verdict evaluates one generated diagnostic test candidate against active comparison evidence. Evidence-insufficient outcomes are normal."}
            facts={[
              { label: "Diagnostic test", value: candidateDisplayName },
              { label: "Confidence", value: verdictMatchesCandidate && verdict ? formatUnknownValue(verdict.confidence, "Unknown") : "Unavailable" }
            ]}
          />
          {verdictMatchesCandidate && verdict ? (
            <EvidenceSummary
              title="Selected verdict evidence"
              description="The verdict uses selected rationale and limitations rather than a dense dashboard."
              items={[
                { label: "Decision interpretation", value: formatUnknownValue(verdict.state, "Decision-support verdict") },
                { label: "Rationale", value: verdict.keyEvidence[0] ?? verdict.explanation },
                { label: "Major trade-off", value: verdict.limitations[0] ?? "No limitation returned", tone: verdict.limitations.length ? "amber" : "slate" }
              ]}
            />
          ) : null}
        </div>
        <div className="mb-6">
          <ActiveDiagnosticTestContext
            testName={candidateDisplayName}
            purpose="The verdict interprets the active diagnostic test against current comparison evidence and visible limitations."
            candidateName={candidateId ? candidateDisplayName : undefined}
            evidenceQuality={verdictMatchesCandidate && verdict ? formatUnknownValue(verdict.evidenceQuality, "Evidence quality unavailable") : "Verdict pending"}
            limitation="Decision Verdict is non-binding decision support, not a trading instruction or suitability approval."
            tone={evidenceInsufficient || staleVerdictIgnored || staleComparisonIgnored ? "amber" : verdictMatchesCandidate ? "blue" : "slate"}
          />
        </div>
        <SiteExplanationHierarchy
          bundle={siteExplanation}
          screen="verdict"
          fallbackTitle="Verdict explanation"
        />

        {activeReview?.readOnlyHistory ? (
          <section className="mb-6 rounded-2xl border border-pmri-border/45 bg-white/[0.026] p-4">
            <StatusBadge tone="slate">Historical</StatusBadge>
            <p className="mt-3 max-w-3xl text-sm leading-7 text-pmri-text2">
              This verdict belongs to a saved compact snapshot. It is visible for review, but it cannot unlock new report or downstream actions without active same-run evidence.
            </p>
          </section>
        ) : null}

        {staleVerdictIgnored ? (
          <section className="mb-6 rounded-2xl border border-pmri-amber/35 bg-pmri-amber/10 p-4">
            <StatusBadge tone="amber">Previous verdict ignored</StatusBadge>
            <p className="mt-3 max-w-3xl text-sm leading-7 text-pmri-text2">
              A prior verdict does not match the active diagnostic test. Generate a new verdict only after the active comparison is current.
            </p>
          </section>
        ) : null}

        {generationFailed && !verdictMatchesCandidate ? (
          <EmptyState
            title="Diagnostic test candidate could not be used"
            description="The selected diagnostic test candidate failed or was infeasible, so Portfolio MRI cannot form an evidence-supported verdict from it."
            why="A verdict needs a feasible diagnostic test candidate and current comparison evidence. Failed or infeasible diagnostic tests are treated as evidence-insufficient outcomes."
            nextStep="Return to Hypothesis Builder and test another diagnostic path."
          />
        ) : null}

        {staleComparisonIgnored && !canRunVerdict && !verdictMatchesCandidate && !generationFailed ? (
          <EmptyState
            title="Previous comparison ignored"
            description="The saved comparison does not match the active diagnostic test, so no verdict is shown from it."
            why="Verdict evidence must belong to the same active review, selected test path, generated test candidate, and comparison."
            nextStep="Return to Comparison and regenerate evidence for the active diagnostic test."
            href="/comparison"
            action="Return to Comparison"
          />
        ) : null}

        {!canRunVerdict && !verdictMatchesCandidate ? (
          !generationFailed && !staleComparisonIgnored ? (
          <EmptyState
            title="Verdict unavailable"
            description="A valid current-vs-test-candidate comparison is required before a decision-support verdict can be formed."
            why="Portfolio MRI cannot determine whether changing the portfolio improves the diagnosed weakness without a valid diagnostic test comparison."
            nextStep={candidateGeneration ? "Return to Comparison and complete a valid same-candidate comparison." : "Return to Hypothesis Builder and generate a valid diagnostic test candidate."}
            href={candidateGeneration ? "/comparison" : "/hypothesis"}
            action={candidateGeneration ? "Return to Comparison" : "Return to Hypothesis Builder"}
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
                  The <span className="font-medium text-pmri-text2">{candidateDisplayName}</span> diagnostic test has active comparison evidence. This step creates the verdict evidence.
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
              title="Test candidate failed or infeasible"
              description="The selected diagnostic test candidate did not produce usable comparison evidence."
              why="A failed or infeasible candidate can explain why the evidence is not usable for a clear verdict."
              nextStep="Test another diagnostic hypothesis or keep the current portfolio under monitoring."
              details={evidenceInsufficientDetails.length ? evidenceInsufficientDetails : ["The verdict did not return enough evidence to support action review."]}
            />
          </div>
        ) : null}

        {evidenceInsufficient && !candidateFailed && verdict ? (
          <div className="space-y-6">
            <EmptyState
              title="Evidence insufficient"
              description="Do not make a portfolio decision from this evidence yet."
              why="The diagnostic test comparison is incomplete or degraded. Portfolio MRI cannot determine whether the diagnostic test improves the diagnosed weakness."
              nextStep="Generate a valid diagnostic test candidate, test another diagnostic path, or keep the current portfolio under monitoring."
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
            <section className="pmri-card rounded-3xl p-6 md:p-7">
              <p className="pmri-label">Decision interpretation</p>
              <h2 className="pmri-heading-section mt-2 text-2xl text-pmri-text">{formatUnknownValue(verdict.state, "Decision-support verdict")}</h2>
              <p className="mt-4 max-w-4xl text-base leading-8 text-pmri-text2">{normalizeDisplaySentence(verdict.actionFraming)}</p>
              <div className="mt-6 grid gap-4 lg:grid-cols-3">
                <article className="rounded-2xl border border-pmri-border/45 bg-white/[0.022] p-4">
                  <p className="pmri-label">Rationale</p>
                  <ul className="mt-3 space-y-2 text-sm leading-7 text-pmri-text2">
                    {(verdict.keyEvidence.length ? verdict.keyEvidence : [verdict.explanation]).slice(0, 4).map((item) => <li key={item}>- {normalizeDisplaySentence(item)}</li>)}
                  </ul>
                </article>
                <article className="rounded-2xl border border-pmri-border/45 bg-white/[0.022] p-4">
                  <p className="pmri-label">Evidence quality</p>
                  <p className="mt-3 text-sm leading-7 text-pmri-text2">Confidence: {formatUnknownValue(verdict.confidence, "Unknown")}</p>
                  <p className="mt-2 text-sm leading-7 text-pmri-muted">{formatUnknownValue(verdict.evidenceQuality, "Evidence quality unavailable")}</p>
                </article>
                <article className="rounded-2xl border border-pmri-border/45 bg-white/[0.022] p-4">
                  <p className="pmri-label">What would change it</p>
                  <ul className="mt-3 space-y-2 text-sm leading-7 text-pmri-muted">
                    {limitationRows.slice(0, 4).map((item) => <li key={item}>- {normalizeDisplaySentence(item)}</li>)}
                  </ul>
                </article>
              </div>
            </section>
            <ClientFitContextCard
              clientFit={clientFitForStage}
              title="Client Fit is one input to the verdict"
              description="The verdict combines Client Fit, objective diagnosis, comparison evidence, and confidence limitations without letting any single profile alignment result override a material issue."
              structuralIssueNote="Client Fit alignment plus a material diagnosis issue should still lead to monitor, review, or diagnostic-test framing rather than an automatic no-action conclusion."
              compact
            />
            <div className="rounded-2xl border border-pmri-border bg-white/[0.025] p-4">
              <p className="mb-3 text-sm leading-7 text-pmri-muted">
                Continue to Report after reviewing the verdict framing. The next page summarizes selected evidence.
              </p>
              {hasLiveLineage ? (
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
              ) : null}
            </div>
          </div>
        ) : null}
      </div>
  );
}
