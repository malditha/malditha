import { createFormState, inspectField, isFormValid, resetForm, submitForm, touchField, updateField } from "./form-state.js";

const form = document.querySelector("form");
const inspector = document.querySelector("#inspector");
const eventOutput = document.querySelector("#event-output");
const status = document.querySelector("#status");
let state = createFormState();

function render() {
  inspector.replaceChildren(...Object.keys(state.values).map((name) => {
    const field = inspectField(state, name);
    const card = document.createElement("article");
    card.className = `state-card state-${field.status}`;
    const title = document.createElement("h3");
    title.textContent = name;
    const list = document.createElement("dl");
    [["value", field.value || "(empty)"], ["touched", field.touched], ["dirty", field.dirty], ["valid", field.valid], ["status", field.status]].forEach(([label, value]) => {
      const dt = document.createElement("dt"); dt.textContent = label;
      const dd = document.createElement("dd"); dd.textContent = String(value);
      list.append(dt, dd);
    });
    if (field.error) { const error = document.createElement("p"); error.textContent = field.error; card.append(title, list, error); }
    else card.append(title, list);
    return card;
  }));
  eventOutput.textContent = state.lastEvent;
  status.textContent = isFormValid(state) ? "Form is valid." : "Form needs attention.";
}

form.addEventListener("input", (event) => {
  const field = event.target;
  if (field.name) { state = updateField(state, field.name, field.value); render(); }
});
form.addEventListener("change", (event) => {
  const field = event.target;
  if (field.name) { state = updateField(state, field.name, field.value, "change"); render(); }
});
form.addEventListener("focusout", (event) => {
  if (event.target.name) { state = touchField(state, event.target.name); render(); }
});
form.addEventListener("submit", (event) => {
  event.preventDefault(); state = submitForm(state); render();
  status.textContent = isFormValid(state) ? "Valid submit captured locally—nothing was sent." : "Submit blocked. Review invalid fields.";
});
form.addEventListener("reset", () => {
  queueMicrotask(() => { state = resetForm(state); render(); });
});
render();
