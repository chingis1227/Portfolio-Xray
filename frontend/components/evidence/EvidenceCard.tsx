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
          <p className="pmri-label">{item.type}</p>
          <h3 className="pmri-heading-section mt-2 text-lg text-pmri-text">{item.title}</h3>
        </div>
        <StatusBadge tone={item.tone}>{item.status}</StatusBadge>
      </div>
      <p className="mt-4 text-sm leading-6 text-pmri-text2">{item.summary}</p>
      <div className="mt-5 border-t border-pmri-border/40 pt-3">
        <p className="text-sm text-pmri-muted">Supporting evidence: <span className="text-pmri-text2">{item.source}</span></p>
      </div>
    </article>
  );
}

