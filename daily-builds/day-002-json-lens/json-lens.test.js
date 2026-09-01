import test from "node:test";
import assert from "node:assert/strict";
import { flattenJson, formatJson, minifyJson, parseJson, searchRows, summarizeJson } from "./json-lens.js";

test("parses valid JSON and reports invalid locations", () => {
  assert.deepEqual(parseJson('{"ok":true}').value, { ok: true });
  const invalid = parseJson('{\n  "ok": true,\n}');
  assert.equal(invalid.ok, false);
  assert.equal(invalid.error.line, 3);
  assert.equal(invalid.error.column, 1);
});

test("formats and minifies parsed values", () => {
  const value = { name: "Kris", active: true };
  assert.match(formatJson(value), /\n  "name"/);
  assert.equal(minifyJson(value), '{"name":"Kris","active":true}');
});

test("flattens objects, arrays, unusual keys, and empty containers", () => {
  const rows = flattenJson({ users: [{ name: "Kris" }], "build status": "done", empty: [] });
  assert.deepEqual(rows.map((row) => row.path), [
    "$.users[0].name",
    '$["build status"]',
    "$.empty"
  ]);
  assert.equal(rows[2].type, "array");
});

test("searches across paths, types, and values", () => {
  const rows = flattenJson({ project: "JSON Lens", complete: true });
  assert.equal(searchRows(rows, "lens").length, 1);
  assert.equal(searchRows(rows, "boolean")[0].path, "$.complete");
  assert.equal(searchRows(rows, "").length, 2);
});

test("summarizes primitive leaf types", () => {
  assert.deepEqual(summarizeJson({ a: 1, b: false, c: null }), {
    values: 3,
    number: 1,
    boolean: 1,
    null: 1
  });
});
