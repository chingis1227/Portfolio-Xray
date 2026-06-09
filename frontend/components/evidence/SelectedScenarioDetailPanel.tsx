import { StatusBadge } from "@/components/ui/StatusBadge";
import { formatStressPercent } from "./stressLabModel";
import type { StressScenarioDetail } from "./stressLabTypes";
import { ContributionBars } from "./ContributionBars";
import { HelpHint, StressSectionHeader } from "./stressLabUi";

export function SelectedScenarioDetailPanel({
  scenario
}: {
  scenario: StressScenarioDetail;
}) {
  const metricLabel = scenario.kind === "historical" ? "Historical drawdown" : "Portfolio loss";
  const metricValue = scenario.kind === "historical"
    ? formatStressPercent(scenario.drawdownPct ?? scenario.portfolioLossPct)
    : formatStressPercent(scenario.portfolioLossPct);
  const grossLoss = scenario.assetsHurt.reduce((sum, row) => sum + Math.abs(row.value), 0);
  const helped = scenario.assetsHelped.reduce((sum, row) => sum + row.value, 0);
  const offsetCoverage = grossLoss > 0 ? helped / grossLoss : null;
  const offsetStatus = offsetCoverage === null
    ? "Unavailable"
    : offsetCoverage === 0
      ? "No meaningful offset"
      : offsetCoverage < 0.25
        ? "Weak offset"
        : offsetCoverage < 0.6
          ? "Partial offset"
          : "Strong offset";
  const offsetTone = offsetStatus === "Strong offset" ? "green" : offsetStatus === "Partial offset" ? "amber" : offsetStatus === "Unavailable" ? "slate" : "red";

  return (
    <section id="selected-scenario" className="pmri-card rounded-3xl p-5 md:p-7">
      <StressSectionHeader
        eyebrow="Block 3.2"
        title={`Selected scenario: ${scenario.displayName}`}
        body="The selected scenario shows actual stress loss contribution, not normal risk contribution."
        badge={scenario.severityLabel}
        badgeTone={scenario.severityTone}
      />
      <div className="mt-6 grid gap-4 xl:grid-cols-[0.9fr_1.2fr_0.9fr]">
        <article className="rounded-2xl border border-pmri-border/55 bg-white/[0.024] p-5">
          <div className="flex items-center gap-2">
            <p className="pmri-label">{metricLabel}</p>
            <HelpHint
              label="Definition"
              text={scenario.kind === "historical" ? "Historical drawdown is the deepest replay loss during the episode." : "Portfolio loss is the estimated stress impact on the current portfolio."}
            />
          </div>
          <p className="data-figure mt-4 text-4xl font-medium text-pmri-text">{metricValue}</p>
          <div className="mt-4 flex flex-wrap gap-2">
            <StatusBadge tone={scenario.evidenceTone}>{scenario.evidenceQualityLabel}</StatusBadge>
            <StatusBadge tone="slate">{scenario.groupLabel}</StatusBadge>
          </div>
          <p className="mt-5 text-sm leading-6 text-pmri-text2">{scenario.interpretation}</p>
          {scenario.limitation ? (
            <p className="mt-4 rounded-2xl border border-pmri-amber/20 bg-pmri-amber/[0.055] p-3 text-xs leading-5 text-pmri-text2">
              {scenario.limitation}
            </p>
          ) : null}
        </article>

        <article className="rounded-2xl border border-pmri-border/55 bg-white/[0.024] p-5">
          <div className="flex items-center justify-between gap-3">
            <div>
              <p className="pmri-label">Asset contribution</p>
              <h3 className="mt-1 text-base font-semibold text-pmri-text">What actually lost or helped</h3>
            </div>
            <HelpHint label="Loss contribution" text="Loss contribution answers which assets lost money in this stress scenario." />
          </div>
          <div className="mt-5">
            <ContributionBars
              rows={scenario.lossContributions}
              limit={8}
              emptyMessage="Asset-level loss contribution is unavailable for this scenario."
            />
          </div>
        </article>

        <article className="rounded-2xl border border-pmri-border/55 bg-white/[0.024] p-5">
          <div className="flex items-center justify-between gap-3">
            <div>
              <p className="pmri-label">Hedge / offset summary</p>
              <h3 className="mt-1 text-base font-semibold text-pmri-text">Selected scenario offset</h3>
            </div>
            <StatusBadge tone={offsetTone}>{offsetStatus}</StatusBadge>
          </div>
          <p className="data-figure mt-4 text-3xl font-medium text-pmri-text">
            {formatStressPercent(offsetCoverage)}
          </p>
          <p className="mt-2 text-sm leading-6 text-pmri-text2">Offset coverage in {scenario.displayName}</p>
          <p className="mt-5 text-sm leading-6 text-pmri-text2">
            {offsetCoverage === null
              ? "Offset coverage is unavailable because asset-level helped and hurt contribution is incomplete for this scenario."
              : `Assets that helped contributed ${formatStressPercent(helped, { signed: true })} against ${formatStressPercent(-grossLoss)} from assets that hurt.`}
          </p>
        </article>
      </div>
    </section>
  );
}
