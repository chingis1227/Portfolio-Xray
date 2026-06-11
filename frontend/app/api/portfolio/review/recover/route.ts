import { readFile } from "node:fs/promises";
import path from "node:path";
import { NextResponse } from "next/server";

export const runtime = "nodejs";
export const dynamic = "force-dynamic";

type RecoverRequest = {
  review_id?: unknown;
};

function jsonError(message: string, status = 400, details: string[] | string = []) {
  return NextResponse.json(
    {
      status: "failed",
      error: message,
      details
    },
    { status }
  );
}

function projectRoot() {
  return path.resolve(process.cwd(), "..");
}

function validateReviewId(value: unknown) {
  const reviewId = typeof value === "string" ? value.trim() : "";
  const errors: string[] = [];

  if (!reviewId) errors.push("review_id is required.");
  if (reviewId && !reviewId.startsWith("frontend_review_")) {
    errors.push("review_id must be a frontend_review_* id.");
  }
  if (reviewId && path.basename(reviewId) !== reviewId) {
    errors.push("review_id must not contain path separators.");
  }

  return { reviewId, errors };
}

function runLocalReviewResultPath(root: string, reviewId: string) {
  const runsRoot = path.resolve(root, "runs");
  const runDir = path.resolve(runsRoot, reviewId);
  const resultPath = path.resolve(runDir, "review_result.json");

  if (path.relative(runsRoot, runDir).startsWith("..") || path.relative(runsRoot, resultPath).startsWith("..")) {
    return null;
  }

  return resultPath;
}

function parseReviewResultJson(raw: string) {
  return JSON.parse(
    raw
      .replace(/-Infinity\b/g, "null")
      .replace(/\bNaN\b/g, "null")
      .replace(/\bInfinity\b/g, "null")
  ) as unknown;
}

function isRecord(value: unknown): value is Record<string, unknown> {
  return Boolean(value) && typeof value === "object" && !Array.isArray(value);
}

function sanitizeRecoveredReviewResult(value: unknown, reviewId: string) {
  if (!isRecord(value)) return null;
  if (value.review_id !== reviewId || value.status !== "completed") return null;

  const outputs = isRecord(value.outputs) ? value.outputs : {};
  const allowedOutputs = Object.fromEntries(
    Object.entries(outputs).filter(([key]) => [
      "portfolio_xray",
      "stress_report",
      "run_metadata",
      "output_manifest",
      "problem_classification",
      "candidate_launchpad",
      "portfolio_alternatives_builder",
      "ai_commentary_context",
      "site_explanation_bundle"
    ].includes(key))
  );

  const paths = isRecord(value.paths) ? value.paths : {};
  const allowedPaths = Object.fromEntries(
    Object.entries(paths).filter(([key, item]) => (
      typeof item === "string"
      && [
        "run_dir",
        "portfolio_xray",
        "stress_report",
        "run_metadata",
        "output_manifest",
        "problem_classification",
        "candidate_launchpad",
        "portfolio_alternatives_builder",
        "ai_commentary_context",
        "site_explanation_bundle"
      ].includes(key)
    ))
  );

  return {
    ...value,
    paths: allowedPaths,
    outputs: allowedOutputs
  };
}

async function recover(reviewId: string) {
  const root = projectRoot();
  const resultPath = runLocalReviewResultPath(root, reviewId);
  if (!resultPath) {
    return jsonError("Review recovery request validation failed.", 400, ["review_id must stay inside the runs directory."]);
  }

  let reviewResult: unknown;
  try {
    reviewResult = parseReviewResultJson(await readFile(resultPath, "utf8"));
  } catch {
    return jsonError("No recoverable run-local review_result.json was found for this review_id.", 404);
  }

  const sanitized = sanitizeRecoveredReviewResult(reviewResult, reviewId);
  if (!sanitized) {
    return jsonError("Run-local review_result.json is not a completed matching frontend review.", 409);
  }

  return NextResponse.json({
    status: "completed",
    stage: "review_recovery",
    review_id: reviewId,
    recovery: {
      source: "run_local_review_result",
      restored_active_stages: ["diagnosis", "evidence", "hypothesis_setup"],
      downstream_artifacts_restored_as_active: false,
      note: "Candidate, comparison, verdict, and report artifacts are not restored as active state during recovery."
    },
    review_result: sanitized
  });
}

export async function GET(request: Request) {
  const url = new URL(request.url);
  const { reviewId, errors } = validateReviewId(url.searchParams.get("review_id"));
  if (errors.length) {
    return jsonError("Review recovery request validation failed.", 400, errors);
  }
  return recover(reviewId);
}

export async function POST(request: Request) {
  let body: RecoverRequest;
  try {
    body = await request.json() as RecoverRequest;
  } catch {
    return jsonError("Request body must be valid JSON.");
  }

  const { reviewId, errors } = validateReviewId(body.review_id);
  if (errors.length) {
    return jsonError("Review recovery request validation failed.", 400, errors);
  }

  return recover(reviewId);
}
