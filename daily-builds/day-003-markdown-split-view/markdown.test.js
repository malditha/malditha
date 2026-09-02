import test from "node:test";
import assert from "node:assert/strict";
import { getMarkdownStats, renderInline, renderMarkdown } from "./markdown.js";

test("renders core block elements", () => {
  const result = renderMarkdown("# Title\n\n- one\n- two\n\n> useful note");
  assert.match(result, /<h1>Title<\/h1>/);
  assert.match(result, /<ul>[\s\S]*<li>one<\/li>[\s\S]*<li>two<\/li>[\s\S]*<\/ul>/);
  assert.match(result, /<blockquote>useful note<\/blockquote>/);
});

test("renders fenced code without interpreting markup", () => {
  const result = renderMarkdown("```html\n<button>Save</button>\n```");
  assert.equal(result, '<pre><code class="language-html">&lt;button&gt;Save&lt;/button&gt;</code></pre>');
});

test("escapes raw HTML and blocks unsafe links", () => {
  assert.equal(renderMarkdown('<script>alert("x")</script>'), '<p>&lt;script&gt;alert(&quot;x&quot;)&lt;/script&gt;</p>');
  assert.match(renderInline("[bad](javascript:alert(1))"), /href="#"/);
});

test("keeps safe links and inline formatting", () => {
  const result = renderInline("**bold** and `code` at [home](https://example.com)");
  assert.match(result, /<strong>bold<\/strong>/);
  assert.match(result, /<code>code<\/code>/);
  assert.match(result, /href="https:\/\/example.com"/);
});

test("calculates writing statistics", () => {
  assert.deepEqual(getMarkdownStats("# One two three"), { words: 3, characters: 15, minutes: 1 });
  assert.deepEqual(getMarkdownStats(""), { words: 0, characters: 0, minutes: 1 });
});
