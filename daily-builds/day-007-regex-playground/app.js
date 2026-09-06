const patternInput = document.querySelector("#pattern");
const textInput = document.querySelector("#test-text");
const replacementInput = document.querySelector("#replacement");
const flagInputs = [...document.querySelectorAll("[name=flag]")];
const status = document.querySelector("#status");
const highlighted = document.querySelector("#highlighted");
const matchList = document.querySelector("#match-list");
const replacementOutput = document.querySelector("#replacement-output");

function selectedFlags() {
  return flagInputs.filter((input) => input.checked).map((input) => input.value).join("");
}

function renderText(segments) {
  highlighted.replaceChildren();
  for (const segment of segments) {
    const node = segment.match ? document.createElement("mark") : document.createTextNode(segment.text);
    if (segment.match) node.textContent = segment.text;
    highlighted.append(node);
  }
}

function renderMatches(matches) {
  matchList.replaceChildren();
  if (!matches.length) {
    const item = document.createElement("li");
    item.textContent = "No matches yet.";
    matchList.append(item);
    return;
  }
  matches.forEach((match, number) => {
    const item = document.createElement("li");
    const title = document.createElement("strong");
    title.textContent = `#${number + 1} · index ${match.index}–${match.end}`;
    const value = document.createElement("code");
    value.textContent = match.value || "(empty match)";
    item.append(title, value);
    if (match.groups.length) {
      const groups = document.createElement("small");
      groups.textContent = `Groups: ${match.groups.map((value) => value ?? "undefined").join(" · ")}`;
      item.append(groups);
    }
    matchList.append(item);
  });
}

function update() {
  try {
    const source = patternInput.value;
    const flags = selectedFlags();
    const text = textInput.value;
    const result = RegexTools.collectMatches(source, flags, text);
    status.className = "status is-valid";
    status.textContent = `${result.matches.length} match${result.matches.length === 1 ? "" : "es"}${result.truncated ? " · first 200 shown" : ""}`;
    renderText(RegexTools.buildSegments(text, result.matches));
    renderMatches(result.matches);
    replacementOutput.textContent = replacementInput.value
      ? RegexTools.previewReplacement(source, flags, text, replacementInput.value)
      : "Add replacement text to preview the result.";
  } catch (error) {
    status.className = "status is-error";
    status.textContent = error.message;
    highlighted.textContent = textInput.value;
    matchList.replaceChildren();
    replacementOutput.textContent = "Fix the pattern to see a replacement preview.";
  }
}

document.querySelector("#playground").addEventListener("input", update);
document.querySelector("#sample").addEventListener("click", () => {
  patternInput.value = "(?<user>[a-z0-9._%+-]+)@(?<domain>[a-z0-9.-]+\\.[a-z]{2,})";
  textInput.value = "Send the brief to hello@example.com or studio@example.org.";
  replacementInput.value = "[$<user> at $<domain>]";
  document.querySelector("[value=g]").checked = true;
  document.querySelector("[value=i]").checked = true;
  update();
});

update();
