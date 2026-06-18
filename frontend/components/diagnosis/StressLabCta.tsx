import { ButtonLink } from "@/components/ui/Button";
import { Surface } from "@/components/ui/Surface";
import type { DiagnosisDisplayModel } from "@/components/diagnosis/diagnosisPresentation";

export function StressLabCta({ model }: { model: DiagnosisDisplayModel }) {
  return (
    <Surface as="section" tone="glass" radius="3xl" padding="md" className="flex flex-col gap-4 md:flex-row md:items-center md:justify-between">
      <div className="max-w-3xl">
        <p className="pmri-type-meta text-pmri-blueSoft">Next safe action</p>
        <h2 className="mt-2 text-xl font-semibold tracking-[-0.035em] text-pmri-text">Review Stress Lab before testing any candidate.</h2>
        <p className="mt-2 text-sm leading-6 text-pmri-text2">{model.nextStep}</p>
      </div>
      <ButtonLink href="/evidence" variant="primary" size="lg" className="shrink-0">
        Open Stress Lab
      </ButtonLink>
    </Surface>
  );
}
