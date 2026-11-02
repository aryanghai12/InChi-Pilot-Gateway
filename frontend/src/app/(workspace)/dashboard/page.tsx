"use client";

import React from "react";
import Link from "next/link";
import styles from "./dashboard.module.css";

export default function DashboardPage() {
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
          <Link href="/opportunities" className={styles.heroCta}>
            <span>Explore Opportunities</span>
            <svg width="15" height="15" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.4" strokeLinecap="round" strokeLinejoin="round">
              <line x1="5" y1="12" x2="19" y2="12" />
              <polyline points="12 5 19 12 12 19" />
            </svg>
          </Link>
        </div>

        {/* Panoramic Landscape SVG Illustration: India Gate & Temple of Heaven connected by Trade Arch */}
        <div className={styles.heroArtwork} aria-hidden="true">
          <svg viewBox="0 0 760 300" fill="none" xmlns="http://www.w3.org/2000/svg" preserveAspectRatio="xMaxYMid meet" style={{ width: "100%", height: "100%" }}>
            <defs>
              <linearGradient id="skySun" x1="450" y1="60" x2="450" y2="200" gradientUnits="userSpaceOnUse">
                <stop stopColor="#F5A873" stopOpacity="0.7" />
                <stop offset="1" stopColor="#F5A873" stopOpacity="0" />
              </linearGradient>
              <linearGradient id="bridgeArc" x1="200" y1="180" x2="560" y2="180" gradientUnits="userSpaceOnUse">
                <stop stopColor="#2E634A" />
                <stop offset="0.5" stopColor="#E2925B" />
                <stop offset="1" stopColor="#2E634A" />
              </linearGradient>
              <linearGradient id="mountainFade" x1="0" y1="0" x2="0" y2="300" gradientUnits="userSpaceOnUse">
                <stop stopColor="#6C8578" stopOpacity="0.35" />
                <stop offset="1" stopColor="#FAF7F2" stopOpacity="0.8" />
              </linearGradient>
            </defs>

            {/* Rising Sun */}
            <circle cx="460" cy="120" r="58" fill="url(#skySun)" />

            {/* Distant Misty Mountain Layers */}
            <path d="M120 220 Q220 120 360 190 Q480 130 620 200 L760 220 L760 300 L120 300 Z" fill="url(#mountainFade)" opacity="0.4" />
            <path d="M260 240 Q400 160 520 220 Q640 170 760 210 L760 300 L260 300 Z" fill="url(#mountainFade)" opacity="0.6" />

            {/* Cultural Trade Arc (Connecting India to China) */}
            <path d="M200 240 C200 60, 580 60, 580 240" stroke="url(#bridgeArc)" strokeWidth="6" strokeLinecap="round" opacity="0.65" />
            <path d="M200 240 C200 60, 580 60, 580 240" stroke="#FFFFFF" strokeWidth="2" strokeDasharray="6 8" strokeLinecap="round" opacity="0.9" />

            {/* Trajectory Waypoints */}
            <circle cx="340" cy="125" r="4.5" fill="#E2925B" stroke="#FFFFFF" strokeWidth="2" />
            <circle cx="440" cy="100" r="5.5" fill="#2E634A" stroke="#FFFFFF" strokeWidth="2" />

            {/* Left Landmark: India Gate Silhouette */}
            <g transform="translate(140, 160) scale(0.68)" opacity="0.85">
              {/* Outer arch pillar base */}
              <rect x="10" y="70" width="70" height="20" fill="#B59E88" rx="2" />
              <rect x="15" y="40" width="18" height="30" fill="#B59E88" />
              <rect x="57" y="40" width="18" height="30" fill="#B59E88" />
              {/* Arch curve */}
              <path d="M33 40 Q45 25 57 40 Z" fill="#FAF7F2" />
              {/* Top entablature */}
              <rect x="12" y="25" width="66" height="15" fill="#B59E88" rx="1" />
              <rect x="18" y="12" width="54" height="13" fill="#B59E88" />
              <rect x="25" y="4" width="40" height="8" fill="#B59E88" rx="1" />
            </g>

            {/* Right Landmark: Chinese Temple / Pagoda Silhouette */}
            <g transform="translate(530, 150) scale(0.65)" opacity="0.88">
              {/* Ground tier */}
              <rect x="25" y="75" width="60" height="25" fill="#8C5042" rx="2" />
              {/* Lower Tier Roof with curved eaves */}
              <path d="M10 75 Q55 60 100 75 Q95 62 55 58 Q15 62 10 75 Z" fill="#4A342D" />
              {/* Middle tier */}
              <rect x="35" y="45" width="40" height="15" fill="#8C5042" />
              <path d="M20 47 Q55 35 90 47 Q85 36 55 33 Q25 36 20 47 Z" fill="#4A342D" />
              {/* Upper tier and finial spire */}
              <path d="M30 33 Q55 20 80 33 Z" fill="#4A342D" />
              <line x1="55" y1="22" x2="55" y2="6" stroke="#E2925B" strokeWidth="3" strokeLinecap="round" />
              <circle cx="55" cy="5" r="2.5" fill="#E2925B" />
            </g>

            {/* Pine & Bamboo Landscape Elements */}
            <path d="M125 240 Q130 215 145 210 Q140 225 125 240 Z" fill="#3D5948" />
            <path d="M110 245 Q120 220 135 220 Q125 235 110 245 Z" fill="#2E4839" />
            <path d="M605 242 Q618 215 635 212 Q622 228 605 242 Z" fill="#2E4839" />
            <path d="M625 245 Q635 225 650 228 Q638 238 625 245 Z" fill="#3D5948" />
          </svg>
        </div>
      </section>

      {/* ====================================================================
          2. METRICS ROW: 4 Stat Cards
          ==================================================================== */}
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
              <span className={styles.statNumber}>128</span>
              <span className={styles.statTrend}>↑ +12%</span>
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
              <span className={styles.statNumber}>312</span>
              <span className={styles.statTrend}>↑ +18%</span>
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
              <span className={styles.statNumber}>56</span>
              <span className={styles.statTrend}>↑ +24%</span>
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
              <span className={styles.statNumber}>18</span>
              <span className={styles.statTrend}>↑ +6%</span>
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
              <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.2" strokeLinecap="round" strokeLinejoin="round">
                <polyline points="9 18 15 12 9 6" />
              </svg>
            </Link>
          </div>

          <div className={styles.readinessContent}>
            {/* Circular Gauge 84% */}
            <div className={styles.gaugeContainer}>
              <svg className={styles.gaugeSvg} viewBox="0 0 100 100">
                <circle cx="50" cy="50" r="40" className={styles.gaugeBgCircle} />
                <circle
                  cx="50"
                  cy="50"
                  r="40"
                  className={styles.gaugeProgressCircle}
                  strokeDasharray="251.2"
                  strokeDashoffset={251.2 * (1 - 0.84)}
                />
              </svg>
              <div className={styles.gaugeTextContainer}>
                <span className={styles.gaugeScore}>84%</span>
                <span className={styles.gaugeLabel}>Ready for China</span>
              </div>
            </div>

            {/* Readiness Checklist */}
            <ul className={styles.readinessChecklist}>
              <li className={styles.checkItem}>
                <span className={styles.checkIconCompleted}>
                  <svg width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="3" strokeLinecap="round" strokeLinejoin="round">
                    <polyline points="20 6 9 17 4 12" />
                  </svg>
                </span>
                <span>Company & Compliance</span>
              </li>
              <li className={styles.checkItem}>
                <span className={styles.checkIconCompleted}>
                  <svg width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="3" strokeLinecap="round" strokeLinejoin="round">
                    <polyline points="20 6 9 17 4 12" />
                  </svg>
                </span>
                <span>Product & Quality Standards</span>
              </li>
              <li className={styles.checkItem}>
                <span className={styles.checkIconCompleted}>
                  <svg width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="3" strokeLinecap="round" strokeLinejoin="round">
                    <polyline points="20 6 9 17 4 12" />
                  </svg>
                </span>
                <span>Export Documentation</span>
              </li>
              <li className={styles.checkItem}>
                <span className={styles.checkIconCompleted}>
                  <svg width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="3" strokeLinecap="round" strokeLinejoin="round">
                    <polyline points="20 6 9 17 4 12" />
                  </svg>
                </span>
                <span>China Market Requirements</span>
              </li>
              <li className={styles.checkItem}>
                <span className={styles.checkIconPending} />
                <span style={{ color: "var(--color-text-muted)" }}>Additional Information</span>
              </li>
            </ul>
          </div>
        </div>

        {/* Right Card: Recent AI Matches Widget */}
        <div className={styles.cardWidget}>
          <div className={styles.cardHeader}>
            <h2 className={styles.cardTitle}>Recent AI Matches</h2>
            <Link href="/matching" className={styles.cardHeaderLink}>
              <span>View All</span>
              <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.2" strokeLinecap="round" strokeLinejoin="round">
                <line x1="5" y1="12" x2="19" y2="12" />
                <polyline points="12 5 19 12 12 19" />
              </svg>
            </Link>
          </div>

          <div className={styles.matchList}>
            {/* Match 1 */}
            <Link href="/matching" className={styles.matchItem}>
              <div className={styles.matchLeft}>
                <div className={styles.matchThumb}>🧶</div>
                <div className={styles.matchInfo}>
                  <span className={styles.matchName}>Zhejiang Textiles Co.</span>
                  <span className={styles.matchMeta}>Textiles · Buyer Match</span>
                </div>
              </div>
              <div className={styles.matchRight}>
                <div className={styles.matchScoreContainer}>
                  <span className={styles.matchScoreText}>94% Match</span>
                  <div className={styles.matchBarBg}>
                    <div className={styles.matchBarFill} style={{ width: "94%" }} />
                  </div>
                </div>
                <svg className={styles.matchArrow} viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.2" strokeLinecap="round" strokeLinejoin="round">
                  <polyline points="9 18 15 12 9 6" />
                </svg>
              </div>
            </Link>

            {/* Match 2 */}
            <Link href="/matching" className={styles.matchItem}>
              <div className={styles.matchLeft}>
                <div className={styles.matchThumb}>🏺</div>
                <div className={styles.matchInfo}>
                  <span className={styles.matchName}>Guangzhou Home Decor</span>
                  <span className={styles.matchMeta}>Home & Living · Buyer Match</span>
                </div>
              </div>
              <div className={styles.matchRight}>
                <div className={styles.matchScoreContainer}>
                  <span className={styles.matchScoreText}>91% Match</span>
                  <div className={styles.matchBarBg}>
                    <div className={styles.matchBarFill} style={{ width: "91%" }} />
                  </div>
                </div>
                <svg className={styles.matchArrow} viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.2" strokeLinecap="round" strokeLinejoin="round">
                  <polyline points="9 18 15 12 9 6" />
                </svg>
              </div>
            </Link>

            {/* Match 3 */}
            <Link href="/matching" className={styles.matchItem}>
              <div className={styles.matchLeft}>
                <div className={styles.matchThumb}>🌾</div>
                <div className={styles.matchInfo}>
                  <span className={styles.matchName}>Shanghai Agro Imports</span>
                  <span className={styles.matchMeta}>Agri Products · Buyer Match</span>
                </div>
              </div>
              <div className={styles.matchRight}>
                <div className={styles.matchScoreContainer}>
                  <span className={styles.matchScoreText}>88% Match</span>
                  <div className={styles.matchBarBg}>
                    <div className={styles.matchBarFill} style={{ width: "88%" }} />
                  </div>
                </div>
                <svg className={styles.matchArrow} viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.2" strokeLinecap="round" strokeLinejoin="round">
                  <polyline points="9 18 15 12 9 6" />
                </svg>
              </div>
            </Link>
          </div>
        </div>
      </section>

      {/* ====================================================================
          4. BOTTOM STEPPER: Your Trade Journey
          ==================================================================== */}
      <section className={styles.stepperCard} aria-labelledby="journey-title">
        <div className={styles.stepperHeader}>
          <h2 id="journey-title" className={styles.stepperTitle}>Your Trade Journey</h2>
          <p className={styles.stepperDesc}>From supplier registration to successful trade</p>
        </div>

        <div className={styles.stepperTrack}>
          <div className={styles.stepperLine} />

          {/* Step 1 */}
          <div className={styles.stepNode}>
            <div className={styles.stepCircleCompleted}>
              <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="3" strokeLinecap="round" strokeLinejoin="round">
                <polyline points="20 6 9 17 4 12" />
              </svg>
            </div>
            <span className={styles.stepLabel}>Register & Verify</span>
          </div>

          {/* Step 2 */}
          <div className={styles.stepNode}>
            <div className={styles.stepCircleCompleted}>
              <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="3" strokeLinecap="round" strokeLinejoin="round">
                <polyline points="20 6 9 17 4 12" />
              </svg>
            </div>
            <span className={styles.stepLabel}>Build Profile</span>
          </div>

          {/* Step 3 */}
          <div className={styles.stepNode}>
            <div className={styles.stepCircleCompleted}>
              <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="3" strokeLinecap="round" strokeLinejoin="round">
                <polyline points="20 6 9 17 4 12" />
              </svg>
            </div>
            <span className={styles.stepLabel}>Check Readiness</span>
          </div>

          {/* Step 4: Active Current Step */}
          <div className={styles.stepNode}>
            <div className={styles.stepCircleActive} aria-current="step">
              <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="#D9824B" strokeWidth="2.2" strokeLinecap="round" strokeLinejoin="round">
                <path d="M12 2v4M12 18v4M4.93 4.93l2.83 2.83M16.24 16.24l2.83 2.83M2 12h4M18 12h4M4.93 19.07l2.83-2.83M16.24 7.76l2.83-2.83" />
              </svg>
            </div>
            <span className={styles.stepLabel} style={{ color: "var(--color-primary)", fontWeight: 700 }}>
              Get AI Matches
            </span>
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
            <span className={`${styles.stepLabel} ${styles.stepLabelPending}`}>Engage Buyers</span>
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
