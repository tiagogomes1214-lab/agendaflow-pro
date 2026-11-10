"""Bootstrap do backend AgendaFlow para deploy Discloud via GitHub."""
import sys
from pathlib import Path

import uvicorn

sys.path.insert(0, str(Path(__file__).resolve().parent / "backend"))

if __name__ == "__main__":
    print("[AgendaFlow] Iniciando API FastAPI na porta 8080", flush=True)
    uvicorn.run("app.main:app", host="0.0.0.0", port=8080, log_level="info")
