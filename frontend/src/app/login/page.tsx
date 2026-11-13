"use client";

export const dynamic = "force-dynamic";

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
        <div style={{ display: "flex", justifyContent: "center", marginBottom: "0.85rem" }}>
          <div
            style={{
              width: 42,
              height: 42,
              background: "linear-gradient(135deg, #2563EB 0%, #1D4ED8 100%)",
              borderRadius: 10,
              display: "flex",
              alignItems: "center",
              justifyContent: "center",
              color: "#FFFFFF",
              boxShadow: "0 0 14px rgba(37, 99, 235, 0.4)",
            }}
          >
            <svg
              width="22"
              height="22"
              viewBox="0 0 24 24"
              fill="none"
              stroke="currentColor"
              strokeWidth="2.5"
              strokeLinecap="round"
              strokeLinejoin="round"
            >
              <path d="M12 2v20M2 12h20M4.93 4.93l14.14 14.14M4.93 19.07l14.14-14.14" />
            </svg>
          </div>
        </div>
        <div style={{ display: "flex", alignItems: "center", justifyContent: "center", gap: "0.5rem" }}>
          <h1 className={styles.title}>InChi Gateway</h1>
          <span
            style={{
              fontSize: "0.625rem",
              fontWeight: 700,
              color: "#2563EB",
              background: "#EFF6FF",
              border: "1px solid #BFDBFE",
              padding: "0.15rem 0.5rem",
              borderRadius: 9999,
              textTransform: "uppercase",
              letterSpacing: "0.05em",
            }}
          >
            v0.1 PILOT
          </span>
        </div>
        <p className={styles.subtitle}>Supervised AI Matching &amp; Cross-Border Trade Gateway</p>
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
        Private internal pilot for authorized BNCS personnel only. User accounts are provisioned by the Platform Administrator in accordance with Architecture Decision D-12 (no public self-registration).
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
