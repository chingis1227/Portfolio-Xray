import { StatusBadge } from "@/components/ui/StatusBadge";
import { formatStressPercent } from "./stressLabModel";
import type { StressScenarioDetail } from "./stressLabTypes";
import { StressSectionHeader } from "./stressLabUi";

type ScenarioLibraryPanelProps = {
  syntheticScenarios: StressScenarioDetail[];
  historicalScenarios: StressScenarioDetail[];
  selectedScenarioId: string;
  onSelectScenario: (scenarioId: string) => void;
};

function ScenarioTile({
  scenario,
  selected,
  onSelect
}: {
  scenario: StressScenarioDetail;
  selected: boolean;
  onSelect: () => void;
}) {
  const metric = scenario.kind === "historical"
    ? scenario.drawdownPct !== null
      ? `Drawdown: ${formatStressPercent(scenario.drawdownPct)}`
      : "Replay limited"
    : scenario.portfolioLossPct !== null
      ? `Loss: ${formatStressPercent(scenario.portfolioLossPct)}`
      : "Unavailable";

  return (
    <button
      type="button"
      onClick={onSelect}
      aria-pressed={selected}
      className={`pmri-focus pmri-hover-panel min-h-[10rem] rounded-2xl border p-4 text-left transition ${
        selected
          ? "border-pmri-blue/48 bg-pmri-blue/[0.075]"
          : "border-pmri-border/60 bg-white/[0.024]"
      }`}
    >
      <div className="flex items-start justify-between gap-3">
        <div className="min-w-0">
          <p className="text-sm font-semibold text-pmri-text">{scenario.displayName}</p>
          <p className="mt-1 text-xs text-pmri-muted">{scenario.groupLabel}</p>
        </div>
        <StatusBadge tone={scenario.severityTone}>{scenario.severityLabel}</StatusBadge>
      </div>
      <p className="data-figure mt-5 text-lg font-medium text-pmri-text2">{metric}</p>
      <div className="mt-4 flex flex-wrap gap-2">
        <StatusBadge tone={scenario.evidenceTone}>{scenario.evidenceQualityLabel}</StatusBadge>
        {selected ? <StatusBadge tone="blue">Selected</StatusBadge> : null}
      </div>
      {scenario.dataNote ? <p className="mt-3 text-xs leading-5 text-pmri-muted">{scenario.dataNote}</p> : null}
    </button>
  );
}

export function ScenarioLibraryPanel({
  syntheticScenarios,
  historicalScenarios,
  selectedScenarioId,
  onSelectScenario
}: ScenarioLibraryPanelProps) {
  return (
    <section id="scenario-library" className="pmri-card rounded-3xl p-5 md:p-7">
      <StressSectionHeader
        eyebrow="Block 3.1"
        title="Scenario Library"
        body="Synthetic shocks and historical episodes are shown together so the stress coverage is visible before interpretation."
        badge="Supporting evidence"
        badgeTone="slate"
      />
      <div className="mt-6 space-y-6">
        <div>
          <div className="mb-3 flex items-center justify-between gap-3">
            <h3 className="text-sm font-semibold text-pmri-text">Synthetic shocks</h3>
            <p className="text-xs text-pmri-muted">{syntheticScenarios.length} scenarios</p>
          </div>
          <div className="grid gap-3 sm:grid-cols-2 xl:grid-cols-4">
            {syntheticScenarios.map((scenario) => (
              <ScenarioTile
                key={scenario.id}
                scenario={scenario}
                selected={scenario.id === selectedScenarioId}
                onSelect={() => onSelectScenario(scenario.id)}
              />
            ))}
          </div>
        </div>
        <div>
          <div className="mb-3 flex items-center justify-between gap-3">
            <h3 className="text-sm font-semibold text-pmri-text">Historical episodes</h3>
            <p className="text-xs text-pmri-muted">{historicalScenarios.length} episodes</p>
          </div>
          <div className="grid gap-3 sm:grid-cols-2 xl:grid-cols-5">
            {historicalScenarios.map((scenario) => (
              <ScenarioTile
                key={scenario.id}
                scenario={scenario}
                selected={scenario.id === selectedScenarioId}
                onSelect={() => onSelectScenario(scenario.id)}
              />
            ))}
          </div>
        </div>
      </div>
    </section>
  );
}
