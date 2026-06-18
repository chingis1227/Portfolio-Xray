import type { ReactNode } from "react";
import type { StatusTone } from "@/lib/types";
import { StatusBadge } from "@/components/ui/StatusBadge";

export type MetricMatrixStatus = {
  label: string;
  tone?: StatusTone;
};

export type MetricMatrixRow = {
  metric: string;
  portfolioValue?: ReactNode;
  reference?: ReactNode;
  status?: MetricMatrixStatus;
  meaning: ReactNode;
  material?: boolean;
};

export type MetricMatrixGroup = {
  title: string;
  description?: string;
  rows: MetricMatrixRow[];
};

export type ComparisonMetricMatrixRow = {
  metric: string;
  currentPortfolio?: ReactNode;
  candidatePortfolio?: ReactNode;
  change?: ReactNode;
  status?: MetricMatrixStatus;
  interpretation: ReactNode;
  material?: boolean;
};

function orderedRows<T extends { material?: boolean }>(rows: T[]) {
  return [...rows].sort((a, b) => Number(Boolean(b.material)) - Number(Boolean(a.material)));
}

export function MetricMatrix({
  groups,
  title = "Diagnosis metrics by decision relevance",
  description = "These rows sit below the first-read conclusion. Each metric is included only when it helps explain the problem, why it matters, or what would change the decision."
}: {
  groups: MetricMatrixGroup[];
  title?: string;
  description?: string;
}) {
  return (
    <section className="pmri-card rounded-3xl p-5 md:p-6">
      <div>
        <p className="pmri-type-meta text-pmri-text2">Metric matrix</p>
        <h2 className="pmri-type-section-title mt-2 text-pmri-text">{title}</h2>
        <p className="mt-2 max-w-3xl text-sm leading-6 text-pmri-text2">
          {description}
        </p>
      </div>
      <div className="mt-6 space-y-6">
        {groups.map((group) => (
          <div key={group.title}>
            <div className="mb-3">
              <h3 className="pmri-type-card-title text-pmri-text">{group.title}</h3>
              {group.description ? <p className="mt-1 text-xs leading-5 text-pmri-muted">{group.description}</p> : null}
            </div>
            <div className="overflow-hidden rounded-2xl border border-pmri-border/50 bg-white/[0.018]">
              <div className="hidden grid-cols-[1.05fr_0.85fr_0.85fr_0.65fr_1.45fr] border-b border-pmri-border/45 px-4 py-3 text-xs font-medium text-pmri-muted md:grid">
                <span>Metric</span>
                <span>Portfolio value</span>
                <span>Reference / threshold</span>
                <span>Status</span>
                <span>Meaning</span>
              </div>
              {orderedRows(group.rows).map((row, index) => (
                <div key={`${group.title}-${row.metric}-${index}`} className="grid gap-3 border-b border-pmri-border/35 px-4 py-4 last:border-b-0 md:grid-cols-[1.05fr_0.85fr_0.85fr_0.65fr_1.45fr] md:items-center">
                  <p className="text-sm font-semibold text-pmri-text">{row.metric}</p>
                  <p className="data-figure text-sm text-pmri-text2">{row.portfolioValue ?? "Unavailable"}</p>
                  <p className="text-sm text-pmri-text2">{row.reference ?? "Unavailable"}</p>
                  <div>{row.status ? <StatusBadge tone={row.status.tone}>{row.status.label}</StatusBadge> : null}</div>
                  <p className="text-sm leading-6 text-pmri-text2">{row.meaning}</p>
                </div>
              ))}
            </div>
          </div>
        ))}
      </div>
    </section>
  );
}

export function ComparisonMetricMatrix({ groups }: { groups: Array<{ title: string; description?: string; rows: ComparisonMetricMatrixRow[] }> }) {
  return (
    <section className="pmri-card rounded-3xl p-5 md:p-6">
      <p className="pmri-type-meta text-pmri-text2">Comparison matrix</p>
      <h2 className="pmri-type-section-title mt-2 text-pmri-text">Current portfolio vs test candidate</h2>
      <p className="mt-2 max-w-3xl text-sm leading-6 text-pmri-text2">
        These comparison metrics are secondary evidence. Read them as investor trade-offs, not as a portfolio winner.
      </p>
      <div className="mt-6 space-y-6">
        {groups.map((group) => (
          <div key={group.title}>
            <h3 className="pmri-type-card-title mb-3 text-pmri-text">{group.title}</h3>
            <div className="overflow-hidden rounded-2xl border border-pmri-border/50 bg-white/[0.018]">
              <div className="hidden grid-cols-[1fr_0.8fr_0.8fr_0.75fr_1.35fr] border-b border-pmri-border/45 px-4 py-3 text-xs font-medium text-pmri-muted md:grid">
                <span>Metric</span>
                <span>Current portfolio</span>
                <span>Candidate portfolio</span>
                <span>Change</span>
                <span>Interpretation</span>
              </div>
              {orderedRows(group.rows).map((row, index) => (
                <div key={`${group.title}-${row.metric}-${index}`} className="grid gap-3 border-b border-pmri-border/35 px-4 py-4 last:border-b-0 md:grid-cols-[1fr_0.8fr_0.8fr_0.75fr_1.35fr] md:items-center">
                  <p className="text-sm font-semibold text-pmri-text">{row.metric}</p>
                  <p className="data-figure text-sm text-pmri-text2">{row.currentPortfolio ?? "Unavailable"}</p>
                  <p className="data-figure text-sm text-pmri-text2">{row.candidatePortfolio ?? "Unavailable"}</p>
                  <div className="text-sm text-pmri-text2">{row.status ? <StatusBadge tone={row.status.tone}>{row.change ?? row.status.label}</StatusBadge> : row.change ?? "Unavailable"}</div>
                  <p className="text-sm leading-6 text-pmri-text2">{row.interpretation}</p>
                </div>
              ))}
            </div>
          </div>
        ))}
      </div>
    </section>
  );
}
