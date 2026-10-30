"use client";

import React from "react";
import { EmptyState } from "@/components/feedback/EmptyState";
import { Button } from "@/components/forms/Button";

export default function RequirementsPage() {
  return (
    <div>
      <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", marginBottom: "1.5rem" }}>
        <div>
          <h1 style={{ fontSize: "1.75rem", fontWeight: 700, color: "var(--color-text-main)" }}>
            Buyer Requirements
          </h1>
          <p style={{ color: "var(--color-text-muted)", fontSize: "0.9375rem" }}>
            Capture buyer procurement criteria with strict distinction between mandatory rules and preferences.
          </p>
        </div>
        <Button variant="primary">New Requirement</Button>
      </div>

      <EmptyState
        title="No Buyer Requirements Recorded"
        guidance="Create a new requirement to define target products, certifications, quantity, pricing, and delivery constraints for matching."
        action={<Button variant="primary">Capture First Requirement</Button>}
      />
    </div>
  );
}
