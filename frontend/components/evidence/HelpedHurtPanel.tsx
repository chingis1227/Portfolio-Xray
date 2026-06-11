import { StatusBadge } from "@/components/ui/StatusBadge";
import { formatStressPercent } from "./stressLabModel";
import type { ContributionRow, StressScenarioDetail } from "./stressLabTypes";
import { EmptyPanel, StressSectionHeader } from "./stressLabUi";

function AssetList({ rows, emptyMessage }: { rows: ContributionRow[]; emptyMessage: string }) {
  if (!rows.length) return <EmptyPanel>{emptyMessage}</EmptyPanel>;

  return (
    <div className="space-y-3">
      {rows.map((row) => (
        <div key={`${row.ticker}-${row.value}`} className="pmri-interactive-bar-row flex items-center justify-between gap-3 rounded-2xl border border-pmri-border/50 bg-white/[0.02] p-3">
          <div>
            <p className="text-sm font-semibold text-pmri-text">{row.ticker}</p>
            <p className="mt-1 text-xs text-pmri-muted">{row.status}</p>
          </div>
          <StatusBadge tone={row.value > 0 ? "green" : row.value < 0 ? "red" : "slate"}>
            {formatStressPercent(row.value, { signed: true })}
          </StatusBadge>
        </div>
      ))}
    </div>
  );
}

export function HelpedHurtPanel({ scenario }: { scenario: StressScenarioDetail }) {
  return (
    <section id="helped-hurt" className="pmri-card rounded-3xl p-5 md:p-7">
      <StressSectionHeader
        eyebrow="Internal compensators"
        title="Assets that helped or hurt in selected scenario"
        body="An asset is counted as helped only when it had positive contribution in the selected stress scenario."
        badge={scenario.displayName}
        badgeTone="slate"
      />
      <div className="mt-6 grid gap-4 lg:grid-cols-2">
        <article className="rounded-2xl border border-pmri-risk/18 bg-pmri-risk/[0.035] p-5">
          <div className="mb-4 flex items-center justify-between gap-3">
            <h3 className="text-base font-semibold text-pmri-text">Assets that hurt in selected scenario</h3>
            <StatusBadge tone="red">{scenario.assetsHurt.length ? `${scenario.assetsHurt.length} hurt` : "Unavailable"}</StatusBadge>
          </div>
          <AssetList rows={scenario.assetsHurt} emptyMessage="No hurt assets are available for this scenario." />
        </article>
        <article className="rounded-2xl border border-pmri-positive/18 bg-pmri-positive/[0.035] p-5">
          <div className="mb-4 flex items-center justify-between gap-3">
            <h3 className="text-base font-semibold text-pmri-text">Assets that helped in selected scenario</h3>
            <StatusBadge tone={scenario.assetsHelped.length ? "green" : "amber"}>
              {scenario.assetsHelped.length ? `${scenario.assetsHelped.length} helped` : "No offset"}
            </StatusBadge>
          </div>
          <AssetList rows={scenario.assetsHelped} emptyMessage="No meaningful helped assets detected in this scenario." />
        </article>
      </div>
    </section>
  );
}
