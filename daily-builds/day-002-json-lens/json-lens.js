export function parseJson(source) {
  try {
    return { ok: true, value: JSON.parse(source), error: null };
  } catch (error) {
    const position = Number(error.message.match(/position (\d+)/)?.[1] ?? 0);
    const before = source.slice(0, position);
    return {
      ok: false,
      value: null,
      error: {
        message: error.message,
        line: before.split("\n").length,
        column: position - before.lastIndexOf("\n")
      }
    };
  }
}

export function formatJson(value, space = 2) {
  return JSON.stringify(value, null, space);
}

export function minifyJson(value) {
  return JSON.stringify(value);
}

export function flattenJson(value, path = "$", rows = []) {
  if (Array.isArray(value)) {
    if (value.length === 0) rows.push({ path, type: "array", value: "[]" });
    value.forEach((item, index) => flattenJson(item, `${path}[${index}]`, rows));
  } else if (value !== null && typeof value === "object") {
    const entries = Object.entries(value);
    if (entries.length === 0) rows.push({ path, type: "object", value: "{}" });
    entries.forEach(([key, item]) => {
      const next = /^[A-Za-z_$][\w$]*$/.test(key)
        ? `${path}.${key}`
        : `${path}[${JSON.stringify(key)}]`;
      flattenJson(item, next, rows);
    });
  } else {
    rows.push({ path, type: value === null ? "null" : typeof value, value: String(value) });
  }
  return rows;
}

export function searchRows(rows, query) {
  const term = query.trim().toLowerCase();
  if (!term) return rows;
  return rows.filter(({ path, type, value }) =>
    `${path} ${type} ${value}`.toLowerCase().includes(term)
  );
}

export function summarizeJson(value) {
  const rows = flattenJson(value);
  return rows.reduce((summary, row) => {
    summary.values += 1;
    summary[row.type] = (summary[row.type] ?? 0) + 1;
    return summary;
  }, { values: 0 });
}
