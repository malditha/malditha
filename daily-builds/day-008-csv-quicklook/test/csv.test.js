import test from "node:test";
import assert from "node:assert/strict";
import { parseCsv, quicklook, summarizeColumns } from "../src/csv.js";

test("parses headers and ordinary rows", () => {
  assert.deepEqual(parseCsv("name,role\nAna,Designer\nSam,Developer"), { headers: ["name", "role"], rows: [["Ana", "Designer"], ["Sam", "Developer"]], errors: [] });
});

test("parses quoted commas and escaped quotes", () => {
  const result = parseCsv('name,note\n"Ana, M.","Said ""hello"""');
  assert.deepEqual(result.rows[0], ["Ana, M.", 'Said "hello"']);
});

test("supports semicolon delimiters", () => {
  assert.deepEqual(parseCsv("name;city\nAna;Manila", ";").rows[0], ["Ana", "Manila"]);
});

test("keeps newlines inside quoted fields", () => {
  assert.equal(parseCsv('name,note\nAna,"line one\nline two"').rows[0][1], "line one\nline two");
});

test("reports uneven rows and unclosed quotes", () => {
  const uneven = parseCsv("a,b\n1\n2,3,4");
  assert.equal(uneven.errors.length, 2);
  assert.match(parseCsv('a,b\n1,"oops').errors[0], /Unclosed/);
});

test("summarizes filled, empty and unique values", () => {
  assert.deepEqual(summarizeColumns(["city"], [["Manila"], [""], ["Manila"], ["Cebu"]])[0], { name: "city", filled: 3, empty: 1, unique: 2 });
});

test("limits preview without changing totals", () => {
  const result = quicklook("n\n1\n2\n3", ",", 2);
  assert.equal(result.rows.length, 3);
  assert.equal(result.preview.length, 2);
});
