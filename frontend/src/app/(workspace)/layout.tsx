"use client";

import React, { useEffect } from "react";
import { useQuery } from "@tanstack/react-query";
import styles from "./workspace.module.css";
import { apiFetch } from "@/lib/api/client";
import { CurrentUser } from "@/lib/api/types";
import { AppHeader } from "@/components/navigation/AppHeader";
import { AppSidebar } from "@/components/navigation/AppSidebar";
import { LoadingSpinner } from "@/components/feedback/LoadingSpinner";

const FALLBACK_DEMO_USER: CurrentUser = {
  id: "demo-user-1",
  email: "priyanka@bncs.local",
  first_name: "Priyanka",
  last_name: "Singh",
  role: "commercial_analyst",
  role_display: "Commercial Analyst",
  is_active: true,
  is_verified: true,
  is_staff: false,
};

export default function WorkspaceLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  const {
    data: fetchedUser,
    isLoading,
    error,
  } = useQuery<CurrentUser>({
    queryKey: ["currentUser"],
    queryFn: async () => {
      try {
        return await apiFetch<CurrentUser>("/api/v1/auth/me/");
      } catch (err) {
        if (
          process.env.NEXT_PUBLIC_DEMO_MODE === "true" ||
          (typeof document !== "undefined" && document.cookie.includes("sessionid=demo-session"))
        ) {
          return FALLBACK_DEMO_USER;
        }
        throw err;
      }
    },
    staleTime: 5 * 60 * 1000,
    retry: false,
  });

  // In standard environments and automated smoke tests (CI/Playwright), any failure
  // to fetch an authenticated user session (401, connection refused, 502 proxy error, or lack of session)
  // indicates an unauthenticated visitor that must be redirected to /login?next=<path>.
  // In demo sessions or demo mode, fallback to synthetic persona without redirecting.
  const isDemoCookie =
    typeof document !== "undefined" && document.cookie.includes("sessionid=demo-session");
  const isDemoMode = process.env.NEXT_PUBLIC_DEMO_MODE === "true" || isDemoCookie;
  const isUnauthorized = !isDemoMode && (Boolean(error) || (!isLoading && !fetchedUser));

  useEffect(() => {
    if (isUnauthorized) {
      if (typeof window !== "undefined" && !window.location.pathname.startsWith("/login")) {
        const returnUrl = encodeURIComponent(window.location.pathname + window.location.search);
        // eslint-disable-next-line @next/next/no-location-assign-relative-destination
        window.location.href = `/login?next=${returnUrl}`;
      }
    }
  }, [isUnauthorized]);

  if (isUnauthorized) {
    return (
      <div className={styles.centerLoading}>
        <LoadingSpinner label="Redirecting to login..." />
      </div>
    );
  }

  const user = fetchedUser || FALLBACK_DEMO_USER;

  if (isLoading) {
    return (
      <div className={styles.centerLoading}>
        <LoadingSpinner label="Connecting to workspace..." />
      </div>
    );
  }

  return (
    <div className={styles.container}>
      <AppSidebar user={user} userRole={user?.role} />
      <div className={styles.contentWrapper}>
        <AppHeader user={user} />
        <main className={styles.main}>{children}</main>
      </div>
    </div>
  );
}
