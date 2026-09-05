import { inspectUrl, transformUrl } from "./url-tools.js";

const form = document.querySelector("#url-form");
const input = document.querySelector("#url-input");
const output = document.querySelector("#url-output");
const error = document.querySelector("#error");
const parts = document.querySelector("#url-parts");
const parameters = document.querySelector("#parameters");
const parameterCount = document.querySelector("#parameter-count");
const copyButton = document.querySelector("#copy-url");

function option(id) {
  return document.querySelector(id).checked;
}

function render() {
  try {
    const transformed = transformUrl(input.value, {
      removeTracking: option("#remove-tracking"),
      sortParameters: option("#sort-parameters"),
      stripHash: option("#strip-hash")
    });
    const details = inspectUrl(transformed);
    output.value = transformed;
    error.textContent = "";

    const values = [
      ["Protocol", details.protocol],
      ["Hostname", details.hostname],
      ["Port", details.port],
      ["Path", details.pathname],
      ["Fragment", details.hash || "none"]
    ];
    parts.innerHTML = values.map(([label, value]) =>
      `<div><span>${label}</span><strong>${escapeHtml(value)}</strong></div>`
    ).join("");

    parameterCount.textContent = `${details.parameters.length} parameter${details.parameters.length === 1 ? "" : "s"}`;
    parameters.innerHTML = details.parameters.length
      ? details.parameters.map(({ name, value, tracking }) =>
          `<li><code>${escapeHtml(name)}</code><span>${escapeHtml(value || "(empty)")}</span>${tracking ? "<em>tracking</em>" : ""}</li>`
        ).join("")
      : "<li class=\"empty\">No query parameters in this URL.</li>";
  } catch (problem) {
    output.value = "";
    parts.innerHTML = "";
    parameters.innerHTML = "<li class=\"empty\">Enter a valid URL to inspect its parameters.</li>";
    parameterCount.textContent = "0 parameters";
    error.textContent = problem instanceof Error ? problem.message : "Check the URL.";
  }
}

function escapeHtml(value) {
  return String(value)
    .replaceAll("&", "&amp;")
    .replaceAll("<", "&lt;")
    .replaceAll(">", "&gt;")
    .replaceAll('"', "&quot;")
    .replaceAll("'", "&#039;");
}

form.addEventListener("submit", (event) => {
  event.preventDefault();
  render();
});
form.addEventListener("change", render);
copyButton.addEventListener("click", async () => {
  if (!output.value) return;
  await navigator.clipboard.writeText(output.value);
  copyButton.textContent = "Copied ✓";
  window.setTimeout(() => { copyButton.textContent = "Copy URL"; }, 1400);
});

render();
