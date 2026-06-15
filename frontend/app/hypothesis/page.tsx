"use client";

import { useEffect, useMemo, useState, type ReactNode } from "react";
import Link from "next/link";
import { ClientFitContextCard } from "@/components/client-fit/ClientFitContextCard";
import { StatusBadge } from "@/components/ui/StatusBadge";
import { diagnosisStageChainReady, useReviewState, type ActiveReviewState } from "@/lib/reviewState";
import type { ClientFitDisplaySummary, StagedReviewStatusResponse } from "@/lib/generated/api-types";
import {
  buildHypothesisScreenModel,
  sanitizeHypothesisError,
  type HypothesisScreenModel,
  type HypothesisTestModel
} from "@/lib/hypothesis/hypothesisScreenModel";

type JsonRecord = Record<string, unknown>;

function isRecord(value: unknown): value is JsonRecord {
  return Boolean(value) && typeof value === "object" && !Array.isArray(value);
}

function optionalText(value: unknown) {
  return typeof value === "string" && value.trim() ? value.trim() : undefined;
}

function safeErrorText(value: unknown, fallback: string) {
  if (!isRecord(value)) return fallback;
  const message = optionalText(value.error) ?? optionalText(isRecord(value.safe_error) ? value.safe_error.message : undefined) ?? fallback;
  const details = value.details;
  const detailText = typeof details === "string"
    ? details
    : Array.isArray(details)
      ? details.filter((item): item is string => typeof item === "string").join(" ")
      : "";
  return [message, detailText].filter(Boolean).join(" ");
}

async function probeLiveReviewLineage(reviewId: string) {
  const response = await fetch(`/api/portfolio/review/status?reviewId=${encodeURIComponent(reviewId)}`, {
    method: "GET",
    cache: "no-store"
  });
  const status = await response.json() as (StagedReviewStatusResponse & { error?: string; details?: unknown });
  if (!response.ok) {
    const message = safeErrorText(status, "This review is compact history. Run a new diagnosis before generating a candidate.");
    return {
      ok: false,
      stale: response.status === 403 || response.status === 404 || /not found|forbidden|different authenticated user/i.test(message),
      message
    };
  }
  if (!diagnosisStageChainReady(status)) {
    return {
      ok: false,
      stale: false,
      message: "Portfolio diagnosis is still preparing. Wait for Diagnosis, Stress Lab, and Hypothesis setup to finish before generating a candidate."
    };
  }
  return { ok: true, stale: false, message: "" };
}

function formatWeight(value: number) {
  return `${(value * 100).toFixed(2).replace(/\.?0+$/, "")}%`;
}

function sampleActiveReview(generated: boolean): ActiveReviewState {
  const selectedCardId = "sample_improve_crisis_resilience";
  return {
    investorCurrency: "USD",
    holdings: [],
    readOnlyHistory: false,
    lineageAvailable: true,
    reviewId: "frontend_review_sample",
    runMode: "real_run",
    runStatus: "completed",
    submitted: true,
    diagnosisReady: true,
    evidenceReady: true,
    improvementPathsReady: true,
    candidateReady: generated,
    comparisonReady: false,
    verdictReady: false,
    updatedAt: new Date().toISOString(),
    reviewSummary: {
      version: 1,
      source: "real_run",
      status: "completed",
      reviewId: "frontend_review_sample",
      generatedAt: new Date().toISOString(),
      investorCurrency: "USD",
      holdingsCount: 5,
      totalWeight: 100,
      cashWeight: 0,
      rawOutputKeys: [],
      outputPaths: {},
      diagnosis: {
        status: "Diagnosis ready",
        headline: "Weak crisis resilience is the main issue to test before comparison.",
        evidenceQuality: "Moderate evidence",
        nextStep: "Improve Crisis Resilience",
        boundaryNote: "Diagnosis is diagnostic-only.",
        drivers: [],
        metrics: [],
        sourceArtifacts: [],
        rejectedAlternatives: [],
        rationaleRefs: []
      },
      primaryProblem: "Weak crisis resilience",
      problemSeverity: "High",
      problemConfidence: "High",
      suggestedActionPaths: ["Improve Crisis Resilience"],
      launchpadCardsCount: 2,
      candidateLaunchpadAvailable: true,
      problemClassificationAvailable: true,
      recommendedFirstTest: "Improve Crisis Resilience",
      launchpadCards: [
        {
          card_id: selectedCardId,
          title: "Improve Crisis Resilience",
          goal: "Improve crisis resilience",
          hypothesis_to_test: "Test whether improving crisis resilience lowers severe stress loss enough to beat the current portfolio on the stated success criteria.",
          card_type: "targeted_hypothesis_test",
          source_problem_label: "Weak crisis resilience",
          suggested_methods: [
            { candidate_method_id: "minimum_cvar", method_role: "targeted_hypothesis" },
            { candidate_method_id: "minimum_variance", method_role: "targeted_hypothesis" }
          ],
          default_method: "minimum_cvar",
          success_criteria: [
            "Lower worst synthetic or historical stress loss versus the current portfolio.",
            "Improve offset coverage in the main hedge-gap scenario.",
            "Reduce top stress-loss concentration without excessive turnover."
          ],
          tradeoff_to_watch: "Lower tail loss vs lower expected return and higher turnover.",
          decision_boundary: "This is not a rebalance recommendation. Actual rebalance decision is made only after Current vs Candidate Comparison and Decision Verdict.",
          is_rebalance_recommendation: false,
          generates_portfolio: false
        },
        {
          card_id: "sample_reduce_credit_liquidity",
          title: "Reduce Credit / Liquidity Risk",
          goal: "Reduce credit / liquidity risk",
          hypothesis_to_test: "Test whether defensive candidates reduce credit and liquidity fragility.",
          card_type: "targeted_hypothesis_test",
          source_problem_label: "Credit / liquidity fragility",
          suggested_methods: [{ candidate_method_id: "minimum_variance", method_role: "targeted_hypothesis" }],
          default_method: "minimum_variance",
          success_criteria: ["Lower credit or liquidity shock loss.", "Reduce fragile carry exposure without over-penalizing intentional income sleeves."],
          tradeoff_to_watch: "Less credit/carry vs income yield.",
          decision_boundary: "This is not a rebalance recommendation.",
          is_rebalance_recommendation: false,
          generates_portfolio: false
        }
      ],
      storage: {
        summaryBytes: 0,
        rawBytes: 0,
        rawPersisted: false,
        rawAccessStrategy: "sample"
      }
    },
    candidateGeneration: generated ? {
      reviewId: "frontend_review_sample",
      status: "completed",
      stage: "candidate_generation",
      selectedCardId,
      candidateId: "minimum_cvar_sample_candidate",
      methodLabel: "Minimum CVaR diagnostic candidate",
      generationStatus: "generated",
      canCompare: true,
      weights: [
        { ticker: "SPY", weight: 0.32 },
        { ticker: "BND", weight: 0.28 },
        { ticker: "GLD", weight: 0.16 },
        { ticker: "VEA", weight: 0.14 },
        { ticker: "CASH", weight: 0.1 }
      ],
      generatedAt: new Date().toISOString()
    } : undefined
  };
}

function WorkstationHeader({ model }: { model: HypothesisScreenModel }) {
  return (
    <header className="relative mb-5 overflow-hidden rounded-[1.75rem] border border-pmri-border/55 bg-[#111317]/90 p-5 shadow-decision md:p-6">
      <div className="pointer-events-none absolute inset-0 bg-[radial-gradient(circle_at_84%_0%,rgba(96,165,250,0.12),transparent_28%),linear-gradient(90deg,rgba(255,255,255,0.045),transparent_44%)]" />
      <div className="relative flex flex-col gap-5 lg:flex-row lg:items-end lg:justify-between">
        <div>
          <div className="mb-4 flex items-center gap-3">
            <span className="h-px w-14 bg-pmri-blueSoft/70" />
            <p className="pmri-label text-pmri-blueSoft">Step 05 / Hypothesis</p>
          </div>
          <h1 className="pmri-heading-display text-pmri-text">{model.header.title}</h1>
          <p className="mt-3 max-w-3xl text-sm leading-7 text-pmri-text2">{model.header.subtitle}</p>
        </div>
        <StatusBadge tone={model.header.badgeTone}>{model.header.badge}</StatusBadge>
      </div>
    </header>
  );
}

function CompactStepper({ actionState }: { actionState: HypothesisScreenModel["action"]["state"] }) {
  const items = [
    { label: "Diagnosis", state: "done" },
    { label: "Hypothesis", state: "active" },
    { label: "Comparison", state: actionState === "continue" ? "next" : "idle" },
    { label: "Verdict", state: "idle" }
  ];
  return (
    <nav className="mb-5 rounded-2xl border border-pmri-border/45 bg-white/[0.022] p-3" aria-label="Decision journey">
      <ol className="grid gap-2 md:grid-cols-4">
        {items.map((item) => (
          <li
            key={item.label}
            className={`rounded-xl border px-3 py-2 text-sm ${
              item.state === "active"
                ? "border-pmri-blue/45 bg-pmri-blue/12 text-pmri-text"
                : item.state === "done"
                  ? "border-pmri-positive/25 bg-pmri-positive/10 text-pmri-text2"
                  : "border-white/10 bg-white/[0.025] text-pmri-muted"
            }`}
          >
            <span className="mr-2 font-mono text-xs">{item.state === "done" ? "✓" : item.state === "active" ? "●" : "○"}</span>
            {item.label}
          </li>
        ))}
      </ol>
    </nav>
  );
}

function PrimaryDiagnosisPanel({ model }: { model: HypothesisScreenModel }) {
  const diagnosis = model.primaryDiagnosis;
  const facts = [
    diagnosis.confidence ? ["Confidence", diagnosis.confidence] : undefined,
    diagnosis.materiality ? ["Materiality", diagnosis.materiality] : undefined,
    ["Next step", diagnosis.nextStep]
  ].filter(Boolean) as Array<[string, string]>;

  return (
    <section className="rounded-3xl border border-white/10 bg-white/[0.026] p-5">
      <p className="pmri-label text-pmri-blueSoft">Primary diagnosis</p>
      <h2 className="pmri-heading-section mt-2 text-2xl text-pmri-text">{diagnosis.label}</h2>
      <p className="mt-3 max-w-4xl text-sm leading-7 text-pmri-text2">{diagnosis.explanation}</p>
      {diagnosis.rootCause ? (
        <p className="mt-4 rounded-2xl border border-white/10 bg-black/15 p-3 text-sm text-pmri-text2">
          <span className="text-pmri-muted">Root cause / status:</span> <span className="text-pmri-text">{diagnosis.rootCause}</span>
        </p>
      ) : null}
      <dl className="mt-4 grid gap-3 md:grid-cols-3">
        {facts.map(([label, value]) => (
          <div key={label} className="rounded-2xl border border-white/10 bg-white/[0.025] p-3">
            <dt className="pmri-label">{label}</dt>
            <dd className="mt-1 text-sm text-pmri-text">{value}</dd>
          </div>
        ))}
      </dl>
    </section>
  );
}

function BulletList({ items, fallback }: { items: string[]; fallback: string }) {
  if (!items.length) return <p className="text-sm leading-6 text-pmri-muted">{fallback}</p>;
  return (
    <ul className="space-y-2 text-sm leading-6 text-pmri-text2">
      {items.map((item) => (
        <li key={item} className="flex gap-2">
          <span className="mt-2 h-1.5 w-1.5 shrink-0 rounded-full bg-pmri-blueSoft" />
          <span>{item}</span>
        </li>
      ))}
    </ul>
  );
}

function RecommendedDiagnosticTestPanel({ test }: { test?: HypothesisTestModel }) {
  if (!test) {
    return (
      <section className="rounded-3xl border border-pmri-amber/30 bg-pmri-amber/10 p-5">
        <p className="pmri-label text-pmri-amber">Recommended diagnostic test</p>
        <h2 className="pmri-heading-section mt-2 text-xl text-pmri-text">No candidate test is available</h2>
        <p className="mt-3 text-sm leading-7 text-pmri-text2">Resolve data quality or rerun diagnosis before generating a candidate.</p>
      </section>
    );
  }

  return (
    <section className="relative overflow-hidden rounded-3xl border border-pmri-blue/35 bg-[linear-gradient(135deg,rgba(59,130,246,0.16),rgba(255,255,255,0.035)_42%,rgba(16,17,20,0.88))] p-5 shadow-decision">
      <div className="pointer-events-none absolute inset-x-0 top-0 h-px bg-gradient-to-r from-transparent via-pmri-blueSoft/60 to-transparent" />
      <div className="flex flex-col gap-3 md:flex-row md:items-start md:justify-between">
        <div>
          <p className="pmri-label text-pmri-blueSoft">Recommended diagnostic test</p>
          <h2 className="pmri-heading-section mt-2 text-3xl text-pmri-text">{test.title}</h2>
          <p className="mt-3 max-w-4xl text-sm leading-7 text-pmri-text2">{test.hypothesis}</p>
        </div>
        <StatusBadge tone={test.canGenerate ? "blue" : "amber"}>{test.statusLabel}</StatusBadge>
      </div>

      <div className="mt-5 grid gap-4 lg:grid-cols-[1fr_1fr]">
        <div className="rounded-2xl border border-white/10 bg-black/15 p-4">
          <p className="pmri-label">Why this test</p>
          <p className="mt-2 text-sm leading-6 text-pmri-text2">{test.why}</p>
          <div className="mt-4 flex flex-wrap gap-2">
            {test.methods.map((method) => (
              <span key={method} className="rounded-full border border-pmri-blue/30 bg-pmri-blue/10 px-3 py-1 text-xs text-pmri-text">
                {method}
              </span>
            ))}
          </div>
        </div>
        <div className="rounded-2xl border border-white/10 bg-black/15 p-4">
          <p className="pmri-label">Success criteria</p>
          <div className="mt-2">
            <BulletList items={test.successCriteria} fallback="Comparison will check whether this test improves the diagnosis." />
          </div>
        </div>
      </div>

      <div className="mt-4 grid gap-4 lg:grid-cols-2">
        {test.tradeoff ? (
          <div className="rounded-2xl border border-white/10 bg-white/[0.025] p-4">
            <p className="pmri-label">Trade-off to watch</p>
            <p className="mt-2 text-sm leading-6 text-pmri-text2">{test.tradeoff}</p>
          </div>
        ) : null}
        <div className="rounded-2xl border border-pmri-amber/25 bg-pmri-amber/10 p-4">
          <p className="pmri-label text-pmri-amber">Decision boundary</p>
          <p className="mt-2 text-sm leading-6 text-pmri-text2">{test.decisionBoundary}</p>
        </div>
      </div>
    </section>
  );
}

function HypothesisActionConsole({
  model,
  onGenerate,
  comparisonHref
}: {
  model: HypothesisScreenModel;
  onGenerate: () => void;
  comparisonHref: string;
}) {
  const test = model.primaryTest;
  const action = model.action;
  const buttonClass = "pmri-focus flex w-full items-center justify-center rounded-full px-5 py-3 text-sm font-semibold transition";

  return (
    <aside className="rounded-3xl border border-pmri-border/60 bg-[#15171c] p-5 shadow-decision xl:sticky xl:top-5">
      <div className="flex items-start justify-between gap-3">
        <div>
          <p className="pmri-label text-pmri-blueSoft">Action console</p>
          <h3 className="pmri-heading-section mt-2 text-xl text-pmri-text">{test?.title ?? "No test selected"}</h3>
        </div>
        <StatusBadge tone={action.state === "continue" ? "green" : action.state === "blocked" ? "amber" : "blue"}>{action.statusLabel}</StatusBadge>
      </div>

      <dl className="mt-6 space-y-4">
        <div>
          <dt className="pmri-label">Selected method</dt>
          <dd className="mt-1 text-sm text-pmri-text">{test?.selectedMethodLabel ?? "No method available"}</dd>
        </div>
        <div>
          <dt className="pmri-label">Candidate state</dt>
          <dd className="mt-1 text-sm text-pmri-text2">{action.statusLabel}</dd>
        </div>
      </dl>

      {action.candidateName ? (
        <div className="mt-5 rounded-2xl border border-pmri-positive/30 bg-pmri-positive/10 p-4">
          <p className="pmri-label text-pmri-positive">Test candidate generated</p>
          <p className="mt-1 text-sm font-medium text-pmri-text">{action.candidateName}</p>
          {action.candidateWeights.length ? (
            <details className="mt-3 text-xs text-pmri-text2">
              <summary className="cursor-pointer text-pmri-blueSoft">View weights</summary>
              <ul className="mt-3 grid gap-2">
                {action.candidateWeights.map((item) => (
                  <li key={item.ticker} className="flex justify-between rounded-lg bg-white/[0.04] px-3 py-2">
                    <span>{item.ticker}</span>
                    <span>{formatWeight(item.weight)}</span>
                  </li>
                ))}
              </ul>
            </details>
          ) : null}
        </div>
      ) : null}

      <div className="mt-6 space-y-3">
        {action.state === "continue" ? (
          <Link href={comparisonHref} className={`${buttonClass} pmri-primary-action`}>
            {action.label}
          </Link>
        ) : (
          <button
            type="button"
            disabled={action.state !== "generate"}
            onClick={onGenerate}
            className={`${buttonClass} ${action.state === "generate" ? "pmri-primary-action" : "pmri-disabled-action"}`}
          >
            {action.state === "generating" ? <span className="pmri-spinner mr-2" /> : null}
            {action.label}
          </button>
        )}
        {action.disabledReason ? (
          <p className="rounded-xl border border-pmri-amber/35 bg-pmri-amber/10 p-3 text-sm leading-6 text-pmri-amber">
            {action.disabledReason}
          </p>
        ) : null}
        {action.userError ? (
          <div className="rounded-xl border border-pmri-amber/35 bg-pmri-amber/10 p-3 text-sm leading-6 text-pmri-amber">
            <p>{action.userError}</p>
            {action.developerError ? (
              <details className="mt-2 text-xs text-pmri-muted">
                <summary className="cursor-pointer">Developer details</summary>
                <p className="mt-2 break-words">{action.developerError}</p>
              </details>
            ) : null}
          </div>
        ) : null}
      </div>
    </aside>
  );
}

function SecondaryContextPanels({
  model,
  clientFit,
  selectedCardId,
  onSelect
}: {
  model: HypothesisScreenModel;
  clientFit?: ClientFitDisplaySummary;
  selectedCardId: string | null;
  onSelect: (id: string) => void;
}) {
  return (
    <section className="mt-7 grid gap-5 xl:grid-cols-3">
      <details className="rounded-3xl border border-pmri-border/55 bg-white/[0.022] p-5" open>
        <summary className="cursor-pointer text-sm font-semibold text-pmri-text">Client Fit context</summary>
        <div className="mt-4">
          <ClientFitContextCard
            clientFit={clientFit}
            title="Client Fit informs the test, but does not choose the answer"
            description="Hypothesis Builder keeps profile-fit context separate from the portfolio diagnosis."
            structuralIssueNote="Client Fit pass does not clear concentration, stress, drawdown, or other structural issues."
            compact
          />
        </div>
      </details>

      <details className="rounded-3xl border border-pmri-border/55 bg-white/[0.022] p-5">
        <summary className="cursor-pointer text-sm font-semibold text-pmri-text">Other possible tests</summary>
        <div className="mt-4 space-y-3">
          {[...model.alternativeTests, ...model.monitorOrDataTests].length ? (
            [...model.alternativeTests, ...model.monitorOrDataTests].map((test) => (
              <button
                key={test.cardId}
                type="button"
                onClick={() => onSelect(test.cardId)}
                className={`pmri-focus w-full rounded-2xl border p-4 text-left transition ${
                  selectedCardId === test.cardId ? "border-pmri-blue/50 bg-pmri-blue/10" : "border-white/10 bg-white/[0.025] hover:border-pmri-blue/35"
                }`}
              >
                <div className="flex items-start justify-between gap-3">
                  <div>
                    <p className="pmri-label">{test.isMonitorOrDataPath ? "Context path" : "Alternative test"}</p>
                    <p className="mt-1 text-sm font-semibold text-pmri-text">{test.title}</p>
                    <p className="mt-2 line-clamp-3 text-xs leading-5 text-pmri-muted">{test.hypothesis}</p>
                  </div>
                  <StatusBadge tone={test.canGenerate ? "blue" : "slate"}>{test.statusLabel}</StatusBadge>
                </div>
              </button>
            ))
          ) : (
            <p className="text-sm leading-6 text-pmri-muted">No secondary tests were returned for this review.</p>
          )}
        </div>
      </details>

      <details className="rounded-3xl border border-pmri-border/55 bg-white/[0.022] p-5">
        <summary className="cursor-pointer text-sm font-semibold text-pmri-text">Evidence & technical details</summary>
        {model.evidencePanel ? (
          <div className="mt-4 space-y-4">
            <div>
              <p className="pmri-label text-pmri-blueSoft">{model.evidencePanel.title}</p>
              <p className="mt-2 text-sm leading-6 text-pmri-muted">{model.evidencePanel.subtitle}</p>
            </div>
            {[
              ...model.evidencePanel.executiveItems,
              ...model.evidencePanel.evidenceItems,
              ...model.evidencePanel.technicalItems
            ].slice(0, 6).map((item) => (
              <article key={item.id} className="rounded-2xl border border-white/10 bg-white/[0.025] p-3">
                <p className="text-sm leading-6 text-pmri-text2">{item.text}</p>
                <div className="mt-2">
                  <StatusBadge tone={item.evidenceTone}>{item.evidenceLabel}</StatusBadge>
                </div>
              </article>
            ))}
          </div>
        ) : (
          <p className="mt-4 text-sm leading-6 text-pmri-muted">Technical evidence is unavailable for this compact review.</p>
        )}
      </details>
    </section>
  );
}

function EmptyState({ title, description, href = "/portfolio-input", cta = "Go to Portfolio Input" }: { title: string; description: string; href?: string; cta?: string }) {
  return (
    <section className="rounded-3xl border border-pmri-border/55 bg-white/[0.026] p-6">
      <p className="text-lg font-medium text-pmri-text">{title}</p>
      <p className="mt-2 max-w-2xl text-sm leading-6 text-pmri-muted">{description}</p>
      <Link href={href} className="pmri-focus pmri-primary-action mt-5 inline-flex rounded-full px-5 py-2.5 text-sm font-medium">
        {cta}
      </Link>
    </section>
  );
}

function HypothesisWorkstation({
  model,
  clientFit,
  selectedCardId,
  onSelect,
  onGenerate,
  comparisonHref
}: {
  model: HypothesisScreenModel;
  clientFit?: ClientFitDisplaySummary;
  selectedCardId: string | null;
  onSelect: (id: string) => void;
  onGenerate: () => void;
  comparisonHref: string;
}) {
  return (
    <>
      <WorkstationHeader model={model} />
      <CompactStepper actionState={model.action.state} />
      {model.pageState === "read_only" ? (
        <section className="mb-5 rounded-2xl border border-pmri-border/45 bg-white/[0.026] p-4">
          <StatusBadge tone="slate">Needs new diagnosis</StatusBadge>
          <p className="mt-3 max-w-3xl text-sm leading-7 text-pmri-text2">
            This saved review is compact history. Generate a new diagnosis for the loaded portfolio before creating or comparing a new candidate.
          </p>
        </section>
      ) : null}
      <div className="grid gap-6 xl:grid-cols-[minmax(0,1fr)_390px]">
        <main className="space-y-5">
          <PrimaryDiagnosisPanel model={model} />
          <RecommendedDiagnosticTestPanel test={model.primaryTest} />
        </main>
        <HypothesisActionConsole model={model} onGenerate={onGenerate} comparisonHref={comparisonHref} />
      </div>
      <SecondaryContextPanels model={model} clientFit={clientFit} selectedCardId={selectedCardId} onSelect={onSelect} />
    </>
  );
}

export default function HypothesisPage() {
  const { activeReview, hydrated, journeyFlags, markLiveLineageUnavailable, recordBuilderSetup, recordCandidateGeneration } = useReviewState();
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

  const effectiveReview = sampleMode ? sampleActiveReview(sampleGenerated) : activeReview;
  const model = useMemo(() => buildHypothesisScreenModel({
    activeReview: effectiveReview,
    selectedCardId,
    isGenerating: isGeneratingCandidate,
    generationError
  }), [effectiveReview, generationError, isGeneratingCandidate, selectedCardId]);

  useEffect(() => {
    if (!selectedCardId && model.defaultSelectedCardId) {
      setSelectedCardId(model.defaultSelectedCardId);
    }
  }, [model.defaultSelectedCardId, selectedCardId]);

  useEffect(() => {
    setGenerationError(undefined);
  }, [selectedCardId, effectiveReview?.reviewId]);

  async function handleGenerateCandidate() {
    if (sampleMode) {
      setSampleGenerated(true);
      return;
    }

    const reviewId = activeReview?.reviewId ?? activeReview?.reviewSummary?.reviewId ?? optionalText(activeReview?.reviewResult?.review_id);
    const cardId = selectedCardId ?? model.defaultSelectedCardId;
    if (!activeReview?.lineageAvailable || activeReview.readOnlyHistory || !reviewId || !cardId) return;
    setIsGeneratingCandidate(true);
    setGenerationError(undefined);

    try {
      const lineageProbe = await probeLiveReviewLineage(reviewId);
      if (!lineageProbe.ok) {
        const message = lineageProbe.stale
          ? "This review is compact history. Run a new diagnosis before generating a candidate."
          : lineageProbe.message;
        if (lineageProbe.stale) markLiveLineageUnavailable(message);
        setGenerationError(message);
        return;
      }

      const prepareResponse = await fetch("/api/portfolio/builder/prepare", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          review_id: reviewId,
          selected_card_id: cardId
        })
      });
      const prepareResult = await prepareResponse.json() as unknown;
      if (!prepareResponse.ok || !isRecord(prepareResult) || prepareResult.status !== "completed") {
        setGenerationError(safeErrorText(prepareResult, "The selected test could not be prepared."));
        return;
      }
      recordBuilderSetup(prepareResult);
      const prepareEnvelope = isRecord(prepareResult.fastapi_envelope) ? prepareResult.fastapi_envelope : {};
      const prepareLineage = isRecord(prepareEnvelope.lineage) ? prepareEnvelope.lineage : {};
      const builderSetupId = optionalText(prepareLineage.builder_setup_id) ?? optionalText(prepareResult.builder_setup_id);

      const response = await fetch("/api/portfolio/candidate/generate", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          review_id: reviewId,
          selected_card_id: cardId,
          builder_setup_id: builderSetupId
        })
      });
      const result = await response.json() as unknown;
      if (!response.ok || !isRecord(result) || result.status !== "completed") {
        setGenerationError(safeErrorText(result, "The test candidate could not be generated."));
        return;
      }
      recordCandidateGeneration(result);
    } catch (error) {
      const raw = error instanceof Error ? error.message : "The test candidate could not be generated. Please try again or choose another test path.";
      setGenerationError(sanitizeHypothesisError(raw).userError ?? raw);
    } finally {
      setIsGeneratingCandidate(false);
    }
  }

  if (!sampleMode && !hydrated) return null;

  if (model.pageState === "locked") {
    const needsClientFit = Boolean(effectiveReview?.runMode === "real_run" && effectiveReview.runStatus === "completed" && !journeyFlags.clientFitReady);
    return (
      <div>
        <WorkstationHeader model={model} />
        <EmptyState
          title={needsClientFit ? "Open Client Fit first." : "Complete Portfolio Input first to unlock Hypothesis Builder."}
          description={needsClientFit
            ? "The journey separates what the portfolio owns, how it behaves under stress, and whether that evidence fits the stated profile."
            : "Run a real portfolio review, or open sample mode with /hypothesis?sample=1."}
          href={needsClientFit ? "/client-fit" : "/portfolio-input"}
          cta={needsClientFit ? "Open Client Fit" : "Go to Portfolio Input"}
        />
      </div>
    );
  }

  if (model.pageState === "unavailable") {
    return (
      <div>
        <WorkstationHeader model={model} />
        <PrimaryDiagnosisPanel model={model} />
        <div className="mt-5">
          <EmptyState
            title="Run diagnosis to unlock Hypothesis Builder."
            description="The completed review does not include test paths for this step."
          />
        </div>
      </div>
    );
  }

  return (
    <HypothesisWorkstation
      model={model}
      clientFit={effectiveReview?.reviewSummary?.clientFit}
      selectedCardId={selectedCardId ?? model.defaultSelectedCardId}
      onSelect={setSelectedCardId}
      onGenerate={handleGenerateCandidate}
      comparisonHref={sampleMode ? "/comparison?sample=1" : "/comparison"}
    />
  );
}
