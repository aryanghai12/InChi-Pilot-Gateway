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
}

const NAV_ITEMS: NavItem[] = [
  {
    href: "/dashboard",
    label: "Dashboard",
    allowedRoles: ["platform_admin", "commercial_analyst", "reviewer"],
  },
  {
    href: "/suppliers",
    label: "Suppliers & Products",
    allowedRoles: ["platform_admin", "commercial_analyst", "reviewer"],
  },
  {
    href: "/readiness",
    label: "China-Readiness",
    allowedRoles: ["platform_admin", "commercial_analyst", "reviewer"],
  },
  {
    href: "/requirements",
    label: "Buyer Requirements",
    allowedRoles: ["platform_admin", "commercial_analyst", "reviewer"],
  },
  {
    href: "/matching",
    label: "Explainable Matching",
    allowedRoles: ["platform_admin", "commercial_analyst", "reviewer"],
  },
  {
    href: "/opportunities",
    label: "Commercial Pipeline",
    allowedRoles: ["platform_admin", "commercial_analyst", "reviewer"],
  },
  {
    href: "/audit",
    label: "Audit History",
    allowedRoles: ["platform_admin", "reviewer"],
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
    <aside className={styles.sidebar} aria-label="Main Navigation">
      <div className={styles.navSectionTitle}>Navigation</div>
      <ul className={styles.navList}>
        {visibleItems.map((item) => {
          const isActive =
            pathname === item.href || pathname.startsWith(`${item.href}/`);
          return (
            <li key={item.href}>
              <Link
                href={item.href}
                className={`${styles.navLink} ${
                  isActive ? styles.navLinkActive : ""
                }`}
                aria-current={isActive ? "page" : undefined}
              >
                {item.label}
              </Link>
            </li>
          );
        })}
      </ul>

      {userRole === "platform_admin" && (
        <div className={styles.adminLink}>
          <div className={styles.navSectionTitle}>Administration</div>
          <a
            href="/admin/"
            className={styles.navLink}
            target="_blank"
            rel="noopener noreferrer"
          >
            Django Admin ↗
          </a>
        </div>
      )}
    </aside>
  );
}
