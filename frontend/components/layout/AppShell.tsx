"use client";

import type { ReactNode } from "react";
import { AnimatePresence, motion, useReducedMotion } from "framer-motion";
import { usePathname } from "next/navigation";
import { Sidebar } from "./Sidebar";
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
    <div className="min-h-screen bg-decision-radial">
      <div className="flex min-h-screen">
        <Sidebar />
        <div className="min-w-0 flex-1">
          {hideTopJourneyProgress ? null : <TopJourneyProgress />}
          <AnimatePresence mode="wait">
            <motion.main
              key={pathname}
              className="mx-auto w-full max-w-[1440px] px-4 py-8 md:px-8 lg:px-10"
              initial={reduceMotion ? false : "initial"}
              animate={reduceMotion ? undefined : "animate"}
              exit={reduceMotion ? undefined : "exit"}
              variants={reduceMotion ? undefined : pageVariants}
            >
              {children}
            </motion.main>
          </AnimatePresence>
        </div>
      </div>
    </div>
  );
}
