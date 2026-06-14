import { recoverViaFastApi } from "@/lib/server/fastapiBridge";

export const runtime = "edge";
export const dynamic = "force-dynamic";

type RecoverRequest = {
  review_id?: unknown;
};

export async function GET(request: Request) {
  const url = new URL(request.url);
  return recoverViaFastApi(url.searchParams.get("review_id"));
}

export async function POST(request: Request) {
  let body: RecoverRequest;
  try {
    body = await request.json() as RecoverRequest;
  } catch {
    return recoverViaFastApi(undefined);
  }

  return recoverViaFastApi(body.review_id);
}
