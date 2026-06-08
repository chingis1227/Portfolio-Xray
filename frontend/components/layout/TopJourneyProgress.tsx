"use client";

import { usePathname } from "next/navigation";
import { buildJourneySteps } from "@/lib/journey";
import { useReviewState } from "@/lib/reviewState";
import type { JourneyStepStatus } from "@/lib/types";

function pillClasses(status: JourneyStepStatus) {
  switch (status) {
    case "active":
      return "border-pmri-blue/70 bg-pmri-blue/18 text-pmri-blueSoft";
    case "completed":
      return "border-pmri-positive/25 bg-transparent text-pmri-positive/90";
    case "available":
      return "border-pmri-border/60 bg-transparent text-pmri-text2";
    case "locked":
      return "border-pmri-border/35 bg-transparent text-pmri-muted/45";
  }
}

function connectorClasses(status: JourneyStepStatus) {
  return status === "completed" ? "bg-pmri-positive/45" : "bg-pmri-border/45";
}

export function TopJourneyProgress() {
  const pathname = usePathname();
  const { journeyFlags } = useReviewState();
  const steps = buildJourneySteps(pathname, journeyFlags);
  const completedCount = steps.filter((step) => step.status === "completed").length;
  const activeStep = steps.find((step) => step.status === "active");

  return (
    <div className="pmri-glass-rail sticky top-0 z-20 border-b border-pmri-border/45 px-4 py-2.5 backdrop-blur-xl lg:px-8">
      <div className="mx-auto flex max-w-[1440px] items-center gap-3 overflow-x-auto">
        <span className="shrink-0 rounded-full border border-pmri-gold/30 bg-pmri-gold/10 px-3 py-1 text-[11px] font-semibold uppercase tracking-[0.18em] text-pmri-gold">
          {completedCount}/{steps.length} sealed
        </span>
        <span className="shrink-0 text-[11px] font-semibold uppercase tracking-[0.18em] text-pmri-muted">
          Now: {activeStep?.shortLabel ?? "Workflow"}
        </span>
        <ol className="flex min-w-max items-center gap-1.5" aria-label="Gated investment decision workflow progress">
          {steps.map((step, index) => (
            <li key={step.id} className="flex items-center gap-1.5">
              <span
                className={`rounded-full border px-2.5 py-0.5 text-[11px] font-medium shadow-sm transition ${pillClasses(step.status)}`}
                title={step.status === "locked" ? step.lockReason : `${step.shortLabel}: ${step.status}`}
              >
                {step.status === "locked" ? "Lock / " : step.status === "completed" ? "Done / " : ""}{step.shortLabel}
              </span>
              {index < steps.length - 1 ? <span className={`h-px w-4 ${connectorClasses(step.status)}`} aria-hidden="true" /> : null}
            </li>
          ))}
        </ol>
      </div>
    </div>
  );
}
