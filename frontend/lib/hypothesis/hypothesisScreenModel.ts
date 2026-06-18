import type { ActiveReviewState, CandidateGenerationSummary, LaunchpadCardSummary } from "@/lib/reviewState";
import type { StatusTone } from "@/lib/types";
import { formatUnknownValue, normalizeDisplayLabel, normalizeDisplaySentence } from "@/lib/displayLabels";
import { buildPublicSiteExplanationDisplayModel, type PublicSiteExplanationItem } from "@/lib/siteExplanationPresenter";

type ClientFitTone = "neutral" | "watch" | "breach";

export type HypothesisTestModel = {
  cardId: string;
  title: string;
  hypothesis: string;
  why: string;
  methods: string[];
  selectedMethodId?: string;
  selectedMethodLabel: string;
  successCriteria: string[];
  tradeoff?: string;
  decisionBoundary: string;
  statusLabel: string;
  canGenerate: boolean;
  disabledReason?: string;
  isMonitorOrDataPath: boolean;
};

export type HypothesisScreenModel = {
  pageState: "locked" | "unavailable" | "ready" | "read_only";
  defaultSelectedCardId: string | null;
  header: {
    title: "Hypothesis Builder";
    subtitle: string;
    badge: string;
    badgeTone: StatusTone;
  };
  primaryDiagnosis: {
    label: string;
    explanation: string;
    rootCause?: string;
    confidence?: string;
    materiality?: string;
    nextStep: string;
  };
  primaryTest?: HypothesisTestModel;
  alternativeTests: HypothesisTestModel[];
  monitorOrDataTests: HypothesisTestModel[];
  clientFitContext?: {
    statusLabel: string;
    summary: string;
    boundary: string;
    tone: ClientFitTone;
    badgeTone: StatusTone;
  };
  evidencePanel?: {
    title: string;
    subtitle: string;
    executiveItems: PublicSiteExplanationItem[];
    evidenceItems: PublicSiteExplanationItem[];
    technicalItems: PublicSiteExplanationItem[];
  };
  action: {
    label: string;
    state: "generate" | "generating" | "generated" | "continue" | "blocked";
    disabledReason?: string;
    statusLabel: string;
    candidateName?: string;
    candidateWeights: Array<{ ticker: string; weight: number }>;
    userError?: string;
    developerError?: string;
  };
};

const METHOD_LABELS: Record<string, string> = {
  equal_weight: "Equal Weight",
  risk_parity: "Risk Parity",
  hierarchical_risk_parity: "Hierarchical Risk Parity",
  hrp: "Hierarchical Risk Parity",
  minimum_variance: "Minimum Variance",
  minimum_cvar: "Minimum CVaR",
  maximum_diversification: "Maximum Diversification"
};

function isRecord(value: unknown): value is Record<string, unknown> {
  return Boolean(value) && typeof value === "object" && !Array.isArray(value);
}

function optionalText(value: unknown) {
  return typeof value === "string" && value.trim() ? value.trim() : undefined;
}

function firstText(...values: unknown[]) {
  for (const value of values) {
    const text = optionalText(value);
    if (text) return text;
  }
  return undefined;
}

function methodId(value: unknown) {
  const raw = optionalText(value)?.toLowerCase().trim().replace(/[\s-]+/g, "_");
  if (!raw) return undefined;
  return raw === "hrp" ? "hierarchical_risk_parity" : raw;
}

function methodLabel(value: unknown) {
  const id = methodId(value);
  return id ? METHOD_LABELS[id] ?? normalizeDisplayLabel(id) : undefined;
}

function cardText(card: LaunchpadCardSummary) {
  return [
    card.card_id,
    card.title,
    card.goal,
    card.card_type,
    card.source_problem_label,
    card.hypothesis_to_test
  ].filter(Boolean).join(" ").toLowerCase();
}

function isMonitorOrDataCard(card: LaunchpadCardSummary) {
  const text = cardText(card);
  const hasMethods = Array.isArray(card.suggested_methods) && card.suggested_methods.length > 0;
  return (
    !hasMethods ||
    text.includes("monitor") ||
    text.includes("data quality") ||
    text.includes("evidence insufficient") ||
    text.includes("do not act") ||
    text.includes("review objectives")
  );
}

function launchpadCardToTest(card: LaunchpadCardSummary, hasLiveLineage: boolean, reviewId?: string): HypothesisTestModel {
  const methods = (card.suggested_methods ?? [])
    .map((item) => methodLabel(item.candidate_method_id))
    .filter((item): item is string => Boolean(item));
  const defaultMethodId = methodId(card.default_method ?? card.suggested_methods?.[0]?.candidate_method_id);
  const monitorOrData = isMonitorOrDataCard(card);
  const canGenerate = Boolean(hasLiveLineage && reviewId && defaultMethodId && !monitorOrData);
  const disabledReason = !hasLiveLineage
    ? "Run a new diagnosis to continue."
    : monitorOrData
      ? "This path is for monitoring or data review, not candidate generation."
      : !defaultMethodId
        ? "No supported candidate method is available for this test."
        : !reviewId
          ? "Review id is unavailable."
          : undefined;

  return {
    cardId: card.card_id,
    title: formatUnknownValue(card.title, "Selected diagnostic test"),
    hypothesis: normalizeDisplaySentence(
      card.hypothesis_to_test ?? card.goal,
      "Test whether the selected candidate improves the diagnosed weakness in comparison."
    ),
    why: normalizeDisplaySentence(
      card.source_problem_label
        ? `This test is tied to the diagnosis: ${card.source_problem_label}.`
        : card.goal,
      "This test is tied to the current portfolio diagnosis."
    ),
    methods: methods.length ? methods : defaultMethodId ? [METHOD_LABELS[defaultMethodId] ?? normalizeDisplayLabel(defaultMethodId)] : [],
    selectedMethodId: defaultMethodId,
    selectedMethodLabel: defaultMethodId ? METHOD_LABELS[defaultMethodId] ?? normalizeDisplayLabel(defaultMethodId) : "No candidate method",
    successCriteria: (card.success_criteria ?? []).map((item) => normalizeDisplaySentence(item)).filter(Boolean),
    tradeoff: card.tradeoff_to_watch ? normalizeDisplaySentence(card.tradeoff_to_watch) : undefined,
    decisionBoundary: normalizeDisplaySentence(
      card.decision_boundary,
      "Review this candidate in comparison."
    ),
    statusLabel: monitorOrData ? "Context path" : "Ready to test",
    canGenerate,
    disabledReason,
    isMonitorOrDataPath: monitorOrData
  };
}

function primaryDiagnosisFromReview(activeReview: ActiveReviewState | null): HypothesisScreenModel["primaryDiagnosis"] {
  const summary = activeReview?.reviewSummary;
  const diagnosis = summary?.diagnosis;
  const primaryProblem = summary?.primaryProblem;
  const nextStep = firstText(summary?.recommendedFirstTest, summary?.suggestedActionPaths?.[0], diagnosis?.nextStep);

  if (!activeReview || activeReview.runStatus !== "completed") {
    return {
      label: "Portfolio diagnosis is not ready",
      explanation: "Complete Portfolio Input and Client Fit before selecting a diagnostic hypothesis.",
      nextStep: "Run portfolio diagnosis first"
    };
  }

  return {
    label: formatUnknownValue(primaryProblem ?? diagnosis?.headline, "Current diagnosis is available"),
    explanation: normalizeDisplaySentence(
      diagnosis?.headline,
      "The diagnosis is ready. The next step is to prepare one test for comparison."
    ),
    rootCause: primaryProblem ? formatUnknownValue(primaryProblem) : undefined,
    confidence: summary?.problemConfidence ? formatUnknownValue(summary.problemConfidence) : undefined,
    materiality: summary?.problemSeverity ? formatUnknownValue(summary.problemSeverity) : undefined,
    nextStep: normalizeDisplaySentence(nextStep, "Select one diagnostic test before comparison.")
  };
}

function clientFitContext(activeReview: ActiveReviewState | null): HypothesisScreenModel["clientFitContext"] {
  const clientFit = activeReview?.reviewSummary?.clientFit;
  if (!clientFit) return undefined;
  const rawStatus = optionalText(clientFit.status_label) ?? "Client Fit context";
  const status = rawStatus.toLowerCase();
  const tone: ClientFitTone = status.includes("breach") || status.includes("outside")
    ? "breach"
    : status.includes("watch") || status.includes("conflict") || status.includes("limit")
      ? "watch"
      : "neutral";
  return {
    statusLabel: formatUnknownValue(rawStatus, "Client Fit context"),
    summary: normalizeDisplaySentence(
      clientFit.main_explanation,
      "Client Fit is shown as context for the test."
    ),
    boundary: normalizeDisplaySentence(
      clientFit.decision_boundary,
      "Client Fit adds profile context to the diagnosis and comparison evidence."
    ),
    tone,
    badgeTone: clientFit.status_tone ?? (tone === "breach" ? "red" : tone === "watch" ? "amber" : "slate")
  };
}

function hasProvidedClientFitContext(activeReview: ActiveReviewState | null) {
  const label = optionalText(activeReview?.reviewSummary?.clientFit?.status_label)?.toLowerCase() ?? "";
  return Boolean(label && !label.includes("not provided"));
}

function evidencePanel(activeReview: ActiveReviewState | null, candidateGenerated: boolean): HypothesisScreenModel["evidencePanel"] {
  const bundle = activeReview?.reviewSummary?.siteExplanation;
  const display = buildPublicSiteExplanationDisplayModel(
    bundle,
    candidateGenerated ? "candidate" : "hypothesis",
    candidateGenerated ? "Candidate evidence" : "Hypothesis evidence"
  );
  if (!display) return undefined;
  return {
    title: display.title,
    subtitle: display.subtitle,
    executiveItems: display.executiveItems,
    evidenceItems: display.evidenceItems,
    technicalItems: display.technicalItems
  };
}

function candidateDisplayName(candidate?: CandidateGenerationSummary, selectedMethod = "Diagnostic") {
  if (!candidate) return undefined;
  if (candidate.methodLabel) return candidate.methodLabel;
  if (candidate.candidateId.includes("equal_weight")) return "Equal Weight Reference Candidate";
  if (candidate.candidateId.includes("risk_parity")) return "Risk Parity Reference Candidate";
  return formatUnknownValue(candidate.candidateId, `${selectedMethod} Test Candidate`);
}

export function sanitizeHypothesisError(error?: string) {
  if (!error) return {};
  const developerError = error;
  const lower = error.toLowerCase();
  if (lower.includes("fastapi") || lower.includes("uvicorn") || lower.includes("127.0.0.1") || lower.includes("backend")) {
    return {
      userError: "Supporting data service is unavailable. You can keep the selected diagnostic test, but candidate generation needs the local analysis service.",
      developerError
    };
  }
  return {
    userError: normalizeDisplaySentence(error, "The test candidate could not be generated."),
    developerError
  };
}

export function buildHypothesisScreenModel({
  activeReview,
  selectedCardId,
  isGenerating = false,
  generationError
}: {
  activeReview: ActiveReviewState | null;
  selectedCardId?: string | null;
  isGenerating?: boolean;
  generationError?: string;
}): HypothesisScreenModel {
  const completedRealReview = activeReview?.runMode === "real_run" && activeReview.runStatus === "completed";
  const hasLiveLineage = Boolean(activeReview?.lineageAvailable && !activeReview?.readOnlyHistory);
  const reviewId = activeReview?.reviewId ?? activeReview?.reviewSummary?.reviewId ?? optionalText(activeReview?.reviewResult?.review_id);
  const rawCards = activeReview?.reviewSummary?.launchpadCards ?? [];
  const tests = rawCards.map((card) => launchpadCardToTest(card, hasLiveLineage, reviewId));
  const generatingTests = tests.filter((test) => !test.isMonitorOrDataPath);
  const monitorOrDataTests = tests.filter((test) => test.isMonitorOrDataPath);
  const defaultSelectedCardId = generatingTests[0]?.cardId ?? tests[0]?.cardId ?? null;
  const requested = selectedCardId ? tests.find((test) => test.cardId === selectedCardId) : undefined;
  const primaryTest = requested ?? generatingTests[0] ?? tests[0];
  const candidateForSelectedCard = activeReview?.candidateGeneration?.selectedCardId === primaryTest?.cardId
    ? activeReview?.candidateGeneration
    : undefined;
  const candidateGenerated = Boolean(candidateForSelectedCard);
  const sanitizedError = sanitizeHypothesisError(generationError);

  let pageState: HypothesisScreenModel["pageState"] = "ready";
  if (!completedRealReview || !activeReview) pageState = "locked";
  else if (!hasProvidedClientFitContext(activeReview)) pageState = "locked";
  else if (activeReview.readOnlyHistory) pageState = "read_only";
  else if (!rawCards.length) pageState = "unavailable";

  const disabledReason = pageState === "read_only"
    ? "This saved review is compact history. Run a new diagnosis to continue."
    : pageState === "locked" && completedRealReview
      ? "Complete Client Fit before testing a hypothesis."
      : pageState === "locked"
        ? "Complete Portfolio Input and Client Fit before testing a hypothesis."
        : primaryTest?.disabledReason;

  const actionState: HypothesisScreenModel["action"]["state"] = isGenerating
    ? "generating"
    : pageState !== "ready"
      ? "blocked"
      : candidateForSelectedCard?.canCompare && hasLiveLineage
      ? "continue"
      : candidateGenerated
        ? "generated"
        : !primaryTest?.canGenerate
          ? "blocked"
          : "generate";

  return {
    pageState,
    defaultSelectedCardId,
    header: {
      title: "Hypothesis Builder",
      subtitle: "Select one diagnosis-led test candidate before Current vs Candidate Comparison.",
      badge: pageState === "read_only" ? "Read-only compact history" : pageState === "locked" ? "Locked" : pageState === "unavailable" ? "Hypothesis unavailable" : "Ready",
      badgeTone: pageState === "ready" ? "blue" : pageState === "locked" || pageState === "unavailable" ? "amber" : "slate"
    },
    primaryDiagnosis: primaryDiagnosisFromReview(activeReview),
    primaryTest,
    alternativeTests: generatingTests.filter((test) => test.cardId !== primaryTest?.cardId),
    monitorOrDataTests,
    clientFitContext: clientFitContext(activeReview),
    evidencePanel: evidencePanel(activeReview, candidateGenerated),
    action: {
      label: actionState === "continue"
        ? "Continue to Comparison"
        : actionState === "generating"
          ? "Generating test candidate..."
          : actionState === "generated"
            ? "Candidate generated"
            : actionState === "blocked"
              ? "Generation unavailable"
              : "Generate test candidate",
      state: actionState,
      disabledReason: actionState === "blocked" ? disabledReason : undefined,
      statusLabel: candidateForSelectedCard?.canCompare ? "Ready for comparison" : candidateGenerated ? "Generated" : primaryTest?.statusLabel ?? "No test selected",
      candidateName: candidateDisplayName(candidateForSelectedCard, primaryTest?.selectedMethodLabel),
      candidateWeights: candidateForSelectedCard?.weights ?? [],
      userError: sanitizedError.userError,
      developerError: sanitizedError.developerError
    }
  };
}
