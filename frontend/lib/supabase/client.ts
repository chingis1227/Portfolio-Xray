import { createBrowserClient } from "@supabase/ssr";
import type { SupabaseClient } from "@supabase/supabase-js";
import { getSupabaseRuntimeStatus } from "./config";

let browserClient: SupabaseClient | null = null;

export function getSupabaseBrowserClient(): SupabaseClient | null {
  const status = getSupabaseRuntimeStatus();
  if (!status.enabled || !status.url || !status.publishableKey) return null;
  if (!browserClient) {
    browserClient = createBrowserClient(status.url, status.publishableKey);
  }
  return browserClient;
}
