import Link from "next/link";
import type { Metric, SiteExplanationBundle, StatusTone } from "@/lib/types";
import type { XRaySummary } from "@/lib/reviewState";
import { buildDiagnosisDisplayModel, type DiagnosisDisplayFact } from "@/lib/diagnosisDisplayModel";
import { riskSeverityLabel } from "@/lib/displayLabels";
import { MetricCard } from "@/components/ui/MetricCard";
import { EvidenceSummary, type EvidenceSummaryItem } from "@/components/ui/EvidenceSummary";
import { MetricMatrix, type MetricMatrixGroup, type MetricMatrixRow } from "@/components/ui/MetricMatrix";
import { ScoreIndicator } from "@/components/ui/ScoreIndicator";
import { VerdictHero } from "@/components/ui/VerdictHero";
import {
  CompositionPanel,
  FactorExposurePanel,
  HiddenRiskAlertsGrid,
  RiskBudgetPanel,
  WeaknessMapGrid
} from "@/components/diagnosis/PortfolioXRayBlocks";

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

function toneLabel(tone: StatusTone) {
  if (tone === "green") return "Aligned";
  if (tone === "amber") return "Medium risk";
  if (tone === "red") return "High risk";
  return riskSeverityLabel(tone) === "Unavailable" ? "Review" : riskSeverityLabel(tone);
}

function DiagnosisHero({ model }: { model: ReturnType<typeof buildDiagnosisDisplayModel> }) {
  return (
    <VerdictHero
      stepContext="Step 02 of 8 - Portfolio Diagnosis"
      headline={model.mainFinding}
      interpretation={model.whyItMatters}
      facts={[
        { label: "Evidence quality", value: `${model.dataCoverage} diagnostic evidence.` },
        { label: "Next review step", value: model.nextStep }
      ]}
      actions={(
        <>
          <Link href="/evidence" className="pmri-focus pmri-primary-action rounded-full px-5 py-2.5 text-sm font-medium transition">
            Review Stress Lab evidence
          </Link>
          <Link href="/hypothesis" className="pmri-focus rounded-full border border-pmri-border bg-white/[0.035] px-5 py-2.5 text-sm font-medium text-pmri-text2 transition hover:border-pmri-blue/45 hover:text-pmri-text">
            Test one candidate hypothesis
          </Link>
        </>
      )}
    />
  );
}

function evidenceSummaryItems(model: ReturnType<typeof buildDiagnosisDisplayModel>): EvidenceSummaryItem[] {
  const primaryIssue = model.whatMatters.find((fact) => fact.tone === "red" || fact.tone === "amber") ?? model.whatMatters[0];
  const mainDrivers = model.primaryEvidence.length ? model.primaryEvidence.join(" ") : "Unavailable in the compact review.";
  return [
    {
      label: "Primary issue",
      value: primaryIssue ? `${primaryIssue.label}: ${primaryIssue.value}` : "Unavailable",
      tone: primaryIssue?.tone ?? "slate"
    },
    {
      label: "Severity",
      value: primaryIssue ? toneLabel(primaryIssue.tone) : "Unavailable",
      tone: primaryIssue?.tone ?? "slate"
    },
    {
      label: "Drivers",
      value: mainDrivers,
      tone: "slate"
    },
    {
      label: "Evidence quality",
      value: `${model.dataCoverage} diagnostic evidence`,
      tone: model.dataCoverageTone
    }
  ];
}

function rowStatus(tone: StatusTone): { label: string; tone: StatusTone } | undefined {
  if (tone === "red") return { label: "Material issue", tone };
  if (tone === "amber") return { label: "Watch", tone };
  if (tone === "slate" || tone === "gold" || tone === "blue" || tone === "green") return { label: "Context", tone: "slate" };
  return undefined;
}

function factRow(fact: DiagnosisDisplayFact, reference: string): MetricMatrixRow {
  return {
    metric: fact.label,
    portfolioValue: fact.value,
    reference,
    status: rowStatus(fact.tone),
    meaning: fact.note,
    material: fact.tone === "red" || fact.tone === "amber"
  };
}

function metricRow(metric: Metric): MetricMatrixRow {
  const scoreMatch = typeof metric.detail === "string" ? metric.detail.match(/^Score\s+(\d+(?:\.\d+)?)\/100$/i) : null;
  return {
    metric: metric.label,
    portfolioValue: metric.value,
    reference: "Diagnostic reference",
    status: metric.tone ? rowStatus(metric.tone) : undefined,
    meaning: scoreMatch ? <ScoreIndicator score={Number(scoreMatch[1])} tone={metric.tone ?? "slate"} /> : metric.detail ?? "Supporting diagnostic metric.",
    material: metric.tone === "red" || metric.tone === "amber"
  };
}

function diagnosisMetricGroups(model: ReturnType<typeof buildDiagnosisDisplayModel>): MetricMatrixGroup[] {
  const riskLabels = new Set(["Downside pain", "Main weakness", "Pain", "Risk level", "Market dependence"]);
  const structureLabels = new Set(["Concentration", "Main exposure"]);
  const riskRows = [
    ...model.whatMatters.filter((fact) => riskLabels.has(fact.label)).map((fact) => factRow(fact, "Review vs stress and drawdown tolerance")),
    ...model.behaviorSnapshot.filter((fact) => riskLabels.has(fact.label)).map((fact) => factRow(fact, "Historical diagnostic window"))
  ];
  const structureRows = model.whatMatters
    .filter((fact) => structureLabels.has(fact.label))
    .map((fact) => factRow(fact, "Current portfolio composition"));
  const evidenceRows: MetricMatrixRow[] = [
    {
      metric: "Evidence quality",
      portfolioValue: model.dataCoverage,
      reference: "Strong / Moderate / Limited / Unavailable",
      status: rowStatus(model.dataCoverageTone),
      meaning: model.dataCoverage === "Limited" ? "Read results with caution and review omissions." : "Shows how much support exists for the diagnosis.",
      material: model.dataCoverageTone === "amber"
    }
  ];
  const secondaryRows = [
    ...model.behaviorSnapshot.filter((fact) => !riskLabels.has(fact.label)).map((fact) => factRow(fact, "Historical diagnostic window")),
    ...model.advancedMetrics.slice(0, 4).map(metricRow)
  ];

  return [
    { title: "Risk pressure", description: "Downside, stress-adjacent, and sensitivity metrics.", rows: riskRows },
    { title: "Portfolio structure", description: "Concentration and dominant exposure context.", rows: structureRows },
    { title: "Evidence quality", description: "Data availability and confidence boundaries.", rows: evidenceRows },
    { title: "Secondary observations", description: "Useful supporting metrics that should not dominate the first read.", rows: secondaryRows }
  ].map((group) => ({
    ...group,
    rows: group.rows.length ? group.rows : [{
      metric: "Unavailable",
      portfolioValue: "Unavailable",
      reference: "Unavailable",
      status: { label: "Unavailable", tone: "slate" as StatusTone },
      meaning: "This group has no compact metric rows for the active review."
    }]
  }));
}

function AdvancedDiagnostics({ model, xraySummary }: { model: ReturnType<typeof buildDiagnosisDisplayModel>; xraySummary?: XRaySummary }) {
  return (
    <details id="advanced-diagnostics" className="pmri-card rounded-3xl p-5 md:p-6">
      <summary className="pmri-focus cursor-pointer list-none rounded-2xl border border-pmri-border/55 bg-white/[0.024] px-4 py-3 text-sm font-semibold text-pmri-text transition hover:border-pmri-blue/45">
        Advanced diagnostics
      </summary>
      <div className="mt-5 space-y-5">
        {model.advancedMetrics.length ? (
          <section>
            <h3 className="text-sm font-semibold text-pmri-text">Professional metrics</h3>
            <div className="mt-3 grid gap-3 sm:grid-cols-2 lg:grid-cols-3">
              {model.advancedMetrics.map((metric) => <MetricCard key={metric.label} metric={metric} />)}
            </div>
          </section>
        ) : null}

        {xraySummary ? (
          <details className="rounded-2xl border border-pmri-border/60 bg-black/10 p-4">
            <summary className="pmri-focus cursor-pointer list-none rounded-xl text-sm font-semibold text-pmri-text2 transition hover:text-pmri-text">
              Full portfolio x-ray detail
            </summary>
            <div className="mt-5 space-y-5">
              <CompositionPanel xray={xraySummary} />
              <FactorExposurePanel xray={xraySummary} />
              <HiddenRiskAlertsGrid xray={xraySummary} />
              <RiskBudgetPanel xray={xraySummary} />
              <WeaknessMapGrid xray={xraySummary} />
            </div>
          </details>
        ) : null}
      </div>
    </details>
  );
}

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
  const model = buildDiagnosisDisplayModel({
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
    <div className="space-y-6">
      <DiagnosisHero model={model} />
      <EvidenceSummary
        title="Why this diagnosis is showing"
        description="The first read is limited to the main issue, severity, drivers, and evidence quality."
        items={evidenceSummaryItems(model)}
      />
      <MetricMatrix groups={diagnosisMetricGroups(model)} />
      <AdvancedDiagnostics model={model} xraySummary={xraySummary} />

    </div>
  );
}
