import { StatusBadge } from "@/components/ui/StatusBadge";
import type { StressLimitations } from "./stressLabTypes";
import { StressSectionHeader } from "./stressLabUi";

function LimitationColumn({ title, rows }: { title: string; rows: string[] }) {
  return (
    <article className="rounded-2xl border border-pmri-border/55 bg-white/[0.024] p-5">
      <h3 className="text-sm font-semibold text-pmri-text">{title}</h3>
      <ul className="mt-4 space-y-3 text-sm leading-6 text-pmri-text2">
        {rows.map((row) => (
          <li key={row} className="flex gap-2">
            <span className="mt-2 h-1.5 w-1.5 shrink-0 rounded-full bg-pmri-borderSoft" />
            <span>{row}</span>
          </li>
        ))}
      </ul>
    </article>
  );
}

export function DataLimitationsPanel({ limitations }: { limitations: StressLimitations }) {
  return (
    <section id="data-limitations" className="pmri-card rounded-3xl p-5 md:p-7">
      <StressSectionHeader
        eyebrow="Data quality"
        title="Data quality / limitations"
        body="Client-ready view of what is limited, why it matters, and what can still be used."
        badge={limitations.evidenceQualityLabel}
        badgeTone={limitations.evidenceTone}
      />
      <div className="mt-5 flex flex-wrap gap-2">
        <StatusBadge tone="slate">Current portfolio review</StatusBadge>
        <StatusBadge tone="blue">Candidate not tested</StatusBadge>
        <StatusBadge tone={limitations.evidenceTone}>Data limitation</StatusBadge>
      </div>
      <p className="mt-5 rounded-2xl border border-pmri-border/55 bg-black/10 p-4 text-sm leading-6 text-pmri-text2">
        {limitations.headline}
      </p>
      <div className="mt-6 grid gap-4 lg:grid-cols-3">
        <LimitationColumn title="What is limited" rows={limitations.whatLimited} />
        <LimitationColumn title="Why it matters" rows={limitations.whyItMatters} />
        <LimitationColumn title="Still usable" rows={limitations.stillUsable} />
      </div>
    </section>
  );
}
