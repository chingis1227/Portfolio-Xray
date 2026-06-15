import type { StagedSafeError } from "@/lib/generated/api-types";

export function stagedSafeErrorMessage(error: StagedSafeError) {
  const parts = [
    error.message,
    error.code ? `Code: ${error.code}` : "",
    error.stage ? `Stage: ${error.stage}` : "",
    error.retryable ? "You can retry after checking that the backend/frontend servers are freshly restarted." : ""
  ].filter(Boolean);
  return parts.join(" ");
}
