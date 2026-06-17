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
      <div className="min-h-[100dvh] bg-pmri-bg">
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
    <div className="pmri-app-stage min-h-[100dvh] bg-decision-radial">
      <Sidebar />
      <div className="min-w-0">
        {hideTopJourneyProgress ? null : <TopJourneyProgress />}
        <main className="mx-auto w-full max-w-[1480px] px-4 pb-32 pt-5 md:px-8 md:pb-36 lg:px-10">
          {children}
        </main>
      </div>
    </div>
  );
}
