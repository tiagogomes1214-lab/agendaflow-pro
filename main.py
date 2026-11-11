"""AgendaFlow — frontend estático Next.js e API FastAPI na mesma aplicação.

Na Discloud, somente o Python é executado. O HTML/JS é compilado
antecipadamente pelo GitHub Actions e versionado na pasta site/.
"""
from contextlib import asynccontextmanager
from pathlib import Path

import uvicorn
from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles

from app.main import app as api

SITE_DIR = Path(__file__).resolve().parent / "site"


@asynccontextmanager
async def lifespan(_app: FastAPI):
    # Aplicações FastAPI montadas não iniciam o lifespan automaticamente.
    # Preserva a inicialização do banco e da conta administrativa.
    async with api.router.lifespan_context(api):
        yield


app = FastAPI(lifespan=lifespan, docs_url=None, redoc_url=None, openapi_url=None)


@app.get("/health")
def health():
    return {"status": "ok", "version": "2.0.0", "deployment": "unificado"}


# O frontend chama /api/public/..., /api/auth/... e /api/admin/...
# Esses endpoints são tratados pelo FastAPI no mesmo host e porta.
app.mount("/api", api)

# A pasta site/ contém a exportação estática do Next.js, criada pelo workflow.
if not (SITE_DIR / "index.html").is_file():
    raise RuntimeError(
        "Frontend nao compilado: pasta site/index.html ausente. "
        "Verifique o workflow Build Frontend Unificado do GitHub Actions."
    )
app.mount("/", StaticFiles(directory=str(SITE_DIR), html=True), name="frontend")


if __name__ == "__main__":
    print("[AgendaFlow] SITE + API no mesmo endereco: 0.0.0.0:8080", flush=True)
    uvicorn.run(app, host="0.0.0.0", port=8080, log_level="info")
