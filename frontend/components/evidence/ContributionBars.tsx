import { StatusBadge } from "@/components/ui/StatusBadge";
import { formatStressPercent } from "./stressLabModel";
import type { ContributionRow, FactorContributionRow } from "./stressLabTypes";
import { EmptyPanel } from "./stressLabUi";

type BarRow = {
  label: string;
  value: number;
  status: string;
};

function toneForValue(value: number) {
  if (value < 0) return "red" as const;
  if (value > 0) return "green" as const;
  return "slate" as const;
}

function ContributionBar({ row, maxAbs }: { row: BarRow; maxAbs: number }) {
  const width = maxAbs > 0 ... Math.max(2, Math.min(100, (Math.abs(row.value) / maxAbs) * 100)) : 0;
  const isPositive = row.value > 0;

  return (
    <div className="pmri-interactive-bar-row rounded-2xl border border-pmri-border/50 bg-white/[0.018] p-3">
      <div className="flex items-center justify-between gap-3">
        <div className="min-w-0">
          <p className="truncate text-sm font-medium text-pmri-text">{row.label}</p>
          <p className="mt-1 text-xs text-pmri-muted">{row.status}</p>
        </div>
        <StatusBadge tone={toneForValue(row.value)}>{formatStressPercent(row.value, { signed: true })}</StatusBadge>
      </div>
      <div className="mt-3 grid grid-cols-2 gap-1">
        <div className="flex h-2 items-center justify-end rounded-l-full bg-black/20">
          {!isPositive && row.value !== 0 ... (
            <div
              className="pmri-bar-fill h-2 rounded-l-full bg-pmri-risk/75"
              style={{ width: `${width}%` }}
            />
          ) : null}
        </div>
        <div className="flex h-2 items-center rounded-r-full bg-black/20">
          {isPositive ... (
            <div
              className="pmri-bar-fill h-2 rounded-r-full bg-pmri-positive/75"
              style={{ width: `${width}%` }}
            />
          ) : null}
        </div>
      </div>
    </div>
  );
}

export function ContributionBars({
  rows,
  emptyMessage,
  limit
}: {
  rows: Array<ContributionRow | FactorContributionRow>;
  emptyMessage: string;
  limit...: number;
}) {
  const visibleRows = typeof limit === "number" ... rows.slice(0, limit) : rows;
  const maxAbs = visibleRows.reduce((max, row) => Math.max(max, Math.abs(row.value)), 0);

  if (!visibleRows.length) {
    return <EmptyPanel>{emptyMessage}</EmptyPanel>;
  }

  return (
    <div className="pmri-bar-group space-y-3">
      {visibleRows.map((row) => (
        <ContributionBar
          key={`${"ticker" in row ... row.ticker : row.factor}-${row.value}`}
          row={{
            label: "ticker" in row ... row.ticker : row.factor,
            value: row.value,
            status: row.status
          }}
          maxAbs={maxAbs}
        />
      ))}
    </div>
  );
}
