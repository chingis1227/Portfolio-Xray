"use client";

import Link from "next/link";
import { usePathname } from "next/navigation";
import { useState } from "react";
import { AnimatePresence, LayoutGroup, motion, useReducedMotion } from "framer-motion";
import { BrandMark } from "@/components/onboarding/BrandMark";
import { buildJourneySteps } from "@/lib/journey";
import { useReviewState } from "@/lib/reviewState";
import { useSupabaseAuth } from "@/lib/supabase/auth";
import { buttonMotion, listContainerVariants, listItemVariants, pmriSpring } from "@/components/ui/motion";
import type { JourneyStepStatus } from "@/lib/types";

type SidebarIconProps = {
  className?: string;
};

function WorkspaceIcon({ className }: SidebarIconProps) {
  return (
    <svg className={className} viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" aria-hidden="true">
      <rect x="4" y="4" width="16" height="16" rx="1.8" />
      <path d="M11 4v16" />
      <path d="M15 9h5" />
    </svg>
  );
}

function PortfolioIcon({ className }: SidebarIconProps) {
  return (
    <svg className={className} viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" aria-hidden="true">
      <circle cx="12" cy="12" r="9" />
      <path d="M12 3v18" />
      <path d="M12 12h9" />
    </svg>
  );
}

function DiagnosisIcon({ className }: SidebarIconProps) {
  return (
    <svg className={className} viewBox="0 0 24 24" fill="none" aria-hidden="true">
      <rect x="4" y="4" width="16" height="16" rx="2.4" fill="currentColor" />
      <path d="M8 15v-3.5M12 15V8.5M16 15v-5" stroke="rgb(5 8 12)" strokeWidth="2" strokeLinecap="round" />
      <circle cx="8" cy="9" r="1" fill="rgb(5 8 12)" />
      <circle cx="16" cy="7" r="1" fill="rgb(5 8 12)" />
    </svg>
  );
}

function StressLabIcon({ className }: SidebarIconProps) {
  return (
    <svg className={className} viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" aria-hidden="true">
      <path d="M10 3h4" />
      <path d="M12 3v6.5" />
      <path d="M8.3 21h7.4c2 0 3.2-2.2 2.1-3.9L14 11.5V9.5h-4v2L6.2 17.1C5.1 18.8 6.3 21 8.3 21Z" />
      <path d="M8.5 16h7" />
    </svg>
  );
}

function ClientFitIcon({ className }: SidebarIconProps) {
  return (
    <svg className={className} viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" aria-hidden="true">
      <circle cx="9" cy="8" r="3" />
      <path d="M3.5 19c.8-3.4 3-5 5.5-5s4.7 1.6 5.5 5" />
      <circle cx="16.5" cy="9.5" r="2.5" />
      <path d="M15 14.2c2.3.2 4.1 1.7 4.8 4.8" />
    </svg>
  );
}

function HypothesisIcon({ className }: SidebarIconProps) {
  return (
    <svg className={className} viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" aria-hidden="true">
      <path d="M8 14.8a6 6 0 1 1 8 0c-1 .8-1.5 1.8-1.5 3.2h-5c0-1.4-.5-2.4-1.5-3.2Z" />
      <path d="M9.5 21h5" />
    </svg>
  );
}

function ComparisonIcon({ className }: SidebarIconProps) {
  return (
    <svg className={className} viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" aria-hidden="true">
      <path d="M4 17h10" />
      <path d="m8 13-4 4 4 4" />
      <path d="M20 7H10" />
      <path d="m16 3 4 4-4 4" />
      <path d="M14 12h-4" />
    </svg>
  );
}

function VerdictIcon({ className }: SidebarIconProps) {
  return (
    <svg className={className} viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" aria-hidden="true">
      <circle cx="12" cy="12" r="9" />
      <path d="m8.5 12.2 2.2 2.2 4.8-5" />
    </svg>
  );
}

function ReportIcon({ className }: SidebarIconProps) {
  return (
    <svg className={className} viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" aria-hidden="true">
      <path d="M7 3h7l4 4v14H7z" />
      <path d="M14 3v5h4" />
      <path d="M10 13h5" />
      <path d="M10 17h4" />
    </svg>
  );
}

function statusClasses(status: JourneyStepStatus) {
  switch (status) {
    case "active":
      return "border-white/[0.12] bg-white/[0.035] text-pmri-text shadow-[inset_0_1px_0_rgba(255,255,255,0.055),0_10px_28px_rgba(0,0,0,0.18)]";
    case "completed":
      return "border-transparent text-pmri-text2/[0.72] hover:border-white/[0.08] hover:bg-white/[0.022]";
    case "available":
      return "border-transparent text-pmri-muted/[0.84] hover:border-white/[0.08] hover:bg-white/[0.022]";
    case "locked":
      return "cursor-not-allowed border-transparent text-pmri-muted/48";
  }
}

function iconClasses(status: JourneyStepStatus) {
  switch (status) {
    case "active":
      return "text-pmri-text drop-shadow-[0_0_10px_rgba(157,204,240,0.12)]";
    case "completed":
      return "text-pmri-blueSoft/[0.72]";
    case "available":
      return "text-pmri-blueSoft/[0.64]";
    case "locked":
      return "text-pmri-muted/[0.42]";
  }
}

const stepIcons: Record<string, (props: SidebarIconProps) => JSX.Element> = {
  "portfolio-input": PortfolioIcon,
  diagnosis: DiagnosisIcon,
  evidence: StressLabIcon,
  "client-fit": ClientFitIcon,
  hypothesis: HypothesisIcon,
  comparison: ComparisonIcon,
  verdict: VerdictIcon,
  report: ReportIcon
};

export function Sidebar() {
  const pathname = usePathname();
  const { journeyFlags } = useReviewState();
  const { enabled, status: authStatus, user, signOut } = useSupabaseAuth();
  const steps = buildJourneySteps(pathname, journeyFlags);
  const [lockMessage, setLockMessage] = useState<string | null>(null);
  const reduceMotion = useReducedMotion();

  return (
    <aside className="hidden min-h-screen w-56 shrink-0 border-r border-white/[0.045] bg-[#07080a]/58 px-3.5 py-5 shadow-[18px_0_58px_rgba(0,0,0,0.18)] backdrop-blur-2xl lg:flex lg:flex-col">
      <div>
        <div className="flex items-center gap-3">
          <div className="flex h-10 w-10 shrink-0 items-center justify-center rounded-2xl border border-white/[0.07] bg-white/[0.026] shadow-[0_16px_40px_rgba(0,0,0,0.2)]">
            <BrandMark size="sm" />
          </div>
          <div className="min-w-0">
            <p className="text-sm font-semibold tracking-[-0.025em] text-pmri-text">Portfolio MRI</p>
            <p className="mt-0.5 text-[0.72rem] leading-5 text-pmri-muted">Investment Decision Room</p>
          </div>
        </div>
      </div>

      <AnimatePresence initial={false}>
        {lockMessage ? (
          <motion.div
            className="mt-6 rounded-2xl border border-pmri-amber/[0.22] bg-pmri-amber/[0.08] px-3 py-3 text-xs leading-5 text-pmri-text2"
            role="status"
            initial={reduceMotion ? false : { opacity: 0, y: -6, scale: 0.98 }}
            animate={reduceMotion ? undefined : { opacity: 1, y: 0, scale: 1 }}
            exit={reduceMotion ? undefined : { opacity: 0, y: -4, scale: 0.98 }}
            transition={pmriSpring}
          >
            {lockMessage}
          </motion.div>
        ) : null}
      </AnimatePresence>

      <nav className="mt-8 space-y-1.5" aria-label="Portfolio MRI account navigation">
        <Link
          href="/workspace"
          className={`pmri-focus pmri-nav-text group flex w-full items-center justify-between rounded-xl border px-3 py-2.5 text-left transition ${pathname.startsWith("/workspace") ? "border-white/[0.12] bg-white/[0.032] text-pmri-text shadow-[inset_0_1px_0_rgba(255,255,255,0.055),0_10px_28px_rgba(0,0,0,0.18)]" : "border-transparent text-pmri-text2/[0.78] hover:border-white/[0.08] hover:bg-white/[0.022]"}`}
          onClick={() => setLockMessage(null)}
        >
          <span className="flex min-w-0 items-center gap-3">
            <span className={`flex h-5 w-5 shrink-0 items-center justify-center ${pathname.startsWith("/workspace") ? "text-pmri-text" : "text-pmri-blueSoft/[0.62]"}`} aria-hidden="true">
              <WorkspaceIcon className="h-[1.125rem] w-[1.125rem]" />
            </span>
            <span className="truncate">Workspace</span>
          </span>
        </Link>
      </nav>

      <LayoutGroup>
      <motion.nav
        className="mt-3 space-y-1"
        aria-label="Portfolio MRI gated journey rail"
        variants={reduceMotion ? undefined : listContainerVariants}
        initial={reduceMotion ? false : "hidden"}
        animate={reduceMotion ? undefined : "visible"}
      >
        {steps.map((step) => {
          const Icon = stepIcons[step.id] ?? ReportIcon;
          const content = (
            <>
              <span className="flex min-w-0 items-center gap-3">
                <motion.span layout className={`flex h-6 w-6 shrink-0 items-center justify-center ${iconClasses(step.status)}`} transition={pmriSpring} aria-hidden="true">
                  <Icon className="h-5 w-5" />
                </motion.span>
                <span className="truncate">{step.shortLabel}</span>
              </span>
            </>
          );

          const className = `pmri-focus pmri-nav-text group flex w-full items-center justify-between rounded-xl border px-3 py-2.5 text-left transition ${statusClasses(step.status)}`;

          return (
            <motion.div key={step.id} variants={reduceMotion ? undefined : listItemVariants} layout>
              {step.status === "locked" ? (
                <motion.button
                  type="button"
                  className={`${className} relative overflow-hidden`}
                  aria-disabled="true"
                  onClick={() => setLockMessage(step.lockReason)}
                  {...(reduceMotion ? {} : buttonMotion)}
                >
                  {content}
                </motion.button>
              ) : (
                <Link
                  href={step.href}
                  className={`${className} relative overflow-hidden`}
                  onClick={() => setLockMessage(null)}
                >
                  {step.status === "active" ? (
                    <motion.span
                      layoutId="sidebar-active-step"
                      className="absolute inset-y-1 left-1 w-0.5 rounded-full bg-pmri-blueSoft/[0.46]"
                      transition={pmriSpring}
                      aria-hidden="true"
                    />
                  ) : null}
                  <span className="relative z-10 flex w-full items-center justify-between">{content}</span>
                </Link>
              )}
            </motion.div>
          );
        })}
      </motion.nav>
      </LayoutGroup>
      {enabled ? (
        <div className="mt-auto rounded-2xl border border-white/[0.055] bg-white/[0.018] p-3">
          <p className="text-[0.68rem] font-medium tracking-[0.06em] text-pmri-muted">Account</p>
          {authStatus === "signed_in" ? (
            <>
              <p className="mt-2 truncate text-xs text-pmri-muted" title={user?.email ?? undefined}>
                {user?.email ?? "Signed-in user"}
              </p>
              <button
                type="button"
                onClick={() => void signOut()}
                className="pmri-focus mt-3 w-full rounded-xl border border-white/[0.075] px-3 py-2 text-xs font-semibold text-pmri-text2 transition hover:border-white/[0.14] hover:bg-white/[0.035]"
              >
                Sign out
              </button>
            </>
          ) : (
            <Link
              href="/onboarding/sign-in"
              className="pmri-focus mt-3 block rounded-xl border border-white/[0.075] px-3 py-2 text-center text-xs font-semibold text-pmri-text2 transition hover:border-white/[0.14] hover:bg-white/[0.035]"
            >
              Sign in
            </Link>
          )}
        </div>
      ) : null}
    </aside>
  );
}
