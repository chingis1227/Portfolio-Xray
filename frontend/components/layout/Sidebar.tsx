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

function statusClasses(status: JourneyStepStatus) {
  switch (status) {
    case "active":
      return "border-pmri-blue/22 bg-pmri-blue/[0.055] text-pmri-text shadow-[inset_2px_0_0_rgba(168,189,211,0.42)]";
    case "completed":
      return "border-transparent text-pmri-text2/85 hover:border-pmri-border/55 hover:bg-white/[0.028]";
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
      return "bg-pmri-muted/55";
    case "available":
      return "bg-pmri-border";
    case "locked":
      return "bg-pmri-border/35";
  }
}

export function Sidebar() {
  const pathname = usePathname();
  const { journeyFlags } = useReviewState();
  const { enabled, status: authStatus, user, signOut } = useSupabaseAuth();
  const steps = buildJourneySteps(pathname, journeyFlags);
  const [lockMessage, setLockMessage] = useState<string | null>(null);
  const reduceMotion = useReducedMotion();

  return (
    <aside className="hidden min-h-screen w-64 shrink-0 border-r border-pmri-border/45 bg-pmri-secondary/88 px-5 py-6 shadow-[16px_0_64px_rgba(0,0,0,0.14)] lg:flex lg:flex-col">
      <div>
        <div className="flex items-center gap-3">
          <div className="flex h-12 w-12 shrink-0 items-center justify-center rounded-2xl border border-pmri-border/55 bg-white/[0.035] shadow-decision">
            <BrandMark size="sm" />
          </div>
          <div className="min-w-0">
            <p className="text-lg font-semibold tracking-[-0.025em] text-pmri-text">Portfolio MRI</p>
            <p className="pmri-microcopy mt-1">Investment Decision Room</p>
          </div>
        </div>
      </div>

      <AnimatePresence initial={false}>
        {lockMessage ? (
          <motion.div
            className="mt-6 rounded-2xl border border-pmri-amber/30 bg-pmri-amber/10 px-3 py-3 text-xs leading-5 text-pmri-text2"
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
          className={`pmri-focus pmri-nav-text group flex w-full items-center justify-between rounded-2xl border px-3.5 py-3 text-left transition ${pathname.startsWith("/workspace") ? "border-pmri-blue/22 bg-pmri-blue/[0.055] text-pmri-text shadow-[inset_2px_0_0_rgba(168,189,211,0.42)]" : "border-transparent text-pmri-text2 hover:border-pmri-border/70 hover:bg-white/[0.035]"}`}
          onClick={() => setLockMessage(null)}
        >
          <span className="flex min-w-0 items-center gap-3">
            <span className={`h-2 w-2 rounded-full ${pathname.startsWith("/workspace") ? "bg-pmri-blue" : "bg-pmri-border"}`} />
            <span className="truncate">Workspace</span>
          </span>
        </Link>
      </nav>

      <LayoutGroup>
      <motion.nav
        className="mt-3 space-y-1.5"
        aria-label="Portfolio MRI gated journey rail"
        variants={reduceMotion ? undefined : listContainerVariants}
        initial={reduceMotion ? false : "hidden"}
        animate={reduceMotion ? undefined : "visible"}
      >
        {steps.map((step) => {
          const content = (
            <>
              <span className="flex min-w-0 items-center gap-3">
                <motion.span layout className={`h-2 w-2 rounded-full ${dotClasses(step.status)}`} transition={pmriSpring} />
                <span className="truncate">{step.shortLabel}</span>
              </span>
              <span className="flex items-center gap-2">
                <span className="data-figure text-[11px] text-pmri-muted/75">0{step.index + 1}</span>
              </span>
            </>
          );

          const className = `pmri-focus pmri-nav-text group flex w-full items-center justify-between rounded-2xl border px-3.5 py-3 text-left transition ${statusClasses(step.status)}`;

          return (
            <motion.div key={step.id} variants={reduceMotion ? undefined : listItemVariants} layout>
              {step.status === "locked" ? (
                <motion.button
                  type="button"
                  className={className}
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
                      className="absolute inset-0 rounded-2xl bg-pmri-blue/[0.035]"
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
        <div className="mt-auto rounded-2xl border border-pmri-border/45 bg-white/[0.02] p-3">
          <p className="pmri-label text-pmri-text2">Account</p>
          {authStatus === "signed_in" ? (
            <>
              <p className="mt-2 truncate text-xs text-pmri-muted" title={user?.email ?? undefined}>
                {user?.email ?? "Signed-in user"}
              </p>
              <button
                type="button"
                onClick={() => void signOut()}
                className="pmri-focus mt-3 w-full rounded-xl border border-pmri-border/55 px-3 py-2 text-xs font-semibold text-pmri-text2 transition hover:border-pmri-border hover:bg-white/[0.04]"
              >
                Sign out
              </button>
            </>
          ) : (
            <Link
              href="/onboarding/sign-in"
              className="pmri-focus mt-3 block rounded-xl border border-pmri-border/55 px-3 py-2 text-center text-xs font-semibold text-pmri-text2 transition hover:border-pmri-border hover:bg-white/[0.04]"
            >
              Sign in
            </Link>
          )}
        </div>
      ) : null}
    </aside>
  );
}
