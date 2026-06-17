"use client";

import Link from "next/link";
import { useSearchParams } from "next/navigation";
import { StressTestLab } from "@/components/evidence/StressTestLab";
import { StatusBadge } from "@/components/ui/StatusBadge";
import { VerdictHero } from "@/components/ui/VerdictHero";
import { EvidenceSummary } from "@/components/ui/EvidenceSummary";
import { buildStressStoryViewModel } from "@/components/evidence/stressStoryModel";
import sampleStressLabData from "@/data/demo/stress-lab.json";
import { ensureStressLabModel } from "@/components/evidence/stressLabModel";
import { useReviewState } from "@/lib/reviewState";

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
    ? activeReview?.reviewSummary?.stressLabModel ?? null
    : null;
  const model = realStressLab ?? (sampleMode ? ensureStressLabModel(sampleStressLabData) : null);
  const siteExplanation = activeReview?.reviewSummary?.siteExplanation;
  const story = model ? buildStressStoryViewModel(model, siteExplanation) : null;

  return (
    <div>
      {story ? (
        <div className="mb-6 space-y-5">
          <VerdictHero
            stepContext="Step 3 of 8 - Stress Lab"
            headline={story.title}
            interpretation={story.answer}
            facts={[
              { label: "Worst scenario", value: story.metrics.find((item) => item.label === "Worst scenario")?.value ?? "Unavailable" },
              { label: "Estimated loss", value: story.metrics.find((item) => item.label === "Worst scenario")?.detail.replace(/^Estimated loss:\s*/, "") ?? "Unavailable" }
            ]}
          />
          <EvidenceSummary
            title="Stress evidence summary"
            description="The summary shows only the facts that explain the current-portfolio stress answer."
            items={story.metrics.map((metric) => ({ label: metric.label, value: `${metric.value} - ${metric.detail}`, tone: metric.tone }))}
          />
        </div>
      ) : null}
      {!hydrated ? null : model ? (
        <>
          <StressTestLab model={model} siteExplanation={siteExplanation} />
          <section className="pmri-card mt-6 rounded-3xl p-5 md:p-6">
            <div className="flex flex-col gap-4 md:flex-row md:items-center md:justify-between">
              <div>
                <p className="pmri-label">Next step</p>
                <h2 className="pmri-heading-section mt-2 text-2xl text-pmri-text">Review Client Fit before testing a hypothesis</h2>
                <p className="mt-2 max-w-2xl text-sm leading-6 text-pmri-muted">
                  Stress Test Lab is objective portfolio evidence. The next screen separately checks whether this risk fits the stated profile.
                </p>
              </div>
              <Link href="/client-fit" className="pmri-focus pmri-primary-action rounded-full px-5 py-2.5 text-sm font-medium transition">
                Continue to Client Fit
              </Link>
            </div>
          </section>
        </>
      ) : completedRealReview ? (
        <MissingStressLabState />
      ) : (
        <LockedStressLabState />
      )}
    </div>
  );
}

export function EvidenceScreen() {
  return <EvidencePageContent />;
}
