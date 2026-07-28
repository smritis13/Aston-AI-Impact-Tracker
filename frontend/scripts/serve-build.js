const fs = require("fs");
const http = require("http");
const path = require("path");

const port = Number(process.env.PORT || 3002);
const buildDir = path.resolve(__dirname, "..", "build");

const contentTypes = {
  ".css": "text/css; charset=utf-8",
  ".html": "text/html; charset=utf-8",
  ".js": "application/javascript; charset=utf-8",
  ".json": "application/json; charset=utf-8",
  ".map": "application/json; charset=utf-8",
  ".png": "image/png",
  ".jpg": "image/jpeg",
  ".jpeg": "image/jpeg",
  ".svg": "image/svg+xml",
  ".ico": "image/x-icon",
  ".woff": "font/woff",
  ".woff2": "font/woff2",
  ".ttf": "font/ttf",
};

const sendFile = (res, filePath) => {
  fs.readFile(filePath, (error, data) => {
    if (error) {
      res.writeHead(404, { "Content-Type": "text/plain; charset=utf-8" });
      res.end("Not found");
      return;
    }

    const ext = path.extname(filePath).toLowerCase();
    res.writeHead(200, {
      "Cache-Control": "no-store",
      "Content-Type": contentTypes[ext] || "application/octet-stream",
    });
    res.end(data);
  });
};

const server = http.createServer((req, res) => {
  const urlPath = decodeURIComponent((req.url || "/").split("?")[0]);
  const requestedPath = path.normalize(urlPath).replace(/^(\.\.[/\\])+/, "");
  const filePath = path.join(buildDir, requestedPath === "/" ? "index.html" : requestedPath);

  if (!filePath.startsWith(buildDir)) {
    res.writeHead(403, { "Content-Type": "text/plain; charset=utf-8" });
    res.end("Forbidden");
    return;
  }

  fs.stat(filePath, (error, stats) => {
    if (!error && stats.isFile()) {
      sendFile(res, filePath);
      return;
    }

    sendFile(res, path.join(buildDir, "index.html"));
  });
});

server.listen(port, "0.0.0.0", () => {
  console.log(`Serving ${buildDir} on http://localhost:${port}`);
});
