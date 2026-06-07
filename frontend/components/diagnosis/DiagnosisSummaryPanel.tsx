import type { Metric } from "@/lib/types";
import { DecisionHeroCard } from "@/components/ui/DecisionHeroCard";
import { MetricCard } from "@/components/ui/MetricCard";
import { StatusBadge } from "@/components/ui/StatusBadge";

type DiagnosisSummaryPanelProps = {
  status: string;
  headline: string;
  evidenceQuality: string;
  nextStep: string;
  boundaryNote: string;
  drivers: string[];
  metrics: Metric[];
};

export function DiagnosisSummaryPanel({ status, headline, evidenceQuality, nextStep, boundaryNote, drivers, metrics }: DiagnosisSummaryPanelProps) {
  return (
    <div className="space-y-6">
      <DecisionHeroCard eyebrow="Diagnosis before action" title={headline} body={boundaryNote} status={status} tone="gold">
        <div className="flex flex-wrap gap-3">
          <StatusBadge tone="amber">Evidence: {evidenceQuality}</StatusBadge>
          <StatusBadge tone="blue">Next: {nextStep}</StatusBadge>
        </div>
      </DecisionHeroCard>

      <div className="grid gap-4 md:grid-cols-3">
        {metrics.map((metric) => <MetricCard key={metric.label} metric={metric} />)}
      </div>

      <section className="pmri-card rounded-2xl p-5">
        <h3 className="text-lg font-semibold text-pmri-text">Top diagnosis drivers</h3>
        <div className="mt-4 grid gap-3 md:grid-cols-3">
          {drivers.map((driver, index) => (
            <article key={driver} className="rounded-xl border border-pmri-border bg-white/[0.03] p-4">
              <p className="font-mono text-xs text-pmri-gold">0{index + 1}</p>
              <p className="mt-3 text-sm leading-6 text-pmri-text2">{driver}</p>
            </article>
          ))}
        </div>
      </section>
    </div>
  );
}
