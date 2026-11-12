"""Teste integrado do AgendaFlow unificado; usa somente dados temporarios."""
import os
import sys
import tempfile
from pathlib import Path

# Execucao via python scripts/... precisa incluir a raiz do repositorio.
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from fastapi.testclient import TestClient

with tempfile.TemporaryDirectory(prefix="agendaflow-smoke-") as tmp:
    os.environ["DATABASE_URL"] = "sqlite+pysqlite:///" + str(Path(tmp) / "database.sqlite")
    os.environ["ADMIN_EMAIL"] = "teste@example.com"
    os.environ["ADMIN_PASSWORD"] = "SenhaApenasParaTeste123456"
    os.environ["JWT_SECRET"] = "ci-test-secret-not-for-production-12345678901234567890"
    os.environ.pop("DB_HOST", None)

    from main import app

    with TestClient(app) as client:
        for url in ("/", "/admin/", "/minha-reserva/"):
            response = client.get(url)
            assert response.status_code == 200, (url, response.status_code)
            assert "text/html" in response.headers["content-type"], url

        for url in ("/health", "/api/health"):
            response = client.get(url)
            assert response.status_code == 200 and response.json()["status"] == "ok", (url, response.text)

        for url in ("/public/services", "/api/public/services"):
            response = client.get(url)
            assert response.status_code == 200 and isinstance(response.json(), list), (url, response.text)

        login = client.post("/api/auth/login", json={
            "email": os.environ["ADMIN_EMAIL"],
            "password": os.environ["ADMIN_PASSWORD"],
        })
        assert login.status_code == 200, (login.status_code, login.text)
        token = login.json()["access_token"]
        stats = client.get("/api/admin/stats", headers={"Authorization": f"Bearer {token}"})
        assert stats.status_code == 200, (stats.status_code, stats.text)
        print("AgendaFlow unificado: paginas, API, login e painel OK")
