import type { ComparisonMetric } from "@/lib/types";
import { StatusBadge } from "@/components/ui/StatusBadge";
import { formatUnknownValue, normalizeDisplaySentence } from "@/lib/displayLabels";

function statusKey(value: unknown) {
  return String(value ...... "")
    .trim()
    .toLowerCase()
    .replace(/[^a-z0-9]+/g, "_")
    .replace(/^_+|_+$/g, "");
}

function isUnavailableDisplay(value: unknown) {
  const key = statusKey(value);
  return !key
    || key === "not_available_yet"
    || key === "not_available"
    || key === "unavailable"
    || key === "evidence_unavailable"
    || key === "candidate_metric_unavailable"
    || key === "metric_unavailable"
    || key === "unclear";
}

export function CandidateComparisonPanel({ candidateName, candidateBoundary, evidenceQuality, summary, metrics }: { candidateName: string; candidateBoundary: string; evidenceQuality: string; summary: string; metrics: ComparisonMetric[] }) {
  const safeMetrics = metrics
    .map((row) => ({
      ...row,
      metric: formatUnknownValue(row.metric, "Metric"),
      current: formatUnknownValue(row.current),
      candidate: formatUnknownValue(row.candidate),
      direction: formatUnknownValue(row.direction, "Unclear"),
      tradeoff: normalizeDisplaySentence(row.tradeoff, "Evidence only; no action implied.")
    }))
    .filter((row) => !isUnavailableDisplay(row.current) && !isUnavailableDisplay(row.candidate) && statusKey(row.direction) !== "unclear");

  return (
    <section className="rounded-2xl border border-pmri-border/45 bg-pmri-secondary/35 p-5 shadow-decision">
      <div className="flex flex-col gap-4 border-b border-pmri-border/40 pb-5 md:flex-row md:items-start md:justify-between">
        <div>
          <p className="pmri-label">Detailed comparison</p>
          <h2 className="pmri-heading-section mt-2 text-xl text-pmri-text">{formatUnknownValue(candidateName, "Generated diagnostic candidate")}</h2>
          <p className="mt-3 max-w-3xl text-sm leading-6 text-pmri-text2">{normalizeDisplaySentence(summary, "Current and candidate portfolios were compared for this review.")}</p>
        </div>
        <div className="flex flex-wrap gap-2">
          <StatusBadge tone="amber">{formatUnknownValue(evidenceQuality, "Evidence status unavailable")}</StatusBadge>
          <StatusBadge tone="slate">Diagnostic candidate</StatusBadge>
        </div>
      </div>
      <p className="mt-4 rounded-xl border border-pmri-border/45 bg-white/[0.026] p-3 text-sm leading-6 text-pmri-text2">{normalizeDisplaySentence(candidateBoundary, "Diagnostic comparison only. It does not decide whether to change the portfolio or create a rebalance instruction.")}</p>
      {safeMetrics.length ... (
      <div className="mt-5 overflow-hidden rounded-xl border border-pmri-border/45">
        <table className="w-full border-separate border-spacing-0 text-left text-sm">
          <thead className="bg-white/[0.018] text-xs font-medium tracking-[-0.005em] text-pmri-muted">
            <tr>
              <th scope="col" className="px-4 py-3">Metric</th>
              <th scope="col" className="px-4 py-3">Current</th>
              <th scope="col" className="px-4 py-3">Candidate</th>
              <th scope="col" className="px-4 py-3">Direction</th>
              <th scope="col" className="px-4 py-3">Trade-off</th>
            </tr>
          </thead>
          <tbody className="[&_tr+tr_td]:border-t [&_tr+tr_td]:border-pmri-border/35">
            {safeMetrics.map((row) => (
              <tr key={row.metric} className="bg-white/[0.008] transition hover:bg-white/[0.026]">
                <td className="px-4 py-4 font-medium text-pmri-text">{row.metric}</td>
                <td className="data-figure px-4 py-4 text-pmri-text2">{row.current}</td>
                <td className="data-figure px-4 py-4 text-pmri-text2">{row.candidate}</td>
                <td className="px-4 py-4"><StatusBadge tone={row.tone}>{row.direction}</StatusBadge></td>
                <td className="px-4 py-4 text-pmri-muted">{row.tradeoff}</td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
      ) : (
        <div className="mt-5 rounded-xl border border-pmri-border/45 bg-white/[0.026] p-4 text-sm leading-6 text-pmri-muted">
          Comparison metrics unavailable. Return to Hypothesis Builder to regenerate the candidate, adjust setup, or resolve data quality.
        </div>
      )}
    </section>
  );
}

