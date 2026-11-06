import React from "react";
import Link from "next/link";
import styles from "./AccessDenied.module.css";

interface AccessDeniedProps {
  message?: string;
  className?: string;
}

export function AccessDenied({
  message = "You do not have the required role permissions to perform this action or view this resource.",
  className = "",
}: AccessDeniedProps) {
  return (
    <div className={`${styles.container} ${className}`} role="alert">
      <span className={styles.badge}>403 Permission Denied</span>
      <h2 className={styles.title}>Access Restricted</h2>
      <p className={styles.message}>{message}</p>
      <Link href="/dashboard" className={styles.backButton}>
        Return to Dashboard
      </Link>
    </div>
  );
}
