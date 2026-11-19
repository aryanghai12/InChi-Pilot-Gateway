import test from "node:test";
import assert from "node:assert/strict";
import { validateEnvironment } from "./environment.mjs";

test("frontend-only mode is valid without backend configuration", () => {
  assert.doesNotThrow(() => validateEnvironment({}));
});
test("full-stack mode requires explicit running stack URL", () => {
  assert.throws(() => validateEnvironment({ E2E_BACKEND: "1" }), /E2E_BASE_URL/);
});
test("API-only mode cannot silently skip all backend tests", () => {
  assert.throws(() => validateEnvironment({ E2E_API_ONLY: "1" }), /requires E2E_BACKEND=1/);
});
test("literal false is rejected instead of enabling backend tests", () => {
  assert.throws(() => validateEnvironment({ E2E_BACKEND: "false" }), /must be 0 or 1/);
});
test("stack URL accepts HTTP and HTTPS origins", () => {
  for (const url of ["http://127.0.0.1:3000", "https://qa.example.test/"]) {
    assert.doesNotThrow(() => validateEnvironment({ E2E_BACKEND: "1", E2E_API_ONLY: "1", E2E_BASE_URL: url }));
  }
});
test("stack URL rejects credentials, non-HTTP schemes and non-origin URLs", () => {
  for (const url of ["file:///tmp", "https://user:pass@example.test", "https://qa.example.test/api", "https://qa.example.test/?token=value", "https://qa.example.test/#fragment"]) {
    assert.throws(() => validateEnvironment({ E2E_BASE_URL: url }));
  }
});
