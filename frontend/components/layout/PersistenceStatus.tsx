"use client";

import { getSupabaseRuntimeStatus } from "@/lib/supabase/config";
import { useSupabasePersistence } from "@/lib/supabase/persistence";

function statusCopy() {
  const status = getSupabaseRuntimeStatus();

  if (status.enabled) {
    return {
      label: "Cloud persistence configured",
      detail: "Supabase public config is present. Sign in with Email OTP to prepare optional cloud saves.",
      dotClassName: "bg-pmri-positive"
    };
  }

  if (status.reason === "missing_env") {
    return {
      label: "Local demo mode",
      detail: "Supabase was requested, but public URL/key are missing. The review still uses local browser storage.",
      dotClassName: "bg-pmri-amber"
    };
  }

  return {
    label: "Local demo mode",
    detail: "Cloud persistence is off. Portfolio MRI keeps the current review in this browser.",
    dotClassName: "bg-pmri-border"
  };
}

export function PersistenceStatus() {
  const copy = statusCopy();
  const { notice, clearNotice } = useSupabasePersistence();

  return (
    <div className="mt-4 rounded-2xl border border-pmri-border/45 bg-white/[0.02] p-4" role="status">
      <div className="flex items-center gap-2">
        <span className={`h-2 w-2 rounded-full ${copy.dotClassName}`} aria-hidden="true" />
        <p className="pmri-label text-pmri-text2">{copy.label}</p>
      </div>
      <p className="mt-2 text-xs leading-5 text-pmri-muted">{copy.detail}</p>
      {notice ... (
        <div className={`mt-3 rounded-xl border px-3 py-2 text-xs leading-5 ${
          notice.tone === "warning"
            ... "border-pmri-amber/35 bg-pmri-amber/10 text-pmri-text2"
            : notice.tone === "success"
              ... "border-pmri-positive/35 bg-pmri-positive/10 text-pmri-text2"
              : "border-pmri-blue/25 bg-pmri-blue/10 text-pmri-text2"
        }`}>
          <div className="flex items-start justify-between gap-3">
            <p>{notice.message}</p>
            <button
              type="button"
              onClick={clearNotice}
              className="pmri-focus shrink-0 rounded-full border border-transparent px-2 py-0.5 text-[11px] font-medium text-pmri-muted transition hover:border-pmri-border/55 hover:text-pmri-text2"
            >
              Dismiss
            </button>
          </div>
        </div>
      ) : null}
    </div>
  );
}
