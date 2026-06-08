import type { Hypothesis } from "@/lib/types";
import { StatusBadge } from "@/components/ui/StatusBadge";

const testApproachLabels: Record<string, string> = {
  equal_weight: "Equal Weight diagnostic benchmark",
  risk_parity: "Risk Parity diagnostic benchmark",
  manual_demo_candidate: "Defensive balance hypothesis"
};

export function HypothesisCard({
  hypothesis,
  isPrimary = false,
  isSelected = false,
  onSelect
}: {
  hypothesis: Hypothesis;
  isPrimary?: boolean;
  isSelected?: boolean;
  onSelect?: () => void;
}) {
  const cardClass = `pmri-card rounded-2xl p-6 text-left transition ${
    isSelected
      ? "border-pmri-blue/70 bg-pmri-blue/10 shadow-decision"
      : isPrimary
        ? "border-pmri-gold/55 bg-[linear-gradient(180deg,rgba(18,38,58,0.96),rgba(13,27,42,0.9))]"
        : "hover:border-pmri-blue/45"
  }`;
  const content = (
    <>
      <div className="flex items-start justify-between gap-4">
        <div>
          <p className="text-xs font-semibold uppercase tracking-[0.14em] text-pmri-muted">Hypothesis test</p>
          <h3 className="mt-2 text-xl font-semibold text-pmri-text">{hypothesis.title}</h3>
        </div>
        <div className="flex flex-col items-end gap-2">
          {isSelected ? <StatusBadge tone="blue">Selected</StatusBadge> : null}
          {isPrimary ? <StatusBadge tone="gold">First test to review</StatusBadge> : null}
          <StatusBadge tone={hypothesis.status === "Concept only" ? "slate" : "blue"}>{hypothesis.status}</StatusBadge>
        </div>
      </div>
      <dl className="mt-6 space-y-5 text-sm">
        <div>
          <dt className="text-xs font-semibold uppercase tracking-[0.12em] text-pmri-muted">Test approach</dt>
          <dd className="mt-1 leading-6 text-pmri-text2">{testApproachLabels[hypothesis.methodId] ?? hypothesis.title}</dd>
        </div>
        <div>
          <dt className="text-xs font-semibold uppercase tracking-[0.12em] text-pmri-muted">Target problem</dt>
          <dd className="mt-1 leading-6 text-pmri-text2">{hypothesis.targetProblem}</dd>
        </div>
        <div>
          <dt className="text-xs font-semibold uppercase tracking-[0.12em] text-pmri-muted">Expected trade-off</dt>
          <dd className="mt-1 leading-6 text-pmri-text2">{hypothesis.expectedTradeoff}</dd>
        </div>
        <div>
          <dt className="text-xs font-semibold uppercase tracking-[0.12em] text-pmri-muted">Evidence source</dt>
          <dd className="mt-1 leading-6 text-pmri-text2">{hypothesis.evidenceSource}</dd>
        </div>
      </dl>
      <p className="mt-6 rounded-xl border border-pmri-amber/35 bg-pmri-amber/10 p-3 text-xs leading-5 text-pmri-amber">Candidate hypothesis test only — not a recommendation.</p>
    </>
  );

  if (onSelect) {
    return (
      <button type="button" onClick={onSelect} className={cardClass} aria-pressed={isSelected}>
        {content}
      </button>
    );
  }

  return <article className={cardClass}>{content}</article>;
}
