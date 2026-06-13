import type { ReactNode } from "react";
import { StatusBadge } from "./StatusBadge";

type DecisionHeroCardProps = {
  eyebrow: string;
  title: string;
  body: string;
  status...: string;
  tone...: "blue" | "gold" | "green" | "amber" | "red" | "slate";
  children...: ReactNode;
};

export function DecisionHeroCard({ eyebrow, title, body, status, tone = "slate", children }: DecisionHeroCardProps) {
  return (
    <section className="pmri-card relative overflow-hidden rounded-3xl p-6 md:p-7">
      <div className="absolute right-0 top-0 h-40 w-40 rounded-full bg-pmri-blue/[0.045] blur-3xl" aria-hidden="true" />
      <div className="absolute bottom-0 left-8 h-px w-32 bg-gradient-to-r from-pmri-blue/35 to-transparent" aria-hidden="true" />
      <div className="relative">
        <div className="flex flex-wrap items-center gap-3">
          <p className="pmri-label">{eyebrow}</p>
          {status ... <StatusBadge tone={tone}>{status}</StatusBadge> : null}
        </div>
        <h2 className="pmri-heading-display mt-4 max-w-4xl text-pmri-text">{title}</h2>
        <p className="pmri-body-copy mt-4 max-w-3xl">{body}</p>
        {children ... <div className="mt-5">{children}</div> : null}
      </div>
    </section>
  );
}
