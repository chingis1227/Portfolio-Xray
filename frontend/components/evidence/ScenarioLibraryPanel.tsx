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
  const unavailable = scenario.availability !== "available";
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
      <div className="mt-4 min-h-5">
        {selected ? <span className="text-xs font-medium text-pmri-blueSoft">Selected</span> : null}
        {!selected && unavailable ? <StatusBadge tone={scenario.evidenceTone}>{scenario.evidenceQualityLabel}</StatusBadge> : null}
      </div>
      {unavailable ? (
        <p className="mt-3 text-xs leading-5 text-pmri-muted">
          Replay limited. No positions have usable direct history for this stress period.
        </p>
      ) : scenario.dataNote ? (
        <p className="mt-3 text-xs leading-5 text-pmri-muted">{scenario.dataNote}</p>
      ) : null}
    </button>
  );
}

function impactValue(scenario: StressScenarioDetail) {
  return scenario.kind === "historical" ? scenario.drawdownPct ?? scenario.portfolioLossPct : scenario.portfolioLossPct;
}

function rankByDamage(a: StressScenarioDetail, b: StressScenarioDetail) {
  const aValue = impactValue(a);
  const bValue = impactValue(b);
  if (aValue === null && bValue === null) return a.displayName.localeCompare(b.displayName);
  if (aValue === null) return 1;
  if (bValue === null) return -1;
  return aValue - bValue || a.displayName.localeCompare(b.displayName);
}

function ScenarioGroup({
  title,
  description,
  scenarios,
  selectedScenarioId,
  onSelectScenario
}: {
  title: string;
  description: string;
  scenarios: StressScenarioDetail[];
  selectedScenarioId: string;
  onSelectScenario: (scenarioId: string) => void;
}) {
  if (!scenarios.length) return null;

  return (
    <div>
      <div className="mb-3">
        <h3 className="text-sm font-semibold text-pmri-text">{title}</h3>
        <p className="mt-1 text-xs leading-5 text-pmri-muted">{description}</p>
      </div>
      <div className="grid gap-3 sm:grid-cols-2 xl:grid-cols-4">
        {scenarios.map((scenario) => (
          <ScenarioTile
            key={scenario.id}
            scenario={scenario}
            selected={scenario.id === selectedScenarioId}
            onSelect={() => onSelectScenario(scenario.id)}
          />
        ))}
      </div>
    </div>
  );
}

export function ScenarioLibraryPanel({
  syntheticScenarios,
  historicalScenarios,
  selectedScenarioId,
  onSelectScenario
}: ScenarioLibraryPanelProps) {
  const allScenarios = [...syntheticScenarios, ...historicalScenarios];
  const worstSynthetic = syntheticScenarios.find((scenario) => scenario.isWorst)
    ?? [...syntheticScenarios].sort(rankByDamage)[0];
  const worstHistorical = historicalScenarios.find((scenario) => scenario.isWorst && scenario.availability === "available")
    ?? historicalScenarios.filter((scenario) => scenario.availability === "available").sort(rankByDamage)[0];
  const mostDamagingIds = new Set([worstSynthetic?.id, worstHistorical?.id].filter(Boolean));
  const mostDamaging = allScenarios.filter((scenario) => mostDamagingIds.has(scenario.id)).sort(rankByDamage);
  const material = allScenarios
    .filter((scenario) => !mostDamagingIds.has(scenario.id) && scenario.availability === "available")
    .filter((scenario) => Math.abs(impactValue(scenario) ?? 0) >= 0.03)
    .sort(rankByDamage);
  const lessOrUnavailable = allScenarios
    .filter((scenario) => !mostDamagingIds.has(scenario.id) && !material.some((item) => item.id === scenario.id))
    .sort((a, b) => {
      if (a.availability !== b.availability) return a.availability === "available" ? -1 : 1;
      return rankByDamage(a, b);
    });

  return (
    <section id="scenario-library" className="pmri-card rounded-3xl p-5 md:p-7">
      <StressSectionHeader
        eyebrow="Scenario coverage"
        title="Scenario library"
        body="Scenarios are ranked by damage first, while synthetic shock versus historical episode remains visible on each card."
      />
      <div className="mt-6 space-y-6">
        <ScenarioGroup
          title="Most damaging scenarios"
          description="Start here: these scenarios produce the largest available synthetic loss or historical drawdown."
          scenarios={mostDamaging}
          selectedScenarioId={selectedScenarioId}
          onSelectScenario={onSelectScenario}
        />
        <ScenarioGroup
          title="Material stress areas"
          description="Meaningful losses that support the diagnosis but are not the single worst case."
          scenarios={material}
          selectedScenarioId={selectedScenarioId}
          onSelectScenario={onSelectScenario}
        />
        <ScenarioGroup
          title="Less damaging / unavailable"
          description="Lower-impact scenarios and historical episodes where replay is limited by direct holding history."
          scenarios={lessOrUnavailable}
          selectedScenarioId={selectedScenarioId}
          onSelectScenario={onSelectScenario}
        />
      </div>
    </section>
  );
}
