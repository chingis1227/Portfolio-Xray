"use client";

import Link from "next/link";
import { PageHeader } from "@/components/layout/PageHeader";
import { SiteExplanationHierarchy } from "@/components/explanation/SiteExplanationHierarchy";
import { StatusBadge } from "@/components/ui/StatusBadge";
import { useReviewState } from "@/lib/reviewState";
import type { ClientFitDisplaySummary } from "@/lib/generated/api-types";

function isProvided(summary: ClientFitDisplaySummary | undefined) {
  const label = (summary?.status_label ?? "").toLowerCase();
  return Boolean(summary && label && !label.includes("not provided"));
}

function fallbackText(value: string | null | undefined, fallback: string) {
  return typeof value === "string" && value.trim() ? value : fallback;
}

function profileTargetRows(summary: ClientFitDisplaySummary | undefined) {
  const rows = summary?.target_rows ?? [];
  return rows.length ? rows : [
    { dimension_label: "Target return", portfolio_value_label: "Not evaluated", target_or_limit_label: "Provided profile required", status_label: "Not provided", status_tone: "amber" as const, explanation: "Complete Client Profile and rerun diagnosis to evaluate this row." },
    { dimension_label: "Volatility", portfolio_value_label: "Not evaluated", target_or_limit_label: "Provided profile required", status_label: "Not provided", status_tone: "amber" as const, explanation: "Complete Client Profile and rerun diagnosis to evaluate this row." },
    { dimension_label: "Temporary loss", portfolio_value_label: "Not evaluated", target_or_limit_label: "Provided profile required", status_label: "Not provided", status_tone: "amber" as const, explanation: "Complete Client Profile and rerun diagnosis to evaluate this row." }
  ];
}

function LockedClientFitState() {
  return (
    <section className="pmri-card rounded-3xl p-6 md:p-8">
      <StatusBadge tone="amber">Client Fit locked</StatusBadge>
      <h2 className="pmri-heading-section mt-4 text-2xl text-pmri-text">Run profile-first diagnosis before Client Fit.</h2>
      <p className="mt-3 max-w-2xl text-sm leading-7 text-pmri-muted">
        Client Fit needs a completed Client Profile, Portfolio X-Ray, and Stress Test Lab evidence. Backend and CLI runs can still produce a missing-profile compatibility state, but the web journey asks for the profile first.
      </p>
      <div className="mt-6 flex flex-wrap gap-3">
        <Link href="/client-profile" className="pmri-focus pmri-primary-action rounded-full px-5 py-2.5 text-sm font-medium transition">Open Client Profile</Link>
        <Link href="/portfolio-input" className="pmri-focus rounded-full border border-pmri-border/60 bg-white/[0.025] px-5 py-2.5 text-sm font-medium text-pmri-text2 transition hover:border-pmri-blue/35 hover:text-pmri-text">Portfolio Input</Link>
      </div>
    </section>
  );
}

export default function ClientFitPage() {
  const { activeReview, hydrated } = useReviewState();
  const summary = activeReview?.reviewSummary?.clientFit;
  const provided = isProvided(summary);
  const ready = Boolean(activeReview?.runStatus === "completed" && activeReview.evidenceReady && summary);
  const rows = profileTargetRows(summary);
  const statusTone = summary?.status_tone ?? "amber";
  const siteExplanation = activeReview?.reviewSummary?.siteExplanation;
  const clientFitSummary = ready && provided ? summary : undefined;

  return (
    <div>
      <PageHeader
        kicker="Step 04 / Client Fit"
        title="Does this risk fit the provided profile..."
        description="A separate non-binding check of portfolio evidence against stated return, volatility, temporary-loss, and horizon limits."
        boundaryNote="Client Fit status is not Diagnostic Quality status and is not a decision action."
      >
        <StatusBadge tone={ready && provided ? statusTone : "amber"}>{ready ? (summary?.status_label ?? "Client Fit evidence") : "Evidence required"}</StatusBadge>
      </PageHeader>

      <SiteExplanationHierarchy bundle={siteExplanation} screen="client_fit" fallbackTitle="Client Fit explanation" />

      {!hydrated ? null : !clientFitSummary ? (
        <LockedClientFitState />
      ) : (
        <div className="space-y-6">
          <section className="pmri-card rounded-3xl p-5 md:p-6">
            <div className="flex flex-col gap-4 md:flex-row md:items-start md:justify-between">
              <div>
                <p className="pmri-label">Your stated profile</p>
                <h2 className="pmri-heading-section mt-2 text-2xl text-pmri-text">{fallbackText(clientFitSummary.profile_label, "Provided planning profile")}</h2>
                <p className="mt-2 max-w-3xl text-sm leading-7 text-pmri-muted">
                  Profile confidence/source quality: {fallbackText(clientFitSummary.source_quality_label, "Source quality not returned")}. This describes the profile input, not whether the portfolio is good or bad.
                </p>
              </div>
              <StatusBadge tone={statusTone}>{clientFitSummary.status_label ?? "Client Fit"}</StatusBadge>
            </div>
          </section>

          <section className="pmri-card overflow-hidden rounded-3xl">
            <div className="border-b border-pmri-border/45 p-5 md:p-6">
              <p className="pmri-label">Portfolio vs your limits</p>
              <h2 className="pmri-heading-section mt-2 text-2xl text-pmri-text">Target and limit checks</h2>
            </div>
            <div className="overflow-x-auto">
              <table className="w-full min-w-[760px] border-separate border-spacing-0 text-left text-sm">
                <thead className="bg-white/[0.018] text-xs font-medium tracking-[-0.005em] text-pmri-muted">
                  <tr>
                    <th scope="col" className="px-5 py-3">Dimension</th>
                    <th scope="col" className="px-5 py-3">Portfolio</th>
                    <th scope="col" className="px-5 py-3">Your target/limit</th>
                    <th scope="col" className="px-5 py-3">Status</th>
                  </tr>
                </thead>
                <tbody className="[&_tr+tr_td]:border-t [&_tr+tr_td]:border-pmri-border/35">
                  {rows.map((row) => (
                    <tr key={row.dimension_label}>
                      <td className="px-5 py-4 font-medium text-pmri-text">{row.dimension_label}</td>
                      <td className="px-5 py-4 text-pmri-text2">{fallbackText(row.portfolio_value_label, "Unavailable")}</td>
                      <td className="px-5 py-4 text-pmri-text2">{fallbackText(row.target_or_limit_label, "No target returned")}</td>
                      <td className="px-5 py-4">
                        <StatusBadge tone={row.status_tone}>{row.status_label}</StatusBadge>
                        {row.explanation ? <p className="mt-2 text-xs leading-5 text-pmri-muted">{row.explanation}</p> : null}
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          </section>

          <section className="grid gap-6 lg:grid-cols-2">
            <article className="pmri-card rounded-3xl p-5 md:p-6">
              <p className="pmri-label">What this means</p>
              <h2 className="pmri-heading-section mt-2 text-xl text-pmri-text">Separate fit from diagnosis</h2>
              <p className="mt-3 text-sm leading-7 text-pmri-text2">
                {fallbackText(clientFitSummary.main_explanation, "Client Fit compares the current portfolio evidence with the stated limits. Structural diagnosis and decision action remain separate checks.")}
              </p>
              <p className="mt-4 rounded-2xl border border-pmri-border/45 bg-white/[0.022] p-4 text-sm leading-7 text-pmri-muted">
                {fallbackText(clientFitSummary.decision_boundary, "This is decision support only. It is not a trade instruction and not a profile sign-off.")}
              </p>
            </article>

            <article className="pmri-card rounded-3xl p-5 md:p-6">
              <p className="pmri-label">Next best test</p>
              <h2 className="pmri-heading-section mt-2 text-xl text-pmri-text">Continue with one diagnostic hypothesis</h2>
              <p className="mt-3 text-sm leading-7 text-pmri-text2">
                {fallbackText(clientFitSummary.next_best_test, "Review the hypothesis page and test one candidate only if the diagnosis and Client Fit evidence justify a comparison.")}
              </p>
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
