const HEX_PATTERN = /^#?([\da-f]{3}|[\da-f]{6})$/i;

export function normalizeHex(value) {
  const input = String(value ?? "").trim();
  const match = input.match(HEX_PATTERN);
  if (!match) throw new TypeError("Enter a 3- or 6-digit hexadecimal color.");

  const digits = match[1].toLowerCase();
  return `#${digits.length === 3 ? [...digits].map((digit) => digit.repeat(2)).join("") : digits}`;
}

export function hexToRgb(value) {
  const hex = normalizeHex(value).slice(1);
  return {
    r: Number.parseInt(hex.slice(0, 2), 16),
    g: Number.parseInt(hex.slice(2, 4), 16),
    b: Number.parseInt(hex.slice(4, 6), 16)
  };
}

export function relativeLuminance(value) {
  const channels = Object.values(hexToRgb(value)).map((channel) => {
    const srgb = channel / 255;
    return srgb <= 0.04045 ? srgb / 12.92 : ((srgb + 0.055) / 1.055) ** 2.4;
  });
  return 0.2126 * channels[0] + 0.7152 * channels[1] + 0.0722 * channels[2];
}

export function contrastRatio(foreground, background) {
  const light = Math.max(relativeLuminance(foreground), relativeLuminance(background));
  const dark = Math.min(relativeLuminance(foreground), relativeLuminance(background));
  return (light + 0.05) / (dark + 0.05);
}

export function contrastResults(foreground, background) {
  const ratio = contrastRatio(foreground, background);
  return {
    ratio,
    normalAA: ratio >= 4.5,
    normalAAA: ratio >= 7,
    largeAA: ratio >= 3,
    largeAAA: ratio >= 4.5,
    uiAA: ratio >= 3
  };
}

function rgbToHex({ r, g, b }) {
  const channel = (value) => Math.round(value).toString(16).padStart(2, "0");
  return `#${channel(r)}${channel(g)}${channel(b)}`;
}

function mix(start, end, amount) {
  const from = hexToRgb(start);
  const to = hexToRgb(end);
  return rgbToHex({
    r: from.r + (to.r - from.r) * amount,
    g: from.g + (to.g - from.g) * amount,
    b: from.b + (to.b - from.b) * amount
  });
}

export function suggestForeground(foreground, background, target = 4.5) {
  const current = normalizeHex(foreground);
  const backdrop = normalizeHex(background);
  if (contrastRatio(current, backdrop) >= target) return current;

  const candidates = ["#000000", "#ffffff"].map((destination) => {
    for (let step = 1; step <= 100; step += 1) {
      const candidate = mix(current, destination, step / 100);
      if (contrastRatio(candidate, backdrop) >= target) return { color: candidate, step };
    }
    return { color: destination, step: Number.POSITIVE_INFINITY };
  });

  const passing = candidates.filter(({ color }) => contrastRatio(color, backdrop) >= target);
  return (passing.sort((a, b) => a.step - b.step)[0] ?? candidates[0]).color;
}
