"use client";

import React from "react";
import { useQuery } from "@tanstack/react-query";
import { apiFetch } from "@/lib/api/client";
import { unwrapPaginated, ApiError } from "@/lib/api/types";
import { EmptyState } from "@/components/feedback/EmptyState";
import { AlertBanner } from "@/components/feedback/AlertBanner";
import { LoadingSpinner } from "@/components/feedback/LoadingSpinner";

export default function MatchingPage() {
  const { data: runs, isLoading, error } = useQuery<any[]>({
    queryKey: ["matchingRuns"],
    queryFn: async () => {
      try {
        const res = await apiFetch<any>("/api/v1/matching/runs/");
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

  const isUnderConstruction = runs === null || (error instanceof ApiError && error.status === 404);

  return (
    <div>
      <div style={{ marginBottom: "1.5rem" }}>
        <h1 style={{ fontSize: "1.75rem", fontWeight: 700, color: "var(--color-text-main)" }}>
          Explainable Matching Engine
        </h1>
        <p style={{ color: "var(--color-text-muted)", fontSize: "0.9375rem" }}>
          Deterministic rule-based eligibility filtering, weighted scoring, and bounded semantic similarity signals.
        </p>
      </div>

      {isUnderConstruction && (
        <div style={{ marginBottom: "1.5rem" }}>
          <AlertBanner
            type="info"
            title="Feature Under Backend Construction"
            message="The Matching Engine service (/api/v1/matching/runs/) is currently under backend development. Automated eligibility evaluations and candidate matches will display here once the service is online."
          />
        </div>
      )}

      {isLoading ? (
        <div style={{ padding: "3rem", display: "flex", justifyContent: "center" }}>
          <LoadingSpinner label="Loading matching engine runs..." />
        </div>
      ) : (
        <EmptyState
          title="No Matching Runs Initiated"
          guidance="Matching runs are executed against completed buyer requirements. Open a ready requirement to initiate candidate matching."
        />
      )}
    </div>
  );
}
