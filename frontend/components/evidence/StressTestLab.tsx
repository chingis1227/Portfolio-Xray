"use client";

import { useMemo, useState } from "react";
import type { ReactNode } from "react";
import { SiteExplanationHierarchy } from "@/components/explanation/SiteExplanationHierarchy";
import { StatusBadge } from "@/components/ui/StatusBadge";
import { MetricMatrix } from "@/components/ui/MetricMatrix";
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
  ["data-quality-drilldown", "Data quality"]
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

      <MetricMatrix
        title="Stress metrics by scenario relevance"
        description="Worst-scenario rows appear before supporting evidence. Missing values are shown as Unavailable rather than inferred."
        groups={[
          {
            title: "Stress vulnerability",
            description: "Current-portfolio stress facts, ordered by materiality.",
            rows: story.metrics.map((metric) => ({
              metric: metric.label,
              portfolioValue: metric.value,
              reference: metric.label === "Worst scenario" ? "Worst visible stress" : "Current portfolio",
              status: metric.tone === "red" || metric.tone === "amber" ? { label: metric.tone === "red" ? "Material" : "Limited", tone: metric.tone } : undefined,
              meaning: metric.detail,
              material: metric.tone === "red" || metric.tone === "amber"
            }))
          },
          {
            title: "Scenario evidence",
            description: "Worst-scenario loss drivers and offset behavior stay visible before deeper drill-downs.",
            rows: [
              {
                metric: "Main loss drivers",
                portfolioValue: selectedScenario.assetsHurt.slice(0, 3).map((row) => row.ticker).join(", ") || "Unavailable",
                reference: selectedScenario.displayName,
                status: selectedScenario.assetsHurt.length ? { label: "Material", tone: "red" } : undefined,
                meaning: selectedScenario.assetsHurt.length ? "Largest hurt positions in the selected stress scenario." : "Asset-level loss contribution is unavailable.",
                material: Boolean(selectedScenario.assetsHurt.length)
              },
              {
                metric: "Offset behavior",
                portfolioValue: model.hedgeGap.statusLabel,
                reference: model.hedgeGap.scenarioDisplayName,
                status: model.hedgeGap.statusTone === "red" || model.hedgeGap.statusTone === "amber" ? { label: model.hedgeGap.statusTone === "red" ? "Weak" : "Partial", tone: model.hedgeGap.statusTone } : undefined,
                meaning: model.hedgeGap.interpretation,
                material: model.hedgeGap.statusTone === "red" || model.hedgeGap.statusTone === "amber"
              }
            ]
          }
        ]}
      />

      <section className="pmri-card rounded-3xl p-5 md:p-6">
        <p className="pmri-label">Analytical canvas</p>
        <h2 className="pmri-heading-section mt-2 text-2xl text-pmri-text">Scenario contribution and protection behavior</h2>
        <p className="mt-2 max-w-3xl text-sm leading-6 text-pmri-muted">
          This canvas keeps the main loss drivers and offset behavior together. The scenario library and technical drill-downs remain below as secondary details.
        </p>
        <div className="mt-5 grid gap-4">
          <LossContributionPanel scenario={selectedScenario} />
          <HedgeGapAnalysisPanel hedgeGap={model.hedgeGap} />
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
          title="Factor attribution"
          summary="Factor-level loss and offset detail for the selected stress scenario."
        >
          <FactorStressAttributionPanel scenario={selectedScenario} />
        </DetailDisclosure>

        <DetailDisclosure
          id="data-quality-drilldown"
          title="Data quality"
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
