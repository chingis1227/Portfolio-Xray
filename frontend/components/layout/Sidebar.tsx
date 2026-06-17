"use client";

import Link from "next/link";
import { usePathname } from "next/navigation";
import { useState } from "react";
import { AnimatePresence, LayoutGroup, motion, useReducedMotion } from "framer-motion";
import {
  ChartLineUp,
  ClipboardText,
  FileText,
  Gauge,
  House,
  Scales,
  ShieldCheck,
  Sparkle,
  UserCircle,
  WaveSine
} from "@phosphor-icons/react";
import { BrandMark } from "@/components/onboarding/BrandMark";
import { buildJourneySteps } from "@/lib/journey";
import { useReviewState } from "@/lib/reviewState";
import { useSupabaseAuth } from "@/lib/supabase/auth";
import { buttonMotion, listContainerVariants, listItemVariants, pmriSpring } from "@/components/ui/motion";
import type { JourneyStepStatus } from "@/lib/types";

function statusClasses(status: JourneyStepStatus) {
  switch (status) {
    case "active":
      return "border-white/30 bg-white/[0.145] text-pmri-text shadow-[inset_0_1px_0_rgba(255,255,255,0.24),0_18px_42px_rgba(0,0,0,0.34)]";
    case "completed":
      return "border-white/[0.06] text-pmri-text2 hover:border-white/18 hover:bg-white/[0.08]";
    case "available":
      return "border-transparent text-pmri-muted hover:border-white/14 hover:bg-white/[0.07] hover:text-pmri-text2";
    case "locked":
      return "cursor-not-allowed border-transparent text-pmri-muted/40 opacity-70";
  }
}

const stepIcons = {
  "portfolio-input": ClipboardText,
  diagnosis: Gauge,
  evidence: WaveSine,
  "client-fit": UserCircle,
  hypothesis: Sparkle,
  comparison: Scales,
  verdict: ShieldCheck,
  report: FileText
};

export function Sidebar() {
  const pathname = usePathname();
  const { journeyFlags } = useReviewState();
  const { enabled, status: authStatus, user, signOut } = useSupabaseAuth();
  const steps = buildJourneySteps(pathname, journeyFlags);
  const [lockMessage, setLockMessage] = useState<string | null>(null);
  const reduceMotion = useReducedMotion();

  return (
    <aside className="pointer-events-none fixed inset-x-0 bottom-4 z-50 px-3 md:bottom-6 md:px-6" aria-label="Portfolio MRI navigation dock">
      <div className="mx-auto flex max-w-[1180px] items-end justify-center gap-3">
        <div className="pointer-events-auto hidden rounded-[1.65rem] border border-white/[0.095] bg-black/45 p-2 shadow-[0_22px_70px_rgba(0,0,0,0.55)] backdrop-blur-2xl lg:flex">
          <Link
            href="/workspace"
            className={`pmri-focus flex h-[3.25rem] w-[3.25rem] items-center justify-center rounded-[1.25rem] border transition ${pathname.startsWith("/workspace") ? "border-white/30 bg-white/[0.15] text-pmri-text" : "border-transparent text-pmri-muted hover:bg-white/[0.07] hover:text-pmri-text2"}`}
            aria-label="Workspace"
            title="Workspace"
            onClick={() => setLockMessage(null)}
          >
            <House size={24} weight={pathname.startsWith("/workspace") ? "fill" : "regular"} />
          </Link>
        </div>

        <div className="pointer-events-auto min-w-0 rounded-[2rem] border border-white/[0.095] bg-[linear-gradient(180deg,rgba(55,57,62,0.74),rgba(23,24,27,0.72))] p-2 shadow-[0_24px_80px_rgba(0,0,0,0.58),inset_0_1px_0_rgba(255,255,255,0.12)] backdrop-blur-2xl">
          <div className="flex max-w-full items-center gap-1.5 overflow-x-auto px-1 [scrollbar-width:none] [&::-webkit-scrollbar]:hidden">
            <Link
              href="/"
              className="pmri-focus mr-1 hidden h-[3.25rem] w-[3.25rem] shrink-0 items-center justify-center rounded-[1.35rem] border border-white/[0.08] bg-white/[0.055] text-pmri-text shadow-[inset_0_1px_0_rgba(255,255,255,0.12)] sm:flex"
              aria-label="Portfolio MRI home"
              title="Portfolio MRI"
            >
              <BrandMark size="sm" />
            </Link>

            <LayoutGroup>
              <motion.nav
                className="flex items-center gap-1.5"
                aria-label="Portfolio MRI gated journey dock"
                variants={reduceMotion ? undefined : listContainerVariants}
                initial={reduceMotion ? false : "hidden"}
                animate={reduceMotion ? undefined : "visible"}
              >
                {steps.map((step) => {
                  const Icon = stepIcons[step.id as keyof typeof stepIcons] ?? ChartLineUp;
                  const isActive = step.status === "active";
                  const className = `pmri-focus group relative flex h-[3.25rem] w-[3.25rem] shrink-0 items-center justify-center rounded-[1.35rem] border transition md:h-14 md:w-14 ${statusClasses(step.status)}`;

                  const content = (
                    <>
                      {isActive ? (
                        <motion.span
                          layoutId="sidebar-active-step"
                          className="absolute inset-0 rounded-[1.35rem] bg-[radial-gradient(circle_at_50%_0%,rgba(255,255,255,0.22),transparent_58%),linear-gradient(180deg,rgba(255,255,255,0.09),rgba(255,255,255,0.025))]"
                          transition={pmriSpring}
                          aria-hidden="true"
                        />
                      ) : null}
                      <span className="relative z-10 flex flex-col items-center gap-0.5">
                        <Icon size={24} weight={isActive ? "fill" : "regular"} />
                        <span className="data-figure text-[9px] leading-none text-current/55">0{step.index + 1}</span>
                      </span>
                      <span className="pointer-events-none absolute bottom-[calc(100%+0.6rem)] left-1/2 hidden -translate-x-1/2 whitespace-nowrap rounded-full border border-white/[0.09] bg-black/80 px-3 py-1.5 text-xs font-medium text-pmri-text2 opacity-0 shadow-[0_14px_40px_rgba(0,0,0,0.45)] backdrop-blur-xl transition group-hover:block group-hover:opacity-100 group-focus-visible:block group-focus-visible:opacity-100 md:block md:opacity-0">
                        {step.shortLabel}
                      </span>
                    </>
                  );

                  return (
                    <motion.div key={step.id} variants={reduceMotion ? undefined : listItemVariants} layout>
                      {step.status === "locked" ? (
                        <motion.button
                          type="button"
                          className={className}
                          aria-label={`${step.shortLabel} locked`}
                          aria-disabled="true"
                          title={step.shortLabel}
                          onClick={() => setLockMessage(step.lockReason)}
                          {...(reduceMotion ? {} : buttonMotion)}
                        >
                          {content}
                        </motion.button>
                      ) : (
                        <Link
                          href={step.href}
                          className={className}
                          aria-label={step.shortLabel}
                          title={step.shortLabel}
                          onClick={() => setLockMessage(null)}
                        >
                          {content}
                        </Link>
                      )}
                    </motion.div>
                  );
                })}
              </motion.nav>
            </LayoutGroup>
          </div>
        </div>

        {enabled ? (
          <div className="pointer-events-auto hidden rounded-[1.65rem] border border-white/[0.095] bg-black/45 p-2 shadow-[0_22px_70px_rgba(0,0,0,0.55)] backdrop-blur-2xl xl:block">
            {authStatus === "signed_in" ? (
              <button
                type="button"
                onClick={() => void signOut()}
                className="pmri-focus flex h-[3.25rem] max-w-[10rem] items-center gap-2 rounded-[1.25rem] border border-transparent px-3 text-left text-xs text-pmri-muted transition hover:border-white/14 hover:bg-white/[0.07] hover:text-pmri-text2"
                title={user?.email ?? "Sign out"}
              >
                <UserCircle size={22} />
                <span className="truncate">Sign out</span>
              </button>
            ) : (
              <Link
                href="/onboarding/sign-in"
                className="pmri-focus flex h-[3.25rem] items-center gap-2 rounded-[1.25rem] border border-transparent px-3 text-xs text-pmri-muted transition hover:border-white/14 hover:bg-white/[0.07] hover:text-pmri-text2"
              >
                <UserCircle size={22} />
                Sign in
              </Link>
            )}
          </div>
        ) : null}
      </div>

      <AnimatePresence initial={false}>
        {lockMessage ? (
          <motion.div
            className="pointer-events-auto mx-auto mt-3 max-w-md rounded-2xl border border-pmri-amber/30 bg-black/70 px-4 py-3 text-center text-xs leading-5 text-pmri-text2 shadow-[0_18px_46px_rgba(0,0,0,0.5)] backdrop-blur-xl"
            role="status"
            initial={reduceMotion ? false : { opacity: 0, y: 8, scale: 0.98 }}
            animate={reduceMotion ? undefined : { opacity: 1, y: 0, scale: 1 }}
            exit={reduceMotion ? undefined : { opacity: 0, y: 6, scale: 0.98 }}
            transition={pmriSpring}
          >
            {lockMessage}
          </motion.div>
        ) : null}
      </AnimatePresence>
    </aside>
  );
}
