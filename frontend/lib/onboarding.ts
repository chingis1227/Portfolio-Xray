import type { ClientFitInput } from "@/lib/generated/api-types";

export type OnboardingInvestorType = "capital_guardian" | "balanced_builder" | "growth_seeker" | "risk_mapper";
export type OnboardingObjective = "preserve" | "balanced" | "growth" | "understand_risk";
export type OnboardingHorizon = "short" | "medium" | "long";
export type OnboardingRiskComfort = "low" | "medium" | "high";
export type OnboardingDecisionStyle = "evidence_first" | "preserve_unless_clear" | "improve_structure" | "test_growth";
export type OnboardingPrimaryConcern = "concentration" | "drawdown" | "rates" | "inflation" | "unknown";
export type OnboardingStressReaction = "sell_all" | "sell_some" | "hold" | "buy_more";
export type OnboardingReturnNeed = "low" | "moderate" | "high" | "very_high";
export type OnboardingStressLimit = "ten" | "fifteen" | "twenty_five" | "thirty_five";
export type OnboardingConcentrationAction = "reduce_first" | "diagnose_then_adjust" | "hold_if_evidence_ok" | "add_if_compensated";
export type OnboardingLiquidityNeed = "low" | "medium" | "high";

export type OnboardingState = {
  name: string;
  investorType: OnboardingInvestorType;
  objective: OnboardingObjective;
  horizon: OnboardingHorizon;
  riskComfort: OnboardingRiskComfort;
  decisionStyle: OnboardingDecisionStyle;
  primaryConcern: OnboardingPrimaryConcern;
  stressReaction: OnboardingStressReaction;
  returnNeed: OnboardingReturnNeed;
  stressLimit: OnboardingStressLimit;
  concentrationAction: OnboardingConcentrationAction;
  liquidityNeed: OnboardingLiquidityNeed;
  updatedAt?: string;
};

type PresetId = NonNullable<ClientFitInput["preset_id"]>;

type PresetDefinition = {
  id: PresetId;
  label: string;
  returnRange: { min: number; max: number };
  volRange: { min: number; max: number };
  drawdown: number;
  horizon: number;
};

export const ONBOARDING_STORAGE_KEY = "pmri.onboarding.v1";
export const ONBOARDING_COMPLETED_STORAGE_KEY = "pmri.onboarding.completed.v1";

export const defaultOnboardingState: OnboardingState = {
  name: "",
  investorType: "balanced_builder",
  objective: "balanced",
  horizon: "medium",
  riskComfort: "medium",
  decisionStyle: "evidence_first",
  primaryConcern: "unknown",
  stressReaction: "hold",
  returnNeed: "moderate",
  stressLimit: "fifteen",
  concentrationAction: "diagnose_then_adjust",
  liquidityNeed: "medium"
};

export const clientFitPresets: Record<PresetId, PresetDefinition> = {
  ultra_conservative: {
    id: "ultra_conservative",
    label: "Ultra Conservative",
    returnRange: { min: 0.02, max: 0.04 },
    volRange: { min: 0.02, max: 0.05 },
    drawdown: -0.10,
    horizon: 2
  },
  conservative: {
    id: "conservative",
    label: "Conservative",
    returnRange: { min: 0.03, max: 0.06 },
    volRange: { min: 0.04, max: 0.07 },
    drawdown: -0.15,
    horizon: 4
  },
  balanced: {
    id: "balanced",
    label: "Balanced",
    returnRange: { min: 0.05, max: 0.07 },
    volRange: { min: 0.07, max: 0.10 },
    drawdown: -0.20,
    horizon: 7
  },
  growth: {
    id: "growth",
    label: "Growth",
    returnRange: { min: 0.07, max: 0.10 },
    volRange: { min: 0.10, max: 0.14 },
    drawdown: -0.275,
    horizon: 10
  },
  aggressive: {
    id: "aggressive",
    label: "Aggressive",
    returnRange: { min: 0.10, max: 0.20 },
    volRange: { min: 0.14, max: 0.20 },
    drawdown: -0.35,
    horizon: 12
  }
};

export const investorTypeOptions: Array<{
  id: OnboardingInvestorType;
  title: string;
  summary: string;
  style: string;
  risk: string;
  horizon: string;
}> = [
  {
    id: "capital_guardian",
    title: "Capital Guardian",
    summary: "You want the diagnostic room to watch drawdown, stability, and downside exposure first.",
    style: "Preservation first",
    risk: "Low",
    horizon: "Short to medium"
  },
  {
    id: "balanced_builder",
    title: "Balanced Builder",
    summary: "You want growth, but the test should keep risk concentration and stress behavior visible.",
    style: "Balanced",
    risk: "Moderate",
    horizon: "Flexible"
  },
  {
    id: "growth_seeker",
    title: "Growth Seeker",
    summary: "You accept wider swings if the portfolio structure is transparent and evidence-backed.",
    style: "Growth-oriented",
    risk: "Higher",
    horizon: "Long"
  },
  {
    id: "risk_mapper",
    title: "Risk Mapper",
    summary: "You mainly want to understand what currently drives the portfolio before testing changes.",
    style: "Diagnostic",
    risk: "Contextual",
    horizon: "Flexible"
  }
];

export function readOnboardingState(): OnboardingState {
  if (typeof window === "undefined") return defaultOnboardingState;
  try {
    const raw = window.localStorage.getItem(ONBOARDING_STORAGE_KEY);
    if (!raw) return defaultOnboardingState;
    const parsed = JSON.parse(raw) as Partial<OnboardingState>;
    return {
      ...defaultOnboardingState,
      ...parsed,
      name: typeof parsed.name === "string" ? parsed.name : ""
    };
  } catch (_error) {
    return defaultOnboardingState;
  }
}

export function writeOnboardingState(next: Partial<OnboardingState>) {
  if (typeof window === "undefined") return;
  const current = readOnboardingState();
  window.localStorage.setItem(ONBOARDING_STORAGE_KEY, JSON.stringify({
    ...current,
    ...next,
    updatedAt: new Date().toISOString()
  }));
}

export function isOnboardingComplete(state: Partial<OnboardingState> | null | undefined): state is OnboardingState {
  if (!state) return false;
  return Boolean(
    typeof state.name === "string"
    && state.name.trim()
    && state.investorType
    && state.objective
    && state.horizon
    && state.riskComfort
    && state.decisionStyle
    && state.primaryConcern
  );
}

export function markOnboardingComplete() {
  if (typeof window === "undefined") return;
  window.localStorage.setItem(ONBOARDING_COMPLETED_STORAGE_KEY, "true");
}

export function hasCompletedOnboarding() {
  if (typeof window === "undefined") return false;
  return window.localStorage.getItem(ONBOARDING_COMPLETED_STORAGE_KEY) === "true"
    && isOnboardingComplete(readOnboardingState());
}

export function restoreOnboardingStateFromMetadata(metadata: unknown) {
  if (typeof window === "undefined" || !metadata || typeof metadata !== "object") return false;
  const record = metadata as Record<string, unknown>;
  if (record.pmri_onboarding_completed !== true || !record.pmri_onboarding || typeof record.pmri_onboarding !== "object") {
    return false;
  }
  const candidate = record.pmri_onboarding as Partial<OnboardingState>;
  if (!isOnboardingComplete(candidate)) return false;
  writeOnboardingState(candidate);
  markOnboardingComplete();
  return true;
}

function presetIdFromScore(score: number): PresetId {
  if (score <= -5) return "ultra_conservative";
  if (score <= -2) return "conservative";
  if (score >= 6) return "aggressive";
  if (score >= 3) return "growth";
  return "balanced";
}

function scoreOnboardingState(state: OnboardingState) {
  let score = 0;

  const stressReactionScore: Record<OnboardingStressReaction, number> = {
    sell_all: -4,
    sell_some: -2,
    hold: 1,
    buy_more: 3
  };
  const horizonScore: Record<OnboardingHorizon, number> = { short: -2, medium: 0, long: 2 };
  const stressLimitScore: Record<OnboardingStressLimit, number> = { ten: -3, fifteen: -1, twenty_five: 2, thirty_five: 4 };
  const returnNeedScore: Record<OnboardingReturnNeed, number> = { low: -2, moderate: 0, high: 2, very_high: 4 };
  const concentrationScore: Record<OnboardingConcentrationAction, number> = {
    reduce_first: -2,
    diagnose_then_adjust: 0,
    hold_if_evidence_ok: 1,
    add_if_compensated: 2
  };

  score += stressReactionScore[state.stressReaction] ?? 0;
  score += horizonScore[state.horizon] ?? 0;
  score += stressLimitScore[state.stressLimit] ?? 0;
  score += returnNeedScore[state.returnNeed] ?? 0;
  score += concentrationScore[state.concentrationAction] ?? 0;

  return score;
}

function presetForState(state: OnboardingState): PresetDefinition {
  return clientFitPresets[presetIdFromScore(scoreOnboardingState(state))];
}

export function inferClientFitPresetIdFromTargets(values: {
  returnMin: number;
  returnMax: number;
  volMin: number;
  volMax: number;
  drawdown: number;
  horizonYears: number;
}): PresetId {
  let score = 0;

  if (values.drawdown >= -0.11) score -= 4;
  else if (values.drawdown >= -0.17) score -= 2;
  else if (values.drawdown <= -0.33) score += 4;
  else if (values.drawdown <= -0.25) score += 2;

  if (values.volMax <= 0.055) score -= 3;
  else if (values.volMax <= 0.08) score -= 1;
  else if (values.volMax >= 0.16) score += 3;
  else if (values.volMax >= 0.12) score += 2;

  if (values.returnMin >= 0.10 || values.returnMax >= 0.16) score += 3;
  else if (values.returnMin >= 0.07 || values.returnMax >= 0.10) score += 2;
  else if (values.returnMax <= 0.045) score -= 2;
  else if (values.returnMax <= 0.065) score -= 1;

  if (values.horizonYears <= 3) score -= 2;
  else if (values.horizonYears >= 11) score += 2;
  else if (values.horizonYears >= 8) score += 1;

  return presetIdFromScore(score);
}

export function buildClientFitProfileFromOnboarding(state: OnboardingState): ClientFitInput {
  const preset = presetForState(state);
  const horizonYears = state.horizon === "short" ? Math.min(preset.horizon, 3) : state.horizon === "long" ? Math.max(preset.horizon, 10) : preset.horizon;
  const namePrefix = state.name.trim() ? `${state.name.trim()}'s ` : "";

  return {
    preset_id: preset.id,
    source: "questionnaire",
    source_quality: "high",
    source_quality_reason: `${namePrefix}risk-behavior intake scored stress reaction, horizon, drawdown limit, return need, and concentration response before portfolio diagnosis.`,
    horizon_years: horizonYears,
    target_return_range: preset.returnRange,
    target_vol_range: preset.volRange,
    target_max_drawdown_pct: preset.drawdown
  };
}

export function profileLabelForOnboarding(state: OnboardingState) {
  return presetForState(state).label;
}

export function diagnosticEmphasisForOnboarding(state: OnboardingState) {
  switch (state.primaryConcern) {
    case "concentration":
      return "concentration and hidden exposure checks";
    case "drawdown":
      return "drawdown and stress-loss evidence";
    case "rates":
      return "rate sensitivity and bond stress behavior";
    case "inflation":
      return "inflation, real-asset, and currency resilience";
    case "unknown":
    default:
      return "broad portfolio diagnosis and Stress Lab evidence";
  }
}
