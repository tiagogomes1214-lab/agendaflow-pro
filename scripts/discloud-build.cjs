"use strict";

// Build do Next.js executado pela Discloud a partir da raiz do GitHub.
const fs = require("node:fs");
const path = require("node:path");
const { spawnSync } = require("node:child_process");

const root = path.resolve(__dirname, "..");
const frontend = path.join(root, "frontend");
const standalone = path.join(frontend, ".next", "standalone");
const dist = path.join(root, "dist");

function run(args) {
  const binary = process.platform === "win32" ? "npm.cmd" : "npm";
  const result = spawnSync(binary, args, {
    cwd: root,
    stdio: "inherit",
    env: { ...process.env, NODE_ENV: "production" },
    shell: process.platform === "win32"
  });
  if (result.error) throw result.error;
  if (result.status !== 0) process.exit(result.status || 1);
}

console.log("[AgendaFlow] Instalando dependencias do frontend.");
run(["--prefix", "frontend", "install", "--no-audit", "--no-fund", "--include=dev"]);
console.log("[AgendaFlow] Compilando Next.js em modo standalone.");
run(["--prefix", "frontend", "run", "build"]);

const serverInRoot = fs.existsSync(path.join(standalone, "server.js"));
const serverInFrontend = fs.existsSync(path.join(standalone, "frontend", "server.js"));
if (!serverInRoot && !serverInFrontend) {
  throw new Error("Next.js nao gerou standalone/server.js. Verifique frontend/next.config.ts e os logs de build.");
}
const prefix = serverInRoot ? "" : "frontend";
const serverRoot = prefix ? path.join(dist, prefix) : dist;

fs.rmSync(dist, { recursive: true, force: true });
fs.cpSync(standalone, dist, { recursive: true, dereference: true });

const staticDir = path.join(frontend, ".next", "static");
if (fs.existsSync(staticDir)) {
  const destination = path.join(serverRoot, ".next", "static");
  fs.mkdirSync(path.dirname(destination), { recursive: true });
  fs.cpSync(staticDir, destination, { recursive: true, dereference: true });
}
const publicDir = path.join(frontend, "public");
if (fs.existsSync(publicDir)) {
  fs.cpSync(publicDir, path.join(serverRoot, "public"), { recursive: true, dereference: true });
}
if (!fs.existsSync(path.join(serverRoot, ".next", "BUILD_ID"))) {
  throw new Error("O build standalone nao preservou .next/BUILD_ID.");
}
const entry = prefix ? "frontend/server.js" : "server.js";
fs.writeFileSync(path.join(dist, "agendaflow-build.json"), JSON.stringify({ entry }) + "\n");
console.log("[AgendaFlow] Build de producao salvo em dist/ com sucesso. Entrada: " + entry);
