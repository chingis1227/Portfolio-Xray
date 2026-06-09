import type { StatusTone } from "@/lib/types";

const DISPLAY_REPLACEMENTS: Array<[RegExp, string]> = [
  [/\bdiagnostic sections?\s*2(?:\.\d+)?(?:\s*[–-]\s*2(?:\.\d+)?)?\b/gi, "portfolio behavior and factor evidence"],
  [/\bblocks?\s*2(?:\.\d+)?(?:\s*[–-]\s*2(?:\.\d+)?)?\b/gi, "portfolio behavior and factor evidence"],
  [/\bRC_vol\b/g, "risk contribution"],
  [/\brc[_\s-]*pct\b/gi, "risk contribution"],
  [/\bbeta[_\s-]*rr\b/gi, "interest-rate sensitivity"],
  [/\brisk[_\s-]*on[_\s-]*weight\b/gi, "risk-on holdings"],
  [/\bequity[_\s-]*weight\b/gi, "equity-linked holdings"],
  [/\brisk[_\s-]*on\b/gi, "growth / risk assets"],
  [/\bfactor[_\s-]*variance[_\s-]*(?:decomposition|contribution)\b/gi, "factor contribution view"],
  [/\bportfolio[_\s-]*xray\b/gi, "Portfolio X-Ray"],
  [/\bstress[_\s-]*report\b/gi, "stress evidence"],
  [/\bequity[_\s-]*shock\b/gi, "Equity sell-off"],
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
  us: "US",
  global: "Global",
  equity_shock: "Equity sell-off",
  rates_shock: "Interest-rate shock",
  inflation_stagflation: "Inflation / stagflation",
  credit_shock: "Credit shock",
  liquidity_shock: "Liquidity shock",
  usd_shock: "USD shock",
  commodity_shock: "Commodity shock",
  recession_severe: "Severe recession",
  real_rates: "Interest-rate sensitivity",
  us_growth: "Growth / risk assets",
  risk_on: "Growth / risk assets",
  risk_on_weight: "Risk-on holdings",
  equity_weight: "Equity-linked holdings",
  VIX_volatility: "VIX volatility"
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
    .replace(/_/g, " ")
    .replace(/\s+/g, " ")
    .replace(/\s+([.,;:])/g, "$1")
    .trim();

  return preserveAcronyms(sentenceCase(output || fallback));
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
  if (label === "Strong evidence") return "green";
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
  if (label === "Low risk") return "green";
  return "slate";
}

export function displayTitleLabel(value?: unknown, fallback = "Unavailable") {
  return preserveAcronyms(titleCaseLoose(normalizeDisplayLabel(value, fallback)));
}
