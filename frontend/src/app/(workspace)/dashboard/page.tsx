"use client";

import React from "react";
import Link from "next/link";
import { useQuery } from "@tanstack/react-query";
import styles from "./dashboard.module.css";
import { apiFetch } from "@/lib/api/client";
import { unwrapPaginated, ApiError } from "@/lib/api/types";
import { EmptyState } from "@/components/feedback/EmptyState";
import { AlertBanner } from "@/components/feedback/AlertBanner";

interface DashboardMetrics {
  total_suppliers?: number;
  total_products?: number;
  active_matches?: number;
  open_opportunities?: number;
}

interface RecentMatchItem {
  id: string;
  supplier_name: string;
  category: string;
  score: number;
}

interface DashboardSummaryResponse {
  metrics?: DashboardMetrics;
  recent_matches?: RecentMatchItem[];
  average_readiness?: number;
}

export default function DashboardPage() {
  const { data: summaryData, isLoading: isSummaryLoading } = useQuery<DashboardSummaryResponse | null>({
    queryKey: ["dashboardSummary"],
    queryFn: async () => {
      try {
        return await apiFetch<DashboardSummaryResponse>("/api/v1/dashboard/summary/");
      } catch (err) {
        if (err instanceof ApiError && err.status === 404) {
          return null;
        }
        throw err;
      }
    },
    staleTime: 60 * 1000,
    retry: false,
  });

  const { data: suppliers = [], isLoading: isSuppliersLoading } = useQuery<any[]>({
    queryKey: ["suppliers"],
    queryFn: async () => {
      try {
        const res = await apiFetch<any>("/api/v1/suppliers/");
        return unwrapPaginated(res);
      } catch {
        return [];
      }
    },
    staleTime: 60 * 1000,
    retry: false,
  });

  const { data: products = [], isLoading: isProductsLoading } = useQuery<any[]>({
    queryKey: ["all_products"],
    queryFn: async () => {
      try {
        const res = await apiFetch<any>("/api/v1/products/");
        return unwrapPaginated(res);
      } catch {
        return [];
      }
    },
    staleTime: 60 * 1000,
    retry: false,
  });

  const isLoading = isSummaryLoading && isSuppliersLoading && isProductsLoading;
  const metrics = summaryData?.metrics;
  const totalSuppliers = metrics?.total_suppliers ?? suppliers.length;
  const totalProducts = metrics?.total_products ?? products.length;
  const activeMatches = metrics?.active_matches ?? 0;
  const openOpportunities = metrics?.open_opportunities ?? 0;
  const recentMatches = summaryData?.recent_matches || [];
  const readinessScore = summaryData?.average_readiness ?? 0;
  const isSummaryPending = summaryData === null;

  return (
    <div className={styles.dashboardContainer}>
      {/* ====================================================================
          1. HERO BANNER: From India to China, More Than Trade
          ==================================================================== */}
      <section className={styles.heroCard} aria-labelledby="hero-title">
        <div className={styles.heroContent}>
          <span className={styles.heroTag}>InChi Pilot Gateway</span>
          <h1 id="hero-title" className={styles.heroTitle}>
            From India to China,
            <span className={styles.heroTitleItalic}>More Than Trade</span>
          </h1>
          <p className={styles.heroSubtitle}>
            A supervised B2B gateway to connect Indian suppliers with verified Chinese demand.
          </p>
          <Link href="/suppliers" className={styles.heroCta}>
            <span>View Suppliers</span>
            <svg width="15" height="15" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.4" strokeLinecap="round" strokeLinejoin="round">
              <line x1="5" y1="12" x2="19" y2="12" />
              <polyline points="12 5 19 12 12 19" />
            </svg>
          </Link>
        </div>
      </section>

      {/* ====================================================================
          2. METRICS ROW: Live database counts (computed from registry when summary 404s)
          ==================================================================== */}
      {isSummaryPending && (
        <div style={{ marginBottom: "1.25rem" }}>
          <AlertBanner
            type="info"
            title="Live Registry Integration Active"
            message="Backend summary endpoint (/api/v1/dashboard/summary/) is currently under construction. Supplier and product metrics are computed directly from live registry data."
          />
        </div>
      )}

      <section className={styles.statsRow} aria-label="Key Platform Metrics">
        {/* Suppliers Stat */}
        <div className={styles.statCard}>
          <div className={styles.statIconWrapper}>
            <svg width="22" height="22" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.8" strokeLinecap="round" strokeLinejoin="round">
              <path d="M17 21v-2a4 4 0 0 0-4-4H5a4 4 0 0 0-4 4v2" />
              <circle cx="9" cy="7" r="4" />
              <path d="M23 21v-2a4 4 0 0 0-3-3.87" />
              <path d="M16 3.13a4 4 0 0 1 0 7.75" />
            </svg>
          </div>
          <div className={styles.statBody}>
            <span className={styles.statLabel}>Suppliers</span>
            <div className={styles.statValues}>
              <span className={styles.statNumber}>
                {isLoading ? "—" : totalSuppliers}
              </span>
            </div>
          </div>
        </div>

        {/* Products Stat */}
        <div className={styles.statCard}>
          <div className={styles.statIconWrapper}>
            <svg width="22" height="22" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.8" strokeLinecap="round" strokeLinejoin="round">
              <path d="M21 16V8a2 2 0 0 0-1-1.73l-7-4a2 2 0 0 0-2 0l-7 4A2 2 0 0 0 3 8v8a2 2 0 0 0 1 1.73l7 4a2 2 0 0 0 2 0l7-4A2 2 0 0 0 21 16z" />
              <polyline points="3.27 6.96 12 12.01 20.73 6.96" />
              <line x1="12" y1="22.08" x2="12" y2="12" />
            </svg>
          </div>
          <div className={styles.statBody}>
            <span className={styles.statLabel}>Products</span>
            <div className={styles.statValues}>
              <span className={styles.statNumber}>
                {isLoading ? "—" : totalProducts}
              </span>
            </div>
          </div>
        </div>

        {/* AI Matches Stat */}
        <div className={styles.statCard}>
          <div className={styles.statIconWrapper}>
            <svg width="22" height="22" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.8" strokeLinecap="round" strokeLinejoin="round">
              <path d="M12 2v4M12 18v4M4.93 4.93l2.83 2.83M16.24 16.24l2.83 2.83M2 12h4M18 12h4M4.93 19.07l2.83-2.83M16.24 7.76l2.83-2.83" />
            </svg>
          </div>
          <div className={styles.statBody}>
            <span className={styles.statLabel}>AI Matches</span>
            <div className={styles.statValues}>
              <span className={styles.statNumber}>
                {isLoading ? "—" : activeMatches}
              </span>
            </div>
          </div>
        </div>

        {/* Opportunities Stat */}
        <div className={styles.statCard}>
          <div className={styles.statIconWrapper}>
            <svg width="22" height="22" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.8" strokeLinecap="round" strokeLinejoin="round">
              <rect x="2" y="7" width="20" height="14" rx="2" ry="2" />
              <path d="M16 21V5a2 2 0 0 0-2-2h-4a2 2 0 0 0-2 2v16" />
            </svg>
          </div>
          <div className={styles.statBody}>
            <span className={styles.statLabel}>Opportunities</span>
            <div className={styles.statValues}>
              <span className={styles.statNumber}>
                {isLoading ? "—" : openOpportunities}
              </span>
            </div>
          </div>
        </div>
      </section>

      {/* ====================================================================
          3. MIDDLE GRID: China Readiness & Recent AI Matches
          ==================================================================== */}
      <section className={styles.middleGrid}>
        {/* Left Card: China Readiness Widget */}
        <div className={styles.cardWidget}>
          <div className={styles.cardHeader}>
            <h2 className={styles.cardTitle}>China Readiness</h2>
            <Link href="/readiness" className={styles.cardHeaderLink} aria-label="View China Readiness assessments">
              <span>View All</span>
              <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.2" strokeLinecap="round" strokeLinejoin="round">
                <polyline points="9 18 15 12 9 6" />
              </svg>
            </Link>
          </div>

          <div className={styles.readinessContent}>
            {/* Dynamic Circular Gauge */}
            <div className={styles.gaugeContainer}>
              <svg className={styles.gaugeSvg} viewBox="0 0 100 100">
                <circle cx="50" cy="50" r="40" className={styles.gaugeBgCircle} />
                <circle
                  cx="50"
                  cy="50"
                  r="40"
                  className={styles.gaugeProgressCircle}
                  strokeDasharray="251.2"
                  strokeDashoffset={251.2 * (1 - Math.min(1, Math.max(0, readinessScore / 100)))}
                />
              </svg>
              <div className={styles.gaugeTextContainer}>
                <span className={styles.gaugeScore}>
                  {readinessScore > 0 ? `${Math.round(readinessScore)}%` : "0%"}
                </span>
                <span className={styles.gaugeLabel}>
                  {readinessScore > 0 ? "Average Score" : "No Assessments"}
                </span>
              </div>
            </div>

            {/* Readiness Checklist / Status */}
            <ul className={styles.readinessChecklist}>
              <li className={styles.checkItem}>
                <span className={styles.checkIconPending} />
                <span style={{ color: "var(--color-text-muted)" }}>Company & Compliance</span>
              </li>
              <li className={styles.checkItem}>
                <span className={styles.checkIconPending} />
                <span style={{ color: "var(--color-text-muted)" }}>Product & Quality Standards</span>
              </li>
              <li className={styles.checkItem}>
                <span className={styles.checkIconPending} />
                <span style={{ color: "var(--color-text-muted)" }}>Export Documentation</span>
              </li>
              <li className={styles.checkItem}>
                <span className={styles.checkIconPending} />
                <span style={{ color: "var(--color-text-muted)" }}>China Market Requirements</span>
              </li>
              <li className={styles.checkItem}>
                <span className={styles.checkIconPending} />
                <span style={{ color: "var(--color-text-muted)" }}>Missing Information Verification</span>
              </li>
            </ul>
          </div>
        </div>

        {/* Right Card: Recent AI Matches Widget */}
        <div className={styles.cardWidget}>
          <div className={styles.cardHeader}>
            <h2 className={styles.cardTitle}>Recent AI Matches</h2>
            <Link href="/matching" className={styles.cardHeaderLink}>
              <span>Match Desk</span>
              <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.2" strokeLinecap="round" strokeLinejoin="round">
                <line x1="5" y1="12" x2="19" y2="12" />
                <polyline points="12 5 19 12 12 19" />
              </svg>
            </Link>
          </div>

          {recentMatches.length > 0 ? (
            <div className={styles.matchList}>
              {recentMatches.map((match) => (
                <Link key={match.id} href={`/matching`} className={styles.matchItem}>
                  <div className={styles.matchLeft}>
                    <div className={styles.matchThumb}>📦</div>
                    <div className={styles.matchInfo}>
                      <span className={styles.matchName}>{match.supplier_name}</span>
                      <span className={styles.matchMeta}>{match.category} · Candidate Match</span>
                    </div>
                  </div>
                  <div className={styles.matchRight}>
                    <div className={styles.matchScoreContainer}>
                      <span className={styles.matchScoreText}>{match.score}% Match</span>
                      <div className={styles.matchBarBg}>
                        <div className={styles.matchBarFill} style={{ width: `${match.score}%` }} />
                      </div>
                    </div>
                    <svg className={styles.matchArrow} viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.2" strokeLinecap="round" strokeLinejoin="round">
                      <polyline points="9 18 15 12 9 6" />
                    </svg>
                  </div>
                </Link>
              ))}
            </div>
          ) : (
            <EmptyState
              title="No Recent AI Matches"
              guidance="Candidate matches will appear here once buyer requirements and matching runs are evaluated."
              action={
                <Link href="/requirements" className={styles.heroCta} style={{ padding: "0.5rem 1rem", fontSize: "0.78rem" }}>
                  <span>Capture First Requirement</span>
                </Link>
              }
            />
          )}
        </div>
      </section>

      {/* ====================================================================
          4. BOTTOM STEPPER: Your Trade Journey
          ==================================================================== */}
      <section className={styles.stepperCard} aria-labelledby="journey-title">
        <div className={styles.stepperHeader}>
          <h2 id="journey-title" className={styles.stepperTitle}>Your Trade Journey</h2>
          <p className={styles.stepperDesc}>From supplier registration to successful commercial opportunities</p>
        </div>

        <div className={styles.stepperTrack}>
          <div className={styles.stepperLine} />

          {/* Step 1: Active Initial Step */}
          <div className={styles.stepNode}>
            <div className={styles.stepCircleActive} aria-current="step">
              <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="#D9824B" strokeWidth="2.2" strokeLinecap="round" strokeLinejoin="round">
                <rect x="3" y="11" width="18" height="11" rx="2" ry="2" />
                <path d="M7 11V7a5 5 0 0 1 10 0v4" />
              </svg>
            </div>
            <span className={styles.stepLabel} style={{ color: "var(--color-primary)", fontWeight: 700 }}>
              Register & Verify
            </span>
          </div>

          {/* Step 2 */}
          <div className={styles.stepNode}>
            <div className={styles.stepCirclePending}>
              <svg width="15" height="15" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.8" strokeLinecap="round" strokeLinejoin="round">
                <rect x="4" y="2" width="16" height="20" rx="2" />
                <line x1="9" y1="6" x2="9" y2="6.01" />
                <line x1="15" y1="6" x2="15" y2="6.01" />
              </svg>
            </div>
            <span className={`${styles.stepLabel} ${styles.stepLabelPending}`}>Build Profile</span>
          </div>

          {/* Step 3 */}
          <div className={styles.stepNode}>
            <div className={styles.stepCirclePending}>
              <svg width="15" height="15" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.8" strokeLinecap="round" strokeLinejoin="round">
                <path d="M12 22s8-4 8-10V5l-8-3-8 3v7c0 6 8 10 8 10z" />
                <polyline points="9 12 11 14 15 10" />
              </svg>
            </div>
            <span className={`${styles.stepLabel} ${styles.stepLabelPending}`}>Check Readiness</span>
          </div>

          {/* Step 4 */}
          <div className={styles.stepNode}>
            <div className={styles.stepCirclePending}>
              <svg width="15" height="15" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.8" strokeLinecap="round" strokeLinejoin="round">
                <path d="M12 2v4M12 18v4M4.93 4.93l2.83 2.83M16.24 16.24l2.83 2.83M2 12h4M18 12h4M4.93 19.07l2.83-2.83M16.24 7.76l2.83-2.83" />
              </svg>
            </div>
            <span className={`${styles.stepLabel} ${styles.stepLabelPending}`}>Get AI Matches</span>
          </div>

          {/* Step 5 */}
          <div className={styles.stepNode}>
            <div className={styles.stepCirclePending}>
              <svg width="15" height="15" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.8" strokeLinecap="round" strokeLinejoin="round">
                <path d="M16 21v-2a4 4 0 0 0-4-4H5a4 4 0 0 0-4 4v2" />
                <circle cx="9" cy="7" r="4" />
                <path d="M19 11l2 2 4-4" />
              </svg>
            </div>
            <span className={`${styles.stepLabel} ${styles.stepLabelPending}`}>Review Dispositions</span>
          </div>

          {/* Step 6 */}
          <div className={styles.stepNode}>
            <div className={styles.stepCirclePending}>
              <svg width="15" height="15" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.8" strokeLinecap="round" strokeLinejoin="round">
                <rect x="2" y="7" width="20" height="14" rx="2" ry="2" />
                <path d="M16 21V5a2 2 0 0 0-2-2h-4a2 2 0 0 0-2 2v16" />
              </svg>
            </div>
            <span className={`${styles.stepLabel} ${styles.stepLabelPending}`}>Track Opportunities</span>
          </div>
        </div>
      </section>
    </div>
  );
}
