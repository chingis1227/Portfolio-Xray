import { StatusBadge } from "@/components/ui/StatusBadge";
import type { StressLimitations, StressScenarioDetail } from "./stressLabTypes";
import { StressSectionHeader } from "./stressLabUi";

function LimitationColumn({ title, rows }: { title: string; rows: string[] }) {
  return (
    <article className="rounded-2xl border border-pmri-border/55 bg-white/[0.024] p-5">
      <h3 className="text-sm font-semibold text-pmri-text">{title}</h3>
      <ul className="mt-4 space-y-3 text-sm leading-6 text-pmri-text2">
        {rows.map((row) => (
          <li key={row} className="flex gap-2">
            <span className="mt-2 h-1.5 w-1.5 shrink-0 rounded-full bg-pmri-borderSoft" />
            <span>{row}</span>
          </li>
        ))}
      </ul>
    </article>
  );
}

export function DataLimitationsPanel({
  limitations,
  syntheticScenarios,
  historicalScenarios
}: {
  limitations: StressLimitations;
  syntheticScenarios: StressScenarioDetail[];
  historicalScenarios: StressScenarioDetail[];
}) {
  const syntheticAvailable = syntheticScenarios.filter((scenario) => scenario.availability === "available").length;
  const historicalAvailable = historicalScenarios.filter((scenario) => scenario.availability === "available").length;
  const limitedEpisodes = historicalScenarios.filter((scenario) => scenario.availability !== "available");
  const syntheticStrong = syntheticAvailable === syntheticScenarios.length;
  const historicalLimited = limitedEpisodes.length > 0;

  return (
    <section id="data-quality" className="pmri-card rounded-3xl p-5 md:p-7">
      <StressSectionHeader
        eyebrow="Data quality"
        title="Data quality"
        body="Synthetic stress coverage and historical replay coverage are separated so limitations are clear but not overstated."
      />
      <div className="mt-6 grid gap-4 lg:grid-cols-3">
        <article className="rounded-2xl border border-pmri-border/55 bg-white/[0.024] p-5">
          <div className="flex items-start justify-between gap-3">
            <h3 className="text-sm font-semibold text-pmri-text">Synthetic stress coverage</h3>
            <StatusBadge tone={syntheticStrong ? "slate" : "amber"}>{syntheticStrong ? "Coverage ready" : "Coverage limited"}</StatusBadge>
          </div>
          <p className="data-figure mt-4 text-2xl text-pmri-text">
            {syntheticAvailable} of {syntheticScenarios.length}
          </p>
          <p className="mt-2 text-sm leading-6 text-pmri-text2">
            Synthetic stress scenarios remain available as pre-candidate evidence.
          </p>
        </article>
        <article className="rounded-2xl border border-pmri-border/55 bg-white/[0.024] p-5">
          <div className="flex items-start justify-between gap-3">
            <h3 className="text-sm font-semibold text-pmri-text">Historical replay coverage</h3>
            <StatusBadge tone={historicalLimited ? "amber" : "slate"}>{historicalLimited ? "Replay limited" : "Replay ready"}</StatusBadge>
          </div>
          <p className="data-figure mt-4 text-2xl text-pmri-text">
            {historicalAvailable} of {historicalScenarios.length}
          </p>
          <p className="mt-2 text-sm leading-6 text-pmri-text2">
            {historicalLimited
              ? `Limited episodes: ${limitedEpisodes.map((scenario) => scenario.displayName).join(", ")}.`
              : "No historical replay limitation was surfaced in this review."}
          </p>
        </article>
        <article className="rounded-2xl border border-pmri-border/55 bg-black/10 p-5">
          <h3 className="text-sm font-semibold text-pmri-text">Still usable</h3>
          <p className="mt-4 text-sm leading-6 text-pmri-text2">
            Portfolio diagnosis evidence and synthetic stress scenarios remain available as supporting evidence for the next review step.
          </p>
        </article>
      </div>
      <p className="mt-5 rounded-2xl border border-pmri-border/55 bg-black/10 p-4 text-sm leading-6 text-pmri-text2">
        {limitations.headline}
      </p>
      <div className="mt-6 grid gap-4 lg:grid-cols-3">
        <LimitationColumn title="What is limited" rows={limitations.whatLimited} />
        <LimitationColumn title="Why it matters" rows={limitations.whyItMatters} />
        <LimitationColumn title="Still usable" rows={limitations.stillUsable} />
      </div>
    </section>
  );
}
