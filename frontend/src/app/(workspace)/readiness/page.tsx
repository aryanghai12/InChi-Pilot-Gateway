"use client";

import React from "react";
import { EmptyState } from "@/components/feedback/EmptyState";

export default function ReadinessPage() {
  return (
    <div>
      <div style={{ marginBottom: "1.5rem" }}>
        <h1 style={{ fontSize: "1.75rem", fontWeight: 700, color: "var(--color-text-main)" }}>
          China-Readiness Assessments
        </h1>
        <p style={{ color: "var(--color-text-muted)", fontSize: "0.9375rem" }}>
          Assess supplier readiness against approved criteria, evaluate evidence, and review outcomes.
        </p>
      </div>

      <EmptyState
        title="No Assessments in Progress"
        guidance="Assessments are initiated from supplier profiles. Select a supplier from the registry to begin a China-readiness assessment."
      />
    </div>
  );
}
