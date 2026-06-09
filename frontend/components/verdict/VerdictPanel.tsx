import type { Metric } from "@/lib/types";
import { DecisionHeroCard } from "@/components/ui/DecisionHeroCard";
import { MetricCard } from "@/components/ui/MetricCard";
import { StatusBadge } from "@/components/ui/StatusBadge";

export function VerdictPanel({ state, headline, explanation, evidenceQuality, boundaryNote, keyEvidence, monitoringTrigger, metrics }: { state: string; headline: string; explanation: string; evidenceQuality: string; boundaryNote: string; keyEvidence: string[]; monitoringTrigger: string; metrics: Metric[] }) {
  return (
    <div className="space-y-6">
      <DecisionHeroCard eyebrow="Decision-support only" title={headline} body={explanation} status={state} tone="slate">
        <div className="flex flex-wrap gap-3">
          <StatusBadge tone="amber">Evidence: {evidenceQuality}</StatusBadge>
          <StatusBadge tone="blue">Not an implementation order</StatusBadge>
        </div>
      </DecisionHeroCard>
      <div className="grid gap-4 md:grid-cols-3">
        {metrics.map((metric) => <MetricCard key={metric.label} metric={metric} />)}
      </div>
      <section className="grid gap-4 lg:grid-cols-[1.2fr_0.8fr]">
        <article className="pmri-card rounded-2xl p-5">
          <h3 className="pmri-heading-section text-lg text-pmri-text">Key evidence behind verdict</h3>
          <ul className="mt-4 space-y-3 text-sm leading-6 text-pmri-text2">
            {keyEvidence.map((item) => <li key={item}>• {item}</li>)}
          </ul>
          <p className="mt-5 rounded-xl border border-pmri-border/70 bg-white/[0.035] p-3 text-sm text-pmri-text2">{boundaryNote}</p>
        </article>
        <article className="pmri-card rounded-2xl p-5">
          <StatusBadge tone="blue">Monitoring trigger</StatusBadge>
          <p className="mt-4 text-sm leading-6 text-pmri-text2">{monitoringTrigger}</p>
        </article>
      </section>
    </div>
  );
}
