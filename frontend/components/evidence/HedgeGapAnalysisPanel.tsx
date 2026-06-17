import { StatusBadge } from "@/components/ui/StatusBadge";
import { formatStressPercent } from "./stressLabModel";
import type { HedgeGapSummary } from "./stressLabTypes";
import { ContributionBars } from "./ContributionBars";
import { HelpHint, StressSectionHeader } from "./stressLabUi";

export function HedgeGapAnalysisPanel({ hedgeGap }: { hedgeGap: HedgeGapSummary }) {
  const grossLossDisplay = hedgeGap.grossLossFromHurt === null
    ? "Unavailable"
    : formatStressPercent(-Math.abs(hedgeGap.grossLossFromHurt));
  const positiveDisplay = formatStressPercent(hedgeGap.positiveContributionFromHelped, { signed: true });
  const coverageDisplay = formatStressPercent(hedgeGap.offsetCoverageRatio);

  return (
    <section id="hedge-gap" className="pmri-card rounded-3xl p-5 md:p-7">
      <StressSectionHeader
        eyebrow="Main hedge gap scenario"
        title="Hedge protection"
        body="This checks whether assets that helped actually offset losses from assets that hurt during stress."
        badge={hedgeGap.statusLabel}
        badgeTone={hedgeGap.statusTone}
      />
      <div className="mt-6 grid gap-5 xl:grid-cols-[0.9fr_1.1fr]">
        <article className="rounded-2xl border border-pmri-border/55 bg-white/[0.024] p-5">
          <div className="flex items-start justify-between gap-3">
            <div>
              <p className="pmri-label">Main hedge gap</p>
              <h3 className="mt-1 text-xl font-semibold text-pmri-text">{hedgeGap.displayName}</h3>
              <p className="mt-1 text-sm text-pmri-muted">{hedgeGap.scenarioDisplayName}</p>
            </div>
            <StatusBadge tone={hedgeGap.statusTone}>{hedgeGap.statusLabel}</StatusBadge>
          </div>
          <div className="mt-6 grid gap-3 sm:grid-cols-3">
            <div className="rounded-2xl border border-pmri-risk/18 bg-pmri-risk/[0.035] p-4">
              <p className="pmri-label">Assets that hurt in main hedge gap scenario</p>
              <p className="data-figure mt-2 text-2xl text-pmri-text">{grossLossDisplay}</p>
            </div>
            <div className="rounded-2xl border border-pmri-blue/18 bg-pmri-blue/[0.035] p-4">
              <p className="pmri-label">Assets that helped in main hedge gap scenario</p>
              <p className="data-figure mt-2 text-2xl text-pmri-text">{positiveDisplay}</p>
            </div>
            <div className="rounded-2xl border border-pmri-border/55 bg-black/10 p-4">
              <div className="flex items-center gap-2">
                <p className="pmri-label">Offset coverage</p>
                <HelpHint label="Formula" text="Offset coverage equals positive contribution from helped assets divided by absolute gross loss from hurt assets." />
              </div>
              <p className="data-figure mt-2 text-2xl text-pmri-text">{coverageDisplay}</p>
            </div>
          </div>
          <div className="mt-5 rounded-2xl border border-pmri-border/55 bg-black/10 p-4">
            <p className="text-sm font-medium text-pmri-text">Compact formula</p>
            <p className="mt-2 text-sm leading-6 text-pmri-text2">
              Offset coverage = positive contribution from assets that helped / absolute gross loss from assets that hurt.
            </p>
            <p className="mt-2 text-sm leading-6 text-pmri-text2">
              In this review: {positiveDisplay} / {grossLossDisplay.replace("-", "")} = {coverageDisplay}.
            </p>
          </div>
          <p className="mt-5 text-sm leading-6 text-pmri-text2">{hedgeGap.interpretation}</p>
        </article>

        <article className="rounded-2xl border border-pmri-border/55 bg-white/[0.024] p-5">
          <div className="grid gap-5 lg:grid-cols-2">
            <div>
              <h3 className="mb-4 text-base font-semibold text-pmri-text">Assets that hurt in main hedge gap scenario</h3>
              <ContributionBars rows={hedgeGap.assetsHurt} emptyMessage="Hurt assets unavailable for the main hedge gap." />
            </div>
            <div>
              <h3 className="mb-4 text-base font-semibold text-pmri-text">Assets that helped in main hedge gap scenario</h3>
              <ContributionBars rows={hedgeGap.assetsHelped} emptyMessage="No meaningful helped assets detected for the main hedge gap." />
            </div>
          </div>
        </article>
      </div>
    </section>
  );
}
