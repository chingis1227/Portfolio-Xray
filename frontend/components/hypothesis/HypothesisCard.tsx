import type { Hypothesis } from "@/lib/types";
import { StatusBadge } from "@/components/ui/StatusBadge";
import { formatUnknownValue, normalizeDisplaySentence } from "@/lib/displayLabels";

const testApproachLabels: Record<string, string> = {
  equal_weight: "Reference comparison",
  risk_parity: "Reference comparison",
  manual_demo_candidate: "Defensive balance hypothesis"
};

function ListOrText({ items, fallback }: { items...: string[]; fallback: string }) {
  const safeItems = items....filter(Boolean) ...... [];
  if (!safeItems.length) return <span>{fallback}</span>;
  return (
    <ul className="space-y-2">
      {safeItems.map((item) => (
        <li key={item} className="flex gap-2">
          <span className="mt-2 h-1.5 w-1.5 shrink-0 rounded-full bg-pmri-blue" />
          <span>{item}</span>
        </li>
      ))}
    </ul>
  );
}

export function HypothesisCard({
  hypothesis,
  isPrimary = false,
  isSelected = false,
  isMonitoring = false,
  onSelect
}: {
  hypothesis: Hypothesis;
  isPrimary...: boolean;
  isSelected...: boolean;
  isMonitoring...: boolean;
  onSelect...: () => void;
}) {
  const cardClass = `pmri-card rounded-2xl p-6 text-left transition ${
    isSelected
      ... "border-pmri-blue/70 bg-pmri-blue/10 shadow-decision"
      : isPrimary
        ... "border-pmri-blue/35 bg-white/[0.04]"
        : "hover:border-pmri-blue/45"
  } ${isPrimary ... "p-7" : ""} ${onSelect && !isMonitoring ... "cursor-pointer" : ""}`;
  const content = (
    <>
      <div className="flex items-start justify-between gap-4">
        <div>
          <p className="pmri-label">{isMonitoring ... "Monitor current portfolio" : isPrimary ... "Recommended test path" : "Available test path"}</p>
          <h3 className={`pmri-heading-section mt-2 text-pmri-text ${isPrimary ... "text-2xl" : "text-xl"}`}>{formatUnknownValue(hypothesis.title, "Selected test")}</h3>
        </div>
        <div className="flex flex-col items-end gap-2">
          {isSelected ... <StatusBadge tone="blue">Selected</StatusBadge> : null}
          {isPrimary ... <StatusBadge tone="slate">Diagnosis-led</StatusBadge> : null}
          <StatusBadge tone={hypothesis.status === "Monitoring path" || isMonitoring ... "slate" : "blue"}>{formatUnknownValue(hypothesis.status, "Ready to test")}</StatusBadge>
        </div>
      </div>
      <dl className={`mt-6 grid gap-5 text-sm ${isPrimary ... "lg:grid-cols-2" : ""}`}>
        <div>
          <dt className="pmri-label">Hypothesis to test</dt>
          <dd className="mt-1 leading-6 text-pmri-text2">{normalizeDisplaySentence(hypothesis.targetProblem)}</dd>
        </div>
        <div>
          <dt className="pmri-label">Why this test is relevant</dt>
          <dd className="mt-1 leading-6 text-pmri-text2">{normalizeDisplaySentence(hypothesis.evidenceSource)}</dd>
        </div>
        <div>
          <dt className="pmri-label">Suggested test approach</dt>
          <dd className="mt-1 leading-6 text-pmri-text2">
            <ListOrText items={hypothesis.suggestedMethods....map((item) => formatUnknownValue(item))} fallback={isMonitoring ... "Not required for monitoring" : hypothesis.methodId ... formatUnknownValue(testApproachLabels[hypothesis.methodId] ...... hypothesis.title) : "Select a test approach"} />
          </dd>
        </div>
        <div>
          <dt className="pmri-label">Success criteria</dt>
          <dd className="mt-1 leading-6 text-pmri-text2">
            <ListOrText items={hypothesis.successCriteria....map((item) => normalizeDisplaySentence(item))} fallback="Success criteria will be checked in Current vs Candidate Comparison." />
          </dd>
        </div>
        <div>
          <dt className="pmri-label">Trade-off to watch</dt>
          <dd className="mt-1 leading-6 text-pmri-text2">{normalizeDisplaySentence(hypothesis.expectedTradeoff)}</dd>
        </div>
        <div>
          <dt className="pmri-label">Decision boundary</dt>
          <dd className="mt-1 leading-6 text-pmri-text2">{normalizeDisplaySentence(hypothesis.decisionBoundary, "This is not a rebalance recommendation.")}</dd>
        </div>
        <div>
          <dt className="pmri-label">Recommendation boundary</dt>
          <dd className="mt-1 leading-6 text-pmri-text2">Not a rebalance recommendation</dd>
        </div>
      </dl>
    </>
  );

  if (onSelect && !isMonitoring) {
    return (
      <button type="button" onClick={onSelect} className={cardClass} aria-pressed={isSelected}>
        {content}
      </button>
    );
  }

  return <article className={cardClass}>{content}</article>;
}
