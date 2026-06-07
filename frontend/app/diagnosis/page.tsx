import { PageHeader } from "@/components/layout/PageHeader";
import { DiagnosisSummaryPanel } from "@/components/diagnosis/DiagnosisSummaryPanel";
import { StatusBadge } from "@/components/ui/StatusBadge";
import data from "@/data/demo/diagnosis-summary.json";
import type { Metric } from "@/lib/types";

const diagnosis = data as {
  status: string;
  headline: string;
  evidenceQuality: string;
  nextStep: string;
  boundaryNote: string;
  drivers: string[];
  metrics: Metric[];
};

export default function DiagnosisPage() {
  return (
    <div>
      <PageHeader
        kicker="Step 02 / Diagnosis"
        title="Diagnosis summary before any candidate"
        description="The decision room first explains what appears wrong or fragile in the current portfolio. It does not jump to optimization."
      >
        <StatusBadge tone="gold">Diagnosis ready</StatusBadge>
      </PageHeader>
      <DiagnosisSummaryPanel {...diagnosis} />
    </div>
  );
}
