import React from "react";
import styles from "./AlertBanner.module.css";

interface AlertBannerProps {
  type?: "error" | "warning" | "info" | "success";
  title?: string;
  message: string;
  correlationId?: string;
  className?: string;
}

export function AlertBanner({
  type = "info",
  title,
  message,
  correlationId,
  className = "",
}: AlertBannerProps) {
  const role = type === "error" ? "alert" : "status";

  return (
    <div className={`${styles.alert} ${styles[type]} ${className}`} role={role}>
      {title && <div className={styles.title}>{title}</div>}
      <div className={styles.message}>{message}</div>
      {correlationId && (
        <div className={styles.meta}>Ref: {correlationId}</div>
      )}
    </div>
  );
}
