"use client";

import React from "react";
import { useQuery } from "@tanstack/react-query";
import { apiFetch } from "@/lib/api/client";
import { unwrapPaginated, ApiError, PaginatedResponse } from "@/lib/api/types";
import { EmptyState } from "@/components/feedback/EmptyState";
import { LoadingSpinner } from "@/components/feedback/LoadingSpinner";

export default function AuditPage() {
  const { isLoading } = useQuery<unknown[] | null>({
    queryKey: ["auditEvents"],
    queryFn: async () => {
      try {
        const res = await apiFetch<unknown[] | PaginatedResponse<unknown>>("/api/v1/audit/events/");
        return unwrapPaginated(res);
      } catch (err) {
        if (err instanceof ApiError && err.status === 404) {
          return null;
        }
        throw err;
      }
    },
    staleTime: 30 * 1000,
    retry: false,
  });

  return (
    <div>
      <div style={{ marginBottom: "1.5rem" }}>
        <h1 style={{ fontSize: "1.75rem", fontWeight: 700, color: "var(--color-text-main)" }}>
          Audit History & Verification
        </h1>
        <p style={{ color: "var(--color-text-muted)", fontSize: "0.9375rem" }}>
          Immutable log of material actions, dispositions, state transitions and user events.
        </p>
      </div>

      {isLoading ? (
        <div style={{ padding: "3rem", display: "flex", justifyContent: "center" }}>
          <LoadingSpinner label="Loading audit history..." />
        </div>
      ) : (
        <EmptyState
          title="No Audit Records"
          guidance="All material creations, updates, reviews, and decisions produce an immutable audit event automatically."
        />
      )}
    </div>
  );
}
