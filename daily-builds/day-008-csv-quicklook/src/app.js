import { quicklook } from "./csv.js";

const input = document.querySelector("#csv-input");
const delimiter = document.querySelector("#delimiter");
const status = document.querySelector("#status");
const table = document.querySelector("#preview");
const summary = document.querySelector("#summary");
const issues = document.querySelector("#issues");
const fileInput = document.querySelector("#file-input");

function render() {
  const result = quicklook(input.value, delimiter.value === "tab" ? "\t" : delimiter.value);
  status.textContent = `${result.rows.length} rows · ${result.headers.length} columns · showing ${result.preview.length}`;
  issues.textContent = result.errors.length ? result.errors.join(" ") : "No structural issues detected.";
  issues.dataset.state = result.errors.length ? "warning" : "ok";
  table.replaceChildren();
  if (!result.headers.length) return;
  const head = table.createTHead().insertRow();
  result.headers.forEach((header, index) => {
    const cell = document.createElement("th");
    cell.scope = "col";
    cell.textContent = header || `Column ${index + 1}`;
    head.append(cell);
  });
  const body = table.createTBody();
  result.preview.forEach((row) => {
    const tr = body.insertRow();
    result.headers.forEach((_, index) => {
      const cell = tr.insertCell();
      cell.textContent = row[index] ?? "";
    });
  });
  summary.replaceChildren(...result.summaries.map((item) => {
    const card = document.createElement("article");
    const title = document.createElement("strong");
    title.textContent = item.name;
    const detail = document.createElement("span");
    detail.textContent = `${item.filled} filled · ${item.empty} empty · ${item.unique} unique`;
    card.append(title, detail);
    return card;
  }));
}

document.querySelector("#analyze").addEventListener("click", render);
document.querySelector("#sample").addEventListener("click", () => {
  input.value = 'name,role,location\n"Ana Cruz",Designer,Manila\n"Mika Santos","Developer, Frontend",Cebu\n"Sam Lee",Developer,\n"Ana Cruz",Designer,Manila';
  render();
});
fileInput.addEventListener("change", async () => {
  const [file] = fileInput.files;
  if (!file) return;
  input.value = await file.text();
  render();
});
render();
