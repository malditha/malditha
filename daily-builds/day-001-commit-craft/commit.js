(function (root, factory) {
  const api = factory();
  if (typeof module === "object" && module.exports) module.exports = api;
  if (root) root.CommitCraft = api;
})(typeof globalThis !== "undefined" ? globalThis : this, function () {
  const allowedTypes = new Set(["feat", "fix", "docs", "style", "refactor", "test", "chore", "perf", "ci", "build", "revert"]);

  function clean(value) {
    return String(value || "").trim().replace(/\s+/g, " ");
  }

  function cleanScope(value) {
    return clean(value).toLowerCase().replace(/[^a-z0-9._-]+/g, "-").replace(/^-+|-+$/g, "");
  }

  function buildCommit(input) {
    const type = allowedTypes.has(input.type) ? input.type : "chore";
    const scope = cleanScope(input.scope);
    const summary = clean(input.summary).replace(/[.!]+$/, "");
    const marker = input.breaking ? "!" : "";
    const header = type + (scope ? "(" + scope + ")" : "") + marker + ": " + summary;
    const sections = [header];

    if (clean(input.body)) sections.push(clean(input.body));
    if (clean(input.issue)) sections.push("Refs: " + clean(input.issue));

    return sections.join("\n\n");
  }

  function validateCommit(input) {
    const message = buildCommit(input);
    const header = message.split("\n")[0];
    const errors = [];

    if (!clean(input.summary)) errors.push("Add a short summary.");
    if (header.length > 72) errors.push("Keep the first line at 72 characters or fewer.");

    return { valid: errors.length === 0, errors, headerLength: header.length, message };
  }

  return { buildCommit, validateCommit };
});
