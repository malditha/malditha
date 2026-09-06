const test = require("node:test");
const assert = require("node:assert/strict");
const { normalizeFlags, compilePattern, collectMatches, buildSegments, previewReplacement } = require("../regex-tools");

test("normalizes duplicate flags", () => assert.equal(normalizeFlags("ggi"), "gi"));
test("rejects unsupported flags", () => assert.throws(() => normalizeFlags("gx"), /Unsupported flag/));
test("rejects incompatible unicode flags", () => assert.throws(() => normalizeFlags("uv"), /cannot be used together/));
test("reports invalid patterns", () => assert.throws(() => compilePattern("["), SyntaxError));
test("collects values, positions and capture groups", () => {
  const result = collectMatches("(cat)", "gi", "Cat and cat");
  assert.deepEqual(result.matches.map(({ value, index, groups }) => ({ value, index, groups })), [
    { value: "Cat", index: 0, groups: ["Cat"] },
    { value: "cat", index: 8, groups: ["cat"] }
  ]);
});
test("advances safely after zero-length matches", () => {
  assert.deepEqual(collectMatches("(?=a)", "g", "aa").matches.map((match) => match.index), [0, 1]);
});
test("builds plain and highlighted segments", () => {
  assert.deepEqual(buildSegments("one two", [{ index: 4, end: 7 }]), [
    { text: "one ", match: false }, { text: "two", match: true }
  ]);
});
test("previews JavaScript replacements", () => {
  assert.equal(previewReplacement("(\\w+), (\\w+)", "g", "Lacanlale, Kris", "$2 $1"), "Kris Lacanlale");
});
