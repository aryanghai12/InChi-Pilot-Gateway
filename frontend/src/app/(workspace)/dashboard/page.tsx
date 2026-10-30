"use client";

import React from "react";
import { EmptyState } from "@/components/feedback/EmptyState";

export default function DashboardPage() {
  return (
    <div>
      <div style={{ marginBottom: "1.5rem" }}>
        <h1 style={{ fontSize: "1.75rem", fontWeight: 700, color: "var(--color-text-main)" }}>
          Operations Dashboard
        </h1>
        <p style={{ color: "var(--color-text-muted)", fontSize: "0.9375rem" }}>
          Current status counts across suppliers, assessments, requirements and commercial pipeline.
        </p>
      </div>

      <EmptyState
        title="Dashboard Initializing"
        guidance="No recorded metrics yet. Complete supplier onboarding, readiness assessments, or requirement capture to populate dashboard counts."
      />
    </div>
  );
}
