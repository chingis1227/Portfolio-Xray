import type { EvidenceItem, Metric } from "@/lib/types";
import { DecisionHeroCard } from "@/components/ui/DecisionHeroCard";
import { MetricCard } from "@/components/ui/MetricCard";
import { EvidenceCard } from "./EvidenceCard";

export function EvidenceCenter({ headline, quality, boundaryNote, items, metrics }: { headline: string; quality: string; boundaryNote: string; items: EvidenceItem[]; metrics: Metric[] }) {
  return (
    <div className="space-y-6">
      <DecisionHeroCard eyebrow="Evidence Center" title={headline} body={boundaryNote} status={quality} tone="amber" />
      <div className="grid gap-4 md:grid-cols-3">
        {metrics.map((metric) => <MetricCard key={metric.label} metric={metric} />)}
      </div>
      <section className="grid gap-4 lg:grid-cols-2">
        {items.map((item) => <EvidenceCard key={`${item.type}-${item.title}`} item={item} />)}
      </section>
    </div>
  );
}
