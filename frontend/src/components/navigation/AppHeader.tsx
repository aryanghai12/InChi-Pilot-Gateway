"use client";

import React from "react";
import Link from "next/link";
import { useRouter } from "next/navigation";
import { useQueryClient } from "@tanstack/react-query";
import styles from "./navigation.module.css";
import { CurrentUser } from "@/lib/api/types";
import { apiFetch } from "@/lib/api/client";

interface AppHeaderProps {
  user?: CurrentUser | null;
}

export function AppHeader({ user }: AppHeaderProps) {
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

  const getInitials = (user?: CurrentUser | null) => {
    if (!user) return "PS";
    if (user.first_name && user.last_name) {
      return (user.first_name[0] + user.last_name[0]).toUpperCase();
    }
    if (user.first_name) {
      return user.first_name.slice(0, 2).toUpperCase();
    }
    if (user.email) {
      return user.email.slice(0, 2).toUpperCase();
    }
    return "PS";
  };

  const getDisplayName = (user?: CurrentUser | null) => {
    if (!user) return "Priyanka";
    if (user.first_name) return user.first_name;
    if (user.email) return user.email.split("@")[0];
    return "User";
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

        <button type="button" className={styles.bellButton} aria-label="Notifications">
          <svg width="17" height="17" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.8" strokeLinecap="round" strokeLinejoin="round">
            <path d="M18 8A6 6 0 0 0 6 8c0 7-3 9-3 9h18s-3-2-3-9" />
            <path d="M13.73 21a2 2 0 0 1-3.46 0" />
          </svg>
        </button>

        <div className={styles.userProfileMenu}>
          {user ? (
            <>
              <div className={styles.avatar} title={`${user.email} (${user.role_display || user.role})`}>
                {getInitials(user)}
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
