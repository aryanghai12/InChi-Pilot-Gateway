"use client";

import React from "react";
import { EmptyState } from "@/components/feedback/EmptyState";
import { Button } from "@/components/forms/Button";

export default function SuppliersPage() {
  return (
    <div>
      <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", marginBottom: "1.5rem" }}>
        <div>
          <h1 style={{ fontSize: "1.75rem", fontWeight: 700, color: "var(--color-text-main)" }}>
            Supplier Registry & Catalogue
          </h1>
          <p style={{ color: "var(--color-text-muted)", fontSize: "0.9375rem" }}>
            Maintain supplier profiles, products, commercial specifications and evidence metadata.
          </p>
        </div>
        <Button variant="primary">New Supplier Draft</Button>
      </div>

      <EmptyState
        title="No Suppliers Registered"
        guidance="No supplier records have been created yet. Create a supplier draft to begin capturing company data, products, and readiness assessments."
        action={<Button variant="primary">Create First Supplier</Button>}
      />
    </div>
  );
}
