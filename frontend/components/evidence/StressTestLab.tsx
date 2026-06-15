"use client";

import { useMemo, useState } from "react";
import type { ReactNode } from "react";
import { SiteExplanationHierarchy } from "@/components/explanation/SiteExplanationHierarchy";
import { StatusBadge } from "@/components/ui/StatusBadge";
import type { SiteExplanationBundle } from "@/lib/types";
import type { StressLabModel } from "./stressLabTypes";
import { DataLimitationsPanel } from "./DataLimitationsPanel";
import { FactorStressAttributionPanel } from "./FactorStressAttributionPanel";
import { HedgeGapAnalysisPanel } from "./HedgeGapAnalysisPanel";
import { LossContributionPanel } from "./LossContributionPanel";
import { ScenarioLibraryPanel } from "./ScenarioLibraryPanel";
import { SelectedScenarioDetailPanel } from "./SelectedScenarioDetailPanel";
import { XRayStressConfirmationPanel } from "./XRayStressConfirmationPanel";
import { buildStressStoryViewModel, type StressStoryFact, type StressStoryMetric } from "./stressStoryModel";

const sectionLinks = [
  ["stress-story", "Answer"],
  ["stress-details", "Details"],
  ["scenario-drilldown", "Scenarios"],
  ["loss-drivers-drilldown", "Loss drivers"],
  ["hedge-protection-drilldown", "Protection"],
  ["evidence-quality-drilldown", "Evidence quality"]
] as const;

function StoryMetricCard({ metric }: { metric: StressStoryMetric }) {
  return (
    <article className="rounded-2xl border border-pmri-border/60 bg-black/10 p-4">
      <div className="flex items-start justify-between gap-3">
        <p className="pmri-label">{metric.label}</p>
        {metric.tone === "red" || metric.tone === "amber" ? (
          <span className={`mt-1 h-2 w-2 shrink-0 rounded-full ${metric.tone === "red" ? "bg-pmri-risk" : "bg-pmri-amber"}`} />
        ) : null}
      </div>
      <p className="data-figure mt-3 text-xl font-medium text-pmri-text">{metric.value}</p>
      <p className="mt-2 text-sm leading-6 text-pmri-text2">{metric.detail}</p>
    </article>
  );
}

function StoryFactCard({ fact }: { fact: StressStoryFact }) {
  return (
    <article className="rounded-2xl border border-pmri-border/55 bg-white/[0.024] p-4">
      <p className="pmri-label">{fact.label}</p>
      <p className="mt-2 text-base font-semibold text-pmri-text">{fact.value}</p>
      <p className="mt-2 text-sm leading-6 text-pmri-muted">{fact.detail}</p>
    </article>
  );
}

function DetailDisclosure({
  id,
  title,
  summary,
  children
}: {
  id?: string;
  title: string;
  summary: string;
  children: ReactNode;
}) {
  return (
    <details id={id} className="group rounded-3xl border border-pmri-border/55 bg-pmri-secondary/35 p-4 shadow-decision">
      <summary className="pmri-focus flex cursor-pointer list-none items-center justify-between gap-4 rounded-2xl px-1 py-1">
        <div>
          <h3 className="text-base font-semibold text-pmri-text">{title}</h3>
          <p className="mt-1 text-sm leading-6 text-pmri-muted">{summary}</p>
        </div>
        <span className="rounded-full border border-pmri-border/70 px-3 py-1 text-xs font-medium text-pmri-text2 transition group-open:border-pmri-blue/50 group-open:text-pmri-blueSoft">
          Open
        </span>
      </summary>
      <div className="mt-4">{children}</div>
    </details>
  );
}

export function StressTestLab({ model, siteExplanation }: { model: StressLabModel; siteExplanation?: SiteExplanationBundle }) {
  const [manualScenarioId, setManualScenarioId] = useState<string | null>(null);
  const allScenarios = useMemo(
    () => [...model.syntheticScenarios, ...model.historicalScenarios],
    [model.historicalScenarios, model.syntheticScenarios]
  );
  const story = useMemo(() => buildStressStoryViewModel(model, siteExplanation), [model, siteExplanation]);
  const worstSyntheticScenario = useMemo(() => {
    const available = model.syntheticScenarios.filter((scenario) => scenario.availability === "available");
    return available.find((scenario) => scenario.isWorst)
      ?? [...available].sort((a, b) => (a.portfolioLossPct ?? 0) - (b.portfolioLossPct ?? 0))[0]
      ?? model.syntheticScenarios.find((scenario) => scenario.isWorst)
      ?? model.syntheticScenarios[0]
      ?? allScenarios[0];
  }, [allScenarios, model.syntheticScenarios]);
  const selectedScenarioId = manualScenarioId ?? worstSyntheticScenario.id;
  const selectedScenario = allScenarios.find((scenario) => scenario.id === selectedScenarioId)
    ?? worstSyntheticScenario
    ?? allScenarios[0];
  const selectedIsWorst = selectedScenario.id === worstSyntheticScenario.id;
  const viewWorstScenario = () => setManualScenarioId(null);

  return (
    <div className="space-y-6">
      <section className="pmri-state-panel rounded-3xl p-4 md:p-5">
        <div className="flex flex-col gap-4 lg:flex-row lg:items-center lg:justify-between">
          <div>
            <p className="pmri-label">Stress review path</p>
            <p className="mt-2 max-w-3xl text-sm leading-6 text-pmri-text2">
              Stress Test Lab turns scenario evidence into one current-portfolio answer first, with deeper evidence kept below.
            </p>
          </div>
          <nav className="flex flex-wrap gap-2" aria-label="Stress Test Lab sections">
            {sectionLinks.map(([href, label]) => (
              <a
                key={href}
                href={`#${href}`}
                className="pmri-focus pmri-section-nav-link rounded-full border border-pmri-border/70 bg-white/[0.025] px-3 py-1.5 text-xs font-medium text-pmri-text2 hover:text-pmri-text"
              >
                {label}
              </a>
            ))}
          </nav>
        </div>
      </section>

      <section id="stress-story" className="pmri-card overflow-hidden rounded-3xl border-pmri-border/70 p-0">
        <div className="border-b border-pmri-border/55 bg-[radial-gradient(circle_at_top_left,rgba(215,122,122,0.13),transparent_34%),linear-gradient(135deg,rgba(255,255,255,0.035),transparent)] p-5 md:p-8">
          <div className="flex flex-col gap-5 lg:flex-row lg:items-start lg:justify-between">
            <div className="max-w-4xl">
              <p className="pmri-label text-pmri-blueSoft">{story.eyebrow}</p>
              <h2 className="pmri-heading-section mt-3 text-3xl text-pmri-text md:text-4xl">{story.title}</h2>
              <p className="mt-4 max-w-3xl text-base leading-8 text-pmri-text2 md:text-lg">
                {story.answer}
              </p>
            </div>
            <div className="flex flex-wrap gap-2 lg:justify-end">
              <StatusBadge tone={story.statusTone}>{story.statusLabel}</StatusBadge>
              <StatusBadge tone={story.confidenceTone}>{story.confidenceLabel}</StatusBadge>
            </div>
          </div>

          <div className="mt-7 grid gap-3 md:grid-cols-2 xl:grid-cols-4">
            {story.metrics.map((metric) => (
              <StoryMetricCard key={metric.label} metric={metric} />
            ))}
          </div>
        </div>

        <div className="grid gap-5 p-5 md:p-7 xl:grid-cols-[1.15fr_0.85fr]">
          <div>
            <p className="pmri-label">Supporting facts</p>
            <div className="mt-3 grid gap-3 md:grid-cols-3">
              {story.facts.map((fact) => (
                <StoryFactCard key={fact.label} fact={fact} />
              ))}
            </div>
          </div>
          <aside className="rounded-2xl border border-pmri-border/55 bg-black/10 p-5">
            <p className="pmri-label">What this means</p>
            <p className="mt-3 text-sm leading-7 text-pmri-text2">{story.whatThisMeans}</p>
            <p className="mt-4 rounded-2xl border border-pmri-border/55 bg-white/[0.024] p-3 text-xs leading-5 text-pmri-muted">
              {story.confidenceDetail}
            </p>
          </aside>
        </div>
      </section>

      <section id="stress-details" className="space-y-4">
        <div className="px-1">
          <p className="pmri-label">Explore details</p>
          <h2 className="pmri-heading-section mt-2 text-2xl text-pmri-text">Stress evidence drill-down</h2>
          <p className="mt-2 max-w-3xl text-sm leading-6 text-pmri-muted">
            Detailed scenarios and technical evidence are available when needed, but they stay behind the main answer.
          </p>
        </div>

        <DetailDisclosure
          id="scenario-drilldown"
          title="Scenarios"
          summary="Synthetic shocks and historical episodes, ranked by damage and availability."
        >
          <ScenarioLibraryPanel
            syntheticScenarios={model.syntheticScenarios}
            historicalScenarios={model.historicalScenarios}
            selectedScenarioId={selectedScenario.id}
            onSelectScenario={setManualScenarioId}
          />
          <div className="mt-4">
            <SelectedScenarioDetailPanel
              scenario={selectedScenario}
              worstScenario={worstSyntheticScenario}
              selectedIsWorst={selectedIsWorst}
              onViewWorstScenario={viewWorstScenario}
            />
          </div>
        </DetailDisclosure>

        <DetailDisclosure
          id="loss-drivers-drilldown"
          title="Loss drivers"
          summary="Assets and factors that hurt or helped in the selected stress scenario."
        >
          <LossContributionPanel scenario={selectedScenario} />
          <div className="mt-4">
            <FactorStressAttributionPanel scenario={selectedScenario} />
          </div>
        </DetailDisclosure>

        <DetailDisclosure
          id="hedge-protection-drilldown"
          title="Hedge protection"
          summary="How much helped assets offset losses from hurt assets."
        >
          <HedgeGapAnalysisPanel hedgeGap={model.hedgeGap} />
        </DetailDisclosure>

        <DetailDisclosure
          id="evidence-quality-drilldown"
          title="Evidence quality"
          summary="Coverage, historical replay limitations, and diagnosis confirmation detail."
        >
          <DataLimitationsPanel
            limitations={model.limitations}
            syntheticScenarios={model.syntheticScenarios}
            historicalScenarios={model.historicalScenarios}
          />
          <div className="mt-4">
            <XRayStressConfirmationPanel confirmation={model.xrayConfirmation} />
          </div>
        </DetailDisclosure>

        {story.evidenceTraceCount ? (
          <DetailDisclosure
            title="Evidence trace"
            summary="Deterministic explanation text used for auditability, hidden from the primary stress answer."
          >
            <SiteExplanationHierarchy
              bundle={siteExplanation}
              screen="evidence"
              fallbackTitle="Stress evidence trace"
            />
          </DetailDisclosure>
        ) : null}
      </section>
    </div>
  );
}
