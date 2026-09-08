import { createServer } from "node:http";
import { readFile } from "node:fs/promises";
import { extname, join } from "node:path";

const root = new URL(".", import.meta.url).pathname;
const types = { ".html": "text/html; charset=utf-8", ".css": "text/css; charset=utf-8", ".js": "text/javascript; charset=utf-8" };

createServer(async (request, response) => {
  const pathname = request.url === "/" ? "/index.html" : request.url.split("?")[0];
  try {
    const file = await readFile(join(root, pathname));
    response.writeHead(200, { "Content-Type": types[extname(pathname)] || "application/octet-stream" });
    response.end(file);
  } catch {
    response.writeHead(404, { "Content-Type": "text/plain; charset=utf-8" });
    response.end("Not found");
  }
}).listen(4173, "127.0.0.1", () => console.log("Form State Debugger: http://localhost:4173"));
