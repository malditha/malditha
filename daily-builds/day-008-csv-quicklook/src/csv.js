export function parseCsv(input, delimiter = ",") {
  if (!input.trim()) return { headers: [], rows: [], errors: [] };
  const records = [];
  const errors = [];
  let record = [];
  let field = "";
  let quoted = false;
  let line = 1;

  for (let index = 0; index < input.length; index += 1) {
    const char = input[index];
    if (quoted) {
      if (char === '"' && input[index + 1] === '"') {
        field += '"';
        index += 1;
      } else if (char === '"') {
        quoted = false;
      } else {
        field += char;
        if (char === "\n") line += 1;
      }
      continue;
    }
    if (char === '"' && field === "") quoted = true;
    else if (char === delimiter) {
      record.push(field);
      field = "";
    } else if (char === "\n") {
      record.push(field.replace(/\r$/, ""));
      records.push(record);
      record = [];
      field = "";
      line += 1;
    } else field += char;
  }

  if (quoted) errors.push(`Unclosed quoted field near line ${line}.`);
  record.push(field.replace(/\r$/, ""));
  if (record.some((value) => value !== "")) records.push(record);

  const headers = records.shift() || [];
  records.forEach((row, index) => {
    if (row.length !== headers.length) errors.push(`Row ${index + 2} has ${row.length} fields; expected ${headers.length}.`);
  });
  return { headers, rows: records, errors };
}

export function summarizeColumns(headers, rows) {
  return headers.map((name, column) => {
    const values = rows.map((row) => row[column] ?? "");
    const filled = values.filter((value) => value.trim() !== "");
    return {
      name: name || `Column ${column + 1}`,
      filled: filled.length,
      empty: values.length - filled.length,
      unique: new Set(filled).size
    };
  });
}

export function quicklook(input, delimiter = ",", previewLimit = 20) {
  const parsed = parseCsv(input, delimiter);
  return { ...parsed, preview: parsed.rows.slice(0, previewLimit), summaries: summarizeColumns(parsed.headers, parsed.rows) };
}
