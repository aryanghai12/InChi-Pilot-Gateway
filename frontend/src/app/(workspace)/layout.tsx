"use client";

import React, { useEffect } from "react";
import { useQuery } from "@tanstack/react-query";
import styles from "./workspace.module.css";
import { apiFetch } from "@/lib/api/client";
import { CurrentUser, ApiError } from "@/lib/api/types";
import { AppHeader } from "@/components/navigation/AppHeader";
import { AppSidebar } from "@/components/navigation/AppSidebar";
import { LoadingSpinner } from "@/components/feedback/LoadingSpinner";
import { AlertBanner } from "@/components/feedback/AlertBanner";

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
    isError,
    error,
  } = useQuery<CurrentUser>({
    queryKey: ["currentUser"],
    queryFn: () => apiFetch<CurrentUser>("/api/v1/auth/me/"),
    staleTime: 5 * 60 * 1000,
    retry: false,
  });

  const isUnauthorized =
    error instanceof ApiError
      ? error.status === 401
      : error && typeof error === "object" && "status" in error
      ? (error as { status: unknown }).status === 401
      : false;

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

  const isDemo = isError || !fetchedUser;
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
        {isDemo && (
          <div style={{ padding: "0.75rem 2.25rem 0", maxWidth: 1440, width: "100%", margin: "0 auto" }}>
            <AlertBanner
              type="info"
              title="Frontend Standalone Mode"
              message="Django backend (:8000) not connected. Workspace previewing with session for Priyanka Singh (commercial_analyst)."
            />
          </div>
        )}
        <main className={styles.main}>{children}</main>
      </div>
    </div>
  );
}
