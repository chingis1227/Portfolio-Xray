"use client";

import Link from "next/link";
import { usePathname, useRouter } from "next/navigation";
import type { ReactNode } from "react";
import { useEffect } from "react";
import { useSupabaseAuth } from "@/lib/supabase/auth";
import { BrandMark } from "./BrandMark";

const steps = ["Name", "Intake", "Setup"];

export function OnboardingFrame({
  children,
  currentStep,
  eyebrow,
  title,
  description,
  backHref = "/",
  aside
}: {
  children: ReactNode;
  currentStep: number;
  eyebrow: string;
  title: string;
  description: string;
  backHref?: string;
  aside?: ReactNode;
}) {
  const router = useRouter();
  const pathname = usePathname();
  const { status } = useSupabaseAuth();

  useEffect(() => {
    const isLocalhost = typeof window !== "undefined" && ["localhost", "127.0.0.1"].includes(window.location.hostname);
    const devBypassParam = typeof window !== "undefined" ? new URLSearchParams(window.location.search).get("dev_bypass") : null;
    if (isLocalhost && devBypassParam === "1") {
      window.sessionStorage.setItem("pmri.auth.devBypass", "1");
    }
    const devBypass = isLocalhost && window.sessionStorage.getItem("pmri.auth.devBypass") === "1";

    if (status === "signed_out" && !devBypass && pathname !== "/onboarding/sign-in") {
      router.replace("/onboarding/sign-in");
    }
  }, [pathname, router, status]);

  return (
    <main className="relative min-h-screen overflow-hidden bg-pmri-bg text-pmri-text">
      <div className="pointer-events-none absolute inset-0 bg-[radial-gradient(circle_at_50%_18%,rgba(59,130,246,0.16),transparent_30%),radial-gradient(circle_at_18%_24%,rgba(170,183,198,0.09),transparent_26%),linear-gradient(180deg,rgba(255,255,255,0.035),transparent_42%)]" />
      <div className="pointer-events-none absolute left-1/2 top-24 h-[420px] w-[420px] -translate-x-1/2 rounded-full border border-pmri-blue/15 opacity-50 [background:repeating-radial-gradient(circle,rgba(96,165,250,0.18)_0_1px,transparent_1px_18px)]" />
      <div className="relative mx-auto flex min-h-screen w-full max-w-6xl flex-col px-5 py-6 md:px-8">
        <header className="flex items-center justify-between gap-4">
          <Link href={backHref} className="pmri-focus rounded-full border border-pmri-border/60 bg-white/[0.025] px-4 py-2 text-sm font-medium text-pmri-text2 transition hover:border-pmri-blue/35 hover:text-pmri-text">
            Back
          </Link>
          <div className="flex min-w-0 flex-1 items-center justify-center gap-2 px-2">
            {steps.map((step, index) => {
              const active = index + 1 <= currentStep;
              return (
                <div key={step} className="flex items-center gap-2">
                  <span className={`h-1.5 w-10 rounded-full transition ${active ? "bg-pmri-blue" : "bg-pmri-border/55"}`} aria-hidden="true" />
                  <span className="hidden text-xs text-pmri-muted md:inline">{step}</span>
                </div>
              );
            })}
          </div>
          <span className="rounded-full border border-pmri-border/60 px-4 py-2 text-sm font-medium text-pmri-muted">
            Profile setup
          </span>
        </header>

        <section className="grid flex-1 items-center gap-8 py-12 lg:grid-cols-[minmax(0,1fr)_380px]">
          <div className="mx-auto w-full max-w-2xl text-center lg:text-left">
            <div className="mb-8 flex justify-center lg:justify-start">
              <div className="rounded-3xl border border-pmri-border/55 bg-white/[0.035] p-4 shadow-decision">
                <BrandMark className="h-14 w-14" />
              </div>
            </div>
            <p className="pmri-label text-pmri-blueSoft">{eyebrow}</p>
            <h1 className="mt-4 text-4xl font-semibold tracking-[-0.055em] text-pmri-text md:text-6xl">{title}</h1>
            <p className="mx-auto mt-5 max-w-2xl text-base leading-7 text-pmri-text2 lg:mx-0">{description}</p>
            <div className="mt-9">{children}</div>
          </div>

          {aside ? (
            <aside className="mx-auto w-full max-w-md lg:mx-0">
              {aside}
            </aside>
          ) : null}
        </section>
      </div>
    </main>
  );
}
