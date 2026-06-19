import type { Metric, SiteExplanationBundle, StatusTone } from "@/lib/types";
import type { XRaySummary } from "@/lib/reviewState";
import {
  evidenceQualityLabel,
  normalizeDisplayLabel,
  normalizeDisplaySentence
} from "@/lib/displayLabels";

export type DiagnosisDisplayFact = {
  label: string;
  value: string;
  detail?: string;
  note: string;
  tone: StatusTone;
};

export type DiagnosisDisplayModel = {
  mainFinding: string;
  whyItMatters: string;
  dataCoverage: string;
  dataCoverageTone: StatusTone;
  primaryEvidence: string[];
  whatMatters: DiagnosisDisplayFact[];
  behaviorSnapshot: DiagnosisDisplayFact[];
  advancedMetrics: Metric[];
  technicalEvidence: string[];
  limitations: string[];
  nextStep: string;
  boundaryNote: string;
};

type DiagnosisDisplayModelInput = {
  headline: string;
  evidenceQuality: string;
  nextStep: string;
  boundaryNote: string;
  drivers: string[];
  metrics: Metric[];
  xraySummary?: XRaySummary;
  siteExplanation?: SiteExplanationBundle;
};

const ADVANCED_METRIC_LABELS = new Set([
  "var 95",
  "es 95",
  "skewness",
  "kurtosis",
  "beta",
  "downside beta",
  "upside beta",
  "benchmark correlation",
  "sharpe",
  "sortino",
  "treynor",
  "vol of vol"
]);

function findMetric(metrics: Metric[], label: string) {
  return metrics.find((metric) => metric.label.toLowerCase() === label.toLowerCase());
}

function metricPool(input: DiagnosisDisplayModelInput) {
  return input.xraySummary?.snapshotCards?.length ? input.xraySummary.snapshotCards : input.metrics;
}

function riskMetrics(input: DiagnosisDisplayModelInput) {
  return input.xraySummary?.riskProfile.metrics ?? input.metrics;
}

function isUnavailable(value?: unknown) {
  const normalized = normalizeDisplayLabel(value, "").toLowerCase();
  return !normalized || normalized === "n/a" || normalized.includes("not available") || normalized.includes("unavailable");
}

function withoutTerminalPeriod(value: string) {
  return value.trim().replace(/\.+$/g, "");
}

export function formatDiagnosisDisplayValue(value?: unknown, fallback = "Unavailable") {
  if (value === null || value === undefined) return fallback;
  const raw = normalizeDisplayLabel(value, fallback);
  if (isUnavailable(raw)) return fallback;
  return raw
    .replace(/\b(-?\d+)\.00%/g, "$1%")
    .replace(/\b(-?\d+\.\d)0%/g, "$1%")
    .replace(/\b(-?\d+)\.00 months\b/gi, "$1 months")
    .replace(/\b(-?\d+\.\d)0 months\b/gi, "$1 months")
    .replace(/\b1 months\b/gi, "1 month")
    .replace(/\b(-?\d+)\.00\b/g, "$1")
    .replace(/\b(-?\d+\.\d)0\b/g, "$1");
}

function uniqueStrings(values: string[], limit?: number) {
  const seen = new Set<string>();
  const output: string[] = [];
  values.forEach((value) => {
    const normalized = normalizeDisplaySentence(formatDiagnosisDisplayValue(value), "").trim();
    if (!normalized || isUnavailable(normalized)) return;
    const key = normalized.toLowerCase();
    if (seen.has(key)) return;
    seen.add(key);
    output.push(normalized);
  });
  return typeof limit === "number" ? output.slice(0, limit) : output;
}

function isUnsafePublicDiagnosisText(value: string) {
  return /portfolio health score|robustness scorecard|\bscorecard\b|\boptimizer\b|rebalance now|must rebalance|trade now|approved portfolio|\.json\b/i.test(value);
}

function parsePercent(value?: string) {
  if (!value) return null;
  const parsed = Number(value.replace("%", "").trim());
  return Number.isFinite(parsed) ? parsed : null;
}

function severityFromTone(tone?: StatusTone, fallback: StatusTone = "slate") {
  return tone ?? fallback;
}

function mainFinding(input: DiagnosisDisplayModelInput) {
  const metrics = metricPool(input);
  const exposure = findMetric(metrics, "Dominant exposure")?.value;
  const top3 = parsePercent(findMetric(metrics, "Top 3 concentration")?.value);
  if (exposure && top3 !== null) {
    const concentrationText = top3 >= 50 ? "concentrated in the top holdings" : "not dominated by the top holdings";
    return `The portfolio is ${formatDiagnosisDisplayValue(exposure).toLowerCase()}-led and ${concentrationText}`;
  }
  return withoutTerminalPeriod(normalizeDisplaySentence(input.headline, "Current portfolio diagnosis is available."));
}

function whyItMatters(input: DiagnosisDisplayModelInput) {
  const metrics = metricPool(input);
  const weakness = findMetric(metrics, "Worst pre-stress weakness") ?? findMetric(metrics, "Primary weakness");
  const drawdown = findMetric(metrics, "Max drawdown");
  if (weakness && drawdown) {
    return `The main weakness to review is ${formatDiagnosisDisplayValue(weakness.value)}, with ${formatDiagnosisDisplayValue(drawdown.value)} observed downside in the diagnostic window`;
  }
  const explanation = input.siteExplanation?.screens?.diagnosis?.executive?.[0]?.text;
  return withoutTerminalPeriod(normalizeDisplaySentence(explanation || input.drivers[0], "Diagnosis summarizes the current portfolio before any candidate test."));
}

function primaryEvidence(input: DiagnosisDisplayModelInput) {
  const metrics = metricPool(input);
  const top3 = findMetric(metrics, "Top 3 concentration");
  const dominant = findMetric(metrics, "Dominant exposure");
  const drawdown = findMetric(metrics, "Max drawdown");
  const weakness = findMetric(metrics, "Worst pre-stress weakness") ?? findMetric(metrics, "Primary weakness");
  return uniqueStrings([
    top3 ? `Top 3 holdings: ${formatDiagnosisDisplayValue(top3.value)}` : "",
    dominant ? `Dominant exposure: ${formatDiagnosisDisplayValue(dominant.value)}${dominant.detail && !isUnavailable(dominant.detail) ? ` ${formatDiagnosisDisplayValue(dominant.detail)}` : ""}` : "",
    drawdown ? `Worst observed drawdown: ${formatDiagnosisDisplayValue(drawdown.value)}` : "",
    weakness ? `Main pre-stress weakness: ${formatDiagnosisDisplayValue(weakness.value)}` : "",
    ...input.drivers
  ], 3);
}

function whatMatters(input: DiagnosisDisplayModelInput): DiagnosisDisplayFact[] {
  const metrics = metricPool(input);
  const top3 = findMetric(metrics, "Top 3 concentration");
  const exposure = findMetric(metrics, "Dominant exposure") ?? findMetric(metrics, "Equity sleeve");
  const drawdown = findMetric(metrics, "Max drawdown");
  const weakness = findMetric(metrics, "Worst pre-stress weakness") ?? findMetric(metrics, "Primary weakness");
  const top3Pct = parsePercent(top3?.value);
  const items: Array<DiagnosisDisplayFact | null> = [
    top3 && !isUnavailable(top3.value) ? {
      label: "Concentration",
      value: `Top 3 = ${formatDiagnosisDisplayValue(top3.value)}`,
      detail: formatDiagnosisDisplayValue(top3.value),
      note: top3Pct !== null && top3Pct >= 50 ? "Largest holdings drive a material share of capital" : "Capital is less concentrated in the largest holdings",
      tone: top3Pct !== null && top3Pct >= 65 ? "red" : top3Pct !== null && top3Pct >= 50 ? "amber" : "slate"
    } : null,
    exposure && !isUnavailable(exposure.value) ? {
      label: "Main exposure",
      value: formatDiagnosisDisplayValue(exposure.value),
      detail: exposure.detail && !isUnavailable(exposure.detail) ? formatDiagnosisDisplayValue(exposure.detail) : undefined,
      note: exposure.detail && !isUnavailable(exposure.detail) ? withoutTerminalPeriod(formatDiagnosisDisplayValue(exposure.detail)) : "Dominant economic risk sleeve",
      tone: severityFromTone(exposure.tone, "slate")
    } : null,
    drawdown && !isUnavailable(drawdown.value) ? {
      label: "Downside pain",
      value: formatDiagnosisDisplayValue(drawdown.value),
      detail: formatDiagnosisDisplayValue(drawdown.value),
      note: drawdown.detail && !isUnavailable(drawdown.detail) ? withoutTerminalPeriod(formatDiagnosisDisplayValue(drawdown.detail)) : "Largest observed loss in the diagnostic window",
      tone: severityFromTone(drawdown.tone, "slate")
    } : null,
    weakness && !isUnavailable(weakness.value) ? {
      label: "Main weakness",
      value: formatDiagnosisDisplayValue(weakness.value),
      detail: weakness.detail && !isUnavailable(weakness.detail) ? formatDiagnosisDisplayValue(weakness.detail) : undefined,
      note: "Review this in Stress Lab before testing a candidate",
      tone: severityFromTone(weakness.tone, "slate")
    } : null
  ];
  return items.filter((item): item is DiagnosisDisplayFact => Boolean(item)).slice(0, 4);
}

function behaviorSnapshot(input: DiagnosisDisplayModelInput): DiagnosisDisplayFact[] {
  const metrics = riskMetrics(input);
  const cagr = findMetric(metrics, "CAGR");
  const drawdown = findMetric(metrics, "Max drawdown");
  const recovery = findMetric(metrics, "Time to recovery");
  const beta = findMetric(metrics, "Beta");
  const volatility = findMetric(metrics, "Annual volatility");
  return [
    cagr && !isUnavailable(cagr.value) ? {
      label: "Growth",
      value: formatDiagnosisDisplayValue(cagr.value),
      note: cagr.detail && !isUnavailable(cagr.detail) ? withoutTerminalPeriod(formatDiagnosisDisplayValue(cagr.detail)) : "Realized growth in the primary diagnostic window",
      tone: "slate"
    } : null,
    drawdown && !isUnavailable(drawdown.value) ? {
      label: "Pain",
      value: recovery && !isUnavailable(recovery.value)
        ? `${formatDiagnosisDisplayValue(drawdown.value)} / ${formatDiagnosisDisplayValue(recovery.value)}`
        : formatDiagnosisDisplayValue(drawdown.value),
      note: "Maximum drawdown and recovery evidence",
      tone: severityFromTone(drawdown.tone, "red")
    } : null,
    beta && !isUnavailable(beta.value) ? {
      label: "Market dependence",
      value: formatDiagnosisDisplayValue(beta.value),
      note: beta.detail && !isUnavailable(beta.detail) ? withoutTerminalPeriod(formatDiagnosisDisplayValue(beta.detail)) : "Sensitivity to benchmark movement",
      tone: severityFromTone(beta.tone, "slate")
    } : volatility && !isUnavailable(volatility.value) ? {
      label: "Risk level",
      value: formatDiagnosisDisplayValue(volatility.value),
      note: "Realized portfolio volatility",
      tone: "slate"
    } : null
  ].filter((item): item is DiagnosisDisplayFact => Boolean(item)).slice(0, 3);
}

function advancedMetrics(input: DiagnosisDisplayModelInput) {
  return riskMetrics(input)
    .filter((metric) => ADVANCED_METRIC_LABELS.has(metric.label.toLowerCase()))
    .filter((metric) => !isUnavailable(metric.value))
    .map((metric) => ({
      ...metric,
      value: formatDiagnosisDisplayValue(metric.value),
      detail: metric.detail && !isUnavailable(metric.detail) ? formatDiagnosisDisplayValue(metric.detail) : undefined
    }));
}

function dataCoverage(evidenceQuality: string) {
  const quality = evidenceQualityLabel(evidenceQuality);
  if (quality === "Strong evidence") return { label: "Strong", tone: "slate" as StatusTone };
  if (quality === "Moderate evidence") return { label: "Moderate", tone: "slate" as StatusTone };
  if (quality === "Limited evidence") return { label: "Limited", tone: "amber" as StatusTone };
  return { label: "Unavailable", tone: "slate" as StatusTone };
}

function userRelevantLimitations(input: DiagnosisDisplayModelInput) {
  const raw = [
    ...(input.xraySummary?.unavailableNotes ?? []),
    ...(input.siteExplanation?.warnings ?? [])
  ];
  return uniqueStrings(raw.filter((note) => {
    const normalized = note.toLowerCase();
    if (normalized.includes("rolling chart")) return false;
    if (normalized.includes("normalized for product contract")) return false;
    if (normalized.includes("factor names normalized")) return false;
    if (normalized.includes("usd->usd") || normalized.includes("vix->")) return false;
    return true;
  }), 4);
}

export function buildDiagnosisDisplayModel(input: DiagnosisDisplayModelInput): DiagnosisDisplayModel {
  const coverage = dataCoverage(input.evidenceQuality);
  const technicalEvidence = uniqueStrings([
    ...(input.siteExplanation?.screens?.diagnosis?.evidence ?? []).map((item) => item.text),
    ...(input.siteExplanation?.screens?.diagnosis?.technical ?? []).map((item) => item.text)
  ].filter((item) => !isUnsafePublicDiagnosisText(item)), 6);

  return {
    mainFinding: mainFinding(input),
    whyItMatters: whyItMatters(input),
    dataCoverage: coverage.label,
    dataCoverageTone: coverage.tone,
    primaryEvidence: primaryEvidence(input),
    whatMatters: whatMatters(input),
    behaviorSnapshot: behaviorSnapshot(input),
    advancedMetrics: advancedMetrics(input),
    technicalEvidence,
    limitations: userRelevantLimitations(input),
    nextStep: withoutTerminalPeriod(normalizeDisplaySentence(input.nextStep, "Review supporting evidence before testing one candidate hypothesis.")),
    boundaryNote: withoutTerminalPeriod(normalizeDisplaySentence(input.boundaryNote, "Diagnostic review context is available."))
  };
}
