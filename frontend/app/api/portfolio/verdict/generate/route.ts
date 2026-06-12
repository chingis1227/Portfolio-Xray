import { verdictViaFastApi } from "@/lib/server/fastapiBridge";

export const runtime = "nodejs";
export const dynamic = "force-dynamic";

export async function POST(request: Request) {
  return verdictViaFastApi(request);
}
