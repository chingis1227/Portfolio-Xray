import { spawn } from "node:child_process";
import { readFile } from "node:fs/promises";
import path from "node:path";
import { NextResponse } from "next/server";
import { resolvePythonExecutable } from "@/lib/server/pythonBridge";

export const runtime = "nodejs";
export const dynamic = "force-dynamic";

const BRIDGE_TIMEOUT_MS = 15 * 60 * 1000;
const MAX_LOG_CHARS = 4000;

type CandidateRequest = {
  review_id?: unknown;
  selected_card_id?: unknown;
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

function tail(value: string) {
  return value.length > MAX_LOG_CHARS ? value.slice(-MAX_LOG_CHARS) : value;
}

function scrubForClient(value: string, root: string) {
  if (!value) return "";
  return tail(value)
    .replaceAll(root, "[project]")
    .replaceAll(root.replaceAll("\\", "/"), "[project]")
    .replace(/Traceback \(most recent call last\):[\s\S]*/g, "Backend failure details were captured safely.")
    .replace(/File "[^"]+", line \d+(?:, in [^\r\n]+)?/g, "Backend file reference hidden.")
    .replace(/[A-Za-z]:[\\/][^\s'")<>]+/g, "[path]")
    .replace(/\/(?:Users|home|var|tmp|mnt)\/[^\s'")<>]+/g, "[path]")
    .trim();
}

function validateRequest(body: CandidateRequest) {
  const reviewId = typeof body.review_id === "string" ? body.review_id.trim() : "";
  const selectedCardId = typeof body.selected_card_id === "string" ? body.selected_card_id.trim() : "";
  const errors: string[] = [];

  if (!reviewId) errors.push("review_id is required.");
  if (!selectedCardId) errors.push("selected_card_id is required.");
  if (reviewId && !reviewId.startsWith("frontend_review_")) {
    errors.push("review_id must be a frontend_review_* id.");
  }
  if (reviewId && path.basename(reviewId) !== reviewId) {
    errors.push("review_id must not contain path separators.");
  }

  return { reviewId, selectedCardId, errors };
}

function runBridge(reviewId: string, selectedCardId: string, root: string) {
  return new Promise<{ code: number | null; stdout: string; stderr: string; timedOut: boolean }>((resolve, reject) => {
    const pythonPath = resolvePythonExecutable(root);
    const scriptPath = path.join(root, "scripts", "run_review_from_payload.py");
    const child = spawn(
      pythonPath,
      [
        scriptPath,
        "--generate-candidate",
        "--review-id",
        reviewId,
        "--selected-card-id",
        selectedCardId
      ],
      {
        cwd: root,
        shell: false,
        windowsHide: true
      }
    );

    let stdout = "";
    let stderr = "";
    let settled = false;

    const timeout = setTimeout(() => {
      child.kill();
      settled = true;
      resolve({ code: 124, stdout, stderr, timedOut: true });
    }, BRIDGE_TIMEOUT_MS);

    child.stdout.setEncoding("utf8");
    child.stderr.setEncoding("utf8");
    child.stdout.on("data", (chunk) => {
      stdout += String(chunk);
    });
    child.stderr.on("data", (chunk) => {
      stderr += String(chunk);
    });
    child.on("error", (error) => {
      clearTimeout(timeout);
      if (!settled) {
        settled = true;
        reject(error);
      }
    });
    child.on("close", (code) => {
      clearTimeout(timeout);
      if (!settled) {
        settled = true;
        resolve({ code, stdout, stderr, timedOut: false });
      }
    });
  });
}

function resultPathFromStdout(stdout: string, root: string) {
  const lastLine = stdout
    .split(/\r?\n/)
    .map((line) => line.trim())
    .filter(Boolean)
    .at(-1);

  if (!lastLine) return null;
  return path.isAbsolute(lastLine) ? lastLine : path.resolve(root, lastLine);
}

function parseBridgeJson(raw: string) {
  return JSON.parse(
    raw
      .replace(/-Infinity\b/g, "null")
      .replace(/\bNaN\b/g, "null")
      .replace(/\bInfinity\b/g, "null")
  ) as unknown;
}

export async function POST(request: Request) {
  const root = projectRoot();

  let body: CandidateRequest;
  try {
    body = await request.json() as CandidateRequest;
  } catch {
    return jsonError("Request body must be valid JSON.");
  }

  const { reviewId, selectedCardId, errors } = validateRequest(body);
  if (errors.length) {
    return jsonError("Candidate generation request validation failed.", 400, errors);
  }

  let bridgeResult: Awaited<ReturnType<typeof runBridge>>;
  try {
    bridgeResult = await runBridge(reviewId, selectedCardId, root);
  } catch (error) {
    console.error("Failed to start candidate generation bridge.", error);
    return jsonError("Could not start candidate generation.", 500);
  }

  console.info("Candidate generation bridge finished.", {
    code: bridgeResult.code,
    timedOut: bridgeResult.timedOut,
    stdoutTail: tail(bridgeResult.stdout),
    stderrTail: tail(bridgeResult.stderr)
  });

  const resultPath = resultPathFromStdout(bridgeResult.stdout, root);
  if (!resultPath) {
    return jsonError("Candidate generation did not return a result path.", 500, [
      scrubForClient(bridgeResult.stderr || bridgeResult.stdout, root)
    ]);
  }

  let result: unknown;
  try {
    result = parseBridgeJson(await readFile(resultPath, "utf8"));
  } catch (error) {
    console.error("Failed to read candidate_generation_result.json.", error);
    return jsonError("Candidate generation finished but the result could not be read.", 500, [
      scrubForClient(bridgeResult.stderr || bridgeResult.stdout, root)
    ]);
  }

  if (bridgeResult.code !== 0) {
    const resultObject = result && typeof result === "object" ? result as Record<string, unknown> : {};
    return NextResponse.json(
      {
        status: "failed",
        stage: "candidate_generation",
        review_id: reviewId,
        selected_card_id: selectedCardId,
        error: typeof resultObject.error === "string" ? scrubForClient(resultObject.error, root) : "Candidate generation failed.",
        details: typeof resultObject.details === "string"
          ? scrubForClient(resultObject.details, root)
          : scrubForClient(bridgeResult.stderr || bridgeResult.stdout, root)
      },
      { status: bridgeResult.timedOut ? 504 : 500 }
    );
  }

  return NextResponse.json(result);
}
