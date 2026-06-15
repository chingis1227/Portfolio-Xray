import Link from "next/link";
import type { Metric, SiteExplanationBundle, StatusTone } from "@/lib/types";
import type { XRaySummary } from "@/lib/reviewState";
import { buildDiagnosisDisplayModel, type DiagnosisDisplayFact } from "@/lib/diagnosisDisplayModel";
import { riskSeverityLabel } from "@/lib/displayLabels";
import { StatusBadge } from "@/components/ui/StatusBadge";
import { MetricCard } from "@/components/ui/MetricCard";
import {
  CompositionPanel,
  FactorExposurePanel,
  HiddenRiskAlertsGrid,
  RiskBudgetPanel,
  WeaknessMapGrid
} from "@/components/diagnosis/PortfolioXRayBlocks";

type DiagnosisSummaryPanelProps = {
  status: string;
  headline: string;
  evidenceQuality: string;
  nextStep: string;
  boundaryNote: string;
  drivers: string[];
  metrics: Metric[];
  xraySummary?: XRaySummary;
  siteExplanation?: SiteExplanationBundle;
};

function toneLabel(tone: StatusTone) {
  if (tone === "green") return "Low risk";
  if (tone === "amber") return "Medium risk";
  if (tone === "red") return "High risk";
  return riskSeverityLabel(tone) === "Unavailable" ? "Review" : riskSeverityLabel(tone);
}

function FactDot() {
  return <span className="mt-2 h-1.5 w-1.5 shrink-0 rounded-full bg-pmri-blueSoft/70" aria-hidden="true" />;
}

function DiagnosisHero({ model }: { model: ReturnType<typeof buildDiagnosisDisplayModel> }) {
  return (
    <section className="pmri-card pmri-animated-border-panel pmri-section-reveal relative overflow-hidden rounded-3xl p-5 md:p-7">
      <div className="absolute -right-10 -top-12 h-52 w-52 rounded-full bg-pmri-blue/[0.045] blur-3xl" aria-hidden="true" />
      <div className="absolute bottom-0 left-0 h-px w-full bg-gradient-to-r from-transparent via-pmri-blueSoft/25 to-transparent" aria-hidden="true" />
      <div className="relative grid gap-7 lg:grid-cols-[1.1fr_0.9fr]">
        <div>
          <div className="flex flex-wrap gap-2">
            <StatusBadge tone="slate">Current portfolio review</StatusBadge>
            <StatusBadge tone={model.dataCoverageTone}>Data coverage: {model.dataCoverage}</StatusBadge>
            <StatusBadge tone="slate">Candidate not tested yet</StatusBadge>
          </div>
          <p className="pmri-label mt-7 text-pmri-text2">Main finding</p>
          <h2 className="mt-3 max-w-4xl text-3xl font-semibold leading-tight tracking-[-0.045em] text-pmri-text md:text-5xl">
            {model.mainFinding}
          </h2>
          <p className="mt-5 max-w-3xl text-base leading-7 text-pmri-text2">
            {model.whyItMatters}
          </p>
        </div>

        <aside className="rounded-3xl border border-pmri-border/60 bg-black/10 p-5 shadow-inner shadow-black/20">
          <p className="pmri-label text-pmri-text2">Evidence behind the finding</p>
          <div className="mt-4 space-y-3">
            {(model.primaryEvidence.length ? model.primaryEvidence : ["Primary evidence is unavailable in the compact review."]).map((item) => (
              <p key={item} className="flex gap-2 text-sm leading-6 text-pmri-text2">
                <FactDot />
                <span>{item}</span>
              </p>
            ))}
          </div>
          <div className="mt-5 rounded-2xl border border-pmri-border/50 bg-white/[0.02] p-4">
            <p className="pmri-label text-pmri-text2">Next safe step</p>
            <p className="mt-2 text-sm leading-6 text-pmri-text2">{model.nextStep}</p>
          </div>
        </aside>
      </div>

      <div className="relative mt-7 flex flex-wrap gap-3">
        <Link href="/evidence" className="pmri-focus pmri-primary-action rounded-full px-5 py-2.5 text-sm font-medium transition">
          Review Stress Lab evidence
        </Link>
        <Link href="/hypothesis" className="pmri-focus rounded-full border border-pmri-border bg-white/[0.035] px-5 py-2.5 text-sm font-medium text-pmri-text2 transition hover:border-pmri-blue/45 hover:text-pmri-text">
          Test one candidate hypothesis
        </Link>
      </div>
    </section>
  );
}

function WhatMattersRow({ fact }: { fact: DiagnosisDisplayFact }) {
  return (
    <div className="grid gap-3 border-b border-pmri-border/45 px-1 py-4 last:border-b-0 md:grid-cols-[0.9fr_0.9fr_1.3fr_auto] md:items-center">
      <p className="text-sm font-semibold text-pmri-text">{fact.label}</p>
      <p className="data-figure text-xl font-semibold text-pmri-text md:text-2xl">{fact.value}</p>
      <p className="text-sm leading-6 text-pmri-text2">{fact.note}</p>
      <div className="md:justify-self-end">
        <StatusBadge tone={fact.tone}>{toneLabel(fact.tone)}</StatusBadge>
      </div>
    </div>
  );
}

function WhatMattersFirst({ facts }: { facts: DiagnosisDisplayFact[] }) {
  return (
    <section id="summary" className="pmri-card pmri-section-reveal scroll-mt-28 rounded-3xl p-5 [--pmri-reveal-delay:60ms] md:p-6">
      <p className="pmri-label text-pmri-text2">Summary</p>
      <div className="mt-2 flex flex-col gap-2 md:flex-row md:items-end md:justify-between">
        <div>
          <h2 className="pmri-heading-section text-2xl text-pmri-text md:text-3xl">What matters first</h2>
          <p className="mt-2 max-w-3xl text-sm leading-6 text-pmri-text2">
            The diagnosis is reduced to the few facts that should guide the next review step.
          </p>
        </div>
      </div>
      <div className="mt-5 rounded-2xl border border-pmri-border/60 bg-white/[0.018] px-4 md:px-5">
        {facts.length ? facts.map((fact) => <WhatMattersRow key={fact.label} fact={fact} />) : (
          <p className="py-5 text-sm leading-6 text-pmri-text2">Decision-useful diagnosis facts are unavailable for this review.</p>
        )}
      </div>
    </section>
  );
}

function BehaviorCard({ fact }: { fact: DiagnosisDisplayFact }) {
  return (
    <article className="rounded-2xl border border-pmri-border/60 bg-white/[0.022] p-5">
      <p className="pmri-label text-pmri-text2">{fact.label}</p>
      <p className="data-figure mt-4 text-3xl font-semibold tracking-[-0.03em] text-pmri-text">{fact.value}</p>
      <p className="mt-3 text-sm leading-6 text-pmri-text2">{fact.note}</p>
    </article>
  );
}

function BehaviorSnapshot({ facts }: { facts: DiagnosisDisplayFact[] }) {
  return (
    <section id="behavior" className="pmri-card pmri-section-reveal scroll-mt-28 rounded-3xl p-5 [--pmri-reveal-delay:90ms] md:p-6">
      <div className="flex flex-col gap-3 md:flex-row md:items-end md:justify-between">
        <div>
          <p className="pmri-label text-pmri-text2">Historical behavior</p>
          <h2 className="pmri-heading-section mt-2 text-2xl text-pmri-text md:text-3xl">How the current portfolio behaved historically</h2>
          <p className="mt-2 max-w-3xl text-sm leading-6 text-pmri-text2">
            A compact read of growth, downside pain, and market dependence. Advanced diagnostics stay hidden until requested.
          </p>
        </div>
        <Link href="/evidence" className="pmri-focus inline-flex w-fit rounded-full border border-pmri-borderSoft/55 bg-white/[0.035] px-4 py-2 text-sm font-medium text-pmri-text2 transition hover:border-pmri-blue/45 hover:text-pmri-text">
          Review supporting evidence
        </Link>
      </div>
      <div className="mt-6 grid gap-4 md:grid-cols-3">
        {facts.length ? facts.map((fact) => <BehaviorCard key={fact.label} fact={fact} />) : (
          <div className="rounded-2xl border border-dashed border-pmri-borderSoft/55 bg-white/[0.018] p-5 text-sm leading-6 text-pmri-text2 md:col-span-3">
            Historical behavior metrics are unavailable for this review.
          </div>
        )}
      </div>
      {facts.length ? (
        <div className="mt-5 h-2 overflow-hidden rounded-full bg-white/[0.055]" aria-hidden="true">
          <div className="h-full w-2/3 rounded-full bg-gradient-to-r from-pmri-blueSoft/70 via-pmri-amber/65 to-pmri-risk/60" />
        </div>
      ) : null}
    </section>
  );
}

function AdvancedDiagnostics({ model, xraySummary }: { model: ReturnType<typeof buildDiagnosisDisplayModel>; xraySummary?: XRaySummary }) {
  return (
    <details id="advanced-diagnostics" className="pmri-card rounded-3xl p-5 md:p-6">
      <summary className="pmri-focus cursor-pointer list-none rounded-2xl border border-pmri-border/55 bg-white/[0.024] px-4 py-3 text-sm font-semibold text-pmri-text transition hover:border-pmri-blue/45">
        Advanced diagnostics and technical evidence
      </summary>
      <div className="mt-5 space-y-5">
        {model.advancedMetrics.length ? (
          <section>
            <h3 className="text-sm font-semibold text-pmri-text">Professional metrics</h3>
            <div className="mt-3 grid gap-3 sm:grid-cols-2 lg:grid-cols-3">
              {model.advancedMetrics.map((metric) => <MetricCard key={metric.label} metric={metric} />)}
            </div>
          </section>
        ) : null}

        {model.technicalEvidence.length ? (
          <section className="rounded-2xl border border-pmri-border/60 bg-white/[0.018] p-4">
            <h3 className="text-sm font-semibold text-pmri-text">Technical evidence</h3>
            <div className="mt-3 space-y-2">
              {model.technicalEvidence.map((item) => <p key={item} className="text-sm leading-6 text-pmri-text2">• {item}</p>)}
            </div>
          </section>
        ) : null}

        {model.limitations.length ? (
          <section className="rounded-2xl border border-pmri-border/60 bg-white/[0.018] p-4">
            <h3 className="text-sm font-semibold text-pmri-text">Data limitations to review</h3>
            <div className="mt-3 space-y-2">
              {model.limitations.map((item) => <p key={item} className="text-sm leading-6 text-pmri-text2">• {item}</p>)}
            </div>
          </section>
        ) : null}

        {xraySummary ? (
          <details className="rounded-2xl border border-pmri-border/60 bg-black/10 p-4">
            <summary className="pmri-focus cursor-pointer list-none rounded-xl text-sm font-semibold text-pmri-text2 transition hover:text-pmri-text">
              Full portfolio x-ray detail
            </summary>
            <div className="mt-5 space-y-5">
              <CompositionPanel xray={xraySummary} />
              <FactorExposurePanel xray={xraySummary} />
              <HiddenRiskAlertsGrid xray={xraySummary} />
              <RiskBudgetPanel xray={xraySummary} />
              <WeaknessMapGrid xray={xraySummary} />
            </div>
          </details>
        ) : null}
      </div>
    </details>
  );
}

export function DiagnosisSummaryPanel({
  headline,
  evidenceQuality,
  nextStep,
  boundaryNote,
  drivers,
  metrics,
  xraySummary,
  siteExplanation
}: DiagnosisSummaryPanelProps) {
  const model = buildDiagnosisDisplayModel({
    headline,
    evidenceQuality,
    nextStep,
    boundaryNote,
    drivers,
    metrics,
    xraySummary,
    siteExplanation
  });

  return (
    <div className="space-y-6">
      <DiagnosisHero model={model} />
      <WhatMattersFirst facts={model.whatMatters} />
      <BehaviorSnapshot facts={model.behaviorSnapshot} />
      <AdvancedDiagnostics model={model} xraySummary={xraySummary} />

      <section className="pmri-card rounded-3xl p-5 md:p-6">
        <div className="flex flex-col gap-4 md:flex-row md:items-center md:justify-between">
          <div>
            <p className="pmri-label">Decision boundary</p>
            <h2 className="pmri-heading-section mt-2 text-2xl text-pmri-text">Review evidence before testing a hypothesis</h2>
            <p className="mt-2 max-w-2xl text-sm leading-6 text-pmri-muted">{model.boundaryNote}</p>
          </div>
          <div className="flex flex-wrap gap-3">
            <Link href="/evidence" className="pmri-focus pmri-primary-action rounded-full px-5 py-2.5 text-sm font-medium transition">
              Review Stress Lab evidence
            </Link>
            <Link href="/hypothesis" className="pmri-focus rounded-full border border-pmri-border bg-white/[0.035] px-5 py-2.5 text-sm font-medium text-pmri-text2 transition hover:border-pmri-blue/45 hover:text-pmri-text">
              Test one candidate hypothesis
            </Link>
          </div>
        </div>
      </section>
    </div>
  );
}
