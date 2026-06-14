import { NextResponse, type NextRequest } from "next/server";
import { createSupabaseServerClient } from "@/lib/supabase/server";

export const runtime = "edge";

function redirectWithStatus(request: NextRequest, status: "success" | "disabled" | "error", message?: string) {
  const url = request.nextUrl.clone();
  url.pathname = "/onboarding/name";
  url.searchParams.set("auth", status);
  if (message) url.searchParams.set("auth_message", message);
  return NextResponse.redirect(url);
}

export async function GET(request: NextRequest) {
  const code = request.nextUrl.searchParams.get("code");
  const supabase = createSupabaseServerClient();

  if (!supabase) {
    return redirectWithStatus(request, "disabled", "Supabase is not configured.");
  }

  if (!code) {
    return redirectWithStatus(request, "error", "Missing Supabase auth code.");
  }

  const { error } = await supabase.auth.exchangeCodeForSession(code);
  if (error) {
    return redirectWithStatus(request, "error", error.message);
  }

  return redirectWithStatus(request, "success");
}
