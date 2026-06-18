import type { ReactNode } from "react";
import type { StatusTone } from "@/lib/types";
import { StatusBadge } from "@/components/ui/StatusBadge";

export type EvidenceSummaryItem = {
  label: string;
  value: ReactNode;
  tone?: StatusTone;
};

type EvidenceSummaryProps = {
  title?: string;
  description?: string;
  items: EvidenceSummaryItem[];
};

export function EvidenceSummary({
  title = "Evidence summary",
  description,
  items
}: EvidenceSummaryProps) {
  const visibleItems = items
    .filter((item) => {
      const label = String(item.label).toLowerCase();
      return !label.includes("boundary") && !label.includes("evidence quality");
    })
    .slice(0, 4);

  return (
    <section className="pmri-card rounded-3xl p-5 md:p-6">
      <div className="flex flex-col gap-2 md:flex-row md:items-end md:justify-between">
        <div>
          <p className="pmri-type-meta text-pmri-text2">Primary evidence</p>
          <h2 className="pmri-type-section-title mt-2 text-pmri-text">{title}</h2>
          {description ? <p className="mt-2 max-w-3xl text-sm leading-6 text-pmri-text2">{description}</p> : null}
        </div>
      </div>
      <div className="mt-5 grid gap-0 overflow-hidden rounded-2xl border border-pmri-border/50 bg-white/[0.018] md:grid-cols-4">
        {visibleItems.length ? visibleItems.map((item, index) => (
          <div key={`${item.label}-${index}`} className="border-b border-pmri-border/35 p-4 last:border-b-0 md:border-b-0 md:border-r md:last:border-r-0 md:border-pmri-border/35">
            <div className="flex items-start justify-between gap-3">
              <p className="pmri-type-meta text-pmri-text2">{item.label}</p>
              {item.tone === "red" || item.tone === "amber" ? (
                <StatusBadge tone={item.tone}>{item.tone === "red" ? "Material" : "Watch"}</StatusBadge>
              ) : null}
            </div>
            <p className="mt-3 text-sm leading-6 text-pmri-text2">{item.value}</p>
          </div>
        )) : (
          <p className="p-5 text-sm leading-6 text-pmri-text2 md:col-span-4">Evidence is unavailable for this review.</p>
        )}
      </div>
    </section>
  );
}
