import type { StatusTone } from "@/lib/types";

const DISPLAY_REPLACEMENTS: Array<[RegExp, string]> = [
  [/\breal\s+candidate\s+launchpad\b/gi, "Hypothesis Builder"],
  [/\bcandidate\s+launchpad\b/gi, "Hypothesis Builder"],
  [/\blaunchpad\s+card\b/gi, "hypothesis test"],
  [/\bcard\s+type\b/gi, "test type"],
  [/\bdefault\s+method\b/gi, "suggested method"],
  [/\bsource\s+(?:problem|card)\b/gi, "diagnosis source"],
  [/\bbuilder\s+setup\b/gi, "Test setup"],
  [/\bsetup[_\s-]*only\b/gi, "Setup only"],
  [/\bmonitor[_\s-]*or[_\s-]*resolve[_\s-]*data\b/gi, "Monitor or improve data quality"],
  [/\bcandidate[_\s-]*generation\b/gi, "Candidate generation"],
  [/\bfactory\b/gi, "candidate builder"],
  [/\bfactory\s+step\s+status\s*:?\s*succeeded\b/gi, "Candidate setup completed"],
  [/\bfactory\s+profile\s+id\s*:?\s*explicit\s+list\b/gi, "Selected candidate setup"],
  [/\bcandidate\s+builder\s+step\s+status\s*:?\s*succeeded\b/gi, "Candidate setup completed"],
  [/\bprofile\s+id\s*:?\s*explicit\s+list\b/gi, "Selected candidate setup"],
  [/\bimplementation\s+order\b/gi, "rebalance instruction"],
  [/\btrade\s+execution\b/gi, "rebalance instruction"],
  [/\bdecision[_\s-]*verdict\.json\b/gi, "decision-support verdict"],
  [/\bcurrent[_\s-]*vs[_\s-]*candidate(?:\.json)?\b/gi, "Current vs Candidate Comparison"],
  [/\bmostly[_\s-]*weak[_\s-]*protection\b/gi, "Limited stress offset"],
  [/\bweak[_\s-]*protection\b/gi, "Weak hedge protection"],
  [/\bno[_\s-]*protection\b/gi, "Limited stress offset"],
  [/\bbaseline[_\s-]*or[_\s-]*candidate[_\s-]*metric[_\s-]*missing\b/gi, "Candidate metric unavailable"],
  [/\bno[_\s-]*available[_\s-]*comparison[_\s-]*metrics\b/gi, "Comparison metrics unavailable"],
  [/\bstale[_\s-]*downstream[_\s-]*artifact[_\s-]*ignored\b/gi, "Earlier evidence was skipped because it did not match the active review"],
  [/\bprevious\s+result\s+ignored\s+because\s+it\s+is\s+outdated\b/gi, "Earlier evidence was skipped because it did not match the active review"],
  [/\bmonitoring\s+diff\.supporting\s+data\b/gi, "monitoring evidence"],
  [/\bdiff\.supporting\s+data\b/gi, "supporting comparison evidence"],
  [/\bstatus\s+degraded\s+across\s+\d+\s+dimension(?:\(s\)|s)?\b/gi, "Some comparison evidence is incomplete"],
  [/\bsuccess\s+criteria\s*:?\s+unavailable\b/gi, "Success criteria were not returned for this test"],
  [/\bevidence\s+is\s+not\s+available\s+yet\s+for\s+this\s+screen\b/gi, "Evidence for this step is summarized in the cards above"],
  [/\bartifacts?\b/gi, "supporting evidence"],
  [/\bdiagnostic sections?\s*2(?:\.\d+)?(?:\s*[-\u2013\u2014]\s*2(?:\.\d+)?)?\b/gi, "portfolio behavior and factor evidence"],
  [/\bblocks?\s*2(?:\.\d+)?(?:\s*[-\u2013\u2014]\s*2(?:\.\d+)?)?\b/gi, "portfolio behavior and factor evidence"],
  [/\bRC_vol\b/g, "risk contribution"],
  [/\brc[_\s-]*pct\b/gi, "risk contribution"],
  [/\bbeta[_\s-]*rr\b/gi, "interest-rate sensitivity"],
  [/\brisk[_\s-]*on[_\s-]*weight\b/gi, "risk-on holdings"],
  [/\bequity[_\s-]*weight\b/gi, "equity-linked holdings"],
  [/\brisk[_\s-]*on\b/gi, "growth / risk assets"],
  [/\bfactor[_\s-]*variance[_\s-]*(?:decomposition|contribution)\b/gi, "factor contribution view"],
  [/\bportfolio[_\s-]*xray\b/gi, "Portfolio Diagnosis"],
  [/\bstress[_\s-]*report\b/gi, "stress evidence"],
  [/\bequity[_\s-]*shock\b/gi, "Equity shock"],
  [/\brates[_\s-]*shock\b/gi, "Interest-rate shock"],
  [/\binflation[_\s-]*stagflation\b/gi, "Inflation / stagflation"],
  [/\bcredit[_\s-]*shock\b/gi, "Credit shock"],
  [/\bliquidity[_\s-]*shock\b/gi, "Liquidity shock"],
  [/\busd[_\s-]*shock\b/gi, "USD shock"],
  [/\bcommodity[_\s-]*shock\b/gi, "Commodity shock"],
  [/\brecession[_\s-]*severe(?:[_\s-]*protection)?\b/gi, "Severe recession"],
  [/\breal[_\s-]*rates\b/gi, "interest-rate sensitivity"],
  [/\bVIX[_\s-]*volatility\b/g, "VIX volatility"],
  [/\bCASH\s+USD\b/g, "Cash USD"],
  [/\bfixed[_\s-]*income\b/gi, "Fixed income"],
  [/\bmulti[_\s-]*asset\b/gi, "Multi-asset"],
  [/\basset[_\s-]*class\b/gi, "asset class"],
  [/\bmain[_\s-]*risk[_\s-]*factor\b/gi, "main risk factor"],
  [/\bcurrency[_\s-]*exposure\b/gi, "currency exposure"],
  [/\brule-based evidence\b/gi, "diagnostic evidence"],
  [/\bKalman uncertainty\b/gi, "factor estimate uncertainty"],
  [/\btechnical detail\b/gi, "supporting evidence"],
  [/\btechnical confidence\b/gi, "evidence quality"],
  [/\bdetector checks whether\b/gi, "The review checks whether"],
  [/\bdetector checks\b/gi, "The review checks"],
  [/\b(?:backend|api|json|raw outputs?|source artifact|real backend review)\b/gi, "supporting data"]
];

const EXACT_LABELS: Record<string, string> = {
  equity: "Equity",
  fixed_income: "Fixed income",
  fixedincome: "Fixed income",
  cash: "Cash",
  commodity: "Commodity",
  gold: "Commodity",
  usd: "USD",
  cash_usd: "Cash USD",
  "CASH USD": "Cash USD",
  "true": "Available",
  "false": "Not available",
  "n/a": "Not available yet",
  na: "Not available yet",
  us: "US",
  global: "Global",
  equity_shock: "Equity shock",
  rates_shock: "Interest-rate shock",
  inflation_stagflation: "Inflation / stagflation",
  credit_shock: "Credit shock",
  liquidity_shock: "Liquidity shock",
  usd_shock: "USD shock",
  commodity_shock: "Commodity shock",
  recession_severe: "Severe recession",
  weak_protection: "Weak hedge protection",
  no_protection: "Limited stress offset",
  mostly_weak_protection: "Limited stress offset",
  real_rates: "Interest-rate sensitivity",
  us_growth: "Growth / risk assets",
  risk_on: "Growth / risk assets",
  risk_on_weight: "Risk-on holdings",
  equity_weight: "Equity-linked holdings",
  VIX_volatility: "VIX volatility",
  equal_weight: "Equal Weight",
  risk_parity: "Risk Parity",
  minimum_variance: "Minimum Variance",
  minimum_cvar: "Minimum CVaR",
  hrp: "Hierarchical Risk Parity",
  maximum_diversification: "Maximum Diversification",
  monitor_or_resolve_data: "Monitor or improve data quality",
  setup_only: "Setup only",
  reference_benchmark_test: "Reference benchmark test",
  targeted_hypothesis_test: "Targeted hypothesis test",
  mixed_evidence_no_action: "Mixed evidence / no immediate rebalance justified",
  evidence_insufficient_data_quality: "Evidence insufficient due to data quality",
  current_portfolio_acceptable: "Current portfolio acceptable with monitoring",
  weak_crisis_resilience: "Weak crisis resilience",
  poor_diversification: "Poor diversification",
  high_concentration: "High concentration",
  weak_hedge_behavior: "Weak hedge behavior",
  duration_rates_vulnerability: "Duration / rates vulnerability",
  credit_liquidity_fragility: "Credit / liquidity fragility",
  baseline_or_candidate_metric_missing: "Candidate metric unavailable",
  no_available_comparison_metrics: "Comparison metrics unavailable",
  stale_downstream_artifact_ignored: "Earlier evidence was skipped because it did not match the active review",
  no_material_rebalance_recommended: "No material rebalance recommended",
  evidence_insufficient: "Evidence insufficient",
  candidate_failed_or_infeasible: "Candidate failed or infeasible",
  test_another_candidate_or_review_evidence: "Test another candidate",
  selected_candidate: "Rebalance review",
  keep_current_portfolio: "Keep current portfolio",
  low: "Low",
  medium: "Medium",
  moderate: "Moderate",
  high: "High"
};

function titleCaseLoose(value: string) {
  return value.replace(/\b\w/g, (letter) => letter.toUpperCase());
}

function sentenceCase(value: string) {
  if (!value) return value;
  return `${value.charAt(0).toUpperCase()}${value.slice(1)}`;
}

function preserveAcronyms(value: string) {
  return value
    .replace(/\bUsd\b/g, "USD")
    .replace(/\bUs\b/g, "US")
    .replace(/\bU\.s\.\b/gi, "US")
    .replace(/\bCagr\b/g, "CAGR")
    .replace(/\bVar\b/g, "VaR")
    .replace(/\bEs\b/g, "ES")
    .replace(/\bVix\b/g, "VIX");
}

export function normalizeDisplayLabel(value?: unknown, fallback = "Unavailable") {
  const raw = value === null || value === undefined ? fallback : String(value);
  const trimmed = raw.trim();
  if (!trimmed) return fallback;

  const exactKey = trimmed.replace(/\s+/g, "_");
  const exact = EXACT_LABELS[exactKey] ?? EXACT_LABELS[exactKey.toLowerCase()];
  if (exact) return exact;

  let output = trimmed;
  DISPLAY_REPLACEMENTS.forEach(([pattern, replacement]) => {
    output = output.replace(pattern, replacement);
  });
  output = output
    .replace(/\bportfolio behavior and factor evidence,?\s*(?:\d(?:\.\d+)?(?:\s*,\s*|\s+and\s+|,\s*and\s*)?)+/gi, "portfolio behavior and factor evidence")
    .replace(/\b(?:sections?\s*)?2\.\d+(?:\s*,\s*(?:and\s*)?2\.\d+)+\b/gi, "portfolio behavior and factor evidence")
    .replace(/\b(Current vs Candidate Comparison)(?:\s+Comparison)+\b/gi, "$1")
    .replace(/_/g, " ")
    .replace(/\s+/g, " ")
    .replace(/\s+([.,;:])/g, "$1")
    .trim();

  return preserveAcronyms(sentenceCase(output || fallback));
}

function looksLikeArtifactFilename(value: string) {
  return /(?:^|[\\/])[\w.-]+\.json$/i.test(value) || /(?:^|[\\/])(?:output|cache|runs|results_csv)[\\/]/i.test(value);
}

const PUBLIC_TECHNICAL_TEXT_PATTERNS: RegExp[] = [
  /\bfactory\b/i,
  /\bartifacts?\b/i,
  /\bjson\b/i,
  /\bdiff\.supporting\b/i,
  /\bexplicit\s+list\b/i,
  /\bstatus\s*:\s*succeeded\b/i,
  /\bprevious\s+result\s+ignored\b/i,
  /\bcandidate\s+builder\s+step\s+status\b/i,
  /\b(?:source_refs?|field_path|schema_version|frontend_review|run_id)\b/i,
  /\b[a-z]+_[a-z0-9_]*\b/i
];

const PUBLIC_TECHNICAL_FALLBACK = "Some supporting comparison evidence is incomplete.";

export function containsPublicTechnicalText(value?: unknown) {
  if (value === null || value === undefined) return false;
  const text = String(value);
  return PUBLIC_TECHNICAL_TEXT_PATTERNS.some((pattern) => pattern.test(text));
}

export function formatUnknownValue(value?: unknown, fallback = "Not available yet") {
  if (value === null || value === undefined) return fallback;
  if (typeof value === "boolean") return value ? "Available" : "Not available";
  if (typeof value === "number") return Number.isFinite(value) ? String(value) : fallback;
  const raw = String(value).trim();
  if (!raw) return fallback;
  if (/^(?:n\/a|na|null|undefined)$/i.test(raw)) return fallback;
  if (looksLikeArtifactFilename(raw)) return fallback;
  return normalizeDisplayLabel(raw, fallback);
}

export function normalizeDisplaySentence(value?: unknown, fallback = "Supporting evidence is unavailable.") {
  const raw = value === null || value === undefined ? fallback : String(value);
  if (/HAC\s*p-value|p-value|regression/i.test(raw)) {
    return "Factor evidence is available in the supporting data.";
  }

  return normalizeDisplayLabel(raw, fallback)
    .replace(/\bn\/a\b/gi, "Unavailable")
    .replace(/\bEquity Linked\b/g, "Equity-linked")
    .replace(/\bRisk On\b/g, "Risk-on");
}

export function sanitizePublicDisplayText(value?: unknown, fallback = PUBLIC_TECHNICAL_FALLBACK) {
  const raw = value === null || value === undefined ? fallback : String(value);
  let cleaned = normalizeDisplaySentence(raw, fallback)
    .replace(/\b(?:Candidate generation|Candidate builder)\s*:?\s*Candidate setup completed\b/gi, "Candidate setup completed")
    .replace(/\bSupporting evidence\s*:?\s*Selected candidate setup\b/gi, "Selected candidate setup")
    .replace(/\bSupporting data\b/gi, "supporting evidence")
    .replace(/\bUnavailable\s+Unavailable\b/gi, "Unavailable")
    .replace(/\s+/g, " ")
    .trim();

  if (!cleaned || containsPublicTechnicalText(cleaned)) {
    cleaned = fallback;
  }

  return preserveAcronyms(sentenceCase(cleaned));
}

export function sanitizePublicDisplayList(items: unknown[] | undefined, fallback?: string) {
  const seen = new Set<string>();
  const sanitized = (items ?? [])
    .map((item) => sanitizePublicDisplayText(item, ""))
    .filter((item) => item && !containsPublicTechnicalText(item))
    .filter((item) => {
      const key = item.toLowerCase();
      if (seen.has(key)) return false;
      seen.add(key);
      return true;
    });
  if (!sanitized.length && fallback) return [sanitizePublicDisplayText(fallback)];
  return sanitized;
}

export function evidenceQualityLabel(value?: unknown) {
  const normalized = normalizeDisplayLabel(value, "").toLowerCase();
  if (!normalized || normalized.includes("insufficient") || normalized.includes("unavailable") || normalized === "n/a") {
    return "Insufficient data";
  }
  if (normalized.includes("strong") || normalized.includes("high") || normalized.includes("available") || normalized.includes("visible")) {
    return "Strong evidence";
  }
  if (normalized.includes("moderate") || normalized.includes("medium") || normalized.includes("partial")) {
    return "Moderate evidence";
  }
  if (normalized.includes("limited") || normalized.includes("low") || normalized.includes("input")) {
    return "Limited evidence";
  }
  return "Moderate evidence";
}

export function evidenceTone(value?: unknown): StatusTone {
  const label = evidenceQualityLabel(value);
  if (label === "Strong evidence") return "slate";
  if (label === "Moderate evidence") return "slate";
  if (label === "Limited evidence") return "amber";
  return "slate";
}

export function riskSeverityLabel(value?: unknown) {
  const normalized = normalizeDisplayLabel(value, "").toLowerCase();
  if (normalized.includes("high") || normalized.includes("severe")) return "High risk";
  if (normalized.includes("medium") || normalized.includes("moderate")) return "Medium risk";
  if (normalized.includes("low")) return "Low risk";
  return "Unavailable";
}

export function riskSeverityTone(value?: unknown): StatusTone {
  const label = riskSeverityLabel(value);
  if (label === "High risk") return "red";
  if (label === "Medium risk") return "amber";
  if (label === "Low risk") return "slate";
  return "slate";
}

export function displayTitleLabel(value?: unknown, fallback = "Unavailable") {
  return preserveAcronyms(titleCaseLoose(normalizeDisplayLabel(value, fallback)));
}
