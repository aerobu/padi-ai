/**
 * GET /api/auth/token — return the current user's access token to the SPA.
 *
 * The token lives in an httpOnly cookie set by the Auth0 callback. This
 * handler exposes only the value to same-origin requests so that fetch
 * code in client components can attach Authorization headers without
 * giving JS direct cookie access.
 */

import { NextResponse } from "next/server";
import { cookies } from "next/headers";
import { ACCESS_TOKEN_COOKIE } from "@/lib/auth-token";

export async function GET() {
  const cookieStore = await cookies();
  const token = cookieStore.get(ACCESS_TOKEN_COOKIE)?.value ?? null;
  return NextResponse.json({ access_token: token });
}
