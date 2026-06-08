"use client";

import Link from "next/link";
import { PageHeader } from "@/components/layout/PageHeader";
import { DiagnosisSummaryPanel } from "@/components/diagnosis/DiagnosisSummaryPanel";
import { StatusBadge } from "@/components/ui/StatusBadge";
import { buildDiagnosisFromReview, useReviewState } from "@/lib/reviewState";

function FailedDiagnosisState({ message, details }: { message: string; details?: string }) {
  return (
    <section className="pmri-card rounded-2xl border-pmri-risk/35 p-6 md:p-8">
      <StatusBadge tone="red">Real run failed</StatusBadge>
      <h2 className="mt-4 text-2xl font-semibold tracking-[-0.02em] text-pmri-text">
        Portfolio diagnosis could not be completed.
      </h2>
      <p className="mt-3 max-w-2xl text-sm leading-6 text-pmri-text2">{message}</p>
      {details ? (
        <pre className="mt-4 max-h-56 overflow-auto rounded-xl border border-pmri-border bg-pmri-secondary p-4 text-xs leading-5 text-pmri-muted">{details}</pre>
      ) : null}
      <Link
        href="/portfolio-input"
        className="pmri-focus mt-6 inline-flex rounded-full border border-pmri-blue/50 bg-pmri-blue px-5 py-2.5 text-sm font-semibold text-white transition hover:bg-pmri-blueSoft"
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
      <h2 className="mt-4 text-2xl font-semibold tracking-[-0.02em] text-pmri-text">
        Complete Portfolio Input first to unlock Diagnosis.
      </h2>
      <p className="mt-3 max-w-2xl text-sm leading-6 text-pmri-muted">
        Enter the current portfolio and run diagnosis so this page can reflect the active review.
      </p>
      <Link
        href="/portfolio-input"
        className="pmri-focus mt-6 inline-flex rounded-full border border-pmri-blue/50 bg-pmri-blue px-5 py-2.5 text-sm font-semibold text-white transition hover:bg-pmri-blueSoft"
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
  const sourceLabel = diagnosisReady
    ? activeReview?.runMode === "real_run" ? "Real run" : "Sample demo"
    : failedRealRun ? "Real run failed" : "Diagnosis locked";

  return (
    <div>
      <PageHeader
        kicker="Step 02 / Diagnosis"
        title="Diagnosis summary before any candidate"
        description="The decision room first explains what appears wrong or fragile in the current portfolio. It does not jump to optimization."
      >
        <StatusBadge tone={failedRealRun ? "red" : diagnosisReady ? "gold" : "amber"}>{sourceLabel}</StatusBadge>
      </PageHeader>
      {!hydrated ? null : failedRealRun && activeReview?.reviewError ? (
        <FailedDiagnosisState message={activeReview.reviewError.message} details={activeReview.reviewError.details} />
      ) : diagnosis ? <DiagnosisSummaryPanel {...diagnosis} /> : <LockedDiagnosisState />}
    </div>
  );
}
