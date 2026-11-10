"""Inicializador da API FastAPI do AgendaFlow na Discloud."""
import uvicorn

if __name__ == "__main__":
    print("[AgendaFlow] Iniciando API FastAPI em 0.0.0.0:8080", flush=True)
    uvicorn.run("app.main:app", host="0.0.0.0", port=8080, log_level="info")
