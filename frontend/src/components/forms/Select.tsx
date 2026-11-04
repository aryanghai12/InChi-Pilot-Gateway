import React from "react";
import styles from "./forms.module.css";

interface SelectProps extends React.SelectHTMLAttributes<HTMLSelectElement> {
  hasError?: boolean;
}

export function Select({ hasError = false, className = "", children, ...props }: SelectProps) {
  return (
    <select
      className={`${styles.select} ${hasError ? styles.selectHasError : ""} ${className}`}
      {...props}
    >
      {children}
    </select>
  );
}
