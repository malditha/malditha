import { getMarkdownStats, renderMarkdown } from "./markdown.js";

const editor = document.querySelector("#editor");
const preview = document.querySelector("#preview");
const words = document.querySelector("#words");
const characters = document.querySelector("#characters");
const readingTime = document.querySelector("#reading-time");
const copyButton = document.querySelector("#copy-html");
const clearButton = document.querySelector("#clear-editor");
const status = document.querySelector("#status");

const starter = `# Markdown Split View

Write Markdown on the **left** and inspect safe HTML on the right.

## Quick checklist

- Add a useful heading
- Explain the idea clearly
- Include \`inline code\` when it helps

> The preview is generated locally. Your writing never leaves the browser.

\`\`\`js
const message = "Ship one useful thing.";
console.log(message);
\`\`\`

[View the 100 Days of Code collection](https://github.com/malditha/malditha/tree/main/daily-builds)
`;

function update() {
  const markdown = editor.value;
  preview.innerHTML = renderMarkdown(markdown) || '<p class="empty">Your preview will appear here.</p>';
  const stats = getMarkdownStats(markdown);
  words.textContent = String(stats.words);
  characters.textContent = String(stats.characters);
  readingTime.textContent = `${stats.minutes} min`;
}

async function copyHtml() {
  await navigator.clipboard.writeText(renderMarkdown(editor.value));
  status.textContent = "HTML copied";
  copyButton.textContent = "Copied!";
  window.setTimeout(() => { copyButton.textContent = "Copy HTML"; status.textContent = "Preview updated"; }, 1600);
}

editor.value = localStorage.getItem("markdown-split-view") || starter;
editor.addEventListener("input", () => { localStorage.setItem("markdown-split-view", editor.value); update(); });
copyButton.addEventListener("click", () => copyHtml().catch(() => { status.textContent = "Copy is unavailable"; }));
clearButton.addEventListener("click", () => { editor.value = ""; localStorage.removeItem("markdown-split-view"); editor.focus(); update(); });
update();
