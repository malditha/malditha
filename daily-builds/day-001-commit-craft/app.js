const form = document.querySelector("#commit-form");
const preview = document.querySelector("#preview");
const errors = document.querySelector("#errors");
const status = document.querySelector("#status");
const counter = document.querySelector("#counter");
const copyButton = document.querySelector("#copy");

function values() {
  const data = new FormData(form);
  return {
    type: data.get("type"), scope: data.get("scope"), summary: data.get("summary"),
    body: data.get("body"), issue: data.get("issue"), breaking: data.get("breaking") === "on"
  };
}

function render() {
  const result = window.CommitCraft.validateCommit(values());
  preview.textContent = result.message;
  counter.textContent = result.headerLength + " / 72";
  counter.classList.toggle("over", result.headerLength > 72);
  status.textContent = result.valid ? "Ready" : "Needs edit";
  status.classList.toggle("warning", !result.valid);
  errors.replaceChildren(...result.errors.map(function (message) {
    const item = document.createElement("li"); item.textContent = message; return item;
  }));
  copyButton.disabled = !result.valid;
}

async function copyMessage() {
  const message = window.CommitCraft.buildCommit(values());
  try {
    await navigator.clipboard.writeText(message);
  } catch (_error) {
    const area = document.createElement("textarea"); area.value = message; document.body.append(area);
    area.select(); document.execCommand("copy"); area.remove();
  }
  copyButton.firstChild.textContent = "Copied ";
  window.setTimeout(function () { copyButton.firstChild.textContent = "Copy commit message "; }, 1400);
}

form.addEventListener("input", render);
copyButton.addEventListener("click", copyMessage);
render();
