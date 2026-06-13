"use client";

import { useEffect, useMemo, useState } from "react";
import { useRouter } from "next/navigation";
import { BrandMark } from "@/components/onboarding/BrandMark";
import { buildClientFitProfileFromOnboarding, profileLabelForOnboarding, readOnboardingState } from "@/lib/onboarding";
import { useReviewState } from "@/lib/reviewState";
import { useSupabaseAuth } from "@/lib/supabase/auth";

const setupSteps = [
  "Saving Client Fit context",
  "Preparing portfolio input workspace",
  "Keeping diagnostics current-portfolio-first",
  "Opening the decision room"
];

export default function OnboardingLoadingPage() {
  const router = useRouter();
  const { saveClientFitProfile } = useReviewState();
  const { status } = useSupabaseAuth();
  const [progress, setProgress] = useState(12);
  const [activeIndex, setActiveIndex] = useState(0);
  const state = useMemo(() => readOnboardingState(), []);
  const profileLabel = profileLabelForOnboarding(state);

  useEffect(() => {
    const isLocalhost = typeof window !== "undefined" && ["localhost", "127.0.0.1"].includes(window.location.hostname);
    const devBypass = isLocalhost && window.sessionStorage.getItem("pmri.auth.devBypass") === "1";

    if (status === "signed_out" && !devBypass) {
      router.replace("/onboarding/sign-in");
      return;
    }
    if (status !== "signed_in" && status !== "disabled" && !devBypass) return;

    const profile = buildClientFitProfileFromOnboarding(state);
    saveClientFitProfile(profile);

    const progressTimer = window.setInterval(() => {
      setProgress((current) => Math.min(current + 13, 100));
      setActiveIndex((current) => Math.min(current + 1, setupSteps.length - 1));
    }, 240);

    const routeTimer = window.setTimeout(() => {
      router.replace("/portfolio-input");
    }, 1250);

    return () => {
      window.clearInterval(progressTimer);
      window.clearTimeout(routeTimer);
    };
  }, [router, saveClientFitProfile, state, status]);

  return (
    <main className="relative flex min-h-screen items-center justify-center overflow-hidden bg-pmri-bg px-5 text-pmri-text">
      <div className="pointer-events-none absolute inset-0 bg-[radial-gradient(circle_at_50%_32%,rgba(59,130,246,0.22),transparent_26%),radial-gradient(circle_at_50%_50%,rgba(170,183,198,0.08),transparent_34%),linear-gradient(180deg,rgba(255,255,255,0.035),transparent_50%)]" />
      <div className="pointer-events-none absolute h-[520px] w-[520px] rounded-full border border-pmri-blue/15 [background:repeating-radial-gradient(circle,rgba(96,165,250,0.22)_0_1px,transparent_1px_20px)] motion-safe:animate-[pmri-spin_18s_linear_infinite]" />
      <section className="relative z-10 w-full max-w-xl text-center">
        <div className="mx-auto flex h-28 w-28 items-center justify-center rounded-[2rem] border border-pmri-border/55 bg-white/[0.035] shadow-decision">
          <BrandMark className="h-20 w-20" />
        </div>
        <p className="data-figure mt-10 text-5xl font-semibold tracking-[-0.045em] text-pmri-text">{progress}%</p>
        <h1 className="mt-4 text-3xl font-semibold tracking-[-0.045em] text-pmri-text md:text-5xl">Setting up your experience</h1>
        <p className="mt-4 text-base leading-7 text-pmri-text2">
          Personalizing the diagnostic room with a {profileLabel} profile.
        </p>
        <div className="mx-auto mt-8 h-2 max-w-md overflow-hidden rounded-full bg-pmri-border/45">
          <div className="h-full rounded-full bg-pmri-blue transition-all duration-300" style={{ width: `${progress}%` }} />
        </div>
        <div className="mx-auto mt-8 grid max-w-md gap-3 text-left">
          {setupSteps.map((step, index) => (
            <div key={step} className={`rounded-2xl border px-4 py-3 text-sm transition ${index <= activeIndex ? "border-pmri-blue/35 bg-pmri-blue/[0.08] text-pmri-text" : "border-pmri-border/45 bg-white/[0.02] text-pmri-muted"}`}>
              {step}
            </div>
          ))}
        </div>
      </section>
    </main>
  );
}
