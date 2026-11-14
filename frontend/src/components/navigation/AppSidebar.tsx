"use client";

import React from "react";
import Link from "next/link";
import { usePathname, useRouter } from "next/navigation";
import { useQueryClient } from "@tanstack/react-query";
import styles from "./navigation.module.css";
import { UserRole, CurrentUser } from "@/lib/api/types";
import { apiFetch } from "@/lib/api/client";

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
      <svg className={styles.navIcon} viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
        <rect x="3" y="3" width="7" height="7" rx="1.5" />
        <rect x="14" y="3" width="7" height="7" rx="1.5" />
        <rect x="14" y="14" width="7" height="7" rx="1.5" />
        <rect x="3" y="14" width="7" height="7" rx="1.5" />
      </svg>
    ),
  },
  {
    href: "/suppliers",
    label: "Supplier Registry",
    allowedRoles: ["platform_admin", "commercial_analyst", "reviewer"],
    icon: (
      <svg className={styles.navIcon} viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
        <path d="M3 21h18" />
        <path d="M19 21v-4" />
        <path d="M19 17a2 2 0 0 0-2-2H7a2 2 0 0 0-2 2v4" />
        <path d="M5 21V5a2 2 0 0 1 2-2h10a2 2 0 0 1 2 2v12" />
        <path d="M9 7h1" />
        <path d="M9 11h1" />
        <path d="M14 7h1" />
        <path d="M14 11h1" />
      </svg>
    ),
  },
  {
    href: "/products",
    label: "Product Catalogue",
    allowedRoles: ["platform_admin", "commercial_analyst", "reviewer"],
    icon: (
      <svg className={styles.navIcon} viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
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
      <svg className={styles.navIcon} viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
        <path d="M9 11l3 3L22 4" />
        <path d="M21 12v7a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2V5a2 2 0 0 1 2-2h11" />
      </svg>
    ),
  },
  {
    href: "/requirements",
    label: "Buyer Requirements",
    allowedRoles: ["platform_admin", "commercial_analyst", "reviewer"],
    icon: (
      <svg className={styles.navIcon} viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
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
      <svg className={styles.navIcon} viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
        <path d="M12 2v4M12 18v4M4.93 4.93l2.83 2.83M16.24 16.24l2.83 2.83M2 12h4M18 12h4M4.93 19.07l2.83-2.83M16.24 7.76l2.83-2.83" />
      </svg>
    ),
  },
  {
    href: "/opportunities",
    label: "Trade Opportunities",
    allowedRoles: ["platform_admin", "commercial_analyst", "reviewer"],
    icon: (
      <svg className={styles.navIcon} viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
        <circle cx="18" cy="18" r="3" />
        <circle cx="6" cy="6" r="3" />
        <path d="M13 6h3a2 2 0 0 1 2 2v7" />
        <line x1="6" y1="9" x2="6" y2="21" />
      </svg>
    ),
  },
  {
    href: "/audit",
    label: "Reports & Insights",
    allowedRoles: ["platform_admin", "commercial_analyst", "reviewer"],
    icon: (
      <svg className={styles.navIcon} viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
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
      <svg className={styles.navIcon} viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
        <path d="M22 19a2 2 0 0 1-2 2H4a2 2 0 0 1-2-2V5a2 2 0 0 1 2-2h5l2 3h9a2 2 0 0 1 2 2z" />
      </svg>
    ),
  },
];

interface AppSidebarProps {
  user?: CurrentUser | null;
  userRole?: UserRole;
}

export function AppSidebar({ user, userRole = "commercial_analyst" }: AppSidebarProps) {
  const pathname = usePathname();
  const router = useRouter();
  const queryClient = useQueryClient();

  const handleLogout = async () => {
    try {
      await apiFetch("/api/v1/auth/logout/", { method: "POST" });
    } catch (err) {
      console.warn("Logout error:", err);
    } finally {
      queryClient.clear();
      router.push("/login");
    }
  };

  const visibleItems = NAV_ITEMS.filter((item) =>
    item.allowedRoles.includes(userRole)
  );

  const getInitials = (user?: CurrentUser | null) => {
    if (!user) return "U";
    if (user.first_name && user.last_name) {
      return (user.first_name[0] + user.last_name[0]).toUpperCase();
    }
    if (user.first_name) {
      return user.first_name.slice(0, 2).toUpperCase();
    }
    if (user.email) {
      return user.email.slice(0, 2).toUpperCase();
    }
    return "U";
  };

  const getDisplayName = (user?: CurrentUser | null) => {
    if (!user) return "Authorized User";
    if (user.first_name && user.last_name) return `${user.first_name} ${user.last_name}`;
    if (user.first_name) return user.first_name;
    if (user.email) return user.email.split("@")[0];
    return "Authorized User";
  };

  const getRoleDisplay = (user?: CurrentUser | null) => {
    if (!user) return "";
    return user.role_display || user.role || "";
  };

  return (
    <aside className={styles.sidebar} aria-label="Main Application Navigation">
      <div className={styles.sidebarTop}>
        {/* Brand Header */}
        <Link href="/dashboard" className={styles.brand}>
          <div className={styles.brandIconBox} aria-hidden="true">
            {/* 8-point Spark / Asterisk Icon */}
            <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.5" strokeLinecap="round" strokeLinejoin="round">
              <path d="M12 2v20M2 12h20M4.93 4.93l14.14 14.14M4.93 19.07l14.14-14.14" />
            </svg>
          </div>
          <div className={styles.brandText}>
            <div className={styles.brandHeaderRow}>
              <span className={styles.brandTitle}>InChi Gateway</span>
              <span className={styles.brandPilotBadge}>PILOT</span>
            </div>
            <span className={styles.brandSubtitle}>CROSS-BORDER PLATFORM</span>
          </div>
        </Link>

        {/* Navigation Items */}
        <nav>
          <ul className={styles.navList}>
            {visibleItems.map((item) => {
              const isActive =
                pathname === item.href ||
                (item.href !== "/dashboard" && pathname.startsWith(item.href.split("#")[0]));
              return (
                <li key={item.href}>
                  <Link
                    href={item.href}
                    className={`${styles.navLink} ${isActive ? styles.navLinkActive : ""}`}
                    aria-current={isActive ? "page" : undefined}
                  >
                    <div className={styles.navLinkLeft}>
                      {item.icon}
                      <span className={styles.navLabel}>{item.label}</span>
                    </div>
                  </Link>
                </li>
              );
            })}
          </ul>
        </nav>
      </div>

      {/* Footer Profile with Logout */}
      <div className={styles.sidebarFooter}>
        <div className={styles.userProfileCard}>
          <div className={styles.userLeft}>
            <div className={styles.avatarCircle} title={user?.email || "User"}>
              {getInitials(user)}
            </div>
            <div className={styles.userMeta}>
              <span className={styles.userName}>{getDisplayName(user)}</span>
              {getRoleDisplay(user) && (
                <span className={styles.userRole}>{getRoleDisplay(user)}</span>
              )}
            </div>
          </div>
          <button
            type="button"
            onClick={handleLogout}
            className={styles.logoutBtn}
            title="Sign out of InChi Gateway"
            aria-label="Sign out"
          >
            <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.2" strokeLinecap="round" strokeLinejoin="round">
              <path d="M18.36 6.64a9 9 0 1 1-12.73 0" />
              <line x1="12" y1="2" x2="12" y2="12" />
            </svg>
          </button>
        </div>
      </div>
    </aside>
  );
}
