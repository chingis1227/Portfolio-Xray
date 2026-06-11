import { StatusBadge } from "@/components/ui/StatusBadge";
import type { StressScorecardItem } from "./stressLabTypes";
import { StressSectionHeader } from "./stressLabUi";

function displayLabel(label: string) {
  if (label === "Assets that helped") return "Assets that helped in worst scenario";
  if (label === "Data coverage") return "Data confidence";
  return label;
}

function badgeLabel(item: StressScorecardItem) {
  if (item.label === "Worst synthetic scenario") return "Most damaging";
  if (item.label === "Main hedge gap") {
    if (item.detail.toLowerCase().includes("unavailable")) return "Insufficient data";
    if (item.tone === "green") return "Partial offset";
    if (item.tone === "amber") return "Partial offset";
    if (item.tone === "red") return "Weak offset";
    return null;
  }
  if (item.label === "Data coverage" || item.label === "Data confidence") return item.value;
  return null;
}

export function StressScorecardPanel({ items }: { items: StressScorecardItem[] }) {
  return (
    <section id="stress-scorecard" className="pmri-card rounded-3xl p-5 md:p-7">
      <StressSectionHeader
        eyebrow="30-second stress view"
        title="Executive Stress Scorecard"
        body="A compact readout of the worst scenario, main drivers, offset behavior, and data confidence."
      />
      <div className="mt-6 grid gap-4 md:grid-cols-2 xl:grid-cols-3">
        {items.map((item) => (
          <article key={item.label} className="pmri-hover-panel rounded-2xl border border-pmri-border/55 bg-white/[0.024] p-4">
            <div className="flex items-start justify-between gap-3">
              <p className="pmri-label">{displayLabel(item.label)}</p>
              {badgeLabel(item) ? <StatusBadge tone={item.tone}>{badgeLabel(item)}</StatusBadge> : null}
            </div>
            <p className="data-figure mt-4 text-xl font-medium text-pmri-text">{item.value}</p>
            <p className="mt-2 text-sm leading-6 text-pmri-text2">{item.detail}</p>
          </article>
        ))}
      </div>
    </section>
  );
}
