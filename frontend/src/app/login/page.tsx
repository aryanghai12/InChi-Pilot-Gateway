"use client";

import React, { useState, useEffect, Suspense } from "react";
import { useRouter, useSearchParams } from "next/navigation";
import { useQueryClient } from "@tanstack/react-query";
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
  const queryClient = useQueryClient();
  const searchParams = useSearchParams();
  const nextUrl = searchParams.get("next") || "/dashboard";

  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [isLoading, setIsLoading] = useState(false);
  const [errorMessage, setErrorMessage] = useState<string | null>(null);
  const [fieldErrors, setFieldErrors] = useState<Record<string, string[]>>({});

  // Bootstrap CSRF cookie on initial page load (ENDPOINT_DATA_AND_BEHAVIOR §2)
  useEffect(() => {
    ensureCsrfToken();
  }, []);

  const handleDemoSignIn = async () => {
    setIsLoading(true);
    setErrorMessage(null);
    setFieldErrors({});

    try {
      // First attempt to log in to Django with test credentials
      const res = await apiFetch<any>("/api/v1/auth/login/", {
        method: "POST",
        body: JSON.stringify({
          email: "analyst@inchi.local",
          password: "AnalystPass123!",
        }),
      });
      const user = res?.user || res;
      if (user && typeof user === "object" && (user.id || user.email)) {
        queryClient.setQueryData(["currentUser"], user);
      }
      router.push(nextUrl);
    } catch {
      // Fallback to standalone client demo session if backend is offline/unreachable
      queryClient.setQueryData(["currentUser"], {
        id: "demo-user-1",
        email: "analyst@inchi.local",
        first_name: "Priyanka",
        last_name: "Singh",
        role: "commercial_analyst",
        role_display: "Commercial Analyst",
        is_active: true,
        is_verified: true,
        is_staff: false,
      });
      router.push(nextUrl);
    } finally {
      setIsLoading(false);
    }
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setIsLoading(true);
    setErrorMessage(null);
    setFieldErrors({});

    try {
      // Backend expects lowercase normalized email & password (ENDPOINT_DATA_AND_BEHAVIOR §2)
      const res = await apiFetch<any>("/api/v1/auth/login/", {
        method: "POST",
        body: JSON.stringify({
          email: email.trim().toLowerCase(),
          password,
        }),
      });

      const user = res?.user || res;
      if (user && typeof user === "object" && (user.id || user.email)) {
        queryClient.setQueryData(["currentUser"], user);
      }

      // Redirect to return url or dashboard
      router.push(nextUrl);
    } catch (err) {
      if (err instanceof ApiError) {
        // Extract structured non_field_errors (e.g. invalid credentials masked by exception handler)
        const nonFieldError =
          err.fieldErrors?.non_field_errors?.[0] ||
          err.fieldErrors?.detail?.[0];

        const isGenericValidationNotice =
          err.message &&
          (err.message.includes("Input validation failed") ||
            err.message.includes("check field errors"));

        const displayMessage =
          err.status === 404
            ? "Backend API (:8000) not detected. Use 'Explore with Demo Session' to preview the frontend."
            : nonFieldError ||
              (isGenericValidationNotice ? "Invalid email or password." : err.message || "Invalid email or password.");

        setErrorMessage(displayMessage);
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
          label="Email Address"
          htmlFor="email"
          required
          errors={fieldErrors.email}
        >
          <Input
            id="email"
            type="email"
            autoComplete="email"
            placeholder="analyst@inchi.local"
            required
            value={email}
            onChange={(e) => setEmail(e.target.value)}
            hasError={Boolean(fieldErrors.email)}
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

        <Button
          type="button"
          variant="secondary"
          onClick={handleDemoSignIn}
          style={{ width: "100%", marginTop: "0.5rem" }}
        >
          Explore with Demo Session
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
