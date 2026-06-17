"use client";

import { usePathname } from "next/navigation";
import { buildJourneySteps } from "@/lib/journey";
import { useReviewState } from "@/lib/reviewState";

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
      <div className="mx-auto flex max-w-[1440px] items-center gap-3">
        <span className="shrink-0 rounded-full border border-pmri-border/45 bg-white/[0.02] px-3 py-1.5 text-xs font-medium tracking-[-0.005em] text-pmri-text2">
          {isWorkspace ? "Account home" : `Step ${displayStepNumber} of ${steps.length}`}
        </span>
        <span className="shrink-0 text-xs font-normal tracking-[-0.005em] text-pmri-muted">
          Now: {currentLabel}
        </span>
      </div>
    </div>
  );
}
