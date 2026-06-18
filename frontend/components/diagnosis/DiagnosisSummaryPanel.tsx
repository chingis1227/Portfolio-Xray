import type { Metric, SiteExplanationBundle } from "@/lib/types";
import type { XRaySummary } from "@/lib/reviewState";
import { buildDiagnosisPresentation } from "@/components/diagnosis/diagnosisPresentation";
import { DiagnosisHero } from "@/components/diagnosis/DiagnosisHero";
import { EvidenceStrip } from "@/components/diagnosis/EvidenceStrip";
import { DiagnosticCanvas } from "@/components/diagnosis/DiagnosticCanvas";
import { AdvancedDiagnostics } from "@/components/diagnosis/AdvancedDiagnostics";
import { StressLabCta } from "@/components/diagnosis/StressLabCta";
import { CaseFileTopCards } from "@/components/ui/CaseFileCards";

type DiagnosisSummaryPanelProps = {
  status: string;
  headline: string;
  evidenceQuality: string;
  nextStep: string;
  boundaryNote: string;
  drivers: string[];
  metrics: Metric[];
  xraySummary?: XRaySummary;
  siteExplanation?: SiteExplanationBundle;
};

export function DiagnosisSummaryPanel({
  headline,
  evidenceQuality,
  nextStep,
  boundaryNote,
  drivers,
  metrics,
  xraySummary,
  siteExplanation
}: DiagnosisSummaryPanelProps) {
  const { model, metricGroups, evidenceItems } = buildDiagnosisPresentation({
    headline,
    evidenceQuality,
    nextStep,
    boundaryNote,
    drivers,
    metrics,
    xraySummary,
    siteExplanation
  });

  return (
    <div className="space-y-3 md:space-y-4">
      <DiagnosisHero model={model} />
      <CaseFileTopCards
        cards={[
          {
            eyebrow: "Main diagnosis",
            title: model.mainFinding,
            value: evidenceItems[0]?.value,
            description: "This is the leading current-portfolio issue to understand before any candidate test.",
            tone: evidenceItems[0]?.tone
          },
          {
            eyebrow: "Why it matters",
            title: "Investment relevance",
            value: evidenceItems[2]?.value,
            description: model.whyItMatters,
            tone: evidenceItems[2]?.tone
          },
          {
            eyebrow: "Key evidence",
            title: evidenceItems[1]?.value ? String(evidenceItems[1].value) : "Evidence needs review",
            value: `Quality: ${model.dataCoverage}`,
            description: "Primary evidence is summarized here; professional metrics remain in the collapsed diagnostics section.",
            tone: model.dataCoverageTone
          }
        ]}
      />
      <EvidenceStrip items={evidenceItems} />
      <DiagnosticCanvas model={model} />
      <StressLabCta model={model} />
      <AdvancedDiagnostics model={model} metricGroups={metricGroups} xraySummary={xraySummary} />
    </div>
  );
}
