import { contrastResults, normalizeHex, suggestForeground } from "./contrast.js";

const form = document.querySelector("form");
const foregroundText = document.querySelector("#foreground-text");
const backgroundText = document.querySelector("#background-text");
const foregroundPicker = document.querySelector("#foreground-picker");
const backgroundPicker = document.querySelector("#background-picker");
const ratioOutput = document.querySelector("#ratio");
const verdict = document.querySelector("#verdict");
const checks = document.querySelector("#checks");
const preview = document.querySelector("#preview");
const suggestion = document.querySelector("#suggestion");
const suggestionButton = document.querySelector("#use-suggestion");
const error = document.querySelector("#error");
const swapButton = document.querySelector("#swap");

let suggestedColor = "";

function sync(source, target) {
  source.addEventListener("input", () => {
    try {
      target.value = normalizeHex(source.value);
      render();
    } catch {
      error.textContent = "Enter a valid hex color such as #1748e8.";
    }
  });
}

function render() {
  try {
    const foreground = normalizeHex(foregroundText.value);
    const background = normalizeHex(backgroundText.value);
    const results = contrastResults(foreground, background);
    suggestedColor = suggestForeground(foreground, background);

    foregroundPicker.value = foreground;
    backgroundPicker.value = background;
    preview.style.setProperty("--preview-fg", foreground);
    preview.style.setProperty("--preview-bg", background);
    ratioOutput.textContent = `${results.ratio.toFixed(2)}:1`;
    verdict.textContent = results.normalAA ? "Readable for normal text" : "Needs stronger contrast";
    verdict.dataset.pass = String(results.normalAA);
    error.textContent = "";

    const rows = [
      ["Normal text AA", results.normalAA, "4.5:1"],
      ["Normal text AAA", results.normalAAA, "7:1"],
      ["Large text AA", results.largeAA, "3:1"],
      ["Large text AAA", results.largeAAA, "4.5:1"],
      ["UI components", results.uiAA, "3:1"]
    ];
    checks.innerHTML = rows.map(([label, pass, target]) => `<li><span>${label}<small>Target ${target}</small></span><strong class="${pass ? "pass" : "fail"}">${pass ? "PASS" : "FAIL"}</strong></li>`).join("");
    suggestion.textContent = results.normalAA ? "Current foreground already passes AA." : `Try ${suggestedColor} for ${contrastResults(suggestedColor, background).ratio.toFixed(2)}:1.`;
    suggestionButton.hidden = results.normalAA;
  } catch (problem) {
    error.textContent = problem instanceof Error ? problem.message : "Check both colors.";
  }
}

sync(foregroundText, foregroundPicker);
sync(backgroundText, backgroundPicker);
sync(foregroundPicker, foregroundText);
sync(backgroundPicker, backgroundText);
form.addEventListener("submit", (event) => { event.preventDefault(); render(); });
swapButton.addEventListener("click", () => {
  [foregroundText.value, backgroundText.value] = [backgroundText.value, foregroundText.value];
  render();
});
suggestionButton.addEventListener("click", () => {
  foregroundText.value = suggestedColor;
  render();
  foregroundText.focus();
});

render();
