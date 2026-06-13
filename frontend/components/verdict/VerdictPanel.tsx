import type { Metric } from "@/lib/types";
import { DecisionHeroCard } from "@/components/ui/DecisionHeroCard";
import { MetricCard } from "@/components/ui/MetricCard";
import { StatusBadge } from "@/components/ui/StatusBadge";
import { formatUnknownValue, normalizeDisplaySentence } from "@/lib/displayLabels";

export function VerdictPanel({ state, headline, explanation, evidenceQuality, boundaryNote, keyEvidence, monitoringTrigger, metrics }: { state: string; headline: string; explanation: string; evidenceQuality: string; boundaryNote: string; keyEvidence: string[]; monitoringTrigger: string; metrics: Metric[] }) {
  const safeMetrics = metrics.map((metric) => ({
    ...metric,
    label: formatUnknownValue(metric.label, "Metric"),
    value: formatUnknownValue(metric.value),
    detail: metric.detail ... normalizeDisplaySentence(metric.detail) : undefined
  }));
  const safeEvidence = keyEvidence.length
    ... keyEvidence.map((item) => normalizeDisplaySentence(item))
    : ["No additional evidence rows were returned for this verdict."];

  return (
    <div className="space-y-6">
      <DecisionHeroCard eyebrow="Decision-support only" title={normalizeDisplaySentence(headline, "Decision verdict generated.")} body={normalizeDisplaySentence(explanation, "The active review produced a decision-support verdict.")} status={formatUnknownValue(state, "Decision-support verdict")} tone="slate">
        <div className="flex flex-wrap gap-3">
          <StatusBadge tone="amber">Evidence: {formatUnknownValue(evidenceQuality, "Evidence status unavailable")}</StatusBadge>
          <StatusBadge tone="blue">Not a trade instruction</StatusBadge>
        </div>
      </DecisionHeroCard>
      <div className="grid gap-4 md:grid-cols-3">
        {safeMetrics.map((metric) => <MetricCard key={metric.label} metric={metric} />)}
      </div>
      <section className="grid gap-4 lg:grid-cols-[1.2fr_0.8fr]">
        <article className="pmri-card rounded-2xl p-5">
          <h3 className="pmri-heading-section text-lg text-pmri-text">Key evidence behind verdict</h3>
          <ul className="mt-4 space-y-3 text-sm leading-6 text-pmri-text2">
            {safeEvidence.map((item) => <li key={item}>• {item}</li>)}
          </ul>
          <p className="mt-5 rounded-xl border border-pmri-border/70 bg-white/[0.035] p-3 text-sm text-pmri-text2">{normalizeDisplaySentence(boundaryNote, "Decision-support only. This is not a trade instruction or rebalance recommendation.")}</p>
        </article>
        <article className="pmri-card rounded-2xl p-5">
          <StatusBadge tone="blue">Monitoring trigger</StatusBadge>
          <p className="mt-4 text-sm leading-6 text-pmri-text2">{normalizeDisplaySentence(monitoringTrigger, "Monitor changes in comparison evidence before revisiting the verdict.")}</p>
        </article>
      </section>
    </div>
  );
}
