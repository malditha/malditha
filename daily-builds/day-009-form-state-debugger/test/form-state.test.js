import test from "node:test";
import assert from "node:assert/strict";
import { createFormState, inspectField, isFormValid, resetForm, submitForm, touchField, updateField, validateValues } from "../src/form-state.js";

test("starts pristine and invalid", () => {
  const state = createFormState();
  assert.equal(inspectField(state, "name").status, "invalid");
  assert.equal(inspectField(state, "name").dirty, false);
  assert.equal(isFormValid(state), false);
});

test("input changes value and dirty state immutably", () => {
  const before = createFormState();
  const after = updateField(before, "name", "Kris");
  assert.equal(before.values.name, "");
  assert.equal(inspectField(after, "name").dirty, true);
  assert.equal(after.lastEvent, "input:name");
});

test("blur marks only the selected field touched", () => {
  const state = touchField(createFormState(), "email");
  assert.equal(state.touched.email, true);
  assert.equal(state.touched.name, false);
});

test("validates email and role", () => {
  const errors = validateValues({ name: "Kris", email: "wrong", role: "" });
  assert.match(errors.email, /valid email/);
  assert.match(errors.role, /Choose/);
});

test("reports a valid complete form", () => {
  let state = createFormState();
  state = updateField(state, "name", "Kris");
  state = updateField(state, "email", "kris@example.com");
  state = updateField(state, "role", "Developer");
  assert.equal(isFormValid(state), true);
  assert.equal(submitForm(state).lastEvent, "submit:valid");
});

test("blocked submit touches every field", () => {
  const state = submitForm(createFormState());
  assert.deepEqual(state.touched, { name: true, email: true, role: true });
  assert.equal(state.submitCount, 1);
  assert.equal(state.lastEvent, "submit:blocked");
});

test("reset returns to the recorded initial values", () => {
  const initial = createFormState({ name: "K", email: "", role: "" });
  const changed = updateField(initial, "name", "Kris");
  const reset = resetForm(changed);
  assert.equal(reset.values.name, "K");
  assert.equal(reset.submitCount, 0);
});
