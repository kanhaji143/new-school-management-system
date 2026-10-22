/**
 * Prepares the app for a static export (Firebase Hosting).
 *
 * Next.js does not support middleware together with `output: "export"`, so the
 * middleware file is temporarily moved aside while building and restored right
 * after. The client-side guard in the dashboard layout keeps the routes
 * protected in the static build.
 */
import { existsSync, renameSync, rmSync } from "node:fs";
import { execSync } from "node:child_process";

const middleware = "src/middleware.ts";
const parked = "middleware.static-build.ts";
const hasMiddleware = existsSync(middleware);

if (hasMiddleware) {
  renameSync(middleware, parked);
}

// A stale .next cache breaks static export (it looks for an old /_document page).
rmSync(".next", { recursive: true, force: true });

try {
  execSync("npx next build", {
    stdio: "inherit",
    env: {
      ...process.env,
      NEXT_STATIC_EXPORT: "1",
      NEXT_PUBLIC_BUILD_ID: String(Date.now()),
    },
  });
} finally {
  if (hasMiddleware) {
    renameSync(parked, middleware);
  }
}
