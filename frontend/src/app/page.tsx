"use client";

import React from "react";
import Link from "next/link";
import { useRouter } from "next/navigation";
import styles from "./landing.module.css";

export default function LandingPage() {
  const router = useRouter();

  const handleExploreDemo = () => {
    if (typeof document !== "undefined") {
      document.cookie = "sessionid=demo-session; path=/; SameSite=Lax";
    }
    router.push("/dashboard");
  };

  return (
    <div className={styles.landingWrapper}>
      {/* -------------------------------------------------------------------- */}
      {/* 1. Header Navigation                                                 */}
      {/* -------------------------------------------------------------------- */}
      <header className={styles.landingHeader}>
        <Link href="/" className={styles.brandLink}>
          <div className={styles.brandIcon} aria-hidden="true">
            <svg width="22" height="22" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.5" strokeLinecap="round" strokeLinejoin="round">
              <path d="M12 2v20M2 12h20M4.93 4.93l14.14 14.14M4.93 19.07l14.14-14.14" />
            </svg>
          </div>
          <div className={styles.brandText}>
            <span className={styles.brandTitle}>InChi Gateway</span>
            <span className={styles.brandSubtitle}>Cross-Border Platform</span>
          </div>
        </Link>

        <nav aria-label="Landing Navigation">
          <ul className={styles.navLinks}>
            <li>
              <a href="#capabilities" className={styles.navLink}>
                Capabilities
              </a>
            </li>
            <li>
              <a href="#workflow" className={styles.navLink}>
                Trade Workflow
              </a>
            </li>
            <li>
              <a href="#governance" className={styles.navLink}>
                Governance &amp; Audit
              </a>
            </li>
          </ul>
        </nav>

        <div className={styles.headerActions}>
          <Link href="/login" className={styles.signInBtn}>
            Sign In
          </Link>
          <button
            type="button"
            onClick={handleExploreDemo}
            className={styles.demoBtn}
          >
            Explore Demo
          </button>
        </div>
      </header>

      {/* -------------------------------------------------------------------- */}
      {/* 2. Hero Section                                                      */}
      {/* -------------------------------------------------------------------- */}
      <main>
        <section className={styles.heroSection}>
          <span className={styles.heroTag}>
            <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.5">
              <circle cx="12" cy="12" r="10" />
              <path d="M12 6v6l4 2" />
            </svg>
            BNCS Cross-Border Gateway · India to China Trade Corridor
          </span>

          <h1 className={styles.heroTitle}>
            From India to China,{" "}
            <span className={styles.heroTitleHighlight}>More Than Trade.</span>
          </h1>

          <p className={styles.heroSubtitle}>
            A supervised, explainable B2B gateway connecting verified Indian manufacturers
            and exporters with qualified Chinese commercial demand through deterministic eligibility
            and AI-assisted match intelligence.
          </p>

          <div className={styles.heroCtaGroup}>
            <Link href="/login" className={styles.primaryCta}>
              <span>Enter Workspace</span>
              <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.4">
                <line x1="5" y1="12" x2="19" y2="12" />
                <polyline points="12 5 19 12 12 19" />
              </svg>
            </Link>

            <button
              type="button"
              onClick={handleExploreDemo}
              className={styles.secondaryCta}
            >
              <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
                <circle cx="12" cy="12" r="10" />
                <polygon points="10 8 16 12 10 16 10 8" />
              </svg>
              <span>Explore Demo Session</span>
            </button>
          </div>

          <div className={styles.trustBadges}>
            <div className={styles.badgeItem}>
              <svg className={styles.badgeIcon} width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.5">
                <polyline points="20 6 9 17 4 12" />
              </svg>
              <span>18-Point Compliance Verification</span>
            </div>
            <div className={styles.badgeItem}>
              <svg className={styles.badgeIcon} width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.5">
                <polyline points="20 6 9 17 4 12" />
              </svg>
              <span>Deterministic Eligibility Gates</span>
            </div>
            <div className={styles.badgeItem}>
              <svg className={styles.badgeIcon} width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.5">
                <polyline points="20 6 9 17 4 12" />
              </svg>
              <span>Human-in-the-Loop Governance</span>
            </div>
            <div className={styles.badgeItem}>
              <svg className={styles.badgeIcon} width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.5">
                <polyline points="20 6 9 17 4 12" />
              </svg>
              <span>Immutable Audit Trail</span>
            </div>
          </div>
        </section>

        {/* ------------------------------------------------------------------ */}
        {/* 3. Platform Capabilities                                           */}
        {/* ------------------------------------------------------------------ */}
        <section id="capabilities" className={styles.capabilitiesSection}>
          <div className={styles.sectionHeader}>
            <div className={styles.sectionTag}>Platform Capabilities</div>
            <h2 className={styles.sectionTitle}>Built for Rigorous Trade Qualification</h2>
            <p className={styles.sectionSubtitle}>
              Four integrated pillars ensuring every supplier recommendation is verified, explainable, and auditable.
            </p>
          </div>

          <div className={styles.grid}>
            <div className={styles.featureCard}>
              <div className={styles.cardIconBox}>
                <svg width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
                  <path d="M12 22s8-4 8-10V5l-8-3-8 3v7c0 6 8 10 8 10z" />
                </svg>
              </div>
              <span className={styles.cardTag}>Standardized Verification</span>
              <h3 className={styles.cardTitle}>China-Readiness Assessment</h3>
              <p className={styles.cardDescription}>
                Standardized 18-point qualification assessing corporate registration, production capacity,
                standards compliance, export history, and categorical evidence conditions.
              </p>
            </div>

            <div className={styles.featureCard}>
              <div className={styles.cardIconBox}>
                <svg width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
                  <circle cx="12" cy="12" r="10" />
                  <path d="m4.93 4.93 14.14 14.14" />
                  <circle cx="12" cy="12" r="6" />
                </svg>
              </div>
              <span className={styles.cardTag}>Decision Support</span>
              <h3 className={styles.cardTitle}>Explainable Matching Engine</h3>
              <p className={styles.cardDescription}>
                Strict mandatory criteria filters execute first to exclude non-compliant candidates,
                followed by weighted preference scoring and bounded semantic similarity signals.
              </p>
            </div>

            <div className={styles.featureCard}>
              <div className={styles.cardIconBox}>
                <svg width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
                  <polyline points="22 7 13.5 15.5 8.5 10.5 2 17" />
                  <polyline points="16 7 22 7 22 13" />
                </svg>
              </div>
              <span className={styles.cardTag}>Commercial Tracking</span>
              <h3 className={styles.cardTitle}>Opportunity Pipeline</h3>
              <p className={styles.cardDescription}>
                Convert accepted match dispositions into tracked commercial opportunities. Monitor stage progression,
                assignment owners, due dates, and closure rationale.
              </p>
            </div>

            <div className={styles.featureCard}>
              <div className={styles.cardIconBox}>
                <svg width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
                  <rect x="3" y="11" width="18" height="11" rx="2" ry="2" />
                  <path d="M7 11V7a5 5 0 0 1 10 0v4" />
                </svg>
              </div>
              <span className={styles.cardTag}>Access &amp; Traceability</span>
              <h3 className={styles.cardTitle}>Least-Privilege Audit Log</h3>
              <p className={styles.cardDescription}>
                Role-based access control enforces least privilege across Platform Admin, Commercial Analyst,
                and Reviewer roles. Every material action writes an immutable audit record.
              </p>
            </div>
          </div>
        </section>

        {/* ------------------------------------------------------------------ */}
        {/* 4. Trade Workflow Process                                          */}
        {/* ------------------------------------------------------------------ */}
        <section id="workflow" className={styles.processSection}>
          <div className={styles.processContainer}>
            <div className={styles.processHeader}>
              <h2 className={styles.processTitle}>The End-to-End Trade Journey</h2>
              <p className={styles.processSubtitle}>
                A human-governed pipeline where AI advises and authorized personnel make every commercial decision.
              </p>
            </div>

            <div className={styles.stepsGrid}>
              <div className={styles.stepCard}>
                <span className={styles.stepNumber}>1</span>
                <h3 className={styles.stepTitle}>Registry &amp; Profile</h3>
                <p className={styles.stepDescription}>
                  Capture detailed supplier credentials, manufacturing capacity, certifications, and bilingual product specs.
                </p>
              </div>

              <div className={styles.stepCard}>
                <span className={styles.stepNumber}>2</span>
                <h3 className={styles.stepTitle}>Readiness Review</h3>
                <p className={styles.stepDescription}>
                  Evaluate suppliers against 18 compliance gates. Reviewers record official readiness outcomes.
                </p>
              </div>

              <div className={styles.stepCard}>
                <span className={styles.stepNumber}>3</span>
                <h3 className={styles.stepTitle}>Capture Demand</h3>
                <p className={styles.stepDescription}>
                  Define buyer requirements with strict separation between mandatory filters and weighted preferences.
                </p>
              </div>

              <div className={styles.stepCard}>
                <span className={styles.stepNumber}>4</span>
                <h3 className={styles.stepTitle}>Rank &amp; Decide</h3>
                <p className={styles.stepDescription}>
                  Run explainable matching. Reviewers inspect per-criterion breakdowns and record signed dispositions.
                </p>
              </div>

              <div className={styles.stepCard}>
                <span className={styles.stepNumber}>5</span>
                <h3 className={styles.stepTitle}>Manage Pipeline</h3>
                <p className={styles.stepDescription}>
                  Advance accepted matches into the commercial opportunity pipeline with complete milestone traceability.
                </p>
              </div>
            </div>
          </div>
        </section>

        {/* ------------------------------------------------------------------ */}
        {/* 5. Governance & Disclaimer Callout                                 */}
        {/* ------------------------------------------------------------------ */}
        <section id="governance" className={styles.disclaimerSection}>
          <div className={styles.disclaimerCard}>
            <div className={styles.disclaimerIcon}>
              <svg width="32" height="32" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
                <circle cx="12" cy="12" r="10" />
                <line x1="12" y1="8" x2="12" y2="12" />
                <line x1="12" y1="16" x2="12.01" y2="16" />
              </svg>
            </div>
            <div className={styles.disclaimerText}>
              <h3>Supervised Internal Platform Policy</h3>
              <p>
                InChi Pilot Gateway is an internal B2B enterprise system developed for authorized BNCS personnel.
                Matching outputs represent decision-support recommendations and do not constitute autonomous commercial commitments,
                legal certification, or regulatory approvals. All evaluations utilize synthetic datasets in accordance
                with pilot governance standards.
              </p>
            </div>
          </div>
        </section>
      </main>

      {/* -------------------------------------------------------------------- */}
      {/* 6. Footer                                                            */}
      {/* -------------------------------------------------------------------- */}
      <footer className={styles.landingFooter}>
        <span>&copy; {new Date().getFullYear()} BNCS Biz N Consumer Solutions Pte Ltd. InChi Pilot Gateway.</span>
        <div className={styles.footerLinks}>
          <Link href="/login">Platform Sign In</Link>
          <a href="#capabilities">Capabilities</a>
          <a href="#workflow">Workflow</a>
          <a href="#governance">Governance</a>
        </div>
      </footer>
    </div>
  );
}
