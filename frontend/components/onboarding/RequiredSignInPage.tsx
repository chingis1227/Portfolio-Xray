"use client";

import { FormEvent, useEffect, useState } from "react";
import { useRouter } from "next/navigation";
import { BrandMark } from "@/components/onboarding/BrandMark";
import { hasCompletedOnboarding } from "@/lib/onboarding";
import { useSupabaseAuth } from "@/lib/supabase/auth";
import { useSupabasePersistence } from "@/lib/supabase/persistence";

type Stage = "email" | "code";

export function RequiredSignInPage() {
  const router = useRouter();
  const { enabled, status, user, message, error, sendEmailOtp, verifyEmailOtp, clearAuthNotice } = useSupabaseAuth();
  const { savedPortfolios, savedReviews, workspaceState, portfoliosLoading, reviewsLoading, workspaceLoading } = useSupabasePersistence();
  const [stage, setStage] = useState<Stage>("email");
  const [email, setEmail] = useState("");
  const [code, setCode] = useState("");
  const [submitting, setSubmitting] = useState(false);
  const [isLocalhost, setIsLocalhost] = useState(false);

  useEffect(() => {
    setIsLocalhost(["localhost", "127.0.0.1"].includes(window.location.hostname));
  }, []);

  useEffect(() => {
    if (status === "signed_in") {
      if (!hasCompletedOnboarding()) {
        const timer = window.setTimeout(() => router.replace("/onboarding/name"), 650);
        return () => window.clearTimeout(timer);
      }
      if (portfoliosLoading || reviewsLoading || workspaceLoading) return;
      const hasSavedWorkspace = Boolean(workspaceState?.activeReviewRowId || workspaceState?.activePortfolioId || savedReviews.length || savedPortfolios.length);
      const nextRoute = hasSavedWorkspace ? "/workspace" : "/portfolio-input";
      const timer = window.setTimeout(() => router.replace(nextRoute), 650);
      return () => window.clearTimeout(timer);
    }
  }, [portfoliosLoading, reviewsLoading, router, savedPortfolios.length, savedReviews.length, status, workspaceLoading, workspaceState?.activePortfolioId, workspaceState?.activeReviewRowId]);

  async function submitEmail(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    const trimmed = email.trim();
    if (!trimmed || !enabled) return;
    setSubmitting(true);
    const sent = await sendEmailOtp(trimmed);
    setSubmitting(false);
    if (sent) setStage("code");
  }

  async function submitCode(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    setSubmitting(true);
    await verifyEmailOtp(email, code);
    setSubmitting(false);
  }

  return (
    <main id="main-content" className="relative flex min-h-[100dvh] items-center justify-center overflow-hidden bg-pmri-bg px-5 py-10 text-pmri-text">
      <div className="pointer-events-none absolute inset-0 bg-[radial-gradient(circle_at_50%_12%,rgba(255,255,255,0.055),transparent_30%),linear-gradient(180deg,rgba(255,255,255,0.026),transparent_46%)]" />
      <div className="pointer-events-none absolute inset-x-0 bottom-[-160px] h-[520px] border-t border-white/[0.035] opacity-35 pmri-moving-grid" />

      <section className="relative z-10 grid w-full max-w-5xl items-center gap-10 lg:grid-cols-[minmax(0,1fr)_420px]">
        <div>
          <BrandMark size="lg" />
          <p className="pmri-label mt-8 text-pmri-muted">Secure workspace</p>
          <h1 className="mt-4 text-4xl font-normal tracking-[-0.055em] text-pmri-text md:text-6xl">
            Sign in before opening the diagnostic room.
          </h1>
          <p className="mt-5 max-w-2xl text-base leading-7 text-pmri-text2">
            Portfolio MRI saves your planning profile before the portfolio screen. Email sign-in keeps the setup tied to your workspace instead of a loose browser session.
          </p>
          <div className="mt-8 grid gap-3 text-sm text-pmri-text2 md:grid-cols-3">
            {["Email first", "Verify code", "Then onboarding"].map((item, index) => (
              <div key={item} className="rounded-lg border border-pmri-border bg-pmri-surface px-4 py-3">
                <span className="data-figure text-pmri-text2">0{index + 1}</span>
                <span className="ml-3 font-normal">{item}</span>
              </div>
            ))}
          </div>
        </div>

        <div className="pmri-card rounded-lg p-6">
          {status === "signed_in" ? (
            <div>
              <p className="pmri-label text-pmri-text2">Signed in</p>
              <h2 className="mt-3 text-2xl font-normal tracking-[-0.035em] text-pmri-text">Opening your workspace...</h2>
              <p className="mt-3 truncate text-sm text-pmri-muted" title={user?.email ?? undefined}>{user?.email}</p>
            </div>
          ) : !enabled ? (
            <div>
              <p className="pmri-label text-pmri-amber">Sign-in required</p>
              <h2 className="mt-3 text-2xl font-normal tracking-[-0.035em] text-pmri-text">Email login is not configured.</h2>
              <p className="mt-3 text-sm leading-6 text-pmri-muted">
                Enable Supabase public configuration to enter the platform with the required email flow.
              </p>
            </div>
          ) : stage === "email" ? (
            <form onSubmit={submitEmail}>
              <p className="pmri-label text-pmri-muted">Step 01 / Email</p>
              <h2 className="mt-3 text-2xl font-normal tracking-[-0.035em] text-pmri-text">Enter your email</h2>
              <p className="mt-3 text-sm leading-6 text-pmri-muted">We will send a one-time code. The code step appears after this email is submitted.</p>
              <label className="mt-6 block">
                <span className="pmri-label block">Email address</span>
                <input
                  autoFocus
                  type="email"
                  value={email}
                  onChange={(event) => {
                    clearAuthNotice();
                    setEmail(event.target.value);
                  }}
                  placeholder="you@example.com"
                  className="pmri-focus mt-2 w-full rounded-lg border border-pmri-border bg-pmri-panel px-4 py-3 text-base text-pmri-text placeholder:text-pmri-muted/60"
                />
              </label>
              <button type="submit" disabled={submitting || !email.trim()} className="pmri-focus pmri-primary-action mt-5 w-full rounded-full px-5 py-3 text-sm font-normal transition disabled:cursor-not-allowed disabled:opacity-60">
                {submitting ? "Sending code..." : "Continue"}
              </button>
              {isLocalhost ? (
                <button
                  type="button"
                  onClick={() => {
                    window.sessionStorage.setItem("pmri.auth.devBypass", "1");
                    router.push("/onboarding/name");
                  }}
                  className="pmri-focus mt-3 w-full rounded-full border border-pmri-border px-5 py-3 text-sm font-normal text-pmri-text2 transition hover:border-white/25 hover:bg-white/[0.04]"
                >
                  Continue locally while Supabase is not ready
                </button>
              ) : null}
            </form>
          ) : (
            <form onSubmit={submitCode}>
              <p className="pmri-label text-pmri-muted">Step 02 / Verification</p>
              <h2 className="mt-3 text-2xl font-normal tracking-[-0.035em] text-pmri-text">Verify your code</h2>
              <p className="mt-3 text-sm leading-6 text-pmri-muted">Enter the code sent to <span className="font-medium text-pmri-text2">{email}</span>.</p>
              <label className="mt-6 block">
                <span className="pmri-label block">Verification code</span>
                <input
                  autoFocus
                  type="text"
                  inputMode="numeric"
                  value={code}
                  onChange={(event) => {
                    clearAuthNotice();
                    setCode(event.target.value);
                  }}
                  placeholder="123456"
                  className="pmri-focus mt-2 w-full rounded-lg border border-pmri-border bg-pmri-panel px-4 py-3 text-center text-2xl font-normal tracking-[0.3em] text-pmri-text placeholder:text-pmri-muted/45"
                />
              </label>
              <button type="submit" disabled={submitting || !code.trim()} className="pmri-focus pmri-primary-action mt-5 w-full rounded-full px-5 py-3 text-sm font-normal transition disabled:cursor-not-allowed disabled:opacity-60">
                {submitting ? "Verifying..." : "Verify and continue"}
              </button>
              <button type="button" onClick={() => { clearAuthNotice(); setStage("email"); }} className="pmri-focus mt-3 w-full rounded-full border border-pmri-border px-5 py-3 text-sm font-normal text-pmri-text2 transition hover:border-white/25 hover:bg-white/[0.04]">
                Change email
              </button>
            </form>
          )}

          {message ? <p className="mt-4 rounded-lg border border-white/25 bg-white/[0.055] px-4 py-3 text-sm leading-6 text-pmri-text2">{message}</p> : null}
          {error ? <p className="mt-4 rounded-lg border border-pmri-amber/30 bg-pmri-amber/10 px-4 py-3 text-sm leading-6 text-pmri-amber">{error}</p> : null}
        </div>
      </section>
    </main>
  );
}
