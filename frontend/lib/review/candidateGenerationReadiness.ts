export type CandidateGenerationReadinessInput = {
  status?: string | null;
  generationStatus?: string | null;
  canCompare?: boolean | null;
};

export function isCompareReadyCandidateGeneration(value: CandidateGenerationReadinessInput | null | undefined): boolean {
  return Boolean(
    value
    && value.status === "completed"
    && value.generationStatus === "generated"
    && value.canCompare === true
  );
}
