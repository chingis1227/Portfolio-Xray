export type StatusTone = "blue" | "gold" | "green" | "amber" | "red" | "slate";

export type JourneyStepStatus = "locked" | "available" | "active" | "completed";

export type JourneyStep = {
  id: string;
  label: string;
  href: string;
  shortLabel: string;
  lockReason: string;
};

export type Metric = {
  label: string;
  value: string;
  detail?: string;
  tone?: StatusTone;
  delta?: string;
};

export type EvidenceItem = {
  type: string;
  title: string;
  status: string;
  summary: string;
  source: string;
  tone: StatusTone;
};

export type SiteExplanationLevel = "executive" | "evidence" | "technical";

export type SiteExplanationTextItem = {
  id: string;
  level: SiteExplanationLevel;
  text: string;
  tone: "neutral" | "caution" | "risk" | "positive";
  evidence_status: "available" | "limited" | "missing" | "preliminary";
  claim_type: "material_claim" | "boundary_note" | "empty_state";
  source_refs: Array<{ artifact: string; field_path: string }>;
};

export type SiteExplanationScreen = {
  executive: SiteExplanationTextItem[];
  evidence: SiteExplanationTextItem[];
  technical: SiteExplanationTextItem[];
};

export type SiteExplanationBundle = {
  schema_version: "site_explanation_bundle_v1";
  review_id?: string;
  screens: Record<string, SiteExplanationScreen>;
  warnings?: string[];
};

export type Holding = {
  ticker: string;
  instrument: string;
  weight: number;
};

export type Hypothesis = {
  id: string;
  title: string;
  targetProblem: string;
  expectedTradeoff: string;
  methodId: string;
  evidenceSource: string;
  status: string;
  testType?: string;
  suggestedMethods?: string[];
  successCriteria?: string[];
  decisionBoundary?: string;
};

export type ComparisonMetric = {
  metric: string;
  current: string;
  candidate: string;
  direction: string;
  tradeoff: string;
  tone: StatusTone;
};
