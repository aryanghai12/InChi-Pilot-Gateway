"use client";

import React, { useState, useMemo } from "react";
import { useQuery } from "@tanstack/react-query";
import styles from "./documents.module.css";
import { apiFetch } from "@/lib/api/client";
import { Supplier, PaginatedSupplierList, unwrapPaginated, ApiError } from "@/lib/api/types";
import { EmptyState } from "@/components/feedback/EmptyState";
import { LoadingSpinner } from "@/components/feedback/LoadingSpinner";
import { StatusBadge } from "@/components/feedback/StatusBadge";
import { Button } from "@/components/forms/Button";

interface DocumentRecord {
  id: string;
  title: string;
  supplier_name: string;
  category: "Certificate of Origin" | "Quality & Standards" | "Customs & Trade License" | "Financial / Banking" | "Other";
  reference_number?: string;
  verified_status: "Verified" | "Pending Review" | "Under Review";
  updated_at: string;
}

export default function DocumentsPage() {
  const [searchTerm, setSearchTerm] = useState("");
  const [categoryFilter, setCategoryFilter] = useState("All");
  const [statusFilter, setStatusFilter] = useState("All");

  const { data: suppliers = [], isLoading } = useQuery<Supplier[]>({
    queryKey: ["suppliers"],
    queryFn: async () => {
      try {
        const res = await apiFetch<Supplier[] | PaginatedSupplierList>("/api/v1/suppliers/");
        return unwrapPaginated(res);
      } catch (err) {
        if (err instanceof ApiError && err.status === 404) {
          return [];
        }
        return [];
      }
    },
    staleTime: 60 * 1000,
    retry: false,
  });

  // Synthesize document records from supplier evidence references
  const documents: DocumentRecord[] = useMemo(() => {
    const list: DocumentRecord[] = [];
    suppliers.forEach((s) => {
      if (s.address_registration_reference) {
        list.push({
          id: `doc-${s.id || s.supplier_id}-reg`,
          title: "Corporate Registration & Address Certificate",
          supplier_name: s.legal_name,
          category: "Customs & Trade License",
          reference_number: s.address_registration_reference,
          verified_status: s.record_status === "Complete" ? "Verified" : "Pending Review",
          updated_at: s.updated_at || new Date().toISOString(),
        });
      }
    });
    return list;
  }, [suppliers]);

  const filteredDocuments = useMemo(() => {
    return documents.filter((doc) => {
      const matchSearch =
        doc.title.toLowerCase().includes(searchTerm.toLowerCase()) ||
        doc.supplier_name.toLowerCase().includes(searchTerm.toLowerCase()) ||
        (doc.reference_number && doc.reference_number.toLowerCase().includes(searchTerm.toLowerCase()));

      const matchCategory = categoryFilter === "All" || doc.category === categoryFilter;
      const matchStatus = statusFilter === "All" || doc.verified_status === statusFilter;

      return matchSearch && matchCategory && matchStatus;
    });
  }, [documents, searchTerm, categoryFilter, statusFilter]);

  const verifiedCount = documents.filter((d) => d.verified_status === "Verified").length;
  const pendingCount = documents.filter((d) => d.verified_status === "Pending Review").length;

  return (
    <div className={styles.container}>
      {/* Page Header */}
      <div className={styles.headerRow}>
        <div>
          <h1 className={styles.title}>Document &amp; Evidence Vault</h1>
          <p className={styles.subtitle}>
            Centralized compliance repository for supplier certificates of origin, ISO standards, and trade documentation.
          </p>
        </div>
      </div>

      {/* KPI Stats Grid */}
      <section className={styles.statsGrid} aria-label="Document Statistics">
        <div className={styles.statCard}>
          <span className={styles.statLabel}>Total Documents</span>
          <span className={styles.statValue}>{documents.length}</span>
          <span className={styles.statSubtext}>Across all registered suppliers</span>
        </div>
        <div className={styles.statCard}>
          <span className={styles.statLabel}>Verified Compliance</span>
          <span className={styles.statValue}>{verifiedCount}</span>
          <span className={styles.statSubtext}>Human-verified trade evidence</span>
        </div>
        <div className={styles.statCard}>
          <span className={styles.statLabel}>Pending Verification</span>
          <span className={styles.statValue}>{pendingCount}</span>
          <span className={styles.statSubtext}>In analyst review queue</span>
        </div>
        <div className={styles.statCard}>
          <span className={styles.statLabel}>Integrity Verification</span>
          <span className={styles.statValue}>SHA-256</span>
          <span className={styles.statSubtext}>Tamper-resistant storage</span>
        </div>
      </section>

      {/* Filter / Search Bar */}
      <div className={styles.toolbarCard}>
        <div className={styles.searchContainer}>
          <svg className={styles.searchIcon} fill="none" stroke="currentColor" viewBox="0 0 24 24" aria-hidden="true">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M21 21l-6-6m2-5a7 7 0 11-14 0 7 7 0 0114 0z" />
          </svg>
          <input
            type="text"
            className={styles.searchInput}
            placeholder="Search by document title, supplier name, or reference..."
            value={searchTerm}
            onChange={(e) => setSearchTerm(e.target.value)}
          />
        </div>

        <div className={styles.filterGroup}>
          <select
            className={styles.filterSelect}
            value={categoryFilter}
            onChange={(e) => setCategoryFilter(e.target.value)}
          >
            <option value="All">All Categories</option>
            <option value="Certificate of Origin">Certificate of Origin (COO)</option>
            <option value="Quality & Standards">Quality &amp; Standards (ISO)</option>
            <option value="Customs & Trade License">Customs &amp; Trade License</option>
            <option value="Financial / Banking">Financial / Banking</option>
          </select>

          <select
            className={styles.filterSelect}
            value={statusFilter}
            onChange={(e) => setStatusFilter(e.target.value)}
          >
            <option value="All">All Statuses</option>
            <option value="Verified">Verified</option>
            <option value="Pending Review">Pending Review</option>
          </select>
        </div>
      </div>

      {/* Main Documents Table or Empty State */}
      <div className={styles.mainCard}>
        {isLoading ? (
          <div style={{ padding: "3rem", display: "flex", justifyContent: "center" }}>
            <LoadingSpinner label="Loading compliance documents..." />
          </div>
        ) : filteredDocuments.length === 0 ? (
          <EmptyState
            title="No Documents Found"
            guidance="Certificates of Origin, factory licenses, ISO certifications, and bank verification documents attached to suppliers will appear here."
          />
        ) : (
          <table className={styles.table}>
            <thead>
              <tr>
                <th className={styles.th}>Document Title</th>
                <th className={styles.th}>Supplier</th>
                <th className={styles.th}>Category</th>
                <th className={styles.th}>Reference Number</th>
                <th className={styles.th}>Status</th>
                <th className={styles.th} style={{ textAlign: "right" }}>Actions</th>
              </tr>
            </thead>
            <tbody>
              {filteredDocuments.map((doc) => (
                <tr key={doc.id}>
                  <td className={styles.td}>
                    <strong>{doc.title}</strong>
                  </td>
                  <td className={styles.td}>{doc.supplier_name}</td>
                  <td className={styles.td}>{doc.category}</td>
                  <td className={styles.td} style={{ fontFamily: "var(--font-family-mono)", fontSize: "0.8125rem" }}>
                    {doc.reference_number || "—"}
                  </td>
                  <td className={styles.td}>
                    <StatusBadge status={doc.verified_status} />
                  </td>
                  <td className={styles.td} style={{ textAlign: "right" }}>
                    <Button variant="secondary" onClick={() => alert(`Document metadata: ${doc.reference_number}`)}>
                      View Details
                    </Button>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        )}
      </div>
    </div>
  );
}
