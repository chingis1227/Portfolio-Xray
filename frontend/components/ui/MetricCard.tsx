import type { Metric } from "@/lib/types";
import { normalizeDisplayLabel } from "@/lib/displayLabels";
import { StatusBadge } from "./StatusBadge";
import { ScoreIndicator } from "./ScoreIndicator";

type MetricCardProps = {
  metric: Metric;
};

const toneLabel = {
  blue: "Info",
  gold: "Context",
  green: "Aligned",
  amber: "Medium risk",
  red: "High risk",
  slate: "Unavailable"
} satisfies Record<NonNullable<Metric["tone"]>, string>;

export function MetricCard({ metric }: MetricCardProps) {
  const badgeLabel = metric.delta ? normalizeDisplayLabel(metric.delta) : toneLabel[metric.tone ?? "slate"];
  const scoreMatch = metric.detail?.match(/^Score\s+(\d+(?:\.\d+)?)\/100$/i);
  const showBadge = Boolean(metric.delta || metric.tone === "red" || metric.tone === "amber" || badgeLabel === "Unavailable");

  return (
    <article className="pmri-card pmri-interactive-card rounded-2xl p-5">
      <div className="flex items-start justify-between gap-3">
        <p className="pmri-label">{normalizeDisplayLabel(metric.label)}</p>
        {metric.tone && showBadge ? <StatusBadge tone={metric.tone}>{badgeLabel}</StatusBadge> : null}
      </div>
      <p className="data-figure mt-5 text-2xl font-medium text-pmri-text">{normalizeDisplayLabel(metric.value)}</p>
      {scoreMatch ? (
        <div className="mt-3">
          <ScoreIndicator score={Number(scoreMatch[1])} tone={metric.tone ?? "slate"} />
        </div>
      ) : metric.detail ? <p className="mt-1 text-sm leading-6 text-pmri-text2">{normalizeDisplayLabel(metric.detail)}</p> : null}
    </article>
  );
}
