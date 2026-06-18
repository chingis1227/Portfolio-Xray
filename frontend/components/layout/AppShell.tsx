"use client";

import type { ReactNode } from "react";
import { AnimatePresence, motion, useReducedMotion } from "framer-motion";
import { usePathname } from "next/navigation";
import { Sidebar } from "./Sidebar";
import { PlatformTopHeader } from "./PlatformTopHeader";
import { TopJourneyProgress } from "./TopJourneyProgress";
import { pageVariants } from "@/components/ui/motion";

export function AppShell({ children }: { children: ReactNode }) {
  const pathname = usePathname();
  const reduceMotion = useReducedMotion();
  const publicExperience = pathname === "/" || pathname.startsWith("/onboarding");
  const redesignedRoutes = [
    "/diagnosis",
    "/evidence",
    "/client-fit",
    "/hypothesis",
    "/comparison",
    "/verdict",
    "/report"
  ];
  const hideTopJourneyProgress = redesignedRoutes.some((route) => pathname === route || pathname.startsWith(`${route}/`));

  if (publicExperience) {
    return (
      <div className="min-h-screen bg-pmri-bg">
        <a href="#main-content" className="pmri-skip-link">Skip to main content</a>
        <AnimatePresence mode="wait">
          <motion.div
            key={pathname}
            initial={reduceMotion ? false : "initial"}
            animate={reduceMotion ? undefined : "animate"}
            exit={reduceMotion ? undefined : "exit"}
            variants={reduceMotion ? undefined : pageVariants}
          >
            {children}
          </motion.div>
        </AnimatePresence>
      </div>
    );
  }

  return (
    <div className="pmri-platform-workspace">
      <a href="#main-content" className="pmri-skip-link">Skip to main content</a>
      <div className="pmri-shell-layer flex min-h-screen">
        <Sidebar />
        <div className="min-w-0 flex-1">
          <PlatformTopHeader />
          {hideTopJourneyProgress ? null : <TopJourneyProgress />}
          <main id="main-content" className="mx-auto w-full max-w-[1220px] px-4 py-5 md:px-6 lg:px-8 xl:px-0">
            {children}
          </main>
        </div>
      </div>
    </div>
  );
}
