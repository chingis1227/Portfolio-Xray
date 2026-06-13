import { formatStressPercent } from "./stressLabModel";
import type { StressScenarioDetail } from "./stressLabTypes";
import { ContributionBars } from "./ContributionBars";
import { HelpHint, StressSectionHeader } from "./stressLabUi";

export function LossContributionPanel({ scenario }: { scenario: StressScenarioDetail }) {
  return (
    <section id="loss-contribution" className="pmri-card rounded-3xl p-5 md:p-7">
      <StressSectionHeader
        eyebrow="Stress loss attribution"
        title="Loss contribution"
        body={`Selected scenario: ${scenario.displayName}. Risk contribution answers who drives normal portfolio risk. Loss contribution answers who actually loses money in this stress scenario.`}
      />
      <div className="mt-6 grid gap-5 lg:grid-cols-[1.2fr_0.8fr]">
        <div>
          <p className="mb-3 rounded-2xl border border-pmri-border/55 bg-black/10 p-3 text-xs leading-5 text-pmri-muted">
            Helped/hurt status is scenario-specific. An asset is counted as helped only when it has positive contribution in that scenario.
          </p>
          <ContributionBars
            rows={scenario.lossContributions}
            limit={6}
            emptyMessage="Asset-level loss contribution is unavailable for this scenario. The scenario result can still be reviewed at portfolio level."
          />
        </div>
        <aside className="rounded-2xl border border-pmri-border/55 bg-white/[0.024] p-5">
          <div className="flex items-center gap-2">
            <h3 className="text-base font-semibold text-pmri-text">Contribution summary</h3>
            <HelpHint label="How to read" text="Negative bars hurt the portfolio in the selected stress scenario. Positive bars helped offset losses in that same scenario." />
          </div>
          <dl className="mt-5 space-y-4">
            <div>
              <dt className="pmri-label">Selected scenario</dt>
              <dd className="mt-1 text-sm text-pmri-text2">{scenario.displayName}</dd>
            </div>
            <div>
              <dt className="pmri-label">Portfolio stress impact</dt>
              <dd className="data-figure mt-1 text-2xl text-pmri-text">
                {formatStressPercent(scenario.kind === "historical" ... scenario.drawdownPct ...... scenario.portfolioLossPct : scenario.portfolioLossPct)}
              </dd>
            </div>
            <div>
              <dt className="pmri-label">Assets that hurt in selected scenario</dt>
              <dd className="mt-1 text-sm leading-6 text-pmri-text2">
                {scenario.assetsHurt.length
                  ... scenario.assetsHurt.slice(0, 3).map((item) => `${item.ticker} ${formatStressPercent(item.value)}`).join(", ")
                  : "Unavailable"}
              </dd>
            </div>
            <div>
              <dt className="pmri-label">Assets that helped in selected scenario</dt>
              <dd className="mt-1 text-sm leading-6 text-pmri-text2">
                {scenario.assetsHelped.length
                  ... scenario.assetsHelped.slice(0, 3).map((item) => `${item.ticker} ${formatStressPercent(item.value, { signed: true })}`).join(", ")
                  : "No meaningful helped assets detected in this scenario."}
              </dd>
            </div>
          </dl>
        </aside>
      </div>
    </section>
  );
}
