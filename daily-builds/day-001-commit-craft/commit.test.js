const test = require("node:test");
const assert = require("node:assert/strict");
const { buildCommit, validateCommit } = require("./commit.js");

test("builds a basic conventional commit", () => {
  assert.equal(buildCommit({ type: "feat", summary: "add project filters" }), "feat: add project filters");
});

test("normalizes scope and removes trailing punctuation", () => {
  assert.equal(
    buildCommit({ type: "fix", scope: "Project List", summary: "prevent an empty state." }),
    "fix(project-list): prevent an empty state"
  );
});

test("marks breaking changes and appends details", () => {
  assert.equal(
    buildCommit({ type: "feat", scope: "api", summary: "change response shape", breaking: true, body: "Returns a data envelope.", issue: "#42" }),
    "feat(api)!: change response shape\n\nReturns a data envelope.\n\nRefs: #42"
  );
});

test("reports missing and oversized summaries", () => {
  assert.equal(validateCommit({ type: "docs", summary: "" }).valid, false);
  assert.match(validateCommit({ type: "docs", summary: "x".repeat(80) }).errors.join(" "), /72 characters/);
});
