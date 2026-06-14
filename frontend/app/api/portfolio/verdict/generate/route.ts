import { verdictViaFastApi } from "@/lib/server/fastapiBridge";

export const runtime = "edge";
export const dynamic = "force-dynamic";

export async function POST(request: Request) {
  return verdictViaFastApi(request);
}
