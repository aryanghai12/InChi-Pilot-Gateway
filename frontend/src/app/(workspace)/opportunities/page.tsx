"use client";

import React from "react";
import { EmptyState } from "@/components/feedback/EmptyState";

export default function OpportunitiesPage() {
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

      <EmptyState
        title="No Commercial Opportunities"
        guidance="Opportunities are generated exclusively from accepted candidate dispositions in a matching run."
      />
    </div>
  );
}
