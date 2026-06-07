"use client";

import Link from "next/link";
import { usePathname } from "next/navigation";
import { getStepIndex, journeySteps } from "@/lib/journey";
import { StatusBadge } from "@/components/ui/StatusBadge";

export function Sidebar() {
  const pathname = usePathname();
  const currentIndex = getStepIndex(pathname);

  return (
    <aside className="hidden min-h-screen w-64 shrink-0 border-r border-pmri-border/70 bg-pmri-secondary/88 px-5 py-6 lg:flex lg:flex-col">
      <div>
        <p className="text-lg font-semibold tracking-tight text-pmri-gold">Portfolio MRI</p>
        <p className="mt-1 text-xs text-pmri-muted">Investment Decision Room</p>
      </div>

      <nav className="mt-10 space-y-1" aria-label="Portfolio MRI stages">
        {journeySteps.map((step, index) => {
          const active = index === currentIndex;
          const complete = index < currentIndex;
          return (
            <Link
              key={step.id}
              href={step.href}
              className={`pmri-focus group flex items-center justify-between rounded-xl border px-3 py-3 text-sm transition ${
                active
                  ? "border-pmri-blue/60 bg-pmri-blue/12 text-pmri-text"
                  : complete
                    ? "border-transparent text-pmri-text2 hover:border-pmri-border hover:bg-white/5"
                    : "border-transparent text-pmri-muted hover:border-pmri-border hover:bg-white/5"
              }`}
            >
              <span className="flex items-center gap-3">
                <span className={`h-2 w-2 rounded-full ${active ? "bg-pmri-blue" : complete ? "bg-pmri-positive" : "bg-pmri-border"}`} />
                {step.shortLabel}
              </span>
              <span className="font-mono text-[11px] text-pmri-muted">0{index + 1}</span>
            </Link>
          );
        })}
      </nav>

      <div className="mt-auto rounded-2xl border border-pmri-border bg-white/[0.03] p-4">
        <StatusBadge tone="gold">Review preview</StatusBadge>
        <p className="mt-3 text-sm leading-5 text-pmri-text2">Sample portfolio review. Decision-support only; not a trading instruction.</p>
      </div>
    </aside>
  );
}
