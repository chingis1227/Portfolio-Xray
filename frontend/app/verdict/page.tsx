import { PageHeader } from "@/components/layout/PageHeader";
import { VerdictPanel } from "@/components/verdict/VerdictPanel";
import { StatusBadge } from "@/components/ui/StatusBadge";
import data from "@/data/demo/decision-verdict.json";
import type { Metric } from "@/lib/types";

const verdict = data as {
  state: string;
  headline: string;
  explanation: string;
  evidenceQuality: string;
  boundaryNote: string;
  keyEvidence: string[];
  monitoringTrigger: string;
  metrics: Metric[];
};

export default function VerdictPage() {
  return (
    <div>
      <PageHeader
        kicker="Step 06 / Verdict"
        title="Decision verdict"
        description="The verdict answers whether evidence is strong enough to support a decision. No-trade and evidence-insufficient are valid outcomes."
      >
        <StatusBadge tone="gold">Decision-support only</StatusBadge>
      </PageHeader>
      <VerdictPanel {...verdict} />
    </div>
  );
}
