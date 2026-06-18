import Link from "next/link";
import type { Metric, SiteExplanationBundle, StatusTone } from "@/lib/types";
import type { XRaySummary } from "@/lib/reviewState";
import { buildDiagnosisDisplayModel, type DiagnosisDisplayFact } from "@/lib/diagnosisDisplayModel";
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

type DiagnosisDisplayModel = ReturnType<typeof buildDiagnosisDisplayModel>;

function factByLabel(facts: DiagnosisDisplayFact[], label: string) {
  return facts.find((fact) => fact.label.toLowerCase() === label.toLowerCase());
}

function extractPercent(value?: string) {
  return value?.match(/-?\d+(?:\.\d+)?%/)?.[0];
}

function evidenceQualityValue(model: DiagnosisDisplayModel) {
  return model.dataCoverage === "Limited" || model.dataCoverage === "Unavailable" ? "Limited" : "Strong";
}

function concentrationFact(model: DiagnosisDisplayModel) {
  return factByLabel(model.whatMatters, "Concentration");
}

function exposureFact(model: DiagnosisDisplayModel) {
  return factByLabel(model.whatMatters, "Main exposure");
}

function downsideFact(model: DiagnosisDisplayModel) {
  return factByLabel(model.whatMatters, "Downside pain")
    ?? factByLabel(model.behaviorSnapshot, "Pain")
    ?? factByLabel(model.whatMatters, "Main weakness");
}

function exposureValue(exposure?: DiagnosisDisplayFact) {
  if (!exposure) return "Unavailable";
  const percent = extractPercent(exposure.detail) ?? extractPercent(exposure.note);
  if (percent && !extractPercent(exposure.value)) return `${exposure.value} = ${percent}`;
  return exposure.value;
}

function evidenceSummaryItems(model: DiagnosisDisplayModel): EvidenceSummaryItem[] {
  const concentration = concentrationFact(model);
  const exposure = exposureFact(model);
  const downside = downsideFact(model);
  const quality = evidenceQualityValue(model);

  return [
    {
      label: "Primary issue",
      value: concentration?.value ?? "Unavailable"
    },
    {
      label: "Main exposure",
      value: exposureValue(exposure)
    },
    {
      label: "Worst observed downside",
      value: downside?.value ?? "Unavailable",
      tone: downside?.value ? "red" : "slate"
    },
    {
      label: "Evidence quality",
      value: quality,
      tone: quality === "Limited" ? "amber" : "slate"
    }
  ];
}

function rowStatus(tone: StatusTone): { label: string; tone: StatusTone } | undefined {
  if (tone === "red") return { label: "Material issue", tone };
  if (tone === "amber") return { label: "Watch", tone };
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

function diagnosisMetricGroups(model: DiagnosisDisplayModel): MetricMatrixGroup[] {
  const riskLabels = new Set(["Downside pain", "Main weakness", "Pain", "Risk level", "Market dependence"]);
  const structureLabels = new Set(["Concentration", "Main exposure"]);
  const riskRows = [
    ...model.whatMatters.filter((fact) => riskLabels.has(fact.label)).map((fact) => factRow(fact, "Review vs stress and drawdown tolerance")),
    ...model.behaviorSnapshot.filter((fact) => riskLabels.has(fact.label)).map((fact) => factRow(fact, "Historical diagnostic window"))
  ];
  const structureRows = model.whatMatters
    .filter((fact) => structureLabels.has(fact.label))
    .map((fact) => factRow(fact, "Current portfolio composition"));
  const secondaryRows = [
    ...model.behaviorSnapshot.filter((fact) => !riskLabels.has(fact.label)).map((fact) => factRow(fact, "Historical diagnostic window")),
    ...model.advancedMetrics.slice(0, 4).map(metricRow)
  ];

  return [
    { title: "Risk pressure", description: "Downside, stress-adjacent, and sensitivity metrics.", rows: riskRows },
    { title: "Portfolio structure", description: "Concentration and dominant exposure context.", rows: structureRows },
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

function concentrationCanvasTitle(fact?: DiagnosisDisplayFact) {
  const percent = extractPercent(fact?.detail ?? fact?.value);
  return percent ? `Top 3 holdings drive ${percent} of capital` : "Top 3 holdings drive a material share of capital";
}

function exposureCanvasTitle(fact?: DiagnosisDisplayFact) {
  const percent = extractPercent(fact?.detail ?? fact?.note);
  if (fact?.value && percent) return `${fact.value} is the dominant exposure at ${percent}`;
  if (fact?.value) return `${fact.value} is the dominant exposure`;
  return "Dominant exposure requires review";
}

function DiagnosisHero({ model }: { model: DiagnosisDisplayModel }) {
  return (
    <VerdictHero
      stepContext="Step 02 of 8 - Portfolio Diagnosis"
      headline={model.mainFinding}
      interpretation={model.whyItMatters}
      actions={(
        <>
          <Link href="/evidence" className="pmri-focus pmri-primary-action rounded-full px-5 py-2.5 text-sm font-medium transition">
            Review Stress Lab evidence
          </Link>
          <Link href="/hypothesis" className="pmri-focus rounded-full border border-white/10 bg-white/[0.026] px-5 py-2.5 text-sm font-medium text-pmri-text2 transition hover:border-pmri-blue/40 hover:bg-white/[0.045] hover:text-pmri-text">
            Test one candidate hypothesis
          </Link>
        </>
      )}
    />
  );
}

function PrimaryDiagnosticCanvas({ model }: { model: DiagnosisDisplayModel }) {
  const concentration = concentrationFact(model);
  const exposure = exposureFact(model);
  const reviewItems = ["USD shock risk", "Interest-rate shock", "Equity sell-off"];

  const drivingItems = [
    {
      title: concentrationCanvasTitle(concentration),
      copy: "High concentration makes a few positions drive most portfolio behavior."
    },
    {
      title: exposureCanvasTitle(exposure),
      copy: "Portfolio behavior is meaningfully linked to equity-market conditions."
    },
    {
      title: "Diversification benefit may be limited by concentration",
      copy: "Diversification benefit may weaken under macro stress and should be verified in Stress Lab."
    }
  ];

  return (
    <section className="pmri-diagnostic-canvas">
      <div className="grid gap-0 lg:grid-cols-[1.28fr_0.72fr]">
        <div className="p-5 md:p-6 lg:p-7">
          <p className="text-[0.68rem] font-medium tracking-[0.08em] text-pmri-muted">Diagnostic canvas</p>
          <h2 className="mt-2 text-[clamp(1.35rem,2vw,1.9rem)] font-semibold leading-tight tracking-[-0.035em] text-pmri-text">
            What is driving the diagnosis
          </h2>
          <div className="mt-5 space-y-4">
            {drivingItems.map((item, index) => (
              <article key={item.title} className="grid gap-3 border-t border-white/[0.055] pt-4 md:grid-cols-[2rem_1fr]">
                <p className="data-figure text-sm text-pmri-muted">0{index + 1}</p>
                <div>
                  <h3 className="text-base font-semibold tracking-[-0.02em] text-pmri-text">{item.title}</h3>
                  <p className="mt-1.5 text-sm leading-6 text-pmri-text2">{item.copy}</p>
                </div>
              </article>
            ))}
          </div>
        </div>
        <aside className="border-t border-white/[0.06] bg-black/[0.14] p-5 md:p-6 lg:border-l lg:border-t-0 lg:p-7">
          <p className="text-[0.68rem] font-medium tracking-[0.08em] text-pmri-muted">Next review</p>
          <h2 className="mt-2 text-xl font-semibold tracking-[-0.03em] text-pmri-text">Where to review next</h2>
          <div className="mt-5 space-y-3">
            {reviewItems.map((item) => (
              <div key={item} className="flex items-center justify-between border-t border-white/[0.055] pt-3 text-sm text-pmri-text2">
                <span>{item}</span>
                <span className="h-1.5 w-1.5 rounded-full bg-pmri-blueSoft/[0.62]" aria-hidden="true" />
              </div>
            ))}
          </div>
          <Link href="/evidence" className="pmri-focus pmri-primary-action mt-6 inline-flex rounded-full px-5 py-2.5 text-sm font-medium transition">
            Review Stress Lab evidence
          </Link>
        </aside>
      </div>
    </section>
  );
}

function AdvancedDiagnostics({
  model,
  metricGroups,
  xraySummary
}: {
  model: DiagnosisDisplayModel;
  metricGroups: MetricMatrixGroup[];
  xraySummary?: XRaySummary;
}) {
  return (
    <details id="advanced-diagnostics" className="pmri-technical-disclosure rounded-3xl p-5 md:p-6">
      <summary className="pmri-focus cursor-pointer list-none rounded-2xl border border-white/[0.075] bg-white/[0.022] px-4 py-3 text-sm font-semibold text-pmri-text transition hover:border-pmri-blue/35 hover:bg-white/[0.04]">
        Advanced diagnostics and technical evidence
      </summary>
      <div className="mt-5 space-y-5">
        <MetricMatrix
          title="Compact metric matrix"
          description="Secondary metrics are grouped here after the primary diagnosis is understood."
          groups={metricGroups}
        />

        {model.advancedMetrics.length ? (
          <section className="pmri-card rounded-3xl p-5 md:p-6">
            <h3 className="text-sm font-semibold text-pmri-text">Professional metrics</h3>
            <p className="mt-2 text-sm leading-6 text-pmri-text2">
              These metrics support the case file but do not lead the first-read diagnosis.
            </p>
            <div className="mt-4 grid gap-3 sm:grid-cols-2 lg:grid-cols-3">
              {model.advancedMetrics.map((metric) => <MetricCard key={metric.label} metric={metric} />)}
            </div>
          </section>
        ) : null}

        {model.technicalEvidence.length || model.limitations.length ? (
          <section className="pmri-card rounded-3xl p-5 md:p-6">
            <h3 className="text-sm font-semibold text-pmri-text">Evidence chain notes</h3>
            {model.technicalEvidence.length ? (
              <ul className="mt-3 space-y-2 text-sm leading-6 text-pmri-text2">
                {model.technicalEvidence.map((item) => <li key={item}>- {item}</li>)}
              </ul>
            ) : null}
            {model.limitations.length ? (
              <div className="mt-4 border-t border-white/[0.06] pt-4">
                <p className="text-xs font-semibold text-pmri-muted">Limitations</p>
                <ul className="mt-2 space-y-2 text-sm leading-6 text-pmri-text2">
                  {model.limitations.map((item) => <li key={item}>- {item}</li>)}
                </ul>
              </div>
            ) : null}
          </section>
        ) : null}

        {xraySummary ? (
          <details className="rounded-2xl border border-white/[0.07] bg-black/10 p-4">
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
  const metricGroups = diagnosisMetricGroups(model);

  return (
    <div className="space-y-4 md:space-y-5">
      <DiagnosisHero model={model} />
      <EvidenceSummary items={evidenceSummaryItems(model)} showHeader={false} />
      <PrimaryDiagnosticCanvas model={model} />
      <AdvancedDiagnostics model={model} metricGroups={metricGroups} xraySummary={xraySummary} />
    </div>
  );
}
