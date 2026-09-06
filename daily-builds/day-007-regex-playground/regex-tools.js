(function (root, factory) {
  const api = factory();
  if (typeof module === "object" && module.exports) module.exports = api;
  else root.RegexTools = api;
})(typeof globalThis !== "undefined" ? globalThis : this, function () {
  const ALLOWED_FLAGS = new Set(["d", "g", "i", "m", "s", "u", "v", "y"]);

  function normalizeFlags(flags = "") {
    const unique = [];
    for (const flag of flags) {
      if (!ALLOWED_FLAGS.has(flag)) throw new Error(`Unsupported flag: ${flag}`);
      if (!unique.includes(flag)) unique.push(flag);
    }
    if (unique.includes("u") && unique.includes("v")) {
      throw new Error("Flags u and v cannot be used together.");
    }
    return unique.join("");
  }

  function compilePattern(source, flags = "") {
    if (!source) throw new Error("Enter a regular expression.");
    return new RegExp(source, normalizeFlags(flags));
  }

  function collectMatches(source, flags, text, limit = 200) {
    const regex = compilePattern(source, flags);
    const scanFlags = regex.flags.includes("g") ? regex.flags : `${regex.flags}g`;
    const scanner = new RegExp(regex.source, scanFlags);
    const matches = [];
    let match;
    while ((match = scanner.exec(text)) !== null && matches.length < limit) {
      matches.push({
        value: match[0],
        index: match.index,
        end: match.index + match[0].length,
        groups: match.slice(1),
        namedGroups: match.groups ? { ...match.groups } : {}
      });
      if (match[0] === "") scanner.lastIndex += 1;
    }
    return { matches, truncated: matches.length === limit && scanner.exec(text) !== null };
  }

  function buildSegments(text, matches) {
    const segments = [];
    let cursor = 0;
    for (const match of matches) {
      if (match.index > cursor) segments.push({ text: text.slice(cursor, match.index), match: false });
      if (match.end > match.index) segments.push({ text: text.slice(match.index, match.end), match: true });
      cursor = Math.max(cursor, match.end);
    }
    if (cursor < text.length) segments.push({ text: text.slice(cursor), match: false });
    return segments;
  }

  function previewReplacement(source, flags, text, replacement) {
    return text.replace(compilePattern(source, flags), replacement);
  }

  return { normalizeFlags, compilePattern, collectMatches, buildSegments, previewReplacement };
});
