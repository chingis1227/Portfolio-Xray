import type { SiteExplanationBundle, SiteExplanationTextItem, StatusTone } from "@/lib/types";

type PublicEvidenceStatus = SiteExplanationTextItem["evidence_status"];

export type PublicSiteExplanationItem = {
  id: string;
  text: string;
  tone: SiteExplanationTextItem["tone"];
  evidenceLabel: string;
  evidenceTone: StatusTone;
};

export type DeveloperSiteExplanationProvenanceItem = {
  id: string;
  level: SiteExplanationTextItem["level"];
  claimType: SiteExplanationTextItem["claim_type"];
  evidenceStatus: SiteExplanationTextItem["evidence_status"];
  sourceRefs: string[];
};

export type DeveloperSiteExplanationProvenance = {
  schemaVersion: SiteExplanationBundle["schema_version"];
  reviewId?: string;
  items: DeveloperSiteExplanationProvenanceItem[];
  warnings: string[];
};

export type PublicSiteExplanationDisplayModel = {
  title: string;
  subtitle: string;
  executiveItems: PublicSiteExplanationItem[];
  evidenceItems: PublicSiteExplanationItem[];
  technicalItems: PublicSiteExplanationItem[];
  developerProvenance?: DeveloperSiteExplanationProvenance;
};

const evidenceStatusPresentation: Record<PublicEvidenceStatus, { label: string; tone: StatusTone }> = {
  available: { label: "Evidence available", tone: "green" },
  limited: { label: "Limited evidence", tone: "amber" },
  missing: { label: "Evidence missing", tone: "amber" },
  preliminary: { label: "Preliminary evidence", tone: "slate" }
};

function toPublicItem(item: SiteExplanationTextItem): PublicSiteExplanationItem {
  const evidence = evidenceStatusPresentation[item.evidence_status] ?? evidenceStatusPresentation.limited;
  return {
    id: item.id,
    text: item.text,
    tone: item.tone,
    evidenceLabel: evidence.label,
    evidenceTone: evidence.tone
  };
}

function toDeveloperProvenanceItem(item: SiteExplanationTextItem): DeveloperSiteExplanationProvenanceItem {
  return {
    id: item.id,
    level: item.level,
    claimType: item.claim_type,
    evidenceStatus: item.evidence_status,
    sourceRefs: item.source_refs.map((ref) => `${ref.artifact}:${ref.field_path}`)
  };
}

export function buildPublicSiteExplanationDisplayModel(
  bundle: SiteExplanationBundle | undefined,
  screen: string,
  fallbackTitle = "Screen explanation",
  options: { includeDeveloperProvenance?: boolean } = {}
): PublicSiteExplanationDisplayModel | null {
  const screenCopy = bundle?.screens?.[screen];
  if (!screenCopy) return null;

  const executiveItems = screenCopy.executive.map(toPublicItem);
  const evidenceItems = screenCopy.evidence.map(toPublicItem);
  const technicalItems = screenCopy.technical.map(toPublicItem);
  const hasAnyCopy = executiveItems.length || evidenceItems.length || technicalItems.length;
  if (!hasAnyCopy) return null;

  return {
    title: fallbackTitle,
    subtitle: "Evidence-backed explanation for the current decision step. Supporting detail stays separated from the main conclusion.",
    executiveItems,
    evidenceItems,
    technicalItems,
    developerProvenance: options.includeDeveloperProvenance && bundle ? {
      schemaVersion: bundle.schema_version,
      reviewId: bundle.review_id,
      items: [
        ...screenCopy.executive.map(toDeveloperProvenanceItem),
        ...screenCopy.evidence.map(toDeveloperProvenanceItem),
        ...screenCopy.technical.map(toDeveloperProvenanceItem)
      ],
      warnings: bundle.warnings ?? []
    } : undefined
  };
}
