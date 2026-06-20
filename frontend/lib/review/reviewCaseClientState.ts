import type {
  StagedProviderStatus,
  StagedReviewStartedResponse,
  StagedReviewStatusResponse,
  StagedSafeError,
  StagedStageState
} from "@/lib/generated/api-types";

export const REVIEW_CASE_CLIENT_STATE_SCHEMA_VERSION = "review_case_client_state_v1";

export const REVIEW_CASE_STAGE_NAMES = [
  "input",
  "data_load",
  "xray",
  "stress",
  "client_fit",
  "problem_classification",
  "launchpad_builder",
  "candidate",
  "comparison",
  "verdict",
  "report"
] as const;

export type ReviewCaseStageName = typeof REVIEW_CASE_STAGE_NAMES[number];

export type ReviewCaseStageStatus = NonNullable<StagedStageState["status"]>;

export type ReviewCaseClientStageProgress = {
  stage: ReviewCaseStageName;
  order: number;
  status: ReviewCaseStageStatus;
  isCurrent: boolean;
  isReady: boolean;
  isTerminal: boolean;
  startedAt: string | null;
  completedAt: string | null;
  artifactRefs: string[];
  artifactCount: number;
};

export type ReviewCaseClientArtifactAvailability = {
  key: string;
  ref: string;
  sourceStage: ReviewCaseStageName | null;
  available: boolean;
};

export type ReviewCaseClientProgressCounts = {
  total: number;
  ready: number;
  running: number;
  blocked: number;
  failed: number;
};

export type ReviewCaseClientReadModel = {
  schemaVersion: typeof REVIEW_CASE_CLIENT_STATE_SCHEMA_VERSION;
  rawStateSchemaVersion: string;
  reviewId: string;
  status: "pending" | "running" | "completed" | "partial" | "blocked" | "failed";
  currentStage: ReviewCaseStageName;
  mode: "demo_qa" | "live";
  updatedAt: string | null;
  providerStatus?: StagedProviderStatus;
  safeError?: StagedSafeError | null;
  warnings: string[];
  stageProgress: ReviewCaseClientStageProgress[];
  artifactAvailability: ReviewCaseClientArtifactAvailability[];
  progressCounts: ReviewCaseClientProgressCounts;
  diagnosisChainReady: boolean;
  nextIncompleteStage: ReviewCaseStageName | null;
};

type StagedProgressLike = {
  schemaVersion?: string;
  schema_version?: string;
  reviewId?: string;
  review_id?: string;
  status?: string;
  currentStage?: string;
  current_stage?: string;
  mode?: string;
  updatedAt?: string | null;
  updated_at?: string | null;
  providerStatus?: StagedProviderStatus;
  provider_status?: StagedProviderStatus;
  safeError?: StagedSafeError | null;
  safe_error?: StagedSafeError | null;
  warnings?: unknown;
  stages?: unknown;
  artifacts?: unknown;
};

const REVIEW_CASE_STAGE_NAME_SET = new Set<string>(REVIEW_CASE_STAGE_NAMES);
const REVIEW_CASE_STAGE_STATUS_SET = new Set<string>([
  "pending",
  "running",
  "completed",
  "partial",
  "blocked",
  "failed",
  "skipped"
]);
const REVIEW_CASE_RUN_STATUS_SET = new Set<string>([
  "pending",
  "running",
  "completed",
  "partial",
  "blocked",
  "failed"
]);

function isRecord(value: unknown): value is Record<string, unknown> {
  return Boolean(value) && typeof value === "object" && !Array.isArray(value);
}

function stringArray(value: unknown): string[] {
  return Array.isArray(value) ? value.filter((item): item is string => typeof item === "string") : [];
}

function safeText(value: unknown, fallback = "") {
  return typeof value === "string" ? value : fallback;
}

function safeStageName(value: unknown, fallback: ReviewCaseStageName = "input"): ReviewCaseStageName {
  return typeof value === "string" && REVIEW_CASE_STAGE_NAME_SET.has(value)
    ? value as ReviewCaseStageName
    : fallback;
}

function safeRunStatus(value: unknown): ReviewCaseClientReadModel["status"] {
  return typeof value === "string" && REVIEW_CASE_RUN_STATUS_SET.has(value)
    ? value as ReviewCaseClientReadModel["status"]
    : "running";
}

function safeStageStatus(value: unknown): ReviewCaseStageStatus {
  return typeof value === "string" && REVIEW_CASE_STAGE_STATUS_SET.has(value)
    ? value as ReviewCaseStageStatus
    : "pending";
}

function isSafeClientArtifactRef(ref: string) {
  if (!ref) return false;
  if (ref.startsWith("logical://")) return true;
  if (ref.startsWith("/") || ref.startsWith("\\") || /^[A-Za-z]:[\\/]/.test(ref)) return false;
  return !ref.split(/[\\/]+/).some((part) => part === "..");
}

function cleanArtifactRefs(value: unknown): string[] {
  return stringArray(value).filter(isSafeClientArtifactRef);
}

function stageRow(value: unknown): StagedStageState {
  const row = isRecord(value) ? value : {};
  return {
    status: safeStageStatus(row.status),
    started_at: typeof row.started_at === "string" ? row.started_at : null,
    completed_at: typeof row.completed_at === "string" ? row.completed_at : null,
    artifact_refs: cleanArtifactRefs(row.artifact_refs)
  };
}

export function isReviewCaseStageReady(status: unknown) {
  return status === "completed" || status === "partial";
}

export function reviewCaseDiagnosisChainReady(progress: Pick<ReviewCaseClientReadModel, "stageProgress"> | StagedProgressLike | null | undefined) {
  const readModel = "stageProgress" in (progress ?? {})
    ? progress as Pick<ReviewCaseClientReadModel, "stageProgress">
    : progress
      ? buildReviewCaseClientReadModel(progress as StagedProgressLike)
      : null;
  const byStage = new Map((readModel?.stageProgress ?? []).map((stage) => [stage.stage, stage]));
  return ["xray", "stress", "problem_classification", "launchpad_builder"]
    .every((stage) => Boolean(byStage.get(stage as ReviewCaseStageName)?.isReady));
}

function buildStageProgress(progress: StagedProgressLike): ReviewCaseClientStageProgress[] {
  const sourceStages = isRecord(progress.stages) ? progress.stages : {};
  const currentStage = safeStageName(progress.currentStage ?? progress.current_stage);
  return REVIEW_CASE_STAGE_NAMES.map((stage, index) => {
    const row = stageRow(sourceStages[stage]);
    const status = safeStageStatus(row.status);
    return {
      stage,
      order: index,
      status,
      isCurrent: stage === currentStage,
      isReady: isReviewCaseStageReady(status),
      isTerminal: status === "completed" || status === "partial" || status === "blocked" || status === "failed" || status === "skipped",
      startedAt: row.started_at ?? null,
      completedAt: row.completed_at ?? null,
      artifactRefs: row.artifact_refs ?? [],
      artifactCount: row.artifact_refs?.length ?? 0
    };
  });
}

function buildArtifactAvailability(progress: StagedProgressLike, stageProgress: ReviewCaseClientStageProgress[]): ReviewCaseClientArtifactAvailability[] {
  const byRefStage = new Map<string, ReviewCaseStageName>();
  for (const stage of stageProgress) {
    for (const ref of stage.artifactRefs) {
      if (!byRefStage.has(ref)) byRefStage.set(ref, stage.stage);
    }
  }

  const artifacts = isRecord(progress.artifacts) ? progress.artifacts : {};
  const topLevelArtifacts = Object.entries(artifacts)
    .filter((entry): entry is [string, string] => typeof entry[1] === "string" && isSafeClientArtifactRef(entry[1]))
    .map(([key, ref]) => ({
      key,
      ref,
      sourceStage: byRefStage.get(ref) ?? null,
      available: true
    }));

  const stageArtifacts = stageProgress.flatMap((stage) => stage.artifactRefs.map((ref) => ({
    key: `${stage.stage}:${ref}`,
    ref,
    sourceStage: stage.stage,
    available: true
  })));

  const seen = new Set<string>();
  return [...topLevelArtifacts, ...stageArtifacts].filter((artifact) => {
    const identity = artifact.ref;
    if (seen.has(identity)) return false;
    seen.add(identity);
    return true;
  });
}

function progressCounts(stageProgress: ReviewCaseClientStageProgress[]): ReviewCaseClientProgressCounts {
  return {
    total: stageProgress.length,
    ready: stageProgress.filter((stage) => stage.isReady).length,
    running: stageProgress.filter((stage) => stage.status === "running").length,
    blocked: stageProgress.filter((stage) => stage.status === "blocked").length,
    failed: stageProgress.filter((stage) => stage.status === "failed").length
  };
}

export function buildReviewCaseClientReadModel(progress: StagedProgressLike): ReviewCaseClientReadModel {
  const stageProgress = buildStageProgress(progress);
  const currentStage = safeStageName(progress.currentStage ?? progress.current_stage);
  return {
    schemaVersion: REVIEW_CASE_CLIENT_STATE_SCHEMA_VERSION,
    rawStateSchemaVersion: safeText(progress.schemaVersion ?? progress.schema_version, "review_state_v1"),
    reviewId: safeText(progress.reviewId ?? progress.review_id),
    status: safeRunStatus(progress.status),
    currentStage,
    mode: progress.mode === "demo_qa" ? "demo_qa" : "live",
    updatedAt: typeof (progress.updatedAt ?? progress.updated_at) === "string" ? progress.updatedAt ?? progress.updated_at as string : null,
    providerStatus: progress.providerStatus ?? progress.provider_status,
    safeError: progress.safeError ?? progress.safe_error ?? null,
    warnings: stringArray(progress.warnings),
    stageProgress,
    artifactAvailability: buildArtifactAvailability(progress, stageProgress),
    progressCounts: progressCounts(stageProgress),
    diagnosisChainReady: reviewCaseDiagnosisChainReady({ stageProgress }),
    nextIncompleteStage: stageProgress.find((stage) => !stage.isReady)?.stage ?? null
  };
}

export function buildReviewCaseClientReadModelFromStarted(started: StagedReviewStartedResponse): ReviewCaseClientReadModel {
  const stages = Object.fromEntries(REVIEW_CASE_STAGE_NAMES.map((stage) => [
    stage,
    stageRow({ status: stage === started.current_stage ? started.status : "pending" })
  ]));
  return buildReviewCaseClientReadModel({
    schema_version: started.schema_version ?? "review_started_v1",
    review_id: started.review_id,
    status: started.status,
    current_stage: started.current_stage,
    mode: started.mode,
    safe_error: started.safe_error ?? null,
    warnings: started.warnings ?? [],
    stages
  });
}

export function buildReviewCaseClientReadModelFromStatus(status: StagedReviewStatusResponse): ReviewCaseClientReadModel {
  return buildReviewCaseClientReadModel(status);
}
