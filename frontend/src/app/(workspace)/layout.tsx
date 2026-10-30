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
import { Button } from "@/components/forms/Button";

export default function WorkspaceLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  const {
    data: user,
    isLoading,
    isError,
    error,
    refetch,
  } = useQuery<CurrentUser>({
    queryKey: ["currentUser"],
    queryFn: () => apiFetch<CurrentUser>("/api/v1/auth/me/"),
    staleTime: 5 * 60 * 1000,
  });

  if (isLoading) {
    return (
      <div className={styles.centerLoading}>
        <LoadingSpinner label="Authenticating session..." />
      </div>
    );
  }

  if (isError) {
    return (
      <div className={styles.centerLoading}>
        <div style={{ maxWidth: 500, padding: "2rem" }}>
          <AlertBanner
            type="error"
            title="Session Error"
            message={
              error instanceof Error
                ? error.message
                : "Failed to establish authenticated session with backend."
            }
          />
          <Button variant="primary" onClick={() => refetch()}>
            Retry
          </Button>
        </div>
      </div>
    );
  }

  return (
    <div className={styles.workspaceRoot}>
      <AppHeader user={user} />
      <div className={styles.layoutBody}>
        <AppSidebar userRole={user?.role} />
        <main className={styles.mainContent}>{children}</main>
      </div>
    </div>
  );
}
