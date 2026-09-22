/**
 * Optional Claude Code function-hook bridge for session.compact.
 * Judgment lives in scripts/compact_hook.py. This file only shells out
 * and falls through to the host summarizer on any failure.
 */
import { spawnSync } from "node:child_process";
import { dirname, join } from "node:path";
import { fileURLToPath } from "node:url";

const here = dirname(fileURLToPath(import.meta.url));
const root = join(here, "..");

export async function register({ hook }: { hook: Function }) {
  hook("session.compact", async (event: unknown, next: (err?: unknown) => unknown) => {
    try {
      const script = join(root, "scripts", "compact_hook.py");
      const result = spawnSync("python3", [script], {
        input: JSON.stringify(event ?? {}),
        encoding: "utf8",
        timeout: 8000,
        env: process.env,
      });
      if (result.status !== 0) return next();
      const parsed = JSON.parse(result.stdout || "{}");
      if (parsed.fallback) return next();
      if (Array.isArray(parsed.kept)) return parsed.kept;
      return next();
    } catch {
      return next();
    }
  });
}
