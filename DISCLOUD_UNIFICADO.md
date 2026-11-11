# AgendaFlow Pro — Frontend e API em uma unica aplicacao Discloud

## Arquitetura
- **Um processo de runtime**: Python + Uvicorn + FastAPI, em `0.0.0.0:8080`.
- **Frontend**: paginas Next.js compiladas estaticamente no GitHub Actions e servidas pelo FastAPI a partir de `site/`.
- **API**: mesmo host, rota `/api/*` (inclui `/api/health`, `/api/auth/login`, `/api/public/...` e `/api/admin/...`).
- **Compatibilidade**: endpoints antigos `/health`, `/public`, `/auth` e `/admin/...` ainda respondem. Assim, o frontend antigo pode continuar consultando a API durante a migracao.
- **Banco de dados**: Supabase PostgreSQL, sem alterar dados ou senhas.

## Compilacao
O workflow `.github/workflows/build-frontend-unificado.yml` roda automaticamente quando esta branch recebe alteracoes.
Ele executa `next build` no GitHub e publica os arquivos HTML/CSS/JS em `site/`.
A Discloud **nao precisa executar Next.js ou Node**: sua imagem Python instala as dependencias do `requirements.txt` da raiz.

Verifique se a branch contem estes arquivos antes de mudar o deploy:
- `site/index.html`
- `site/admin/index.html`
- `site/minha-reserva/index.html`

## Migracao sem excluir o sistema existente
1. Mantenha a aplicacao **agendaflow** (Python) e suas variaveis DB_*, JWT_SECRET, ADMIN_EMAIL, ADMIN_PASSWORD etc.
2. No GitHub integrado da aplicacao **agendaflow**, selecione a branch **discloud-unificado** e execute **Rebuild**.
3. O novo `discloud.config` tem **ID=agendaflow**, **TYPE=site**, **VERSION=3.11**, **RAM=512**, **MAIN=main.py** e **START=python main.py**.
4. Teste `https://agendaflow.discloud.dev/health` — deve retornar status ok.
5. Teste `https://agendaflow.discloud.dev/api/health` — tambem deve retornar status ok.
6. Abra `https://agendaflow.discloud.dev/`, `/admin/` e `/minha-reserva/`.
7. Teste login do gestor, consulta de servicos, horarios e reserva usando **dados de teste**.
8. So depois de conferir tudo, pare a aplicacao de frontend antiga **agendaflow-tiago** para liberar 512 MB. Nao exclua antes da validacao.

**Atencao:** o site unificado sera servido no dominio da aplicacao Python, `agendaflow.discloud.dev`. O antigo dominio do frontend `agendaflow-tiago.discloud.dev` e independente. Migrar esse dominio exige outra etapa no painel Discloud.

A variavel `API_INTERNAL_URL` nao e necessaria nesta versao; a aplicacao React chama o FastAPI diretamente por `/api/` no mesmo dominio.
Nao coloque chaves privadas no GitHub nem no Next.js exportado.
