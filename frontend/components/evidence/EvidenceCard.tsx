import type { EvidenceItem } from "@/lib/types";
import { StatusBadge } from "@/components/ui/StatusBadge";

type EvidenceCardProps = {
  item: EvidenceItem;
};

export function EvidenceCard({ item }: EvidenceCardProps) {
  return (
    <article className="pmri-card rounded-2xl p-5">
      <div className="flex items-start justify-between gap-4">
        <div>
          <p className="text-xs font-semibold uppercase tracking-[0.16em] text-pmri-muted">{item.type}</p>
          <h3 className="mt-2 text-lg font-semibold text-pmri-text">{item.title}</h3>
        </div>
        <StatusBadge tone={item.tone}>{item.status}</StatusBadge>
      </div>
      <p className="mt-4 text-sm leading-6 text-pmri-text2">{item.summary}</p>
      <div className="mt-5 border-t border-pmri-border pt-3">
        <p className="text-xs text-pmri-muted">Evidence source: <span className="text-pmri-text2">{item.source}</span></p>
      </div>
    </article>
  );
}

