"use client";

import Link from "next/link";
import { usePathname } from "next/navigation";
import { StatusBadge } from "@/components/ui/StatusBadge";
import { buildJourneySteps } from "@/lib/journey";
import { useReviewState } from "@/lib/reviewState";
import type { StatusTone } from "@/lib/types";

type RouteMeta = {
  title: string;
  eyebrow: string;
};

type HeaderCta = {
  label: string;
  href?: string;
  disabled?: boolean;
};

const routeMeta: Array<{ prefix: string; meta: RouteMeta }> = [
  { prefix: "/workspace", meta: { eyebrow: "Account home", title: "Workspace" } },
  { prefix: "/portfolio-input", meta: { eyebrow: "Step 01 / Portfolio", title: "Define current portfolio" } },
  { prefix: "/diagnosis", meta: { eyebrow: "Step 02 / Diagnosis", title: "Portfolio Diagnosis" } },
  { prefix: "/evidence", meta: { eyebrow: "Step 03 / Stress Lab", title: "Stress Test Lab" } },
  { prefix: "/client-fit", meta: { eyebrow: "Step 04 / Client Fit", title: "Client Fit Check" } },
  { prefix: "/hypothesis", meta: { eyebrow: "Step 05 / Hypothesis", title: "Candidate Launchpad" } },
  { prefix: "/comparison", meta: { eyebrow: "Step 06 / Comparison", title: "Current vs Candidate" } },
  { prefix: "/verdict", meta: { eyebrow: "Step 07 / Verdict", title: "Decision Verdict" } },
  { prefix: "/report", meta: { eyebrow: "Step 08 / Report", title: "Grounded Report" } },
  { prefix: "/client-profile", meta: { eyebrow: "Advanced / Client Fit", title: "Manual diagnostic context" } }
];

function routeForPath(pathname: string): RouteMeta {
  return routeMeta.find((item) => pathname === item.prefix || pathname.startsWith(`${item.prefix}/`))?.meta
    ?? { eyebrow: "Investment Decision Room", title: "Portfolio MRI" };
}

function normalizeStatus(value?: string | null) {
  if (!value) return "No active review";
  return value
    .replace(/[_-]+/g, " ")
    .replace(/\b\w/g, (letter) => letter.toUpperCase());
}

function reviewStatusTone(status?: string | null): StatusTone {
  const normalized = String(status ?? "").toLowerCase();
  if (normalized.includes("fail") || normalized.includes("blocked")) return "red";
  if (normalized.includes("running") || normalized.includes("pending")) return "blue";
  if (normalized.includes("draft") || normalized.includes("partial")) return "amber";
  return "slate";
}

function evidenceTone(label?: string | null): StatusTone {
  const normalized = String(label ?? "").toLowerCase();
  if (!normalized || normalized.includes("unavailable") || normalized.includes("missing")) return "slate";
  if (normalized.includes("limited") || normalized.includes("partial") || normalized.includes("insufficient")) return "amber";
  if (normalized.includes("failed") || normalized.includes("blocked")) return "red";
  return "slate";
}

function formatDateTime(value?: string | null) {
  if (!value) return "";
  const date = new Date(value);
  if (Number.isNaN(date.getTime())) return "";
  return new Intl.DateTimeFormat("en", {
    month: "short",
    day: "numeric",
    hour: "2-digit",
    minute: "2-digit"
  }).format(date);
}

function readOutputSummaryField(outputs: unknown, field: "analysis_window") {
  if (!outputs || typeof outputs !== "object" || Array.isArray(outputs)) return "";
  const summary = (outputs as Record<string, unknown>).review_summary;
  if (!summary || typeof summary !== "object" || Array.isArray(summary)) return "";
  const value = (summary as Record<string, unknown>)[field];
  return typeof value === "string" ? value : "";
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
      ? { label: "Review Stress Lab", href: "/evidence" }
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
      ? { label: "Compare candidate", href: "/comparison" }
      : { label: "Generate candidate below", disabled: true };
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

function UtilityItem({ label, value }: { label: string; value: string }) {
  return (
    <div className="min-w-0 border-l border-pmri-border/45 pl-3">
      <p className="pmri-type-meta text-pmri-muted">{label}</p>
      <p className="mt-0.5 truncate text-sm font-medium text-pmri-text2">{value}</p>
    </div>
  );
}

export function PlatformTopHeader() {
  const pathname = usePathname();
  const { activeReview, journeyFlags } = useReviewState();
  const meta = routeForPath(pathname);
  const portfolioName = activeReview?.cloudPortfolio?.name
    ?? (activeReview?.holdings.length ? "Current portfolio" : "No active portfolio");
  const currency = activeReview?.investorCurrency || activeReview?.reviewSummary?.investorCurrency || "USD";
  const holdingsCount = activeReview?.reviewSummary?.holdingsCount ?? activeReview?.holdings.length ?? 0;
  const reviewStatus = activeReview?.stagedProgress?.status ?? activeReview?.runStatus;
  const evidenceQuality = pathname.startsWith("/comparison")
    ? activeReview?.comparisonResult?.evidenceQuality ?? activeReview?.reviewSummary?.diagnosis.evidenceQuality
    : pathname.startsWith("/verdict")
      ? activeReview?.verdictResult?.evidenceQuality ?? activeReview?.comparisonResult?.evidenceQuality ?? activeReview?.reviewSummary?.diagnosis.evidenceQuality
      : activeReview?.reviewSummary?.evidence?.quality ?? activeReview?.reviewSummary?.diagnosis.evidenceQuality;
  const analysisWindow = readOutputSummaryField(activeReview?.reviewResult?.outputs, "analysis_window");
  const updatedAt = formatDateTime(activeReview?.reviewSummary?.generatedAt ?? activeReview?.updatedAt);
  const cta = ctaForPath({ pathname, flags: journeyFlags, runStatus: activeReview?.runStatus });

  return (
    <header className="sticky top-0 z-30 border-b border-pmri-border/38 bg-pmri-bg/88 shadow-[0_18px_44px_rgba(0,0,0,0.18)] backdrop-blur-xl">
      <div className="mx-auto flex w-full max-w-[1240px] flex-col gap-3 px-4 py-3 md:px-6 lg:px-8 xl:px-0">
        <div className="flex flex-col gap-3 lg:flex-row lg:items-center lg:justify-between">
          <div className="min-w-0">
            <p className="pmri-type-meta text-pmri-blueSoft">Portfolio MRI · {meta.eyebrow}</p>
            <p className="mt-1 truncate text-lg font-semibold tracking-[-0.03em] text-pmri-text md:text-xl">
              {meta.title}
            </p>
          </div>

          <div className="flex flex-wrap items-center gap-3">
            <StatusBadge tone={reviewStatusTone(reviewStatus)} dot={Boolean(reviewStatus)}>
              {normalizeStatus(reviewStatus)}
            </StatusBadge>
            {evidenceQuality ? (
              <StatusBadge tone={evidenceTone(evidenceQuality)} dot={evidenceTone(evidenceQuality) !== "slate"}>
                Evidence · {evidenceQuality}
              </StatusBadge>
            ) : null}
            {cta.href && !cta.disabled ? (
              <Link href={cta.href} className="pmri-focus pmri-primary-action rounded-full px-4 py-2 text-xs font-semibold transition">
                {cta.label}
              </Link>
            ) : (
              <span className="rounded-full border border-pmri-border/65 bg-white/[0.03] px-4 py-2 text-xs font-semibold text-pmri-muted">
                {cta.label}
              </span>
            )}
          </div>
        </div>

        <div className="grid gap-2 text-sm sm:grid-cols-2 lg:grid-cols-5">
          <UtilityItem label="Portfolio" value={portfolioName} />
          <UtilityItem label="Currency" value={currency} />
          <UtilityItem label="Holdings" value={holdingsCount ? `${holdingsCount} holdings` : "No holdings"} />
          <UtilityItem label="Data window" value={analysisWindow || "Not provided"} />
          <UtilityItem label="Updated" value={updatedAt || "Not saved"} />
        </div>
      </div>
    </header>
  );
}
