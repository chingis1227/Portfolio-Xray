import type { ReactNode } from "react";

type SectionHeaderProps = {
  eyebrow?: ReactNode;
  title: ReactNode;
  description?: ReactNode;
  actions?: ReactNode;
  className?: string;
};

export function SectionHeader({ eyebrow, title, description, actions, className }: SectionHeaderProps) {
  return (
    <div className={["flex flex-col gap-3 md:flex-row md:items-start md:justify-between", className].filter(Boolean).join(" ")}>
      <div className="max-w-3xl">
        {eyebrow ? <p className="pmri-type-meta text-pmri-muted">{eyebrow}</p> : null}
        <h2 className="pmri-type-section-title mt-2 text-pmri-text">{title}</h2>
        {description ? <p className="mt-2 text-sm leading-6 text-pmri-text2">{description}</p> : null}
      </div>
      {actions ? <div className="flex shrink-0 flex-wrap gap-2">{actions}</div> : null}
    </div>
  );
}
