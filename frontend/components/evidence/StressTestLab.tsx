"use client";

import { useMemo, useState } from "react";
import type { StressLabModel } from "./stressLabTypes";
import { DataLimitationsPanel } from "./DataLimitationsPanel";
import { FactorStressAttributionPanel } from "./FactorStressAttributionPanel";
import { HedgeGapAnalysisPanel } from "./HedgeGapAnalysisPanel";
import { LossContributionPanel } from "./LossContributionPanel";
import { MainStressDiagnosisPanel } from "./MainStressDiagnosisPanel";
import { ScenarioLibraryPanel } from "./ScenarioLibraryPanel";
import { SelectedScenarioDetailPanel } from "./SelectedScenarioDetailPanel";
import { StressScorecardPanel } from "./StressScorecardPanel";
import { XRayStressConfirmationPanel } from "./XRayStressConfirmationPanel";

const sectionLinks = [
  ["stress-diagnosis", "Overview"],
  ["scenario-library", "Scenarios"],
  ["selected-scenario", "Scenario detail"],
  ["loss-contribution", "Loss contribution"],
  ["hedge-gap", "Hedge protection"],
  ["xray-confirmation", "Diagnosis confirmation"],
  ["data-quality", "Data quality"]
] as const;

export function StressTestLab({ model }: { model: StressLabModel }) {
  const [manualScenarioId, setManualScenarioId] = useState<string | null>(null);
  const allScenarios = useMemo(
    () => [...model.syntheticScenarios, ...model.historicalScenarios],
    [model.historicalScenarios, model.syntheticScenarios]
  );
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
              Stress Test Lab checks whether Diagnosis weaknesses show up under scenario evidence, then passes evidence into Hypothesis.
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

      <MainStressDiagnosisPanel
        worstScenario={worstSyntheticScenario}
        hedgeGap={model.hedgeGap}
        syntheticScenarios={model.syntheticScenarios}
        historicalScenarios={model.historicalScenarios}
        limitations={model.limitations}
      />
      <StressScorecardPanel items={model.scorecard} />
      <ScenarioLibraryPanel
        syntheticScenarios={model.syntheticScenarios}
        historicalScenarios={model.historicalScenarios}
        selectedScenarioId={selectedScenario.id}
        onSelectScenario={setManualScenarioId}
      />
      <SelectedScenarioDetailPanel
        scenario={selectedScenario}
        worstScenario={worstSyntheticScenario}
        selectedIsWorst={selectedIsWorst}
        onViewWorstScenario={viewWorstScenario}
      />
      <LossContributionPanel scenario={selectedScenario} />
      <FactorStressAttributionPanel scenario={selectedScenario} />
      <HedgeGapAnalysisPanel hedgeGap={model.hedgeGap} />
      <XRayStressConfirmationPanel confirmation={model.xrayConfirmation} />
      <DataLimitationsPanel
        limitations={model.limitations}
        syntheticScenarios={model.syntheticScenarios}
        historicalScenarios={model.historicalScenarios}
      />
    </div>
  );
}
