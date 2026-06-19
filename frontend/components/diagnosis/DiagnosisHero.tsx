import type { DiagnosisDisplayModel } from "@/components/diagnosis/diagnosisPresentation";
import { GlassPanel } from "@/components/ui/Surface";

export function DiagnosisHero({ model }: { model: DiagnosisDisplayModel }) {
  return (
    <GlassPanel className="pmri-case-hero px-5 py-5 md:px-7 md:py-6">
      <div className="absolute -right-16 -top-24 h-64 w-64 rounded-full bg-pmri-blue/[0.06] blur-3xl" aria-hidden="true" />
      <div className="absolute -bottom-24 left-8 h-56 w-56 rounded-full bg-white/[0.026] blur-3xl" aria-hidden="true" />
      <div className="relative">
        <div>
          <p className="pmri-type-meta text-pmri-blueSoft">Step 02 / Portfolio Diagnosis</p>
          <h1 className="mt-3 max-w-[58rem] text-[clamp(1.72rem,3.1vw,3rem)] font-semibold leading-[1.02] tracking-[-0.055em] text-pmri-text [text-wrap:wrap]">
            {model.mainFinding}
          </h1>
          <p className="mt-3 max-w-[66rem] text-[0.95rem] leading-7 text-pmri-text2 [text-wrap:wrap] md:text-base">
            {model.whyItMatters}
          </p>
        </div>
      </div>
    </GlassPanel>
  );
}
