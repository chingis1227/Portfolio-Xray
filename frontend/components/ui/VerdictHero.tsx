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
    <section className="pmri-case-hero px-5 py-5 md:px-7 md:py-6">
      <div className="absolute -right-14 -top-20 h-64 w-64 rounded-full bg-pmri-blue/[0.055] blur-3xl" aria-hidden="true" />
      <div className="absolute -bottom-20 left-12 h-56 w-56 rounded-full bg-white/[0.028] blur-3xl" aria-hidden="true" />
      <div className="relative">
        <p className="text-[0.68rem] font-medium tracking-[0.08em] text-pmri-blueSoft">
          {stepContext}
        </p>
        <h1 className="mt-3 max-w-4xl text-[clamp(2rem,3.9vw,3.55rem)] font-semibold leading-[1.02] tracking-[-0.055em] text-pmri-text">
          {headline}
        </h1>
        <p className="mt-4 max-w-3xl text-[0.98rem] leading-7 text-pmri-text2 md:text-[1.05rem]">
          {interpretation}
        </p>

        {visibleFacts.length ? (
          <div className="mt-5 flex flex-wrap gap-x-4 gap-y-2 border-t border-white/[0.06] pt-4 text-sm text-pmri-muted">
            {visibleFacts.map((fact, index) => (
              <span key={`${fact.label ?? "fact"}-${index}`} className="flex max-w-[22rem] items-baseline gap-2">
                {fact.label ? <span className="text-pmri-text2">{fact.label}</span> : null}
                <span className="text-pmri-muted">{fact.value}</span>
              </span>
            ))}
          </div>
        ) : null}

        {actions ? <div className="mt-5 flex flex-wrap gap-3">{actions}</div> : null}
      </div>
    </section>
  );
}
