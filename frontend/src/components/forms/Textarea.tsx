import React from "react";
import styles from "./forms.module.css";

interface TextareaProps extends React.TextareaHTMLAttributes<HTMLTextAreaElement> {
  hasError?: boolean;
}

export function Textarea({ hasError = false, className = "", ...props }: TextareaProps) {
  return (
    <textarea
      className={`${styles.textarea} ${hasError ? styles.textareaHasError : ""} ${className}`}
      {...props}
    />
  );
}
