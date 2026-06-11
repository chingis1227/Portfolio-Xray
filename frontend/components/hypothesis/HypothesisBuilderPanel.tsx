import { StatusBadge } from "@/components/ui/StatusBadge";

const methodLabels: Record<string, string> = {
  equal_weight_reference_test: "Equal Weight diagnostic benchmark"
};

export function HypothesisBuilderPanel({ selectedMethod, builderStatus, boundaryNote, constraints }: { selectedMethod: string; builderStatus: string; boundaryNote: string; constraints: string[] }) {
  return (
    <aside className="pmri-card rounded-2xl p-6">
      <div className="flex items-center justify-between gap-3">
        <div>
          <p className="pmri-label">Guided test setup</p>
          <h3 className="pmri-heading-section mt-2 text-lg text-pmri-text">Choose one hypothesis to review</h3>
        </div>
        <StatusBadge tone="blue">{builderStatus}</StatusBadge>
      </div>
      <div className="mt-6 rounded-2xl border border-pmri-blue/25 bg-pmri-blue/10 p-4">
        <p className="pmri-label text-pmri-blueSoft">Hypothesis test used</p>
        <p className="mt-2 text-sm leading-6 text-pmri-text2">{methodLabels[selectedMethod] ?? "Diagnostic benchmark selected for review"}</p>
      </div>
      <p className="mt-4 rounded-xl border border-pmri-border/70 bg-white/[0.035] p-3 text-sm leading-6 text-pmri-text2">{boundaryNote}</p>
      <div className="mt-6">
        <p className="pmri-label">Guardrails before comparison</p>
        <ul className="mt-4 space-y-3 text-sm leading-6 text-pmri-text2">
          {constraints.map((constraint) => (
            <li key={constraint} className="flex gap-3">
              <span className="mt-2 h-1.5 w-1.5 shrink-0 rounded-full bg-pmri-blue" />
              <span>{constraint}</span>
            </li>
          ))}
        </ul>
      </div>
    </aside>
  );
}
