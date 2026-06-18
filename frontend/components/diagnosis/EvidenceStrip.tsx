import { EvidenceItem } from "@/components/ui/EvidenceItem";
import type { EvidenceSummaryItem } from "@/components/ui/EvidenceSummary";

export function EvidenceStrip({ items }: { items: EvidenceSummaryItem[] }) {
  const visibleItems = items.slice(0, 4);
  return (
    <section className="pmri-evidence-strip grid gap-0 md:grid-cols-4" aria-label="Primary diagnosis evidence">
      {visibleItems.length ? visibleItems.map((item, index) => (
        <div key={`${item.label}-${index}`} className="border-b border-white/[0.055] last:border-b-0 md:border-b-0 md:border-r md:last:border-r-0">
          <EvidenceItem label={item.label} value={item.value} tone={item.tone} />
        </div>
      )) : (
        <p className="p-5 text-sm leading-6 text-pmri-text2 md:col-span-4">Evidence is unavailable for this review.</p>
      )}
    </section>
  );
}
