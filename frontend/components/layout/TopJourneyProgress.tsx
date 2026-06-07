"use client";

import { usePathname } from "next/navigation";
import { getStepIndex, journeySteps } from "@/lib/journey";

export function TopJourneyProgress() {
  const pathname = usePathname();
  const currentIndex = getStepIndex(pathname);

  return (
    <div className="sticky top-0 z-20 border-b border-pmri-border/45 bg-pmri-bg/78 px-4 py-2.5 backdrop-blur-xl lg:px-8">
      <div className="mx-auto flex max-w-[1440px] items-center gap-3 overflow-x-auto">
        <span className="shrink-0 text-[11px] font-semibold uppercase tracking-[0.18em] text-pmri-muted">Status</span>
        <ol className="flex min-w-max items-center gap-1.5" aria-label="Top journey progress">
          {journeySteps.map((step, index) => {
            const active = index === currentIndex;
            const complete = index < currentIndex;
            return (
              <li key={step.id} className="flex items-center gap-1.5">
                <span className={`rounded-full border px-2.5 py-0.5 text-[11px] font-medium ${
                  active
                    ? "border-pmri-blue/70 bg-pmri-blue/18 text-pmri-blueSoft"
                    : complete
                      ? "border-pmri-positive/25 bg-transparent text-pmri-positive/90"
                      : "border-pmri-border/60 bg-transparent text-pmri-muted"
                }`}>
                  {step.shortLabel}
                </span>
                {index < journeySteps.length - 1 ? <span className="h-px w-4 bg-pmri-border/55" aria-hidden="true" /> : null}
              </li>
            );
          })}
        </ol>
      </div>
    </div>
  );
}
