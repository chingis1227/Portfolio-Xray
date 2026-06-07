import { PageHeader } from "@/components/layout/PageHeader";
import { ClientReadyReportPreview } from "@/components/report/ClientReadyReportPreview";
import { StatusBadge } from "@/components/ui/StatusBadge";
import data from "@/data/demo/client-ready-report.json";

const report = data as {
  title: string;
  subtitle: string;
  sections: { title: string; body: string }[];
  monitoring: string;
  boundaryNote: string;
};

export default function ReportPage() {
  return (
    <div>
      <PageHeader
        kicker="Step 07 / Report"
        title="Client-ready report preview"
        description="A concise narrative that explains the decision-support evidence without turning it into advice, suitability review, or trading instruction."
      >
        <StatusBadge tone="blue">Preview only</StatusBadge>
      </PageHeader>
      <ClientReadyReportPreview {...report} />
    </div>
  );
}
