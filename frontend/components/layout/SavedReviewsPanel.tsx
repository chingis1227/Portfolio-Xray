"use client";

import { useMemo } from "react";
import { useReviewState } from "@/lib/reviewState";
import { useSupabasePersistence, type SavedReviewRecord } from "@/lib/supabase/persistence";

const STAGE_LABELS = {
  input: "Input",
  data_load: "Data",
  xray: "X-Ray",
  stress: "Stress",
  client_fit: "Fit",
  problem_classification: "Problem",
  launchpad_builder: "Launchpad",
  diagnosis: "Dx",
  builder: "Builder",
  candidate: "Candidate",
  comparison: "Compare",
  verdict: "Verdict",
  report: "Report"
} as const;

function reviewTitle(review: SavedReviewRecord) {
  if (review.title) return review.title;
  if (typeof review.compactSummary.currentStage === "string") return `Staged review: ${review.compactSummary.currentStage}`;
  const headline = typeof review.compactSummary.diagnosisHeadline === "string" ? review.compactSummary.diagnosisHeadline : undefined;
  return headline || `Review ${review.reviewId}`;
}

function formatReviewDate(value?: string) {
  if (!value) return "Time unavailable";
  const date = new Date(value);
  if (Number.isNaN(date.getTime())) return value;
  return date.toLocaleDateString(undefined, { month: "short", day: "numeric", hour: "2-digit", minute: "2-digit" });
}

export function SavedReviewsPanel() {
  const { enabled, signedIn, savedReviews, reviewsLoading, refreshSavedReviews, setNotice } = useSupabasePersistence();
  const { hydrateCloudReview } = useReviewState();

  const visibleReviews = useMemo(() => savedReviews.slice(0, 5), [savedReviews]);

  if (!enabled || !signedIn) return null;

  return (
    <section className="mt-4 rounded-2xl border border-pmri-border/45 bg-white/[0.02] p-4">
      <div className="flex items-center justify-between gap-3">
        <div>
          <p className="pmri-label text-pmri-text2">Saved cloud reviews</p>
          <p className="mt-1 text-[11px] leading-4 text-pmri-muted">Compact summaries only; full artifacts stay local.</p>
        </div>
        <button
          type="button"
          onClick={() => void refreshSavedReviews()}
          className="pmri-focus rounded-full border border-pmri-border/55 px-2.5 py-1 text-[11px] font-medium text-pmri-muted transition hover:border-pmri-blue/45 hover:text-pmri-text2"
        >
          {reviewsLoading ? "..." : "Refresh"}
        </button>
      </div>

      {!reviewsLoading && !visibleReviews.length ? (
        <p className="mt-3 text-xs leading-5 text-pmri-muted">No saved reviews yet. Run diagnosis while signed in to create cloud history.</p>
      ) : null}

      <div className="mt-3 space-y-2">
        {visibleReviews.map((review) => {
          const stages = Object.keys(STAGE_LABELS).filter((stage) => Boolean(review.stages[stage as keyof typeof STAGE_LABELS]));
          return (
            <article key={review.id} className="rounded-xl border border-pmri-border/35 bg-white/[0.018] p-3">
              <p className="text-xs font-medium leading-5 text-pmri-text2">{reviewTitle(review)}</p>
              <p className="mt-1 text-[11px] leading-4 text-pmri-muted">{formatReviewDate(review.updatedAt ?? review.completedAt)} - {review.reviewId}</p>
              <div className="mt-2 flex flex-wrap gap-1">
                {stages.slice(0, 6).map((stage) => (
                  <span key={stage} className="rounded-full border border-pmri-border/35 px-2 py-0.5 text-[10px] text-pmri-muted">
                    {STAGE_LABELS[stage as keyof typeof STAGE_LABELS]}
                  </span>
                ))}
              </div>
              <button
                type="button"
                onClick={() => {
                  hydrateCloudReview(review);
                  setNotice("success", `Recovered compact cloud review ${review.reviewId}.`);
                }}
                className="pmri-focus mt-3 w-full rounded-full border border-pmri-blue/40 bg-pmri-blue/[0.09] px-3 py-1.5 text-[11px] font-medium text-pmri-blueSoft transition hover:bg-pmri-blue/[0.14]"
              >
                Recover compact state
              </button>
            </article>
          );
        })}
      </div>
    </section>
  );
}
