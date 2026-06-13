"use client";

import { FormEvent, useState } from "react";
import { useSupabaseAuth } from "@/lib/supabase/auth";

export function PublicAuthCard() {
  const { enabled, status, user, message, error, sendEmailOtp, verifyEmailOtp, signOut, clearAuthNotice } = useSupabaseAuth();
  const [email, setEmail] = useState("");
  const [otpCode, setOtpCode] = useState("");
  const [isSending, setIsSending] = useState(false);
  const [isVerifying, setIsVerifying] = useState(false);

  async function handleSubmit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    setIsSending(true);
    await sendEmailOtp(email);
    setIsSending(false);
  }

  async function handleVerifyOtp() {
    setIsVerifying(true);
    await verifyEmailOtp(email, otpCode);
    setIsVerifying(false);
  }

  if (!enabled) {
    return (
      <div className="pmri-card rounded-3xl p-5">
        <p className="pmri-label text-pmri-blueSoft">Local session</p>
        <h2 className="mt-2 text-xl font-semibold tracking-[-0.03em] text-pmri-text">Start without an account</h2>
        <p className="mt-3 text-sm leading-6 text-pmri-muted">
          Your onboarding profile stays in this browser. Cloud save can be enabled later without changing the diagnostic flow.
        </p>
      </div>
    );
  }

  return (
    <div className="pmri-card rounded-3xl p-5" aria-live="polite">
      <div className="flex items-start justify-between gap-4">
        <div>
          <p className="pmri-label text-pmri-blueSoft">Save your workspace</p>
          <h2 className="mt-2 text-xl font-semibold tracking-[-0.03em] text-pmri-text">
            {status === "signed_in" ? "Workspace connected" : "Optional secure sign-in"}
          </h2>
        </div>
        <span className={`mt-2 h-2.5 w-2.5 rounded-full ${status === "signed_in" ? "bg-pmri-positive" : "bg-pmri-amber"}`} aria-hidden="true" />
      </div>

      {status === "loading" ? (
        <p className="mt-4 text-sm text-pmri-muted">Checking saved workspace…</p>
      ) : status === "signed_in" ? (
        <div className="mt-4 space-y-4">
          <p className="truncate text-sm text-pmri-text2" title={user?.email ?? undefined}>{user?.email ?? "Signed-in user"}</p>
          <p className="text-sm leading-6 text-pmri-muted">You can continue onboarding now. Saved portfolios and review history unlock inside the platform.</p>
          <button type="button" onClick={() => void signOut()} className="pmri-focus rounded-full border border-pmri-border/60 px-4 py-2 text-sm font-medium text-pmri-text2 transition hover:border-pmri-border hover:bg-white/[0.04]">
            Sign out
          </button>
        </div>
      ) : (
        <form className="mt-4 space-y-3" onSubmit={handleSubmit}>
          <p className="text-sm leading-6 text-pmri-muted">Use email if you want this workspace to be recoverable. You can also skip it.</p>
          <label className="block">
            <span className="pmri-label block">Email</span>
            <input
              type="email"
              value={email}
              onChange={(event) => {
                clearAuthNotice();
                setEmail(event.target.value);
              }}
              placeholder="you@example.com"
              className="pmri-focus mt-2 w-full rounded-xl border border-pmri-border/55 bg-pmri-secondary/85 px-3 py-2.5 text-sm text-pmri-text placeholder:text-pmri-muted/60"
            />
          </label>
          <button type="submit" disabled={isSending} className="pmri-focus w-full rounded-full border border-pmri-blue/40 bg-pmri-blue px-4 py-2.5 text-sm font-semibold text-pmri-text transition hover:bg-pmri-blueSoft disabled:cursor-not-allowed disabled:opacity-60">
            {isSending ? "Sending code…" : "Send secure email code"}
          </button>
          <div className="border-t border-pmri-border/35 pt-3">
            <label className="block">
              <span className="pmri-label block">Code from email</span>
              <input
                type="text"
                inputMode="numeric"
                value={otpCode}
                onChange={(event) => {
                  clearAuthNotice();
                  setOtpCode(event.target.value);
                }}
                placeholder="123456"
                className="pmri-focus mt-2 w-full rounded-xl border border-pmri-border/55 bg-pmri-secondary/85 px-3 py-2.5 text-sm text-pmri-text placeholder:text-pmri-muted/60"
              />
            </label>
            <button type="button" disabled={isVerifying} onClick={() => void handleVerifyOtp()} className="pmri-focus mt-3 w-full rounded-full border border-pmri-border/60 px-4 py-2.5 text-sm font-semibold text-pmri-text2 transition hover:border-pmri-border hover:bg-white/[0.04] disabled:cursor-not-allowed disabled:opacity-60">
              {isVerifying ? "Verifying…" : "Verify code"}
            </button>
          </div>
        </form>
      )}

      {message ? <p className="mt-3 text-sm leading-6 text-pmri-positive">{message}</p> : null}
      {error ? <p className="mt-3 text-sm leading-6 text-pmri-amber">{error}</p> : null}
    </div>
  );
}
