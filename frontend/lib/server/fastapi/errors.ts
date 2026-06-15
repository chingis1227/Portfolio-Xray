function projectRoot() {
  return "";
}

function isRecord(value: unknown): value is Record<string, unknown> {
  return Boolean(value) && typeof value === "object" && !Array.isArray(value);
}

function textValue(value: unknown, fallback = "") {
  return typeof value === "string" && value.trim() ? value.trim() : fallback;
}

export function scrubForClient(value: string, root = projectRoot()) {
  if (!value) return "";
  let cleaned = value.slice(-4000);
  if (root) {
    cleaned = cleaned
      .replaceAll(root, "[project]")
      .replaceAll(root.replaceAll("\\", "/"), "[project]");
  }
  return cleaned
    .replace(/\[project\][\\/][^\s'")<>]+/g, "[path]")
    .replace(/Traceback \(most recent call last\):[\s\S]*/g, "Backend failure details were captured safely.")
    .replace(/File "[^"]+", line \d+(?:, in [^\r\n]+)?/g, "Backend file reference hidden.")
    .replace(/[^\s'")<>]*run_review_from_payload\.py/g, "[path]")
    .replace(/[A-Za-z]:[\\/][^\s'")<>]+/g, "[path]")
    .replace(/\/(?:Users|home|var|tmp|mnt)\/[^\s'")<>]+/g, "[path]")
    .trim();
}

export function safeDetails(value: unknown): string[] {
  if (Array.isArray(value)) {
    return value.map((item) => (typeof item === "string" ? scrubForClient(item) : "")).filter(Boolean);
  }
  if (typeof value === "string" && value.trim()) return [scrubForClient(value)];
  return [];
}

export function legacyErrorFromFastApi(body: unknown, fallback: string) {
  const envelope = isRecord(body) ? body : {};
  const safeError = isRecord(envelope.safe_error) ? envelope.safe_error : {};
  const message = textValue(safeError.message, textValue(envelope.detail, fallback));
  const details = safeDetails(safeError.details);
  return {
    status: "failed",
    error: scrubForClient(message || fallback),
    details
  };
}
