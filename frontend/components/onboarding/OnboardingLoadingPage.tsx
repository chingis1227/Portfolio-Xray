"use client";

import { useEffect, useMemo, useState } from "react";
import { useRouter } from "next/navigation";
import { BrandMark } from "@/components/onboarding/BrandMark";
import { buildClientFitProfileFromOnboarding, markOnboardingComplete, profileLabelForOnboarding, readOnboardingState } from "@/lib/onboarding";
import { useReviewState } from "@/lib/reviewState";
import { useSupabaseAuth } from "@/lib/supabase/auth";
import { getSupabaseBrowserClient } from "@/lib/supabase/client";

const setupSteps = [
  "Saving Client Fit context",
  "Preparing portfolio input workspace",
  "Keeping diagnostics current-portfolio-first",
  "Opening the decision room"
];

export function OnboardingLoadingPage() {
  const router = useRouter();
  const { hydrated, saveClientFitProfile } = useReviewState();
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
    if (!hydrated) return;

    const profile = buildClientFitProfileFromOnboarding(state);
    saveClientFitProfile(profile);
    markOnboardingComplete();

    if (status === "signed_in") {
      const supabase = getSupabaseBrowserClient();
      void supabase?.auth.updateUser({
        data: {
          pmri_onboarding_completed: true,
          pmri_onboarding: state
        }
      });
    }

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
  }, [hydrated, router, saveClientFitProfile, state, status]);

  return (
    <main id="main-content" className="relative flex min-h-[100dvh] items-center justify-center overflow-hidden bg-pmri-bg px-5 text-pmri-text">
      <div className="pointer-events-none absolute inset-0 bg-[radial-gradient(circle_at_50%_32%,rgba(255,255,255,0.055),transparent_28%),linear-gradient(180deg,rgba(255,255,255,0.026),transparent_50%)]" />
      <div className="pointer-events-none absolute h-[520px] w-[520px] rounded-full border border-white/[0.045] [background:repeating-radial-gradient(circle,rgba(255,255,255,0.055)_0_1px,transparent_1px_20px)]" />
      <section className="relative z-10 w-full max-w-xl text-center">
        <div className="mx-auto flex h-28 w-28 items-center justify-center rounded-lg border border-pmri-border bg-pmri-surface">
          <BrandMark size="xl" />
        </div>
        <p className="data-figure mt-10 text-5xl font-normal tracking-[-0.045em] text-pmri-text">{progress}%</p>
        <h1 className="mt-4 text-3xl font-normal tracking-[-0.045em] text-pmri-text md:text-4xl">Setting up your experience</h1>
        <p className="mt-4 text-base leading-7 text-pmri-text2">
          Personalizing the diagnostic room with a {profileLabel} profile.
        </p>
        <div className="mx-auto mt-8 h-2 max-w-md overflow-hidden rounded-full bg-pmri-border">
          <div className="h-full rounded-full bg-pmri-text transition-all duration-300" style={{ width: `${progress}%` }} />
        </div>
        <div className="mx-auto mt-8 grid max-w-md gap-3 text-left">
          {setupSteps.map((step, index) => (
            <div key={step} className={`rounded-lg border px-4 py-3 text-sm transition ${index <= activeIndex ? "border-white/35 bg-white/[0.06] text-pmri-text" : "border-pmri-border bg-white/[0.02] text-pmri-muted"}`}>
              {step}
            </div>
          ))}
        </div>
      </section>
    </main>
  );
}
