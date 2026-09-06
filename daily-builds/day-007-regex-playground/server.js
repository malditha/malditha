const http = require("node:http");
const { readFile } = require("node:fs/promises");
const { extname, join } = require("node:path");

const port = Number(process.env.PORT) || 4173;
const files = { "/": "index.html", "/index.html": "index.html", "/style.css": "style.css", "/regex-tools.js": "regex-tools.js", "/app.js": "app.js" };
const types = { ".html": "text/html; charset=utf-8", ".css": "text/css; charset=utf-8", ".js": "text/javascript; charset=utf-8" };

http.createServer(async (request, response) => {
  const pathname = new URL(request.url, "http://localhost").pathname;
  const file = files[pathname];
  if (!file) { response.writeHead(404, { "content-type": "text/plain; charset=utf-8" }); response.end("Not found"); return; }
  try {
    const body = await readFile(join(__dirname, file));
    response.writeHead(200, { "content-type": types[extname(file)], "x-content-type-options": "nosniff" });
    response.end(body);
  } catch {
    response.writeHead(500, { "content-type": "text/plain; charset=utf-8" });
    response.end("Unable to load the playground.");
  }
}).listen(port, () => console.log(`Regex Playground: http://localhost:${port}`));
