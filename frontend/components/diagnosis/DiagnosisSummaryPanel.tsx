import type { Metric, SiteExplanationBundle } from "@/lib/types";
import type { XRaySummary } from "@/lib/reviewState";
import { buildDiagnosisPresentation } from "@/components/diagnosis/diagnosisPresentation";
import { DiagnosisHero } from "@/components/diagnosis/DiagnosisHero";
import { EvidenceStrip } from "@/components/diagnosis/EvidenceStrip";
import { DiagnosticCanvas } from "@/components/diagnosis/DiagnosticCanvas";
import { AdvancedDiagnostics } from "@/components/diagnosis/AdvancedDiagnostics";
import { StressLabCta } from "@/components/diagnosis/StressLabCta";
import { TopUtilityHeader } from "@/components/ui/TopUtilityHeader";

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
      <TopUtilityHeader
        eyebrow="Current portfolio · diagnosis-first"
        title="Read the material issue, supporting evidence, next risk review, and safe handoff before any candidate work."
        items={[
          { label: "Scope", value: "Current only" },
          { label: "Evidence", value: model.dataCoverage, tone: model.dataCoverageTone },
          { label: "Next", value: "Stress Lab", tone: "blue" }
        ]}
      />
      <DiagnosisHero model={model} />
      <EvidenceStrip items={evidenceItems} />
      <DiagnosticCanvas model={model} />
      <StressLabCta model={model} />
      <AdvancedDiagnostics model={model} metricGroups={metricGroups} xraySummary={xraySummary} />
    </div>
  );
}
