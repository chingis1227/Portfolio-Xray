"use client";

import Link from "next/link";
import { PageHeader } from "@/components/layout/PageHeader";
import { DiagnosisSummaryPanel } from "@/components/diagnosis/DiagnosisSummaryPanel";
import { SiteExplanationHierarchy } from "@/components/explanation/SiteExplanationHierarchy";
import { StatusBadge } from "@/components/ui/StatusBadge";
import { buildDiagnosisFromReview, useReviewState } from "@/lib/reviewState";

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

export default function DiagnosisPage() {
  const { activeReview, hydrated } = useReviewState();
  const diagnosisReady = Boolean(
    activeReview?.submitted
    && activeReview.diagnosisReady
    && activeReview.runStatus === "completed"
    && activeReview.reviewSummary
  );
  const failedRealRun = Boolean(activeReview?.runMode === "real_run" && activeReview.runStatus === "failed");
  const diagnosis = diagnosisReady && activeReview ? buildDiagnosisFromReview(activeReview) : null;
  const xraySummary = diagnosisReady ? activeReview?.reviewSummary?.xraySummary : undefined;
  const siteExplanation = activeReview?.reviewSummary?.siteExplanation;

  return (
    <div>
      <PageHeader
        kicker="Investment Decision Room"
        title="Portfolio X-Ray Diagnosis"
        description="Current-portfolio review before any candidate test."
      />
      <SiteExplanationHierarchy
        bundle={siteExplanation}
        screen="diagnosis"
        fallbackTitle="Diagnosis explanation"
      />
      {!hydrated ? null : failedRealRun && activeReview?.reviewError ? (
        <FailedDiagnosisState message={activeReview.reviewError.message} details={activeReview.reviewError.details} />
      ) : diagnosis ? <DiagnosisSummaryPanel {...diagnosis} xraySummary={xraySummary} /> : <LockedDiagnosisState />}
    </div>
  );
}
