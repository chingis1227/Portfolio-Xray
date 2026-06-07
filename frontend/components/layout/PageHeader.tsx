import type { ReactNode } from "react";

type PageHeaderProps = {
  kicker: string;
  title: string;
  description: string;
  children?: ReactNode;
};

export function PageHeader({ kicker, title, description, children }: PageHeaderProps) {
  return (
    <header className="mb-8 flex flex-col gap-5 border-b border-pmri-border/70 pb-6 lg:flex-row lg:items-end lg:justify-between">
      <div>
        <p className="text-xs font-semibold uppercase tracking-[0.18em] text-pmri-blueSoft">{kicker}</p>
        <h1 className="mt-3 text-3xl font-semibold tracking-[-0.02em] text-pmri-text md:text-4xl">{title}</h1>
        <p className="mt-3 max-w-3xl text-sm leading-6 text-pmri-text2 md:text-base">{description}</p>
      </div>
      {children ? <div className="shrink-0">{children}</div> : null}
    </header>
  );
}
