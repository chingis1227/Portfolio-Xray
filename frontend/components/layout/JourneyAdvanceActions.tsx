"use client";

import { useRouter } from "next/navigation";
import { useReviewState } from "@/lib/reviewState";

export function CandidateReadyAction() {
  const router = useRouter();
  const { markCandidateReady } = useReviewState();

  return (
    <button
      type="button"
      className="pmri-focus rounded-full border border-pmri-blue/50 bg-pmri-blue px-5 py-2.5 text-sm font-medium text-pmri-bg shadow-decision transition hover:bg-pmri-blueSoft"
      onClick={() => {
        markCandidateReady();
        router.push("/comparison");
      }}
    >
      Compare test candidate
    </button>
  );
}

export function ComparisonReadyAction() {
  const router = useRouter();
  const { markComparisonReady } = useReviewState();

  return (
    <button
      type="button"
      className="pmri-focus rounded-full border border-pmri-blue/50 bg-pmri-blue px-5 py-2.5 text-sm font-medium text-pmri-bg shadow-decision transition hover:bg-pmri-blueSoft"
      onClick={() => {
        markComparisonReady();
        router.push("/verdict");
      }}
    >
      Generate verdict
    </button>
  );
}

export function VerdictReadyAction() {
  const router = useRouter();
  const { markVerdictReady } = useReviewState();

  return (
    <button
      type="button"
      className="pmri-focus rounded-full border border-pmri-blue/50 bg-pmri-blue px-5 py-2.5 text-sm font-medium text-pmri-bg shadow-decision transition hover:bg-pmri-blueSoft"
      onClick={() => {
        markVerdictReady();
        router.push("/report");
      }}
    >
      Open report
    </button>
  );
}
