"use client";

import Link from "next/link";
import { usePathname } from "next/navigation";
import { useState } from "react";
import { buildJourneySteps } from "@/lib/journey";
import { useReviewState } from "@/lib/reviewState";
import type { JourneyStepStatus } from "@/lib/types";

function statusClasses(status: JourneyStepStatus) {
  switch (status) {
    case "active":
      return "border-pmri-blue/22 bg-pmri-blue/[0.055] text-pmri-text shadow-[inset_2px_0_0_rgba(168,189,211,0.42)]";
    case "completed":
      return "border-transparent text-pmri-text2 hover:border-pmri-border/70 hover:bg-white/[0.035]";
    case "available":
      return "border-transparent text-pmri-muted hover:border-pmri-border/60 hover:bg-white/[0.03]";
    case "locked":
      return "cursor-not-allowed border-transparent text-pmri-muted/40 opacity-70";
  }
}

function dotClasses(status: JourneyStepStatus) {
  switch (status) {
    case "active":
      return "bg-pmri-blue";
    case "completed":
      return "bg-pmri-positive";
    case "available":
      return "bg-pmri-border";
    case "locked":
      return "bg-pmri-border/35";
  }
}

export function Sidebar() {
  const pathname = usePathname();
  const { journeyFlags } = useReviewState();
  const steps = buildJourneySteps(pathname, journeyFlags);
  const [lockMessage, setLockMessage] = useState<string | null>(null);

  return (
    <aside className="hidden min-h-screen w-64 shrink-0 border-r border-pmri-border/45 bg-pmri-secondary/88 px-5 py-6 shadow-[16px_0_64px_rgba(0,0,0,0.14)] lg:flex lg:flex-col">
      <div>
        <p className="text-lg font-semibold tracking-[-0.025em] text-pmri-text">Portfolio MRI</p>
        <p className="pmri-microcopy mt-1">Investment Decision Room</p>
        <div className="mt-5 rounded-2xl border border-pmri-border/45 bg-white/[0.02] p-4">
          <p className="pmri-label text-pmri-text2">Decision-safe workspace</p>
          <p className="mt-2 text-sm leading-6 text-pmri-muted">Current portfolio first. Candidate tests are diagnostic, not orders.</p>
        </div>
      </div>

      {lockMessage ? (
        <div className="mt-6 rounded-2xl border border-pmri-amber/30 bg-pmri-amber/10 px-3 py-3 text-xs leading-5 text-pmri-text2" role="status">
          {lockMessage}
        </div>
      ) : null}

      <nav className="mt-8 space-y-1.5" aria-label="Portfolio MRI gated journey rail">
        {steps.map((step) => {
          const content = (
            <>
              <span className="flex min-w-0 items-center gap-3">
                <span className={`h-2 w-2 rounded-full ${dotClasses(step.status)}`} />
                <span className="truncate">{step.shortLabel}</span>
              </span>
              <span className="flex items-center gap-2">
                <span className="data-figure text-[11px] text-pmri-muted/75">0{step.index + 1}</span>
              </span>
            </>
          );

          const className = `pmri-focus pmri-nav-text group flex w-full items-center justify-between rounded-2xl border px-3.5 py-3 text-left transition ${statusClasses(step.status)}`;

          return step.status === "locked" ? (
            <button
              key={step.id}
              type="button"
              className={className}
              aria-disabled="true"
              onClick={() => setLockMessage(step.lockReason)}
            >
              {content}
            </button>
          ) : (
            <Link
              key={step.id}
              href={step.href}
              className={className}
              onClick={() => setLockMessage(null)}
            >
              {content}
            </Link>
          );
        })}
      </nav>
    </aside>
  );
}
