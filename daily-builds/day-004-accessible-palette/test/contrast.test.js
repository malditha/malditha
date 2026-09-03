import test from "node:test";
import assert from "node:assert/strict";
import { contrastRatio, contrastResults, hexToRgb, normalizeHex, relativeLuminance, suggestForeground } from "../contrast.js";

test("normalizes shorthand and full hex colors", () => {
  assert.equal(normalizeHex("abc"), "#aabbcc");
  assert.equal(normalizeHex("#1748E8"), "#1748e8");
  assert.throws(() => normalizeHex("blue"), /hexadecimal color/);
});

test("converts hex colors into RGB channels", () => {
  assert.deepEqual(hexToRgb("#ff4fa3"), { r: 255, g: 79, b: 163 });
});

test("calculates known luminance endpoints", () => {
  assert.equal(relativeLuminance("#000000"), 0);
  assert.equal(relativeLuminance("#ffffff"), 1);
});

test("calculates contrast independent of color order", () => {
  assert.equal(contrastRatio("#000", "#fff"), 21);
  assert.equal(contrastRatio("#fff", "#000"), 21);
});

test("classifies AA and AAA text thresholds", () => {
  assert.deepEqual(contrastResults("#767676", "#ffffff"), {
    ratio: contrastRatio("#767676", "#ffffff"),
    normalAA: true,
    normalAAA: false,
    largeAA: true,
    largeAAA: true,
    uiAA: true
  });
});

test("suggests a passing AA foreground when the pair fails", () => {
  const suggestion = suggestForeground("#bbbbbb", "#ffffff");
  assert.ok(contrastRatio(suggestion, "#ffffff") >= 4.5);
});

test("keeps a foreground that already passes the target", () => {
  assert.equal(suggestForeground("#111111", "#ffffff"), "#111111");
});
