"use client";

import type { ReactNode } from "react";
import Link from "next/link";
import { usePathname } from "next/navigation";
import { buildJourneySteps } from "@/lib/journey";
import { useReviewState } from "@/lib/reviewState";
import { PageHeader } from "./PageHeader";
import { StatusBadge } from "@/components/ui/StatusBadge";

type JourneyGateProps = {
  stepId: string;
  children: ReactNode;
};

export function JourneyGate({ stepId, children }: JourneyGateProps) {
  const pathname = usePathname();
  const { journeyFlags } = useReviewState();
  const step = buildJourneySteps(pathname, journeyFlags).find((item) => item.id === stepId);

  if (!step || step.status !== "locked") {
    return <>{children}</>;
  }

  return (
    <div>
      <PageHeader
        kicker={`Step 0${step.index + 1} / Locked`}
        title={`${step.shortLabel} is not available yet`}
        description="Portfolio MRI opens each stage only after the previous investment evidence has been created."
      >
        <StatusBadge tone="amber">Locked workflow stage</StatusBadge>
      </PageHeader>
      <section className="pmri-card rounded-3xl p-6">
        <div className="flex flex-col gap-4 md:flex-row md:items-center md:justify-between">
          <div>
            <p className="text-xs font-semibold uppercase tracking-[0.16em] text-pmri-muted">Required first</p>
            <p className="mt-2 text-lg font-semibold text-pmri-text">{step.lockReason}</p>
            <p className="mt-2 max-w-2xl text-sm leading-6 text-pmri-muted">
              Locked stages are intentionally muted and do not show downstream demo content before the workflow has enough state.
            </p>
          </div>
          <Link
            href="/portfolio-input"
            className="pmri-focus rounded-full border border-pmri-blue/50 bg-pmri-blue px-5 py-2.5 text-sm font-semibold text-white shadow-decision transition hover:bg-pmri-blueSoft"
          >
            Go to Portfolio Input
          </Link>
        </div>
      </section>
    </div>
  );
}
