import type { ReactNode } from "react";

type PageHeaderProps = {
  kicker: string;
  title: string;
  description: string;
  children?: ReactNode;
};

export function PageHeader({ kicker, title, description, children }: PageHeaderProps) {
  return (
    <header className="relative mb-8 overflow-hidden rounded-3xl border border-pmri-border/70 bg-pmri-secondary/45 p-5 shadow-decision backdrop-blur md:p-7">
      <div className="pointer-events-none absolute inset-0 bg-[radial-gradient(circle_at_18%_0%,rgba(212,175,55,0.13),transparent_30%),radial-gradient(circle_at_88%_18%,rgba(59,130,246,0.14),transparent_28%)]" />
      <div className="relative flex flex-col gap-5 lg:flex-row lg:items-end lg:justify-between">
        <div>
          <div className="h-px w-40 pmri-kicker-rule" aria-hidden="true" />
          <p className="mt-3 text-xs font-semibold uppercase tracking-[0.2em] text-pmri-blueSoft">{kicker}</p>
          <h1 className="mt-3 text-3xl font-semibold tracking-[-0.03em] text-pmri-text md:text-5xl">{title}</h1>
          <p className="mt-4 max-w-3xl text-sm leading-6 text-pmri-text2 md:text-base">{description}</p>
          <p className="mt-3 text-xs font-semibold uppercase tracking-[0.16em] text-pmri-gold/85">
            Evidence first · one hypothesis at a time · no trade execution
          </p>
        </div>
        {children ? <div className="shrink-0">{children}</div> : null}
      </div>
    </header>
  );
}
