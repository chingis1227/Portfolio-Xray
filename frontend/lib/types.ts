export type StatusTone = "blue" | "gold" | "green" | "amber" | "red" | "slate";

export type JourneyStep = {
  id: string;
  label: string;
  href: string;
  shortLabel: string;
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
};

export type ComparisonMetric = {
  metric: string;
  current: string;
  candidate: string;
  direction: string;
  tradeoff: string;
  tone: StatusTone;
};
