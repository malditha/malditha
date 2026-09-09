import test from "node:test";
import assert from "node:assert/strict";
import { buildGitignore, normalizePattern, parseCustomPatterns, presets, summarizeGitignore } from "../core.js";

test("normalizes Windows separators and whitespace", () => assert.equal(normalizePattern("  cache\\tmp\\  "), "cache/tmp/"));
test("ignores empty lines and comments", () => assert.deepEqual(parseCustomPatterns("\n# note\nlogs/"), ["logs/"]));
test("rejects multiline patterns passed directly", () => assert.throws(() => normalizePattern("one\ntwo"), /one line/));
test("deduplicates custom patterns", () => assert.deepEqual(parseCustomPatterns("tmp/\ntmp/\n*.db"), ["tmp/", "*.db"]));
test("includes secret protection in the Next.js preset", () => assert.ok(buildGitignore(presets["next-app"]).includes(".env.*")));
test("keeps the env example exception after env rules", () => {
  const output = buildGitignore(["secrets"]);
  assert.ok(output.indexOf(".env.*") < output.indexOf("!.env.example"));
});
test("deduplicates rules shared by groups or custom input", () => {
  const output = buildGitignore(["logs", "logs"], "*.log");
  assert.equal(output.match(/^\*\.log$/gm)?.length, 1);
});
test("reports only valid unique groups and emitted rules", () => {
  const report = summarizeGitignore(["node", "node", "missing"], "custom/");
  assert.equal(report.groups, 1);
  assert.equal(report.rules, 7);
});
test("returns an empty file when no rules are selected", () => assert.equal(buildGitignore([], ""), ""));
