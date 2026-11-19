"use client";

import React from "react";
import { useQuery } from "@tanstack/react-query";
import { apiFetch } from "@/lib/api/client";
import { unwrapPaginated, ApiError, PaginatedResponse } from "@/lib/api/types";
import { EmptyState } from "@/components/feedback/EmptyState";
import { LoadingSpinner } from "@/components/feedback/LoadingSpinner";

export default function MatchingPage() {
  const { isLoading } = useQuery<unknown[] | null>({
    queryKey: ["matchingRuns"],
    queryFn: async () => {
      try {
        const res = await apiFetch<unknown[] | PaginatedResponse<unknown>>("/api/v1/matching/runs/");
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
          Explainable Matching Engine
        </h1>
        <p style={{ color: "var(--color-text-muted)", fontSize: "0.9375rem" }}>
          Deterministic rule-based eligibility filtering, weighted scoring, and bounded semantic similarity signals.
        </p>
      </div>

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
