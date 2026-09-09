import { buildGitignore, presets, ruleGroups, summarizeGitignore } from "./core.js";

const groupList = document.querySelector("#group-list");
const customInput = document.querySelector("#custom-patterns");
const output = document.querySelector("#output");
const status = document.querySelector("#status");
const summary = document.querySelector("#summary");

for (const [id, group] of Object.entries(ruleGroups)) {
  const label = document.createElement("label");
  label.className = "rule-card";
  label.innerHTML = `<input type="checkbox" value="${id}"><span>${group.label}</span><small>${group.rules.length} rules</small>`;
  groupList.append(label);
}

function selectedGroups() {
  return [...groupList.querySelectorAll("input:checked")].map((input) => input.value);
}

function render(message = "Preview updated.") {
  try {
    const report = summarizeGitignore(selectedGroups(), customInput.value);
    output.value = report.output;
    summary.textContent = `${report.groups} groups · ${report.rules} unique rules`;
    status.textContent = message;
  } catch (error) {
    status.textContent = error.message;
  }
}

document.querySelectorAll("[data-preset]").forEach((button) => {
  button.addEventListener("click", () => {
    const wanted = new Set(presets[button.dataset.preset]);
    groupList.querySelectorAll("input").forEach((input) => { input.checked = wanted.has(input.value); });
    render(`${button.textContent.trim()} preset applied.`);
  });
});

groupList.addEventListener("change", () => render());
customInput.addEventListener("input", () => render());

document.querySelector("#copy").addEventListener("click", async () => {
  if (!output.value) return render("Choose at least one rule group.");
  await navigator.clipboard.writeText(output.value);
  status.textContent = "Copied .gitignore to clipboard.";
});

document.querySelector("#download").addEventListener("click", () => {
  const content = buildGitignore(selectedGroups(), customInput.value);
  if (!content) return render("Choose at least one rule group.");
  const link = document.createElement("a");
  link.href = URL.createObjectURL(new Blob([content], { type: "text/plain" }));
  link.download = ".gitignore";
  link.click();
  URL.revokeObjectURL(link.href);
  status.textContent = "Downloaded .gitignore.";
});

document.querySelector('[data-preset="next-app"]').click();
