"use client";

import { usePathname } from "next/navigation";
import { buildJourneySteps } from "@/lib/journey";
import { useReviewState } from "@/lib/reviewState";
import type { JourneyStepStatus } from "@/lib/types";

function pillClasses(status: JourneyStepStatus) {
  switch (status) {
    case "active":
      return "border-pmri-blue/22 bg-pmri-blue/[0.055] text-pmri-text";
    case "completed":
      return "border-transparent bg-transparent text-pmri-text2";
    case "available":
      return "border-transparent bg-transparent text-pmri-muted";
    case "locked":
      return "border-transparent bg-transparent text-pmri-muted/38";
  }
}

function connectorClasses(status: JourneyStepStatus) {
  return status === "completed" ? "bg-pmri-text2/35" : "bg-pmri-border/35";
}

export function TopJourneyProgress() {
  const pathname = usePathname();
  const { journeyFlags } = useReviewState();
  const steps = buildJourneySteps(pathname, journeyFlags);
  const routeStep = steps.find((step) => pathname.startsWith(step.href));
  const isWorkspace = pathname.startsWith("/workspace");
  const completedCount = steps.filter((step) => step.status === "completed").length;
  const displayStepNumber = routeStep ? routeStep.index + 1 : Math.min(completedCount + 1, steps.length);
  const currentLabel = isWorkspace ? "Workspace" : routeStep?.shortLabel ?? "Workflow";

  return (
    <div className="pmri-glass-rail sticky top-0 z-20 border-b border-pmri-border/35 px-4 py-2.5 backdrop-blur-xl lg:px-8">
      <div className="mx-auto flex max-w-[1440px] items-center gap-3 overflow-x-auto">
        <span className="shrink-0 rounded-full border border-pmri-border/45 bg-white/[0.02] px-3 py-1.5 text-xs font-medium tracking-[-0.005em] text-pmri-text2">
          {isWorkspace ? "Account home" : `Step ${displayStepNumber} of ${steps.length}`}
        </span>
        <span className="shrink-0 text-xs font-normal tracking-[-0.005em] text-pmri-muted">
          Now: {currentLabel}
        </span>
        <ol className="flex min-w-max items-center gap-1.5" aria-label="Gated investment decision workflow progress">
          {steps.map((step, index) => (
            <li key={step.id} className="flex items-center gap-1.5">
              <span
                className={`rounded-full border px-2.5 py-1 text-xs font-medium tracking-[-0.01em] transition ${pillClasses(step.status)}`}
                title={step.status === "locked" ? step.lockReason : `${step.shortLabel}: ${step.status}`}
              >
                {step.shortLabel}
              </span>
              {index < steps.length - 1 ? <span className={`h-px w-4 ${connectorClasses(step.status)}`} aria-hidden="true" /> : null}
            </li>
          ))}
        </ol>
      </div>
    </div>
  );
}
