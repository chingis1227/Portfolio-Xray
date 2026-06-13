import { StatusBadge } from "@/components/ui/StatusBadge";
import { formatStressPercent } from "./stressLabModel";
import type { HedgeGapSummary, StressLimitations, StressScenarioDetail } from "./stressLabTypes";

function joinTickers(rows: StressScenarioDetail["assetsHurt"], fallback: string) {
  const labels = rows.slice(0, 3).map((row) => row.ticker);
  return labels.length ... labels.join(", ") : fallback;
}

function dataConfidenceCopy({
  syntheticScenarios,
  historicalScenarios,
  limitations
}: {
  syntheticScenarios: StressScenarioDetail[];
  historicalScenarios: StressScenarioDetail[];
  limitations: StressLimitations;
}) {
  const syntheticAvailable = syntheticScenarios.filter((scenario) => scenario.availability === "available").length;
  const historicalAvailable = historicalScenarios.filter((scenario) => scenario.availability === "available").length;
  const limitedHistorical = historicalScenarios
    .filter((scenario) => scenario.availability !== "available")
    .map((scenario) => scenario.displayName);

  if (limitedHistorical.length) {
    return `Synthetic stress coverage is strong: ${syntheticAvailable} of ${syntheticScenarios.length} scenarios available; older historical replay is limited (${limitedHistorical.join(", ")}).`;
  }

  return `${limitations.evidenceQualityLabel}: ${syntheticAvailable} of ${syntheticScenarios.length} synthetic scenarios and ${historicalAvailable} of ${historicalScenarios.length} historical episodes are available.`;
}

export function MainStressDiagnosisPanel({
  worstScenario,
  hedgeGap,
  syntheticScenarios,
  historicalScenarios,
  limitations
}: {
  worstScenario: StressScenarioDetail;
  hedgeGap: HedgeGapSummary;
  syntheticScenarios: StressScenarioDetail[];
  historicalScenarios: StressScenarioDetail[];
  limitations: StressLimitations;
}) {
  const loss = formatStressPercent(worstScenario.portfolioLossPct);
  const offsetCoverage = formatStressPercent(hedgeGap.offsetCoverageRatio);
  const lossDrivers = joinTickers(worstScenario.assetsHurt, "Unavailable");

  return (
    <section id="stress-diagnosis" className="pmri-card rounded-3xl border-pmri-blue/18 bg-pmri-blue/[0.035] p-5 md:p-7">
      <div className="flex flex-col gap-4 lg:flex-row lg:items-start lg:justify-between">
        <div className="max-w-4xl">
          <p className="pmri-label">Answer first</p>
          <h2 className="pmri-heading-section mt-2 text-3xl text-pmri-text">Main Stress Diagnosis</h2>
          <p className="mt-4 max-w-3xl text-base leading-7 text-pmri-text2">
            The current portfolio’s weakest stress area is {hedgeGap.displayName}. The portfolio is estimated to lose{" "}
            <span className="font-semibold text-pmri-text">{loss}</span> in the worst synthetic scenario, while assets that helped in that scenario offset only{" "}
            <span className="font-semibold text-pmri-text">{offsetCoverage}</span> of losses from assets that hurt.
          </p>
        </div>
        <StatusBadge tone={hedgeGap.statusTone}>{hedgeGap.statusLabel}</StatusBadge>
      </div>

      <div className="mt-6 grid gap-3 md:grid-cols-2 xl:grid-cols-4">
        <article className="rounded-2xl border border-pmri-border/55 bg-black/10 p-4">
          <p className="pmri-label">Worst synthetic scenario</p>
          <p className="data-figure mt-2 text-xl text-pmri-text">{worstScenario.displayName}</p>
          <p className="mt-1 text-sm text-pmri-text2">{loss}</p>
        </article>
        <article className="rounded-2xl border border-pmri-border/55 bg-black/10 p-4">
          <p className="pmri-label">Main loss drivers</p>
          <p className="mt-2 text-lg font-semibold text-pmri-text">{lossDrivers}</p>
          <p className="mt-1 text-sm text-pmri-text2">Assets that hurt in worst scenario</p>
        </article>
        <article className="rounded-2xl border border-pmri-border/55 bg-black/10 p-4">
          <p className="pmri-label">Main hedge gap</p>
          <p className="mt-2 text-lg font-semibold text-pmri-text">{hedgeGap.displayName}</p>
          <p className="mt-1 text-sm text-pmri-text2">{offsetCoverage} offset coverage</p>
        </article>
        <article className="rounded-2xl border border-pmri-border/55 bg-black/10 p-4">
          <p className="pmri-label">Data confidence</p>
          <p className="mt-2 text-sm leading-6 text-pmri-text2">
            {dataConfidenceCopy({ syntheticScenarios, historicalScenarios, limitations })}
          </p>
        </article>
      </div>
    </section>
  );
}
