import type { ReactNode } from "react";

type VerdictHeroFact = {
  label?: string;
  value: ReactNode;
};

type VerdictHeroProps = {
  stepContext: string;
  headline: string;
  interpretation: string;
  facts?: VerdictHeroFact[];
  actions?: ReactNode;
};

export function VerdictHero({
  stepContext,
  headline,
  interpretation,
  facts = [],
  actions
}: VerdictHeroProps) {
  const visibleFacts = facts.filter((fact) => String(fact.label ?? "").trim().toLowerCase() !== "boundary").slice(0, 3);

  return (
    <section className="pmri-card pmri-animated-border-panel relative overflow-hidden rounded-3xl p-6 md:p-8">
      <div className="absolute -right-12 -top-16 h-56 w-56 rounded-full bg-pmri-blue/[0.045] blur-3xl" aria-hidden="true" />
      <div className="absolute bottom-0 left-0 h-px w-full bg-gradient-to-r from-transparent via-pmri-blueSoft/20 to-transparent" aria-hidden="true" />
      <div className="relative">
        <p className="pmri-type-meta text-pmri-blueSoft">{stepContext}</p>
        <h1 className="pmri-type-page-title mt-4 max-w-5xl text-pmri-text">
          {headline}
        </h1>
        <p className="pmri-type-body mt-5 max-w-3xl md:text-lg">
          {interpretation}
        </p>

        {visibleFacts.length ? (
          <div className="mt-7 grid gap-3 md:grid-cols-3">
            {visibleFacts.map((fact, index) => (
              <div key={`${fact.label ?? "fact"}-${index}`} className="rounded-2xl border border-pmri-border/45 bg-white/[0.022] p-4">
                {fact.label ? <p className="pmri-type-meta text-pmri-text2">{fact.label}</p> : null}
                <p className="mt-2 text-sm leading-6 text-pmri-text2">{fact.value}</p>
              </div>
            ))}
          </div>
        ) : null}


        {actions ? <div className="mt-6 flex flex-wrap gap-3">{actions}</div> : null}
      </div>
    </section>
  );
}
