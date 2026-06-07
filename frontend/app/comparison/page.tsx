import { PageHeader } from "@/components/layout/PageHeader";
import { CandidateComparisonPanel } from "@/components/comparison/CandidateComparisonPanel";
import { TradeoffSummary } from "@/components/comparison/TradeoffSummary";
import { StatusBadge } from "@/components/ui/StatusBadge";
import data from "@/data/demo/current-vs-candidate-comparison.json";
import type { ComparisonMetric } from "@/lib/types";

const comparison = data as {
  candidateName: string;
  candidateBoundary: string;
  evidenceQuality: string;
  summary: string;
  metrics: ComparisonMetric[];
  improved: string[];
  worsened: string[];
};

export default function ComparisonPage() {
  return (
    <div>
      <PageHeader
        kicker="Step 05 / Comparison"
        title="Current vs candidate comparison"
        description="The interface forces balanced framing: what improved, what worsened, what stayed inconclusive, and what trade-off was created."
      >
        <StatusBadge tone="amber">Trade-off required</StatusBadge>
      </PageHeader>
      <div className="space-y-6">
        <TradeoffSummary
          improved={comparison.improved}
          worsened={comparison.worsened}
          evidenceQuality={comparison.evidenceQuality}
          boundary={comparison.candidateBoundary}
        />
        <CandidateComparisonPanel {...comparison} />
      </div>
    </div>
  );
}
