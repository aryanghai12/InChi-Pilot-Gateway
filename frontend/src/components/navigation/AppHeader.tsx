"use client";

import React from "react";
import Link from "next/link";
import { useRouter } from "next/navigation";
import styles from "./navigation.module.css";
import { CurrentUser } from "@/lib/api/types";
import { apiFetch } from "@/lib/api/client";

interface AppHeaderProps {
  user?: CurrentUser | null;
}

export function AppHeader({ user }: AppHeaderProps) {
  const router = useRouter();

  const handleLogout = async () => {
    try {
      await apiFetch("/api/v1/auth/logout/", { method: "POST" });
    } catch (err) {
      console.warn("Logout error:", err);
    } finally {
      router.push("/login");
    }
  };

  const getInitials = (name?: string) => {
    if (!name) return "PS";
    const parts = name.split(/[._\s-]+/);
    if (parts.length >= 2) {
      return (parts[0][0] + parts[1][0]).toUpperCase();
    }
    return name.slice(0, 2).toUpperCase();
  };

  const getDisplayName = (user?: CurrentUser | null) => {
    if (!user) return "Priyanka";
    if (user.username === "priyanka.singh" || user.username === "priyanka") return "Priyanka";
    return user.username;
  };

  return (
    <header className={styles.header}>
      <div className={styles.greetingSection}>
        <h2 className={styles.greetingTitle}>Good morning, {getDisplayName(user)}</h2>
        <span className={styles.greetingSubtitle}>BNCS Internal Workspace</span>
      </div>

      <div className={styles.headerRight}>
        <div className={styles.searchBox}>
          <svg className={styles.searchIcon} viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
            <circle cx="11" cy="11" r="8" />
            <line x1="21" y1="21" x2="16.65" y2="16.65" />
          </svg>
          <input
            type="search"
            placeholder="Search suppliers, products, buyers..."
            className={styles.searchInput}
            aria-label="Search gateway directory"
          />
        </div>

        <button type="button" className={styles.bellButton} aria-label="Notifications (1 unread)">
          <svg width="17" height="17" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.8" strokeLinecap="round" strokeLinejoin="round">
            <path d="M18 8A6 6 0 0 0 6 8c0 7-3 9-3 9h18s-3-2-3-9" />
            <path d="M13.73 21a2 2 0 0 1-3.46 0" />
          </svg>
          <span className={styles.notificationDot} />
        </button>

        <div className={styles.userProfileMenu}>
          {user ? (
            <>
              <div className={styles.avatar} title={`${user.username} (${user.role})`}>
                {getInitials(user.username)}
              </div>
              <button
                type="button"
                onClick={handleLogout}
                className={styles.logoutBtn}
                aria-label="Sign out of your account"
              >
                Sign out
              </button>
            </>
          ) : (
            <Link href="/login" className={styles.logoutBtn}>
              Sign in
            </Link>
          )}
        </div>
      </div>
    </header>
  );
}
