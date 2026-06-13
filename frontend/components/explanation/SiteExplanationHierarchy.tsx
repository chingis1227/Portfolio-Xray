import type { SiteExplanationBundle, SiteExplanationScreen, SiteExplanationTextItem } from "@/lib/types";
import { StatusBadge } from "@/components/ui/StatusBadge";

type Props = {
  bundle?: SiteExplanationBundle;
  screen: string;
  fallbackTitle?: string;
};

const toneClass: Record<SiteExplanationTextItem["tone"], string> = {
  neutral: "border-pmri-border bg-white/[0.025]",
  caution: "border-pmri-amber/35 bg-pmri-amber/10",
  risk: "border-pmri-red/35 bg-pmri-red/10",
  positive: "border-pmri-green/35 bg-pmri-green/10"
};

function labelForEvidenceStatus(status: string) {
  return status.replace(/_/g, " ");
}

function ExplanationItems({ items, compact = false }: { items: SiteExplanationTextItem[]; compact?: boolean }) {
  if (!items.length) return null;
  return (
    <div className={compact ? "space-y-2" : "grid gap-3 md:grid-cols-2"}>
      {items.map((item) => (
        <article key={item.id} className={`rounded-2xl border p-4 ${toneClass[item.tone] ?? toneClass.neutral}`}>
          <div className="flex items-start justify-between gap-3">
            <p className="text-sm leading-6 text-pmri-text2">{item.text}</p>
            <StatusBadge tone={item.evidence_status === "available" ? "green" : item.evidence_status === "missing" ? "amber" : "slate"}>
              {labelForEvidenceStatus(item.evidence_status)}
            </StatusBadge>
          </div>
          {item.source_refs.length ? (
            <p className="mt-3 text-xs leading-5 text-pmri-muted">
              Source: {item.source_refs.map((ref) => `${ref.artifact}:${ref.field_path}`).join(" · ")}
            </p>
          ) : null}
        </article>
      ))}
    </div>
  );
}

export function SiteExplanationHierarchy({ bundle, screen, fallbackTitle = "Screen explanation" }: Props) {
  const screenCopy: SiteExplanationScreen | undefined = bundle?.screens?.[screen];
  if (!screenCopy) return null;
  const hasAnyCopy = screenCopy.executive.length || screenCopy.evidence.length || screenCopy.technical.length;
  if (!hasAnyCopy) return null;

  return (
    <section className="mb-6 rounded-3xl border border-pmri-border/55 bg-pmri-secondary/40 p-5 shadow-decision">
      <div className="flex flex-col gap-3 md:flex-row md:items-start md:justify-between">
        <div>
          <p className="pmri-label text-pmri-blueSoft">Explanation hierarchy</p>
          <h2 className="mt-2 pmri-heading-section text-xl text-pmri-text">{fallbackTitle}</h2>
          <p className="mt-2 max-w-3xl text-sm leading-7 text-pmri-muted">
            Executive text is shown first. Supporting evidence follows. Technical details stay collapsed until opened.
          </p>
        </div>
        <StatusBadge tone="blue">site_explanation_bundle_v1</StatusBadge>
      </div>

      <div className="mt-5 space-y-5">
        <ExplanationItems items={screenCopy.executive} compact />
        {screenCopy.evidence.length ? (
          <div>
            <p className="pmri-label mb-3">Supporting evidence</p>
            <ExplanationItems items={screenCopy.evidence} />
          </div>
        ) : null}
        {screenCopy.technical.length ? (
          <details className="rounded-2xl border border-pmri-border bg-white/[0.02] p-4">
            <summary className="cursor-pointer text-sm font-medium text-pmri-text">Technical details and limitations</summary>
            <div className="mt-4">
              <ExplanationItems items={screenCopy.technical} />
            </div>
          </details>
        ) : null}
      </div>
    </section>
  );
}
