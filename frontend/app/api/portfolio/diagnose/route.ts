import { spawn } from "node:child_process";
import { randomUUID } from "node:crypto";
import { mkdir, readFile, writeFile } from "node:fs/promises";
import path from "node:path";
import { NextResponse } from "next/server";

export const runtime = "nodejs";
export const dynamic = "force-dynamic";

const WEIGHT_TOLERANCE = 0.01;
const BRIDGE_TIMEOUT_MS = 15 * 60 * 1000;
const MAX_LOG_CHARS = 4000;

type PortfolioPayload = {
  investor_currency?: unknown;
  holdings?: unknown;
  mode?: unknown;
};

type ValidatedHolding =
  | { type: "instrument"; ticker: string; weight: number }
  | { type: "cash"; currency: string; weight: number };

type ValidatedPayload = {
  investor_currency: string;
  holdings: ValidatedHolding[];
};

function jsonError(message: string, status = 400, details: string[] = []) {
  return NextResponse.json(
    {
      status: "failed",
      error: message,
      details
    },
    { status }
  );
}

function validatePayload(body: PortfolioPayload): { payload?: ValidatedPayload; errors: string[] } {
  const errors: string[] = [];
  const investorCurrency = typeof body.investor_currency === "string"
    ? body.investor_currency.trim().toUpperCase()
    : "";

  if (!investorCurrency) {
    errors.push("investor_currency is required.");
  }

  if (!Array.isArray(body.holdings)) {
    errors.push("holdings array is required.");
    return { errors };
  }

  if (body.holdings.length < 2) {
    errors.push("At least 2 holdings are required.");
  }

  const holdings: ValidatedHolding[] = [];
  let totalWeight = 0;

  body.holdings.forEach((rawHolding, index) => {
    if (!rawHolding || typeof rawHolding !== "object" || Array.isArray(rawHolding)) {
      errors.push(`holding[${index}] must be an object.`);
      return;
    }

    const row = rawHolding as Record<string, unknown>;
    const weight = typeof row.weight === "number" && Number.isFinite(row.weight) ? row.weight : Number.NaN;

    if (!(weight > 0)) {
      errors.push(`holding[${index}].weight must be greater than 0.`);
      return;
    }

    totalWeight += weight;

    if (row.type === "instrument") {
      const ticker = typeof row.ticker === "string" ? row.ticker.trim().toUpperCase() : "";
      if (!ticker) {
        errors.push(`holding[${index}] instrument row requires ticker.`);
        return;
      }
      holdings.push({ type: "instrument", ticker, weight });
      return;
    }

    if (row.type === "cash") {
      const currency = typeof row.currency === "string" ? row.currency.trim().toUpperCase() : "";
      if (!currency) {
        errors.push(`holding[${index}] cash row requires currency.`);
        return;
      }
      holdings.push({ type: "cash", currency, weight });
      return;
    }

    errors.push(`holding[${index}].type must be "instrument" or "cash".`);
  });

  if (Math.abs(totalWeight - 100) > WEIGHT_TOLERANCE) {
    errors.push(`Total weight must equal 100 within ${WEIGHT_TOLERANCE}; got ${totalWeight}.`);
  }

  if (errors.length) {
    return { errors };
  }

  return {
    payload: {
      investor_currency: investorCurrency,
      holdings
    },
    errors
  };
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

function runBridge(payloadPath: string, root: string) {
  return new Promise<{ code: number | null; stdout: string; stderr: string; timedOut: boolean }>((resolve, reject) => {
    const pythonPath = path.join(root, ".venv", "Scripts", "python.exe");
    const scriptPath = path.join(root, "scripts", "run_review_from_payload.py");
    const child = spawn(
      pythonPath,
      [scriptPath, "--payload", payloadPath, "--mode", "diagnosis_plus_problem"],
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

function parseReviewResultJson(raw: string) {
  return JSON.parse(
    raw
      .replace(/-Infinity\b/g, "null")
      .replace(/\bNaN\b/g, "null")
      .replace(/\bInfinity\b/g, "null")
  ) as unknown;
}

export async function POST(request: Request) {
  const root = projectRoot();

  let body: PortfolioPayload;
  try {
    body = await request.json() as PortfolioPayload;
  } catch {
    return jsonError("Request body must be valid JSON.");
  }

  const { payload, errors } = validatePayload(body);
  if (!payload) {
    return jsonError("Portfolio input validation failed.", 400, errors);
  }

  const payloadDir = path.join(root, "runs", "frontend_api_payloads");
  const payloadPath = path.join(payloadDir, `portfolio_payload_${Date.now()}_${randomUUID()}.json`);

  try {
    await mkdir(payloadDir, { recursive: true });
    await writeFile(payloadPath, JSON.stringify(payload, null, 2), "utf8");
  } catch (error) {
    console.error("Failed to write frontend API payload.", error);
    return jsonError("Could not prepare portfolio diagnosis run.", 500);
  }

  let bridgeResult: Awaited<ReturnType<typeof runBridge>>;
  try {
    bridgeResult = await runBridge(payloadPath, root);
  } catch (error) {
    console.error("Failed to start portfolio diagnosis bridge.", error);
    return jsonError("Could not start portfolio diagnosis.", 500);
  }

  console.info("Portfolio diagnosis bridge finished.", {
    code: bridgeResult.code,
    timedOut: bridgeResult.timedOut,
    stdoutTail: tail(bridgeResult.stdout),
    stderrTail: tail(bridgeResult.stderr)
  });

  const reviewResultPath = resultPathFromStdout(bridgeResult.stdout, root);
  if (!reviewResultPath) {
    return jsonError("Portfolio diagnosis did not return a review result path.", 500, [
      scrubForClient(bridgeResult.stderr || bridgeResult.stdout, root)
    ]);
  }

  let reviewResult: unknown;
  try {
    reviewResult = parseReviewResultJson(await readFile(reviewResultPath, "utf8"));
  } catch (error) {
    console.error("Failed to read review_result.json.", error);
    return jsonError("Portfolio diagnosis finished but the result could not be read.", 500, [
      scrubForClient(bridgeResult.stderr || bridgeResult.stdout, root)
    ]);
  }

  if (bridgeResult.code !== 0) {
    const resultObject = reviewResult && typeof reviewResult === "object" ? reviewResult as Record<string, unknown> : {};
    return NextResponse.json(
      {
        status: "failed",
        error: typeof resultObject.error === "string" ? scrubForClient(resultObject.error, root) : "Portfolio diagnosis failed.",
        details: typeof resultObject.details === "string"
          ? scrubForClient(resultObject.details, root)
          : scrubForClient(bridgeResult.stderr || bridgeResult.stdout, root)
      },
      { status: bridgeResult.timedOut ? 504 : 500 }
    );
  }

  return NextResponse.json(reviewResult);
}
