export const ruleGroups = {
  secrets: {
    label: "Secrets & local configuration",
    rules: [".env", ".env.*", "!.env.example", "*.pem", "*.key", "credentials.json"]
  },
  node: {
    label: "Node.js",
    rules: ["node_modules/", ".npm/", ".pnpm-store/", "npm-debug.log*", "yarn-debug.log*", "yarn-error.log*"]
  },
  nextjs: {
    label: "Next.js",
    rules: [".next/", "out/", ".vercel/", "next-env.d.ts"]
  },
  python: {
    label: "Python",
    rules: ["__pycache__/", "*.py[cod]", ".venv/", "venv/", ".pytest_cache/", ".coverage", "htmlcov/"]
  },
  docker: {
    label: "Docker overrides",
    rules: ["docker-compose.override.yml", "*.local.yml"]
  },
  vscode: {
    label: "VS Code",
    rules: [".vscode/*", "!.vscode/extensions.json", "!.vscode/settings.example.json"]
  },
  jetbrains: {
    label: "JetBrains IDEs",
    rules: [".idea/", "*.iml"]
  },
  macos: {
    label: "macOS",
    rules: [".DS_Store", ".AppleDouble", ".LSOverride"]
  },
  windows: {
    label: "Windows",
    rules: ["Thumbs.db", "Desktop.ini", "$RECYCLE.BIN/"]
  },
  linux: {
    label: "Linux",
    rules: ["*~", ".fuse_hidden*", ".directory", ".Trash-*"]
  },
  logs: {
    label: "Logs & runtime files",
    rules: ["logs/", "*.log", "*.pid", "*.seed", "*.pid.lock"]
  },
  coverage: {
    label: "Test coverage",
    rules: ["coverage/", ".nyc_output/", "junit.xml"]
  }
};

export const presets = {
  "next-app": ["secrets", "node", "nextjs", "logs", "coverage"],
  "python-app": ["secrets", "python", "logs"],
  "mixed-stack": ["secrets", "node", "nextjs", "python", "docker", "logs", "coverage"]
};

export function normalizePattern(value) {
  const pattern = String(value ?? "").trim().replaceAll("\\", "/");
  if (!pattern || pattern.startsWith("#")) return "";
  if (/\r|\n|\0/.test(pattern)) throw new Error("Patterns must use one line each.");
  return pattern;
}

export function parseCustomPatterns(text) {
  const seen = new Set();
  return String(text ?? "")
    .split(/\r?\n/)
    .map(normalizePattern)
    .filter((pattern) => pattern && !seen.has(pattern) && seen.add(pattern));
}

export function buildGitignore(groupIds, customText = "") {
  const selected = [...new Set(groupIds)].filter((id) => ruleGroups[id]);
  const emitted = new Set();
  const sections = [];

  for (const id of selected) {
    const group = ruleGroups[id];
    const rules = group.rules.filter((rule) => !emitted.has(rule) && emitted.add(rule));
    if (rules.length) sections.push(`# ${group.label}\n${rules.join("\n")}`);
  }

  const custom = parseCustomPatterns(customText).filter((rule) => !emitted.has(rule) && emitted.add(rule));
  if (custom.length) sections.push(`# Custom project rules\n${custom.join("\n")}`);

  return sections.length ? `${sections.join("\n\n")}\n` : "";
}

export function summarizeGitignore(groupIds, customText = "") {
  const output = buildGitignore(groupIds, customText);
  const rules = output.split("\n").filter((line) => line && !line.startsWith("#"));
  return { groups: [...new Set(groupIds)].filter((id) => ruleGroups[id]).length, rules: rules.length, output };
}
