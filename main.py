"""AgendaFlow - site Next.js e API FastAPI juntos na mesma aplicação Discloud.

O GitHub Actions compila o frontend estático em site/.
Somente FastAPI/Uvicorn executa na Discloud, em 0.0.0.0:8080.
"""
from pathlib import Path

import uvicorn
from fastapi import Request
from fastapi.staticfiles import StaticFiles

from app.main import app

SITE_DIR = Path(__file__).resolve().parent / "site"

# O React faz requisições para /api/public, /api/auth e /api/admin.
# Encaminhe esses caminhos à API FastAPI, sem rede externa ou outro servidor.
# Os caminhos antigos (/public, /auth, /admin) permanecem disponíveis
# durante a migração, para não interromper o frontend separado existente.
@app.middleware("http")
async def api_alias(request: Request, call_next):
    if request.scope["path"].startswith("/api/"):
        request.scope["path"] = request.scope["path"][4:]
        request.scope["raw_path"] = request.scope["path"].encode("utf-8")
    return await call_next(request)


if not (SITE_DIR / "index.html").is_file():
    raise RuntimeError(
        "Frontend nao compilado: site/index.html ausente. "
        "Confira o workflow GitHub Actions 'Compilar frontend do AgendaFlow unificado'."
    )

# Os endpoints de API foram registrados antes deste mount.
# Servir a pasta Next.js por último garante /, /admin/ e /minha-reserva/.
app.mount("/", StaticFiles(directory=str(SITE_DIR), html=True), name="site")


if __name__ == "__main__":
    print("[AgendaFlow] Frontend + API na mesma aplicacao: 0.0.0.0:8080", flush=True)
    uvicorn.run(app, host="0.0.0.0", port=8080, log_level="info")
