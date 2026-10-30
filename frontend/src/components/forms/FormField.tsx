import React from "react";
import styles from "./forms.module.css";

interface FormFieldProps {
  label: string;
  htmlFor?: string;
  required?: boolean;
  hint?: string;
  errors?: string[];
  children: React.ReactNode;
  className?: string;
}

export function FormField({
  label,
  htmlFor,
  required = false,
  hint,
  errors,
  children,
  className = "",
}: FormFieldProps) {
  const hasErrors = errors && errors.length > 0;

  return (
    <div className={`${styles.formField} ${className}`}>
      <label htmlFor={htmlFor} className={styles.label}>
        {label}
        {required && <span className={styles.required}>*</span>}
      </label>
      {children}
      {hint && !hasErrors && <p className={styles.hint}>{hint}</p>}
      {hasErrors && (
        <ul className={styles.fieldErrors} role="alert">
          {errors.map((error, idx) => (
            <li key={idx} className={styles.fieldErrorItem}>
              {error}
            </li>
          ))}
        </ul>
      )}
    </div>
  );
}
