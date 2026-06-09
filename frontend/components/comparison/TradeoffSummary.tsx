import { StatusBadge } from "@/components/ui/StatusBadge";

export function TradeoffSummary({
  improved,
  worsened,
  unclear,
  evidenceQuality,
  boundary
}: {
  improved: string[];
  worsened: string[];
  unclear?: string[];
  evidenceQuality: string;
  boundary: string;
}) {
  const unclearItems = unclear?.length ? unclear : [
    "Whether the trade-off fits the client mandate.",
    "Whether evidence is strong enough for a material change.",
    worsened[2] ?? boundary
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
          <StatusBadge tone="amber">Evidence: {evidenceQuality}</StatusBadge>
          <StatusBadge tone="slate">No-trade valid</StatusBadge>
        </div>
      </div>

      <div className="mt-6 grid gap-4 lg:grid-cols-3">
        <article className="rounded-2xl border border-pmri-positive/18 bg-pmri-positive/[0.055] p-5">
          <StatusBadge tone="green">What changed</StatusBadge>
          <ul className="mt-4 space-y-3 text-sm leading-6 text-pmri-text2">
            {improved.map((item) => <li key={item}>• {item}</li>)}
          </ul>
        </article>
        <article className="rounded-2xl border border-pmri-amber/18 bg-pmri-amber/[0.055] p-5">
          <StatusBadge tone="amber">What it costs</StatusBadge>
          <ul className="mt-4 space-y-3 text-sm leading-6 text-pmri-text2">
            {worsened.slice(0, 4).map((item) => <li key={item}>• {item}</li>)}
          </ul>
        </article>
        <article className="rounded-2xl border border-pmri-border/45 bg-white/[0.026] p-5">
          <StatusBadge tone="slate">What remains unclear</StatusBadge>
          <ul className="mt-4 space-y-3 text-sm leading-6 text-pmri-text2">
            {unclearItems.slice(0, 4).map((item) => <li key={item}>• {item}</li>)}
          </ul>
        </article>
      </div>

      <p className="mt-5 rounded-xl border border-pmri-border/45 bg-white/[0.026] p-3 text-sm leading-6 text-pmri-text2">{boundary}</p>
    </section>
  );
}
