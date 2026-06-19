import type { Metric, SiteExplanationBundle, StatusTone } from "@/lib/types";
import type { XRaySummary } from "@/lib/reviewState";
import { buildDiagnosisDisplayModel, type DiagnosisDisplayFact } from "@/lib/diagnosisDisplayModel";
import type { EvidenceSummaryItem } from "@/components/ui/EvidenceSummary";
import type { MetricMatrixGroup, MetricMatrixRow } from "@/components/ui/MetricMatrix";
import { ScoreIndicator } from "@/components/ui/ScoreIndicator";

export type DiagnosisPresentationInput = {
  headline: string;
  evidenceQuality: string;
  nextStep: string;
  boundaryNote: string;
  drivers: string[];
  metrics: Metric[];
  xraySummary?: XRaySummary;
  siteExplanation?: SiteExplanationBundle;
};

export type DiagnosisDisplayModel = ReturnType<typeof buildDiagnosisDisplayModel>;

export function buildDiagnosisPresentation(input: DiagnosisPresentationInput) {
  const model = buildDiagnosisDisplayModel(input);
  return {
    model,
    metricGroups: diagnosisMetricGroups(model),
    evidenceItems: evidenceSummaryItems(model, input.metrics)
  };
}

export function factByLabel(facts: DiagnosisDisplayFact[], label: string) {
  return facts.find((fact) => fact.label.toLowerCase() === label.toLowerCase());
}

export function extractPercent(value?: string) {
  return value?.match(/-?\d+(?:\.\d+)?%/)?.[0];
}

function metricByLabels(metrics: Metric[], labels: string[]) {
  return labels
    .map((label) => metrics.find((metric) => metric.label.toLowerCase() === label.toLowerCase()))
    .find(Boolean);
}

function metricFact(metrics: Metric[], labels: string[], label: string, note: string): DiagnosisDisplayFact | undefined {
  const metric = metricByLabels(metrics, labels);
  if (!metric || !metric.value || /unavailable|n\/a/i.test(String(metric.value))) return undefined;
  const cleanNote = note.replace(/\.+$/g, "");
  const cleanDetail = typeof metric.detail === "string" ? metric.detail.replace(/\.+$/g, "") : undefined;
  return {
    label,
    value: String(metric.value),
    detail: cleanDetail,
    note: cleanDetail && cleanDetail.trim() ? cleanDetail : cleanNote,
    tone: metric.tone ?? "slate"
  };
}

export function evidenceQualityValue(model: DiagnosisDisplayModel) {
  return model.dataCoverage === "Limited" || model.dataCoverage === "Unavailable" ? "Limited" : "Strong";
}

export function concentrationFact(model: DiagnosisDisplayModel, metrics: Metric[] = []) {
  return factByLabel(model.whatMatters, "Concentration")
    ?? metricFact(metrics, ["Top 3 concentration", "Concentration"], "Concentration", "Largest holdings drive a material share of capital");
}

export function exposureFact(model: DiagnosisDisplayModel, metrics: Metric[] = []) {
  return factByLabel(model.whatMatters, "Main exposure")
    ?? metricFact(metrics, ["Dominant exposure", "Main exposure", "Equity sleeve"], "Main exposure", "Dominant economic risk sleeve");
}

export function downsideFact(model: DiagnosisDisplayModel, metrics: Metric[] = []) {
  return factByLabel(model.whatMatters, "Downside pain")
    ?? factByLabel(model.behaviorSnapshot, "Pain")
    ?? factByLabel(model.whatMatters, "Main weakness")
    ?? metricFact(metrics, ["Max drawdown", "Downside pain", "Worst observed downside"], "Downside pain", "Largest observed loss in the diagnostic window");
}

function exposureValue(exposure?: DiagnosisDisplayFact) {
  if (!exposure) return "Not evaluated";
  const percent = extractPercent(exposure.detail) ?? extractPercent(exposure.note);
  if (percent && !extractPercent(exposure.value)) return `${exposure.value} = ${percent}`;
  return exposure.value;
}

export function evidenceSummaryItems(model: DiagnosisDisplayModel, metrics: Metric[] = []): EvidenceSummaryItem[] {
  const concentration = concentrationFact(model, metrics);
  const exposure = exposureFact(model, metrics);
  const downside = downsideFact(model, metrics);
  const quality = evidenceQualityValue(model);

  return [
    { label: "Primary issue", value: concentration?.value ?? "Not evaluated" },
    { label: "Main exposure", value: exposureValue(exposure) },
    { label: "Worst observed downside", value: downside?.value ?? "Not evaluated", tone: downside?.value ? "red" : "slate" },
    { label: "Evidence quality", value: quality, tone: quality === "Limited" ? "amber" : "slate" }
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

export function diagnosisMetricGroups(model: DiagnosisDisplayModel): MetricMatrixGroup[] {
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

export function concentrationCanvasTitle(model: DiagnosisDisplayModel, metrics: Metric[] = []) {
  const fact = concentrationFact(model, metrics);
  const percent = extractPercent(fact?.detail ?? fact?.value);
  return percent ? `Top 3 holdings drive ${percent} of capital` : "Top 3 holdings drive a material share of capital";
}

export function exposureCanvasTitle(model: DiagnosisDisplayModel, metrics: Metric[] = []) {
  const fact = exposureFact(model, metrics);
  const percent = extractPercent(fact?.detail ?? fact?.note);
  if (fact?.value && percent) return `${fact.value} is the dominant exposure at ${percent}`;
  if (fact?.value) return `${fact.value} is the dominant exposure`;
  return "Dominant exposure requires review";
}
