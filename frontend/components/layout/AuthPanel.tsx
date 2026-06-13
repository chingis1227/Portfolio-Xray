"use client";

import { FormEvent, useState } from "react";
import { useSupabaseAuth } from "@/lib/supabase/auth";

export function AuthPanel() {
  const { enabled, status, user, message, error, sendEmailOtp, verifyEmailOtp, signOut, clearAuthNotice } = useSupabaseAuth();
  const [email, setEmail] = useState("");
  const [otpCode, setOtpCode] = useState("");
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [isVerifying, setIsVerifying] = useState(false);

  if (!enabled) return null;

  async function handleSubmit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    setIsSubmitting(true);
    await sendEmailOtp(email);
    setIsSubmitting(false);
  }

  async function handleVerifyOtp() {
    setIsVerifying(true);
    await verifyEmailOtp(email, otpCode);
    setIsVerifying(false);
  }

  return (
    <div className="mt-4 rounded-2xl border border-pmri-border/45 bg-white/[0.02] p-4" aria-live="polite">
      <div className="flex items-center justify-between gap-3">
        <div>
          <p className="pmri-label text-pmri-text2">Cloud sign-in</p>
          <p className="mt-1 text-xs leading-5 text-pmri-muted">
            {status === "signed_in" ? "Signed in for optional cloud persistence." : "Email OTP unlocks optional saved portfolios and review history."}
          </p>
        </div>
        <span className={`h-2 w-2 rounded-full ${status === "signed_in" ? "bg-pmri-positive" : "bg-pmri-amber"}`} aria-hidden="true" />
      </div>

      {status === "loading" ? (
        <p className="mt-3 text-xs text-pmri-muted">Checking Supabase session…</p>
      ) : status === "signed_in" ? (
        <div className="mt-3 space-y-3">
          <p className="truncate text-xs text-pmri-text2" title={user?.email ?? undefined}>{user?.email ?? "Signed-in user"}</p>
          <button
            type="button"
            className="pmri-focus rounded-xl border border-pmri-border/55 px-3 py-2 text-xs font-semibold text-pmri-text2 transition hover:border-pmri-border hover:bg-white/[0.04]"
            onClick={() => void signOut()}
          >
            Sign out
          </button>
        </div>
      ) : (
        <form className="mt-3 space-y-3" onSubmit={handleSubmit}>
          <label className="block text-xs text-pmri-muted" htmlFor="supabase-auth-email">
            Email address
          </label>
          <input
            id="supabase-auth-email"
            type="email"
            autoComplete="email"
            value={email}
            onChange={(event) => {
              clearAuthNotice();
              setEmail(event.target.value);
            }}
            placeholder="you@example.com"
            className="pmri-focus w-full rounded-xl border border-pmri-border/55 bg-pmri-primary/55 px-3 py-2 text-sm text-pmri-text placeholder:text-pmri-muted/60"
          />
          <button
            type="submit"
            disabled={isSubmitting}
            className="pmri-focus w-full rounded-xl bg-pmri-blue px-3 py-2 text-xs font-semibold text-pmri-primary transition hover:bg-pmri-blue/90 disabled:cursor-not-allowed disabled:opacity-60"
          >
            {isSubmitting ? "Sending…" : "Email sign-in link"}
          </button>
          <div className="space-y-2 border-t border-pmri-border/35 pt-3">
            <label className="block text-xs text-pmri-muted" htmlFor="supabase-auth-otp">
              OTP code from email
            </label>
            <input
              id="supabase-auth-otp"
              type="text"
              inputMode="numeric"
              value={otpCode}
              onChange={(event) => {
                clearAuthNotice();
                setOtpCode(event.target.value);
              }}
              placeholder="123456"
              className="pmri-focus w-full rounded-xl border border-pmri-border/55 bg-pmri-primary/55 px-3 py-2 text-sm text-pmri-text placeholder:text-pmri-muted/60"
            />
            <button
              type="button"
              disabled={isVerifying}
              className="pmri-focus w-full rounded-xl border border-pmri-border/55 px-3 py-2 text-xs font-semibold text-pmri-text2 transition hover:border-pmri-border hover:bg-white/[0.04] disabled:cursor-not-allowed disabled:opacity-60"
              onClick={() => void handleVerifyOtp()}
            >
              {isVerifying ? "Verifying…" : "Verify OTP code"}
            </button>
          </div>
        </form>
      )}

      {message ? <p className="mt-3 text-xs leading-5 text-pmri-positive">{message}</p> : null}
      {error ? <p className="mt-3 text-xs leading-5 text-pmri-amber">{error}</p> : null}
    </div>
  );
}
