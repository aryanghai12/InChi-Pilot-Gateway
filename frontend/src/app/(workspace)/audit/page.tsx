"use client";

import React from "react";
import { EmptyState } from "@/components/feedback/EmptyState";

export default function AuditPage() {
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

      <EmptyState
        title="No Audit Records"
        guidance="All material creations, updates, reviews, and decisions produce an immutable audit event automatically."
      />
    </div>
  );
}
