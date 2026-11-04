import React from "react";
import styles from "./StatusBadge.module.css";

export type BadgeVariant = "neutral" | "success" | "warning" | "danger" | "info";

interface StatusBadgeProps {
  status: string;
  variant?: BadgeVariant;
  className?: string;
}

export function StatusBadge({ status, variant, className = "" }: StatusBadgeProps) {
  // Infer variant from status string if not explicitly passed
  const resolvedVariant: BadgeVariant =
    variant ||
    (() => {
      const s = status.toLowerCase().replace(/[-_ ]/g, "");
      if (["complete", "ready", "accepted", "won", "eligible"].includes(s)) {
        return "success";
      }
      if (["draft", "pending", "onhold", "clarification", "moreinforequired", "insufficientdata"].includes(s)) {
        return "warning";
      }
      if (["archived", "rejected", "lost", "blocked", "excluded", "failed"].includes(s)) {
        return "danger";
      }
      if (["submitted", "reviewed", "commercialdiscussion", "initialcontact"].includes(s)) {
        return "info";
      }
      return "neutral";
    })();

  const formattedStatus = status.replace(/_/g, " ");

  return (
    <span className={`${styles.badge} ${styles[resolvedVariant]} ${className}`}>
      {formattedStatus}
    </span>
  );
}
