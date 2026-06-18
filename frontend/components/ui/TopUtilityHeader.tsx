import type { ReactNode } from "react";
import { StatusBadge } from "@/components/ui/StatusBadge";
import type { StatusTone } from "@/lib/types";

type TopUtilityHeaderItem = {
  label: ReactNode;
  value: ReactNode;
  tone?: StatusTone;
};

type TopUtilityHeaderProps = {
  eyebrow: ReactNode;
  title: ReactNode;
  items?: TopUtilityHeaderItem[];
};

export function TopUtilityHeader({ eyebrow, title, items = [] }: TopUtilityHeaderProps) {
  return (
    <section className="rounded-2xl border border-white/[0.055] bg-black/[0.18] px-4 py-3 shadow-[inset_0_1px_0_rgba(255,255,255,0.035)] backdrop-blur-xl">
      <div className="flex flex-col gap-3 md:flex-row md:items-center md:justify-between">
        <div className="min-w-0">
          <p className="pmri-type-meta text-pmri-blueSoft">{eyebrow}</p>
          <p className="mt-1 truncate text-sm font-semibold tracking-[-0.018em] text-pmri-text">{title}</p>
        </div>
        {items.length ? (
          <div className="flex flex-wrap gap-2">
            {items.map((item, index) => (
              <StatusBadge key={`${String(item.label)}-${index}`} tone={item.tone ?? "slate"}>
                {item.label}: {item.value}
              </StatusBadge>
            ))}
          </div>
        ) : null}
      </div>
    </section>
  );
}
