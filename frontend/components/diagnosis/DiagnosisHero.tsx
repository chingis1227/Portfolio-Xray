import type { DiagnosisDisplayModel } from "@/components/diagnosis/diagnosisPresentation";
import { StatusBadge } from "@/components/ui/StatusBadge";
import { GlassPanel } from "@/components/ui/Surface";

export function DiagnosisHero({ model }: { model: DiagnosisDisplayModel }) {
  return (
    <GlassPanel className="pmri-case-hero px-5 py-5 md:px-7 md:py-6">
      <div className="absolute -right-16 -top-24 h-64 w-64 rounded-full bg-pmri-blue/[0.06] blur-3xl" aria-hidden="true" />
      <div className="absolute -bottom-24 left-8 h-56 w-56 rounded-full bg-white/[0.026] blur-3xl" aria-hidden="true" />
      <div className="relative grid gap-5 lg:grid-cols-[1fr_auto] lg:items-start">
        <div>
          <div className="flex flex-wrap items-center gap-2">
            <p className="pmri-type-meta text-pmri-blueSoft">Step 02 of 8 · Portfolio Diagnosis</p>
            <StatusBadge tone={model.dataCoverageTone}>Evidence {model.dataCoverage}</StatusBadge>
          </div>
          <h1 className="mt-3 max-w-4xl text-[clamp(1.72rem,3.1vw,3rem)] font-semibold leading-[1.02] tracking-[-0.055em] text-pmri-text">
            {model.mainFinding}
          </h1>
          <p className="mt-3 max-w-3xl text-[0.95rem] leading-7 text-pmri-text2 md:text-base">
            {model.whyItMatters}
          </p>
        </div>
        <aside className="max-w-sm rounded-2xl border border-white/[0.07] bg-black/[0.18] p-4">
          <p className="pmri-type-meta text-pmri-muted">Boundary</p>
          <p className="mt-2 text-sm leading-6 text-pmri-text2">{model.boundaryNote}</p>
        </aside>
      </div>
    </GlassPanel>
  );
}