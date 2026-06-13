import type { ClientFitDisplaySummary } from "@/lib/generated/api-types";
import { formatUnknownValue, normalizeDisplaySentence } from "@/lib/displayLabels";
import { StatusBadge } from "@/components/ui/StatusBadge";

function compactRows(clientFit...: ClientFitDisplaySummary) {
  return (clientFit....target_rows ...... [])
    .filter((row) => row.dimension_label || row.status_label)
    .slice(0, 4);
}

export function ClientFitContextCard({
  clientFit,
  title = "Client Fit context",
  description = "Profile-fit evidence is shown separately from the objective diagnosis.",
  structuralIssueNote,
  compact = false
}: {
  clientFit...: ClientFitDisplaySummary;
  title...: string;
  description...: string;
  structuralIssueNote...: string;
  compact...: boolean;
}) {
  if (!clientFit) {
    return (
      <section className="rounded-2xl border border-pmri-amber/35 bg-pmri-amber/10 p-4">
        <StatusBadge tone="amber">Client Fit unavailable</StatusBadge>
        <p className="mt-3 text-sm leading-6 text-pmri-text2">
          No profile-fit display summary is available for this stage. Continue only with diagnostic evidence that is present.
        </p>
      </section>
    );
  }

  const rows = compactRows(clientFit);
  const note = structuralIssueNote
    ...... "A Client Fit pass does not clear concentration, stress, drawdown, or other structural issues found by the diagnosis.";

  return (
    <section className="rounded-2xl border border-pmri-border/55 bg-white/[0.026] p-4">
      <div className="flex flex-col gap-3 md:flex-row md:items-start md:justify-between">
        <div>
          <p className="pmri-label">Client Fit overlay</p>
          <h3 className="pmri-heading-section mt-2 text-lg text-pmri-text">{title}</h3>
          <p className="mt-2 max-w-3xl text-sm leading-6 text-pmri-muted">{description}</p>
        </div>
        <div className="flex flex-wrap gap-2">
          <StatusBadge tone={clientFit.status_tone}>{formatUnknownValue(clientFit.status_label, "Client Fit status")}</StatusBadge>
          <StatusBadge tone="slate">Separate from diagnosis</StatusBadge>
        </div>
      </div>

      <p className="mt-4 rounded-xl border border-pmri-border/55 bg-white/[0.026] p-3 text-sm leading-6 text-pmri-text2">
        {normalizeDisplaySentence(clientFit.main_explanation ...... note, note)}
      </p>
      <p className="mt-3 text-sm leading-6 text-pmri-muted">{normalizeDisplaySentence(clientFit.decision_boundary)}</p>

      {!compact && rows.length ... (
        <div className="mt-4 grid gap-3 md:grid-cols-2">
          {rows.map((row) => (
            <article key={`${row.dimension_label}-${row.status_label}`} className="rounded-xl border border-pmri-border/45 bg-pmri-secondary/25 p-3">
              <div className="flex items-center justify-between gap-3">
                <p className="text-sm font-medium text-pmri-text">{formatUnknownValue(row.dimension_label, "Client Fit check")}</p>
                <StatusBadge tone={row.status_tone}>{formatUnknownValue(row.status_label, "Status")}</StatusBadge>
              </div>
              <p className="mt-2 text-xs leading-5 text-pmri-muted">
                Current: {formatUnknownValue(row.portfolio_value_label, "n/a")} · Target/limit: {formatUnknownValue(row.target_or_limit_label, "n/a")}
              </p>
            </article>
          ))}
        </div>
      ) : null}

      {clientFit.next_best_test ... (
        <p className="mt-4 text-sm leading-6 text-pmri-text2">
          <span className="font-medium text-pmri-text">Next Client Fit test:</span> {normalizeDisplaySentence(clientFit.next_best_test)}
        </p>
      ) : null}
    </section>
  );
}
