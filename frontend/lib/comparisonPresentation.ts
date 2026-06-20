import { sanitizePublicDisplayText } from "@/lib/displayLabels";
import type { ComparisonMetric } from "@/lib/types";

export type ComparisonPublicSummaryInput = {
  improved?: string[];
  worsened?: string[];
  evidenceQuality?: string;
  metrics?: ComparisonMetric[];
  materiality?: string;
};

export type ComparisonPublicSummary = {
  improved: string;
  worsened: string;
  materiality: string;
  hasImprovedMetric: boolean;
};

function statusKey(value: unknown) {
  return String(value ?? "")
    .trim()
    .toLowerCase()
    .replace(/[^a-z0-9]+/g, "_")
    .replace(/^_+|_+$/g, "");
}

function isImprovedMetric(metric: ComparisonMetric) {
  const direction = statusKey(metric.direction);
  return direction.includes("improved") || metric.tone === "blue";
}

function isWorsenedMetric(metric: ComparisonMetric) {
  const direction = statusKey(metric.direction);
  return direction.includes("worse") || direction.includes("worsened") || metric.tone === "amber" || metric.tone === "red";
}

function firstMeaningful(items: string[] | undefined) {
  const item = (items ?? []).find((value) => value && !/^no available comparison metric showed/i.test(value));
  return item ? sanitizePublicDisplayText(item) : undefined;
}

function concentrationImproved(metrics: ComparisonMetric[]) {
  return metrics.some((metric) => isImprovedMetric(metric) && /concentration|largest holding|hhi|single holding/i.test(metric.metric));
}

export function deriveComparisonPublicSummary(input: ComparisonPublicSummaryInput): ComparisonPublicSummary {
  const metrics = input.metrics ?? [];
  const improvedMetrics = metrics.filter(isImprovedMetric);
  const worsenedMetrics = metrics.filter(isWorsenedMetric);
  const hasImprovedMetric = improvedMetrics.length > 0;
  const evidenceQuality = sanitizePublicDisplayText(input.evidenceQuality, "comparison evidence is incomplete").toLowerCase();
  const evidenceLimited = /limited|incomplete|insufficient|partial|degraded|unavailable/.test(evidenceQuality);

  let improved = firstMeaningful(input.improved);
  if (!improved && concentrationImproved(metrics) && evidenceLimited) {
    improved = "The candidate reduces concentration, but verdict confidence remains limited because comparison evidence is incomplete.";
  } else if (!improved && concentrationImproved(metrics)) {
    improved = "The candidate reduces concentration in the displayed comparison metrics.";
  } else if (!improved && hasImprovedMetric) {
    improved = `${sanitizePublicDisplayText(improvedMetrics[0]?.metric, "A displayed metric")} improved in the comparison matrix.`;
  }

  let worsened = firstMeaningful(input.worsened);
  if (!worsened && worsenedMetrics.length) {
    worsened = `${sanitizePublicDisplayText(worsenedMetrics[0]?.metric, "A displayed metric")} needs review as the main trade-off.`;
  }

  return {
    improved: improved ?? "No displayed metric showed a material improvement.",
    worsened: worsened ?? "No material worsening is visible in the displayed comparison metrics.",
    materiality: sanitizePublicDisplayText(input.materiality, "Materiality needs review."),
    hasImprovedMetric
  };
}
