import type { SiteExplanationBundle } from "@/lib/types";
import { StatusBadge } from "@/components/ui/StatusBadge";
import {
  buildPublicSiteExplanationDisplayModel,
  type DeveloperSiteExplanationProvenance,
  type PublicSiteExplanationItem
} from "@/lib/siteExplanationPresenter";

type Props = {
  bundle?: SiteExplanationBundle;
  screen: string;
  fallbackTitle?: string;
  showDeveloperProvenance?: boolean;
};

const toneClass: Record<PublicSiteExplanationItem["tone"], string> = {
  neutral: "border-pmri-border bg-white/[0.025]",
  caution: "border-pmri-amber/35 bg-pmri-amber/10",
  risk: "border-pmri-red/35 bg-pmri-red/10",
  positive: "border-pmri-green/35 bg-pmri-green/10"
};

function ExplanationItems({ items, compact = false }: { items: PublicSiteExplanationItem[]; compact?: boolean }) {
  if (!items.length) return null;
  return (
    <div className={compact ? "space-y-2" : "grid gap-3 md:grid-cols-2"}>
      {items.map((item) => (
        <article key={item.id} className={`rounded-2xl border p-4 ${toneClass[item.tone] ?? toneClass.neutral}`}>
          <div className="flex items-start justify-between gap-3">
            <p className="text-sm leading-6 text-pmri-text2">{item.text}</p>
            <StatusBadge tone={item.evidenceTone}>
              {item.evidenceLabel}
            </StatusBadge>
          </div>
        </article>
      ))}
    </div>
  );
}

function DeveloperProvenanceDetails({ provenance }: { provenance?: DeveloperSiteExplanationProvenance }) {
  if (!provenance) return null;

  return (
    <details className="rounded-2xl border border-dashed border-pmri-border bg-white/[0.015] p-4">
      <summary className="cursor-pointer text-sm font-medium text-pmri-muted">
        Developer provenance
      </summary>
      <div className="mt-4 space-y-3 text-xs leading-5 text-pmri-muted">
        <div className="flex flex-wrap gap-2">
          <span className="rounded-full border border-pmri-border px-2 py-1">
            schema: {provenance.schemaVersion}
          </span>
          {provenance.reviewId ? (
            <span className="rounded-full border border-pmri-border px-2 py-1">
              review: {provenance.reviewId}
            </span>
          ) : null}
        </div>
        {provenance.items.map((item) => (
          <div key={item.id} className="rounded-xl border border-pmri-border/70 p-3">
            <div className="font-medium text-pmri-text2">{item.id}</div>
            <div className="mt-1">
              {item.level} · {item.claimType} · {item.evidenceStatus}
            </div>
            {item.sourceRefs.length ? (
              <ul className="mt-2 list-disc space-y-1 pl-5">
                {item.sourceRefs.map((sourceRef) => (
                  <li key={sourceRef} className="break-all">{sourceRef}</li>
                ))}
              </ul>
            ) : (
              <p className="mt-2">No audit references recorded for this text item.</p>
            )}
          </div>
        ))}
        {provenance.warnings.length ? (
          <div>
            <div className="font-medium text-pmri-text2">Warnings</div>
            <ul className="mt-2 list-disc space-y-1 pl-5">
              {provenance.warnings.map((warning) => (
                <li key={warning}>{warning}</li>
              ))}
            </ul>
          </div>
        ) : null}
      </div>
    </details>
  );
}

export function SiteExplanationHierarchy({
  bundle,
  screen,
  fallbackTitle = "Screen explanation",
  showDeveloperProvenance = false
}: Props) {
  const displayModel = buildPublicSiteExplanationDisplayModel(bundle, screen, fallbackTitle, {
    includeDeveloperProvenance: showDeveloperProvenance
  });
  if (!displayModel) return null;

  return (
    <section className="mb-6 rounded-3xl border border-pmri-border/55 bg-pmri-secondary/40 p-5 shadow-decision">
      <div className="flex flex-col gap-3 md:flex-row md:items-start md:justify-between">
        <div>
          <p className="pmri-label text-pmri-blueSoft">Decision evidence</p>
          <h2 className="mt-2 pmri-heading-section text-xl text-pmri-text">{displayModel.title}</h2>
          <p className="mt-2 max-w-3xl text-sm leading-7 text-pmri-muted">
            {displayModel.subtitle}
          </p>
        </div>
      </div>

      <div className="mt-5 space-y-5">
        <ExplanationItems items={displayModel.executiveItems} compact />
        {displayModel.evidenceItems.length ? (
          <div>
            <p className="pmri-label mb-3">Supporting evidence</p>
            <ExplanationItems items={displayModel.evidenceItems} />
          </div>
        ) : null}
        {displayModel.technicalItems.length ? (
          <details className="rounded-2xl border border-pmri-border bg-white/[0.02] p-4">
            <summary className="cursor-pointer text-sm font-medium text-pmri-text">Technical details and limitations</summary>
            <div className="mt-4">
              <ExplanationItems items={displayModel.technicalItems} />
            </div>
          </details>
        ) : null}
        {showDeveloperProvenance ? (
          <DeveloperProvenanceDetails provenance={displayModel.developerProvenance} />
        ) : null}
      </div>
    </section>
  );
}
