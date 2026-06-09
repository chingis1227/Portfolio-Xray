import { StatusBadge } from "@/components/ui/StatusBadge";
import type { StressLabModel, XRayConfirmationRow } from "./stressLabTypes";
import { EmptyPanel, StressSectionHeader } from "./stressLabUi";

function ConfirmationList({ rows, emptyMessage }: { rows: XRayConfirmationRow[]; emptyMessage: string }) {
  if (!rows.length) return <EmptyPanel>{emptyMessage}</EmptyPanel>;

  return (
    <div className="space-y-3">
      {rows.map((row) => (
        <article key={`${row.label}-${row.detail}`} className="rounded-2xl border border-pmri-border/50 bg-white/[0.02] p-4">
          <div className="flex items-start justify-between gap-3">
            <h3 className="text-sm font-semibold text-pmri-text">{row.label}</h3>
            <StatusBadge tone={row.tone}>{row.tone === "amber" ? "Confirmed" : "Review"}</StatusBadge>
          </div>
          <p className="mt-2 text-sm leading-6 text-pmri-text2">{row.detail}</p>
        </article>
      ))}
    </div>
  );
}

export function XRayStressConfirmationPanel({ confirmation }: { confirmation: StressLabModel["xrayConfirmation"] }) {
  return (
    <section id="xray-confirmation" className="pmri-card rounded-3xl p-5 md:p-7">
      <StressSectionHeader
        eyebrow="Why this follows Diagnosis"
        title="Which X-Ray weaknesses were confirmed by stress tests?"
        body="Diagnosis creates pre-stress hypotheses. Stress Test Lab checks which of those weaknesses show up under scenario evidence."
        badge="X-Ray bridge"
        badgeTone="blue"
      />
      <div className="mt-5 rounded-2xl border border-pmri-border/55 bg-black/10 p-4 text-sm leading-6 text-pmri-text2">
        {confirmation.note}
      </div>
      <div className="mt-6 grid gap-4 xl:grid-cols-3">
        <div>
          <div className="mb-3 flex items-center justify-between gap-3">
            <h3 className="text-sm font-semibold text-pmri-text">Confirmed by stress evidence</h3>
            <StatusBadge tone="amber">{confirmation.confirmed.length || "None"}</StatusBadge>
          </div>
          <ConfirmationList rows={confirmation.confirmed} emptyMessage="No X-Ray weakness confirmation was returned for this stress run." />
        </div>
        <div>
          <div className="mb-3 flex items-center justify-between gap-3">
            <h3 className="text-sm font-semibold text-pmri-text">Less material in stress review</h3>
            <StatusBadge tone="slate">{confirmation.lessMaterial.length || "None"}</StatusBadge>
          </div>
          <ConfirmationList rows={confirmation.lessMaterial} emptyMessage="No less-material stress findings were returned." />
        </div>
        <div>
          <div className="mb-3 flex items-center justify-between gap-3">
            <h3 className="text-sm font-semibold text-pmri-text">Insufficient data</h3>
            <StatusBadge tone="amber">{confirmation.insufficientData.length || "None"}</StatusBadge>
          </div>
          <ConfirmationList rows={confirmation.insufficientData} emptyMessage="No historical replay limitation was surfaced in this review." />
        </div>
      </div>
    </section>
  );
}
