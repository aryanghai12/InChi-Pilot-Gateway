"use client";

import React from "react";
import Link from "next/link";
import { useRouter } from "next/navigation";
import styles from "./navigation.module.css";
import { CurrentUser } from "@/lib/api/types";
import { StatusBadge } from "../feedback/StatusBadge";
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

  return (
    <header className={styles.header}>
      <Link href="/dashboard" className={styles.brand}>
        <span>InChi Pilot Gateway</span>
        <span className={styles.brandBadge}>v0.1</span>
      </Link>

      <div className={styles.userControls}>
        {user ? (
          <>
            <div className={styles.userInfo}>
              <span className={styles.username}>{user.username}</span>
              <StatusBadge status={user.role} />
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
    </header>
  );
}
