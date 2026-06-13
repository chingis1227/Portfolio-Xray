import type { ClientFitInput } from "@/lib/generated/api-types";

export type OnboardingInvestorType = "capital_guardian" | "balanced_builder" | "growth_seeker" | "risk_mapper";
export type OnboardingObjective = "preserve" | "balanced" | "growth" | "understand_risk";
export type OnboardingHorizon = "short" | "medium" | "long";
export type OnboardingRiskComfort = "low" | "medium" | "high";
export type OnboardingDecisionStyle = "evidence_first" | "preserve_unless_clear" | "improve_structure" | "test_growth";
export type OnboardingPrimaryConcern = "concentration" | "drawdown" | "rates" | "inflation" | "unknown";
export type OnboardingLiquidityNeed = "low" | "medium" | "high";

export type OnboardingState = {
  name: string;
  investorType: OnboardingInvestorType;
  objective: OnboardingObjective;
  horizon: OnboardingHorizon;
  riskComfort: OnboardingRiskComfort;
  decisionStyle: OnboardingDecisionStyle;
  primaryConcern: OnboardingPrimaryConcern;
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

export const defaultOnboardingState: OnboardingState = {
  name: "",
  investorType: "balanced_builder",
  objective: "balanced",
  horizon: "medium",
  riskComfort: "medium",
  decisionStyle: "evidence_first",
  primaryConcern: "unknown",
  liquidityNeed: "medium"
};

const presets: Record<PresetId, PresetDefinition> = {
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

function presetForState(state: OnboardingState): PresetDefinition {
  if (state.decisionStyle === "preserve_unless_clear" || state.objective === "preserve" || state.riskComfort === "low" || state.liquidityNeed === "high") {
    return state.horizon === "short" ? presets.ultra_conservative : presets.conservative;
  }
  if (state.decisionStyle === "test_growth" || state.objective === "growth" || state.riskComfort === "high") {
    return state.horizon === "short" ? presets.balanced : presets.growth;
  }
  if (state.horizon === "long") return presets.growth;
  return presets.balanced;
}

export function buildClientFitProfileFromOnboarding(state: OnboardingState): ClientFitInput {
  const preset = presetForState(state);
  const horizonYears = state.horizon === "short" ? Math.min(preset.horizon, 3) : state.horizon === "long" ? Math.max(preset.horizon, 10) : preset.horizon;
  const namePrefix = state.name.trim() ? `${state.name.trim()}'s ` : "";

  return {
    preset_id: preset.id,
    source: "questionnaire",
    source_quality: "medium",
    source_quality_reason: `${namePrefix}friendly onboarding profile captured before portfolio diagnosis.`,
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
      return "broad X-Ray and Stress Lab evidence";
  }
}
