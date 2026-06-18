import type { ReactNode } from "react";
import type { StatusTone } from "@/lib/types";

export type CaseFileCard = {
  eyebrow: string;
  title: string;
  value?: ReactNode;
  description: ReactNode;
  tone?: StatusTone;
};

const neutralCardClass = "border-pmri-border/55 bg-white/[0.022]";

const toneCardClass: Record<StatusTone, string> = {
  blue: "border-pmri-blue/24 bg-pmri-blue/[0.04]",
  gold: neutralCardClass,
  green: neutralCardClass,
  amber: "border-pmri-amber/28 bg-pmri-amber/[0.045]",
  red: "border-pmri-risk/28 bg-pmri-risk/[0.045]",
  slate: neutralCardClass
};

const gridColumnClass: Record<2 | 3 | 4, string> = {
  2: "lg:grid-cols-2",
  3: "lg:grid-cols-3",
  4: "lg:grid-cols-4"
};

function caseFileCardKey(card: CaseFileCard, index: number) {
  return `${index}-${card.eyebrow}-${card.title}`;
}

export function CaseFileTopCards({
  cards,
  columns = 3
}: {
  cards: CaseFileCard[];
  columns?: 2 | 3 | 4;
}) {
  const visibleCards = cards.slice(0, columns);

  return (
    <section className={`grid gap-4 ${gridColumnClass[columns]}`}>
      {visibleCards.map((card, index) => (
        <article key={caseFileCardKey(card, index)} className={`rounded-3xl border p-5 ${toneCardClass[card.tone ?? "slate"]}`}>
          <p className="pmri-label text-pmri-muted">{card.eyebrow}</p>
          <h2 className="pmri-heading-section mt-2 text-xl text-pmri-text">{card.title}</h2>
          {card.value ? <p className="data-figure mt-3 text-lg text-pmri-text2">{card.value}</p> : null}
          <p className="mt-3 text-sm leading-6 text-pmri-text2">{card.description}</p>
        </article>
      ))}
    </section>
  );
}

export function NextDecisionPanel({
  title,
  description,
  action
}: {
  title: string;
  description: ReactNode;
  action?: ReactNode;
}) {
  return (
    <section className="rounded-3xl border border-pmri-border/55 bg-white/[0.022] p-5 md:p-6">
      <p className="pmri-label text-pmri-blueSoft">Next decision</p>
      <div className="mt-2 flex flex-col gap-4 md:flex-row md:items-center md:justify-between">
        <div>
          <h2 className="pmri-heading-section text-xl text-pmri-text">{title}</h2>
          <p className="mt-2 max-w-3xl text-sm leading-6 text-pmri-text2">{description}</p>
        </div>
        {action ? <div className="shrink-0">{action}</div> : null}
      </div>
    </section>
  );
}
