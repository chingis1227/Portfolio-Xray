import type { ComparisonMetric } from "@/lib/types";
import { StatusBadge } from "@/components/ui/StatusBadge";

export function CandidateComparisonPanel({ candidateName, candidateBoundary, evidenceQuality, summary, metrics }: { candidateName: string; candidateBoundary: string; evidenceQuality: string; summary: string; metrics: ComparisonMetric[] }) {
  return (
    <section className="rounded-2xl border border-pmri-border/45 bg-pmri-secondary/35 p-5 shadow-decision">
      <div className="flex flex-col gap-4 border-b border-pmri-border/40 pb-5 md:flex-row md:items-start md:justify-between">
        <div>
          <p className="pmri-label">Detailed comparison</p>
          <h2 className="pmri-heading-section mt-2 text-xl text-pmri-text">{candidateName}</h2>
          <p className="mt-3 max-w-3xl text-sm leading-6 text-pmri-text2">{summary}</p>
        </div>
        <div className="flex flex-wrap gap-2">
          <StatusBadge tone="amber">{evidenceQuality}</StatusBadge>
          <StatusBadge tone="slate">Diagnostic candidate</StatusBadge>
        </div>
      </div>
      <p className="mt-4 rounded-xl border border-pmri-border/45 bg-white/[0.026] p-3 text-sm leading-6 text-pmri-text2">{candidateBoundary}</p>
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
            {metrics.map((row) => (
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
    </section>
  );
}

