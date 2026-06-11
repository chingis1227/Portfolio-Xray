"use client";

import Link from "next/link";
import { useSearchParams } from "next/navigation";
import { Suspense } from "react";
import { PageHeader } from "@/components/layout/PageHeader";
import { SiteExplanationHierarchy } from "@/components/explanation/SiteExplanationHierarchy";
import { StressTestLab } from "@/components/evidence/StressTestLab";
import { StatusBadge } from "@/components/ui/StatusBadge";
import sampleStressLabData from "@/data/demo/stress-lab.json";
import { buildStressLabModelFromOutputs, ensureStressLabModel } from "@/components/evidence/stressLabModel";
import { cleanSiteExplanationBundle, useReviewState } from "@/lib/reviewState";

function LockedStressLabState() {
  return (
    <section className="pmri-card rounded-2xl p-6 md:p-8">
      <StatusBadge tone="amber">Stress review locked</StatusBadge>
      <h2 className="mt-4 pmri-heading-section text-2xl text-pmri-text">
        Complete Portfolio Input first to unlock Stress Test Lab.
      </h2>
      <p className="mt-3 max-w-2xl text-sm leading-7 text-pmri-muted">
        Run a current-portfolio diagnosis first. Stress Test Lab will then show scenario losses, helped and hurt assets, hedge gaps, and data limitations.
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

function MissingStressLabState() {
  return (
    <section className="pmri-card rounded-2xl border-pmri-amber/30 p-6 md:p-8">
      <StatusBadge tone="amber">Stress evidence limited</StatusBadge>
      <h2 className="mt-4 pmri-heading-section text-2xl text-pmri-text">
        Full Stress Test Lab detail is not available in this saved browser state.
      </h2>
      <p className="mt-3 max-w-2xl text-sm leading-7 text-pmri-muted">
        Saved browser state keeps only a compact summary. Rerun Portfolio Input to rebuild the full stress scenario library, loss contribution, hedge gap, and historical limitation detail.
      </p>
      <Link
        href="/portfolio-input"
        className="pmri-focus mt-6 inline-flex rounded-full border border-pmri-blue/50 bg-pmri-blue px-5 py-2.5 text-sm font-medium text-pmri-bg transition hover:bg-pmri-blueSoft"
      >
        Rerun Portfolio Input
      </Link>
    </section>
  );
}

function EvidencePageContent() {
  const { activeReview, hydrated } = useReviewState();
  const searchParams = useSearchParams();
  const sampleMode = searchParams.get("sample") === "1";
  const completedRealReview = Boolean(
    activeReview?.submitted
    && activeReview.runMode === "real_run"
    && activeReview.runStatus === "completed"
  );
  const realStressLab = completedRealReview
    ? buildStressLabModelFromOutputs(activeReview?.reviewResult?.outputs)
    : null;
  const model = realStressLab ?? (sampleMode ? ensureStressLabModel(sampleStressLabData) : null);
  const stateLabel = realStressLab ? "Stress review ready" : sampleMode ? "Sample review" : "Stress review locked";
  const stateTone = realStressLab ? "green" : sampleMode ? "amber" : "slate";
  const siteExplanation = cleanSiteExplanationBundle(activeReview?.reviewResult?.outputs?.site_explanation_bundle)
    ?? activeReview?.reviewSummary?.siteExplanation;

  return (
    <div>
      <PageHeader
        kicker="Step 03 / Stress Test Lab"
        title="Stress Test Lab"
        description="How the current portfolio behaves under historical and synthetic market stress."
        boundaryNote="Current portfolio only. No candidate or rebalance verdict is created in Stress Test Lab."
      >
        <StatusBadge tone={stateTone}>{stateLabel}</StatusBadge>
      </PageHeader>
      <SiteExplanationHierarchy
        bundle={siteExplanation}
        screen="evidence"
        fallbackTitle="Stress evidence explanation"
      />
      {!hydrated ? null : model ? (
        <StressTestLab model={model} />
      ) : completedRealReview ? (
        <MissingStressLabState />
      ) : (
        <LockedStressLabState />
      )}
    </div>
  );
}

export default function EvidencePage() {
  return (
    <Suspense fallback={null}>
      <EvidencePageContent />
    </Suspense>
  );
}
