import { NextResponse } from "next/server";
import type { NextRequest } from "next/server";

const PROTECTED_PREFIXES = [
  "/dashboard",
  "/suppliers",
  "/products",
  "/readiness",
  "/requirements",
  "/matching",
  "/opportunities",
  "/audit",
];

export function middleware(request: NextRequest) {
  const { pathname } = request.nextUrl;

  const isProtected = PROTECTED_PREFIXES.some(
    (prefix) => pathname === prefix || pathname.startsWith(`${prefix}/`)
  );

  if (isProtected) {
    const sessionCookie = request.cookies.get("sessionid");
    if (!sessionCookie || !sessionCookie.value) {
      const returnUrl = encodeURIComponent(pathname + request.nextUrl.search);
      const loginUrl = new URL(`/login?next=${returnUrl}`, request.url);
      return NextResponse.redirect(loginUrl);
    }
  }

  return NextResponse.next();
}

export const config = {
  matcher: [
    "/dashboard/:path*",
    "/suppliers/:path*",
    "/products/:path*",
    "/readiness/:path*",
    "/requirements/:path*",
    "/matching/:path*",
    "/opportunities/:path*",
    "/audit/:path*",
  ],
};
