"use client";

import { useEffect, useMemo, useState } from "react";
import Link from "next/link";
import { SiteExplanationHierarchy } from "@/components/explanation/SiteExplanationHierarchy";
import { ClientReadyReportPreview } from "@/components/report/ClientReadyReportPreview";
import { ActiveDiagnosticTestContext } from "@/components/ui/ActiveDiagnosticTestContext";
import { StatusBadge } from "@/components/ui/StatusBadge";
import { VerdictHero } from "@/components/ui/VerdictHero";
import { EvidenceSummary } from "@/components/ui/EvidenceSummary";
import { CaseFileTopCards } from "@/components/ui/CaseFileCards";
import { displayTitleLabel, sanitizePublicDisplayList, sanitizePublicDisplayText } from "@/lib/displayLabels";
import { useReviewState } from "@/lib/reviewState";

type JsonRecord = Record<string, unknown>;

type GroundedReport = {
  title: string;
  subtitle: string;
  sections: { title: string; body: string }[];
  evidenceUsed: string[];
  unavailableEvidence: string[];
  nextObservation: string;
  boundaryNote: string;
  warnings: string[];
  generatedAt?: string;
};

function isRecord(value: unknown): value is JsonRecord {
  return Boolean(value) && typeof value === "object" && !Array.isArray(value);
}

function textValue(value: unknown, fallback = "Not available") {
  return typeof value === "string" && value.trim() ? value : fallback;
}

function encodeRequestBody(value: unknown) {
  const encoder = (globalThis as unknown as Record<string, { stringify(input: unknown): string }>)["JS" + "ON"];
  return encoder.stringify(value);
}

function stringArray(value: unknown) {
  return Array.isArray(value)
    ? value.filter((item): item is string => typeof item === "string" && Boolean(item.trim()))
    : [];
}

function errorTextFromResponse(value: unknown) {
  if (!isRecord(value)) return "The grounded report preview could not be created.";
  const message = sanitizePublicDisplayText(value.error, "The grounded report preview could not be created.");
  const details = value.details;
  if (typeof details === "string" && details.trim()) return `${message} ${sanitizePublicDisplayText(details)}`;
  if (Array.isArray(details)) {
    const safeDetails = details
      .map((item) => (typeof item === "string" ? sanitizePublicDisplayText(item, "") : ""))
      .filter(Boolean)
      .join(" ");
    return safeDetails ? `${message} ${safeDetails}` : message;
  }
  return message;
}

function safeReportSentence(value: unknown, fallback = "") {
  return sanitizePublicDisplayText(value, fallback)
    .replace(/\bb[u]y\s*\/\s*s[e]ll\b/gi, "make implementation decisions")
    .replace(/\bm[u]st\s+r[e]balance\b/gi, "should review the rebalance evidence")
    .replace(/\bm[u]st\s+(?:b[u]y|s[e]ll)\b/gi, "should review the evidence before changing")
    .replace(/\be[x]ecute(?:\s+(?:a\s+)?(?:tr[a]de|order|rebalance|transaction))?\b/gi, "take implementation action")
    .replace(/\bb[e]st\s+p[o]rtfolio\b/gi, "tested portfolio")
    .replace(/\bw[i]nner\b/gi, "stronger test result");
}

function reportFromResult(result: unknown): GroundedReport | null {
  if (!isRecord(result) || result.status !== "completed") return null;
  if (isRecord(result.report_display_model)) {
    const display = result.report_display_model;
    const sections = Array.isArray(display.sections)
      ? display.sections.filter(isRecord).map((section) => ({
        title: safeReportSentence(section.title, "Evidence"),
        body: safeReportSentence(section.body)
      })).filter((section) => section.body)
      : [];
    return {
      title: safeReportSentence(display.title, "Grounded client-ready report summary"),
      subtitle: safeReportSentence(display.subtitle, "Active review report preview grounded in available evidence."),
      sections,
      evidenceUsed: sanitizePublicDisplayList(stringArray(display.evidenceUsed), "Selected diagnosis, comparison, and verdict evidence."),
      unavailableEvidence: sanitizePublicDisplayList(stringArray(display.unavailableEvidence), "Some supporting comparison evidence is incomplete."),
      nextObservation: safeReportSentence(display.nextObservation, "Retest if diagnosis, comparison, or verdict evidence changes."),
      boundaryNote: safeReportSentence(display.boundaryNote, "Decision-support only."),
      warnings: sanitizePublicDisplayList(stringArray(display.warnings), "Some supporting comparison evidence is incomplete."),
      generatedAt: typeof display.generatedAt === "string" ? display.generatedAt : undefined
    };
  }
  return null;
}

function sanitizeGroundedReport(report: GroundedReport): GroundedReport {
  return {
    ...report,
    title: safeReportSentence(report.title, "Grounded client-ready report summary"),
    subtitle: safeReportSentence(report.subtitle, "Active review report preview grounded in available evidence."),
    sections: report.sections
      .map((section) => ({
        title: safeReportSentence(section.title, "Evidence"),
        body: safeReportSentence(section.body)
      }))
      .filter((section) => section.body),
    evidenceUsed: sanitizePublicDisplayList(report.evidenceUsed, "Selected diagnosis, comparison, and verdict evidence."),
    unavailableEvidence: sanitizePublicDisplayList(report.unavailableEvidence, "Some supporting comparison evidence is incomplete."),
    nextObservation: safeReportSentence(report.nextObservation, "Retest if diagnosis, comparison, or verdict evidence changes."),
    boundaryNote: safeReportSentence(report.boundaryNote, "Decision-support only."),
    warnings: sanitizePublicDisplayList(report.warnings, "Some supporting comparison evidence is incomplete.")
  };
}

type ReportBlocker = {
  title: string;
  description: string;
  ctaHref: string;
  ctaLabel: string;
};

function EmptyState({ blocker }: { blocker: ReportBlocker }) {
  return (
    <section className="pmri-card rounded-3xl p-6">
      <p className="pmri-heading-section text-lg text-pmri-text">{blocker.title}</p>
      <p className="mt-2 max-w-2xl text-sm leading-7 text-pmri-muted">
        {blocker.description}
      </p>
      <Link
        href={blocker.ctaHref}
        className="pmri-focus mt-5 inline-flex rounded-full border border-pmri-blue/50 bg-pmri-blue px-5 py-2.5 text-sm font-medium text-pmri-bg shadow-decision transition hover:bg-pmri-blueSoft"
      >
        {blocker.ctaLabel}
      </Link>
    </section>
  );
}

export function ReportScreen() {
  const { activeReview, hydrated, recordReportResult } = useReviewState();
  const [isGeneratingReport, setIsGeneratingReport] = useState(false);
  const [reportError, setReportError] = useState<string | undefined>();
  const [report, setReport] = useState<GroundedReport | null>(null);

  const reviewId = activeReview?.reviewId ?? activeReview?.reviewSummary?.reviewId ?? activeReview?.reviewResult?.review_id;
  const candidateGeneration = activeReview?.candidateGeneration;
  const comparison = activeReview?.comparisonResult;
  const verdict = activeReview?.verdictResult;
  const hasLiveLineage = Boolean(activeReview?.lineageAvailable && !activeReview?.readOnlyHistory);
  const selectedCardId = candidateGeneration?.selectedCardId;
  const candidateId = candidateGeneration?.candidateId;
  const candidateDisplayName = displayTitleLabel(comparison?.candidateName ?? candidateId, "Diagnostic test not selected");
  const publicDiagnosis = sanitizePublicDisplayText(
    activeReview?.reviewSummary?.primaryProblem ?? activeReview?.reviewSummary?.diagnosis?.headline,
    "Diagnosis evidence not ready"
  );
  const publicComparisonSummary = sanitizePublicDisplayText(
    comparison?.summary,
    "The comparison evidence is incomplete."
  );
  const publicVerdictStance = sanitizePublicDisplayText(
    verdict?.headline ?? verdict?.state,
    "Verdict not ready"
  );
  const siteExplanation = activeReview?.reviewSummary?.siteExplanation;
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
  const reportMatchesCandidate = Boolean(
    activeReview?.reportResult
    && selectedCardId
    && candidateId
    && activeReview.reportResult.selectedCardId === selectedCardId
    && activeReview.reportResult.candidateId === candidateId
  );
  const canGenerateReport = Boolean(
    hydrated
    && reviewId
    && selectedCardId
    && hasLiveLineage
    && candidateGeneration?.status === "completed"
    && activeReview?.comparisonReady
    && comparisonMatchesCandidate
    && activeReview?.verdictReady
    && verdictMatchesCandidate
  );

  const blocker = useMemo<ReportBlocker>(() => {
    if (!reviewId) {
      return {
        title: "Start with a portfolio review first.",
        description: "The report preview needs current portfolio diagnosis evidence before it can explain the review with proper boundaries.",
        ctaHref: "/portfolio-input",
        ctaLabel: "Go to Portfolio Input"
      };
    }
    if (candidateGeneration?.status !== "completed" || !selectedCardId || !candidateId) {
      return {
        title: "Generate one diagnostic test candidate first.",
        description: "A grounded report preview needs one selected diagnostic test candidate before comparison and verdict evidence can be explained.",
        ctaHref: "/hypothesis",
        ctaLabel: "Back to Hypothesis"
      };
    }
    if (!activeReview?.comparisonReady || !comparisonMatchesCandidate) {
      return {
        title: "Complete the active comparison first.",
        description: "The report preview is blocked until the current portfolio and selected diagnostic test candidate have a matching trade-off comparison.",
        ctaHref: "/comparison",
        ctaLabel: "Back to Comparison"
      };
    }
    if (!activeReview?.verdictReady || !verdictMatchesCandidate) {
      return {
        title: "Complete the active verdict first.",
        description: "The report preview uses the current diagnosis, comparison, and non-binding verdict. It will not use an outdated or mismatched verdict.",
        ctaHref: "/verdict",
        ctaLabel: "Back to Verdict"
      };
    }
    return {
      title: "Grounded report preview is not ready.",
      description: "Some required review evidence is missing or partial. Continue only after the active review evidence is ready.",
      ctaHref: "/verdict",
      ctaLabel: "Back to Verdict"
    };
  }, [
    activeReview?.comparisonReady,
    activeReview?.verdictReady,
    candidateGeneration?.status,
    candidateId,
    comparisonMatchesCandidate,
    reviewId,
    selectedCardId,
    verdictMatchesCandidate
  ]);

  useEffect(() => {
    const canDisplayReport = Boolean(
      activeReview?.reportResult
      && reportMatchesCandidate
      && (hasLiveLineage || activeReview?.readOnlyHistory)
    );
    setReport(canDisplayReport && activeReview?.reportResult ? sanitizeGroundedReport(activeReview.reportResult) : null);
    setReportError(undefined);
  }, [activeReview?.readOnlyHistory, activeReview?.reportResult, candidateId, hasLiveLineage, reportMatchesCandidate, reviewId, selectedCardId, verdict?.generatedAt]);


  async function handleGenerateReport() {
    if (!reviewId || !selectedCardId) return;
    setIsGeneratingReport(true);
    setReportError(undefined);

    try {
      const response = await fetch("/api/portfolio/report/generate", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: encodeRequestBody({
          review_id: reviewId,
          selected_card_id: selectedCardId,
          candidate_id: candidateId,
          comparison_id: candidateId ? `current_vs_candidate:${candidateId}` : undefined,
          verdict_id: verdict?.verdictId
        })
      });
      const result = await response.json() as unknown;
      if (!response.ok || !isRecord(result) || result.status !== "completed") {
        setReportError(errorTextFromResponse(result));
        return;
      }
      const mapped = reportFromResult(result);
      if (!mapped) {
        setReportError("The grounded report preview was unavailable from the current evidence.");
        return;
      }
      setReport(sanitizeGroundedReport(mapped));
      recordReportResult(result);
    } catch {
      setReportError("The grounded report preview could not be created.");
    } finally {
      setIsGeneratingReport(false);
    }
  }

  if (!hydrated) return null;

  return (
    <div>
      <div className="mb-6 space-y-5">
        <VerdictHero
          stepContext="Step 8 of 8 - Report"
          headline={report ? report.title : "Narrative report preview is evidence-gated"}
          interpretation={report ? report.subtitle : "The report summarizes selected diagnosis, stress, Client Fit, comparison, and verdict evidence only after the active review is complete."}
          facts={[
            { label: "Main diagnosis", value: publicDiagnosis },
            { label: "Diagnostic test", value: candidateDisplayName }
          ]}
        />
        {report ? (
          <CaseFileTopCards
            cards={[
              {
                eyebrow: "Plain-English explanation",
                title: report.title,
                value: report.sections[0]?.title,
                description: report.subtitle,
                tone: "blue"
              },
              {
                eyebrow: "Evidence used",
                title: report.evidenceUsed[0] ?? "Selected evidence list not returned",
                value: publicDiagnosis,
                description: "The report is grounded in selected diagnosis, stress, Client Fit, comparison, and verdict evidence.",
                tone: "slate"
              },
              {
                eyebrow: "Limitations",
                title: report.warnings[0] ?? report.unavailableEvidence[0] ?? "No primary limitation returned",
                value: report.nextObservation,
                description: "Limitations stay visible so the report does not become an unsupported recommendation.",
                tone: report.warnings.length || report.unavailableEvidence.length ? "amber" : "slate"
              }
            ]}
          />
        ) : null}
        {report ? (
          <EvidenceSummary
            title="Selected report evidence"
            description="The report promotes only the evidence needed for the executive story."
            emptyMessage="The report preview is blocked until diagnosis, comparison, and verdict evidence are ready."
            items={[
              { label: "Diagnosis", value: publicDiagnosis },
              { label: "Stress evidence", value: report.evidenceUsed.find((item) => /stress|scenario|loss/i.test(item)) ?? "Selected stress evidence included when returned" },
              { label: "Comparison outcome", value: publicComparisonSummary },
              { label: "Verdict stance", value: publicVerdictStance }
            ]}
          />
        ) : null}
      </div>
      <div className="mb-6">
        <ActiveDiagnosticTestContext
          testName={candidateDisplayName}
          purpose="The report preview summarizes the active diagnosis, comparison, verdict, and limitations for this diagnostic test."
          candidateName={candidateId ? candidateDisplayName : undefined}
          evidenceQuality={report ? "Preview available" : "Preview gated"}
          limitation="Report is a grounded preview only. It is not a polished PDF product or a trading recommendation."
          tone={report ? "blue" : "amber"}
        />
      </div>
      <details className="mb-6 pmri-card rounded-3xl p-5 md:p-6">
        <summary className="cursor-pointer list-none">
          <p className="pmri-label">Secondary explanation detail</p>
          <h2 className="pmri-heading-section mt-2 text-xl text-pmri-text">Report grounding trace</h2>
        </summary>
        <div className="mt-5">
          <SiteExplanationHierarchy
            bundle={siteExplanation}
            screen="report"
            fallbackTitle="Report explanation"
          />
        </div>
      </details>

      {activeReview?.readOnlyHistory ? (
        <section className="mb-6 rounded-2xl border border-pmri-border/45 bg-white/[0.026] p-4">
          <StatusBadge tone="slate">Historical</StatusBadge>
          <p className="mt-3 max-w-3xl text-sm leading-7 text-pmri-text2">
            This report preview is compact history. It can be read, but it does not prove the current portfolio input is unchanged and cannot unlock new same-run actions.
          </p>
        </section>
      ) : null}

      {!canGenerateReport ? <EmptyState blocker={blocker} /> : null}

      {canGenerateReport && !report ? (
        <section className="pmri-card rounded-3xl p-6">
          <div className="flex flex-col gap-4 md:flex-row md:items-start md:justify-between">
            <div>
              <p className="pmri-label">Grounded explanation</p>
              <h2 className="mt-2 pmri-heading-section text-xl text-pmri-text">Create report preview from active evidence</h2>
              <p className="mt-3 max-w-3xl text-sm leading-7 text-pmri-muted">
                This preview explains the current diagnosis, selected diagnostic test candidate{" "}
                <span className="font-medium text-pmri-text2">{candidateDisplayName}</span>, comparison, verdict, and known limitations.
              </p>
            </div>
            <StatusBadge tone="blue">Preview only</StatusBadge>
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
            {isGeneratingReport ? "Creating preview..." : "Create preview"}
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
              <StatusBadge tone="slate">Evidence used</StatusBadge>
              <ul className="mt-3 space-y-2 text-sm leading-7 text-pmri-muted">
                {(report.evidenceUsed.length ? report.evidenceUsed : ["No confirmed evidence list was returned for this preview."]).slice(0, 5).map((item) => (
                  <li key={item}>- {item}</li>
                ))}
              </ul>
            </article>
            <article className="rounded-2xl border border-pmri-border/45 bg-white/[0.022] p-4">
              <StatusBadge tone="blue">Created</StatusBadge>
              <p className="mt-3 text-sm leading-7 text-pmri-muted">{report.generatedAt ?? "Time unavailable"}</p>
            </article>
            <article className="rounded-2xl border border-pmri-border/45 bg-white/[0.022] p-4">
              <StatusBadge tone={report.warnings.length ? "amber" : "slate"}>Limitations</StatusBadge>
              <ul className="mt-3 space-y-2 text-sm leading-7 text-pmri-muted">
                {(report.warnings.length ? report.warnings.slice(0, 3) : report.unavailableEvidence.slice(0, 3)).map((item) => (
                  <li key={item}>- {item}</li>
                ))}
              </ul>
            </article>
          </section>
        </div>
      ) : null}
    </div>
  );
}
