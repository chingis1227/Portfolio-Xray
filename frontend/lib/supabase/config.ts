export type SupabaseRuntimeStatus = {
  enabled: boolean;
  url?: string;
  publishableKey?: string;
  reason: "enabled" | "flag_disabled" | "missing_env";
};

function envValue(value: string | undefined) {
  return typeof value === "string" && value.trim() ? value.trim() : undefined;
}

export function getSupabaseRuntimeStatus(): SupabaseRuntimeStatus {
  const flag = envValue(process.env.NEXT_PUBLIC_PMRI_SUPABASE_ENABLED);
  const url = envValue(process.env.NEXT_PUBLIC_SUPABASE_URL);
  const publishableKey = envValue(process.env.NEXT_PUBLIC_SUPABASE_PUBLISHABLE_KEY);

  if (flag !== "true") return { enabled: false, reason: "flag_disabled" };
  if (!url || !publishableKey) return { enabled: false, reason: "missing_env" };
  return { enabled: true, url, publishableKey, reason: "enabled" };
}

export function isSupabaseEnabled() {
  return getSupabaseRuntimeStatus().enabled;
}

export const REVIEW_STAGE_SUMMARY_SOFT_LIMIT_BYTES = 55 * 1024;
