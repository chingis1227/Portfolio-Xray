import type { ReactNode } from "react";
import { StatusBadge } from "./StatusBadge";

type DecisionHeroCardProps = {
  eyebrow: string;
  title: string;
  body: string;
  status?: string;
  tone?: "blue" | "gold" | "green" | "amber" | "red" | "slate";
  children?: ReactNode;
};

export function DecisionHeroCard({ eyebrow, title, body, status, tone = "gold", children }: DecisionHeroCardProps) {
  return (
    <section className="pmri-card relative overflow-hidden rounded-2xl border-pmri-gold/25 p-6 md:p-8">
      <div className="absolute right-0 top-0 h-44 w-44 rounded-full bg-pmri-blue/10 blur-3xl" aria-hidden="true" />
      <div className="absolute bottom-0 left-8 h-px w-32 bg-pmri-gold/70" aria-hidden="true" />
      <div className="relative">
        <div className="flex flex-wrap items-center gap-3">
          <p className="text-xs font-semibold uppercase tracking-[0.16em] text-pmri-gold">{eyebrow}</p>
          {status ? <StatusBadge tone={tone}>{status}</StatusBadge> : null}
        </div>
        <h2 className="mt-4 max-w-3xl text-3xl font-semibold leading-tight tracking-[-0.02em] text-pmri-text md:text-4xl">{title}</h2>
        <p className="mt-4 max-w-3xl text-base leading-7 text-pmri-text2">{body}</p>
        {children ? <div className="mt-6">{children}</div> : null}
      </div>
    </section>
  );
}
