"use client";

import { useEffect, useMemo, useState, type ReactNode } from "react";
import Link from "next/link";
import { PageHeader } from "@/components/layout/PageHeader";
import { HypothesisBuilderPanel } from "@/components/hypothesis/HypothesisBuilderPanel";
import { HypothesisCard } from "@/components/hypothesis/HypothesisCard";
import { StatusBadge } from "@/components/ui/StatusBadge";
import demoData from "@/data/demo/hypothesis-launchpad.json";
import { useReviewState, type CandidateGenerationSummary } from "@/lib/reviewState";
import type { Hypothesis } from "@/lib/types";

type JsonRecord = Record<string, unknown>;

const demoLaunchpad = demoData as {
  selectedMethod: string;
  builderStatus: string;
  boundaryNote: string;
  hypotheses: Hypothesis[];
  constraints: string[];
};

function isRecord(value: unknown): value is JsonRecord {
  return Boolean(value) && typeof value === "object" && !Array.isArray(value);
}

function getArray(value: unknown): unknown[] {
  return Array.isArray(value) ? value : [];
}

function textValue(value: unknown, fallback = "n/a") {
  return typeof value === "string" && value.trim() ? value : fallback;
}

function optionalText(value: unknown) {
  return typeof value === "string" && value.trim() ? value : undefined;
}

function booleanValue(value: unknown, fallback = false) {
  return typeof value === "boolean" ? value : fallback;
}

function displayValue(value: unknown, fallback = "n/a") {
  if (typeof value === "boolean") return value ? "true" : "false";
  if (typeof value === "number") return Number.isFinite(value) ? String(value) : fallback;
  if (typeof value === "string" && value.trim()) return value;
  return fallback;
}

function errorTextFromResponse(value: unknown) {
  if (!isRecord(value)) return "Candidate generation failed.";
  const message = textValue(value.error, "Candidate generation failed.");
  const details = value.details;
  if (typeof details === "string" && details.trim()) return `${message} ${details}`;
  if (Array.isArray(details)) {
    const safeDetails = details
      .map((item) => (typeof item === "string" ? item : ""))
      .filter(Boolean)
      .join(" ");
    return safeDetails ? `${message} ${safeDetails}` : message;
  }
  return message;
}

function formatWeight(value: number) {
  return `${(value * 100).toFixed(2).replace(/\.?0+$/, "")}%`;
}

function methodLabel(methodId: string) {
  if (methodId === "equal_weight") return "Equal Weight reference test";
  if (methodId === "risk_parity") return "Risk Parity reference test";
  return methodId.replaceAll("_", " ");
}

function launchpadCardToHypothesis(card: JsonRecord): Hypothesis {
  const suggestedMethods = getArray(card.suggested_methods)
    .filter(isRecord)
    .map((method) => optionalText(method.candidate_method_id))
    .filter((item): item is string => Boolean(item));
  const methodId = optionalText(card.default_method) ?? suggestedMethods[0] ?? textValue(card.card_type, "launchpad_card");
  const successCriteria = getArray(card.success_criteria)
    .map((item) => textValue(item, ""))
    .filter(Boolean);

  return {
    id: textValue(card.card_id, textValue(card.title, "launchpad-card")),
    title: textValue(card.title, "Candidate Launchpad card"),
    targetProblem: textValue(
      card.hypothesis_to_test,
      textValue(card.what_this_tests_en, textValue(card.source_problem_label, "Problem Classification handoff"))
    ),
    expectedTradeoff: textValue(
      card.tradeoff_to_watch,
      textValue(card.expected_tradeoff_to_check_en, successCriteria[0] ?? "Trade-offs must be checked before any verdict.")
    ),
    methodId,
    evidenceSource: textValue(
      card.why_this_test,
      textValue(card.why_this_path_en, "Candidate Launchpad generated from Problem Classification.")
    ),
    status: suggestedMethods.length
      ? `Setup only - ${suggestedMethods.map(methodLabel).join(" / ")}`
      : textValue(card.launch_status, "Setup only")
  };
}

function EmptyState({ title, description }: { title: string; description: string }) {
  return (
    <section className="pmri-card rounded-3xl p-6">
      <p className="text-lg font-semibold text-pmri-text">{title}</p>
      <p className="mt-2 max-w-2xl text-sm leading-6 text-pmri-muted">{description}</p>
      <Link
        href="/portfolio-input"
        className="pmri-focus mt-5 inline-flex rounded-full border border-pmri-blue/50 bg-pmri-blue px-5 py-2.5 text-sm font-semibold text-white shadow-decision transition hover:bg-pmri-blueSoft"
      >
        Go to Portfolio Input
      </Link>
    </section>
  );
}

function FieldRow({ label, children }: { label: string; children: ReactNode }) {
  return (
    <div>
      <dt className="text-xs font-semibold uppercase tracking-[0.12em] text-pmri-muted">{label}</dt>
      <dd className="mt-1 text-sm leading-6 text-pmri-text2">{children}</dd>
    </div>
  );
}

function TextList({ items, empty = "n/a" }: { items: unknown[]; empty?: string }) {
  const rows = items.map((item) => displayValue(item, "")).filter(Boolean);
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

function SuggestedMethods({ value }: { value: unknown }) {
  const methods = getArray(value).filter(isRecord);
  if (!methods.length) return <span>n/a</span>;
  return (
    <ul className="space-y-3">
      {methods.map((method, index) => {
        const methodId = displayValue(method.candidate_method_id, `method_${index + 1}`);
        const role = optionalText(method.method_role);
        const why = optionalText(method.why_this_method);
        return (
          <li key={`${methodId}-${index}`} className="rounded-xl border border-white/10 bg-white/[0.03] p-3">
            <p className="font-semibold text-pmri-text">{methodLabel(methodId)}</p>
            {role ? <p className="mt-1 text-xs uppercase tracking-[0.1em] text-pmri-muted">{role.replaceAll("_", " ")}</p> : null}
            {why ? <p className="mt-2 text-xs leading-5 text-pmri-muted">{why}</p> : null}
          </li>
        );
      })}
    </ul>
  );
}

function BuilderSetupPanel({
  selectedCard,
  builderDocument,
  reviewId,
  candidateGeneration,
  isGenerating,
  generationError,
  onGenerate
}: {
  selectedCard?: JsonRecord;
  builderDocument?: JsonRecord;
  reviewId?: string;
  candidateGeneration?: CandidateGenerationSummary;
  isGenerating: boolean;
  generationError?: string;
  onGenerate: () => void;
}) {
  if (!selectedCard) {
    return (
      <aside className="pmri-card rounded-2xl p-6">
        <p className="text-xs font-semibold uppercase tracking-[0.14em] text-pmri-gold">Builder Setup</p>
        <h3 className="mt-2 text-lg font-semibold text-pmri-text">Select a Hypothesis card</h3>
        <p className="mt-4 text-sm leading-6 text-pmri-muted">
          Click a real Candidate Launchpad card to preview the Builder setup. No candidate will be generated on this page.
        </p>
      </aside>
    );
  }

  const selectedCardId = textValue(selectedCard.card_id, "");
  const builderMatches = isRecord(builderDocument) && textValue(builderDocument.selected_card_id, "") === selectedCardId;
  const builderPrefill = builderMatches && isRecord(builderDocument?.builder_prefill) ? builderDocument.builder_prefill : undefined;
  const candidateSetup = builderMatches && isRecord(builderDocument?.candidate_setup) ? builderDocument.candidate_setup : undefined;
  const generatesPortfolio = booleanValue(selectedCard.generates_portfolio, false);
  const isRebalanceRecommendation = booleanValue(selectedCard.is_rebalance_recommendation, false);
  const canGenerateCandidate = builderMatches
    && reviewId
    && booleanValue(builderDocument?.can_generate_candidate, booleanValue(candidateSetup?.can_generate_candidate, false));
  const candidateForSelectedCard = candidateGeneration?.selectedCardId === selectedCardId ? candidateGeneration : undefined;

  return (
    <aside className="pmri-card rounded-2xl p-6">
      <div className="flex items-start justify-between gap-3">
        <div>
          <p className="text-xs font-semibold uppercase tracking-[0.14em] text-pmri-gold">Builder Setup</p>
          <h3 className="mt-2 text-lg font-semibold text-pmri-text">{textValue(selectedCard.title, "Selected Hypothesis card")}</h3>
        </div>
        <StatusBadge tone="blue">Setup only</StatusBadge>
      </div>

      <p className="mt-4 rounded-xl border border-pmri-gold/30 bg-pmri-gold/10 p-3 text-sm leading-6 text-pmri-gold">
        No candidate has been generated yet. This is a setup preview, not a recommendation.
      </p>

      <dl className="mt-6 space-y-5">
        <FieldRow label="Goal">{displayValue(selectedCard.goal)}</FieldRow>
        <FieldRow label="Hypothesis to test">{displayValue(selectedCard.hypothesis_to_test)}</FieldRow>
        <FieldRow label="Card type">{displayValue(selectedCard.card_type)}</FieldRow>
        <FieldRow label="Source problem">{displayValue(selectedCard.source_problem_label)}</FieldRow>
        <FieldRow label="Suggested methods">
          <SuggestedMethods value={selectedCard.suggested_methods} />
        </FieldRow>
        <FieldRow label="Default method">{displayValue(selectedCard.default_method)}</FieldRow>
        <FieldRow label="Success criteria">
          <TextList items={getArray(selectedCard.success_criteria)} />
        </FieldRow>
        <FieldRow label="Tradeoff to watch">{displayValue(selectedCard.tradeoff_to_watch)}</FieldRow>
        <FieldRow label="When to skip">{displayValue(selectedCard.when_to_skip)}</FieldRow>
        <FieldRow label="Decision boundary">{displayValue(selectedCard.decision_boundary)}</FieldRow>
        <FieldRow label="Is rebalance recommendation">{isRebalanceRecommendation ? "true" : "false"}</FieldRow>
        <FieldRow label="Generates portfolio">{generatesPortfolio ? "true" : "false"}</FieldRow>
      </dl>

      {builderMatches ? (
        <div className="mt-6 rounded-2xl border border-pmri-blue/25 bg-pmri-blue/10 p-4">
          <p className="text-xs font-semibold uppercase tracking-[0.12em] text-pmri-blueSoft">Backend Builder setup</p>
          <dl className="mt-4 space-y-4">
            <FieldRow label="Builder goal">{displayValue(builderPrefill?.goal)}</FieldRow>
            <FieldRow label="Suggested method">{displayValue(builderPrefill?.suggested_method)}</FieldRow>
            <FieldRow label="Constraint preset">{displayValue(builderPrefill?.constraint_preset)}</FieldRow>
            <FieldRow label="Max asset weight">{displayValue(builderPrefill?.max_asset_weight)}</FieldRow>
            <FieldRow label="Min asset weight">{displayValue(builderPrefill?.min_asset_weight)}</FieldRow>
            <FieldRow label="Validation status">{displayValue(candidateSetup?.validation_status)}</FieldRow>
            <FieldRow label="Can generate candidate">{displayValue(candidateSetup?.can_generate_candidate)}</FieldRow>
          </dl>
        </div>
      ) : (
        <p className="mt-6 rounded-xl border border-pmri-amber/35 bg-pmri-amber/10 p-3 text-sm leading-6 text-pmri-amber">
          Builder preview derived from Launchpad card. Backend candidate setup will be created before generation.
        </p>
      )}

      <div className="mt-6">
        <button
          type="button"
          disabled={!canGenerateCandidate || isGenerating}
          onClick={onGenerate}
          className={`w-full rounded-full border px-5 py-3 text-sm font-semibold transition ${
            canGenerateCandidate && !isGenerating
              ? "pmri-focus border-pmri-blue/50 bg-pmri-blue text-white shadow-decision hover:bg-pmri-blueSoft"
              : "cursor-not-allowed border-white/10 bg-white/10 text-pmri-muted"
          }`}
        >
          {isGenerating ? "Generating candidate..." : "Generate candidate"}
        </button>
        <p className="mt-3 text-xs leading-5 text-pmri-muted">
          {canGenerateCandidate
            ? "This creates one diagnostic candidate only. It will not compare portfolios or create a verdict."
            : "Generation is enabled only when the backend Builder setup matches this card and says it can generate a candidate."}
        </p>
        {generationError ? (
          <p className="mt-3 rounded-xl border border-pmri-red/35 bg-pmri-red/10 p-3 text-xs leading-5 text-pmri-red">
            {generationError}
          </p>
        ) : null}
        {candidateForSelectedCard ? (
          <div className="mt-4 rounded-2xl border border-pmri-green/30 bg-pmri-green/10 p-4">
            <div className="flex items-start justify-between gap-3">
              <div>
                <p className="text-xs font-semibold uppercase tracking-[0.12em] text-pmri-green">Candidate generated</p>
                <p className="mt-1 text-sm font-semibold text-pmri-text">{candidateForSelectedCard.candidateId || "candidate"}</p>
              </div>
              <StatusBadge tone={candidateForSelectedCard.status === "completed" ? "green" : "amber"}>
                {candidateForSelectedCard.generationStatus}
              </StatusBadge>
            </div>
            <p className="mt-3 text-xs leading-5 text-pmri-muted">
              Compare-ready: {candidateForSelectedCard.canCompare ? "yes" : "no"} · no comparison or verdict was generated.
            </p>
            {candidateForSelectedCard.weights.length ? (
              <ul className="mt-3 grid gap-2 text-xs text-pmri-text2">
                {candidateForSelectedCard.weights.slice(0, 8).map((item) => (
                  <li key={item.ticker} className="flex justify-between rounded-lg bg-white/[0.04] px-3 py-2">
                    <span>{item.ticker}</span>
                    <span>{formatWeight(item.weight)}</span>
                  </li>
                ))}
              </ul>
            ) : (
              <p className="mt-3 text-xs leading-5 text-pmri-muted">No weights were returned for this candidate.</p>
            )}
          </div>
        ) : null}
      </div>
    </aside>
  );
}

export default function HypothesisPage() {
  const { activeReview, hydrated, recordCandidateGeneration } = useReviewState();
  const [sampleMode, setSampleMode] = useState(false);
  const [selectedCardId, setSelectedCardId] = useState<string | null>(null);
  const [isGeneratingCandidate, setIsGeneratingCandidate] = useState(false);
  const [generationError, setGenerationError] = useState<string | undefined>();

  useEffect(() => {
    setSampleMode(new URLSearchParams(window.location.search).get("sample") === "1");
  }, []);

  const candidateLaunchpad = activeReview?.reviewResult?.outputs?.candidate_launchpad;
  const compactLaunchpadCards = activeReview?.reviewSummary?.launchpadCards;
  const launchpadRecord = isRecord(candidateLaunchpad)
    ? candidateLaunchpad
    : Array.isArray(compactLaunchpadCards)
      ? { cards: compactLaunchpadCards }
      : undefined;
  const builderOutput = activeReview?.reviewResult?.outputs?.portfolio_alternatives_builder;
  const compactBuilderOutput = activeReview?.reviewSummary?.builderSetup;
  const builderRecord = isRecord(builderOutput) ? builderOutput : isRecord(compactBuilderOutput) ? compactBuilderOutput : undefined;
  const rawLaunchpadCards = useMemo(() => getArray(launchpadRecord?.cards).filter(isRecord), [launchpadRecord]);
  const realCards = useMemo(() => rawLaunchpadCards.map(launchpadCardToHypothesis), [rawLaunchpadCards]);
  const completedRealReview = activeReview?.runMode === "real_run" && activeReview.runStatus === "completed";

  useEffect(() => {
    if (!selectedCardId) return;
    const stillExists = rawLaunchpadCards.some((card) => textValue(card.card_id, "") === selectedCardId);
    if (!stillExists) setSelectedCardId(null);
  }, [rawLaunchpadCards, selectedCardId]);

  const selectedRawCard = rawLaunchpadCards.find((card) => textValue(card.card_id, "") === selectedCardId);
  const reviewId = activeReview?.reviewId ?? activeReview?.reviewSummary?.reviewId ?? activeReview?.reviewResult?.review_id;

  useEffect(() => {
    setGenerationError(undefined);
  }, [selectedCardId, reviewId]);

  async function handleGenerateCandidate() {
    if (!reviewId || !selectedCardId) return;
    setIsGeneratingCandidate(true);
    setGenerationError(undefined);

    try {
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
        setGenerationError(errorTextFromResponse(result));
        return;
      }
      recordCandidateGeneration(result);
    } catch {
      setGenerationError("Candidate generation failed. Please try again; no comparison or verdict was created.");
    } finally {
      setIsGeneratingCandidate(false);
    }
  }

  if (sampleMode) {
    return (
      <div>
        <PageHeader
          kicker="Step 04 / Hypothesis"
          title="Sample hypothesis launchpad"
          description="Explicit demo mode is enabled by ?sample=1. This is not a real backend review."
        >
          <StatusBadge tone="slate">Demo sample</StatusBadge>
        </PageHeader>
        <div className="grid gap-7 xl:grid-cols-[minmax(0,1fr)_380px]">
          <section className="grid gap-5 lg:grid-cols-2">
            {demoLaunchpad.hypotheses.map((hypothesis) => (
              <HypothesisCard key={hypothesis.id} hypothesis={hypothesis} isPrimary={demoLaunchpad.selectedMethod.includes(hypothesis.methodId)} />
            ))}
          </section>
          <HypothesisBuilderPanel
            selectedMethod={demoLaunchpad.selectedMethod}
            builderStatus={demoLaunchpad.builderStatus}
            boundaryNote={demoLaunchpad.boundaryNote}
            constraints={demoLaunchpad.constraints}
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
        >
          <StatusBadge tone="amber">Real review required</StatusBadge>
        </PageHeader>
        <EmptyState
          title="Complete Portfolio Input first to unlock Hypothesis."
          description="Demo JSON is not used here unless you explicitly open /hypothesis?sample=1."
        />
      </div>
    );
  }

  if (!launchpadRecord || realCards.length === 0) {
    return (
      <div>
        <PageHeader
          kicker="Step 04 / Hypothesis"
          title="Problem Classification run required"
          description="Run diagnosis with Problem Classification to unlock Hypothesis."
        >
          <StatusBadge tone="amber">Launchpad missing</StatusBadge>
        </PageHeader>
        <EmptyState
          title="Run diagnosis with Problem Classification to unlock Hypothesis."
          description="The completed review does not include outputs.candidate_launchpad, so no real launchpad cards can be shown."
        />
      </div>
    );
  }

  return (
    <div>
      <PageHeader
        kicker="Step 04 / Hypothesis"
        title="Real Candidate Launchpad"
        description="These are hypothesis tests from the backend Candidate Launchpad. They are not recommendations and do not generate a candidate by themselves."
      >
        <StatusBadge tone="gold">Not a recommendation</StatusBadge>
      </PageHeader>
      <div className="mb-5 rounded-2xl border border-pmri-gold/35 bg-pmri-gold/10 p-4 text-sm leading-6 text-pmri-gold">
        Candidate is not a recommendation. Launchpad card is not a portfolio. Builder setup is not a rebalance instruction. Equal Weight / Risk Parity are reference tests if present.
      </div>
      <div className="grid gap-7 xl:grid-cols-[minmax(0,1fr)_420px]">
        <section className="grid gap-5 lg:grid-cols-2">
          {realCards.map((hypothesis, index) => (
            <HypothesisCard
              key={hypothesis.id}
              hypothesis={hypothesis}
              isPrimary={index === 0}
              isSelected={selectedCardId === hypothesis.id}
              onSelect={() => setSelectedCardId(hypothesis.id)}
            />
          ))}
        </section>
        <BuilderSetupPanel
          selectedCard={selectedRawCard}
          builderDocument={builderRecord}
          reviewId={reviewId}
          candidateGeneration={activeReview?.candidateGeneration}
          isGenerating={isGeneratingCandidate}
          generationError={generationError}
          onGenerate={handleGenerateCandidate}
        />
      </div>
    </div>
  );
}
