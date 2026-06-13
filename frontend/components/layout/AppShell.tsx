"use client";

import type { ReactNode } from "react";
import { usePathname } from "next/navigation";
import { Sidebar } from "./Sidebar";
import { TopJourneyProgress } from "./TopJourneyProgress";

export function AppShell({ children }: { children: ReactNode }) {
  const pathname = usePathname();
  const publicExperience = pathname === "/" || pathname.startsWith("/onboarding");

  if (publicExperience) {
    return <div className="min-h-screen bg-pmri-bg">{children}</div>;
  }

  return (
    <div className="min-h-screen bg-decision-radial">
      <div className="flex min-h-screen">
        <Sidebar />
        <div className="min-w-0 flex-1">
          <TopJourneyProgress />
          <main className="mx-auto w-full max-w-[1440px] px-4 py-8 md:px-8 lg:px-10">{children}</main>
        </div>
      </div>
    </div>
  );
}
