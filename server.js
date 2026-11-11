"use strict";

const fs = require("node:fs");
const path = require("node:path");

process.env.NODE_ENV = "production";

// Host e porta fixos no codigo gerado pelo BUILD (nao dependem do .env).
const SITE_HOST = "0.0.0.0";
const SITE_PORT = 8080;

const dist = path.join(__dirname, "dist");
const manifestPath = path.join(dist, "agendaflow-build.json");
if (!fs.existsSync(manifestPath)) {
  console.error("[AgendaFlow] Arquivos de build ausentes em dist/.");
  console.error("[AgendaFlow] Confirme que BUILD=npm run build terminou com sucesso nos logs do build.");
  process.exit(1);
}

const manifest = JSON.parse(fs.readFileSync(manifestPath, "utf8"));
if (!["server.js", "frontend/server.js"].includes(manifest.entry)) {
  throw new Error("Manifesto de build invalido.");
}
const entry = path.join(dist, manifest.entry);
const buildId = path.join(path.dirname(entry), ".next", "BUILD_ID");
if (!fs.existsSync(entry) || !fs.existsSync(buildId)) {
  console.error("[AgendaFlow] Build incompleto. Releia os logs do BUILD no painel Discloud.");
  process.exit(1);
}

console.log(`[AgendaFlow] Iniciando Next.js no host ${SITE_HOST}, porta ${SITE_PORT} (fixos no codigo).`);
require(entry);
