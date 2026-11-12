"use client";

import React from "react";
import { useQuery } from "@tanstack/react-query";
import { apiFetch } from "@/lib/api/client";
import { unwrapPaginated, ApiError } from "@/lib/api/types";
import { EmptyState } from "@/components/feedback/EmptyState";
import { AlertBanner } from "@/components/feedback/AlertBanner";
import { LoadingSpinner } from "@/components/feedback/LoadingSpinner";

export default function AuditPage() {
  const { data: auditEvents, isLoading, error } = useQuery<any[]>({
    queryKey: ["auditEvents"],
    queryFn: async () => {
      try {
        const res = await apiFetch<any>("/api/v1/audit/events/");
        return unwrapPaginated(res);
      } catch (err) {
        if (err instanceof ApiError && err.status === 404) {
          return null as any;
        }
        throw err;
      }
    },
    staleTime: 30 * 1000,
    retry: false,
  });

  const isUnderConstruction = auditEvents === null || (error instanceof ApiError && error.status === 404);

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

      {isUnderConstruction && (
        <div style={{ marginBottom: "1.5rem" }}>
          <AlertBanner
            type="info"
            title="Feature Under Backend Construction"
            message="The Immutable Audit Log service (/api/v1/audit/events/) is currently under backend development. State transitions, reviewer decisions, and material exports will be recorded and cryptographically verifiable here once the endpoint is mounted."
          />
        </div>
      )}

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
