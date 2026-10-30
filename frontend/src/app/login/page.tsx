"use client";

import React, { useState, useEffect, Suspense } from "react";
import { useRouter, useSearchParams } from "next/navigation";
import styles from "./login.module.css";
import { apiFetch, ensureCsrfToken } from "@/lib/api/client";
import { ApiError } from "@/lib/api/types";
import { FormField } from "@/components/forms/FormField";
import { Input } from "@/components/forms/Input";
import { Button } from "@/components/forms/Button";
import { AlertBanner } from "@/components/feedback/AlertBanner";
import { LoadingSpinner } from "@/components/feedback/LoadingSpinner";

function LoginForm() {
  const router = useRouter();
  const searchParams = useSearchParams();
  const nextUrl = searchParams.get("next") || "/dashboard";

  const [username, setUsername] = useState("");
  const [password, setPassword] = useState("");
  const [isLoading, setIsLoading] = useState(false);
  const [errorMessage, setErrorMessage] = useState<string | null>(null);
  const [fieldErrors, setFieldErrors] = useState<Record<string, string[]>>({});

  // Bootstrap CSRF cookie on initial page load (ARCHITECTURE.md §5, §7)
  useEffect(() => {
    ensureCsrfToken();
  }, []);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setIsLoading(true);
    setErrorMessage(null);
    setFieldErrors({});

    try {
      await apiFetch("/api/v1/auth/login/", {
        method: "POST",
        body: JSON.stringify({ username, password }),
      });

      // Redirect to return url or dashboard
      router.push(nextUrl);
    } catch (err) {
      if (err instanceof ApiError) {
        setErrorMessage(err.message || "Invalid credentials provided.");
        if (err.fieldErrors) {
          setFieldErrors(err.fieldErrors);
        }
      } else {
        setErrorMessage("An unexpected error occurred during sign-in.");
      }
    } finally {
      setIsLoading(false);
    }
  };

  return (
    <div className={styles.loginCard}>
      <div className={styles.header}>
        <h1 className={styles.title}>InChi Pilot Gateway</h1>
        <p className={styles.subtitle}>Sign in with your internal BNCS account</p>
      </div>

      {errorMessage && (
        <AlertBanner
          type="error"
          title="Authentication Failed"
          message={errorMessage}
        />
      )}

      <form onSubmit={handleSubmit} noValidate>
        <FormField
          label="Username"
          htmlFor="username"
          required
          errors={fieldErrors.username}
        >
          <Input
            id="username"
            type="text"
            autoComplete="username"
            required
            value={username}
            onChange={(e) => setUsername(e.target.value)}
            hasError={Boolean(fieldErrors.username)}
            disabled={isLoading}
          />
        </FormField>

        <FormField
          label="Password"
          htmlFor="password"
          required
          errors={fieldErrors.password}
        >
          <Input
            id="password"
            type="password"
            autoComplete="current-password"
            required
            value={password}
            onChange={(e) => setPassword(e.target.value)}
            hasError={Boolean(fieldErrors.password)}
            disabled={isLoading}
          />
        </FormField>

        <Button
          type="submit"
          variant="primary"
          isLoading={isLoading}
          style={{ width: "100%", marginTop: "0.5rem" }}
        >
          Sign In
        </Button>
      </form>

      <div className={styles.notice}>
        Private internal pilot for authorized BNCS personnel only. Unauthorized access is monitored and audited.
      </div>
    </div>
  );
}

export default function LoginPage() {
  return (
    <div className={styles.pageWrapper}>
      <Suspense fallback={<LoadingSpinner label="Loading sign-in form..." />}>
        <LoginForm />
      </Suspense>
    </div>
  );
}
