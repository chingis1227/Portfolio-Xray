import type { ReactNode } from "react";
import type { StatusTone } from "@/lib/types";

export type EvidenceSummaryItem = {
  label: string;
  value: ReactNode;
  tone?: StatusTone;
};

type EvidenceSummaryProps = {
  title?: string;
  description?: string;
  items: EvidenceSummaryItem[];
  showHeader?: boolean;
  emptyMessage?: string;
};

function valueToneClass(tone?: StatusTone) {
  if (tone === "red") return "text-pmri-risk";
  if (tone === "amber") return "text-pmri-amber";
  if (tone === "blue") return "text-pmri-blueSoft";
  return "text-pmri-text2";
}

export function EvidenceSummary({
  title = "Evidence summary",
  description,
  items,
  showHeader = true,
  emptyMessage = "This review does not yet include enough evidence for this conclusion; use the next-step guidance before relying on this screen."
}: EvidenceSummaryProps) {
  const visibleItems = items.slice(0, 4);

  return (
    <section className={showHeader ? "space-y-4" : undefined}>
      {showHeader ? (
        <div className="flex flex-col gap-2 md:flex-row md:items-end md:justify-between">
          <div>
            <p className="text-[0.68rem] font-medium tracking-[0.08em] text-pmri-muted">Primary evidence</p>
            <h2 className="pmri-type-section-title mt-2 text-pmri-text">{title}</h2>
            {description ? <p className="mt-2 max-w-3xl text-sm leading-6 text-pmri-text2">{description}</p> : null}
          </div>
        </div>
      ) : null}
      <div className="pmri-evidence-strip grid gap-0 md:grid-cols-4">
        {visibleItems.length ? visibleItems.map((item, index) => (
          <div key={`${item.label}-${index}`} className="border-b border-white/[0.055] px-4 py-3.5 last:border-b-0 md:border-b-0 md:border-r md:last:border-r-0">
            <p className="text-[0.68rem] font-medium tracking-[0.055em] text-pmri-muted">{item.label}</p>
            <p className={`data-figure mt-2 text-sm font-semibold leading-5 ${valueToneClass(item.tone)}`}>
              {item.value}
            </p>
          </div>
        )) : (
          <p className="p-5 text-sm leading-6 text-pmri-text2 md:col-span-4">{emptyMessage}</p>
        )}
      </div>
    </section>
  );
}
