"use client";

import { useEffect, useMemo, useState } from "react";
import { useRouter } from "next/navigation";
import { OnboardingFrame } from "@/components/onboarding/OnboardingFrame";
import {
  readOnboardingState,
  writeOnboardingState,
  type OnboardingDecisionStyle,
  type OnboardingHorizon,
  type OnboardingObjective,
  type OnboardingPrimaryConcern,
  type OnboardingRiskComfort,
  type OnboardingState
} from "@/lib/onboarding";

type Option<T extends string> = {
  id: T;
  label: string;
  detail: string;
};

const objectiveOptions: Array<Option<OnboardingObjective>> = [
  { id: "preserve", label: "Preserve capital first", detail: "The diagnosis should be strict about drawdown and stability." },
  { id: "balanced", label: "Balance growth and resilience", detail: "The diagnosis should weigh upside against stress behavior." },
  { id: "growth", label: "Grow over a full cycle", detail: "The diagnosis can tolerate more volatility if evidence improves." },
  { id: "understand_risk", label: "Understand what I already own", detail: "The first job is to identify the real risk drivers." }
];

const horizonOptions: Array<Option<OnboardingHorizon>> = [
  { id: "short", label: "Less than 3 years", detail: "Capital path and temporary loss matter more." },
  { id: "medium", label: "3–10 years", detail: "The system can test medium-term trade-offs." },
  { id: "long", label: "10+ years", detail: "The system can tolerate wider cycles in the evidence." }
];

const riskOptions: Array<Option<OnboardingRiskComfort>> = [
  { id: "low", label: "Small temporary losses", detail: "Use conservative Client Fit ranges." },
  { id: "medium", label: "Moderate drawdowns", detail: "Use balanced ranges and stress checks." },
  { id: "high", label: "Large swings if justified", detail: "Allow growth-oriented ranges." }
];

const decisionOptions: Array<Option<OnboardingDecisionStyle>> = [
  { id: "evidence_first", label: "Do nothing unless evidence is clear", detail: "No-change remains a serious outcome." },
  { id: "preserve_unless_clear", label: "Protect capital unless change is obvious", detail: "The system should penalize weak downside evidence." },
  { id: "improve_structure", label: "Improve structure before chasing return", detail: "Focus on concentration, overlap, and hidden exposures." },
  { id: "test_growth", label: "Test whether more growth is justified", detail: "Compare growth evidence against added risk." }
];

const concernOptions: Array<Option<OnboardingPrimaryConcern>> = [
  { id: "concentration", label: "Hidden concentration", detail: "Are several tickers really the same risk..." },
  { id: "drawdown", label: "Loss in a stress event", detail: "What happens when markets break against me..." },
  { id: "rates", label: "Rates and bond sensitivity", detail: "How exposed is the portfolio to rate shocks..." },
  { id: "inflation", label: "Inflation / real asset protection", detail: "Does the portfolio have any offset..." },
  { id: "unknown", label: "I am not sure yet", detail: "Start with broad X-Ray and Stress Lab evidence." }
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

export default function InvestorTypePage() {
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
      investorType: state.objective === "growth" ? "growth_seeker" : state.objective === "preserve" ? "capital_guardian" : state.primaryConcern === "unknown" ? "risk_mapper" : "balanced_builder"
    } satisfies OnboardingState;
    writeOnboardingState(next);
    router.push("/onboarding/loading");
  }

  const questions = useMemo(() => [
    {
      key: "objective",
      number: "01",
      title: "What is the portfolio's primary job...",
      value: state.objective,
      options: objectiveOptions,
      onChange: (objective: OnboardingObjective) => update({ objective })
    },
    {
      key: "horizon",
      number: "02",
      title: "What is the real decision horizon...",
      value: state.horizon,
      options: horizonOptions,
      onChange: (horizon: OnboardingHorizon) => update({ horizon })
    },
    {
      key: "riskComfort",
      number: "03",
      title: "How much temporary loss can the plan tolerate...",
      value: state.riskComfort,
      options: riskOptions,
      onChange: (riskComfort: OnboardingRiskComfort) => update({ riskComfort })
    },
    {
      key: "decisionStyle",
      number: "04",
      title: "How should the system treat changes...",
      value: state.decisionStyle,
      options: decisionOptions,
      onChange: (decisionStyle: OnboardingDecisionStyle) => update({ decisionStyle })
    },
    {
      key: "primaryConcern",
      number: "05",
      title: "What worries you most about the current portfolio...",
      value: state.primaryConcern,
      options: concernOptions,
      onChange: (primaryConcern: OnboardingPrimaryConcern) => update({ primaryConcern })
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
