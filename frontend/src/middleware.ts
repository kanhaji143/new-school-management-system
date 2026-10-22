import { NextResponse } from "next/server";
import type { NextRequest } from "next/server";

/**
 * Lightweight route protection.
 *
 * The authoritative auth check happens on the server (DRF). Here we only
 * redirect to /login when the auth cookie is absent. The dashboard layout
 * additionally guards against hydration flash and handles the real token state.
 *
 * Note: the access/refresh tokens live in the persisted Zustand store
 * (localStorage). Middleware runs on the edge and cannot read localStorage,
 * so we mirror "logged in" into a non-HttpOnly cookie on login.
 */
export function middleware(request: NextRequest) {
  const { pathname } = request.nextUrl;
  const hasAuth = request.cookies.get("smart-school-auth")?.value;

  if (pathname.startsWith("/login") || pathname.startsWith("/register")) {
    return NextResponse.next();
  }
  if (!hasAuth) {
    const loginUrl = new URL("/login", request.url);
    return NextResponse.redirect(loginUrl);
  }
  return NextResponse.next();
}

export const config = {
  matcher: ["/dashboard/:path*", "/parent/:path*", "/students/:path*", "/timetable/:path*", "/"],
};
