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
      return "border-pmri-blue/60 bg-pmri-blue/12 text-pmri-text shadow-[0_0_0_1px_rgba(59,130,246,0.08)]";
    case "completed":
      return "border-transparent text-pmri-text2 hover:border-pmri-border hover:bg-white/5";
    case "available":
      return "border-transparent text-pmri-muted hover:border-pmri-border hover:bg-white/5";
    case "locked":
      return "cursor-not-allowed border-transparent text-pmri-muted/45 opacity-75";
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

function statusLabel(status: JourneyStepStatus) {
  switch (status) {
    case "active":
      return "Active";
    case "completed":
      return "Done";
    case "available":
      return "Open";
    case "locked":
      return "Locked";
  }
}

export function Sidebar() {
  const pathname = usePathname();
  const { journeyFlags } = useReviewState();
  const steps = buildJourneySteps(pathname, journeyFlags);
  const [lockMessage, setLockMessage] = useState<string | null>(null);

  return (
    <aside className="hidden min-h-screen w-64 shrink-0 border-r border-pmri-border/70 bg-pmri-secondary/88 px-5 py-6 shadow-[18px_0_80px_rgba(0,0,0,0.18)] lg:flex lg:flex-col">
      <div>
        <p className="text-lg font-semibold tracking-tight text-pmri-gold">Portfolio MRI</p>
        <p className="mt-1 text-xs text-pmri-muted">Investment Decision Room</p>
        <div className="mt-4 rounded-2xl border border-pmri-gold/25 bg-pmri-gold/10 p-3">
          <p className="text-[10px] font-semibold uppercase tracking-[0.16em] text-pmri-gold">Operating mode</p>
          <p className="mt-1 text-xs leading-5 text-pmri-text2">Current portfolio first. Candidate tests are diagnostic, not orders.</p>
        </div>
      </div>

      {lockMessage ? (
        <div className="mt-6 rounded-2xl border border-pmri-amber/30 bg-pmri-amber/10 px-3 py-3 text-xs leading-5 text-pmri-text2" role="status">
          {lockMessage}
        </div>
      ) : null}

      <nav className="mt-8 space-y-1" aria-label="Portfolio MRI gated journey rail">
        {steps.map((step) => {
          const content = (
            <>
              <span className="flex min-w-0 items-center gap-3">
                <span className={`h-2 w-2 rounded-full ${dotClasses(step.status)}`} />
                <span className="truncate">{step.shortLabel}</span>
              </span>
              <span className="flex items-center gap-2">
                <span className="hidden text-[10px] uppercase tracking-[0.12em] text-pmri-muted/80 xl:inline">{statusLabel(step.status)}</span>
                {step.status === "locked" ? <span aria-hidden="true" className="text-[10px] font-semibold uppercase tracking-[0.12em] text-pmri-muted/55">Lock</span> : null}
                <span className="font-mono text-[11px] text-pmri-muted">0{step.index + 1}</span>
              </span>
            </>
          );

          const className = `pmri-focus group flex w-full items-center justify-between rounded-xl border px-3 py-3 text-left text-sm transition ${statusClasses(step.status)}`;

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
