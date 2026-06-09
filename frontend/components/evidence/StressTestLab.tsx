"use client";

import { useMemo, useState } from "react";
import { StatusBadge } from "@/components/ui/StatusBadge";
import type { StressLabModel } from "./stressLabTypes";
import { DataLimitationsPanel } from "./DataLimitationsPanel";
import { FactorStressAttributionPanel } from "./FactorStressAttributionPanel";
import { HedgeGapAnalysisPanel } from "./HedgeGapAnalysisPanel";
import { HelpedHurtPanel } from "./HelpedHurtPanel";
import { LossContributionPanel } from "./LossContributionPanel";
import { ScenarioLibraryPanel } from "./ScenarioLibraryPanel";
import { SelectedScenarioDetailPanel } from "./SelectedScenarioDetailPanel";
import { StressScorecardPanel } from "./StressScorecardPanel";
import { XRayStressConfirmationPanel } from "./XRayStressConfirmationPanel";

const sectionLinks = [
  ["stress-scorecard", "Scorecard"],
  ["scenario-library", "Scenarios"],
  ["selected-scenario", "Selected detail"],
  ["loss-contribution", "Loss contribution"],
  ["hedge-gap", "Hedge gap"],
  ["xray-confirmation", "X-Ray bridge"],
  ["data-limitations", "Data limits"]
] as const;

export function StressTestLab({ model }: { model: StressLabModel }) {
  const [selectedScenarioId, setSelectedScenarioId] = useState(model.selectedScenarioId);
  const allScenarios = useMemo(
    () => [...model.syntheticScenarios, ...model.historicalScenarios],
    [model.historicalScenarios, model.syntheticScenarios]
  );
  const selectedScenario = allScenarios.find((scenario) => scenario.id === selectedScenarioId)
    ?? allScenarios.find((scenario) => scenario.id === model.selectedScenarioId)
    ?? allScenarios[0];

  return (
    <div className="space-y-6">
      <section className="pmri-state-panel rounded-3xl p-4 md:p-5">
        <div className="flex flex-col gap-4 lg:flex-row lg:items-center lg:justify-between">
          <div>
            <div className="flex flex-wrap gap-2">
              <StatusBadge tone="blue">{model.headerStatusLabel}</StatusBadge>
              <StatusBadge tone="slate">Candidate not tested</StatusBadge>
              <StatusBadge tone="slate">No trade execution</StatusBadge>
            </div>
            <p className="mt-3 max-w-3xl text-sm leading-6 text-pmri-text2">
              Stress Test Lab exists after Diagnosis to test whether pre-stress weaknesses actually show up under market stress.
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

      <StressScorecardPanel items={model.scorecard} />
      <ScenarioLibraryPanel
        syntheticScenarios={model.syntheticScenarios}
        historicalScenarios={model.historicalScenarios}
        selectedScenarioId={selectedScenario.id}
        onSelectScenario={setSelectedScenarioId}
      />
      <SelectedScenarioDetailPanel scenario={selectedScenario} />
      <LossContributionPanel scenario={selectedScenario} />
      <HelpedHurtPanel scenario={selectedScenario} />
      <FactorStressAttributionPanel scenario={selectedScenario} />
      <HedgeGapAnalysisPanel hedgeGap={model.hedgeGap} />
      <XRayStressConfirmationPanel confirmation={model.xrayConfirmation} />
      <DataLimitationsPanel limitations={model.limitations} />
    </div>
  );
}
