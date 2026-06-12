import { createServerClient } from "@supabase/ssr";
import type { SupabaseClient } from "@supabase/supabase-js";
import { cookies } from "next/headers";
import { getSupabaseRuntimeStatus } from "./config";

export function createSupabaseServerClient(): SupabaseClient | null {
  const status = getSupabaseRuntimeStatus();
  if (!status.enabled || !status.url || !status.publishableKey) return null;

  const cookieStore = cookies();

  return createServerClient(status.url, status.publishableKey, {
    cookies: {
      getAll() {
        return cookieStore.getAll();
      },
      setAll(cookiesToSet) {
        try {
          cookiesToSet.forEach(({ name, value, options }) => {
            cookieStore.set(name, value, options);
          });
        } catch {
          // Server Components cannot always write cookies. Route handlers such as
          // /auth/callback can, and browser auth still works when Supabase is disabled.
        }
      }
    }
  });
}
