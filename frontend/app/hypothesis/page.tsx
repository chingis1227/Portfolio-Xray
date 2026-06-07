import { PageHeader } from "@/components/layout/PageHeader";
import { HypothesisBuilderPanel } from "@/components/hypothesis/HypothesisBuilderPanel";
import { HypothesisCard } from "@/components/hypothesis/HypothesisCard";
import { StatusBadge } from "@/components/ui/StatusBadge";
import data from "@/data/demo/hypothesis-launchpad.json";
import type { Hypothesis } from "@/lib/types";

const launchpad = data as {
  selectedMethod: string;
  builderStatus: string;
  boundaryNote: string;
  hypotheses: Hypothesis[];
  constraints: string[];
};

export default function HypothesisPage() {
  return (
    <div>
      <PageHeader
        kicker="Step 04 / Hypothesis"
        title="Launch a candidate hypothesis test"
        description="A candidate is a testable hypothesis against the diagnosis. Equal Weight and Risk Parity are diagnostic benchmarks, not recommendations."
      >
        <StatusBadge tone="gold">Not a recommendation</StatusBadge>
      </PageHeader>
      <div className="grid gap-7 xl:grid-cols-[minmax(0,1fr)_380px]">
        <section className="grid gap-5 lg:grid-cols-2">
          {launchpad.hypotheses.map((hypothesis) => (
            <HypothesisCard
              key={hypothesis.id}
              hypothesis={hypothesis}
              isPrimary={launchpad.selectedMethod.includes(hypothesis.methodId)}
            />
          ))}
        </section>
        <HypothesisBuilderPanel
          selectedMethod={launchpad.selectedMethod}
          builderStatus={launchpad.builderStatus}
          boundaryNote={launchpad.boundaryNote}
          constraints={launchpad.constraints}
        />
      </div>
    </div>
  );
}
