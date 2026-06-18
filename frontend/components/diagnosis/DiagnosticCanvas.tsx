import { MetricValue } from "@/components/ui/MetricValue";
import { SectionHeader } from "@/components/ui/SectionHeader";
import { StatusBadge } from "@/components/ui/StatusBadge";
import {
  concentrationCanvasTitle,
  concentrationFact,
  downsideFact,
  exposureCanvasTitle,
  exposureFact,
  type DiagnosisDisplayModel
} from "@/components/diagnosis/diagnosisPresentation";
import type { DiagnosisDisplayFact } from "@/lib/diagnosisDisplayModel";

function evidenceToneLabel(fact?: DiagnosisDisplayFact) {
  if (!fact) return "Not evaluated";
  if (fact.tone === "red") return "Material";
  if (fact.tone === "amber") return "Watch";
  return "Observed";
}

export function DiagnosticCanvas({ model }: { model: DiagnosisDisplayModel }) {
  const concentration = concentrationFact(model);
  const exposure = exposureFact(model);
  const downside = downsideFact(model);
  const reviewItems = [
    { label: "Worst risk to review", value: downside?.value ?? "Stress evidence", tone: downside?.tone ?? "amber" },
    { label: "Stress Lab focus", value: model.nextStep, tone: "blue" as const },
    { label: "Candidate testing", value: "Only after stress evidence is reviewed", tone: "slate" as const }
  ];
  const drivingItems = [
    {
      title: concentrationCanvasTitle(model),
      copy: concentration?.note ?? "High concentration can make a few positions drive most portfolio behavior.",
      fact: concentration
    },
    {
      title: exposureCanvasTitle(model),
      copy: exposure?.note ?? "Portfolio behavior should be read through its dominant economic exposure.",
      fact: exposure
    },
    {
      title: downside ? `Worst observed downside is ${downside.value}` : "Downside evidence should be reviewed next",
      copy: downside?.note ?? "Stress Lab should verify whether downside risk is temporary, concentrated, or structural.",
      fact: downside
    }
  ];

  return (
    <section className="pmri-diagnostic-canvas">
      <div className="grid gap-0 lg:grid-cols-[1.25fr_0.75fr]">
        <div className="p-5 md:p-6 lg:p-7">
          <SectionHeader eyebrow="Diagnostic canvas" title="What is material in the current portfolio" />
          <div className="mt-5 grid gap-3 sm:grid-cols-3">
            <MetricValue label="Primary issue" value={concentration?.value ?? "Not evaluated"} detail={evidenceToneLabel(concentration)} tone={concentration?.tone} size="sm" />
            <MetricValue label="Main exposure" value={exposure?.value ?? "Not evaluated"} detail={exposure?.detail ?? evidenceToneLabel(exposure)} tone={exposure?.tone} size="sm" />
            <MetricValue label="Downside evidence" value={downside?.value ?? "Not evaluated"} detail={evidenceToneLabel(downside)} tone={downside?.tone} size="sm" />
          </div>
          <div className="mt-5 space-y-3">
            {drivingItems.map((item, index) => (
              <article key={item.title} className="grid gap-3 border-t border-white/[0.055] pt-4 md:grid-cols-[2rem_1fr_auto] md:items-start">
                <p className="data-figure text-sm text-pmri-muted">0{index + 1}</p>
                <div>
                  <h3 className="text-base font-semibold tracking-[-0.02em] text-pmri-text">{item.title}</h3>
                  <p className="mt-1.5 text-sm leading-6 text-pmri-text2">{item.copy}</p>
                </div>
                {item.fact ? <StatusBadge tone={item.fact.tone}>{evidenceToneLabel(item.fact)}</StatusBadge> : null}
              </article>
            ))}
          </div>
        </div>
        <aside className="border-t border-white/[0.06] bg-black/[0.14] p-5 md:p-6 lg:border-l lg:border-t-0 lg:p-7">
          <SectionHeader eyebrow="Next review" title="What risk should be reviewed next" />
          <div className="mt-5 space-y-3">
            {reviewItems.map((item) => (
              <div key={item.label} className="rounded-2xl border border-white/[0.055] bg-white/[0.018] p-4">
                <div className="flex items-start justify-between gap-3">
                  <p className="pmri-type-meta text-pmri-muted">{item.label}</p>
                  <span className="mt-1 h-1.5 w-1.5 rounded-full bg-pmri-blueSoft/[0.62]" aria-hidden="true" />
                </div>
                <p className="mt-2 text-sm leading-6 text-pmri-text2">{item.value}</p>
              </div>
            ))}
          </div>
        </aside>
      </div>
    </section>
  );
}
