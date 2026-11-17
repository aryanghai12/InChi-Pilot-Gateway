export function validateEnvironment(env) {
  for (const name of ["E2E_BACKEND", "E2E_API_ONLY"]) {
    if (env[name] !== undefined && !["0", "1"].includes(env[name])) {
      throw new Error(`${name} must be 0 or 1`);
    }
  }
  if (env.E2E_API_ONLY === "1" && env.E2E_BACKEND !== "1") {
    throw new Error("API-only execution requires E2E_BACKEND=1; skipped API tests are not a regression pass");
  }
  if (env.E2E_BACKEND === "1" && !env.E2E_BASE_URL) {
    throw new Error("Full-stack execution requires E2E_BASE_URL for an already running synthetic test stack");
  }
  if (env.E2E_BASE_URL) {
    const url = new URL(env.E2E_BASE_URL);
    if (!["http:", "https:"].includes(url.protocol) || url.username || url.password || url.search || url.hash || url.pathname !== "/") {
      throw new Error("E2E_BASE_URL must be an HTTP(S) origin without credentials, path, query or fragment");
    }
  }
}
