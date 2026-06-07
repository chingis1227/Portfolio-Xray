import type { ComparisonMetric } from "@/lib/types";
import { StatusBadge } from "@/components/ui/StatusBadge";

export function CandidateComparisonPanel({ candidateName, candidateBoundary, evidenceQuality, summary, metrics }: { candidateName: string; candidateBoundary: string; evidenceQuality: string; summary: string; metrics: ComparisonMetric[] }) {
  return (
    <section className="rounded-2xl border border-pmri-border/80 bg-pmri-secondary/45 p-5">
      <div className="flex flex-col gap-4 border-b border-pmri-border/70 pb-5 md:flex-row md:items-start md:justify-between">
        <div>
          <p className="text-xs font-semibold uppercase tracking-[0.16em] text-pmri-muted">Detailed comparison</p>
          <h2 className="mt-2 text-xl font-semibold text-pmri-text">{candidateName}</h2>
          <p className="mt-3 max-w-3xl text-sm leading-6 text-pmri-text2">{summary}</p>
        </div>
        <div className="flex flex-wrap gap-2">
          <StatusBadge tone="amber">{evidenceQuality}</StatusBadge>
          <StatusBadge tone="gold">Diagnostic benchmark</StatusBadge>
        </div>
      </div>
      <p className="mt-4 rounded-xl border border-pmri-gold/30 bg-pmri-gold/10 p-3 text-sm leading-6 text-pmri-gold">{candidateBoundary}</p>
      <div className="mt-5 overflow-hidden rounded-xl border border-pmri-border/80">
        <table className="w-full border-collapse text-left text-sm">
          <thead className="bg-pmri-secondary/70 text-xs uppercase tracking-[0.12em] text-pmri-muted">
            <tr>
              <th scope="col" className="px-4 py-3">Metric</th>
              <th scope="col" className="px-4 py-3">Current</th>
              <th scope="col" className="px-4 py-3">Candidate</th>
              <th scope="col" className="px-4 py-3">Direction</th>
              <th scope="col" className="px-4 py-3">Trade-off</th>
            </tr>
          </thead>
          <tbody className="divide-y divide-pmri-border/70">
            {metrics.map((row) => (
              <tr key={row.metric} className="bg-white/[0.01]">
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

