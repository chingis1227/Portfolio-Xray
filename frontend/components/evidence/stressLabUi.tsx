import type { ReactNode } from "react";
import { StatusBadge } from "@/components/ui/StatusBadge";
import type { StatusTone } from "@/lib/types";

type SectionHeaderProps = {
  eyebrow?: string;
  title: string;
  body?: string;
  badge?: string;
  badgeTone?: StatusTone;
};

export function StressSectionHeader({ eyebrow, title, body, badge, badgeTone = "slate" }: SectionHeaderProps) {
  return (
    <div className="flex flex-col gap-3 md:flex-row md:items-start md:justify-between">
      <div className="max-w-3xl">
        {eyebrow ? <p className="pmri-label">{eyebrow}</p> : null}
        <h2 className="pmri-heading-section mt-1 text-2xl text-pmri-text">{title}</h2>
        {body ? <p className="mt-2 text-sm leading-6 text-pmri-text2">{body}</p> : null}
      </div>
      {badge ? <StatusBadge tone={badgeTone}>{badge}</StatusBadge> : null}
    </div>
  );
}

export function HelpHint({ label, text }: { label: string; text: string }) {
  return (
    <span
      tabIndex={0}
      className="pmri-info-hint pmri-focus inline-flex cursor-help rounded-full border border-pmri-border/70 bg-white/[0.025] px-2 py-1 text-[0.68rem] font-medium text-pmri-muted"
      data-tooltip={text}
      aria-label={`${label}: ${text}`}
    >
      {label}
    </span>
  );
}

export function EmptyPanel({ children }: { children: ReactNode }) {
  return (
    <div className="rounded-2xl border border-dashed border-pmri-border/70 bg-black/10 p-4 text-sm leading-6 text-pmri-muted">
      {children}
    </div>
  );
}
