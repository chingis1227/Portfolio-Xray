import { StatusBadge } from "@/components/ui/StatusBadge";
import { formatUnknownValue, normalizeDisplaySentence } from "@/lib/displayLabels";

export function TradeoffSummary({
  improved,
  worsened,
  unclear,
  costs,
  evidenceQuality,
  boundary
}: {
  improved: string[];
  worsened: string[];
  unclear?: string[];
  costs?: string[];
  evidenceQuality: string;
  boundary: string;
}) {
  const safeImproved = improved.length
    ? improved.map((item) => normalizeDisplaySentence(item))
    : ["No available comparison metric showed a material improvement."];
  const safeWorsened = worsened.length
    ? worsened.map((item) => normalizeDisplaySentence(item))
    : ["No available comparison metric showed a material worsening."];
  const safeCosts = costs?.length
    ? costs.map((item) => normalizeDisplaySentence(item))
    : ["Turnover and cost evidence is not available for this comparison."];
  const unclearItems = unclear?.length ? unclear.map((item) => normalizeDisplaySentence(item)) : [
    "Whether the trade-off fits the client mandate.",
    "Whether evidence is strong enough for a material change.",
    safeWorsened[2] ?? normalizeDisplaySentence(boundary)
  ];

  return (
    <section className="pmri-card rounded-3xl p-6 md:p-7">
      <div className="flex flex-col gap-4 border-b border-pmri-border/40 pb-5 md:flex-row md:items-start md:justify-between">
        <div>
          <p className="pmri-label">Trade-off conclusion</p>
          <h2 className="pmri-heading-display mt-2 max-w-4xl text-pmri-text">
            Comparison evidence is visible, but it does not automatically justify action.
          </h2>
        </div>
        <div className="flex flex-wrap gap-2">
          <StatusBadge tone="amber">Evidence: {formatUnknownValue(evidenceQuality, "Evidence status unavailable")}</StatusBadge>
          <StatusBadge tone="slate">Trade-off evidence</StatusBadge>
        </div>
      </div>

      <div className="mt-6 grid gap-4 lg:grid-cols-4">
        <article className="rounded-2xl border border-pmri-positive/18 bg-pmri-positive/[0.055] p-5">
          <StatusBadge tone="green">What improves</StatusBadge>
          <ul className="mt-4 space-y-3 text-sm leading-6 text-pmri-text2">
            {safeImproved.map((item) => <li key={item}>• {item}</li>)}
          </ul>
        </article>
        <article className="rounded-2xl border border-pmri-amber/18 bg-pmri-amber/[0.055] p-5">
          <StatusBadge tone="amber">What worsens</StatusBadge>
          <ul className="mt-4 space-y-3 text-sm leading-6 text-pmri-text2">
            {safeWorsened.slice(0, 4).map((item) => <li key={item}>• {item}</li>)}
          </ul>
        </article>
        <article className="rounded-2xl border border-pmri-gold/20 bg-pmri-gold/[0.055] p-5">
          <StatusBadge tone="gold">What it costs</StatusBadge>
          <ul className="mt-4 space-y-3 text-sm leading-6 text-pmri-text2">
            {safeCosts.slice(0, 4).map((item) => <li key={item}>• {item}</li>)}
          </ul>
        </article>
        <article className="rounded-2xl border border-pmri-border/45 bg-white/[0.026] p-5">
          <StatusBadge tone="slate">What remains unclear</StatusBadge>
          <ul className="mt-4 space-y-3 text-sm leading-6 text-pmri-text2">
            {unclearItems.slice(0, 4).map((item) => <li key={item}>• {item}</li>)}
          </ul>
        </article>
      </div>

      <p className="mt-5 rounded-xl border border-pmri-border/45 bg-white/[0.026] p-3 text-sm leading-6 text-pmri-text2">{normalizeDisplaySentence(boundary)}</p>
    </section>
  );
}
