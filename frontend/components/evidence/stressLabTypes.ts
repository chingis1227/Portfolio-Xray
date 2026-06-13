import type { StatusTone } from "@/lib/types";

export type ScenarioKind = "synthetic" | "historical";

export type ContributionStatus = "Hurt" | "Helped" | "Neutral";

export type ContributionRow = {
  ticker: string;
  value: number;
  status: ContributionStatus;
};

export type FactorContributionRow = {
  factor: string;
  value: number;
  status: "Loss driver" | "Offset" | "Neutral";
};

export type StressScenarioTile = {
  id: string;
  displayName: string;
  groupLabel: "Synthetic shock" | "Historical episode";
  kind: ScenarioKind;
  portfolioLossPct: number | null;
  drawdownPct: number | null;
  availability: string;
  severityLabel: string;
  severityTone: StatusTone;
  evidenceQualityLabel: string;
  evidenceTone: StatusTone;
  isWorst: boolean;
  dataNote...: string;
};

export type StressScenarioDetail = StressScenarioTile & {
  lossContributions: ContributionRow[];
  assetsHurt: ContributionRow[];
  assetsHelped: ContributionRow[];
  factorAttribution: FactorContributionRow[];
  interpretation: string;
  limitation...: string;
};

export type StressScorecardItem = {
  label: string;
  value: string;
  detail: string;
  tone: StatusTone;
};

export type HedgeGapSummary = {
  displayName: string;
  scenarioDisplayName: string;
  grossLossFromHurt: number | null;
  positiveContributionFromHelped: number | null;
  offsetCoverageRatio: number | null;
  statusLabel: string;
  statusTone: StatusTone;
  interpretation: string;
  assetsHurt: ContributionRow[];
  assetsHelped: ContributionRow[];
};

export type XRayConfirmationRow = {
  label: string;
  detail: string;
  tone: StatusTone;
};

export type StressLimitations = {
  headline: string;
  evidenceQualityLabel: string;
  evidenceTone: StatusTone;
  whatLimited: string[];
  whyItMatters: string[];
  stillUsable: string[];
};

export type StressLabModel = {
  headerStatusLabel: string;
  scorecard: StressScorecardItem[];
  syntheticScenarios: StressScenarioDetail[];
  historicalScenarios: StressScenarioDetail[];
  selectedScenarioId: string;
  hedgeGap: HedgeGapSummary;
  xrayConfirmation: {
    confirmed: XRayConfirmationRow[];
    lessMaterial: XRayConfirmationRow[];
    insufficientData: XRayConfirmationRow[];
    note: string;
  };
  limitations: StressLimitations;
};
