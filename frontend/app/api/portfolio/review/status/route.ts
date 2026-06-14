import { stagedReviewStatusViaFastApi } from "@/lib/server/fastapiBridge";

export const runtime = "nodejs";
export const dynamic = "force-dynamic";

export async function GET(request: Request) {
  const url = new URL(request.url);
  return stagedReviewStatusViaFastApi(url.searchParams.get("reviewId") ?? url.searchParams.get("review_id"));
}
