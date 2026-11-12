"use client";

import React from "react";
import Link from "next/link";
import { usePathname } from "next/navigation";
import styles from "./navigation.module.css";
import { UserRole } from "@/lib/api/types";

interface NavItem {
  href: string;
  label: string;
  allowedRoles: UserRole[];
  icon: React.ReactNode;
}

const NAV_ITEMS: NavItem[] = [
  {
    href: "/dashboard",
    label: "Dashboard",
    allowedRoles: ["platform_admin", "commercial_analyst", "reviewer"],
    icon: (
      <svg className={styles.navIcon} viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.8" strokeLinecap="round" strokeLinejoin="round">
        <path d="M3 9l9-7 9 7v11a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2z" />
        <polyline points="9 22 9 12 15 12 15 22" />
      </svg>
    ),
  },
  {
    href: "/suppliers",
    label: "Supplier Registry",
    allowedRoles: ["platform_admin", "commercial_analyst", "reviewer"],
    icon: (
      <svg className={styles.navIcon} viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.8" strokeLinecap="round" strokeLinejoin="round">
        <rect x="4" y="2" width="16" height="20" rx="2" />
        <line x1="9" y1="6" x2="9" y2="6.01" />
        <line x1="15" y1="6" x2="15" y2="6.01" />
        <line x1="9" y1="10" x2="9" y2="10.01" />
        <line x1="15" y1="10" x2="15" y2="10.01" />
        <line x1="9" y1="14" x2="9" y2="14.01" />
        <line x1="15" y1="14" x2="15" y2="14.01" />
        <path d="M9 18h6" />
      </svg>
    ),
  },
  {
    href: "/products",
    label: "Product Catalogue",
    allowedRoles: ["platform_admin", "commercial_analyst", "reviewer"],
    icon: (
      <svg className={styles.navIcon} viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.8" strokeLinecap="round" strokeLinejoin="round">
        <path d="M21 16V8a2 2 0 0 0-1-1.73l-7-4a2 2 0 0 0-2 0l-7 4A2 2 0 0 0 3 8v8a2 2 0 0 0 1 1.73l7 4a2 2 0 0 0 2 0l7-4A2 2 0 0 0 21 16z" />
        <polyline points="3.27 6.96 12 12.01 20.73 6.96" />
        <line x1="12" y1="22.08" x2="12" y2="12" />
      </svg>
    ),
  },
  {
    href: "/readiness",
    label: "China Readiness",
    allowedRoles: ["platform_admin", "commercial_analyst", "reviewer"],
    icon: (
      <svg className={styles.navIcon} viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.8" strokeLinecap="round" strokeLinejoin="round">
        <path d="M12 22s8-4 8-10V5l-8-3-8 3v7c0 6 8 10 8 10z" />
        <polyline points="9 12 11 14 15 10" />
      </svg>
    ),
  },
  {
    href: "/requirements",
    label: "Buyer Requirements",
    allowedRoles: ["platform_admin", "commercial_analyst", "reviewer"],
    icon: (
      <svg className={styles.navIcon} viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.8" strokeLinecap="round" strokeLinejoin="round">
        <path d="M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8z" />
        <polyline points="14 2 14 8 20 8" />
        <line x1="16" y1="13" x2="8" y2="13" />
        <line x1="16" y1="17" x2="8" y2="17" />
        <polyline points="10 9 9 9 8 9" />
      </svg>
    ),
  },
  {
    href: "/matching",
    label: "AI Match Desk",
    allowedRoles: ["platform_admin", "commercial_analyst", "reviewer"],
    icon: (
      <svg className={styles.navIcon} viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.8" strokeLinecap="round" strokeLinejoin="round">
        <path d="M12 2v4M12 18v4M4.93 4.93l2.83 2.83M16.24 16.24l2.83 2.83M2 12h4M18 12h4M4.93 19.07l2.83-2.83M16.24 7.76l2.83-2.83" />
      </svg>
    ),
  },
  {
    href: "/opportunities",
    label: "Trade Opportunities",
    allowedRoles: ["platform_admin", "commercial_analyst", "reviewer"],
    icon: (
      <svg className={styles.navIcon} viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.8" strokeLinecap="round" strokeLinejoin="round">
        <rect x="2" y="7" width="20" height="14" rx="2" ry="2" />
        <path d="M16 21V5a2 2 0 0 0-2-2h-4a2 2 0 0 0-2 2v16" />
      </svg>
    ),
  },
  {
    href: "/audit",
    label: "Reports & Insights",
    allowedRoles: ["platform_admin", "commercial_analyst", "reviewer"],
    icon: (
      <svg className={styles.navIcon} viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.8" strokeLinecap="round" strokeLinejoin="round">
        <line x1="18" y1="20" x2="18" y2="10" />
        <line x1="12" y1="20" x2="12" y2="4" />
        <line x1="6" y1="20" x2="6" y2="14" />
      </svg>
    ),
  },
  {
    href: "/audit#documents",
    label: "Documents",
    allowedRoles: ["platform_admin", "commercial_analyst", "reviewer"],
    icon: (
      <svg className={styles.navIcon} viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.8" strokeLinecap="round" strokeLinejoin="round">
        <path d="M22 19a2 2 0 0 1-2 2H4a2 2 0 0 1-2-2V5a2 2 0 0 1 2-2h5l2 3h9a2 2 0 0 1 2 2z" />
      </svg>
    ),
  },
];

interface AppSidebarProps {
  userRole?: UserRole;
}

export function AppSidebar({ userRole = "commercial_analyst" }: AppSidebarProps) {
  const pathname = usePathname();

  const visibleItems = NAV_ITEMS.filter((item) =>
    item.allowedRoles.includes(userRole)
  );

  return (
    <aside className={styles.sidebar} aria-label="Main Application Navigation">
      <Link href="/dashboard" className={styles.brand}>
        {/* Elegant Mountain Crest Calligraphy Icon */}
        <svg className={styles.mountainIcon} viewBox="0 0 48 48" fill="none" xmlns="http://www.w3.org/2000/svg">
          <path d="M8 36C12 24 16 16 22 14C27 22 30 26 34 20C38 24 40 32 42 36" stroke="#1E3A2F" strokeWidth="3.2" strokeLinecap="round" strokeLinejoin="round" />
          <path d="M16 36C19 28 22 22 26 21C29 25 31 29 34 27" stroke="#D9824B" strokeWidth="2.4" strokeLinecap="round" strokeLinejoin="round" />
        </svg>
        <div className={styles.brandText}>
          <span className={styles.brandTitle}>InChi</span>
          <span className={styles.brandSubtitle}>Pilot Gateway</span>
        </div>
      </Link>

      <nav>
        <ul className={styles.navList}>
          {visibleItems.map((item) => {
            const isActive = pathname === item.href || (item.href !== "/dashboard" && pathname.startsWith(item.href.split("#")[0]));
            return (
              <li key={item.href}>
                <Link
                  href={item.href}
                  className={`${styles.navLink} ${isActive ? styles.navLinkActive : ""}`}
                  aria-current={isActive ? "page" : undefined}
                >
                  {item.icon}
                  <span>{item.label}</span>
                </Link>
              </li>
            );
          })}
        </ul>
      </nav>

      {/* Decorative Ink-wash Bamboo Branch Silhouette */}
      <svg className={styles.bambooMotif} viewBox="0 0 120 180" fill="none" xmlns="http://www.w3.org/2000/svg">
        <path d="M20 180C22 130 25 80 20 10" stroke="#1E3A2F" strokeWidth="3" strokeLinecap="round" />
        <path d="M19 130C23 129 25 129 28 131" stroke="#1E3A2F" strokeWidth="2.5" />
        <path d="M17 75C21 74 24 74 27 76" stroke="#1E3A2F" strokeWidth="2.5" />
        <path d="M22 128C38 120 50 110 58 98C46 102 34 112 22 128Z" fill="#1E3A2F" />
        <path d="M24 126C42 125 58 122 70 116C56 122 40 125 24 126Z" fill="#1E3A2F" />
        <path d="M19 72C34 60 45 48 52 32C42 40 30 52 19 72Z" fill="#1E3A2F" />
        <path d="M21 70C38 67 52 61 62 52C48 60 34 66 21 70Z" fill="#1E3A2F" />
      </svg>
    </aside>
  );
}
