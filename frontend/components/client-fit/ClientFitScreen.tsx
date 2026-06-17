"use client";

import Link from "next/link";
import { StatusBadge } from "@/components/ui/StatusBadge";
import { VerdictHero } from "@/components/ui/VerdictHero";
import { EvidenceSummary } from "@/components/ui/EvidenceSummary";
import { MetricMatrix } from "@/components/ui/MetricMatrix";
import { buildClientFitPresentation, type ClientFitReason } from "@/lib/clientFitPresentation";
import { useReviewState } from "@/lib/reviewState";
import type { ClientFitDisplaySummary } from "@/lib/generated/api-types";
import type { StatusTone } from "@/lib/types";

function hasSummary(summary: ClientFitDisplaySummary | undefined) {
  return Boolean(summary && typeof summary.status_label === "string" && summary.status_label.trim());
}

function isMissingProfile(summary: ClientFitDisplaySummary | undefined) {
  return /not provided|profile missing/i.test(summary?.status_label ?? "");
}

const toneAccent: Record<StatusTone, string> = {
  blue: "from-pmri-blue/18 via-white/[0.035] to-transparent",
  gold: "from-pmri-borderSoft/16 via-white/[0.035] to-transparent",
  green: "from-white/[0.08] via-white/[0.03] to-transparent",
  amber: "from-pmri-amber/18 via-white/[0.035] to-transparent",
  red: "from-pmri-risk/18 via-white/[0.035] to-transparent",
  slate: "from-white/[0.08] via-white/[0.03] to-transparent"
};

const rowToneClass: Record<StatusTone, string> = {
  blue: "border-pmri-blue/18 bg-pmri-blue/[0.035]",
  gold: "border-pmri-borderSoft/20 bg-white/[0.025]",
  green: "border-pmri-border/55 bg-white/[0.02]",
  amber: "border-pmri-amber/20 bg-pmri-amber/[0.04]",
  red: "border-pmri-risk/20 bg-pmri-risk/[0.04]",
  slate: "border-pmri-border/55 bg-white/[0.02]"
};

function LockedClientFitState() {
  return (
    <section className="pmri-card rounded-3xl p-6 md:p-8">
      <StatusBadge tone="amber">Evidence required</StatusBadge>
      <h2 className="pmri-heading-section mt-4 text-2xl text-pmri-text">Run the profile-first diagnosis before this check.</h2>
      <p className="mt-3 max-w-2xl text-sm leading-7 text-pmri-muted">
        This screen needs a completed risk profile, portfolio diagnosis, and Stress Test Lab evidence.
      </p>
      <div className="mt-6 flex flex-wrap gap-3">
        <Link href="/client-profile" className="pmri-focus pmri-primary-action rounded-full px-5 py-2.5 text-sm font-medium transition">Open risk profile</Link>
        <Link href="/portfolio-input" className="pmri-focus rounded-full border border-pmri-border/60 bg-white/[0.025] px-5 py-2.5 text-sm font-medium text-pmri-text2 transition hover:border-pmri-blue/35 hover:text-pmri-text">Portfolio Input</Link>
      </div>
    </section>
  );
}

function ReasonCard({ reason, index }: { reason: ClientFitReason; index: number }) {
  return (
    <article className={`pmri-hover-panel rounded-3xl border p-4 ${rowToneClass[reason.tone] ?? rowToneClass.slate}`}>
      <div className="flex items-start justify-between gap-4">
        <div>
          <p className="pmri-label">Reason {index + 1}</p>
          <h3 className="pmri-heading-section mt-2 text-lg text-pmri-text">{reason.label}</h3>
        </div>
        <StatusBadge tone={reason.tone}>{reason.status}</StatusBadge>
      </div>
      <div className="mt-5 grid grid-cols-2 gap-3 text-sm">
        <div className="rounded-2xl border border-pmri-border/45 bg-black/10 p-3">
          <p className="pmri-label">Portfolio</p>
          <p className="data-figure mt-1 text-lg text-pmri-text">{reason.value}</p>
        </div>
        <div className="rounded-2xl border border-pmri-border/45 bg-black/10 p-3">
          <p className="pmri-label">Profile</p>
          <p className="data-figure mt-1 text-lg text-pmri-text">{reason.target}</p>
        </div>
      </div>
      <p className="mt-4 text-sm leading-6 text-pmri-muted">{reason.explanation}</p>
    </article>
  );
}

function CompactCheckRow({ reason }: { reason: ClientFitReason }) {
  return (
    <div className="grid gap-3 border-t border-pmri-border/35 px-5 py-4 text-sm md:grid-cols-[1.15fr_0.8fr_0.9fr_auto] md:items-center">
      <div>
        <p className="font-medium text-pmri-text">{reason.label}</p>
        <p className="mt-1 text-xs leading-5 text-pmri-muted md:hidden">{reason.explanation}</p>
      </div>
      <p className="data-figure text-pmri-text2">{reason.value}</p>
      <p className="data-figure text-pmri-text2">{reason.target}</p>
      <StatusBadge tone={reason.tone}>{reason.status}</StatusBadge>
    </div>
  );
}

export function ClientFitScreen() {
  const { activeReview, hydrated } = useReviewState();
  const summary = activeReview?.reviewSummary?.clientFit;
  const ready = Boolean(activeReview?.runStatus === "completed" && activeReview.evidenceReady && hasSummary(summary));
  const siteExplanation = activeReview?.reviewSummary?.siteExplanation;
  const presentation = buildClientFitPresentation(ready ? summary : undefined, siteExplanation);
  const missingProfile = ready && isMissingProfile(summary);

  return (
    <div>
      <VerdictHero
        stepContext="Step 4 of 8 - Client Fit"
        headline={ready ? presentation.headline : "Risk profile check is required"}
        interpretation={ready ? presentation.summary : "This screen checks alignment with the stated profile after diagnosis and Stress Lab evidence are available."}
        facts={[
          { label: "Profile", value: ready ? presentation.profileLabel : "Unavailable" },
          { label: "Evidence", value: ready ? presentation.sourceLabel : "Evidence required" }
        ]}
      />

      {!hydrated ? null : !ready ? (
        <LockedClientFitState />
      ) : (
        <div className="space-y-6">
          {missingProfile ? (
            <section className="pmri-card rounded-3xl p-5 md:p-6">
              <p className="pmri-label">Missing profile</p>
              <h2 className="pmri-heading-section mt-2 text-2xl text-pmri-text">Complete your risk profile to unlock this check.</h2>
              <p className="mt-3 max-w-3xl text-sm leading-7 text-pmri-muted">
                Backend-compatible runs can preserve a missing-profile state, but the normal web journey uses your profile before testing a hypothesis.
              </p>
              <Link href="/client-profile" className="pmri-focus pmri-primary-action mt-5 inline-flex rounded-full px-5 py-2.5 text-sm font-medium transition">
                Open risk profile
              </Link>
            </section>
          ) : (
            <>
              <EvidenceSummary
                title="Main profile mismatch dimensions"
                description="Only the most relevant fit facts are shown before the full row-level check."
                items={presentation.primaryReasons.map((reason) => ({
                  label: reason.label,
                  value: `${reason.value} vs ${reason.target}. ${reason.explanation}`,
                  tone: reason.tone
                }))}
              />

              <MetricMatrix
                title="Client Fit checks by profile dimension"
                description="Rows compare the current portfolio evidence with stated profile limits. Missing values are shown as Unavailable rather than inferred."
                groups={[{
                  title: "Portfolio vs stated profile",
                  description: "Row-level statuses are restrained and used only where they clarify a specific profile dimension.",
                  rows: presentation.allRows.map((reason) => ({
                    metric: reason.label,
                    portfolioValue: reason.value,
                    reference: reason.target,
                    status: reason.tone === "red" || reason.tone === "amber" ? { label: reason.status, tone: reason.tone } : undefined,
                    meaning: reason.explanation,
                    material: reason.tone === "red" || reason.tone === "amber"
                  }))
                }]}
              />
            </>
          )}

          <section className="grid gap-6 lg:grid-cols-[1fr_0.9fr]">
            <details className="pmri-card rounded-3xl p-5 md:p-6">
              <summary className="cursor-pointer list-none">
                <p className="pmri-label">Evidence details</p>
                <h2 className="pmri-heading-section mt-2 text-xl text-pmri-text">How we checked this</h2>
                <p className="mt-3 text-sm leading-7 text-pmri-muted">{presentation.evidenceSummary}</p>
              </summary>
              <div className="mt-5 space-y-3">
                {presentation.technicalDetails.map((detail) => (
                  <p key={detail} className="rounded-2xl border border-pmri-border/45 bg-white/[0.018] p-4 text-sm leading-7 text-pmri-muted">
                    {detail}
                  </p>
                ))}
              </div>
            </details>

            <article className="pmri-card rounded-3xl p-5 md:p-6">
              <p className="pmri-label">Next step</p>
              <h2 className="pmri-heading-section mt-2 text-xl text-pmri-text">Continue with one diagnostic hypothesis</h2>
              <p className="mt-3 text-sm leading-7 text-pmri-text2">{presentation.nextBestTest}</p>
              <Link href="/hypothesis" className="pmri-focus pmri-primary-action mt-5 inline-flex rounded-full px-5 py-2.5 text-sm font-medium transition">
                Continue to Hypothesis
              </Link>
            </article>
          </section>
        </div>
      )}
    </div>
  );
}
