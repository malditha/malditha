const escapeHtml = (value) => value
  .replaceAll("&", "&amp;")
  .replaceAll("<", "&lt;")
  .replaceAll(">", "&gt;")
  .replaceAll('"', "&quot;")
  .replaceAll("'", "&#39;");

function safeHref(value) {
  const href = value.trim();
  return /^(https?:\/\/|mailto:|#|\/)/i.test(href) ? escapeHtml(href) : "#";
}

export function renderInline(source) {
  const code = [];
  let text = escapeHtml(source).replace(/`([^`]+)`/g, (_, value) => {
    code.push(`<code>${value}</code>`);
    return `\u0000CODE${code.length - 1}\u0000`;
  });

  text = text
    .replace(/!\[([^\]]*)\]\(([^)]+)\)/g, (_, alt, url) => `<img src="${safeHref(url)}" alt="${alt}">`)
    .replace(/\[([^\]]+)\]\(([^)]+)\)/g, (_, label, url) => `<a href="${safeHref(url)}" target="_blank" rel="noreferrer">${label}</a>`)
    .replace(/\*\*([^*]+)\*\*/g, "<strong>$1</strong>")
    .replace(/__([^_]+)__/g, "<strong>$1</strong>")
    .replace(/(^|[^*])\*([^*]+)\*/g, "$1<em>$2</em>")
    .replace(/(^|[^_])_([^_]+)_/g, "$1<em>$2</em>")
    .replace(/~~([^~]+)~~/g, "<del>$1</del>");

  return text.replace(/\u0000CODE(\d+)\u0000/g, (_, index) => code[Number(index)]);
}

export function renderMarkdown(markdown) {
  const lines = markdown.replace(/\r\n?/g, "\n").split("\n");
  const html = [];
  let paragraph = [];
  let listType = null;
  let quote = [];
  let code = null;
  let language = "";

  const flushParagraph = () => {
    if (paragraph.length) html.push(`<p>${renderInline(paragraph.join(" "))}</p>`);
    paragraph = [];
  };
  const closeList = () => {
    if (listType) html.push(`</${listType}>`);
    listType = null;
  };
  const flushQuote = () => {
    if (quote.length) html.push(`<blockquote>${renderInline(quote.join(" "))}</blockquote>`);
    quote = [];
  };
  const flushOpenBlocks = () => { flushParagraph(); closeList(); flushQuote(); };

  for (const line of lines) {
    const fence = line.match(/^```\s*([\w-]*)/);
    if (fence) {
      if (code !== null) {
        html.push(`<pre><code${language ? ` class="language-${escapeHtml(language)}"` : ""}>${escapeHtml(code.join("\n"))}</code></pre>`);
        code = null;
        language = "";
      } else {
        flushOpenBlocks();
        code = [];
        language = fence[1];
      }
      continue;
    }
    if (code !== null) { code.push(line); continue; }

    if (!line.trim()) { flushOpenBlocks(); continue; }

    const heading = line.match(/^(#{1,6})\s+(.+)$/);
    if (heading) {
      flushOpenBlocks();
      const level = heading[1].length;
      html.push(`<h${level}>${renderInline(heading[2])}</h${level}>`);
      continue;
    }
    if (/^([-*_])(?:\s*\1){2,}\s*$/.test(line)) {
      flushOpenBlocks(); html.push("<hr>"); continue;
    }
    const unordered = line.match(/^\s*[-+*]\s+(.+)$/);
    const ordered = line.match(/^\s*\d+[.)]\s+(.+)$/);
    if (unordered || ordered) {
      flushParagraph(); flushQuote();
      const type = ordered ? "ol" : "ul";
      if (listType !== type) { closeList(); listType = type; html.push(`<${type}>`); }
      html.push(`<li>${renderInline((unordered || ordered)[1])}</li>`);
      continue;
    }
    const quoted = line.match(/^>\s?(.*)$/);
    if (quoted) {
      flushParagraph(); closeList(); quote.push(quoted[1]); continue;
    }

    closeList(); flushQuote(); paragraph.push(line.trim());
  }

  if (code !== null) html.push(`<pre><code>${escapeHtml(code.join("\n"))}</code></pre>`);
  flushOpenBlocks();
  return html.join("\n");
}

export function getMarkdownStats(markdown) {
  const plain = markdown
    .replace(/```[\s\S]*?```/g, " ")
    .replace(/!?(\[([^\]]*)\])\([^)]+\)/g, "$2")
    .replace(/[#>*_~`-]/g, " ")
    .trim();
  const words = plain ? plain.split(/\s+/).length : 0;
  return { words, characters: markdown.length, minutes: Math.max(1, Math.ceil(words / 200)) };
}
