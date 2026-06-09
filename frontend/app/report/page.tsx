"use client";

import { useEffect, useMemo, useState } from "react";
import Link from "next/link";
import { PageHeader } from "@/components/layout/PageHeader";
import { JourneyGate } from "@/components/layout/JourneyGate";
import { ClientReadyReportPreview } from "@/components/report/ClientReadyReportPreview";
import { StatusBadge } from "@/components/ui/StatusBadge";
import { useReviewState } from "@/lib/reviewState";

type JsonRecord = Record<string, unknown>;

type GroundedReport = {
  title: string;
  subtitle: string;
  sections: { title: string; body: string }[];
  monitoring: string;
  boundaryNote: string;
  warnings: string[];
  generatedAt?: string;
  path?: string;
};

function isRecord(value: unknown): value is JsonRecord {
  return Boolean(value) && typeof value === "object" && !Array.isArray(value);
}

function textValue(value: unknown, fallback = "n/a") {
  return typeof value === "string" && value.trim() ? value : fallback;
}

function stringArray(value: unknown) {
  return Array.isArray(value)
    ? value.filter((item): item is string => typeof item === "string" && Boolean(item.trim()))
    : [];
}

function titleFromTopic(topic: string) {
  const labels: Record<string, string> = {
    portfolio_diagnosis: "Diagnosis",
    stress_behavior: "Stress evidence",
    hypothesis_tested: "Candidate test",
    candidate_logic: "Builder setup",
    current_vs_candidate: "Current vs candidate",
    what_improved: "What improved",
    what_worsened: "What worsened",
    turnover_cost: "Turnover and cost",
    decision_verdict: "Decision verdict",
    monitoring_next: "Next observation points"
  };
  return labels[topic] ?? topic.replaceAll("_", " ");
}

function errorTextFromResponse(value: unknown) {
  if (!isRecord(value)) return "Report commentary failed.";
  const message = textValue(value.error, "Report commentary failed.");
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

function reportFromResult(result: unknown): GroundedReport | null {
  if (!isRecord(result) || result.status !== "completed") return null;
  const context = isRecord(result.ai_commentary_context) ? result.ai_commentary_context : {};
  const draft = isRecord(context.client_explanation_draft) ? context.client_explanation_draft : {};
  const journal = isRecord(context.light_decision_journal) ? context.light_decision_journal : {};
  const sentences = Array.isArray(draft.sentences) ? draft.sentences.filter(isRecord) : [];
  const verdictId = textValue(journal.decision_verdict, "decision-support verdict");
  const candidate = isRecord(journal.selected_candidate) ? journal.selected_candidate : {};
  const candidateId = textValue(result.candidate_id, textValue(candidate.candidate_id, "selected candidate"));

  const sections = sentences
    .map((sentence) => ({
      title: titleFromTopic(textValue(sentence.topic, "Evidence")),
      body: textValue(sentence.text, "")
    }))
    .filter((section) => section.body)
    .slice(0, 9);

  const sourceArtifacts = isRecord(context.source_artifacts) ? context.source_artifacts : {};
  const sourceCount = Object.values(sourceArtifacts).filter(Boolean).length;
  const warnings = stringArray(context.warnings);

  return {
    title: "Grounded client-ready report summary",
    subtitle: `Active review report for ${candidateId}. It is grounded in ${sourceCount} evidence package type(s) and ends with ${verdictId.replaceAll("_", " ")}.`,
    sections: sections.length
      ? sections
      : [
        {
          title: "Executive summary",
          body: "The AI Commentary context was available, but no plain-language sentences were returned."
        }
      ],
    monitoring: textValue(
      journal.next_review_trigger,
      "No monitoring trigger evidence was provided; revisit if diagnosis, comparison, or verdict evidence changes."
    ),
    boundaryNote: "Decision-support only. This report does not recommend trades, execute trades, provide suitability advice, or identify a best portfolio.",
    warnings,
    generatedAt: typeof context.generated_at === "string" ? context.generated_at : undefined,
    path: typeof result.path === "string" ? result.path : undefined
  };
}

function EmptyState() {
  return (
    <section className="pmri-card rounded-3xl p-6">
      <p className="pmri-heading-section text-lg text-pmri-text">Complete the active verdict first.</p>
      <p className="mt-2 max-w-2xl text-sm leading-7 text-pmri-muted">
        The Report page uses the active review evidence package. It needs one generated candidate and a matching decision verdict before it can build grounded commentary.
      </p>
      <Link
        href="/verdict"
        className="pmri-focus mt-5 inline-flex rounded-full border border-pmri-blue/50 bg-pmri-blue px-5 py-2.5 text-sm font-medium text-pmri-bg shadow-decision transition hover:bg-pmri-blueSoft"
      >
        Back to Verdict
      </Link>
    </section>
  );
}

export default function ReportPage() {
  const { activeReview, hydrated } = useReviewState();
  const [isGeneratingReport, setIsGeneratingReport] = useState(false);
  const [reportError, setReportError] = useState<string | undefined>();
  const [report, setReport] = useState<GroundedReport | null>(null);

  const reviewId = activeReview?.reviewId ?? activeReview?.reviewSummary?.reviewId ?? activeReview?.reviewResult?.review_id;
  const candidateGeneration = activeReview?.candidateGeneration;
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
  const canGenerateReport = Boolean(
    hydrated
    && reviewId
    && selectedCardId
    && candidateGeneration?.status === "completed"
    && activeReview?.verdictReady
    && verdictMatchesCandidate
  );

  useEffect(() => {
    setReport(null);
    setReportError(undefined);
  }, [reviewId, selectedCardId, candidateId, verdict?.generatedAt]);

  const statusTone = useMemo<"green" | "gold" | "amber">(() => {
    if (report) return "green";
    if (canGenerateReport) return "gold";
    return "amber";
  }, [canGenerateReport, report]);

  async function handleGenerateReport() {
    if (!reviewId || !selectedCardId) return;
    setIsGeneratingReport(true);
    setReportError(undefined);

    try {
      const response = await fetch("/api/portfolio/report/generate", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          review_id: reviewId,
          selected_card_id: selectedCardId
        })
      });
      const result = await response.json() as unknown;
      if (!response.ok || !isRecord(result) || result.status !== "completed") {
        setReportError(errorTextFromResponse(result));
        return;
      }
      const mapped = reportFromResult(result);
      if (!mapped) {
        setReportError("Report commentary returned an unexpected shape.");
        return;
      }
      setReport(mapped);
    } catch {
      setReportError("Report commentary failed. No report summary was created.");
    } finally {
      setIsGeneratingReport(false);
    }
  }

  if (!hydrated) return null;

  return (
    <JourneyGate stepId="report">
      <div>
        <PageHeader
          kicker="Step 07 / Report"
          title="Client-ready report preview"
          description="A concise narrative grounded in the active review: diagnosis, candidate test, comparison, verdict, limitations, and next observation points."
        >
          <StatusBadge tone={statusTone}>
            {report ? "Grounded report" : canGenerateReport ? "Ready to generate" : "Verdict required"}
          </StatusBadge>
        </PageHeader>

        {!canGenerateReport ? <EmptyState /> : null}

        {canGenerateReport && !report ? (
          <section className="pmri-card rounded-3xl p-6">
            <div className="flex flex-col gap-4 md:flex-row md:items-start md:justify-between">
              <div>
                <p className="pmri-label">Grounded commentary</p>
                <h2 className="mt-2 pmri-heading-section text-xl text-pmri-text">Generate report summary from active evidence</h2>
                <p className="mt-3 max-w-3xl text-sm leading-7 text-pmri-muted">
                  This reads the AI Commentary context for candidate <span className="font-medium text-pmri-text2">{candidateId}</span>. It does not regenerate PDFs or create an implementation order.
                </p>
              </div>
              <StatusBadge tone="blue">No PDF generation</StatusBadge>
            </div>
            <button
              type="button"
              disabled={isGeneratingReport}
              onClick={handleGenerateReport}
              className={`mt-6 rounded-full border px-5 py-3 text-sm font-medium transition ${
                isGeneratingReport
                  ? "cursor-not-allowed border-white/10 bg-white/10 text-pmri-muted"
                  : "pmri-focus border-pmri-blue/50 bg-pmri-blue text-pmri-bg shadow-decision hover:bg-pmri-blueSoft"
              }`}
            >
              {isGeneratingReport ? "Opening report..." : "Open report"}
            </button>
            {reportError ? (
              <p className="mt-4 rounded-xl border border-pmri-red/35 bg-pmri-red/10 p-3 text-sm leading-6 text-pmri-red">
                {reportError}
              </p>
            ) : null}
          </section>
        ) : null}

        {report ? (
          <div className="space-y-5">
            <ClientReadyReportPreview {...report} />
            <section className="grid gap-4 lg:grid-cols-3">
              <article className="rounded-2xl border border-pmri-border/45 bg-white/[0.022] p-4">
                <StatusBadge tone="slate">Evidence grounding</StatusBadge>
                <p className="mt-3 text-sm leading-7 text-pmri-muted">Grounded in the active review context.</p>
              </article>
              <article className="rounded-2xl border border-pmri-border/45 bg-white/[0.022] p-4">
                <StatusBadge tone="blue">Generated at</StatusBadge>
                <p className="mt-3 text-sm leading-7 text-pmri-muted">{report.generatedAt ?? "Timestamp unavailable"}</p>
              </article>
              <article className="rounded-2xl border border-pmri-border/45 bg-white/[0.022] p-4">
                <StatusBadge tone={report.warnings.length ? "amber" : "green"}>Limitations</StatusBadge>
                <ul className="mt-3 space-y-2 text-sm leading-7 text-pmri-muted">
                  {(report.warnings.length ? report.warnings.slice(0, 3) : ["No AI Commentary context warnings were returned."]).map((item) => (
                    <li key={item}>• {item}</li>
                  ))}
                </ul>
              </article>
            </section>
          </div>
        ) : null}
      </div>
    </JourneyGate>
  );
}
