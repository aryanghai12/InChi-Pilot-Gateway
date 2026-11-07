"use client";

import React from "react";
import { EmptyState } from "@/components/feedback/EmptyState";

export default function MatchingPage() {
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

      <EmptyState
        title="No Matching Runs Initiated"
        guidance="Matching runs are executed against completed buyer requirements. Open a ready requirement to initiate candidate matching."
      />
    </div>
  );
}
