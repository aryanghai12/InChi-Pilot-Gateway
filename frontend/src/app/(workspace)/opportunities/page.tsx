"use client";

import React from "react";
import { useQuery } from "@tanstack/react-query";
import { apiFetch } from "@/lib/api/client";
import { unwrapPaginated, ApiError } from "@/lib/api/types";
import { EmptyState } from "@/components/feedback/EmptyState";
import { AlertBanner } from "@/components/feedback/AlertBanner";
import { LoadingSpinner } from "@/components/feedback/LoadingSpinner";

export default function OpportunitiesPage() {
  const { data: opportunities, isLoading, error } = useQuery<any[]>({
    queryKey: ["opportunities"],
    queryFn: async () => {
      try {
        const res = await apiFetch<any>("/api/v1/opportunities/");
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

  const isUnderConstruction = opportunities === null || (error instanceof ApiError && error.status === 404);

  return (
    <div>
      <div style={{ marginBottom: "1.5rem" }}>
        <h1 style={{ fontSize: "1.75rem", fontWeight: 700, color: "var(--color-text-main)" }}>
          Commercial Opportunities Pipeline
        </h1>
        <p style={{ color: "var(--color-text-muted)", fontSize: "0.9375rem" }}>
          Track progression of accepted matches through commercial stages with activity history.
        </p>
      </div>

      {isUnderConstruction && (
        <div style={{ marginBottom: "1.5rem" }}>
          <AlertBanner
            type="info"
            title="Feature Under Backend Construction"
            message="The Commercial Opportunities service (/api/v1/opportunities/) is currently under backend development. Opportunities generated from accepted candidate matches will automatically synchronize here once deployed."
          />
        </div>
      )}

      {isLoading ? (
        <div style={{ padding: "3rem", display: "flex", justifyContent: "center" }}>
          <LoadingSpinner label="Loading commercial pipeline..." />
        </div>
      ) : (
        <EmptyState
          title="No Commercial Opportunities"
          guidance="Opportunities are generated exclusively from accepted candidate dispositions in a matching run."
        />
      )}
    </div>
  );
}
