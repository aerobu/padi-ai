import { NextRequest, NextResponse } from 'next/server';

/**
 * Auth0 Login Route
 * Redirects the user to Auth0 for authentication
 */
export async function GET(request: NextRequest) {
  const origin = request.headers.get('origin') || 'http://localhost:3000';
  const returnTo = `${origin}/dashboard`;

  // Get Auth0 configuration from environment
  const domain = process.env.NEXT_PUBLIC_AUTH0_DOMAIN;
  const clientId = process.env.NEXT_PUBLIC_AUTH0_CLIENT_ID;
  const audience = process.env.NEXT_PUBLIC_AUTH0_AUDIENCE;

  if (!domain || !clientId) {
    return NextResponse.json(
      { error: 'Auth0 configuration not set' },
      { status: 500 }
    );
  }

  // Build Auth0 authorization URL
  const authParams = new URLSearchParams({
    response_type: 'code',
    client_id: clientId,
    redirect_uri: `${origin}/api/auth/callback`,
    scope: 'openid profile email',
    audience: audience || '',
    state: returnTo,
    connection: 'password', // Use password connection for email/password auth
  });

  const authUrl = `${domain}/authorize?${authParams.toString()}`;

  return NextResponse.redirect(authUrl);
}
