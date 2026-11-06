import React from "react";
import styles from "./EmptyState.module.css";

interface EmptyStateProps {
  title: string;
  guidance: string;
  action?: React.ReactNode;
  className?: string;
}

export function EmptyState({
  title,
  guidance,
  action,
  className = "",
}: EmptyStateProps) {
  return (
    <div className={`${styles.emptyState} ${className}`}>
      <h3 className={styles.title}>{title}</h3>
      <p className={styles.guidance}>{guidance}</p>
      {action && <div className={styles.actionWrapper}>{action}</div>}
    </div>
  );
}
