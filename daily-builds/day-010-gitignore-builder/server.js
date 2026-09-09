import { createServer } from "node:http";
import { readFile } from "node:fs/promises";
import { extname, join } from "node:path";

const port = Number(process.env.PORT || 4173);
const types = { ".html": "text/html; charset=utf-8", ".css": "text/css; charset=utf-8", ".js": "text/javascript; charset=utf-8" };

createServer(async (request, response) => {
  const pathname = new URL(request.url, `http://${request.headers.host}`).pathname;
  const file = pathname === "/" ? "index.html" : pathname.slice(1);
  if (file.includes("..")) { response.writeHead(400).end("Bad request"); return; }
  try {
    const content = await readFile(join(process.cwd(), file));
    response.writeHead(200, { "content-type": types[extname(file)] || "application/octet-stream" });
    response.end(content);
  } catch {
    response.writeHead(404, { "content-type": "text/plain; charset=utf-8" });
    response.end("Not found");
  }
}).listen(port, () => console.log(`Gitignore Builder: http://localhost:${port}`));
