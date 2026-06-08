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
    <section className="pmri-card rounded-2xl border-pmri-gold/30 p-6 md:p-7">
      <div className="flex flex-col gap-4 border-b border-pmri-border/80 pb-5 md:flex-row md:items-start md:justify-between">
        <div>
          <p className="text-xs font-semibold uppercase tracking-[0.16em] text-pmri-gold">Trade-off conclusion</p>
          <h2 className="mt-2 max-w-3xl text-2xl font-semibold tracking-[-0.02em] text-pmri-text md:text-3xl">
            Comparison evidence is visible, but it does not automatically justify action.
          </h2>
        </div>
        <div className="flex flex-wrap gap-2">
          <StatusBadge tone="amber">Evidence: {evidenceQuality}</StatusBadge>
          <StatusBadge tone="gold">No-trade valid</StatusBadge>
        </div>
      </div>

      <div className="mt-6 grid gap-4 lg:grid-cols-3">
        <article className="rounded-2xl border border-pmri-positive/25 bg-pmri-positive/10 p-5">
          <StatusBadge tone="green">What changed</StatusBadge>
          <ul className="mt-4 space-y-3 text-sm leading-6 text-pmri-text2">
            {improved.map((item) => <li key={item}>• {item}</li>)}
          </ul>
        </article>
        <article className="rounded-2xl border border-pmri-amber/25 bg-pmri-amber/10 p-5">
          <StatusBadge tone="amber">What it costs</StatusBadge>
          <ul className="mt-4 space-y-3 text-sm leading-6 text-pmri-text2">
            {worsened.slice(0, 4).map((item) => <li key={item}>• {item}</li>)}
          </ul>
        </article>
        <article className="rounded-2xl border border-pmri-border bg-white/[0.03] p-5">
          <StatusBadge tone="slate">What remains unclear</StatusBadge>
          <ul className="mt-4 space-y-3 text-sm leading-6 text-pmri-text2">
            {unclearItems.slice(0, 4).map((item) => <li key={item}>• {item}</li>)}
          </ul>
        </article>
      </div>

      <p className="mt-5 rounded-xl border border-pmri-gold/35 bg-pmri-gold/10 p-3 text-sm leading-6 text-pmri-gold">{boundary}</p>
    </section>
  );
}
