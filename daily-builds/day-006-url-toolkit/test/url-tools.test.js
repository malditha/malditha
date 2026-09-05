import test from "node:test";
import assert from "node:assert/strict";
import { inspectUrl, isTrackingParameter, parseUrl, transformUrl } from "../url-tools.js";

test("adds HTTPS when a scheme is omitted", () => {
  assert.equal(parseUrl("Example.COM/docs").toString(), "https://example.com/docs");
});

test("rejects empty, invalid and unsupported URLs", () => {
  assert.throws(() => parseUrl(""), /Enter a URL/);
  assert.throws(() => parseUrl("https://"), /valid web URL/);
  assert.throws(() => parseUrl("ftp://example.com/file"), /HTTP and HTTPS/);
});

test("recognizes common tracking parameter names", () => {
  assert.equal(isTrackingParameter("utm_source"), true);
  assert.equal(isTrackingParameter("FBCLID"), true);
  assert.equal(isTrackingParameter("topic"), false);
});

test("removes tracking parameters while preserving useful parameters", () => {
  assert.equal(
    transformUrl("https://example.com/?utm_source=mail&topic=urls&fbclid=abc", { removeTracking: true }),
    "https://example.com/?topic=urls"
  );
});

test("removes duplicate tracking parameters", () => {
  assert.equal(
    transformUrl("example.com/?utm_term=a&utm_term=b&keep=yes", { removeTracking: true }),
    "https://example.com/?keep=yes"
  );
});

test("sorts parameters and strips a fragment when requested", () => {
  assert.equal(
    transformUrl("https://example.com/path?z=2&a=1#section", { sortParameters: true, stripHash: true }),
    "https://example.com/path?a=1&z=2"
  );
});

test("inspects URL components and preserves repeated parameters", () => {
  assert.deepEqual(inspectUrl("https://example.com:8443/a?tag=one&tag=two#top"), {
    protocol: "https",
    hostname: "example.com",
    port: "8443",
    pathname: "/a",
    hash: "top",
    parameters: [
      { name: "tag", value: "one", tracking: false },
      { name: "tag", value: "two", tracking: false }
    ]
  });
});
