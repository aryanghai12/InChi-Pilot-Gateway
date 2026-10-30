import type { NextConfig } from "next";

const BACKEND_ORIGIN = process.env.BACKEND_ORIGIN || "http://localhost:8000";
const ADMIN_URL_PATH = (process.env.ADMIN_URL_PATH || "admin").replace(/^\/+|\/+$/g, "");
const DJANGO_STATIC_PREFIX = (process.env.DJANGO_STATIC_PREFIX || "static").replace(/^\/+|\/+$/g, "");

const nextConfig: NextConfig = {
  output: "standalone",
  reactStrictMode: true,

  // Single-origin proxy rewrites to Django backend (ARCHITECTURE.md TD-09, §5, §7)
  async rewrites() {
    return [
      {
        source: "/api/:path*",
        destination: `${BACKEND_ORIGIN}/api/:path*`,
      },
      {
        source: `/${ADMIN_URL_PATH}`,
        destination: `${BACKEND_ORIGIN}/${ADMIN_URL_PATH}/`,
      },
      {
        source: `/${ADMIN_URL_PATH}/:path*`,
        destination: `${BACKEND_ORIGIN}/${ADMIN_URL_PATH}/:path*`,
      },
      {
        source: `/${DJANGO_STATIC_PREFIX}/:path*`,
        destination: `${BACKEND_ORIGIN}/${DJANGO_STATIC_PREFIX}/:path*`,
      },
    ];
  },

  // Client-side security headers (ARCHITECTURE.md §7)
  async headers() {
    return [
      {
        source: "/:path*",
        headers: [
          {
            key: "X-Content-Type-Options",
            value: "nosniff",
          },
          {
            key: "X-Frame-Options",
            value: "DENY",
          },
          {
            key: "Referrer-Policy",
            value: "strict-origin-when-cross-origin",
          },
          {
            key: "Permissions-Policy",
            value: "camera=(), microphone=(), geolocation=()",
          },
        ],
      },
    ];
  },
};

export default nextConfig;
