"use client";

import { useEffect, useMemo, useState, type ReactNode } from "react";
import Link from "next/link";
import { PageHeader } from "@/components/layout/PageHeader";
import { SiteExplanationHierarchy } from "@/components/explanation/SiteExplanationHierarchy";
import { HypothesisCard } from "@/components/hypothesis/HypothesisCard";
import { StatusBadge } from "@/components/ui/StatusBadge";
import { formatUnknownValue, normalizeDisplayLabel, normalizeDisplaySentence } from "@/lib/displayLabels";
import { cleanSiteExplanationBundle, useReviewState, type CandidateGenerationSummary } from "@/lib/reviewState";
import type { Hypothesis } from "@/lib/types";

type JsonRecord = Record<string, unknown>;

const METHOD_LABELS: Record<string, string> = {
  equal_weight: "Equal Weight",
  risk_parity: "Risk Parity",
  hierarchical_risk_parity: "HRP",
  hrp: "HRP",
  minimum_variance: "Minimum Variance",
  minimum_cvar: "Minimum CVaR",
  maximum_diversification: "Maximum Diversification"
};

const MVP_METHOD_IDS = new Set(Object.keys(METHOD_LABELS));

const SAMPLE_CARDS: JsonRecord[] = [
  {
    card_id: "sample_reference_comparison",
    title: "Compare against reference candidates",
    goal: "Reference comparison",
    hypothesis_to_test: "Test whether the current portfolio still earns its complexity against simple reference candidates.",
    card_type: "reference_benchmark_test",
    launch_status: "reference_test",
    why_this_test: "Evidence is mixed. A simple Equal Weight and Risk Parity comparison gives the advisor a clean professional baseline before forming a verdict.",
    default_method: "equal_weight",
    suggested_methods: [
      { candidate_method_id: "equal_weight", method_role: "reference_benchmark" },
      { candidate_method_id: "risk_parity", method_role: "reference_benchmark" }
    ],
    success_criteria: [
      "Current portfolio remains competitive on risk-adjusted return.",
      "Stress loss and drawdown do not materially worsen versus the reference candidate.",
      "Risk concentration is not meaningfully higher than the reference candidate."
    ],
    tradeoff_to_watch: "Reference candidates may reduce concentration, but they can also dilute intentional exposures.",
    decision_boundary: "This test candidate is for comparison only. A recommendation can be formed only after comparison and verdict."
  },
  {
    card_id: "sample_monitor_current",
    title: "Monitor current portfolio",
    goal: "Monitor current portfolio",
    card_type: "monitor_or_data_step",
    launch_status: "monitor",
    why_this_test: "If the advisor does not want to test a reference candidate, keep the current portfolio under monitoring until stronger evidence appears.",
    success_criteria: ["Stress loss, concentration, and hedge behavior remain within advisor tolerance."],
    tradeoff_to_watch: "Monitoring avoids turnover, but it does not test whether a simpler reference candidate would improve the case.",
    decision_boundary: "Monitoring is not candidate generation and not a rebalance recommendation."
  }
];

const SAMPLE_BUILDER_DOCUMENT: JsonRecord = {
  selected_card_id: "sample_reference_comparison",
  can_generate_candidate: true,
  builder_prefill: {
    goal: "Reference comparison",
    suggested_method: "equal_weight",
    constraint_preset: "basic_reference",
    success_criteria: [
      "Current portfolio remains competitive on risk-adjusted return.",
      "Stress loss and drawdown do not materially worsen versus the reference candidate.",
      "Risk concentration is not meaningfully higher than the reference candidate."
    ]
  },
  candidate_setup: {
    goal: "Reference comparison",
    selected_method: "equal_weight",
    can_generate_candidate: true,
    parameters: {
      mode: "capped",
      constraint_preset: "basic_reference"
    },
    success_criteria: [
      "Current portfolio remains competitive on risk-adjusted return.",
      "Stress loss and drawdown do not materially worsen versus the reference candidate.",
      "Risk concentration is not meaningfully higher than the reference candidate."
    ]
  }
};

function sampleCandidateGeneration(): CandidateGenerationSummary {
  return {
    status: "completed",
    stage: "candidate_generation",
    selectedCardId: "sample_reference_comparison",
    candidateId: "equal_weight_reference_candidate",
    generationStatus: "generated",
    canCompare: true,
    weights: [
      { ticker: "VOO", weight: 0.2 },
      { ticker: "VEA", weight: 0.2 },
      { ticker: "VWO", weight: 0.2 },
      { ticker: "BND", weight: 0.2 },
      { ticker: "GLD", weight: 0.2 }
    ],
    generatedAt: new Date().toISOString()
  };
}

function isRecord(value: unknown): value is JsonRecord {
  return Boolean(value) && typeof value === "object" && !Array.isArray(value);
}

function getArray(value: unknown): unknown[] {
  return Array.isArray(value) ? value : [];
}

function optionalText(value: unknown) {
  return typeof value === "string" && value.trim() ? value : undefined;
}

function firstText(...values: unknown[]) {
  for (const value of values) {
    const text = optionalText(value);
    if (text) return text;
  }
  return undefined;
}

function textValue(value: unknown, fallback = "Prepare selected test first") {
  return typeof value === "string" && value.trim() ? value : fallback;
}

function booleanValue(value: unknown, fallback = false) {
  return typeof value === "boolean" ? value : fallback;
}

function displayLabel(value: unknown, fallback = "Unavailable") {
  return normalizeDisplayLabel(value, fallback);
}

function displaySentence(value: unknown, fallback = "Supporting evidence is unavailable.") {
  return normalizeDisplaySentence(value, fallback);
}

function formatWeight(value: number) {
  return `${(value * 100).toFixed(2).replace(/\.?0+$/, "")}%`;
}

function formatOptionalWeight(value: unknown) {
  return typeof value === "number" && Number.isFinite(value) ? formatWeight(value) : undefined;
}

function methodId(value: unknown) {
  const raw = optionalText(value)?.toLowerCase().trim().replace(/[\s-]+/g, "_");
  if (!raw) return undefined;
  if (raw === "hrp") return "hierarchical_risk_parity";
  return raw;
}

function methodLabel(value: unknown) {
  const id = methodId(value);
  return id ? METHOD_LABELS[id] ?? displayLabel(id) : "Select a test approach";
}

function rawMethodIds(card?: JsonRecord) {
  if (!card) return [];
  const suggested = getArray(card.suggested_methods)
    .filter(isRecord)
    .map((method) => methodId(method.candidate_method_id))
    .filter((item): item is string => Boolean(item));
  const defaultMethod = methodId(card.default_method);
  return Array.from(new Set([defaultMethod, ...suggested].filter((item): item is string => Boolean(item))));
}

function cardText(card?: JsonRecord) {
  if (!card) return "";
  return [
    card.card_type,
    card.launch_status,
    card.title,
    card.goal,
    card.description,
    card.hypothesis_to_test,
    card.why_this_test,
    card.source_diagnosis_id,
    card.source_problem_id,
    card.source_problem_label
  ]
    .map((value) => optionalText(value)?.toLowerCase() ?? "")
    .join(" ");
}

function isMonitoringCard(card: JsonRecord) {
  const raw = cardText(card);
  return raw.includes("monitor") || raw.includes("keep current portfolio");
}

function isDataQualityCard(card: JsonRecord) {
  const raw = cardText(card);
  return raw.includes("data quality") || raw.includes("evidence_insufficient") || raw.includes("resolve_data");
}

function diagnosisKindFromText(value: string) {
  const raw = value.toLowerCase();
  if (raw.includes("data quality") || raw.includes("evidence_insufficient")) return "data_quality";
  if (raw.includes("crisis") || raw.includes("tail") || raw.includes("drawdown") || raw.includes("cvar")) return "crisis";
  if (raw.includes("concentration") || raw.includes("diversification") || raw.includes("duplicate")) return "diversification";
  if (raw.includes("mixed") || raw.includes("acceptable") || raw.includes("reference")) return "reference";
  return "reference";
}

function contextualMethodIds(card?: JsonRecord, diagnosisText = "") {
  if (card && (isMonitoringCard(card) || isDataQualityCard(card))) return [];
  const rawCard = cardText(card);
  const kind = diagnosisKindFromText(`${diagnosisText} ${rawCard}`);
  const cardMethods = rawMethodIds(card);
  const rawMethods = cardMethods.filter((id) => MVP_METHOD_IDS.has(id));
  if (card && (!cardMethods.length || !rawMethods.length)) return [];
  if (kind === "data_quality") return [];
  if (kind === "crisis") {
    const preferred = ["minimum_cvar", "minimum_variance"];
    return rawMethods.length ? preferred.filter((id) => rawMethods.includes(id)) : preferred;
  }
  if (kind === "diversification") {
    const preferred = ["risk_parity", "equal_weight", "hierarchical_risk_parity", "maximum_diversification"];
    return rawMethods.length ? preferred.filter((id) => rawMethods.includes(id)).concat(rawMethods.filter((id) => !preferred.includes(id))) : preferred;
  }
  return ["equal_weight", "risk_parity"];
}

function isVisibleMvpCandidateCard(card: JsonRecord, diagnosisText: string) {
  const raw = cardText(card);
  if (isMonitoringCard(card) || isDataQualityCard(card)) return false;
  if (raw.includes("disabled") || raw.includes("unsupported") || raw.includes("blocked")) return false;
  return contextualMethodIds(card, diagnosisText).length > 0;
}

function evidenceText(value: unknown) {
  if (typeof value === "string" && value.trim()) return displaySentence(value);
  if (!isRecord(value)) return undefined;
  return firstText(value.summary, value.label_en, value.title, value.description, value.interpretation, value.value);
}

function safeErrorText(value: unknown, fallback: string) {
  if (!isRecord(value)) return fallback;
  const message = displaySentence(value.error, fallback)
    .replace(/\bJ(?:SON)\b/g, "request")
    .replace(/\bback(?:end)\b/gi, "service");
  const details = value.details;
  if (typeof details === "string" && details.trim()) {
    return `${message} ${displaySentence(details).replace(/\bJ(?:SON)\b/g, "request").replace(/\bback(?:end)\b/gi, "service")}`;
  }
  if (Array.isArray(details)) {
    const safeDetails = details
      .map((item) => (typeof item === "string" ? displaySentence(item).replace(/\bJ(?:SON)\b/g, "request").replace(/\bback(?:end)\b/gi, "service") : ""))
      .filter(Boolean)
      .join(" ");
    return safeDetails ? `${message} ${safeDetails}` : message;
  }
  return message;
}

function cardMatchesRecommendedTest(card: JsonRecord, recommendedNextTest: string) {
  const haystack = `${cardText(card)} ${rawMethodIds(card).join(" ")}`;
  const recommended = recommendedNextTest.toLowerCase();
  if ((recommended.includes("equal weight") || recommended.includes("risk parity") || recommended.includes("reference"))
    && (haystack.includes("equal_weight") || haystack.includes("equal weight") || haystack.includes("risk_parity") || haystack.includes("risk parity") || haystack.includes("reference"))) {
    return true;
  }
  if ((recommended.includes("minimum variance") || recommended.includes("minimum cvar") || recommended.includes("risk reduction"))
    && (haystack.includes("minimum_variance") || haystack.includes("minimum cvar") || haystack.includes("minimum_cvar") || haystack.includes("risk reduction"))) {
    return true;
  }
  if ((recommended.includes("hrp") || recommended.includes("maximum diversification") || recommended.includes("diversification"))
    && (haystack.includes("hrp") || haystack.includes("hierarchical_risk_parity") || haystack.includes("maximum_diversification") || haystack.includes("diversification"))) {
    return true;
  }
  return recommended ? haystack.includes(recommended) : false;
}

function defaultSelectedCardId(cards: JsonRecord[], recommendedNextTest: string, primaryCardId?: string) {
  const candidateCards = cards.filter((card) => !isMonitoringCard(card) && !isDataQualityCard(card));
  if (!candidateCards.length) return null;
  const recommendedMatch = candidateCards.find((card) => cardMatchesRecommendedTest(card, recommendedNextTest));
  if (recommendedMatch) return textValue(recommendedMatch.card_id, "");
  const primaryMatch = primaryCardId
    ? candidateCards.find((card) => textValue(card.card_id, "") === primaryCardId)
    : undefined;
  return textValue(primaryMatch?.card_id ?? candidateCards[0]?.card_id, "");
}

function launchpadCardToHypothesis(card: JsonRecord, diagnosisText = ""): Hypothesis {
  const isMonitor = isMonitoringCard(card);
  const methods = contextualMethodIds(card, diagnosisText);
  const successCriteria = getArray(card.success_criteria)
    .map((item) => textValue(item, ""))
    .filter(Boolean);

  return {
    id: textValue(card.card_id, textValue(card.title, "launchpad-card")),
    title: displayLabel(card.title, isMonitor ? "Monitor current portfolio" : "Compare against reference candidates"),
    targetProblem: displaySentence(
      firstText(card.hypothesis_to_test, card.what_this_tests_en, card.goal, card.description),
      isMonitor
        ? "Monitor the current portfolio until stronger evidence appears."
        : "Test whether the current portfolio should be compared against a simple candidate."
    ),
    expectedTradeoff: displaySentence(
      firstText(card.tradeoff_to_watch, card.expected_tradeoff_to_check_en),
      isMonitor
        ? "Monitoring avoids unnecessary turnover, but it does not test a candidate."
        : "Avoid unnecessary turnover unless comparison evidence shows a material improvement."
    ),
    methodId: methods[0] ?? methodId(card.default_method) ?? "equal_weight",
    evidenceSource: displaySentence(
      firstText(card.why_this_test, card.why_this_path_en),
      isMonitor
        ? "Use monitoring when evidence does not justify a candidate test."
        : "This test checks the diagnosis against a simple professional reference."
    ),
    status: isMonitor ? "Monitor current portfolio" : "Ready to test",
    testType: isMonitor ? "Monitoring path" : "Reference comparison",
    suggestedMethods: methods.map((id) => METHOD_LABELS[id] ?? displayLabel(id)),
    successCriteria: successCriteria.length
      ? successCriteria.map((item) => displaySentence(item))
      : [
          "The current portfolio should remain competitive on risk-adjusted return, stress loss, drawdown, and concentration."
        ],
    decisionBoundary: displaySentence(
      card.decision_boundary,
      "Candidates are test portfolios for comparison. They are not recommendations."
    )
  };
}

type ProblemClassificationView = {
  available: boolean;
  headline: string;
  explanation: string;
  rootCause?: string;
  evidence: string[];
  confidence?: string;
  materiality?: string;
  actionability?: string;
  nextStep: string;
  recommendedTestName: string;
  recommendedReason: string;
  recommendedMethods: string[];
  successCriteria: string[];
};

function buildProblemClassificationView({
  problemClassification,
  primaryProblem,
  problemSeverity,
  problemConfidence,
  suggestedActionPaths,
  recommendedFirstTest
}: {
  problemClassification: unknown;
  primaryProblem?: string;
  problemSeverity?: string;
  problemConfidence?: string;
  suggestedActionPaths?: string[];
  recommendedFirstTest?: string;
}): ProblemClassificationView {
  const problem = isRecord(problemClassification) ? problemClassification : undefined;
  const primaryDiagnosis = isRecord(problem?.primary_diagnosis) ? problem.primary_diagnosis : undefined;
  const rootCause = isRecord(primaryDiagnosis?.root_cause) ? primaryDiagnosis.root_cause : undefined;
  const nextDiagnosticStep = isRecord(problem?.next_diagnostic_step) ? problem.next_diagnostic_step : undefined;
  const actionability = isRecord(problem?.actionability)
    ? problem.actionability
    : isRecord(primaryDiagnosis?.actionability)
      ? primaryDiagnosis.actionability
      : undefined;
  const diagnosisText = [
    primaryDiagnosis?.diagnosis_id,
    primaryDiagnosis?.label_en,
    primaryDiagnosis?.thesis_en,
    rootCause?.problem_id,
    rootCause?.label_en,
    primaryProblem,
    recommendedFirstTest,
    suggestedActionPaths?.join(" ")
  ]
    .map((value) => optionalText(value) ?? "")
    .join(" ");
  const kind = diagnosisKindFromText(diagnosisText);
  const available = Boolean(problem || primaryProblem);
  const evidence = [
    ...getArray(primaryDiagnosis?.key_evidence),
    ...getArray(problem?.key_evidence)
  ]
    .map(evidenceText)
    .filter((item): item is string => Boolean(item))
    .slice(0, 5);
  const successCriteria = getArray(problem?.success_criteria)
    .map((item) => displaySentence(item))
    .filter(Boolean)
    .slice(0, 4);

  if (!available) {
    return {
      available: false,
      headline: "Current diagnosis is unavailable",
      explanation: "Run the portfolio review before selecting a test path.",
      evidence: [],
      nextStep: "Run portfolio diagnosis first",
      recommendedTestName: "Run diagnosis first",
      recommendedReason: "A test path needs a current diagnosis and stress evidence.",
      recommendedMethods: [],
      successCriteria: []
    };
  }

  if (kind === "data_quality") {
    return {
      available: true,
      headline: "Resolve data quality first",
      explanation: "The evidence is not reliable enough to create a candidate test. The professional next step is to improve data quality before comparing portfolios.",
      rootCause: displayLabel(firstText(rootCause?.label_en, primaryDiagnosis?.label_en, primaryProblem), "Evidence quality issue"),
      evidence,
      confidence: displayLabel(firstText(primaryDiagnosis?.confidence, problemConfidence, problem?.confidence), ""),
      materiality: displayLabel(firstText(problem?.materiality, problemSeverity, primaryDiagnosis?.materiality), ""),
      actionability: displayLabel(firstText(actionability?.label_en, actionability?.status, actionability?.level), ""),
      nextStep: "Resolve data quality first",
      recommendedTestName: "Resolve data quality first",
      recommendedReason: "Candidate generation should wait until the evidence is reliable enough for comparison.",
      recommendedMethods: [],
      successCriteria
    };
  }

  const methods = contextualMethodIds(undefined, diagnosisText).map((id) => METHOD_LABELS[id] ?? displayLabel(id));
  return {
    available: true,
    headline: "No immediate rebalance is justified yet",
    explanation: kind === "reference"
      ? "Evidence is mixed. No direct rebalance is justified yet. The next professional step is to test the current portfolio against simple reference candidates before forming a verdict."
      : "The diagnosis points to a testable weakness, but it is not a verdict. The next professional step is to generate one diagnostic candidate and compare trade-offs before any action logic is formed.",
    rootCause: displayLabel(firstText(rootCause?.label_en, primaryDiagnosis?.label_en, primaryProblem), "Mixed evidence / no immediate rebalance"),
    evidence,
    confidence: displayLabel(firstText(primaryDiagnosis?.confidence, problemConfidence, problem?.confidence), ""),
    materiality: displayLabel(firstText(problem?.materiality, problemSeverity, primaryDiagnosis?.materiality), ""),
    actionability: displayLabel(firstText(actionability?.label_en, actionability?.status, actionability?.level), ""),
    nextStep: displaySentence(
      firstText(nextDiagnosticStep?.label, nextDiagnosticStep?.label_en, recommendedFirstTest, suggestedActionPaths?.[0]),
      "Compare against reference candidates"
    ).replace(/\bcompare\s+against\s+simple\s+references\b/i, "Compare against reference candidates"),
    recommendedTestName: kind === "reference" ? "Compare against reference candidates" : "Test one diagnostic candidate",
    recommendedReason: kind === "reference"
      ? "Simple references reveal whether the current allocation is defensible before an advisor considers any rebalance discussion."
      : "One selected candidate isolates the diagnosed weakness so the next page can evaluate improvement, deterioration, turnover, and materiality.",
    recommendedMethods: methods.length ? methods : ["Equal Weight", "Risk Parity"],
    successCriteria: successCriteria.length
      ? successCriteria
      : [
          "Current portfolio remains competitive on risk-adjusted return.",
          "Stress loss and drawdown do not materially worsen versus the candidate.",
          "Risk concentration is not meaningfully higher than the candidate."
        ]
  };
}

function FieldRow({ label, children }: { label: string; children: ReactNode }) {
  return (
    <div>
      <dt className="pmri-label">{label}</dt>
      <dd className="mt-1 text-sm leading-6 text-pmri-text2">{children}</dd>
    </div>
  );
}

function TextList({ items, empty = "Review the selected test first" }: { items: unknown[]; empty?: string }) {
  const rows = items.map((item) => formatUnknownValue(item, "")).filter(Boolean);
  if (!rows.length) return <span>{empty}</span>;
  return (
    <ul className="space-y-2">
      {rows.map((item) => (
        <li key={item} className="flex gap-2">
          <span className="mt-2 h-1.5 w-1.5 shrink-0 rounded-full bg-pmri-blue" />
          <span>{item}</span>
        </li>
      ))}
    </ul>
  );
}

function WorkflowRail() {
  const steps = ["Current Diagnosis", "Recommended Test", "Available Test Paths", "Selected Test Setup", "Generate Test Candidate", "Test Candidate Generated", "Continue to Comparison"];
  return (
    <div className="mb-5 overflow-x-auto rounded-2xl border border-pmri-border/45 bg-white/[0.025] p-3">
      <div className="flex min-w-max items-center gap-2 text-xs text-pmri-muted">
        {steps.map((step, index) => (
          <div key={step} className="flex items-center gap-2">
            <span className="rounded-full border border-white/10 bg-white/[0.035] px-3 py-1.5">{step}</span>
            {index < steps.length - 1 ? <span className="text-pmri-blueSoft">→</span> : null}
          </div>
        ))}
      </div>
    </div>
  );
}

function CurrentDiagnosisSection({ view }: { view: ProblemClassificationView }) {
  const fields = [
    view.confidence ? ["Confidence", view.confidence] : undefined,
    view.materiality ? ["Materiality", view.materiality] : undefined,
    view.actionability ? ["Actionability", view.actionability] : undefined,
    ["Next step", view.nextStep]
  ].filter(Boolean) as Array<[string, string]>;

  return (
    <section className="pmri-card mb-5 rounded-3xl p-6">
      <div className="flex flex-col gap-3 sm:flex-row sm:items-start sm:justify-between">
        <div>
          <p className="pmri-label">Current Diagnosis</p>
          <h2 className="pmri-heading-section mt-2 text-2xl text-pmri-text">{view.headline}</h2>
        </div>
        <StatusBadge tone={view.available ? "blue" : "amber"}>
          {view.available ? "Diagnosis loaded" : "Run diagnosis first"}
        </StatusBadge>
      </div>

      <p className="mt-4 max-w-4xl text-sm leading-7 text-pmri-text2">{view.explanation}</p>

      {view.rootCause ? (
        <div className="mt-5 rounded-2xl border border-white/10 bg-white/[0.03] p-4">
          <p className="pmri-label">Root cause / status</p>
          <p className="mt-1 text-sm leading-6 text-pmri-text">{view.rootCause}</p>
        </div>
      ) : null}

      {view.evidence.length ? (
        <div className="mt-5">
          <p className="pmri-label">Key evidence</p>
          <ul className="mt-3 grid gap-2 lg:grid-cols-2">
            {view.evidence.slice(0, 5).map((item) => (
              <li key={item} className="rounded-2xl border border-white/10 bg-white/[0.03] p-3 text-sm leading-6 text-pmri-text2">
                {item}
              </li>
            ))}
          </ul>
        </div>
      ) : null}

      <dl className="mt-5 grid gap-3 md:grid-cols-4">
        {fields.map(([label, value]) => (
          <div key={label} className="rounded-2xl border border-white/10 bg-white/[0.03] p-3">
            <dt className="pmri-label">{label}</dt>
            <dd className="mt-1 text-sm text-pmri-text">{value}</dd>
          </div>
        ))}
      </dl>
    </section>
  );
}

function RecommendedTestSection({ view }: { view: ProblemClassificationView }) {
  return (
    <section className="mb-5 rounded-3xl border border-pmri-blue/25 bg-pmri-blue/10 p-6">
      <div className="flex flex-col gap-4 md:flex-row md:items-start md:justify-between">
        <div>
          <p className="pmri-label text-pmri-blueSoft">Recommended Test</p>
          <h2 className="pmri-heading-section mt-2 text-2xl text-pmri-text">{view.recommendedTestName}</h2>
          <p className="mt-3 max-w-3xl text-sm leading-7 text-pmri-text2">{view.recommendedReason}</p>
        </div>
        <StatusBadge tone={view.recommendedMethods.length ? "blue" : "amber"}>
          {view.recommendedMethods.length ? "Diagnostic test" : "Resolve data first"}
        </StatusBadge>
      </div>
      <div className="mt-5 grid gap-4 lg:grid-cols-2">
        <div className="rounded-2xl border border-white/10 bg-white/[0.03] p-4">
          <p className="pmri-label">Suggested test approach</p>
          {view.recommendedMethods.length ? (
            <div className="mt-3 flex flex-wrap gap-2">
              {view.recommendedMethods.map((method) => (
                <span key={method} className="rounded-full border border-pmri-blue/25 bg-pmri-blue/10 px-3 py-1 text-sm text-pmri-text">
                  {method}
                </span>
              ))}
            </div>
          ) : (
            <p className="mt-3 text-sm leading-6 text-pmri-text2">Resolve data quality first.</p>
          )}
        </div>
        <div className="rounded-2xl border border-white/10 bg-white/[0.03] p-4">
          <p className="pmri-label">Success criteria</p>
          <div className="mt-3 text-sm leading-6 text-pmri-text2">
            <TextList items={view.successCriteria} />
          </div>
        </div>
      </div>
    </section>
  );
}

function DecisionBoundaryBlock() {
  return (
    <div className="mb-5 rounded-2xl border border-pmri-amber/25 bg-pmri-amber/10 p-4">
      <p className="pmri-label text-pmri-amber">Decision Boundary</p>
      <p className="mt-2 text-sm leading-6 text-pmri-text">
        Candidates are test portfolios for comparison. They are not recommendations. A verdict is formed only after comparison.
      </p>
    </div>
  );
}

function MonitoringAlternative({ cards }: { cards: Hypothesis[] }) {
  if (!cards.length) return null;
  return (
    <div className="mt-5 rounded-2xl border border-pmri-border/60 bg-white/[0.022] p-4">
      <div className="flex flex-col gap-3 sm:flex-row sm:items-start sm:justify-between">
        <div>
          <p className="pmri-label">Secondary follow-up path</p>
          <h3 className="pmri-heading-section mt-1 text-lg text-pmri-text">Monitor current portfolio</h3>
          <p className="mt-2 max-w-2xl text-sm leading-6 text-pmri-muted">
            Use monitoring when the advisor chooses not to generate a candidate. Monitoring does not create a test portfolio.
          </p>
        </div>
        <StatusBadge tone="slate">No generated candidate</StatusBadge>
      </div>
      <ul className="mt-3 space-y-2 text-sm leading-6 text-pmri-text2">
        {cards.flatMap((card) => card.successCriteria ?? []).slice(0, 3).map((item) => (
          <li key={item}>• {item}</li>
        ))}
      </ul>
    </div>
  );
}

function AvailableTestPathsSection({
  realCards,
  monitoringCards,
  selectedCardId,
  onSelect
}: {
  realCards: Hypothesis[];
  monitoringCards: Hypothesis[];
  selectedCardId: string | null;
  onSelect: (id: string) => void;
}) {
  const selectedCard = realCards.find((card) => card.id === selectedCardId) ?? realCards[0];
  const otherCards = realCards.filter((card) => card.id !== selectedCard?.id);
  return (
    <section>
      <div className="mb-3 flex flex-col gap-2 sm:flex-row sm:items-end sm:justify-between">
        <div>
          <p className="pmri-label">Available test paths</p>
          <h2 className="pmri-heading-section mt-1 text-xl text-pmri-text">Choose one hypothesis to test</h2>
        </div>
        <p className="max-w-lg text-sm leading-6 text-pmri-muted">Test paths are hypotheses. They are not ready-made portfolios.</p>
      </div>
      {selectedCard ? (
        <HypothesisCard
          hypothesis={selectedCard}
          isPrimary
          isSelected
          onSelect={() => onSelect(selectedCard.id)}
        />
      ) : (
        <div className="rounded-2xl border border-pmri-amber/35 bg-pmri-amber/10 p-4 text-sm leading-6 text-pmri-amber">
          Resolve data quality first.
        </div>
      )}
      {otherCards.length ? (
        <div className="mt-5 grid gap-4 lg:grid-cols-2">
          {otherCards.map((card) => (
            <HypothesisCard
              key={card.id}
              hypothesis={card}
              isSelected={selectedCardId === card.id}
              onSelect={() => onSelect(card.id)}
            />
          ))}
        </div>
      ) : null}
      <MonitoringAlternative cards={monitoringCards} />
    </section>
  );
}

function candidateStatusLabel(candidate?: CandidateGenerationSummary) {
  if (!candidate) return "Not generated yet";
  const status = candidate.generationStatus.toLowerCase();
  if (candidate.canCompare) return "Ready for comparison";
  if (status.includes("infeasible")) return "Infeasible";
  if (status.includes("unsupported")) return "Unsupported";
  if (status.includes("fail")) return "Generation failed";
  return "Generated";
}

function candidateDisplayName(candidate: CandidateGenerationSummary, selectedMethod: string) {
  if (candidate.candidateId.includes("equal_weight")) return "Equal Weight Reference Candidate";
  if (candidate.candidateId.includes("risk_parity")) return "Risk Parity Reference Candidate";
  if (candidate.candidateId) return displayLabel(candidate.candidateId, `${selectedMethod} Test Candidate`);
  return `${selectedMethod} Test Candidate`;
}

function weightPreview(weights: CandidateGenerationSummary["weights"], method: string) {
  if (!weights.length) return "Weight preview will appear when the candidate is ready.";
  const equal = weights.every((item) => Math.abs(item.weight - weights[0].weight) < 0.0001);
  return equal
    ? `${weights.length} holdings · ${formatWeight(weights[0].weight)} each · Reference candidate`
    : `${weights.length} holdings · ${method} · Test candidate`;
}

function BuilderSetupPanel({
  selectedCard,
  builderDocument,
  reviewId,
  candidateGeneration,
  isGenerating,
  generationError,
  onGenerate,
  comparisonHref
}: {
  selectedCard?: JsonRecord;
  builderDocument?: JsonRecord;
  reviewId?: string;
  candidateGeneration?: CandidateGenerationSummary;
  isGenerating: boolean;
  generationError?: string;
  onGenerate: () => void;
  comparisonHref: string;
}) {
  if (!selectedCard) {
    return (
      <aside className="pmri-card rounded-2xl p-6 xl:sticky xl:top-5">
        <p className="pmri-label">Selected test setup</p>
        <h3 className="pmri-heading-section mt-2 text-lg text-pmri-text">Choose a test path first.</h3>
        <p className="mt-4 text-sm leading-6 text-pmri-muted">
          The setup panel will show one selected goal, one test approach, and the next action.
        </p>
      </aside>
    );
  }

  const selectedCardId = textValue(selectedCard.card_id, "");
  const builderMatches = isRecord(builderDocument) && textValue(builderDocument.selected_card_id, "") === selectedCardId;
  const builderPrefill = builderMatches && isRecord(builderDocument?.builder_prefill) ? builderDocument.builder_prefill : undefined;
  const candidateSetup = builderMatches && isRecord(builderDocument?.candidate_setup) ? builderDocument.candidate_setup : undefined;
  const parameters = isRecord(candidateSetup?.parameters) ? candidateSetup.parameters : undefined;
  const candidateForSelectedCard = candidateGeneration?.selectedCardId === selectedCardId ? candidateGeneration : undefined;
  const selectedTitle = displayLabel(selectedCard.title, "Selected test");
  const selectedGoal = displayLabel(firstText(candidateSetup?.goal, builderPrefill?.goal, selectedCard.goal, selectedCard.hypothesis_to_test), selectedTitle);
  const selectedMethodId = methodId(firstText(candidateSetup?.selected_method, builderPrefill?.suggested_method, selectedCard.default_method, contextualMethodIds(selectedCard)[0]));
  const selectedMethod = selectedMethodId ? METHOD_LABELS[selectedMethodId] ?? displayLabel(selectedMethodId) : "Select a test approach";
  const successCriteria = getArray(candidateSetup?.success_criteria).length
    ? getArray(candidateSetup?.success_criteria)
    : getArray(builderPrefill?.success_criteria).length
      ? getArray(builderPrefill?.success_criteria)
      : getArray(selectedCard.success_criteria);
  const constraintPreset = firstText(parameters?.constraint_preset, builderPrefill?.constraint_preset);
  const mode = firstText(parameters?.mode, builderPrefill?.mode);
  const minWeight = formatOptionalWeight(parameters?.min_asset_weight ?? builderPrefill?.min_asset_weight);
  const maxWeight = formatOptionalWeight(parameters?.max_asset_weight ?? builderPrefill?.max_asset_weight);
  const isReferenceMethod = selectedMethodId === "equal_weight" || selectedMethodId === "risk_parity";
  const showConstraintPreset = Boolean(constraintPreset && !(isReferenceMethod && constraintPreset === "basic_reference"));
  const showMode = Boolean(mode && !(isReferenceMethod && mode === "capped"));
  const canGenerate = Boolean(reviewId && selectedCardId && selectedMethodId && MVP_METHOD_IDS.has(selectedMethodId) && !isDataQualityCard(selectedCard) && !isMonitoringCard(selectedCard));
  const status = candidateStatusLabel(candidateForSelectedCard);

  return (
    <aside className="pmri-card rounded-2xl p-6 xl:sticky xl:top-5">
      <div className="flex items-start justify-between gap-3">
        <div>
          <p className="pmri-label">Selected test setup</p>
          <h3 className="pmri-heading-section mt-2 text-lg text-pmri-text">{selectedTitle}</h3>
        </div>
        <StatusBadge tone={candidateForSelectedCard?.canCompare ? "green" : candidateForSelectedCard ? "amber" : "blue"}>
          {status}
        </StatusBadge>
      </div>

      <dl className="mt-6 space-y-4">
        <FieldRow label="Selected goal">{selectedGoal}</FieldRow>
        <FieldRow label="Test approach">{selectedMethod}</FieldRow>
        {showConstraintPreset ? <FieldRow label="Simple guardrail">{displayLabel(constraintPreset)}</FieldRow> : null}
        {showMode ? <FieldRow label="Test style">{displayLabel(mode)}</FieldRow> : null}
        {minWeight || maxWeight ? (
          <FieldRow label="Weight bounds">
            {[minWeight ? `Minimum ${minWeight}` : undefined, maxWeight ? `Maximum ${maxWeight}` : undefined].filter(Boolean).join(" · ")}
          </FieldRow>
        ) : null}
        <FieldRow label="Success criteria">
          <TextList items={successCriteria} empty="Comparison will check whether this test improves the diagnosis." />
        </FieldRow>
        <FieldRow label="Test candidate state">
          <span className={candidateForSelectedCard?.canCompare ? "text-pmri-positive" : "text-pmri-text2"}>{status}</span>
        </FieldRow>
      </dl>

      <div className="mt-6 space-y-3">
        {candidateForSelectedCard ? (
          <>
            <div className="rounded-2xl border border-pmri-green/30 bg-pmri-green/10 p-4">
              <p className="pmri-label text-pmri-positive">Test candidate generated</p>
              <p className="mt-1 text-sm font-medium text-pmri-text">{candidateDisplayName(candidateForSelectedCard, selectedMethod)}</p>
              <p className="mt-2 text-sm leading-6 text-pmri-text2">{weightPreview(candidateForSelectedCard.weights, selectedMethod)}</p>
              {candidateForSelectedCard.weights.length ? (
                <details className="mt-3 text-xs text-pmri-text2">
                  <summary className="cursor-pointer text-pmri-blueSoft">View weights</summary>
                  <ul className="mt-3 grid gap-2">
                    {candidateForSelectedCard.weights.map((item) => (
                      <li key={item.ticker} className="flex justify-between rounded-lg bg-white/[0.04] px-3 py-2">
                        <span>{item.ticker}</span>
                        <span>{formatWeight(item.weight)}</span>
                      </li>
                    ))}
                  </ul>
                </details>
              ) : null}
            </div>
            <p className="text-sm leading-6 text-pmri-text2">
              Next step: compare the current portfolio with {candidateDisplayName(candidateForSelectedCard, selectedMethod)}.
            </p>
            {candidateForSelectedCard.canCompare ? (
              <Link
                href={comparisonHref}
                className="pmri-focus pmri-primary-action flex w-full items-center justify-center rounded-full px-5 py-3 text-sm font-semibold transition"
              >
                Continue to Comparison
              </Link>
            ) : (
              <button
                type="button"
                disabled
                className="w-full cursor-not-allowed rounded-full border border-white/10 bg-white/10 px-5 py-3 text-sm font-medium text-pmri-muted"
              >
                Comparison needs a usable test candidate
              </button>
            )}
          </>
        ) : (
          <>
            <button
              type="button"
              disabled={!canGenerate || isGenerating}
              onClick={onGenerate}
              className={`w-full rounded-full border px-5 py-3 text-sm font-medium transition ${
                canGenerate && !isGenerating
                  ? "pmri-focus pmri-primary-action"
                  : "cursor-not-allowed border-white/10 bg-white/10 text-pmri-muted"
              }`}
            >
              {isGenerating ? "Generating test candidate..." : "Generate test candidate"}
            </button>
            {!canGenerate ? (
              <p className="rounded-xl border border-pmri-amber/35 bg-pmri-amber/10 p-3 text-sm leading-6 text-pmri-amber">
                Resolve data quality first.
              </p>
            ) : null}
          </>
        )}
        {generationError ? (
          <p className="rounded-xl border border-pmri-red/35 bg-pmri-red/10 p-3 text-xs leading-5 text-pmri-red">
            {generationError}
          </p>
        ) : null}
      </div>
    </aside>
  );
}

function EmptyState({ title, description }: { title: string; description: string }) {
  return (
    <section className="pmri-card rounded-3xl p-6">
      <p className="text-lg font-medium text-pmri-text">{title}</p>
      <p className="mt-2 max-w-2xl text-sm leading-6 text-pmri-muted">{description}</p>
      <Link
        href="/portfolio-input"
        className="pmri-focus mt-5 inline-flex rounded-full border border-pmri-blue/50 bg-pmri-blue px-5 py-2.5 text-sm font-medium text-pmri-bg shadow-decision transition hover:bg-pmri-blueSoft"
      >
        Go to Portfolio Input
      </Link>
    </section>
  );
}

export default function HypothesisPage() {
  const { activeReview, hydrated, recordBuilderSetup, recordCandidateGeneration } = useReviewState();
  const [sampleMode, setSampleMode] = useState(false);
  const [sampleGenerated, setSampleGenerated] = useState(false);
  const [selectedCardId, setSelectedCardId] = useState<string | null>(null);
  const [isGeneratingCandidate, setIsGeneratingCandidate] = useState(false);
  const [generationError, setGenerationError] = useState<string | undefined>();

  useEffect(() => {
    const params = new URLSearchParams(window.location.search);
    setSampleMode(params.get("sample") === "1");
    setSampleGenerated(params.get("generated") === "1");
  }, []);

  const problemClassification = activeReview?.reviewResult?.outputs?.problem_classification;
  const candidateLaunchpad = activeReview?.reviewResult?.outputs?.candidate_launchpad;
  const compactLaunchpadCards = activeReview?.reviewSummary?.launchpadCards;
  const launchpadRecord = isRecord(candidateLaunchpad)
    ? candidateLaunchpad
    : Array.isArray(compactLaunchpadCards)
      ? { cards: compactLaunchpadCards }
      : undefined;
  const builderOutput = activeReview?.reviewResult?.outputs?.portfolio_alternatives_builder;
  const compactBuilderOutput = activeReview?.builderSetup ?? activeReview?.reviewSummary?.builderSetup;
  const builderRecord = isRecord(compactBuilderOutput) ? compactBuilderOutput : isRecord(builderOutput) ? builderOutput : undefined;
  const rawLaunchpadCards = useMemo(() => getArray(launchpadRecord?.cards).filter(isRecord), [launchpadRecord]);
  const allCandidateRawCards = useMemo(() => rawLaunchpadCards.filter((card) => !isMonitoringCard(card) && !isDataQualityCard(card)), [rawLaunchpadCards]);
  const monitoringRawCards = useMemo(() => rawLaunchpadCards.filter((card) => isMonitoringCard(card) || isDataQualityCard(card)), [rawLaunchpadCards]);
  const problemClassificationView = useMemo(() => buildProblemClassificationView({
    problemClassification,
    primaryProblem: activeReview?.reviewSummary?.primaryProblem,
    problemSeverity: activeReview?.reviewSummary?.problemSeverity,
    problemConfidence: activeReview?.reviewSummary?.problemConfidence,
    suggestedActionPaths: activeReview?.reviewSummary?.suggestedActionPaths,
    recommendedFirstTest: activeReview?.reviewSummary?.recommendedFirstTest
  }), [
    activeReview?.reviewSummary?.primaryProblem,
    activeReview?.reviewSummary?.problemSeverity,
    activeReview?.reviewSummary?.problemConfidence,
    activeReview?.reviewSummary?.suggestedActionPaths,
    activeReview?.reviewSummary?.recommendedFirstTest,
    problemClassification
  ]);
  const diagnosisText = `${problemClassificationView.headline} ${problemClassificationView.rootCause ?? ""} ${problemClassificationView.nextStep}`;
  const candidateRawCards = useMemo(
    () => allCandidateRawCards.filter((card) => isVisibleMvpCandidateCard(card, diagnosisText)),
    [allCandidateRawCards, diagnosisText]
  );
  const realCards = useMemo(() => candidateRawCards.map((card) => launchpadCardToHypothesis(card, diagnosisText)), [candidateRawCards, diagnosisText]);
  const monitoringCards = useMemo(() => monitoringRawCards.map((card) => launchpadCardToHypothesis(card, diagnosisText)), [monitoringRawCards, diagnosisText]);
  const completedRealReview = activeReview?.runMode === "real_run" && activeReview.runStatus === "completed";
  const siteExplanation = cleanSiteExplanationBundle(activeReview?.reviewResult?.outputs?.site_explanation_bundle)
    ?? activeReview?.reviewSummary?.siteExplanation;

  const launchpadRecordView = launchpadRecord as JsonRecord | undefined;
  const launchpadSummary = isRecord(launchpadRecordView?.summary) ? launchpadRecordView.summary : undefined;
  const primaryCardId = optionalText(launchpadSummary?.primary_card_id);
  const resolvedDefaultCardId = useMemo(
    () => defaultSelectedCardId(candidateRawCards, problemClassificationView.nextStep, primaryCardId),
    [candidateRawCards, primaryCardId, problemClassificationView.nextStep]
  );

  useEffect(() => {
    if (sampleMode && !selectedCardId) {
      setSelectedCardId("sample_reference_comparison");
      return;
    }
    if (!resolvedDefaultCardId) return;
    const currentIsValid = selectedCardId
      ? candidateRawCards.some((card) => textValue(card.card_id, "") === selectedCardId)
      : false;
    if (!currentIsValid) setSelectedCardId(resolvedDefaultCardId);
  }, [candidateRawCards, resolvedDefaultCardId, sampleMode, selectedCardId]);

  useEffect(() => {
    setGenerationError(undefined);
  }, [selectedCardId, activeReview?.reviewId]);

  async function handleGenerateCandidate() {
    const reviewId = activeReview?.reviewId ?? activeReview?.reviewSummary?.reviewId ?? activeReview?.reviewResult?.review_id;
    if (!reviewId || !selectedCardId) return;
    setIsGeneratingCandidate(true);
    setGenerationError(undefined);

    try {
      const prepareResponse = await fetch("/api/portfolio/builder/prepare", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          review_id: reviewId,
          selected_card_id: selectedCardId
        })
      });
      const prepareResult = await prepareResponse.json() as unknown;
      if (!prepareResponse.ok || !isRecord(prepareResult) || prepareResult.status !== "completed") {
        setGenerationError(safeErrorText(prepareResult, "The selected test could not be prepared."));
        return;
      }
      recordBuilderSetup(prepareResult);

      const response = await fetch("/api/portfolio/candidate/generate", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          review_id: reviewId,
          selected_card_id: selectedCardId
        })
      });
      const result = await response.json() as unknown;
      if (!response.ok || !isRecord(result) || result.status !== "completed") {
      setGenerationError(safeErrorText(result, "The test candidate could not be generated."));
        return;
      }
      recordCandidateGeneration(result);
    } catch {
      setGenerationError("The test candidate could not be generated. Please try again or choose another test path.");
    } finally {
      setIsGeneratingCandidate(false);
    }
  }

  if (sampleMode) {
    const sampleProblemView: ProblemClassificationView = {
      available: true,
      headline: "No immediate rebalance is justified yet",
      explanation: "Evidence is mixed. No direct rebalance is justified yet. The next professional step is to test the current portfolio against simple reference candidates before forming a verdict.",
      rootCause: "Mixed evidence / no dominant actionable problem",
      evidence: [
        "Stress evidence does not prove a single urgent weakness.",
        "Concentration and risk distribution deserve a simple reference check.",
        "A reference comparison can separate useful complexity from unnecessary complexity."
      ],
      confidence: "Moderate",
      materiality: "Moderate",
      actionability: "Test before action",
      nextStep: "Compare against reference candidates",
      recommendedTestName: "Compare against reference candidates",
      recommendedReason: "Equal Weight and Risk Parity are simple professional references. They help the advisor decide whether the current portfolio deserves to remain unchanged before any verdict is formed.",
      recommendedMethods: ["Equal Weight", "Risk Parity"],
      successCriteria: [
        "Current portfolio remains competitive on risk-adjusted return.",
        "Stress loss and drawdown do not materially worsen versus the reference candidate.",
        "Risk concentration is not meaningfully higher than the reference candidate."
      ]
    };
    const sampleCandidateCards = SAMPLE_CARDS.filter((card) => !isMonitoringCard(card)).map((card) => launchpadCardToHypothesis(card, sampleProblemView.nextStep));
    const sampleMonitoringCards = SAMPLE_CARDS.filter(isMonitoringCard).map((card) => launchpadCardToHypothesis(card, sampleProblemView.nextStep));
    const sampleSelectedCard = SAMPLE_CARDS.find((card) => textValue(card.card_id, "") === (selectedCardId ?? "sample_reference_comparison"));

    return (
      <div>
        <PageHeader
          kicker="Step 04 / Hypothesis"
          title="Hypothesis Builder"
          description="Turn the current diagnosis into one clear candidate test before comparison."
          boundaryNote="Candidates are test portfolios for comparison. They are not recommendations."
        >
          <StatusBadge tone="slate">Sample review</StatusBadge>
        </PageHeader>
        <WorkflowRail />
        <CurrentDiagnosisSection view={sampleProblemView} />
        <RecommendedTestSection view={sampleProblemView} />
        <DecisionBoundaryBlock />
        <div className="grid gap-7 xl:grid-cols-[minmax(0,1fr)_400px]">
          <AvailableTestPathsSection
            realCards={sampleCandidateCards}
            monitoringCards={sampleMonitoringCards}
            selectedCardId={selectedCardId ?? "sample_reference_comparison"}
            onSelect={setSelectedCardId}
          />
          <BuilderSetupPanel
            selectedCard={sampleSelectedCard}
            builderDocument={SAMPLE_BUILDER_DOCUMENT}
            reviewId="frontend_review_sample"
            candidateGeneration={sampleGenerated ? sampleCandidateGeneration() : undefined}
            isGenerating={false}
            generationError={generationError}
            onGenerate={() => setSampleGenerated(true)}
            comparisonHref="/comparison?sample=1"
          />
        </div>
      </div>
    );
  }

  if (!hydrated) return null;

  if (!completedRealReview) {
    return (
      <div>
        <PageHeader
          kicker="Step 04 / Hypothesis"
          title="Hypothesis is locked"
          description="Complete Portfolio Input first to unlock Hypothesis."
          boundaryNote="Candidates are test portfolios for comparison. They are not recommendations."
        >
          <StatusBadge tone="amber">Real review required</StatusBadge>
        </PageHeader>
        <EmptyState
          title="Complete Portfolio Input first to unlock Hypothesis."
          description="Open sample mode with /hypothesis?sample=1, or run a real portfolio review."
        />
      </div>
    );
  }

  if (!launchpadRecord || rawLaunchpadCards.length === 0) {
    return (
      <div>
        <PageHeader
          kicker="Step 04 / Hypothesis"
          title="Hypothesis Builder"
          description="Turn the portfolio diagnosis into a testable investment hypothesis."
          boundaryNote="Candidates are test portfolios for comparison. They are not recommendations."
        >
          <StatusBadge tone="amber">Hypothesis unavailable</StatusBadge>
        </PageHeader>
        <SiteExplanationHierarchy
          bundle={siteExplanation}
          screen="hypothesis"
          fallbackTitle="Hypothesis explanation"
        />
        <CurrentDiagnosisSection view={problemClassificationView} />
        <EmptyState
          title="Run diagnosis to unlock Hypothesis Builder."
          description="The completed review does not include test paths for this step."
        />
      </div>
    );
  }

  const selectedRawCard = candidateRawCards.find((card) => textValue(card.card_id, "") === selectedCardId);
  const reviewId = activeReview?.reviewId ?? activeReview?.reviewSummary?.reviewId ?? activeReview?.reviewResult?.review_id;

  return (
    <div>
      <PageHeader
        kicker="Step 04 / Hypothesis"
        title="Hypothesis Builder"
        description="Turn the current diagnosis into one clear candidate test before comparison."
        boundaryNote="Candidates are test portfolios for comparison. They are not recommendations."
      >
        <StatusBadge tone="slate">Not a recommendation</StatusBadge>
      </PageHeader>
      <SiteExplanationHierarchy
        bundle={siteExplanation}
        screen={activeReview?.candidateGeneration ? "candidate" : "hypothesis"}
        fallbackTitle={activeReview?.candidateGeneration ? "Candidate explanation" : "Hypothesis explanation"}
      />
      <WorkflowRail />
      <CurrentDiagnosisSection view={problemClassificationView} />
      <RecommendedTestSection view={problemClassificationView} />
      <DecisionBoundaryBlock />
      <div className="grid gap-7 xl:grid-cols-[minmax(0,1fr)_400px]">
        <AvailableTestPathsSection
          realCards={realCards}
          monitoringCards={monitoringCards}
          selectedCardId={selectedCardId}
          onSelect={setSelectedCardId}
        />
        <BuilderSetupPanel
          selectedCard={selectedRawCard}
          builderDocument={builderRecord}
          reviewId={reviewId}
          candidateGeneration={activeReview?.candidateGeneration}
          isGenerating={isGeneratingCandidate}
          generationError={generationError}
          onGenerate={handleGenerateCandidate}
          comparisonHref="/comparison"
        />
      </div>
    </div>
  );
}
