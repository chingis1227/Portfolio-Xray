"use client";

import { useEffect } from "react";
import Link from "next/link";
import { useRouter } from "next/navigation";

export function OnboardingGoalsCompatibilityPage() {
  const router = useRouter();

  useEffect(() => {
    router.replace("/onboarding/investor-type");
  }, [router]);

  return (
    <main className="flex min-h-[100dvh] items-center justify-center bg-pmri-bg px-6 text-pmri-text">
      <section className="pmri-card max-w-md rounded-3xl p-6 text-center">
        <p className="pmri-label text-pmri-text2">Onboarding moved</p>
        <h1 className="mt-3 text-2xl font-semibold tracking-[-0.03em]">Opening investor type intake</h1>
        <p className="mt-3 text-sm leading-6 text-pmri-text2">
          This compatibility page redirects to the current onboarding question flow.
        </p>
        <Link href="/onboarding/investor-type" className="pmri-focus pmri-primary-action mt-5 inline-flex rounded-full px-5 py-2.5 text-sm font-medium transition">
          Continue onboarding
        </Link>
      </section>
    </main>
  );
}
