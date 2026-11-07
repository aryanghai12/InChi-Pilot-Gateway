import React from "react";
import styles from "./forms.module.css";

interface InputProps extends React.InputHTMLAttributes<HTMLInputElement> {
  hasError?: boolean;
}

export function Input({ hasError = false, className = "", ...props }: InputProps) {
  return (
    <input
      className={`${styles.input} ${hasError ? styles.inputHasError : ""} ${className}`}
      {...props}
    />
  );
}
