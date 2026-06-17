import type { ReactNode } from "react";

type PageHeaderProps = {
  kicker: string;
  title: string;
  description: string;
  children?: ReactNode;
};

export function PageHeader({ kicker, title, description, children }: PageHeaderProps) {
  return (
    <header className="relative mb-7 overflow-hidden rounded-[1.75rem] border border-pmri-border/45 bg-pmri-secondary/55 p-5 shadow-decision backdrop-blur md:p-6">
      <div className="pointer-events-none absolute inset-0 bg-[radial-gradient(circle_at_90%_16%,rgba(168,189,211,0.055),transparent_30%)]" />
      <div className="relative flex flex-col gap-4 lg:flex-row lg:items-end lg:justify-between">
        <div>
          <div className="h-px w-40 pmri-kicker-rule" aria-hidden="true" />
          <p className="pmri-label mt-3 text-pmri-blueSoft">{kicker}</p>
          <h1 className="pmri-heading-hero mt-3 max-w-5xl text-pmri-text">{title}</h1>
          <p className="pmri-body-copy mt-4 max-w-3xl md:text-base">{description}</p>
        </div>
        {children ? <div className="shrink-0">{children}</div> : null}
      </div>
    </header>
  );
}
