import type { SiteExplanationBundle, SiteExplanationTextItem, StatusTone } from "@/lib/types";
import { containsPublicTechnicalText, sanitizePublicDisplayText } from "@/lib/displayLabels";

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
  available: { label: "Evidence available", tone: "slate" },
  limited: { label: "Limited evidence", tone: "amber" },
  missing: { label: "Evidence unavailable", tone: "amber" },
  preliminary: { label: "Preliminary evidence", tone: "slate" }
};

const unsafePublicTextPattern = /\b(?:stress_report|portfolio_xray|problem_classification|candidate_generation|current_vs_candidate|decision_verdict|site_explanation_bundle|schema_version|field_path|source_refs|artifact|frontend_review|trade now|must rebalance|best portfolio|suitability approved)\b|\.json\b|\bbuy\b|\bsell\b(?!-off)/i;

function publicExplanationText(value: string) {
  const normalized = sanitizePublicDisplayText(value, "Some supporting comparison evidence is incomplete.").replace(/\s+/g, " ").trim();
  if (!normalized || unsafePublicTextPattern.test(normalized) || containsPublicTechnicalText(normalized)) {
    return "Some supporting comparison evidence is incomplete.";
  }
  return normalized;
}

function toPublicItem(item: SiteExplanationTextItem): PublicSiteExplanationItem {
  const evidence = evidenceStatusPresentation[item.evidence_status] ?? evidenceStatusPresentation.limited;
  return {
    id: item.id,
    text: publicExplanationText(item.text),
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
