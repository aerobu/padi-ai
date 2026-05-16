import { NextRequest, NextResponse } from 'next/server';
import { ACCESS_TOKEN_COOKIE } from '@/lib/auth-token';

/**
 * Auth0 Callback Route
 * Handles the OAuth callback from Auth0
 */
export async function GET(request: NextRequest) {
  const origin =
    request.headers.get("origin") ?? new URL(request.url).origin;
  const url = new URL(request.url);
  const searchParams = url.searchParams;
  const code = searchParams.get('code');
  const state = searchParams.get('state');
  const error = searchParams.get('error');

  if (error) {
    // Handle authentication error
    return NextResponse.redirect(`${origin}/login?error=${error}`);
  }

  if (!code) {
    return NextResponse.redirect(`${origin}/login?error=missing_code`);
  }

  // Resolve returnTo as an absolute URL and guard against open-redirect.
  // If state is a full URL on our own origin, use it directly.
  // If state is a relative path, resolve it against our origin.
  // Any off-origin or malformed state falls back to /dashboard.
  let returnTo: string;
  if (state) {
    try {
      const stateUrl = new URL(state, origin);
      // Only allow redirects to our own origin (same-origin redirect guard).
      returnTo = stateUrl.origin === origin ? stateUrl.toString() : `${origin}/dashboard`;
    } catch {
      returnTo = `${origin}/dashboard`;
    }
  } else {
    returnTo = `${origin}/dashboard`;
  }

  // Exchange code for token
  try {
    const domain = process.env.NEXT_PUBLIC_AUTH0_DOMAIN;
    const clientId = process.env.NEXT_PUBLIC_AUTH0_CLIENT_ID;
    const clientSecret = process.env.AUTH0_CLIENT_SECRET;

    if (!domain || !clientId || !clientSecret) {
      throw new Error('Auth0 configuration missing');
    }

    const tokenResponse = await fetch(`${domain}/oauth/token`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/x-www-form-urlencoded',
      },
      body: new URLSearchParams({
        grant_type: 'authorization_code',
        client_id: clientId,
        client_secret: clientSecret,
        redirect_uri: `${origin}/api/auth/callback`,
        code,
      }),
    });

    if (!tokenResponse.ok) {
      throw new Error('Failed to exchange code for token');
    }

    const tokenData = await tokenResponse.json();

    // Store the access token in an httpOnly cookie. The /api/auth/token
    // route handler exposes it to client components so apiClient can attach
    // an Authorization: Bearer header (fix C-11).
    const response = NextResponse.redirect(returnTo);
    const cookieOpts = {
      httpOnly: true,
      secure: process.env.NODE_ENV === 'production',
      sameSite: 'lax' as const,
      maxAge: 86400, // 24h
      path: '/',
    };
    response.cookies.set(ACCESS_TOKEN_COOKIE, tokenData.access_token, cookieOpts);
    // Back-compat for any code still reading 'auth_token'.
    response.cookies.set('auth_token', tokenData.access_token, cookieOpts);

    return response;
  } catch (err) {
    console.error('Auth callback error:', err);
    return NextResponse.redirect(`${origin}/login?error=exchange_failed`);
  }
}
