"use client";

import type { Session, User } from "@supabase/supabase-js";
import { createContext, useCallback, useContext, useEffect, useMemo, useState, type ReactNode } from "react";
import { getSupabaseBrowserClient } from "./client";
import { getSupabaseRuntimeStatus } from "./config";

type AuthStatus = "disabled" | "loading" | "signed_out" | "signed_in";

type SupabaseAuthContextValue = {
  enabled: boolean;
  status: AuthStatus;
  session: Session | null;
  user: User | null;
  message: string | null;
  error: string | null;
  sendEmailOtp: (email: string) => Promise<void>;
  verifyEmailOtp: (email: string, token: string) => Promise<void>;
  signOut: () => Promise<void>;
  clearAuthNotice: () => void;
};

const SupabaseAuthContext = createContext<SupabaseAuthContextValue | null>(null);

function buildRedirectTo() {
  if (typeof window === "undefined") return undefined;
  return `${window.location.origin}/auth/callback`;
}

function humanizeError(message: string) {
  if (message.toLowerCase().includes("fetch")) {
    return "Could not reach Supabase Auth. Check the public URL/key and network connection.";
  }
  return message;
}

export function SupabaseAuthProvider({ children }: { children: ReactNode }) {
  const runtimeStatus = getSupabaseRuntimeStatus();
  const enabled = runtimeStatus.enabled;
  const [session, setSession] = useState<Session | null>(null);
  const [status, setStatus] = useState<AuthStatus>(enabled ? "loading" : "disabled");
  const [message, setMessage] = useState<string | null>(null);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    if (!enabled) {
      setSession(null);
      setStatus("disabled");
      return;
    }

    const supabase = getSupabaseBrowserClient();
    if (!supabase) {
      setSession(null);
      setStatus("disabled");
      return;
    }

    let isMounted = true;
    setStatus("loading");

    supabase.auth.getSession().then(({ data, error: sessionError }) => {
      if (!isMounted) return;
      if (sessionError) {
        setError(humanizeError(sessionError.message));
        setStatus("signed_out");
        return;
      }
      setSession(data.session);
      setStatus(data.session ? "signed_in" : "signed_out");
    });

    const { data: subscription } = supabase.auth.onAuthStateChange((_event, nextSession) => {
      if (!isMounted) return;
      setSession(nextSession);
      setStatus(nextSession ? "signed_in" : "signed_out");
      setError(null);
    });

    return () => {
      isMounted = false;
      subscription.subscription.unsubscribe();
    };
  }, [enabled]);

  const sendEmailOtp = useCallback(async (email: string) => {
    setError(null);
    setMessage(null);

    const trimmedEmail = email.trim();
    if (!trimmedEmail) {
      setError("Enter an email address first.");
      return;
    }

    const supabase = getSupabaseBrowserClient();
    if (!enabled || !supabase) {
      setError("Cloud sign-in is disabled. The local demo remains available without login.");
      return;
    }

    const { error: otpError } = await supabase.auth.signInWithOtp({
      email: trimmedEmail,
      options: {
        emailRedirectTo: buildRedirectTo(),
        shouldCreateUser: true
      }
    });

    if (otpError) {
      setError(humanizeError(otpError.message));
      return;
    }

    setMessage("Check your email for the Portfolio MRI sign-in link or OTP code.");
  }, [enabled]);

  const verifyEmailOtp = useCallback(async (email: string, token: string) => {
    setError(null);
    setMessage(null);

    const trimmedEmail = email.trim();
    const trimmedToken = token.trim();
    if (!trimmedEmail || !trimmedToken) {
      setError("Enter both email address and OTP code.");
      return;
    }

    const supabase = getSupabaseBrowserClient();
    if (!enabled || !supabase) {
      setError("Cloud sign-in is disabled. The local demo remains available without login.");
      return;
    }

    const { error: verifyError } = await supabase.auth.verifyOtp({
      email: trimmedEmail,
      token: trimmedToken,
      type: "email"
    });

    if (verifyError) {
      setError(humanizeError(verifyError.message));
      return;
    }

    setMessage("Signed in. Optional cloud persistence is ready for later sessions.");
  }, [enabled]);

  const signOut = useCallback(async () => {
    setError(null);
    setMessage(null);

    const supabase = getSupabaseBrowserClient();
    if (!enabled || !supabase) return;

    const { error: signOutError } = await supabase.auth.signOut();
    if (signOutError) {
      setError(humanizeError(signOutError.message));
      return;
    }

    setSession(null);
    setStatus("signed_out");
    setMessage("Signed out. Local browser review state is still available.");
  }, [enabled]);

  const clearAuthNotice = useCallback(() => {
    setError(null);
    setMessage(null);
  }, []);

  const value = useMemo<SupabaseAuthContextValue>(() => ({
    enabled,
    status,
    session,
    user: session?.user ?? null,
    message,
    error,
    sendEmailOtp,
    verifyEmailOtp,
    signOut,
    clearAuthNotice
  }), [clearAuthNotice, enabled, error, message, sendEmailOtp, session, signOut, status, verifyEmailOtp]);

  return <SupabaseAuthContext.Provider value={value}>{children}</SupabaseAuthContext.Provider>;
}

export function useSupabaseAuth() {
  const context = useContext(SupabaseAuthContext);
  if (!context) throw new Error("useSupabaseAuth must be used within SupabaseAuthProvider");
  return context;
}
