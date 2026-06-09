import { StatusBadge } from "@/components/ui/StatusBadge";
import type { StressScorecardItem } from "./stressLabTypes";
import { StressSectionHeader } from "./stressLabUi";

export function StressScorecardPanel({ items }: { items: StressScorecardItem[] }) {
  return (
    <section id="stress-scorecard" className="pmri-card rounded-3xl p-5 md:p-7">
      <StressSectionHeader
        eyebrow="30-second stress view"
        title="Executive Stress Scorecard"
        body="A compact readout of how the current portfolio behaves before any candidate test."
        badge="Current portfolio only"
        badgeTone="blue"
      />
      <div className="mt-6 grid gap-4 md:grid-cols-2 xl:grid-cols-3">
        {items.map((item) => (
          <article key={item.label} className="pmri-hover-panel rounded-2xl border border-pmri-border/55 bg-white/[0.024] p-4">
            <div className="flex items-start justify-between gap-3">
              <p className="pmri-label">{item.label}</p>
              <StatusBadge tone={item.tone}>{item.tone === "red" ? "Stress area" : item.tone === "green" ? "Offset visible" : "Review"}</StatusBadge>
            </div>
            <p className="data-figure mt-4 text-xl font-medium text-pmri-text">{item.value}</p>
            <p className="mt-2 text-sm leading-6 text-pmri-text2">{item.detail}</p>
          </article>
        ))}
      </div>
    </section>
  );
}
