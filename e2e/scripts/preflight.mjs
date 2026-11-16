import { existsSync } from "node:fs";
import { fileURLToPath } from "node:url";
import { validateEnvironment } from "../support/environment.mjs";

try {
  validateEnvironment(process.env);
  if (!process.env.E2E_BASE_URL) {
    const frontend = fileURLToPath(new URL("../../frontend/package.json", import.meta.url));
    if (!existsSync(frontend)) throw new Error("Blocked: frontend/package.json is absent on this branch. Supply E2E_BASE_URL for a running test stack; do not report application tests as passed.");
  }
  if (process.env.E2E_BACKEND === "1") {
    for (const role of ["ANALYST", "REVIEWER", "ADMIN"]) {
      for (const suffix of ["EMAIL", "PASSWORD"]) {
        const key = `E2E_${role}_${suffix}`;
        if (!process.env[key]) throw new Error(`Blocked: missing ${key} for synthetic test account`);
      }
    }
  }
  console.log("Preflight passed (configuration/source availability only; no application behavior verified)");
} catch (error) {
  console.error(error.message);
  process.exitCode = 1;
}
