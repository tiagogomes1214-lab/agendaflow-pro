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

// O servidor standalone gerado pelo Next.js costuma ler PORT e HOSTNAME
// do ambiente antes que o Next carregue .env. Para a Discloud, fixamos
// os valores DIRETAMENTE no codigo gerado, sem depender dessas variaveis.
// A alteracao ocorre a cada BUILD, preservando a estrutura standalone.
const generatedEntry = path.join(dist, entry);
let generatedCode = fs.readFileSync(generatedEntry, "utf8");
const portPattern = /^([ \\t]*)const currentPort\\s*=\\s*[^\\r\\n]*process\\.env\\.PORT[^\\r\\n]*$/m;
const hostPattern = /^([ \\t]*)const hostname\\s*=\\s*[^\\r\\n]*process\\.env\\.HOSTNAME[^\\r\\n]*$/m;
if (!portPattern.test(generatedCode) || !hostPattern.test(generatedCode)) {
  throw new Error("[AgendaFlow] O formato do servidor standalone mudou. Nao foi possivel definir host e porta no codigo; verifique a versao do Next.js.");
}
generatedCode = generatedCode
  .replace(portPattern, "$1const currentPort = 8080; // Discloud: porta fixa no codigo")
  .replace(hostPattern, "$1const hostname = '0.0.0.0'; // Discloud: host fixo no codigo");
fs.writeFileSync(generatedEntry, generatedCode);
const check = spawnSync(process.execPath, ["--check", generatedEntry], { stdio: "inherit" });
if (check.status !== 0) {
  throw new Error("[AgendaFlow] A validacao de sintaxe do servidor gerado falhou.");
}
console.log("[AgendaFlow] HOST e PORT fixados no codigo do Next.js: 0.0.0.0:8080.");
fs.writeFileSync(path.join(dist, "agendaflow-build.json"), JSON.stringify({ entry }) + "\n");
console.log("[AgendaFlow] Build de producao salvo em dist/ com sucesso. Entrada: " + entry);
