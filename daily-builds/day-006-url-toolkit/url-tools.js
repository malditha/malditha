const TRACKING_KEYS = new Set(["fbclid", "gclid", "dclid", "msclkid", "mc_cid", "mc_eid"]);

export function isTrackingParameter(name) {
  const key = String(name).toLowerCase();
  return key.startsWith("utm_") || TRACKING_KEYS.has(key);
}

export function parseUrl(input) {
  const value = String(input ?? "").trim();
  if (!value) throw new TypeError("Enter a URL to inspect.");

  const candidate = /^[a-z][a-z\d+.-]*:\/\//i.test(value) ? value : `https://${value}`;
  let url;
  try {
    url = new URL(candidate);
  } catch {
    throw new TypeError("Enter a valid web URL.");
  }

  if (!["http:", "https:"].includes(url.protocol)) {
    throw new TypeError("Only HTTP and HTTPS URLs are supported.");
  }
  if (!url.hostname) throw new TypeError("The URL needs a hostname.");

  return url;
}

export function inspectUrl(input) {
  const url = parseUrl(input);
  return {
    protocol: url.protocol.slice(0, -1),
    hostname: url.hostname,
    port: url.port || "default",
    pathname: url.pathname,
    hash: url.hash ? url.hash.slice(1) : "",
    parameters: [...url.searchParams.entries()].map(([name, value]) => ({
      name,
      value,
      tracking: isTrackingParameter(name)
    }))
  };
}

export function transformUrl(input, options = {}) {
  const { removeTracking = false, sortParameters = false, stripHash = false } = options;
  const url = parseUrl(input);

  if (removeTracking) {
    for (const key of [...url.searchParams.keys()]) {
      if (isTrackingParameter(key)) url.searchParams.delete(key);
    }
  }
  if (sortParameters) url.searchParams.sort();
  if (stripHash) url.hash = "";

  return url.toString();
}
