import type { ClientFitDisplaySummary, ClientFitTargetDisplayRow } from "@/lib/generated/api-types";
import type { SiteExplanationBundle, StatusTone } from "@/lib/types";
import { sanitizePublicDisplayText } from "@/lib/displayLabels";

export type ClientFitReason = {
  id: string;
  label: string;
  value: string;
  target: string;
  status: string;
  tone: StatusTone;
  explanation: string;
};

export type ClientFitPresentation = {
  statusLabel: string;
  statusTone: StatusTone;
  profileLabel: string;
  sourceLabel: string;
  headline: string;
  summary: string;
  primaryReasons: ClientFitReason[];
  secondaryRows: ClientFitReason[];
  allRows: ClientFitReason[];
  boundaryNote: string;
  nextBestTest: string;
  evidenceSummary: string;
  technicalDetails: string[];
};

const PROFILE_LABELS: Record<string, string> = {
  ultra_conservative: "Very cautious",
  conservative: "Cautious",
  balanced: "Balanced",
  growth: "Growth-oriented",
  aggressive: "Aggressive growth"
};

const DIMENSION_LABELS: Record<string, string> = {
  "Return target": "Return goal",
  "Volatility comfort range": "Volatility",
  "Historical drawdown limit": "Historical drawdown",
  "Worst stress loss limit": "Stress loss",
  "Investment horizon": "Horizon",
  "Goal-risk consistency": "Goal/risk consistency"
};

const SHORT_STATUS_LABELS: Array<[RegExp, string]> = [
  [/within stated client fit profile/i, "Within your profile"],
  [/outside stated client fit limits/i, "Outside your profile"],
  [/client fit watch/i, "Worth reviewing"],
  [/goal-risk conflict/i, "Goal and risk conflict"],
  [/client fit evidence insufficient/i, "Not enough evidence"],
  [/client fit not provided/i, "Profile missing"],
  [/client fit match/i, "Matches"],
  [/within stated client fit profile/i, "Within your profile"]
];

const ROW_STATUS_LABELS: Array<[RegExp, string]> = [
  [/outside stated client fit limits/i, "Outside"],
  [/within stated client fit profile/i, "Within"],
  [/client fit watch/i, "Watch"],
  [/client fit match/i, "Matches"],
  [/goal-risk conflict/i, "Conflict"],
  [/client fit evidence insufficient/i, "Insufficient"],
  [/client fit not provided/i, "Missing"]
];

const unsafeClientFitPublicTextPattern = /\b(?:suitability|suitable|approved|safe portfolio|no action needed|trade now|must rebalance|best portfolio|optimizer mandate)\b|\bsell\b(?!-off)|\bbuy\b/i;
const NEAR_LIMIT_PERCENT_BREACH = 0.5;

function fallbackText(value: string | null | undefined, fallback: string) {
  return typeof value === "string" && value.trim() ? value.trim() : fallback;
}

function cleanPublicClientFitText(value: string | null | undefined, fallback: string) {
  const text = sanitizePublicDisplayText(fallbackText(value, fallback), fallback).replace(/\s+/g, " ").trim();
  if (!text || unsafeClientFitPublicTextPattern.test(text)) return fallback;
  return text;
}

function cleanTechnicalText(value: string | null | undefined) {
  const text = fallbackText(value, "")
    .replace(/\bclient fit\b/gi, "Client Fit")
    .replace(/\s+/g, " ")
    .trim();
  if (unsafeClientFitPublicTextPattern.test(text)) return "";
  return text;
}

function shortLabel(value: string | null | undefined, pairs: Array<[RegExp, string]>, fallback: string) {
  const text = fallbackText(value, fallback);
  const match = pairs.find(([pattern]) => pattern.test(text));
  return match ? match[1] : text;
}

function statusRank(row: ClientFitTargetDisplayRow) {
  const label = `${row.status_label ?? ""} ${row.status_tone ?? ""}`.toLowerCase();
  if (label.includes("conflict")) return 0;
  if (label.includes("outside") || label.includes("breach") || row.status_tone === "red") return 1;
  if (label.includes("watch") || row.status_tone === "amber") return 2;
  if (label.includes("insufficient") || label.includes("missing")) return 3;
  return 4;
}

function profileLabel(value: string | null | undefined) {
  const raw = fallbackText(value, "Provided risk profile");
  return PROFILE_LABELS[raw] ?? raw.replace(/_/g, " ").replace(/\b\w/g, (char) => char.toUpperCase());
}

function dimensionLabel(value: string | null | undefined) {
  const raw = fallbackText(value, "Profile check");
  return DIMENSION_LABELS[raw] ?? raw;
}

function parsePercentLabel(value: string | null | undefined) {
  const text = fallbackText(value, "");
  const match = text.match(/-?\d+(?:\.\d+)?/);
  if (!match) return null;
  const parsed = Number(match[0]);
  return Number.isFinite(parsed) ? parsed : null;
}

function formatYearCount(value: number) {
  const rounded = Math.round(value * 10) / 10;
  const label = Number.isInteger(rounded) ? String(rounded) : rounded.toFixed(1);
  return `${label} year${rounded === 1 ? "" : "s"}`;
}

function clientFitValueLabel(label: string, row: ClientFitTargetDisplayRow) {
  const raw = fallbackText(row.portfolio_value_label, "Unavailable");
  if (/horizon/i.test(label)) {
    const numeric = parsePercentLabel(raw);
    if (/%/.test(raw) && numeric !== null) return formatYearCount(numeric / 100);
    if (/^\s*\d+(?:\.\d+)?\s*$/.test(raw) && numeric !== null) return formatYearCount(numeric);
  }
  return sanitizePublicDisplayText(raw, "Unavailable");
}

function nearLimitReason(label: string, row: ClientFitTargetDisplayRow) {
  if (!/stress loss|drawdown/i.test(label)) return false;
  const portfolio = parsePercentLabel(row.portfolio_value_label);
  const target = parsePercentLabel(row.target_or_limit_label);
  if (portfolio === null || target === null) return false;
  const breach = Math.abs(portfolio) - Math.abs(target);
  return breach > 0 && breach <= NEAR_LIMIT_PERCENT_BREACH;
}

function rowToReason(row: ClientFitTargetDisplayRow, index: number): ClientFitReason {
  const label = dimensionLabel(row.dimension_label);
  const isNearLimit = nearLimitReason(label, row);
  return {
    id: `${row.dimension_label || "client-fit-row"}-${index}`,
    label,
    value: clientFitValueLabel(label, row),
    target: sanitizePublicDisplayText(row.target_or_limit_label, "No target returned"),
    status: isNearLimit ? "Near limit" : shortLabel(row.status_label, ROW_STATUS_LABELS, "Check"),
    tone: isNearLimit ? "amber" : row.status_tone ?? "slate",
    explanation: isNearLimit
      ? "Stress loss is slightly beyond the stated limit; treat this as a review flag, not a hard suitability result."
      : cleanPublicClientFitText(row.explanation, "This check compares the current portfolio evidence with your stated profile.")
  };
}

function hasOnlyNearLimitBreaches(reasons: ClientFitReason[]) {
  const hardBreaches = reasons.filter((row) => row.tone === "red" || /outside|conflict/i.test(row.status));
  if (!hardBreaches.length) return reasons.some((row) => /near limit|slightly outside/i.test(row.status));
  return hardBreaches.every((row) => /near limit|slightly outside/i.test(row.status));
}

function statusHeadline(statusLabel: string, reasons: ClientFitReason[]) {
  if (hasOnlyNearLimitBreaches(reasons)) return "The current portfolio is close to the risk limit you described.";
  if (/outside/i.test(statusLabel)) return "The current portfolio is outside the risk level you described.";
  if (/worth reviewing|watch/i.test(statusLabel)) return "The current portfolio is close enough to review carefully.";
  if (/within/i.test(statusLabel)) return "The current portfolio sits within the risk profile you described.";
  if (/goal and risk conflict/i.test(statusLabel)) return "Your return goal and risk limits appear to be in tension.";
  if (/missing/i.test(statusLabel)) return "A completed risk profile is needed before this check can run.";
  return "This check compares your stated profile with current portfolio evidence.";
}

function statusSummary(statusLabel: string, topReasons: ClientFitReason[]) {
  const failed = topReasons.filter((row) => row.tone === "red" || /outside|conflict/i.test(row.status));
  const watch = topReasons.filter((row) => row.tone === "amber" || /watch/i.test(row.status));
  if (hasOnlyNearLimitBreaches(topReasons)) {
    const names = watch.slice(0, 2).map((row) => row.label.toLowerCase()).join(" and ");
    return `${names || "The profile check"} is near the stated boundary. Treat this as diagnostic context before choosing a candidate test.`;
  }
  if (failed.length) {
    const names = failed.slice(0, 2).map((row) => row.label.toLowerCase()).join(" and ");
    return `Main mismatch: ${names}. Treat this as diagnostic context before choosing a candidate test.`;
  }
  if (watch.length) {
    const names = watch.slice(0, 2).map((row) => row.label.toLowerCase()).join(" and ");
    return `No single row is a final decision, but ${names} deserve attention before moving forward.`;
  }
  if (/within/i.test(statusLabel)) {
    return "The profile check does not flag a major mismatch. Keep the diagnosis and stress evidence separate before making a decision.";
  }
  return "This result adds profile context to the diagnosis and stress evidence.";
}

function evidenceSummary(bundle: SiteExplanationBundle | undefined) {
  const screen = bundle?.screens?.client_fit;
  const count = (screen?.executive?.length ?? 0) + (screen?.evidence?.length ?? 0) + (screen?.technical?.length ?? 0);
  if (!count) return "Evidence: current portfolio diagnosis, stress test, and stated risk profile when available.";
  return `Evidence: ${count} bounded explanation item${count === 1 ? "" : "s"} from the active review.`;
}

function technicalDetails(bundle: SiteExplanationBundle | undefined, summary: ClientFitDisplaySummary | undefined) {
  const screen = bundle?.screens?.client_fit;
  const fromBundle = [...(screen?.executive ?? []), ...(screen?.technical ?? [])]
    .map((item) => cleanTechnicalText(item.text))
    .filter(Boolean);
  const details = [
    ...fromBundle,
    cleanTechnicalText(summary?.decision_boundary),
    "Client Fit is separate from Diagnostic Quality and Decision Verdict."
  ];
  return Array.from(new Set(details)).slice(0, 4);
}

export function buildClientFitPresentation(
  summary: ClientFitDisplaySummary | undefined,
  bundle?: SiteExplanationBundle
): ClientFitPresentation {
  const rows = [...(summary?.target_rows ?? [])]
    .sort((left, right) => statusRank(left) - statusRank(right))
    .map(rowToReason);
  const statusLabel = shortLabel(summary?.status_label, SHORT_STATUS_LABELS, "Profile missing");
  const primaryReasons = rows.filter((row) => row.tone !== "green").slice(0, 3);
  const visibleReasons = primaryReasons.length ? primaryReasons : rows.slice(0, 3);
  const presentationTone = hasOnlyNearLimitBreaches(visibleReasons) ? "amber" : summary?.status_tone ?? "amber";

  return {
    statusLabel,
    statusTone: presentationTone,
    profileLabel: profileLabel(summary?.profile_label),
    sourceLabel: profileLabel(summary?.source_quality_label),
    headline: statusHeadline(statusLabel, visibleReasons),
    summary: statusSummary(statusLabel, visibleReasons),
    primaryReasons: visibleReasons,
    secondaryRows: rows.slice(3),
    allRows: rows,
    boundaryNote: cleanPublicClientFitText(
      summary?.decision_boundary,
      "Client Fit adds profile context alongside the diagnosis, stress evidence, and comparison."
    ),
    nextBestTest: cleanPublicClientFitText(
      summary?.next_best_test,
      "Continue to the hypothesis page and test one candidate only if the diagnosis evidence justifies a comparison."
    ),
    evidenceSummary: evidenceSummary(bundle),
    technicalDetails: technicalDetails(bundle, summary)
  };
}
