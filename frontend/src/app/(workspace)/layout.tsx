"use client";

import React from "react";
import { useQuery } from "@tanstack/react-query";
import styles from "./workspace.module.css";
import { apiFetch } from "@/lib/api/client";
import { CurrentUser } from "@/lib/api/types";
import { AppHeader } from "@/components/navigation/AppHeader";
import { AppSidebar } from "@/components/navigation/AppSidebar";
import { LoadingSpinner } from "@/components/feedback/LoadingSpinner";
import { AlertBanner } from "@/components/feedback/AlertBanner";

const FALLBACK_DEMO_USER: CurrentUser = {
  id: "demo-user-1",
  username: "priyanka.singh",
  email: "priyanka@bncs.local",
  role: "commercial_analyst",
  is_active: true,
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
  } = useQuery<CurrentUser>({
    queryKey: ["currentUser"],
    queryFn: () => apiFetch<CurrentUser>("/api/v1/auth/me/"),
    staleTime: 5 * 60 * 1000,
    retry: false,
  });

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
      <AppSidebar userRole={user?.role} />
      <div className={styles.contentWrapper}>
        <AppHeader user={user} />
        {isDemo && (
          <div style={{ padding: "0.75rem 2.25rem 0", maxWidth: 1440, width: "100%", margin: "0 auto" }}>
            <AlertBanner
              type="info"
              title="Frontend Demo Mode"
              message="Backend API (Django :8000) is not connected yet. Rendering authenticated workspace with synthetic session for Priyanka Singh (commercial_analyst)."
            />
          </div>
        )}
        <main className={styles.main}>{children}</main>
      </div>
    </div>
  );
}
