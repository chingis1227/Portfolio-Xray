import type { StressScenarioDetail } from "./stressLabTypes";
import { ContributionBars } from "./ContributionBars";
import { StressSectionHeader } from "./stressLabUi";

export function FactorStressAttributionPanel({ scenario }: { scenario: StressScenarioDetail }) {
  if (!scenario.factorAttribution.length) {
    return (
      <section id="factor-attribution" className="pmri-card rounded-3xl p-5 md:p-7">
        <StressSectionHeader
          eyebrow="Factor view"
          title="Factor stress attribution"
          body="Factor attribution unavailable for this stress run."
          badge="Unavailable"
          badgeTone="slate"
        />
      </section>
    );
  }

  return (
    <section id="factor-attribution" className="pmri-card rounded-3xl p-5 md:p-7">
      <StressSectionHeader
        eyebrow="Factor view"
        title="Factor stress attribution"
        body="This shows which macro and risk factors explain the selected stress loss."
        badge={scenario.displayName}
        badgeTone={scenario.severityTone}
      />
      <div className="mt-6">
        <ContributionBars
          rows={scenario.factorAttribution}
          emptyMessage="Factor attribution unavailable for this stress run."
        />
      </div>
    </section>
  );
}
