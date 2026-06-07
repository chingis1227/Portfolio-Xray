import type { Metric } from "@/lib/types";
import { StatusBadge } from "./StatusBadge";

type MetricCardProps = {
  metric: Metric;
};

export function MetricCard({ metric }: MetricCardProps) {
  return (
    <article className="pmri-card rounded-xl p-4">
      <div className="flex items-start justify-between gap-3">
        <p className="text-xs font-medium uppercase tracking-[0.12em] text-pmri-muted">{metric.label}</p>
        {metric.tone ? <StatusBadge tone={metric.tone}>{metric.delta ?? metric.tone}</StatusBadge> : null}
      </div>
      <p className="data-figure mt-4 text-2xl font-semibold tracking-tight text-pmri-text">{metric.value}</p>
      {metric.detail ? <p className="mt-1 text-sm text-pmri-muted">{metric.detail}</p> : null}
    </article>
  );
}
