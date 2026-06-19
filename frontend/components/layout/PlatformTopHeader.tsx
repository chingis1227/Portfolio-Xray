"use client";

import Link from "next/link";
import { usePathname } from "next/navigation";
import { buildJourneySteps } from "@/lib/journey";
import { useReviewState } from "@/lib/reviewState";

type RouteMeta = {
  title: string;
  eyebrow: string;
};

type HeaderCta = {
  label: string;
  href?: string;
  disabled?: boolean;
};

type HeaderAction = HeaderCta & {
  variant: "primary" | "secondary";
};

const routeMeta: Array<{ prefix: string; meta: RouteMeta }> = [
  { prefix: "/workspace", meta: { eyebrow: "Account home", title: "Workspace" } },
  { prefix: "/portfolio-input", meta: { eyebrow: "Step 01 / Portfolio", title: "Define current portfolio" } },
  { prefix: "/diagnosis", meta: { eyebrow: "Step 02 / Diagnosis", title: "Portfolio Diagnosis" } },
  { prefix: "/evidence", meta: { eyebrow: "Step 03 / Stress Lab", title: "Stress Test Lab" } },
  { prefix: "/client-fit", meta: { eyebrow: "Step 04 / Client Fit", title: "Client Fit Check" } },
  { prefix: "/hypothesis", meta: { eyebrow: "Step 05 / Hypothesis", title: "Diagnostic Test" } },
  { prefix: "/comparison", meta: { eyebrow: "Step 06 / Comparison", title: "Current vs Test Candidate" } },
  { prefix: "/verdict", meta: { eyebrow: "Step 07 / Verdict", title: "Decision Verdict" } },
  { prefix: "/report", meta: { eyebrow: "Step 08 / Report", title: "Grounded Report" } },
  { prefix: "/client-profile", meta: { eyebrow: "Advanced / Client Fit", title: "Manual diagnostic context" } }
];

function routeForPath(pathname: string): RouteMeta {
  return routeMeta.find((item) => pathname === item.prefix || pathname.startsWith(`${item.prefix}/`))?.meta
    ?? { eyebrow: "Investment Decision Room", title: "Portfolio MRI" };
}

function ctaForPath({
  pathname,
  flags,
  runStatus
}: {
  pathname: string;
  flags: ReturnType<typeof useReviewState>["journeyFlags"];
  runStatus?: string;
}): HeaderCta {
  const steps = buildJourneySteps(pathname, flags);
  const activeStep = steps.find((step) => step.status === "active");
  const nextAvailableStep = activeStep ? steps.find((step) => step.index > activeStep.index && step.status !== "locked") : null;

  if (pathname.startsWith("/workspace")) return { label: "Start new review", href: "/portfolio-input" };
  if (pathname.startsWith("/portfolio-input")) {
    if (runStatus === "running") return { label: "Diagnosis running", disabled: true };
    return { label: "Run diagnosis below", disabled: true };
  }
  if (pathname.startsWith("/diagnosis")) {
    return flags.diagnosisGenerated
      ? { label: "Review diagnosis below", disabled: true }
      : { label: "Complete input", href: "/portfolio-input" };
  }
  if (pathname.startsWith("/evidence")) {
    return flags.evidenceGenerated
      ? { label: "Check Client Fit", href: "/client-fit" }
      : { label: "Open Diagnosis", href: "/diagnosis" };
  }
  if (pathname.startsWith("/client-fit")) {
    return flags.clientFitReady
      ? { label: "Open Hypothesis", href: "/hypothesis" }
      : { label: "Review evidence first", href: "/evidence" };
  }
  if (pathname.startsWith("/hypothesis")) {
    return flags.candidateReady
      ? { label: "Compare test candidate", href: "/comparison" }
      : { label: "Generate test candidate below", disabled: true };
  }
  if (pathname.startsWith("/comparison")) {
    return flags.comparisonReady
      ? { label: "Open Verdict", href: "/verdict" }
      : { label: "Run comparison below", disabled: true };
  }
  if (pathname.startsWith("/verdict")) {
    return flags.verdictReady
      ? { label: "Open Report", href: "/report" }
      : { label: "Generate verdict below", disabled: true };
  }
  if (pathname.startsWith("/report")) return { label: "Back to Workspace", href: "/workspace" };
  if (pathname.startsWith("/client-profile")) return { label: "Return to Portfolio", href: "/portfolio-input" };
  return nextAvailableStep ? { label: `Continue to ${nextAvailableStep.shortLabel}`, href: nextAvailableStep.href } : { label: "Open Workspace", href: "/workspace" };
}

function secondaryActionsForPath(pathname: string): HeaderAction[] {
  return [];
}

function HeaderLinkAction({ action }: { action: HeaderAction }) {
  const baseClass = "pmri-focus rounded-full px-4 py-2 text-xs font-semibold transition";
  const secondaryClass = "border border-white/10 bg-white/[0.026] text-pmri-text2 hover:border-pmri-blue/35 hover:bg-white/[0.045] hover:text-pmri-text";
  const primaryClass = "pmri-primary-action";

  if (action.disabled || !action.href) {
    return (
      <span className={`${baseClass} border border-white/[0.08] bg-white/[0.022] text-pmri-muted`}>
        {action.label}
      </span>
    );
  }

  return (
    <Link
      href={action.href}
      className={`${baseClass} ${action.variant === "primary" ? primaryClass : secondaryClass}`}
    >
      {action.label}
    </Link>
  );
}

export function PlatformTopHeader() {
  const pathname = usePathname();
  const { activeReview, journeyFlags } = useReviewState();
  const meta = routeForPath(pathname);
  const cta = ctaForPath({ pathname, flags: journeyFlags, runStatus: activeReview?.runStatus });
  const actions: HeaderAction[] = [
    ...secondaryActionsForPath(pathname),
    { ...cta, variant: "primary" }
  ];

  return (
    <header className="sticky top-0 z-30 border-b border-white/[0.045] bg-[#050608]/[0.82] shadow-[0_18px_52px_rgba(0,0,0,0.26)] backdrop-blur-2xl">
      <div className="mx-auto flex w-full max-w-[1220px] flex-col gap-2.5 px-4 py-3 md:px-6 lg:px-8 xl:px-0">
        <div className="flex flex-col gap-3 lg:flex-row lg:items-center lg:justify-between">
          <div className="min-w-0">
            <p className="text-[0.68rem] font-medium tracking-[0.08em] text-pmri-muted">
              Portfolio MRI / {meta.eyebrow}
            </p>
            <h1 className="mt-1.5 text-2xl font-semibold leading-tight tracking-[-0.045em] text-pmri-text [text-wrap:wrap] md:text-[2rem]">
              {meta.title}
            </h1>
          </div>

          <div className="flex flex-wrap items-center gap-2">
            {actions.map((action) => (
              <HeaderLinkAction key={`${action.variant}-${action.label}`} action={action} />
            ))}
          </div>
        </div>
      </div>
    </header>
  );
}
