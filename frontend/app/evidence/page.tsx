import { PageHeader } from "@/components/layout/PageHeader";
import { EvidenceCenter } from "@/components/evidence/EvidenceCenter";
import { StatusBadge } from "@/components/ui/StatusBadge";
import data from "@/data/demo/evidence-center.json";
import type { EvidenceItem, Metric } from "@/lib/types";

const evidence = data as {
  headline: string;
  quality: string;
  boundaryNote: string;
  items: EvidenceItem[];
  metrics: Metric[];
};

export default function EvidencePage() {
  return (
    <div>
      <PageHeader
        kicker="Step 03 / Evidence"
        title="Evidence Center"
        description="X-Ray, stress, classification, and input-quality signals are organized as decision evidence before any candidate is tested."
      >
        <StatusBadge tone="amber">Evidence first</StatusBadge>
      </PageHeader>
      <EvidenceCenter {...evidence} />
    </div>
  );
}
