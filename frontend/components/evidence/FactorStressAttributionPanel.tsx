import type { StressScenarioDetail } from "./stressLabTypes";
import { ContributionBars } from "./ContributionBars";
import { StressSectionHeader } from "./stressLabUi";

export function FactorStressAttributionPanel({ scenario }: { scenario: StressScenarioDetail }) {
  if (!scenario.factorAttribution.length) {
    return (
      <section id="factor-attribution" className="pmri-card rounded-3xl p-5 md:p-7">
      <StressSectionHeader
          eyebrow="Selected scenario"
          title="Factor stress attribution"
          body="Factor attribution unavailable for this stress run."
        />
      </section>
    );
  }

  return (
    <section id="factor-attribution" className="pmri-card rounded-3xl p-5 md:p-7">
      <StressSectionHeader
        eyebrow="Selected scenario"
        title="Factor stress attribution"
        body={`Which macro and risk factors explain the selected stress loss in ${scenario.displayName}.`}
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
