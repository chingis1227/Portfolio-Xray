export function safeMaxAssetWeightForHoldingCount(holdingCount: number, requestedMax: number | null | undefined) {
  if (requestedMax === null || requestedMax === undefined) return null;
  if (!Number.isFinite(requestedMax) || requestedMax <= 0) return requestedMax;
  const count = Math.max(1, Math.floor(holdingCount));
  const feasibleMinimum = Math.ceil((1 / count) * 100) / 100;
  return Math.min(1, Math.max(requestedMax, feasibleMinimum));
}

export function holdingCountFromReview(activeReview: { holdings?: unknown[]; reviewSummary?: { holdingsCount?: number } } | null | undefined) {
  const holdingsCount = activeReview?.holdings?.length;
  if (typeof holdingsCount === "number" && holdingsCount > 0) return holdingsCount;
  const summaryCount = activeReview?.reviewSummary?.holdingsCount;
  return typeof summaryCount === "number" && summaryCount > 0 ? summaryCount : 0;
}
