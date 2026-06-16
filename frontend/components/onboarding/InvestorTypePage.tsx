"use client";

import { useEffect, useMemo, useState } from "react";
import { useRouter } from "next/navigation";
import { OnboardingFrame } from "@/components/onboarding/OnboardingFrame";
import {
  readOnboardingState,
  writeOnboardingState,
  type OnboardingConcentrationAction,
  type OnboardingHorizon,
  type OnboardingReturnNeed,
  type OnboardingState,
  type OnboardingStressLimit,
  type OnboardingStressReaction
} from "@/lib/onboarding";

type Option<T extends string> = {
  id: T;
  label: string;
  detail: string;
};

const stressReactionOptions: Array<Option<OnboardingStressReaction>> = [
  { id: "sell_all", label: "Sell all risky positions", detail: "Avoid a deeper loss even if the portfolio may rebound later." },
  { id: "sell_some", label: "Sell some and wait", detail: "Cut risk first, then decide whether to re-enter." },
  { id: "hold", label: "Hold and review evidence", detail: "Do not panic, but check whether the portfolio still fits the plan." },
  { id: "buy_more", label: "Buy more if fundamentals hold", detail: "Use the drawdown as an opportunity if the evidence remains strong." }
];

const horizonOptions: Array<Option<OnboardingHorizon>> = [
  { id: "short", label: "Less than 3 years", detail: "Capital path and temporary loss matter more." },
  { id: "medium", label: "3-10 years", detail: "The system can test medium-term trade-offs." },
  { id: "long", label: "10+ years", detail: "The system can tolerate wider cycles in the evidence." }
];

const stressLimitOptions: Array<Option<OnboardingStressLimit>> = [
  { id: "ten", label: "Around 10%", detail: "A low temporary-loss limit; use strict defensive ranges." },
  { id: "fifteen", label: "Around 15%", detail: "Some temporary loss is acceptable, but preservation still matters." },
  { id: "twenty_five", label: "Around 25%", detail: "The profile can tolerate equity-like drawdowns if evidence supports it." },
  { id: "thirty_five", label: "Around 35%+", detail: "Large cyclical losses are acceptable for higher growth potential." }
];

const returnNeedOptions: Array<Option<OnboardingReturnNeed>> = [
  { id: "low", label: "3-5% is enough", detail: "Capital stability matters more than higher expected return." },
  { id: "moderate", label: "5-8% target range", detail: "Balanced growth with visible downside control." },
  { id: "high", label: "8-12% target range", detail: "Higher return is needed, with more volatility accepted." },
  { id: "very_high", label: "12%+ target range", detail: "Aggressive growth target; the system should flag risk conflicts clearly." }
];

const concentrationOptions: Array<Option<OnboardingConcentrationAction>> = [
  { id: "reduce_first", label: "Reduce concentration first", detail: "Do not accept single-theme or single-name risk without strong proof." },
  { id: "diagnose_then_adjust", label: "Diagnose before changing", detail: "Show whether concentration is actually driving the risk." },
  { id: "hold_if_evidence_ok", label: "Hold if evidence is good", detail: "Concentration is acceptable when stress and quality checks support it." },
  { id: "add_if_compensated", label: "Add if upside compensates", detail: "Accept more concentration only if the risk-return evidence improves." }
];

function Question<T extends string>({
  number,
  title,
  value,
  options,
  onChange,
  active
}: {
  number: string;
  title: string;
  value: T;
  options: Array<Option<T>>;
  onChange: (value: T) => void;
  active: boolean;
}) {
  return (
    <section
      key={number}
      className={`rounded-[2rem] border border-pmri-border/45 bg-white/[0.022] p-4 shadow-decision transition duration-500 md:p-5 motion-safe:animate-[pmri-section-reveal_520ms_cubic-bezier(0.2,0.8,0.2,1)] ${
        active ? "opacity-100" : "opacity-0"
      }`}
    >
      <div className="flex flex-col gap-3 sm:flex-row sm:items-center sm:justify-between">
        <div className="flex items-center gap-3">
          <span className="flex h-8 w-8 items-center justify-center rounded-full border border-pmri-blue/30 bg-pmri-blue/[0.07] data-figure text-xs text-pmri-blueSoft">{number}</span>
          <h2 className="text-lg font-semibold tracking-[-0.025em] text-pmri-text">{title}</h2>
        </div>
        <span className="rounded-full border border-pmri-border/45 bg-white/[0.025] px-3 py-1 text-xs text-pmri-muted">
          Choose one answer
        </span>
      </div>
      <div className="mt-4 grid gap-3 md:grid-cols-2">
        {options.map((option) => (
          <button
            key={option.id}
            type="button"
            onClick={() => onChange(option.id)}
            className={`pmri-focus cursor-pointer rounded-2xl border p-4 text-left transition ${value === option.id ? "border-pmri-blue/60 bg-pmri-blue/[0.11]" : "border-pmri-border/55 bg-white/[0.02] hover:border-pmri-border hover:bg-white/[0.04]"}`}
          >
            <span className="block text-sm font-semibold text-pmri-text">{option.label}</span>
            <span className="mt-1 block text-xs leading-5 text-pmri-muted">{option.detail}</span>
          </button>
        ))}
      </div>
    </section>
  );
}

export function InvestorTypePage() {
  const router = useRouter();
  const [state, setState] = useState<OnboardingState>(() => readOnboardingState());
  const [activeQuestionIndex, setActiveQuestionIndex] = useState(0);

  useEffect(() => {
    setState(readOnboardingState());
  }, []);

  function update(next: Partial<OnboardingState>) {
    setState((current) => ({ ...current, ...next }));
  }

  function continueToLoading() {
    const next = {
      ...state,
      investorType: state.stressReaction === "buy_more" || state.returnNeed === "very_high"
        ? "growth_seeker"
        : state.stressReaction === "sell_all" || state.stressLimit === "ten"
          ? "capital_guardian"
          : state.primaryConcern === "unknown"
            ? "risk_mapper"
            : "balanced_builder"
    } satisfies OnboardingState;
    writeOnboardingState(next);
    router.push("/onboarding/loading");
  }

  const questions = useMemo(() => [
    {
      key: "stressReaction",
      number: "01",
      title: "If this portfolio fell 25% in three months...",
      value: state.stressReaction,
      options: stressReactionOptions,
      onChange: (stressReaction: OnboardingStressReaction) => update({ stressReaction })
    },
    {
      key: "horizon",
      number: "02",
      title: "When will this money need to work for withdrawals...",
      value: state.horizon,
      options: horizonOptions,
      onChange: (horizon: OnboardingHorizon) => update({ horizon })
    },
    {
      key: "stressLimit",
      number: "03",
      title: "What temporary loss limit should trigger concern...",
      value: state.stressLimit,
      options: stressLimitOptions,
      onChange: (stressLimit: OnboardingStressLimit) => update({ stressLimit })
    },
    {
      key: "returnNeed",
      number: "04",
      title: "What return target would make the risk worthwhile...",
      value: state.returnNeed,
      options: returnNeedOptions,
      onChange: (returnNeed: OnboardingReturnNeed) => update({ returnNeed })
    },
    {
      key: "concentrationAction",
      number: "05",
      title: "If the current portfolio is concentrated...",
      value: state.concentrationAction,
      options: concentrationOptions,
      onChange: (concentrationAction: OnboardingConcentrationAction) => update({ concentrationAction })
    }
  ], [state]);

  const currentQuestion = questions[activeQuestionIndex] ?? questions[0];
  const isLastQuestion = activeQuestionIndex >= questions.length - 1;
  const progressPct = Math.round(((activeQuestionIndex + 1) / questions.length) * 100);

  function answerCurrent(value: string) {
    currentQuestion.onChange(value as never);
    if (!isLastQuestion) {
      window.setTimeout(() => {
        setActiveQuestionIndex((current) => Math.min(current + 1, questions.length - 1));
      }, 180);
    }
  }

  return (
    <OnboardingFrame
      currentStep={2}
      eyebrow="Portfolio manager intake"
      title={`Five questions before we open the portfolio screen${state.name ? `, ${state.name}` : ""}.`}
      description="Answer one question at a time. We will use the answers to prepare a starting planning preset before the portfolio screen opens."
      backHref="/onboarding/name"
    >
      <div className="space-y-5 text-left">
        <div className="rounded-2xl border border-pmri-border/45 bg-white/[0.018] p-3">
          <div className="flex items-center justify-between gap-3 text-xs text-pmri-muted">
            <span>Question {activeQuestionIndex + 1} of {questions.length}</span>
            <span className="data-figure">{progressPct}%</span>
          </div>
          <div className="mt-3 h-1.5 overflow-hidden rounded-full bg-pmri-border/45">
            <div className="h-full rounded-full bg-pmri-blue transition-all duration-500" style={{ width: `${progressPct}%` }} />
          </div>
        </div>

        <Question
          key={currentQuestion.key}
          number={currentQuestion.number}
          title={currentQuestion.title}
          value={currentQuestion.value as never}
          options={currentQuestion.options as Array<Option<never>>}
          onChange={answerCurrent}
          active
        />

        <div className="flex flex-col gap-3 sm:flex-row sm:items-center sm:justify-between">
          <button
            type="button"
            disabled={activeQuestionIndex === 0}
            onClick={() => setActiveQuestionIndex((current) => Math.max(0, current - 1))}
            className="pmri-focus rounded-full border border-pmri-border/60 bg-white/[0.025] px-5 py-3 text-sm font-medium text-pmri-text2 transition hover:border-pmri-blue/35 hover:text-pmri-text disabled:cursor-not-allowed disabled:opacity-40"
          >
            Back
          </button>
          {isLastQuestion ? (
            <button type="button" onClick={continueToLoading} className="pmri-focus pmri-primary-action rounded-full px-6 py-3 text-sm font-semibold transition">
              Save intake and open Portfolio Input
            </button>
          ) : (
            <button
              type="button"
              onClick={() => setActiveQuestionIndex((current) => Math.min(current + 1, questions.length - 1))}
              className="pmri-focus rounded-full border border-pmri-blue/35 bg-pmri-blue/[0.08] px-5 py-3 text-sm font-medium text-pmri-text transition hover:bg-pmri-blue/[0.12]"
            >
              Next question
            </button>
          )}
        </div>
      </div>
    </OnboardingFrame>
  );
}
