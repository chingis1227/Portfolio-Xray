"use client";

import { useEffect, useState } from "react";
import { useRouter } from "next/navigation";
import { OnboardingFrame } from "@/components/onboarding/OnboardingFrame";
import { readOnboardingState, writeOnboardingState } from "@/lib/onboarding";

export default function OnboardingNamePage() {
  const router = useRouter();
  const [name, setName] = useState("");

  useEffect(() => {
    setName(readOnboardingState().name);
  }, []);

  function continueToProfile() {
    writeOnboardingState({ name: name.trim() });
    router.push("/onboarding/investor-type");
  }

  return (
    <OnboardingFrame
      currentStep={1}
      eyebrow="Personal setup"
      title="What should we call you..."
      description="This is only used to make the intake feel personal before the portfolio screen opens."
    >
      <div className="mx-auto max-w-xl lg:mx-0">
        <label className="block text-left">
          <span className="pmri-label block">Name</span>
          <input
            autoFocus
            value={name}
            onChange={(event) => setName(event.target.value)}
            onKeyDown={(event) => {
              if (event.key === "Enter") continueToProfile();
            }}
            placeholder="Pavel"
            className="pmri-focus mt-3 w-full border-0 border-b border-pmri-border/80 bg-transparent px-1 py-4 text-center text-3xl font-semibold tracking-[-0.035em] text-pmri-text outline-none placeholder:text-pmri-muted/50 focus:border-pmri-blue lg:text-left"
          />
        </label>
        <div className="mt-8 flex flex-col gap-3 sm:flex-row">
          <button type="button" onClick={continueToProfile} className="pmri-focus pmri-primary-action rounded-full px-6 py-3 text-sm font-semibold transition">
            Continue
          </button>
        </div>
      </div>
    </OnboardingFrame>
  );
}
