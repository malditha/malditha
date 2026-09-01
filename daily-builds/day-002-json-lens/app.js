import { flattenJson, formatJson, minifyJson, parseJson, searchRows, summarizeJson } from "./json-lens.js";

const input = document.querySelector("#json-input");
const output = document.querySelector("#json-output");
const status = document.querySelector("#status");
const search = document.querySelector("#search");
const rows = document.querySelector("#rows");
const stats = document.querySelector("#stats");
let currentRows = [];

function renderRows(query = "") {
  const matches = searchRows(currentRows, query);
  rows.innerHTML = matches.length
    ? matches.map((row) => `<tr><td><code>${escapeHtml(row.path)}</code></td><td><span class="type">${row.type}</span></td><td>${escapeHtml(row.value)}</td></tr>`).join("")
    : '<tr><td colspan="3" class="empty">No matching values</td></tr>';
}

function escapeHtml(value) {
  return value.replace(/[&<>"']/g, (character) => ({ "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;", "'": "&#039;" })[character]);
}

function inspect(mode = "format") {
  const result = parseJson(input.value);
  if (!result.ok) {
    status.textContent = `Line ${result.error.line}, column ${result.error.column}: ${result.error.message}`;
    status.dataset.state = "error";
    output.value = "";
    currentRows = [];
    stats.textContent = "Fix the JSON to inspect its structure.";
    renderRows();
    return;
  }

  output.value = mode === "minify" ? minifyJson(result.value) : formatJson(result.value);
  currentRows = flattenJson(result.value);
  const summary = summarizeJson(result.value);
  status.textContent = `Valid JSON · ${summary.values} inspectable value${summary.values === 1 ? "" : "s"}`;
  status.dataset.state = "valid";
  stats.textContent = Object.entries(summary).map(([key, count]) => `${key}: ${count}`).join(" · ");
  renderRows(search.value);
}

document.querySelector("#format").addEventListener("click", () => inspect("format"));
document.querySelector("#minify").addEventListener("click", () => inspect("minify"));
document.querySelector("#sample").addEventListener("click", () => {
  input.value = JSON.stringify({ project: "JSON Lens", day: 2, skills: ["JavaScript", "testing"], complete: true }, null, 2);
  inspect();
});
document.querySelector("#copy").addEventListener("click", async () => {
  if (!output.value) return;
  await navigator.clipboard.writeText(output.value);
  status.textContent = "Output copied to clipboard.";
});
search.addEventListener("input", () => renderRows(search.value));
input.addEventListener("input", () => inspect());

document.querySelector("#sample").click();
