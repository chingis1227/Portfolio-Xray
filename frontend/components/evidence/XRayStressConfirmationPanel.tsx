import { StatusBadge } from "@/components/ui/StatusBadge";
import type { StressLabModel, XRayConfirmationRow } from "./stressLabTypes";
import { StressSectionHeader } from "./stressLabUi";

type ConfirmationDisplayRow = XRayConfirmationRow & {
  status: "Confirmed" | "Less material" | "Data-limited";
};

function statusTone(status: ConfirmationDisplayRow["status"]) {
  if (status === "Confirmed") return "amber" as const;
  if (status === "Less material") return "slate" as const;
  return "amber" as const;
}

export function XRayStressConfirmationPanel({ confirmation }: { confirmation: StressLabModel["xrayConfirmation"] }) {
  const rows: ConfirmationDisplayRow[] = [
    ...confirmation.confirmed.map((row) => ({ ...row, status: "Confirmed" as const })),
    ...confirmation.lessMaterial.map((row) => ({ ...row, status: "Less material" as const })),
    ...confirmation.insufficientData.map((row) => ({ ...row, status: "Data-limited" as const }))
  ];

  return (
    <section id="xray-confirmation" className="pmri-card rounded-3xl p-5 md:p-7">
      <StressSectionHeader
        eyebrow="Why this follows Diagnosis"
        title="Diagnosis confirmation"
        body="Diagnosis creates pre-stress hypotheses. Stress Lab checks whether those weaknesses appear under scenario evidence."
      />
      <div className="mt-5 rounded-2xl border border-pmri-border/55 bg-black/10 p-4 text-sm leading-6 text-pmri-text2">
        {confirmation.note}
      </div>
      <div className="mt-6 overflow-hidden rounded-2xl border border-pmri-border/55">
        <div className="grid grid-cols-[0.9fr_1.4fr_0.55fr] gap-3 border-b border-pmri-border/55 bg-white/[0.035] px-4 py-3 text-xs font-semibold uppercase tracking-[0.16em] text-pmri-muted">
          <span>X-Ray weakness</span>
          <span>Stress evidence</span>
          <span>Confirmation status</span>
        </div>
        <div className="divide-y divide-pmri-border/45">
          {rows.length ? rows.map((row) => (
            <article key={`${row.status}-${row.label}-${row.detail}`} className="grid gap-3 px-4 py-4 text-sm md:grid-cols-[0.9fr_1.4fr_0.55fr] md:items-start">
              <h3 className="font-semibold text-pmri-text">{row.label}</h3>
              <p className="leading-6 text-pmri-text2">{row.detail}</p>
              <div>
                <StatusBadge tone={statusTone(row.status)}>{row.status}</StatusBadge>
              </div>
            </article>
          )) : (
            <p className="p-4 text-sm leading-6 text-pmri-muted">
              No diagnosis confirmation mapping was returned for this stress run.
            </p>
          )}
        </div>
      </div>
    </section>
  );
}
