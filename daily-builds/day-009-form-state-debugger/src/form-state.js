export const fieldRules = {
  name: (value) => value.trim().length >= 2 ? "" : "Enter at least 2 characters.",
  email: (value) => /^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(value.trim()) ? "" : "Enter a valid email address.",
  role: (value) => value ? "" : "Choose a role."
};

export function createFormState(initial = { name: "", email: "", role: "" }) {
  return {
    initial: { ...initial },
    values: { ...initial },
    touched: Object.fromEntries(Object.keys(initial).map((key) => [key, false])),
    errors: validateValues(initial),
    submitCount: 0,
    lastEvent: "initialized"
  };
}

export function validateValues(values) {
  return Object.fromEntries(Object.entries(values).map(([key, value]) => [key, fieldRules[key]?.(String(value)) || ""]));
}

export function updateField(state, name, value, event = "input") {
  if (!(name in state.values)) return state;
  const values = { ...state.values, [name]: value };
  return { ...state, values, errors: validateValues(values), lastEvent: `${event}:${name}` };
}

export function touchField(state, name) {
  if (!(name in state.values)) return state;
  return { ...state, touched: { ...state.touched, [name]: true }, lastEvent: `blur:${name}` };
}

export function submitForm(state) {
  const touched = Object.fromEntries(Object.keys(state.values).map((key) => [key, true]));
  const errors = validateValues(state.values);
  return { ...state, touched, errors, submitCount: state.submitCount + 1, lastEvent: Object.values(errors).some(Boolean) ? "submit:blocked" : "submit:valid" };
}

export function resetForm(state) {
  return createFormState(state.initial);
}

export function inspectField(state, name) {
  const value = state.values[name] ?? "";
  const dirty = value !== state.initial[name];
  const error = state.errors[name] || "";
  return { name, value, touched: Boolean(state.touched[name]), dirty, valid: !error, error, status: error ? "invalid" : dirty ? "ready" : "pristine" };
}

export function isFormValid(state) {
  return !Object.values(state.errors).some(Boolean);
}
